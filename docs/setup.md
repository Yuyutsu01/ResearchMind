# Local Development Setup Guide

This document describes how to configure, install, and execute the **Research Intelligence Platform** on a local development machine.

---

## Prerequisites
- **Python:** Version 3.9 or higher.
- **NodeJS:** Version 16.0 or higher.
- **Docker & Docker Compose:** Optional (for containerized runs).
- **Relational Storage:** PostgreSQL (SQLite fallback is automatically supported).
- **In-Memory Cache:** Redis instance.

---

## 1. Backend Manual Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix:
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` configuration file inside `backend/` with the following variables:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=postgresql://user:pass@localhost:5432/research_db
   REDIS_URL=redis://localhost:6379/0
   ```

5. Run the FastAPI development server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

The backend API will be available at `http://localhost:8000` and Swagger docs at `http://localhost:8000/docs`.

---

## 2. Frontend Manual Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite hot-reloading development server:
   ```bash
   npm run dev
   ```

4. Access the user interface at `http://localhost:5173`.

---

## 3. Database Fallbacks

By default, the platform will fallback to a local SQLite file (`research_platform.db`) and a memory-based cache dictionary if PostgreSQL and Redis environment URLs are not provided, allowing zero-config local testing.

To run performance tests locally, execute the benchmark suite:
```bash
# To run in Mock Mode (no API keys required)
python backend/benchmark.py --mock

# To run using real LLM API keys
python backend/benchmark.py
```
