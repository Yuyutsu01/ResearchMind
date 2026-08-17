import json
import time
from typing import List, Dict, Any, Optional
from src.adapters.db.redis_cache import redis_cache

class RedisSessionManager:
    """
    Manages active session metadata, agent state, running tasks queue, 
    and stream history inside Redis with TTL-based automatic cleanup.
    """
    def __init__(self):
        self.redis = redis_cache.client
        self.default_ttl = 86400  # 24 hours TTL for persistent sessions

    def _get_key(self, session_id: int, suffix: str) -> str:
        return f"session:{session_id}:{suffix}"

    def register_active_connection(self, session_id: int, connection_id: str):
        """Registers a live websocket client in the session's active connections set."""
        if not self.redis:
            return
        try:
            key = self._get_key(session_id, "connections")
            self.redis.sadd(key, connection_id)
            self.redis.expire(key, self.default_ttl)
            print(f"[Redis Session] Registered connection '{connection_id}' to Session #{session_id}.")
        except Exception as e:
            print(f"[Redis Session Error] Failed to register connection: {e}")

    def unregister_active_connection(self, session_id: int, connection_id: str):
        """Removes a websocket client from the session's active connections set."""
        if not self.redis:
            return
        try:
            key = self._get_key(session_id, "connections")
            self.redis.srem(key, connection_id)
            # If no active connections remain, we keep the data but let it expire via standard TTL
        except Exception as e:
            print(f"[Redis Session Error] Failed to unregister connection: {e}")

    def get_active_connections_count(self, session_id: int) -> int:
        """Returns the number of active clients for the session."""
        if not self.redis:
            return 0
        try:
            key = self._get_key(session_id, "connections")
            return self.redis.scard(key)
        except Exception:
            return 0

    def push_priority_page(self, session_id: int, page_num: int):
        """Pushes a page index requested by the user viewport onto the Redis queue."""
        if not self.redis:
            return
        try:
            key = self._get_key(session_id, "page_queue")
            self.redis.rpush(key, str(page_num))
            self.redis.expire(key, self.default_ttl)
            print(f"[Redis Session] Queued priority Page #{page_num} for Session #{session_id}.")
        except Exception as e:
            print(f"[Redis Session Error] Failed to push page priority: {e}")

    def pop_priority_page(self, session_id: int) -> Optional[int]:
        """Pops a page from the session's priority queue."""
        if not self.redis:
            return None
        try:
            key = self._get_key(session_id, "page_queue")
            val = self.redis.lpop(key)
            return int(val) if val else None
        except Exception as e:
            print(f"[Redis Session Error] Failed to pop page priority: {e}")
            return None

    def is_priority_queue_empty(self, session_id: int) -> bool:
        """Checks if the priority queue has items."""
        if not self.redis:
            return True
        try:
            key = self._get_key(session_id, "page_queue")
            return self.redis.llen(key) == 0
        except Exception:
            return True

    def save_agent_state(self, session_id: int, state: Dict[str, Any]):
        """Persists agent workspace configurations or state JSON."""
        if not self.redis:
            return
        try:
            key = self._get_key(session_id, "agent_state")
            self.redis.setex(key, self.default_ttl, json.dumps(state))
        except Exception as e:
            print(f"[Redis Session Error] Failed to save agent state: {e}")

    def get_agent_state(self, session_id: int) -> Dict[str, Any]:
        """Retrieves persisted agent state or configuration defaults."""
        if not self.redis:
            return {}
        try:
            key = self._get_key(session_id, "agent_state")
            val = self.redis.get(key)
            return json.loads(val) if val else {}
        except Exception:
            return {}

    def append_stream_history(self, session_id: int, selection_text: str, result_summary: str):
        """Saves interaction selection stream logs to Redis."""
        if not self.redis:
            return
        try:
            key = self._get_key(session_id, "stream_history")
            entry = json.dumps({"text": selection_text, "summary": result_summary, "timestamp": time.time()})
            self.redis.rpush(key, entry)
            self.redis.expire(key, self.default_ttl)
        except Exception as e:
            print(f"[Redis Session Error] Failed to append stream history: {e}")

    def get_stream_history(self, session_id: int) -> List[Dict[str, Any]]:
        """Retrieves all previous selection highlights from Redis."""
        if not self.redis:
            return []
        try:
            key = self._get_key(session_id, "stream_history")
            items = self.redis.lrange(key, 0, -1)
            return [json.loads(i) for i in items]
        except Exception:
            return []

    def set_task_status(self, session_id: int, step: str, msg: str, page: Optional[int] = None):
        """Persists the running status/progress details of the ingestion worker."""
        if not self.redis:
            return
        try:
            key = self._get_key(session_id, "task_status")
            status_data = {"step": step, "msg": msg, "page": page}
            self.redis.setex(key, self.default_ttl, json.dumps(status_data))
        except Exception as e:
            print(f"[Redis Session Error] Failed to write task status: {e}")

    def get_task_status(self, session_id: int) -> Dict[str, Any]:
        """Retrieves the last cached progress update of the background ingestion worker."""
        if not self.redis:
            return {}
        try:
            key = self._get_key(session_id, "task_status")
            val = self.redis.get(key)
            return json.loads(val) if val else {}
        except Exception:
            return {}

    def clear_session_state(self, session_id: int):
        """Cleans up all Redis keys associated with a session (e.g. on session deletion)."""
        if not self.redis:
            return
        try:
            suffixes = ["connections", "page_queue", "agent_state", "stream_history", "task_status"]
            keys = [self._get_key(session_id, s) for s in suffixes]
            self.redis.delete(*keys)
            print(f"[Redis Session] Cleared session #{session_id} state.")
        except Exception as e:
            print(f"[Redis Session Error] Failed to clear session state: {e}")

redis_session = RedisSessionManager()
