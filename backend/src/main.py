import os
from dotenv import load_dotenv

# Load environment variables from the workspace root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv()

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

import time
from fastapi import Request, Response
from src.adapters.telemetry import telemetry

# HTTP Request Latency & Counter Telemetry Middleware
@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    endpoint = request.url.path
    telemetry.record_api_request(request.method, endpoint, response.status_code, duration)
    return response

# Startup DB schemas creation
@app.on_event("startup")
def on_startup():
    init_db()
    from src.domain.swarm.orchestrator import swarm_orchestrator
    swarm_orchestrator.recover_pending_workflows()

# Mount uploaded PDFs directory statically
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Routers
app.include_router(routes.router)
app.include_router(websocket.router)

@app.get("/")
def read_root():
    return {"status": "online", "service": "ResearchMind Server"}

@app.get("/metrics")
def get_metrics():
    """Prometheus Scrape Endpoint."""
    content, media_type = telemetry.get_metrics_content()
    return Response(content=content, media_type=media_type)
