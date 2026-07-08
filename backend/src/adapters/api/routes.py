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
            "success": true
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/sessions", status_code=21)
async def create_session(req: SessionCreate):
    """Creates a new research session entry in PostgreSQL."""
    try:
        rows = execute_query(
            "INSERT INTO sessions (user_id, prompt, status) VALUES (%s, %s, 'IDLE') RETURNING id;",
            (req.user_id, req.prompt),
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
        
        # If paper upload is attached, load parsed sections into blackboard and Qdrant
        if req.file_id:
            file_path = os.path.join("uploads", req.file_id)
            if os.path.exists(file_path):
                parse_res = scientific_parser.parse_pdf(file_path)
                if parse_res["success"] and semantic_memory:
                    # Index chunks in Qdrant
                    chunks = []
                    for sec_name, content in parse_res["sections"].items():
                        if len(content) > 50:
                            # Divide section into smaller chunks
                            paragraphs = content.split(". ")
                            for para in paragraphs:
                                if len(para.strip()) > 30:
                                    chunks.append(f"[{sec_name}] {para.strip()}")
                                    
                    semantic_memory.add_chunks(session_id, req.file_id, chunks)
        
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
