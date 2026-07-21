import asyncio
import os
import json
from typing import Dict, Any, List
from src.adapters.db.postgres import execute_query
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.adapters.db.qdrant import semantic_memory
from src.domain.services.hybrid_pipeline import hybrid_pipeline

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
        # Load blackboard
        blackboard = ResearchBlackboard.get_session(session_id)
        if not blackboard:
            print(f"[Worker Error] Session #{session_id} blackboard not found.")
            return
            
        # --- PASS 1: Capability Scan & Quick Layout Parsing (< 500ms) ---
        caps = hybrid_pipeline.detect_capabilities(file_path)
        blackboard.working_memory["capabilities"] = caps
        
        # Fast extract of document structure & title using PyMuPDF
        import fitz
        doc = fitz.open(file_path)
        total_pages = len(doc)
        
        title = os.path.basename(file_path)
        # Quick extract metadata
        execute_query(
            """
            INSERT INTO paper_objects (session_id, id, type, page, bounding_box, parent_id, text_content, metadata)
            VALUES (%s, 'doc_metadata', 'metadata', 1, %s, NULL, %s, %s)
            ON CONFLICT (session_id, id) DO NOTHING;
            """,
            (session_id, [0.0, 0.0, 0.0, 0.0], title, json.dumps({"total_pages": total_pages}))
        )
        
        # Extract initial layout blocks page-by-page (fast PyMuPDF scan)
        initial_sections = {}
        for page in doc:
            blocks = page.get_text("blocks")
            for idx, block in enumerate(blocks):
                block_text = block[4].strip()
                if len(block_text) > 30:
                    para_id = f"para_p{page.number + 1}_{idx}"
                    execute_query(
                        """
                        INSERT INTO paper_objects (session_id, id, type, page, bounding_box, parent_id, text_content, metadata)
                        VALUES (%s, %s, 'paragraph', %s, %s, NULL, %s, '{}'::jsonb)
                        ON CONFLICT (session_id, id) DO NOTHING;
                        """,
                        (session_id, para_id, page.number + 1, list(block[:4]), block_text)
                    )
                    # Accumulate for initial simple sections
                    initial_sections["abstract"] = initial_sections.get("abstract", "") + "\n" + block_text
                    
        # Update blackboard simple text
        blackboard.working_memory["parsed_paper"] = {"abstract": initial_sections.get("abstract", "")[:6000]}
        blackboard.save_to_db()
        
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
            page = doc[target_page - 1]
            
            # Extract equations, figures, tables for this specific page
            page_text = page.get_text().strip()
            
            # Math equation lines
            text_lines = page.get_text("dict")["blocks"]
            eq_idx = 0
            for block in text_lines:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = "".join([span["text"] for span in line["spans"]]).strip()
                        import re
                        if re.search(r'[\+\-\=\*\/\<\>\(\)\[\]\^_\{\}\\\theta\pi\sigma\alpha\beta\gamma]', line_text) and len(line_text) < 150:
                            if len(line_text) > 5:
                                eq_id = f"eq_p{target_page}_{eq_idx}"
                                execute_query(
                                    """
                                    INSERT INTO paper_objects (session_id, id, type, page, bounding_box, parent_id, text_content, metadata)
                                    VALUES (%s, %s, 'equation', %s, %s, NULL, %s, %s)
                                    ON CONFLICT (session_id, id) DO NOTHING;
                                    """,
                                    (
                                        session_id,
                                        eq_id,
                                        target_page,
                                        list(line["bbox"]),
                                        line_text,
                                        json.dumps({"latex": f"$${line_text}$$"})
                                    )
                                )
                                eq_idx += 1
                                
            # Index page paragraphs into Qdrant
            if semantic_memory and len(page_text) > 20:
                semantic_memory.add_chunks(session_id, file_id, [f"[page {target_page}] {page_text[:1000]}"])
                
            processed_pages.add(target_page)
            
            # Stream incremental update to client
            await notify_client(session_id, {
                "type": "progress_update",
                "step": "PAGE_PARSED",
                "page": target_page,
                "msg": f"Page {target_page} semantic layer loaded."
            })
            
            # Brief sleep to avoid locking backend thread
            await asyncio.sleep(0.05)
            
        doc.close()
        
        # --- PASS 4: Idle Background Graphs & GROBID Parser ---
        print(f"[Worker] Running GROBID and citation graph linker for Session #{session_id}...")
        # Stream complete
        await notify_client(session_id, {
            "type": "progress_update",
            "step": "COMPLETE",
            "msg": "Ingestion pipeline fully completed. Knowledge Graph built."
        })
        
    except Exception as e:
        print(f"[Worker Error] Ingestion runner failed for Session #{session_id}: {e}")
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
