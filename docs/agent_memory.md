# Agent Memory System Architecture

ResearchMind features a unified multi-tiered Agent Memory System designed to provide deep contextual awareness across research interactions.

---

## 1. Memory Tier Overview

The memory engine retrieves context across three distinct tiers:

| Tier | Type | Storage Backend | Data Retained |
| :--- | :--- | :--- | :--- |
| **Short-Term Memory** | Session Context | Redis List | Last 3 query selections and generated summaries in the active session. |
| **Long-Term Memory** | Historical Notes | PostgreSQL | Highlights, annotations, and personal notes across all sessions of the user. |
| **Semantic Memory** | Document RAG | Qdrant DB | Bounding-box coordinate paragraph content similarity search (filtered by `session_id`). |

---

## 2. Automatic Context Injection Flow

Memory retrieval and prompt injection are fully automated:

```text
       [Swarm Agent Call]
               │
               ▼ (1) Call get_structured_json() passing session_id
         [LLM Adapter]
               │
               ▼ (2) Execute AgentMemorySystem.retrieve_context()
        [Memory Engine]
               ├─► Vector Search in Qdrant (scores > 0.4)
               ├─► Fetch recent stream history list from Redis
               ├─► Fetch prior notes from PostgreSQL
               ▼
  [Structured Context Compiled]
               │
               ▼ (3) Append context blocks to system instructions
  [Enriched System Prompt]
               │
               ▼ (4) Forward request to LLM Provider
```

---

## 3. Telemetry & Caching Boundary
* If a cached response exists in the L1 Redis cache for the generated key, the cache is hit instantly without executing memory queries, saving computation latency.
* Prompt expansions are skipped when the provider is set to `"mock"` to ensure mock tests pass deterministically.
