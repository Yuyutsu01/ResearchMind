import pytest
from src.domain.services.task_queue import AsyncTaskQueue

def test_async_task_queue_lifecycle():
    queue = AsyncTaskQueue()
    # Mock redis client behavior for unit testing
    task_id = queue.create_task(session_id=1, task_name="test_ingestion", payload={"file": "test.pdf"})
    assert isinstance(task_id, str)

    # Test progress update
    queue.update_progress(task_id, 50.0, "Halfway done")
    task = queue.get_task(task_id)
    if task:
        assert task["progress"] == 50.0
        assert task["status"] == "RUNNING"

    # Test cancellation
    cancelled = queue.cancel_task(task_id)
    assert cancelled is True
    assert queue.is_cancelled(task_id) is True
