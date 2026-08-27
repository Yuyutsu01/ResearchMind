"""
Redis Response & Context Caching Module for ResearchMind Swarm Architecture (Phase 6 & 7)

Provides sub-10ms Redis cache retrieval for repeated selection queries and 
cached SharedContext structures, returning cache hits in < 100ms.
"""

import hashlib
from typing import Dict, Any, Optional
from src.adapters.db.redis_cache import redis_cache
from src.domain.swarm.context_builder import SharedContext

class ResponseCache:
    """
    Manages Redis response and context caching.
    """

    def _hash_selection(self, session_id: int, selection_text: str, reading_level: str = "") -> str:
        raw = f"{session_id}:{selection_text.strip()}:{reading_level.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def get_cached_response(self, session_id: int, selection_text: str, reading_level: str = "") -> Optional[Dict[str, Any]]:
        """
        Retrieves pre-computed response markdown payload from Redis cache.
        """
        key_hash = self._hash_selection(session_id, selection_text, reading_level)
        cache_key = f"cache:response:{session_id}:{key_hash}"
        cached = redis_cache.get(cache_key)
        if cached:
            print(f"[ResponseCache] HIT for key '{cache_key}'")
            return cached
        print(f"[ResponseCache] MISS for key '{cache_key}'")
        return None

    def set_cached_response(
        self, 
        session_id: int, 
        selection_text: str, 
        response_payload: Dict[str, Any], 
        reading_level: str = "", 
        ttl: int = 86400
    ):
        """
        Caches finalized response markdown payload in Redis with 24-hour TTL.
        """
        key_hash = self._hash_selection(session_id, selection_text, reading_level)
        cache_key = f"cache:response:{session_id}:{key_hash}"
        redis_cache.set(cache_key, response_payload, ttl_seconds=ttl)
        print(f"[ResponseCache] Cached response payload at key '{cache_key}' (TTL: {ttl}s)")

    def get_cached_context(self, session_id: int, selection_text: str) -> Optional[SharedContext]:
        """
        Retrieves cached SharedContext dataclass from Redis.
        """
        key_hash = self._hash_selection(session_id, selection_text)
        cache_key = f"cache:context:{session_id}:{key_hash}"
        cached_dict = redis_cache.get(cache_key)
        if cached_dict:
            print(f"[ResponseCache] Context HIT for key '{cache_key}'")
            return SharedContext(**cached_dict)
        return None

    def set_cached_context(self, session_id: int, selection_text: str, context: SharedContext, ttl: int = 86400):
        """
        Caches SharedContext in Redis.
        """
        key_hash = self._hash_selection(session_id, selection_text)
        cache_key = f"cache:context:{session_id}:{key_hash}"
        redis_cache.set(cache_key, context.to_dict(), ttl_seconds=ttl)

response_cache = ResponseCache()
