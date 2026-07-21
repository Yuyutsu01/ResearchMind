# ResearchMind - Interactive AI Scholar Workspace

> **Interactive research-paper workspace where the PDF remains the primary interface and a collaborating swarm of specialized AI agents enriches understanding in real-time.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%20(TS)-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Tailwind CSS v4](https://img.shields.io/badge/Styling-Tailwind%20v4-38B2AC?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-D32F2F?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Cache-Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)

---

## 🔬 Core Vision

Instead of reading a research paper and constantly switching between ChatGPT, Google, Wikipedia, textbooks, and YouTube, researchers interact with the paper inside an intelligent workspace. 

The paper remains central and visible at all times. Every sentence, equation, figure, table, reference, or technical term becomes interactive. When a user highlights or clicks any part of the paper, a swarm of specialized AI agents collaborates in the background to produce explanations tailored to the user's focus.

---

## 🔬 Architectural Philosophy & Bio-Inspiration

ResearchMind Swarm v1 is inspired by the **SwarmSys** paper and the biological concept of **Ant Pheromone Stigmergy**.

Traditional multi-agent frameworks rely on rigid, hardcoded DAG pipelines (e.g. LangGraph chains) or monolithic coordinators which cascade failure when a single API call errors out. Instead, ResearchMind Swarm treats research as an adaptive, non-linear process coordinated via environmental modification.

```text
       [Agent A] 
           │
           │ (depose "pheromone" event)
           ▼
┌──────────────────────────────────────┐
│          Research Blackboard         │  <--- Environment Substrate
│  [Working Memory]  [Event Queue]     │
└──────────────────────────────────────┘
           ▲
           │ (senses pheromone, wakes up)
           │
       [Agent B]
```

### Stigmergy & Event Pheromones
In nature, ants coordinate by depositing chemical traces (pheromones) in the physical environment. Other ants detect these traces and adjust their trajectories, producing complex emergent behaviors.

---

## 🏗️ System Architecture & Progressive Pipeline

ResearchMind is built as a **modular monolith** optimized for low-latency, desktop-like responsiveness:

```text
+---------------------------------------------------------------+
|                       Research Paper Viewer                   |
|  Entire paper displayed exactly like a PDF                    |
|  User highlights:                                             |
|  "The transformer encoder generates contextual embeddings..." |
+-------------------------------------+-------------------------+
                                      |
                                      | WebSocket Event
                                      V
+---------------------------------------------------------------+
|                 AI Research Assistant Panel                   |
|---------------------------------------------------------------|
| Simple Intuition • Detailed Mechanics • Prerequisites          |
| Equation Derivations • ASCII Block Diagrams                   |
+---------------------------------------------------------------+
```

### 1. Progressive Document Pipeline
* **Capability Detector**: Performs a quick inspection of character density and image presence to determine processing capabilities.
* **Layout Coordinate Parser**: Employs PyMuPDF to extract sections, paragraphs, equations, figures, and bibliography elements along with absolute pixel bounding boxes page-by-page.
* **PostgreSQL Relational Schema**: Houses element node IDs, parent boundaries, and topological citation relationships.

### 2. Multi-Level Caching & Indexing
* **L1 Cache (Redis)**: Caches agent summary queries and raw paragraph lookups.
* **L2 Vector Database (Qdrant)**: Indices sentence-transformer chunks page-by-page in the background.
* **L3 Relational Database (PostgreSQL)**: Handles persistent user session files, research notebooks, and interaction timelines.

### 3. Collaborating Agent Swarms
A central **Swarm Orchestrator** manages user selection actions, activating only the relevant sub-agents in parallel to minimize latency:
* **ExplanationAgent**: Translates academic formulas and statements into plain English.
* **MathematicsAgent**: Generates LaTeX equations, maps variable definitions, and breaks down derivations step-by-step.
* **BackgroundKnowledgeAgent**: Detects prerequisite concepts.
* **VisualTeachingAgent**: Renders ASCII conceptual flowcharts and structural diagrams.
* **FigureInterpretationAgent / TableAnalysisAgent**: Interprets axes, legends, trends, and quantitative tabular benchmarks.
* **CitationAgent**: Resolves linked referenced publications.
* **QuestionPredictionAgent**: Recommends relevant follow-up inquiries.

### 4. GPU-Saving Virtualized PDF Reader
* Renders pages using Next.js canvas rendering upscaled dynamically to prevent text blurriness on Retina screens.
* Uses an `IntersectionObserver` to unmount canvases outside the viewport window to prevent memory leaks, maintaining a smooth 60fps scrolling experience.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15 (App Router), TS | Desktop IDE workspace panels & state management |
| **Styling** | Tailwind CSS v4, Outfit font | Premium Chromium-Black theme styles |
| **PDF Rendering** | HTML5 Canvas + PDF.js | High-DPI crisp text rendering layer |
| **Backend** | FastAPI, Python 3.11+ | High-performance REST and WebSocket gateways |
| **Agent Orchestrator** | asyncio, Python threads | Selective agent routing matrices |
| **Vector Search** | Qdrant | Cosine-similarity sentence embeddings |
| **ACID Database** | PostgreSQL | Relational schemas, notebook logs, & timeline events |
| **Caching** | Redis Cache | Sub-50ms query cache retrievals |

---

## 🚀 Getting Started

### 1. Set Up Environment Variables
Create a `.env` file in the root workspace directory:
```env
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/researchmind
REDIS_HOST=localhost
REDIS_PORT=6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 2. Run Database & Infrastructure Services
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
