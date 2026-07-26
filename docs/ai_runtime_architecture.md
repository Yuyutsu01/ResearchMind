# ResearchMind AI Runtime Architecture Documentation

## 1. Executive Summary

ResearchMind's AI platform has been upgraded with a modular **AI Runtime Layer** (`backend/src/runtime/`).

The Runtime Layer separates infrastructure, safety, memory, and orchestration into clean, independently replaceable packages:

- **Phase 1 Foundation**:
  - `runtime/harness/`: **AI Harness** surrounding every LLM call (prompt construction, token budgeting, cost tracking, tool execution isolation).
  - `runtime/guardrails/`: **Guardrail Layer** running Multi-Stage Safety Checks (Pre-LLM Prompt Injection Defense, Post-LLM Citation Verification, Pre-UI Schema Validation).

---

## 2. Phase 1 Module Index & Interfaces

| Component | File Path | Primary Responsibilities |
| :--- | :--- | :--- |
| **AIHarness** | [harness.py](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/backend/src/runtime/harness/harness.py) | Central LLM execution wrapper, token budget enforcement, cost metrics tracking. |
| **GuardrailEngine** | [guardrails.py](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/backend/src/runtime/guardrails/guardrails.py) | Pre-LLM injection defense, Post-LLM citation grounding check, Pre-UI payload validation. |

---

## 3. Data Flow with AI Runtime Layer

```
User Selection
      │
      ▼
Pre-LLM Guardrail (Prompt Injection Scan) ── Is Unsafe? ──► [Block Request & Warn]
      │ Is Safe
      ▼
ResponseCache (Sub-10ms Redis Lookup)
      │ Cache MISS
      ▼
IntentRouter (Minimal Required Agent Set)
      │
      ▼
ContextBuilder (Single-Pass SharedContext Assembly)
      │
      ▼
Swarm Agents ──► AIHarness.execute(...) ──► LLM Provider (Cost & Token Budget Tracked)
      │
      ▼
Post-LLM Guardrail (Citation & Grounding Check)
      │
      ▼
Pre-UI Guardrail (Schema Integrity Validation)
      │
      ▼
ResponseComposer ──► WebSocket ──► SwarmAnalystPanel
```
