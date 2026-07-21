import os
import json
import redis
from typing import Optional, Any

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

class RedisCache:
    def __init__(self):
        try:
            print(f"[Redis Cache] Connecting to redis://{REDIS_HOST}:{REDIS_PORT}...")
            self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
            self.client.ping()
            print("[Redis Cache] Connected successfully.")
        except Exception as e:
            print(f"[Redis Cache Warning] Redis offline: {e}")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """Gets a cached JSON item from Redis."""
        if not self.client:
            return None
        try:
            val = self.client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            print(f"[Redis Get Error] Failed to read key '{key}': {e}")
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Caches a serialized JSON item inside Redis with TTL."""
        if not self.client:
            return
        try:
            self.client.setex(key, ttl_seconds, json.dumps(value))
        except Exception as e:
            print(f"[Redis Set Error] Failed to cache key '{key}': {e}")

# Singleton Instance
redis_cache = RedisCache()
