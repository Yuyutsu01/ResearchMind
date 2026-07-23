# Persistent Session Management Architecture (Redis)

ResearchMind leverages Redis as a shared persistence engine for active session states, eliminating in-memory dict/queue loss during process restarts.

---

## 1. Key Schemas & Data Structures

All data stored inside Redis is scoped under the `session:{session_id}` prefix:

```text
session:{session_id}:connections    -->  Redis SET storing UUIDs of active WebSocket client descriptors
session:{session_id}:page_queue      -->  Redis LIST representing the progressive page priorities queue
session:{session_id}:agent_state     -->  Redis STRING storing JSON dump of agent state settings
session:{session_id}:stream_history  -->  Redis LIST containing sequential highlight query and analysis summaries
session:{session_id}:task_status     -->  Redis STRING storing JSON dump of ingestion worker execution status
```

---

## 2. Component Integration

### 2.1 WebSocket Connection Registry (`websocket.py`)
* When a client establishes a WebSocket connection, a random connection ID is generated (`conn_xyz`).
* The ID is registered via `sadd` in `session:{session_id}:connections`.
* On disconnect, the ID is removed. If a process restart occurs, the set can be parsed to count active readers.

### 2.2 Viewport Progressive Priority Queue (`background_worker.py`)
* Instead of using Python's in-memory `asyncio.Queue`, the viewport priority scheduler pushes page visible indices to a Redis list (`rpush`).
* The background parser pops target indexes from the queue (`lpop`).
* This enables state survival across container restarts.

### 2.3 Automatic Expiration (TTL Cleanup)
* Every key initialized under the `session:{session_id}` prefix is configured with a default **Time-To-Live (TTL) of 24 hours (86,400 seconds)**.
* Old or abandoned sessions automatically clean up, avoiding database bloat.
