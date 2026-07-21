import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.adapters.db.postgres import init_db
from src.adapters.api import routes, websocket

# Create uploads directory statically
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="ResearchMind API", version="2.0.0")

# Enable CORS for Next.js frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup DB schemas creation
@app.on_event("startup")
def on_startup():
    init_db()

# Mount uploaded PDFs directory statically
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Routers
app.include_router(routes.router)
app.include_router(websocket.router)

@app.get("/")
def read_root():
    return {"status": "online", "service": "ResearchMind Server"}
