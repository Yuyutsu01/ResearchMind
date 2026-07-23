# Persistent Agent Orchestration (Workflows & Checkpoints)

ResearchMind implements transactional orchestrations for swarm intelligence operations using a centralized checkpointing database schema.

---

## 1. Schema Design & Tables

To enable durability, individual highlight-selection runs and agent sub-tasks are serialized inside PostgreSQL:

### 1.1 `workflow_runs`
Tracks the high-level parent task triggered by a user selection:
* `run_id`: UUID (Primary Key).
* `session_id`: Reference to user session.
* `selection_text`: The highlighted string.
* `selection_type`: Highlight class (e.g. `EQUATION`, `FIGURE`, `TEXT`).
* `status`: Current state (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`).

### 1.2 `task_checkpoints`
Tracks the execution lifecycle of individual sub-agents participating in the workflow:
* `task_id`: UUID (Primary Key).
* `run_id`: Reference to parent `workflow_runs`.
* `agent_name`: Sub-agent identifier (e.g. `math`, `visual`, `background`).
* `status`: Task state (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).
* `result`: JSONB field storing the structured return from the LLM adapter on success, or error trace on failure.
* `retries`: Integer tracking execution attempts.

---

## 2. Execution & Durability Lifecycle

```text
  [process_selection()]
         │
         ▼ (1) Generate UUID and insert "PENDING" workflow_runs row
  [Database Row Created]
         │
         ▼ (2) Create "PENDING" task_checkpoints rows for sub-agents (Math, Visual...)
  [Checkpoints Created]
         │
         ▼ (3) Launch execute_checkpointed_task() in parallel
  [Parallel Execution]
         ├─► [Check Cancellation] ──────► Aborts if workflow status is "CANCELLED"
         ├─► [Update status: "RUNNING"] ──► Write status to task_checkpoints
         ├─► [Invoke Agent Func] ──────► Execute LLM query
         │         ├─► [Success] ──────► Update status: "COMPLETED", cache JSON result
         │         └─► [Failure] ──────► Increment retries. Sleep and retry up to 3x.
         │                               Mark "FAILED" if exhausted.
         ▼
  [Merge & Complete]
         ▼ (4) If any task failed -> Run FAILED. If all successful -> Run COMPLETED.
```

---

## 3. Crash Recovery (Startup Hook)

If a container crash, hardware failure, or server restart occurs during execution:
* The backend execution daemon triggers the `recover_pending_workflows` hook during startup.
* The hook queries Postgres for any workflows marked `PENDING` or `RUNNING`.
* Uncompleted runs are set to `FAILED` to ensure the system returns to a consistent, safe state, preventing dangling locks or corrupted memory sessions.
