# Background Task System Architecture

ResearchMind isolates heavy operations (PDF parsing, text block extraction, Qdrant embedding generation, and report building) from the main FastAPI request loop into a Redis-backed `AsyncTaskQueue`.

---

## 1. Task Lifecycle & Schemas

Tasks are stored in Redis under the `task:{task_id}` prefix key with a default **24-hour TTL**:

```json
{
  "task_id": "3a92f24a-7182-41b9-8e43-1e5f8f8b87a1",
  "session_id": 42,
  "name": "ingestion_pipeline",
  "status": "RUNNING",
  "progress": 65.5,
  "retries": 0,
  "max_retries": 3,
  "payload": {
    "file_id": "attention_is_all_you_need.pdf"
  },
  "msg": "Indexed page 4/12",
  "error": null,
  "created_at": 1721730000.0,
  "updated_at": 1721730045.0
}
```

### Supported Task Statuses
* `PENDING`: Task enqueued, awaiting worker activation.
* `RUNNING`: Worker actively executing step passes.
* `COMPLETED`: Ingestion and embedding vector upserts fully finished.
* `FAILED`: Internal exception thrown; error message recorded.
* `CANCELLED`: Execution halted by user action.

---

## 2. API Endpoints

### 2.1 Enqueue Task
* **`POST /api/v1/sessions`**: Enqueues an ingestion task when a PDF `file_id` is supplied, returning the generated `task_id`.

### 2.2 Inspect Task Progress
* **`GET /api/v1/tasks/{task_id}`**: Retrieves task status, completion percentage (`progress`), and status logs.

### 2.3 Cancel Task
* **`POST /api/v1/tasks/{task_id}/cancel`**: Sets `status="CANCELLED"`. Workers check cancellation flags between page indexing passes and halt safely.
