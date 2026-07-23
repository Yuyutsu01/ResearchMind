import os
import shutil
import json
import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from src.adapters.db.postgres import execute_query
from src.adapters.db.qdrant import semantic_memory

from src.domain.services.task_queue import task_queue

router = APIRouter(prefix="/api/v1")

class SessionCreate(BaseModel):
    user_id: int
    prompt: str
    file_id: Optional[str] = None

class NoteCreate(BaseModel):
    selection_text: str
    selection_type: str
    ai_explanations: dict
    user_note: Optional[str] = None

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Saves an uploaded scientific PDF to disk."""
    try:
        os.makedirs("uploads", exist_ok=True)
        file_path = os.path.join("uploads", file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "file_id": file.filename,
            "filename": file.filename,
            "file_path": file_path,
            "status": "uploaded",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/sessions", status_code=201)
async def create_session(req: SessionCreate):
    """Creates a new research session and spawns the progressive background parser."""
    try:
        # Check if user exists
        user_exists = execute_query("SELECT id FROM users WHERE id = %s", (req.user_id,), fetch=True)
        user_id = req.user_id
        if not user_exists:
            first_user = execute_query("SELECT id FROM users ORDER BY id ASC LIMIT 1", fetch=True)
            if first_user:
                user_id = first_user[0]["id"]
            else:
                execute_query("INSERT INTO users (name, email) VALUES ('Default Researcher', 'researcher@mind.ai')")
                first_user = execute_query("SELECT id FROM users ORDER BY id ASC LIMIT 1", fetch=True)
                user_id = first_user[0]["id"]

        rows = execute_query(
            "INSERT INTO sessions (user_id, prompt, status, file_id) VALUES (%s, %s, 'LOADING_PDF', %s) RETURNING id;",
            (user_id, req.prompt, req.file_id),
            fetch=True
        )
        session_id = rows[0]["id"]
        
        task_id = None
        # If paper upload is attached, launch the progressive background parser task instantly
        if req.file_id:
            file_path = os.path.join("uploads", req.file_id)
            if os.path.exists(file_path):
                task_id = task_queue.create_task(session_id, "ingestion_pipeline", {"file_id": req.file_id, "path": file_path})
                from src.domain.services.background_worker import run_progressive_ingestion
                asyncio.create_task(run_progressive_ingestion(session_id, file_path, req.file_id, task_id=task_id))
                
        return {
            "session_id": session_id,
            "task_id": task_id,
            "status": "LOADING_PDF",
            "prompt": req.prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Retrieves background task status and progress metrics."""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "task": task}

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancels a running background task."""
    success = task_queue.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Task could not be cancelled")
    return {"success": True, "message": f"Task #{task_id} cancelled."}

@router.get("/sessions/{session_id}/paper")
async def get_session_paper(session_id: int):
    """Retrieves session paper layout metadata and basic parsed sections for backward compatibility."""
    try:
        row = execute_query("SELECT file_id FROM sessions WHERE id = %s;", (session_id,), fetch=True)
        if not row or not row[0]["file_id"]:
            return {"success": False, "error": "No paper attached to this session."}
            
        file_id = row[0]["file_id"]
        
        # Reconstruct simple section texts from paper_objects table paragraphs
        objects = execute_query(
            "SELECT parent_id, text_content FROM paper_objects WHERE session_id = %s AND type = 'paragraph';",
            (session_id,),
            fetch=True
        )
        
        sections = {}
        for obj in objects:
            sec = obj["parent_id"] or "abstract"
            sections[sec] = sections.get(sec, "") + "\n" + obj["text_content"]
            
        # Limit text length
        for k, v in sections.items():
            sections[k] = v.strip()[:6000]
            
        return {
            "success": True,
            "file_id": file_id,
            "sections": sections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/objects")
async def get_session_objects(session_id: int):
    """Retrieves all parsed layout objects for the session."""
    try:
        rows = execute_query(
            "SELECT id, type, page, bounding_box, parent_id, text_content, metadata FROM paper_objects WHERE session_id = %s ORDER BY page ASC, id ASC;",
            (session_id,),
            fetch=True
        )
        return {"success": True, "objects": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/objects/{obj_id}")
async def get_session_object_details(session_id: int, obj_id: str):
    """Retrieves the details and relationships of a specific semantic object."""
    try:
        row = execute_query(
            "SELECT id, type, page, bounding_box, parent_id, text_content, metadata FROM paper_objects WHERE session_id = %s AND id = %s;",
            (session_id, obj_id),
            fetch=True
        )
        if not row:
            raise HTTPException(status_code=404, detail="Object not found")
            
        rels = execute_query(
            "SELECT target_id, relationship_type FROM object_relationships WHERE session_id = %s AND source_id = %s;",
            (session_id, obj_id),
            fetch=True
        )
        
        return {
            "success": True,
            "object": row[0],
            "relationships": rels
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/timeline")
async def get_session_timeline(session_id: int):
    """Retrieves the user's reading history timeline logs."""
    try:
        rows = execute_query(
            "SELECT id, action_type, details, created_at FROM reading_timeline WHERE session_id = %s ORDER BY id DESC;",
            (session_id,),
            fetch=True
        )
        return {"success": True, "timeline": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/notebook")
async def get_session_notebook(session_id: int):
    """Retrieves the user's notebook note logs."""
    try:
        rows = execute_query(
            "SELECT id, selection_text, selection_type, ai_explanations, user_note, created_at FROM research_notebook WHERE session_id = %s ORDER BY id DESC;",
            (session_id,),
            fetch=True
        )
        return {"success": True, "notebook": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/notebook")
async def create_notebook_note(session_id: int, req: NoteCreate):
    """Saves a selection highlight and its AI explanation with optional user comments."""
    try:
        execute_query(
            "INSERT INTO research_notebook (session_id, selection_text, selection_type, ai_explanations, user_note) VALUES (%s, %s, %s, %s, %s);",
            (session_id, req.selection_text, req.selection_type, json.dumps(req.ai_explanations), req.user_note)
        )
        return {"success": True, "message": "Note saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
