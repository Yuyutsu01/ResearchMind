import asyncio
import os
import json
from typing import Dict, Any, List, Optional
from src.adapters.db.postgres import execute_query
from src.adapters.db.qdrant import semantic_memory
from src.domain.parser.pdf_parser import scientific_parser
from src.adapters.db.redis_session import redis_session
from src.domain.services.task_queue import task_queue

async def run_progressive_ingestion(session_id: int, file_path: str, file_id: str, task_id: Optional[str] = None):
    """
    Asynchronous progressive background worker executing the multi-stage ingestion pipeline.
    """
    print(f"[Worker] Starting progressive ingestion for Session #{session_id} (Task ID: {task_id})...")
    if task_id:
        task_queue.update_progress(task_id, 5.0, "Starting capability scan & parsing...", status="RUNNING")
    
    # Session queues are managed persistently in Redis
    pass
        
    try:
        # --- PASS 1: Capability Scan & Quick Layout Parsing (< 500ms) ---
        caps = scientific_parser.detect_capabilities(file_path)
        
        # Save capabilities state inside sessions table metadata
        execute_query(
            "UPDATE sessions SET status = 'PARSING', file_id = %s WHERE id = %s;",
            (file_id, session_id)
        )
        
        # Parse document structure page-by-page (fast PyMuPDF scan)
        pipeline_res = scientific_parser.parse_document_layout(file_path)
        if not pipeline_res["success"]:
            raise Exception("Scientific parser layout scan failed.")
            
        objects = pipeline_res["objects"]
        relationships = pipeline_res["relationships"]
        
        # Save all objects to database
        for obj in objects:
            execute_query(
                """
                INSERT INTO paper_objects (session_id, id, type, page, bounding_box, parent_id, text_content, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id, id) DO UPDATE
                SET type = EXCLUDED.type, page = EXCLUDED.page, bounding_box = EXCLUDED.bounding_box,
                    parent_id = EXCLUDED.parent_id, text_content = EXCLUDED.text_content, metadata = EXCLUDED.metadata;
                """,
                (
                    session_id,
                    obj["id"],
                    obj["type"],
                    obj["page"],
                    obj["bbox"],
                    obj.get("parent_id"),
                    obj.get("text_content"),
                    json.dumps(obj.get("metadata", {}))
                )
            )
            
        # Save all relationships to database
        for rel in relationships:
            execute_query(
                """
                INSERT INTO object_relationships (session_id, source_id, target_id, relationship_type)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (session_id, source_id, target_id, relationship_type) DO NOTHING;
                """,
                (
                    session_id,
                    rel["source_id"],
                    rel["target_id"],
                    rel["relationship_type"]
                )
            )
            
        # Cache Pass 1 complete status in Redis and notify
        redis_session.set_task_status(session_id, "SECTIONS_READY", "PDF parsed. You can start reading!")
        if task_id:
            task_queue.update_progress(task_id, 20.0, "PDF outline parsed. Generating page embeddings...")

        await notify_client(session_id, {
            "type": "progress_update",
            "step": "SECTIONS_READY",
            "msg": "PDF parsed. You can start reading!",
            "capabilities": caps
        })
        
        # --- PASS 2 & 3: Progressive Page and Embedding Processing ---
        processed_pages = set()
        total_pages = caps["total_pages"]
        
        # Process pages sequentially or on-demand
        for page_idx in range(1, total_pages + 1):
            if task_id and task_queue.is_cancelled(task_id):
                print(f"[Worker] Task #{task_id} was cancelled by user. Halting worker execution.")
                return

            # Check if user has jumped to any page (Redis priority queue)
            priority_page = redis_session.pop_priority_page(session_id)
            while priority_page is not None and priority_page in processed_pages:
                priority_page = redis_session.pop_priority_page(session_id)
            
            target_page = priority_page if priority_page is not None else page_idx
            if target_page in processed_pages:
                continue
                
            print(f"[Worker] Parsing target Page #{target_page} in background...")
            
            # Fetch page paragraphs from database to generate embeddings
            rows = execute_query(
                "SELECT text_content FROM paper_objects WHERE session_id = %s AND page = %s AND type = 'paragraph';",
                (session_id, target_page),
                fetch=True
            )
            
            if rows and semantic_memory:
                chunks = [r["text_content"] for r in rows if r["text_content"]]
                if chunks:
                    semantic_memory.add_chunks(session_id, file_id, chunks)
                    
            processed_pages.add(target_page)
            
            # Cache incremental page parse status and notify
            pct = 20.0 + (len(processed_pages) / max(total_pages, 1)) * 75.0
            if task_id:
                task_queue.update_progress(task_id, pct, f"Indexed page {target_page}/{total_pages}")
            redis_session.set_task_status(session_id, "PAGE_PARSED", f"Page {target_page} semantic layer loaded.", page=target_page)
            await notify_client(session_id, {
                "type": "progress_update",
                "step": "PAGE_PARSED",
                "page": target_page,
                "msg": f"Page {target_page} semantic layer loaded."
            })
            
            # Brief sleep to avoid locking backend thread
            await asyncio.sleep(0.05)
            
        # Update session status to READY
        execute_query("UPDATE sessions SET status = 'READY' WHERE id = %s;", (session_id,))
        if task_id:
            task_queue.update_progress(task_id, 100.0, "Ingestion completed.", status="COMPLETED")

        # Cache complete status and notify
        redis_session.set_task_status(session_id, "COMPLETE", "Ingestion pipeline fully completed. Knowledge Graph built.")
        await notify_client(session_id, {
            "type": "progress_update",
            "step": "COMPLETE",
            "msg": "Ingestion pipeline fully completed. Knowledge Graph built."
        })
        
    except Exception as e:
        print(f"[Worker Error] Ingestion runner failed for Session #{session_id}: {e}")
        execute_query("UPDATE sessions SET status = 'FAILED' WHERE id = %s;", (session_id,))
        if task_id:
            task_queue.update_progress(task_id, 0.0, f"Ingestion failed: {e}", status="FAILED", error=str(e))
        redis_session.set_task_status(session_id, "ERROR", f"Ingestion pipeline failed: {str(e)}")
        await notify_client(session_id, {
            "type": "progress_update",
            "step": "ERROR",
            "msg": f"Ingestion pipeline failed: {str(e)}"
        })

async def notify_client(session_id: int, payload: dict):
    """
    Dispatches a WebSocket notification payload to the active session.
    """
    from src.adapters.api.websocket import active_connections
    if session_id in active_connections:
        for client in active_connections[session_id]:
            try:
                await client.send_json(payload)
            except Exception:
                pass
