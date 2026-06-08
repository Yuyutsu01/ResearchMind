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

@app.delete("/history/{task_id}")
async def delete_history_item(task_id: int):
    """
    Deletes a specific task history item, its DB references, and any associated generated report files.
    """
    try:
        # Check if the task exists
        query_check = "SELECT id FROM tasks WHERE id = %s"
        row = execute_query(query_check, (task_id,), fetch=True)
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Select and remove associated report files from the filesystem
        query_reports = "SELECT file_path FROM reports WHERE task_id = %s"
        report_files = execute_query(query_reports, (task_id,), fetch=True)
        for rep in report_files:
            file_path = rep.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"[Delete File Error] {file_path}: {e}")
        
        # Delete related database entries
        execute_query("DELETE FROM tool_calls WHERE task_id = %s", (task_id,))
        execute_query("DELETE FROM plans WHERE task_id = %s", (task_id,))
        execute_query("DELETE FROM reports WHERE task_id = %s", (task_id,))
        execute_query("DELETE FROM concepts WHERE task_id = %s", (task_id,))
        execute_query("DELETE FROM tasks WHERE id = %s", (task_id,))
        
        return {"success": True, "message": f"Successfully deleted task {task_id}."}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to delete history item: {str(e)}")


@app.get("/api/reports/{task_id}")
async def get_reports_for_task(task_id: int):
    """
    Returns the generated document paths for a specific task.
    """
    query = "SELECT file_path, format, section_summary FROM reports WHERE task_id = %s"
    rows = execute_query(query, (task_id,), fetch=True)
    return {"reports": rows}

@app.get("/api/concepts/{task_id}")
async def get_concepts_endpoint(task_id: int):
    """
    Retrieves the extracted scientific concepts for a specific task.
    """
    from memory.postgres.db import get_concepts
    concepts = get_concepts(task_id)
    return {"concepts": concepts}

@app.get("/api/citation-graph/{task_id}")
async def get_citation_graph_endpoint(task_id: int):
    """
    Generates and returns the D3 citation node-link graph for a specific task.
    """
    from tools.citation_graph import generate_citation_graph
    graph_data = generate_citation_graph(task_id)
    return graph_data

@app.post("/api/export/{task_id}/{export_format}")
async def export_task_endpoint(task_id: int, export_format: str):
    """
    Generates and saves a compiled export document (latex, docx, pptx) for a research task.
    """
    try:
        task_query = "SELECT prompt FROM tasks WHERE id = %s"
        task_row = execute_query(task_query, (task_id,), fetch=True)
        if not task_row:
            raise HTTPException(status_code=404, detail="Task not found")
        title = task_row[0]["prompt"]
        
        reports_query = "SELECT section_summary FROM reports WHERE task_id = %s"
        report_rows = execute_query(reports_query, (task_id,), fetch=True)
        
        sections = {}
        for r in report_rows:
            summary_str = r.get("section_summary")
            if summary_str:
                try:
                    summary = json.loads(summary_str) if isinstance(summary_str, str) else summary_str
                    sections.update(summary)
                except Exception:
                    continue
                    
        if not sections:
            raise HTTPException(status_code=400, detail="No generated sections found to export.")
            
        import re
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")[:50]
        os.makedirs("reports", exist_ok=True)
        
        from tools.export_tool import generate_latex_template, generate_docx_document, generate_pptx_presentation
        
        filename = ""
        if export_format.lower() == "latex":
            filename = f"{safe_title}.tex"
            file_path = os.path.join("reports", filename)
            tex_content = generate_latex_template(title, sections)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tex_content)
        elif export_format.lower() == "docx":
            filename = f"{safe_title}.docx"
            file_path = os.path.join("reports", filename)
            generate_docx_document(title, sections, file_path)
        elif export_format.lower() == "pptx":
            filename = f"{safe_title}.pptx"
            file_path = os.path.join("reports", filename)
            generate_pptx_presentation(title, sections, file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format. Use docx, pptx, or latex.")
            
        # Register new export in database reports table if not already present
        check_q = "SELECT id FROM reports WHERE task_id = %s AND format = %s"
        existing = execute_query(check_q, (task_id, export_format), fetch=True)
        if not existing:
            insert_q = "INSERT INTO reports (task_id, file_path, format, section_summary) VALUES (%s, %s, %s, %s)"
            execute_query(insert_q, (task_id, file_path, export_format, json.dumps(sections)))
            
        return {"success": True, "file_path": f"/reports/{filename}", "filename": filename}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

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
