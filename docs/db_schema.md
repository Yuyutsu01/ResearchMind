# ResearchMind Swarm v1 - Database Schema

This document specifies the PostgreSQL relational database schema. The database acts as a persistent checkpoint and history manager, while active operations reside in-memory (RAM) and Redis Cache.

---

## 1. Schema Overview

```
 +------------------+           +----------------------+
 |      users       |           |       sessions       |
 |------------------|           |----------------------|
 | id (PK)          |<─────────*| id (PK)              |
 | name             |           | user_id (FK)         |
 | email            |           | prompt               |
 | created_at       |           | status (SM State)    |
 +------------------+           | created_at           |
                                +----------------------+
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                  ▼
             +--------------------+ +--------------+ +------------------+
             | blackboard_        | | knowledge_   | | telemetry_       |
             | checkpoints        | | graph        | | metrics          |
             |--------------------| |--------------| |------------------|
             | id (PK)            | | id (PK)      | | id (PK)          |
             | session_id (FK)    | | session_id   | | session_id (FK)  |
             | blackboard_state   | | nodes (JSONB)| | metric_name      |
             | (JSONB)            | | edges (JSONB)| | value            |
             | created_at         | | updated_at   | | unit             |
             +--------------------+ +--------------+ | created_at       |
                                                     +------------------+
```

---

## 2. Table Definitions

### `users`
Tracks the platform users.
```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### `sessions`
Represents a single research session. The `status` field corresponds directly to the Research State Machine (`IDLE`, `SEARCHING`, `READING`, `VERIFYING`, `SYNTHESIZING`, `QUESTIONING_USER`, `COMPLETE`).
```sql
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    prompt TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'IDLE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### `blackboard_checkpoints`
Stores low-frequency checkpoints of the blackboard state for crash recovery. The `blackboard_state` is a JSON representation of Working Memory, Event Queue, Active Tasks, Context, Session State, and Budget.
```sql
CREATE TABLE IF NOT EXISTS blackboard_checkpoints (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    blackboard_state JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### `knowledge_graph`
Stores the NetworkX graph state for persistence.
```sql
CREATE TABLE IF NOT EXISTS knowledge_graph (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    nodes JSONB NOT NULL DEFAULT '[]'::jsonb,
    edges JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### `confidence_claims`
Maintained by the Confidence Engine and Critic Agent to log extracted claims and evidence.
```sql
CREATE TABLE IF NOT EXISTS confidence_claims (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    confidence_score REAL NOT NULL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'PROVISIONAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### `hypotheses`
Tracks active hypotheses formulated by the Synthesizer Agent.
```sql
CREATE TABLE IF NOT EXISTS hypotheses (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    hypothesis_text TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, VALIDATED, FALSIFIED, SUPERSEDED
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### `telemetry_metrics`
Tracks performance history against the 5 key metrics.
```sql
CREATE TABLE IF NOT EXISTS telemetry_metrics (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL, -- TCR, Autonomy, Grounding, Hallucination, Cost
    value REAL NOT NULL,
    unit VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
