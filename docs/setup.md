# Local Development Setup Guide

This document describes how to configure, install, and execute the **Research Intelligence Platform** on a local development machine. It provides tailored instructions for **Windows Command Prompt (CMD)**, **PowerShell**, and **macOS/Linux (Bash/Zsh)**.

---

## Prerequisites
- **Python:** Version 3.9 or higher.
- **Node.js:** Version 16.0 or higher.
- **Docker & Docker Compose:** Optional (for containerized runs).
- **Relational Storage:** PostgreSQL (SQLite fallback is automatically supported).
- **In-Memory Cache:** Redis instance (memory fallback is automatically supported).

---

## 1. Quick Start: Containerized Suite (Zero-Config)

If you have Docker and Docker Compose installed, you can start the entire platform with a single command from the project root:

```bash
docker-compose up --build
```
- **Backend API**: `http://localhost:8000`
- **Frontend Dashboard**: `http://localhost:3000`

---

## 2. Manual Setup (Local Development)

If you are developing locally and want automatic hot-reloading, run the backend and frontend separately in two different terminal windows.

### A. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Clean previous virtual environments** (if you moved/renamed the folder):
   * **Windows CMD**:
     ```cmd
     if exist venv rmdir /s /q venv
     ```
   * **Windows PowerShell**:
     ```powershell
     if (Test-Path venv) { Remove-Item -Recurse -Force venv }
     ```
   * **macOS/Linux (Bash/Zsh)**:
     ```bash
     rm -rf venv
     ```

3. **Create a new virtual environment**:
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment**:
   * **Windows CMD**:
     ```cmd
     venv\Scripts\activate.bat
     ```
   * **Windows PowerShell**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   * **macOS/Linux (Bash/Zsh)**:
     ```bash
     source venv/bin/activate
     ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Start the FastAPI Development Server**:
   > [!IMPORTANT]
   > On Windows, running `uvicorn` directly can sometimes fail due to absolute script path mismatches if folders were moved. **Always run uvicorn via Python module syntax** to avoid this issue:
   
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

The backend API will now be available at `http://localhost:8000`. You can inspect the interactive documentation at `http://localhost:8000/docs`.

---

### B. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```

The frontend will run at `http://localhost:5173`. Open this URL in your browser to view the application dashboard.

---

## 3. Database Fallbacks & Configuration

By default, the platform fallback system works out of the box with zero configuration:
- If no PostgreSQL credentials are provided, it falls back to a local SQLite file (`research_platform.db`).
- If no Redis cache URL is found, it falls back to a local memory cache dictionary.

### Custom Environment Config
To connect to your own databases or use real LLM APIs, create a `.env` file inside the `backend/` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/research_db
REDIS_URL=redis://localhost:6379/0
```

### Running Performance Tests
To run local offline tests on the agent retrieval engine without deploying the UI, use the benchmark tool:
```bash
# To run in Mock Mode (no OpenAI/LLM API keys required)
python backend/benchmark.py --mock

# To run using real live API keys
python backend/benchmark.py
```

