import os
import sys
import shutil
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

# Ensure local modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.postgres.db import create_task, update_task_output, get_telemetry_summary, execute_query
from agent.supervisor import create_supervisor_graph, AgentState
from agent.rl.policy_engine import policy_engine
from agent.rl.trainer import train_policy
from agent.rl.reward_engine import calculate_reward
from agent.rl.experience_store import save_transition

app = FastAPI(title="Research Intelligence Agent API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static directories for reports and uploads
os.makedirs("uploads", exist_ok=True)
os.makedirs("reports", exist_ok=True)
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

class ChatRequest(BaseModel):
    request: str
    pdf_path: Optional[str] = None

@app.get("/")
async def root():
    return {
        "status": "online", 
        "message": "Research Intelligence API is running",
        "rl_states": list(policy_engine.q_table.keys())
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Saves an uploaded scientific paper to disk.
    """
    try:
        file_path = os.path.join("uploads", file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "file_path": file_path, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload: {str(e)}")

@app.get("/history")
async def get_history():
    """
    Returns previous query runs.
    """
    query = "SELECT id, prompt, final_output, status, created_at FROM tasks ORDER BY id DESC LIMIT 20"
    rows = execute_query(query, fetch=True)
    return {"history": rows}

@app.get("/api/reports/{task_id}")
async def get_reports_for_task(task_id: int):
    """
    Returns the generated document paths for a specific task.
    """
    query = "SELECT file_path, format, section_summary FROM reports WHERE task_id = %s"
    rows = execute_query(query, (task_id,), fetch=True)
    return {"reports": rows}

@app.get("/telemetry")
async def get_telemetry():
    """
    Retrieves execution performance metrics.
    """
    summary = get_telemetry_summary()
    return {"metrics": summary}

@app.get("/rl/q-table")
async def get_q_table():
    """
    Exposes the active Q-table for visualization.
    """
    return {"q_table": policy_engine.q_table}

@app.post("/rl/train")
async def trigger_train():
    """
    Triggers reinforcement learning training on experience replay.
    """
    updates = train_policy()
    return {"success": True, "updates_performed": updates}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    print("[WebSocket] Client connected to research stream.")
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                user_request = message.get("request", "")
                pdf_path = message.get("pdf_path", "")
            except json.JSONDecodeError:
                user_request = data
                pdf_path = ""

            if not user_request:
                await websocket.send_json({"type": "error", "message": "Empty query received."})
                continue

            await websocket.send_json({"type": "status", "message": "Initializing task context..."})
            task_id = create_task(user_request)
            
            # Select RL Actions for State representation
            has_pdf = pdf_path != "" and os.path.exists(pdf_path)
            state_key = policy_engine.get_state_key(user_request, has_pdf)
            
            source_action = policy_engine.choose_action(state_key, "source_selection")
            retrieval_action = policy_engine.choose_action(state_key, "retrieval_strategy")
            expansion_action = policy_engine.choose_action(state_key, "expansion_depth")
            
            rl_actions = {
                "source_selection": source_action,
                "retrieval_strategy": retrieval_action,
                "expansion_depth": expansion_action
            }
            
            await websocket.send_json({
                "type": "rl_choices", 
                "task_id": task_id, 
                "state_key": state_key, 
                "choices": rl_actions
            })
            
            # Formulate Graph Input State
            initial_state: AgentState = {
                "query": user_request,
                "has_pdf": has_pdf,
                "pdf_path": pdf_path,
                "paper_metadata": {},
                "retrieved_papers": [],
                "external_context": [],
                "sections": {},
                "validation_results": {},
                "reports": {},
                "errors": [],
                "messages": [f"Init task with Q-learning actions: {rl_actions}"],
                "rl_actions": rl_actions,
                "task_id": task_id,
                "duration_ms": 0.0
            }
            
            # Compile and execute LangGraph
            app_graph = create_supervisor_graph()
            import time
            start_time = time.time()
            
            # Async stream updates to Client
            async for event in app_graph.astream(initial_state):
                for node_name, node_output in event.items():
                    await websocket.send_json({
                        "type": "agent_step",
                        "agent": node_name,
                        "messages": node_output.get("messages", [])[-1:] if node_output.get("messages") else [],
                        "metadata": node_output.get("paper_metadata", {}),
                        "retrieved_count": len(node_output.get("retrieved_papers", []))
                    })
            
            # Graph final retrieval
            final_res = app_graph.invoke(initial_state)
            duration_ms = (time.time() - start_time) * 1000.0
            
            # Update DB with completion
            final_out = final_res.get("sections", {}).get("summary", "Analysis completed.")
            update_task_output(task_id, final_out, "completed")
            
            # Calculate Rewards and Update Replay Memory
            val_score = final_res.get("validation_results", {}).get("citation_check", {}).get("score", 0.9)
            cit_score = final_res.get("validation_results", {}).get("citation_check", {}).get("score", 0.9)
            
            reward = calculate_reward(
                validation_score=val_score,
                citation_score=cit_score,
                duration_ms=duration_ms,
                user_feedback=0.95
            )
            
            # Store transition for training
            state_repr = {"query": user_request, "has_pdf": has_pdf}
            next_state_repr = {"query": user_request, "has_pdf": has_pdf, "success": val_score > 0.6}
            save_transition(state_repr, rl_actions, reward, next_state_repr)
            
            await websocket.send_json({
                "type": "result",
                "task_id": task_id,
                "validation": final_res.get("validation_results"),
                "reports": final_res.get("reports"),
                "duration_ms": duration_ms,
                "reward": reward
            })
            
    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected from research stream.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
