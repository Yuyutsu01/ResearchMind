import json
import asyncio
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.adapters.db.postgres import execute_query
from src.domain.swarm.orchestrator import swarm_orchestrator
from src.adapters.db.redis_session import redis_session


router = APIRouter()
active_connections = {}

@router.websocket("/ws/v1/research/{session_id}")
async def websocket_research(websocket: WebSocket, session_id: int):
    await websocket.accept()
    conn_id = f"conn_{uuid.uuid4().hex[:8]}"
    print(f"[WebSocket] Connected client {conn_id} to session {session_id}.")
    
    if session_id not in active_connections:
        active_connections[session_id] = []
    active_connections[session_id].append(websocket)
    
    # Register active websocket session in Redis
    redis_session.register_active_connection(session_id, conn_id)
    
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
                redis_session.push_priority_page(session_id, page_num)
                    
            # 2. Interactive Selection Handler
            elif msg.get("type") == "selection":
                sel_text = msg.get("text", "")
                sel_type = msg.get("selection_type", "TEXT")
                obj_id = msg.get("id")
                page_num = int(msg.get("page", 1))
                custom_prompt = msg.get("custom_prompt")
                doc_obj = msg.get("document_object")
                
                obj_metadata = doc_obj or {}
                # If selection comes from a pre-parsed object ID, resolve coordinates/context from DB if not already provided
                if obj_id and not obj_metadata.get("bounding_box"):
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
                
                # Progressive section streaming callback
                def stream_section_ready(section_name: str, chunk_data: dict):
                    asyncio.create_task(send_client_payload({
                        "type": "section_stream",
                        "section": section_name,
                        "chunk": chunk_data
                    }))

                # Execute 10-phase swarm orchestration analysis
                prompt_text = f"{custom_prompt}\n\nSelected Content:\n{sel_text}" if custom_prompt else sel_text
                explanation = await swarm_orchestrator.process_selection(
                    session_id, prompt_text, sel_type, obj_id, page_num=page_num, stream_callback=stream_section_ready
                )
                
                # Append interaction and result summary to persistent Redis history
                summary = f"Analyzed {sel_type}"
                redis_session.append_stream_history(session_id, sel_text, summary)

                # Return complete finalized explanation & telemetry payload
                await send_client_payload({
                    "type": "selection_explanation",
                    "text": sel_text,
                    "selection_type": sel_type,
                    "id": obj_id,
                    "conversation_id": explanation.get("conversation_id"),
                    "page": page_num,
                    "explanation": explanation,
                    "telemetry": explanation.get("telemetry"),
                    "document_object": obj_metadata
                })

            # 3. Conversational Follow-up Question Handler
            elif msg.get("type") == "chat_followup":
                conv_id = msg.get("conversation_id", "")
                question = msg.get("question", "")

                def stream_section_ready(section_name: str, chunk_data: dict):
                    asyncio.create_task(send_client_payload({
                        "type": "section_stream",
                        "section": section_name,
                        "chunk": chunk_data
                    }))

                res = await swarm_orchestrator.process_chat_followup(
                    session_id=session_id,
                    conversation_id=conv_id,
                    question=question,
                    stream_callback=stream_section_ready
                )

                await send_client_payload({
                    "type": "chat_response",
                    "conversation_id": conv_id,
                    "role": "assistant",
                    "content": res["content"],
                    "telemetry": res.get("telemetry")
                })
                
    except WebSocketDisconnect:
        print(f"[WebSocket] Client {conn_id} disconnected from session {session_id}.")
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
        # Unregister active connection in Redis
        redis_session.unregister_active_connection(session_id, conn_id)
        if session_id in active_connections:
            if websocket in active_connections[session_id]:
                active_connections[session_id].remove(websocket)
