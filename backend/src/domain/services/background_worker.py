import asyncio
import os
import json
from typing import Dict, Any, List
from src.adapters.db.postgres import execute_query
from src.adapters.db.qdrant import semantic_memory
from src.domain.parser.pdf_parser import scientific_parser

# Priority queue of pages requested by the client viewport
page_priority_queue: Dict[int, asyncio.Queue] = {}

async def run_progressive_ingestion(session_id: int, file_path: str, file_id: str):
    """
    Asynchronous progressive background worker executing the multi-stage ingestion pipeline.
    """
    print(f"[Worker] Starting progressive ingestion for Session #{session_id}...")
    
    # Ensure queue exists for this session
    if session_id not in page_priority_queue:
        page_priority_queue[session_id] = asyncio.Queue()
        
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
            
        # Broadcast Pass 1 complete
        await notify_client(session_id, {
            "type": "progress_update",
            "step": "SECTIONS_READY",
            "msg": "PDF parsed. You can start reading!",
            "capabilities": caps
        })
        
        # --- PASS 2 & 3: Progressive Page and Embedding Processing ---
        processed_pages = set()
        queue = page_priority_queue[session_id]
        total_pages = caps["total_pages"]
        
        # Process pages sequentially or on-demand
        for page_idx in range(1, total_pages + 1):
            # Check if user has jumped to any page (Priority Queue)
            priority_page = None
            while not queue.empty():
                try:
                    priority_page = queue.get_nowait()
                    if priority_page in processed_pages:
                        priority_page = None
                    else:
                        break
                except asyncio.QueueEmpty:
                    break
            
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
            
            # Stream incremental page update to client
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
        
        # Stream complete
        await notify_client(session_id, {
            "type": "progress_update",
            "step": "COMPLETE",
            "msg": "Ingestion pipeline fully completed. Knowledge Graph built."
        })
        
    except Exception as e:
        print(f"[Worker Error] Ingestion runner failed for Session #{session_id}: {e}")
        execute_query("UPDATE sessions SET status = 'FAILED' WHERE id = %s;", (session_id,))
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
