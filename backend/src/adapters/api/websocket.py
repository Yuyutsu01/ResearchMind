import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.adapters.db.postgres import execute_query
from src.domain.swarm.orchestrator import swarm_orchestrator

router = APIRouter()
active_connections = {}

@router.websocket("/ws/v1/research/{session_id}")
async def websocket_research(websocket: WebSocket, session_id: int):
    await websocket.accept()
    print(f"[WebSocket] Connected to session {session_id}.")
    
    if session_id not in active_connections:
        active_connections[session_id] = []
    active_connections[session_id].append(websocket)
    
    async def send_client_payload(data: dict):
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            print(f"[WebSocket Send Warning] Failed to stream data: {e}")

    try:
        # Stream initial ready response
        await send_client_payload({
            "type": "state_change",
            "state": "CONNECTED"
        })
        
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            # 1. On-demand visible page prefetch scheduling
            if msg.get("type") == "page_visible":
                page_num = int(msg.get("page", 1))
                from src.domain.services.background_worker import page_priority_queue
                if session_id in page_priority_queue:
                    await page_priority_queue[session_id].put(page_num)
                    
            # 2. Interactive Selection Handler
            elif msg.get("type") == "selection":
                sel_text = msg.get("text", "")
                sel_type = msg.get("selection_type", "TEXT")
                obj_id = msg.get("id")
                
                obj_metadata = {}
                # If selection comes from a pre-parsed object ID, resolve coordinates/context
                if obj_id:
                    obj_row = execute_query(
                        "SELECT type, page, bounding_box, parent_id, text_content, metadata FROM paper_objects WHERE session_id = %s AND id = %s;",
                        (session_id, obj_id),
                        fetch=True
                    )
                    if obj_row:
                        obj = obj_row[0]
                        sel_text = obj["text_content"] or sel_text
                        sel_type = obj["type"].upper()
                        
                        rels = execute_query(
                            "SELECT target_id, relationship_type FROM object_relationships WHERE session_id = %s AND source_id = %s;",
                            (session_id, obj_id),
                            fetch=True
                        )
                        obj_metadata = {
                            "id": obj_id,
                            "type": obj["type"],
                            "page": obj["page"],
                            "parent_id": obj["parent_id"],
                            "bounding_box": obj["bounding_box"],
                            "metadata": obj["metadata"],
                            "relationships": rels
                        }
                
                # Execute swarm orchestration analysis
                explanation = await swarm_orchestrator.process_selection(session_id, sel_text, sel_type, obj_id)
                
                # Return progressive explanation payload
                await send_client_payload({
                    "type": "selection_explanation",
                    "text": sel_text,
                    "selection_type": sel_type,
                    "id": obj_id,
                    "explanation": explanation,
                    "metadata": obj_metadata
                })
                
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected from session {session_id}.")
    except Exception as e:
        print(f"[WebSocket Error] Exception inside streaming loop: {e}")
        try:
            await send_client_payload({
                "type": "error",
                "message": f"Internal execution error: {str(e)}"
            })
        except Exception:
            pass
    finally:
        if session_id in active_connections:
            if websocket in active_connections[session_id]:
                active_connections[session_id].remove(websocket)
