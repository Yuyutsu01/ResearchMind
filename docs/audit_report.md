# Project Audit Report: ResearchMind Platform

This audit report documents the current architectural baseline, modules, data flows, and performance/security bottlenecks of **ResearchMind** before executing the multi-phase production upgrade.

---

## 1. Architecture Overview

ResearchMind is structured as a **modular monolith** optimized for low-latency interactive document reading.

```
                      ┌───────────────────────────┐
                      │    Next.js Client (SPA)   │
                      │  Canvas Overlay / Panels  │
                      └─────────────┬─────────────┘
                                    │ REST & WebSockets
                                    ▼
                      ┌───────────────────────────┐
                      │    FastAPI API Gateway    │
                      └──────┬─────────────┬──────┘
                             │             │
                             ▼             ▼
                     ┌──────────────┐ ┌──────────────┐
                     │ Background   │ │ Swarm        │
                     │ Ingestion    │ │ Orchestrator │
                     └──────┬───────┘ └──────┬───────┘
                            │                │
                      ┌─────┴─────┐    ┌─────┴─────┐
                      ▼           ▼    ▼           ▼
                  [Postgres] [Qdrant] [Redis]  [LLM]
```

### Module Responsibilities
* **`backend/src/main.py`**: API Gateway bootstrapper; manages middleware configuration, startup database initialization, static uploads routing, and endpoints registration.
* **`backend/src/adapters/api`**:
  * `routes.py`: Manages session configuration, notebook edits, uploads, timelines, and layout object lookups.
  * `websocket.py`: Asynchronous websocket handler maintaining connection states and forwarding interactive text selections to the Swarm.
* **`backend/src/adapters/db`**:
  * `postgres.py`: Connection pool manager utilizing raw SQL transactions for persistent storage.
  * `qdrant.py`: Local vector storage wrapping sentence-transformer embeddings with session filters.
  * `redis_cache.py`: Hot explanation L1 caching layer.
* **`backend/src/adapters/llm_adapter.py`**: LLM interface calling OpenAI Chat Completions, caching responses, and providing local fallback mocks.
* **`backend/src/domain/parser/pdf_parser.py`**: Character, image, drawing, section layout, and citation parsing utilizing PyMuPDF (`fitz`).
* **`backend/src/domain/services/background_worker.py`**: Coordinates multi-stage PDF ingestion (structural indexing -> priority-queued sentence embedding).
* **`backend/src/domain/swarm`**:
  * `agents.py`: Specialized agents querying specific domain tasks (math, figures, tables, etc.).
  * `orchestrator.py`: Orchestrator routing selected text to appropriate agents in parallel and logging interactions.
* **`frontend/src/app`**: Dashboard initialization and globals.
* **`frontend/src/components/ReadingWorkspace.tsx`**: Dynamic virtualized PDF layout canvases with selective viewport unmounting to prevent memory exhaustion.

---

## 2. Complete Dependency Graph (Textual)

```
[backend/src/main.py]
  ├── [src/adapters/db/postgres.py]
  └── [src/adapters/api/routes.py]
        ├── [src/domain/services/background_worker.py]
        │     ├── [src/adapters/db/postgres.py]
        │     ├── [src/adapters/db/qdrant.py]
        │     └── [src/domain/parser/pdf_parser.py]
        │           └── [fitz (PyMuPDF)]
        └── [src/adapters/db/qdrant.py]
              └── [sentence-transformers]
  └── [src/adapters/api/websocket.py]
        ├── [src/domain/swarm/orchestrator.py]
        │     ├── [src/domain/swarm/agents.py]
        │     │     └── [src/adapters/llm_adapter.py]
        │     │           ├── [src/adapters/db/redis_cache.py]
        │     │           └── [httpx]
        │     └── [src/adapters/db/postgres.py]
        └── [src/domain/services/background_worker.py]
```

---

## 3. Data Flow & Lifecycles

### 3.1 Document Ingestion Flow
1. **User Uploads PDF** -> `POST /api/v1/upload` writes file to `uploads/`.
2. **Session Creation** -> `POST /api/v1/sessions` creates a postgres database record and invokes `run_progressive_ingestion` in a non-blocking `asyncio.create_task` loop.
3. **Pass 1 Ingestion** -> Parser scans basic layout elements and headings (<500ms) -> Saves details to `paper_objects` and `object_relationships` -> Streams `SECTIONS_READY` WebSocket progress update to the client.
4. **Pass 2 & 3 Ingestion** -> Worker iterates pages. If a user triggers a `page_visible` ws event, that page is priority-processed. Paragraph text blocks are parsed and vectorized into Qdrant using the local `all-MiniLM-L6-v2` encoder. Incremental `PAGE_PARSED` websocket updates are dispatched.

### 3.2 Interactive Selection Lifecycle
1. **Highlight Selection** -> Client triggers a text selection or object selection.
2. **WS Dispatch** -> Client sends a selection payload: `type="selection"`.
3. **Orchestration Matrix** -> Backend processes the type, maps relationships from postgres, and routes parallel agent threads via `asyncio.to_thread`.
4. **LLM Execution & L1 Cache** -> Agents compute L1 cache keys. If a cache miss occurs, the adapter executes an OpenAI call. On success, the response is saved in Redis and returned.
5. **Selection Event Log** -> Action details are written to `reading_timeline` in Postgres.
6. **WS Response** -> Sends complete selection analysis payload to the client.

---

## 4. Architectural Bottlenecks & Critical Issues

### 4.1 Broken Docker Deployments
* **Issue**: The `deploy/docker-compose.yml` specifies building `backend` and `frontend` using custom `Dockerfile` paths, but **no Dockerfiles exist in the repository**.
* **Impact**: Running `docker-compose up` fails immediately, making deployment impossible without manual host system configuration.

### 4.2 LLM Configuration Mismatches
* **Issue**: `.env` specifies `LLM_API_KEY` (pointing to Groq), `LLM_BASE_URL` (pointing to Groq), and `LLM_MODEL`. However, `llm_adapter.py` is hardcoded to look for `OPENAI_API_KEY` and calls `https://api.openai.com/v1/chat/completions`.
* **Impact**: Groq/Gemini configurations are completely ignored. Unless `OPENAI_API_KEY` is explicitly set in the host environment, the system falls back to synthetic mock responses.

### 4.3 Blocking Event Loop Risks
* **Issue**: Local `sentence-transformers` embeddings generation (`semantic_memory.add_chunks`) runs on the main async event loop.
* **Impact**: When processing large papers or multiple concurrent page uploads, the CPU-heavy matrix calculations will block the main thread, causing other WebSocket connections to freeze.

### 4.4 In-Memory WebSocket Session Limitations
* **Issue**: Active websocket connections mapping is stored in an in-memory dictionary `active_connections` in `websocket.py`.
* **Impact**: If the backend process restarts or crashes, all active connection references are lost, preventing the progressive worker from notifying clients about ingestion statuses.

### 4.5 Testing & CI Pipeline Gaps
* **Issue**: The `.github/workflows/ci.yml` file only executes `flake8` linting and `benchmark.py --mock`. The actual test file `backend/tests/test_swarm.py` is never run in CI.
* **Impact**: Regression bugs in agent routing or database integrations can easily pass checks and merge to master.

---

## 5. Technical Debt Checklist

* [ ] Lack of Alembic database migration tools (raw SQL startup scripts only).
* [ ] Hardcoded OpenAI connection pathways in LLM adapters.
* [ ] Unused dependencies: `zustand` is installed but no state uses it.
* [ ] In-memory session tracking lacks horizontal scale capabilities.
* [ ] Lack of standardized logging, tracing, or performance metrics.
