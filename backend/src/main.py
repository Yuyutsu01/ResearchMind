import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add current directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters.db.postgres import init_db
from src.adapters.api.routes import router as rest_router
from src.adapters.api.websocket import router as ws_router

app = FastAPI(title="ResearchMind Swarm API", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folders
os.makedirs("reports", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
app.mount("/reports", StaticFiles(directory="reports"), name="reports")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Register routers
app.include_router(rest_router)
app.include_router(ws_router)

@app.on_event("startup")
def startup_event():
    # Initialize PostgreSQL schemas
    init_db()

@app.get("/")
def read_root():
    return {"status": "online", "platform": "ResearchMind Swarm v1"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
