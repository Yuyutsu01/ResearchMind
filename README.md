# ResearchMind - Interactive AI Scholar Workspace & AI Runtime Engine

> **Interactive research-paper workspace where the PDF remains the primary interface and a collaborating swarm of specialized AI agents enriches understanding in real-time.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%20(TS)-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Tailwind CSS v4](https://img.shields.io/badge/Styling-Tailwind%20v4-38B2AC?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-D32F2F?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Cache-Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)

---

## Core Vision

Instead of reading a research paper and constantly switching between ChatGPT, Google, Wikipedia, textbooks, and YouTube, researchers interact with the paper inside an intelligent workspace. 

The paper remains central and visible at all times. Every sentence, equation, figure, table, reference, or technical term becomes interactive. When a user highlights or clicks any part of the paper, a swarm of specialized AI agents collaborates in the background to produce explanations tailored to the user's focus.

---

## Production AI Runtime Architecture

ResearchMind is powered by a production-grade **AI Runtime Layer** (`backend/src/runtime/`) built on SOLID architectural principles:

```text
User Selection (PDF Native Text Layer)
          │
          ▼
Pre-LLM Guardrail (Prompt Injection Defense) ──► Blocked if Malicious
          │
          ▼
ResponseCache (Sub-10ms Redis Lookup) ────────► Cache HIT (< 100ms Return)
          │ Cache MISS
          ▼
IntentRouter (Minimal Required Agent Set < 10ms)
          │
          ▼
ContextBuilder (Single-Pass SharedContext Assembly < 50ms)
          │
          ▼
Swarm Agents ──► AIHarness.execute(...) ──► LLM Provider (Token & Cost Tracked)
          │
          ▼
Post-LLM Guardrail (Citation & Grounding Verification)
          │
          ▼
ResponseComposer (Structured Markdown & Reading-Level Adaptor)
          │
          ▼
WebSocket Progressive Stream (TTFT < 700ms) ──► SwarmAnalystPanel
```

### 1. AI Harness (`runtime/harness/`)
* Centralized infrastructure wrapper surrounding all LLM calls.
* Manages prompt construction, context injection, token budgeting, execution resilience, and cost tracking ($/1K tokens).

### 2. Multi-Stage Guardrail Engine (`runtime/guardrails/`)
* **Pre-LLM Guard**: Scans incoming text selections for prompt injection patterns inside PDFs.
* **Post-LLM Guard**: Verifies citation references against database metadata to prevent hallucinated citations.
* **Pre-UI Guard**: Validates JSON schema integrity before output is composed and rendered in the frontend.

### 3. High-Performance Latency Pipeline (10-Phase Engine)
* **Intent Router**: Selective routing by content type (`equation` -> `math`, `background`, `questions`), avoiding unnecessary agent executions.
* **Single-Pass SharedContext Builder**: Fetches titles, section headers, surrounding paragraphs, figures, and citations **in a single pass** to eliminate duplicate queries.
* **LLM Tier Router**: Maps agent tasks to complexity model tiers (`FAST`, `REASONING`, `VISION`).
* **Progressive Section Streaming**: Streams Markdown section chunks over WebSocket as soon as available (**Time-To-First-Token < 700ms**).
* **Developer Telemetry Badge**: Displays real-time stage timings in the UI (`⚡ CACHE HIT (18ms)` / `⚡ TTFT: 520ms | 1.4s`).

### 4. Response Composer & Reading-Level Adaptor
* Formats multi-agent outputs into structured Markdown tab templates (`Explain`, `Math`, `Background`, `Visual`, `Citation`).
* Supports dynamic Reading-Level Selection: 🎓 **Beginner**, 📖 **Undergraduate**, 🧪 **Researcher**.
* Interactive **Collapsible Section Accordions** in `SwarmAnalystPanel`.

### 5. Adobe Acrobat-Fidelity Selection Engine
* Uses PDF.js native text layer and spatial spatial indexing to provide smooth, continuous text selection matching Adobe Acrobat fidelity.

---

## Collaborating Agent Swarms

A central **Swarm Orchestrator** manages user selection actions, activating only the required sub-agents in parallel:

* **ExplanationAgent**: Translates academic formulas and statements into plain English.
* **MathematicsAgent**: Generates LaTeX equations, maps variable definitions, and breaks down derivations step-by-step.
* **BackgroundKnowledgeAgent**: Detects prerequisite concepts.
* **VisualTeachingAgent**: Renders ASCII conceptual flowcharts and structural diagrams.
* **FigureInterpretationAgent / TableAnalysisAgent**: Interprets axes, legends, trends, and quantitative tabular benchmarks.
* **CitationAgent**: Resolves linked referenced publications.
* **QuestionPredictionAgent**: Recommends relevant follow-up inquiries.

---

## Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15 (App Router), TS | Desktop IDE workspace panels & state management |
| **Styling** | Tailwind CSS v4, Outfit font | Premium Chromium-Black theme styles |
| **PDF Engine** | PDF.js Native Text Layer + Canvas | Adobe Acrobat-grade continuous text selection |
| **Backend** | FastAPI, Python 3.11+ | High-performance REST and WebSocket gateways |
| **AI Runtime** | AIHarness & GuardrailEngine | Token budgeting, cost tracking & safety guards |
| **Swarm Pipeline** | IntentRouter & ParallelExecutor | Selective concurrent agent execution |
| **Vector Search** | Qdrant | Cosine-similarity sentence embeddings |
| **ACID Database** | PostgreSQL | Relational schemas, notebook logs, & timeline events |
| **Caching** | Redis Cache | Sub-10ms query & response cache retrievals |

---

## Getting Started

### 1. Set Up Environment Variables
Create a `.env` file in the root workspace directory:
```env
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/researchmind
REDIS_HOST=localhost
REDIS_PORT=6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 2. Run Infrastructure Services
Launch PostgreSQL, Qdrant, and Redis containers via Docker Compose:
```bash
docker-compose up -d
```

### 3. Spin Up Backend Server
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.main:app --port 8001 --reload
```

### 4. Run Frontend App
```bash
cd frontend
npm install
npm run dev -- -p 3001
```
Open **`http://localhost:3001`** in your browser to begin reading!

---

## References & Architecture Docs

* [Swarm Performance Architecture Documentation](docs/swarm_performance_architecture.md)
* [AI Runtime Architecture Documentation](docs/ai_runtime_architecture.md)
* [Response Composer Architecture Documentation](docs/response_composer_architecture.md)
* [SwarmSys: Decentralized Swarm-Inspired Agents for Scalable and Adaptive Reasoning](https://arxiv.org/abs/2510.10047)
