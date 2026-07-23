# Testing Strategy & Automated CI Pipeline

ResearchMind incorporates automated unit testing, API integration testing, memory context testing, swarm orchestration verification, and continuous integration workflows.

---

## 1. Test Suite Structure

All backend unit and integration tests reside in `backend/tests/`:

```text
backend/tests/
├── test_swarm.py           # SwarmOrchestrator routing matrix & transactional checkpoints
├── test_llm_providers.py   # LLM provider abstractions, backoff retries, and token cost tracking
├── test_task_queue.py      # AsyncTaskQueue progress tracking and cancellation tests
├── test_api_routes.py      # REST API endpoints & telemetry metrics tests
└── test_memory_system.py   # AgentMemorySystem short-term, long-term, and vector memory retrieval
```

---

## 2. Executing Tests Locally

Run the Pytest suite locally from the workspace root:

```bash
$env:PYTHONPATH="backend"; .\backend\venv\Scripts\pytest backend/tests/
```
*(Or on Linux/macOS: `PYTHONPATH=backend pytest backend/tests/`)*

---

## 3. GitHub Actions Continuous Integration (CI)

The GitHub Actions workflow defined in `.github/workflows/ci.yml` runs automatically on every push or pull request:
1. **Backend Job**: Sets up Python 3.11, installs requirements, and runs `pytest backend/tests/`.
2. **Frontend Job**: Sets up Node 20, installs dependencies, and verifies standalone production compilation (`npm run build`).
