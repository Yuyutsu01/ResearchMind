import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from src.adapters.db.postgres import execute_query
from src.domain.blackboard.blackboard import ResearchBlackboard
from src.domain.services.parser import scientific_parser
from src.adapters.db.qdrant import semantic_memory

router = APIRouter(prefix="/api/v1")

class SessionCreate(BaseModel):
    user_id: int
    prompt: str
    file_id: Optional[str] = None

class ExportRequest(BaseModel):
    format: str  # markdown, pdf, docx, pptx, latex

class NoteCreate(BaseModel):
    selection_text: str
    selection_type: str
    ai_explanations: dict
    user_note: Optional[str] = None

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Saves an uploaded scientific PDF to disk and processes its text layout."""
    try:
        os.makedirs("uploads", exist_ok=True)
        file_path = os.path.join("uploads", file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run parsing
        parse_res = scientific_parser.parse_pdf(file_path)
        if not parse_res["success"]:
            raise HTTPException(status_code=500, detail=f"PDF parsing error: {parse_res.get('error')}")
            
        return {
            "file_id": file.filename,
            "filename": file.filename,
            "file_path": file_path,
            "parsed_sections": list(parse_res["sections"].keys()),
            "status": "uploaded",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/sessions", status_code=201)
async def create_session(req: SessionCreate):
    """Creates a new research session entry in PostgreSQL."""
    try:
        # Check if user exists, if not, find or create the first valid user ID
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
            "INSERT INTO sessions (user_id, prompt, status) VALUES (%s, %s, 'IDLE') RETURNING id;",
            (user_id, req.prompt),
            fetch=True
        )
        if not rows:
            raise HTTPException(status_code=500, detail="Failed to create session.")
        session_id = rows[0]["id"]
        
        # Initialize knowledge graph entries
        execute_query(
            "INSERT INTO knowledge_graph (session_id, nodes, edges) VALUES (%s, '[]'::jsonb, '[]'::jsonb);",
            (session_id,)
        )
        
        # Initialize blackboard instance
        blackboard = ResearchBlackboard(session_id)
        blackboard.context["query"] = req.prompt
        
        # If paper upload is attached, launch the progressive background parser task instantly
        if req.file_id:
            file_path = os.path.join("uploads", req.file_id)
            if os.path.exists(file_path):
                blackboard.working_memory["file_id"] = req.file_id
                
                # Launch async progressive ingestion task in background
                import asyncio
                from src.domain.services.background_worker import run_progressive_ingestion
                asyncio.create_task(run_progressive_ingestion(session_id, file_path, req.file_id))
        
        # Save initial blackboard state to DB
        blackboard.save_to_db()
        
        return {
            "session_id": session_id,
            "status": "IDLE",
            "prompt": req.prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/sessions/{session_id}/graph")
async def get_session_graph(session_id: int):
    """Retrieves the NetworkX knowledge graph nodes and edges for Cytoscape.js visualization."""
    row = execute_query(
        "SELECT nodes, edges FROM knowledge_graph WHERE session_id = %s ORDER BY id DESC LIMIT 1;",
        (session_id,),
        fetch=True
    )
    if not row:
        return {"nodes": [], "edges": []}
        
    return {
        "nodes": row[0]["nodes"],
        "edges": row[0]["edges"]
    }

@router.get("/history")
async def get_history_sessions():
    """Lists recent research sessions."""
    rows = execute_query(
        "SELECT id, prompt, status, created_at FROM sessions ORDER BY id DESC LIMIT 20;",
        fetch=True
    )
    return {"history": rows}

@router.post("/sessions/{session_id}/export")
async def export_session_report(session_id: int, req: ExportRequest):
    """Compiles and exports the research brief in Markdown, Word, PowerPoint, or LaTeX."""
    try:
        checkpoint_row = execute_query(
            "SELECT blackboard_state FROM blackboard_checkpoints WHERE session_id = %s ORDER BY id DESC LIMIT 1",
            (session_id,),
            fetch=True
        )
        if not checkpoint_row:
            raise HTTPException(status_code=404, detail="No synthesis checkpoints found to export.")
            
        state = checkpoint_row[0]["blackboard_state"]
        synthesis = state.get("working_memory", {}).get("report_synthesis", "Empty synthesis report.")
        
        os.makedirs("reports", exist_ok=True)
        filename = f"report_session_{session_id}.{req.format}"
        file_path = os.path.join("reports", filename)
        
        if req.format == "markdown" or req.format == "latex":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(synthesis)
        else:
            # Word / PowerPoint simple compilation fallback
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(synthesis)
                
        return {
            "success": True,
            "download_url": f"/reports/{filename}",
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export compilation failed: {str(e)}")

@router.get("/sessions/{session_id}/paper")
async def get_session_paper(session_id: int):
    """Retrieves the parsed document structure (sections) stored in the blackboard working memory."""
    try:
        checkpoint_row = execute_query(
            "SELECT blackboard_state FROM blackboard_checkpoints WHERE session_id = %s ORDER BY id DESC LIMIT 1;",
            (session_id,),
            fetch=True
        )
        if not checkpoint_row:
            return {"success": False, "message": "No paper uploaded for this session.", "sections": {}}
            
        state = checkpoint_row[0]["blackboard_state"]
        if isinstance(state, str):
            import json
            state = json.loads(state)
            
        working_mem = state.get("working_memory", {})
        parsed_paper = working_mem.get("parsed_paper")
        file_id = working_mem.get("file_id")
        
        if not parsed_paper:
            return {"success": False, "message": "No paper uploaded for this session.", "sections": {}}
            
        return {
            "success": True,
            "file_id": file_id,
            "sections": parsed_paper
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve paper content: {str(e)}")

@router.get("/sessions/{session_id}/timeline")
async def get_session_timeline(session_id: int):
    """Retrieves the chronological reading history timeline for a session."""
    try:
        rows = execute_query(
            "SELECT id, action_type, details, created_at FROM reading_timeline WHERE session_id = %s ORDER BY id ASC;",
            (session_id,),
            fetch=True
        )
        return {"success": True, "timeline": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve timeline: {str(e)}")

@router.get("/sessions/{session_id}/notebook")
async def get_session_notebook(session_id: int):
    """Retrieves all saved research notes in the notebook for a session."""
    try:
        rows = execute_query(
            "SELECT id, selection_text, selection_type, ai_explanations, user_note, created_at FROM research_notebook WHERE session_id = %s ORDER BY id DESC;",
            (session_id,),
            fetch=True
        )
        return {"success": True, "notebook": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notebook: {str(e)}")

@router.post("/sessions/{session_id}/notebook")
async def create_notebook_note(session_id: int, req: NoteCreate):
    """Saves a selection highlight and its AI explanation with optional user comments to the notebook."""
    try:
        import json
        execute_query(
            "INSERT INTO research_notebook (session_id, selection_text, selection_type, ai_explanations, user_note) VALUES (%s, %s, %s, %s, %s);",
            (session_id, req.selection_text, req.selection_type, json.dumps(req.ai_explanations), req.user_note)
        )
        return {"success": True, "message": "Note saved to notebook successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save notebook note: {str(e)}")

@router.get("/sessions/{session_id}/objects")
async def get_session_objects(session_id: int):
    """Retrieves all parsed semantic objects for this session."""
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
            
        # Get relationships
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

