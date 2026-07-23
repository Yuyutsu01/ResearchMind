import os
import json
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, Callable
from src.adapters.db.redis_cache import redis_cache

class AsyncTaskQueue:
    """
    Redis-backed Asynchronous Task Queue for heavy operations 
    (PDF parsing, chunking, embedding generation, report building).
    Provides task status tracking, progress metrics, retries, and cancellation support.
    """
    def __init__(self):
        self.redis = redis_cache.client
        self.ttl = 86400  # 24 hours TTL for task records

    def _get_key(self, task_id: str) -> str:
        return f"task:{task_id}"

    def create_task(self, session_id: int, task_name: str, payload: Dict[str, Any], max_retries: int = 3) -> str:
        """Initializes a new task record in Redis."""
        task_id = str(uuid.uuid4())
        task_data = {
            "task_id": task_id,
            "session_id": session_id,
            "name": task_name,
            "status": "PENDING",
            "progress": 0.0,
            "retries": 0,
            "max_retries": max_retries,
            "payload": payload,
            "msg": "Task enqueued.",
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        if self.redis:
            try:
                self.redis.setex(self._get_key(task_id), self.ttl, json.dumps(task_data))
            except Exception as e:
                print(f"[TaskQueue Error] Failed to write task record: {e}")
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves task state from Redis."""
        if not self.redis:
            return None
        try:
            val = self.redis.get(self._get_key(task_id))
            return json.loads(val) if val else None
        except Exception:
            return None

    def update_progress(self, task_id: str, progress: float, msg: str = "", status: str = "RUNNING", error: Optional[str] = None):
        """Updates task progress percentage and status message."""
        task = self.get_task(task_id)
        if not task:
            return
        task["progress"] = min(max(progress, 0.0), 100.0)
        task["status"] = status
        task["msg"] = msg
        if error:
            task["error"] = error
        task["updated_at"] = time.time()

        if self.redis:
            try:
                self.redis.setex(self._get_key(task_id), self.ttl, json.dumps(task))
            except Exception as e:
                print(f"[TaskQueue Error] Failed to update progress: {e}")

    def cancel_task(self, task_id: str) -> bool:
        """Flags a task as CANCELLED."""
        task = self.get_task(task_id)
        if not task:
            return False
        task["status"] = "CANCELLED"
        task["msg"] = "Task cancelled by user."
        task["updated_at"] = time.time()
        if self.redis:
            try:
                self.redis.setex(self._get_key(task_id), self.ttl, json.dumps(task))
                return True
            except Exception:
                return False
        return True

    def is_cancelled(self, task_id: str) -> bool:
        """Checks if task was flagged for cancellation."""
        task = self.get_task(task_id)
        return bool(task and task.get("status") == "CANCELLED")

task_queue = AsyncTaskQueue()
