import os
import time

_local_cache = {}
_local_expiry = {}

# Check redis availability
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_redis_client = None

try:
    import redis
    # test connection with low timeout
    _redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=1.0)
    _redis_client.ping()
    print("[Cache] Connected to Redis successfully.")
except Exception:
    _redis_client = None
    print("[Cache] Redis not available. Using local in-memory cache fallback.")

def set_val(key: str, value: str, expire_seconds: int = None):
    if _redis_client:
        try:
            _redis_client.set(key, value, ex=expire_seconds)
            return
        except Exception:
            pass
    # Fallback
    _local_cache[key] = value
    if expire_seconds:
        _local_expiry[key] = time.time() + expire_seconds
    else:
        _local_expiry[key] = None

def get_val(key: str) -> str:
    if _redis_client:
        try:
            val = _redis_client.get(key)
            if val is not None:
                return val.decode("utf-8")
        except Exception:
            pass
    # Fallback check
    if key in _local_cache:
        expiry = _local_expiry.get(key)
        if expiry and time.time() > expiry:
            # Expired
            _local_cache.pop(key, None)
            _local_expiry.pop(key, None)
            return None
        return _local_cache[key]
    return None

def delete_val(key: str):
    if _redis_client:
        try:
            _redis_client.delete(key)
            return
        except Exception:
            pass
    # Fallback
    _local_cache.pop(key, None)
    _local_expiry.pop(key, None)

def flush_all():
    global _local_cache, _local_expiry
    if _redis_client:
        try:
            _redis_client.flushdb()
            return
        except Exception:
            pass
    _local_cache = {}
    _local_expiry = {}
