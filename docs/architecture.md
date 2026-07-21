# ResearchMind System Architecture

This document describes the design, data flows, and module interactions of **ResearchMind**.

---

## 1. High-Level Diagram

```text
                     ┌────────────────────────┐
                     │    Next.js Frontend    │
                     │  (TypeScript, Tailwind)│
                     └───────────┬────────────┘
                                 │ REST / WebSockets
                                 ▼
                     ┌────────────────────────┐
                     │    FastAPI Gateway     │
                     │   (src/main.py)        │
                     └───────────┬────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌──────────────────┐                            ┌──────────────────┐
│ Swarm Orchestrator│                            │Background Ingestion│
│ (orchestrator.py)│                            │ (background_worker)│
└────────┬─────────┘                            └────────┬─────────┘
         │                                               │
   ┌─────┼─────────────┐                           ┌─────┴─────┐
   ▼     ▼             ▼                           ▼           ▼
[Math] [Vision] [Explanation]                 [PyMuPDF]    [Qdrant]
Agent  Agent       Agent                       Parser      Embedder
```

---

## 2. Component Layout

ResearchMind is structured as a **modular monolith** to maximize development velocity while maintaining strict separation of concerns.

### 2.1 Backend Modules (`backend/src`)
* **`adapters/api`**: Houses REST routes (`routes.py`) for session management, file uploads, and notebook logging, alongside WebSocket connections (`websocket.py`) for interactive selections.
* **`adapters/db`**: Connectors for PostgreSQL (`postgres.py`) storage of layout blocks, Redis Cache (`redis_cache.py`) for low-latency JSON lookups, and Qdrant (`qdrant.py`) for vector embeddings.
* **`domain/parser`**: Coordinates coordinates parsing (`pdf_parser.py`) utilizing PyMuPDF (`fitz`).
* **`domain/swarm`**: Core AI swarm containing `orchestrator.py` and specialized experts (`agents.py`).

### 2.2 Frontend Components (`frontend/src`)
* **`app/`**: Next.js App Router workspace mounting `page.tsx` and custom global CSS.
* **`components/`**: Renders `ReadingWorkspace.tsx` featuring the IntersectionObserver virtualization canvas layers.

---

## 3. Data Ingestion Flow

1. User uploads a scientific PDF.
2. FastAPI saves the PDF under `uploads/` and returns the session ID instantly (<50ms).
3. Background progressive parser executes **Pass 1**:
   * Scans text blocks and layout shapes.
   * Maps relative coordinates and inserts layout elements into PostgreSQL.
   * Dispatches `SECTIONS_READY` WS message to client.
4. When a user scrolls to a page:
   * Client sends a `page_visible` event.
   * Ingestion queue prioritizes generating embeddings for that page's text blocks (**Pass 2**).
   * Embeddings are upserted to Qdrant.
