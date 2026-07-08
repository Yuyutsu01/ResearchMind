# ResearchMind Swarm v1
> **Autonomous Research Intelligence Platform powered by Stigmergetic Swarm Coordination & Reinforcement Learning Strategy.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%20(TS)-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Stable-Baselines3](https://img.shields.io/badge/RL-Stable--Baselines3-FF6F61?style=flat-square&logo=gymnasium&logoColor=white)](https://stable-baselines3.readthedocs.io)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-D32F2F?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Cache-Redis-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)

---

## 🔬 Architectural Philosophy & Bio-Inspiration

ResearchMind Swarm v1 is inspired by the **SwarmSys** paper and the biological concept of **Ant Pheromone Stigmergy**. 

Traditional multi-agent frameworks rely on rigid, hardcoded DAG pipelines (e.g. LangGraph chains) or monolithic coordinators which cascade failure when a single API call errors out. Instead, ResearchMind Swarm treats research as an adaptive, non-linear process coordinated via environmental modification.

```
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

In ResearchMind Swarm v1, this is represented by:
* **The Research Blackboard**: The shared environment substrate. It holds the active Knowledge Graph, Citation Graph, Task Queue, and Session state.
* **The Event Bus (Redis Streams / AsyncIO)**: Represents the pheromone dispersion network. When an agent performs a task, it modifies the Blackboard and emits an Event (e.g. `NEW_PAPER_FOUND`, `PAPER_ANALYZED`, `CONTRADICTION_FOUND`).
* **Task Scheduler (Priority Queue)**: Subscribed agents sense these events, prioritize task entries, and enqueue execution, letting complex workflows emerge without direct agent-to-agent coupling.

---

## 🧠 Memory Tiering Specification

To manage large contexts, information is divided into four memory layers:
1. **Working Memory (Research Blackboard)**: In-RAM and Redis Cache. Volatile, low-latency workspace for active sessions. Auto-checkpoints to PostgreSQL as a snapshot.
2. **Semantic Memory (Qdrant)**: High-dimensional vector database. Embeds paper chunks and scrapes (via SentenceTransformers) for semantic RAG retrieval filtered by `session_id`.
3. **Knowledge Memory (NetworkX)**: Directed graph in RAM representing scientific taxonomies, methods, formulas, and citation lineage. Serialized periodically to PostgreSQL JSONB.
4. **Relational Memory (PostgreSQL)**: Long-term ACID database containing user histories, project sessions, and performance telemetry metrics.

---

## 🚦 Research State Machine

Execution flow is governed by a centralized state machine visible on the client interface:
```
[IDLE] ──> [SEARCHING] ──> [READING] ──> [VERIFYING] ──> [SYNTHESIZING] ──> [QUESTIONING_USER] ──> [COMPLETE]
```
* **SEARCHING**: Explorer Agent queries academic databases and does citation walks.
* **READING**: Analyst Agent parses PDFs (via PyMuPDF) and extracts formulas, concepts, and experimental bounds.
* **VERIFYING**: Critic Agent runs validation checks, detects contradictions, and adjusts confidence.
* **SYNTHESIZING**: Synthesizer Agent consolidates duplicate concepts and updates NetworkX graphs.
* **QUESTIONING_USER**: UI Agent pauses research to request user-in-the-loop choices.

The next optimal action at each loop is predicted by a **Stable-Baselines3 PPO Strategist** trained on budget, graph completeness, and claim confidence rewards.

---

## 📊 Telemetry Metrics Framework

The platform actively tracks 5 key metrics logged in PostgreSQL and streamed live over WebSockets:
1. **Task Completion Rate (TCR)**: Evaluates if the session successfully generated a validated research summary without breaching resource constraints.
2. **Autonomy Score**: Ratio of steps executed autonomously without requiring human clarification.
3. **Answer Grounding Score**: Percentage of synthesized claims backed by direct citations and RAG context matches.
4. **Hallucination Rate**: Ratio of generated claims flagged as unsupported or inconsistent by the Critic.
5. **Cost per Session**: Cumulative cost (USD) computed from LLM input/output tokens and API calls.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| --- | --- | --- |
| **Backend** | Python 3.12+ / FastAPI | Async REST APIs & WebSocket streaming |
| **Frontend** | Next.js (React + TypeScript) | Responsive UI with Tailwind CSS & Shadcn UI |
| **Graph Visualizer** | Cytoscape.js | Citation & Knowledge Graph rendering |
| **Vector DB** | Qdrant | Semantic memory search |
| **RDBMS** | PostgreSQL | Relational storage & state snapshots |
| **Cache/Bus** | Redis / AsyncIO | Caching and event stream |
| **Graph Engine** | NetworkX | In-memory Knowledge Graph manipulation |
| **Document Parser** | PyMuPDF (Fitz) | Section extraction |
| **RL Engine** | Stable-Baselines3 (PPO) / PyTorch | Strategic action optimization |

---

## 🚀 Getting Started

### Prerequisites
* Docker & Docker Desktop
* Make (optional, for shortcut targets)

### Setup & Run
1. Configure your local environment by creating a `.env` file at the root:
   ```env
   # PostgreSQL Relational Connection
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/researchmind

   # Redis Caching Connection
   REDIS_URL=redis://localhost:6379/0

   # Qdrant Vector Connection
   QDRANT_HOST=localhost
   QDRANT_PORT=6333

   # LLM Settings (Ollama / Custom)
   LLM_BASE_URL=http://localhost:11434/v1
   LLM_API_KEY=ollama
   LLM_MODEL=llama3
   ```
2. Build and launch the environment:
   ```bash
   make dev
   ```
   *(Or: `docker-compose -f deploy/docker-compose.yml up --build`)*
3. Access the interfaces:
   * **Frontend Dashboard**: `http://localhost:3000`
   * **API Docs**: `http://localhost:8000/docs`
   * **Stop stack**: `make down`

---

## 🧪 Testing

Run backend Swarm tests using `pytest` inside the virtual environment:
```bash
cd backend
$env:PYTHONPATH="."
python -m pytest tests/test_swarm.py
```

---

## 📚 References

This architecture was designed and implemented under the inspiration of:
* **SwarmSys**: *Ruohao Li, Hongjun Liu, et al. "SwarmSys: Decentralized Swarm-Inspired Agents for Scalable and Adaptive Reasoning."* arXiv preprint arXiv:2510.10047 (2025). 
* **Stigmergetic Pheromones**: The decentralized coordination of autonomous agents via indirect environmental modification (stigmergy) and pheromone-inspired updates (event bus triggers).
