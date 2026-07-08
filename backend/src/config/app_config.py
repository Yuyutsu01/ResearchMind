import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Settings
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_API_KEY = os.environ.get("LLM_API_KEY", "ollama")
    LLM_MODEL = os.environ.get("LLM_MODEL", "llama3")

    # DB Settings
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/researchmind")

    # Cache Settings
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Directories
    UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
    REPORT_DIR = os.path.join(os.getcwd(), "reports")

    # Budget Limits
    MAX_TOKENS_PER_SESSION = 500000
    MAX_DOLLARS_PER_SESSION = 10.00
    MAX_API_CALLS_PER_SESSION = 50

# Ensure directories exist
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.REPORT_DIR, exist_ok=True)
