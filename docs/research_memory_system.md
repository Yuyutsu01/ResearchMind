# ResearchMind Research Memory System Documentation

## 1. Executive Summary

The **Research Memory System** (`backend/src/runtime/memory/research_memory.py`) manages a persistent knowledge graph per user/session, storing learned concepts, preferred explanation depth, and bookmarks across paper reading sessions.

Instead of outputting redundant introductory definitions for familiar topics, the system adapts LLM system prompts automatically to suppress basic explanations and focus directly on advanced paper mechanics.

---

## 2. Memory Architecture & Dual-Layer Persistence

```
User Action (Selects & Reads Paper Content)
                     │
                     ▼
          ResearchMemorySystem
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
Redis Memory Cache      PostgreSQL Memory Schema
(sub-5ms Lookup)        (user_research_memory Table)
         │                       │
         └───────────┬───────────┘
                     ▼
       AIHarness.execute(...) System Prompt
       [Injected: USER KNOWLEDGE STATE]
```

---

## 3. Data Schema & Prompt Context

### User Memory Dataclass Schema
- `session_id`: Unique reading session identifier.
- `learned_concepts`: List of concept strings already mastered by the user (e.g. `["Transformers", "Q-Learning"]`).
- `preferred_level`: Reading depth (`Beginner`, `Undergraduate`, `Researcher`).
- `notes`: Annotated research notes.

### Injected Prompt Context Format
```text
USER KNOWLEDGE STATE:
The user already understands the following concepts: [Transformers, Self-Attention].
ADAPTIVE INSTRUCTION: Do NOT explain basic definitions for these mastered concepts. Focus directly on novel paper mechanics, mathematical derivations, or paper-specific contributions.
```
