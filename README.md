# ResearchMind

**An open-source, interactive research paper workspace powered by a multi-agent AI runtime.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18%2B-green?style=flat-square&logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 15](https://img.shields.io/badge/Frontend-Next.js%2015-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Tailwind CSS v4](https://img.shields.io/badge/Styling-Tailwind%20v4-38B2AC?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-D32F2F?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Cache-Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)

---

## Overview

Reading scientific papers traditionally involves a fragmented workflow: switching continuously between the PDF viewer, search engines, AI chatbots, external dictionaries, and reference lists.

ResearchMind eliminates this context-switching by keeping the PDF as the primary interface. Selecting text, formulas, citations, tables, or figures triggers a swarm of specialized AI agents that analyze the paper's structure and render contextual explanations inline.

```text
Traditional Workflow:   PDF ──► Google ──► ChatGPT ──► Wikipedia ──► Back to PDF
ResearchMind Workflow:  PDF Selection ──► AI Agent Swarm ──► Contextual Inline Explanation
```

---

## Key Features

* **Native PDF Workspace**: PDF.js canvas and native text-layer rendering with continuous text selection.
* **Interactive Element Selection**: Instant selection handling for text blocks, formulas, figures, tables, and citations.
* **Specialized Agent Swarms**: Specialized agents for mathematical derivations, prerequisite concepts, ASCII block diagrams, figure analysis, and citation mapping.
* **Multi-Stage Guardrails**: Pre-LLM prompt injection defense, post-LLM citation verification against database metadata, and pre-UI schema validation.
* **Adaptive Reading Levels**: Toggle explanation depth dynamically between **Beginner**, **Undergraduate**, and **Researcher**.
* **Progressive Streaming Engine**: WebSocket streaming delivering Time-To-First-Token in `< 700ms`.
* **Multi-Tier Caching**: Sub-10ms Redis caching for paper structures, contexts, and pre-computed responses.
* **Research Notebook & Timeline**: Persistent annotation notebook and chronological reading session timeline.

---

## Architecture Overview

ResearchMind uses a modular runtime architecture separating selection processing, intent routing, context retrieval, safety guardrails, agent orchestration, and streaming layout composition.

```text
┌──────────────────┐
│  PDF Workspace   │  (Native Canvas & Text Layer Selection)
└────────┬─────────┘
         │ WebSocket Payload
         ▼
┌──────────────────┐
│ Guardrail Layer  │  (Pre-LLM Prompt Injection Defense)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Intent Router   │  (Selective Agent Routing by Content Type)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Context Builder  │  (Single-Pass SharedContext Assembly)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  AI Harness &    │  (Concurrent Agent Execution, LLM Router &
│   Agent Swarm    │   Token Budget / Cost Telemetry)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│Response Composer │  (Markdown Tab Layouts & Reading-Level Adaptation)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Streaming UI     │  (Progressive WebSocket Timeline & Collapsible Accordions)
└──────────────────┘
```

Detailed technical explanations are available in the [Documentation](#documentation) directory.

---

## Project Structure

```text
ResearchMind/
├── backend/                  # Python FastAPI Backend
│   ├── src/
│   │   ├── adapters/         # Database, Redis, LLM provider & Telemetry adapters
│   │   ├── domain/
│   │   │   ├── parser/       # PyMuPDF coordinate & layout extractor
│   │   │   ├── services/     # Task queues, cache & session services
│   │   │   └── swarm/        # Agent swarms, intent router & response composer
│   │   └── runtime/          # Core AI Runtime (Harness & Guardrails)
│   └── tests/                # Pytest unit and integration test suite
├── frontend/                 # Next.js 15 App Router Frontend
│   └── src/
│       ├── components/       # Workspace panels, PDF viewer & Swarm Analyst UI
│       └── lib/              # Text selection engine & spatial index
├── deploy/                   # Docker Compose & service definitions
└── docs/                     # Technical architecture documentation
```

---

## Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15 (App Router), TypeScript | Workspace UI, state management, and sidebars |
| **PDF Rendering** | PDF.js + HTML5 Canvas | Crisp PDF rendering and continuous text selection |
| **Styling** | Tailwind CSS v4, Outfit font | Dark-mode scholar workspace aesthetics |
| **Backend API** | FastAPI, Python 3.11+ | REST endpoints and WebSocket streaming gateways |
| **AI Runtime** | AIHarness & GuardrailEngine | LLM execution, token budgeting, cost tracking & safety guards |
| **Agent Swarm** | asyncio, Python threads | Selective concurrent agent execution |
| **Vector DB** | Qdrant | Cosine-similarity embeddings for paper chunks |
| **Relational DB** | PostgreSQL | Paper layout trees, notebooks, and reading timelines |
| **Cache Layer** | Redis | Sub-10ms response and context caching |

---

## Quick Start

### Prerequisites

* **Python 3.11+**
* **Node.js 18+**
* **Docker & Docker Compose**

### 1. Clone & Setup Environment

```bash
git clone https://github.com/Yuyutsu01/ResearchMind.git
cd ResearchMind
cp .env.example .env
```

### 2. Start Infrastructure Services

```bash
docker-compose -f deploy/docker-compose.yml up -d
```

### 3. Start Backend Server

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn src.main:app --port 8001 --reload
```

### 4. Start Frontend Application

```bash
cd frontend
npm install
npm run dev -- -p 3001
```

Open **`http://localhost:3001`** in your browser to start reading papers.

---

## Configuration

System settings and API keys are managed via environment variables defined in `.env`:

```env
# LLM Providers
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key

# Infrastructure
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/researchmind
REDIS_HOST=localhost
REDIS_PORT=6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

Refer to [.env.example](.env.example) for complete options.

---

## Documentation

Detailed technical documents are stored in the `docs/` directory:

* [AI Runtime Architecture](docs/ai_runtime_architecture.md) — AI Harness, Guardrails, and safety policies.
* [Swarm Performance Architecture](docs/swarm_performance_architecture.md) — 10-phase performance pipeline and caching.
* [Response Composer Architecture](docs/response_composer_architecture.md) — Structured markdown rendering and reading levels.
* [Background Task Queue](docs/background_tasks.md) — Redis task queue and offline resilience fallback.

---

## Roadmap

- [x] Native PDF text-layer selection engine
- [x] Multi-agent swarm orchestration (`math`, `background`, `visual`, `citation`)
- [x] Single-pass `SharedContext` builder & `IntentRouter`
- [x] Multi-stage Guardrail Engine (Pre-LLM injection defense & citation verification)
- [x] AI Harness with token budgeting and cost tracking
- [x] Response Composer & Reading-Level Adaptor
- [x] Redis response caching and progressive WebSocket section streaming
- [ ] Cross-paper Knowledge Graph visualization
- [ ] Multi-document comparative analysis
- [ ] Model Context Protocol (MCP) Tool Integration
- [ ] Plugin Agent Registry

---

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'feat: add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

Please ensure all tests pass (`pytest` and `npm run build`) before submitting your PR.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
