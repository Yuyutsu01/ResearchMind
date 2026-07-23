import os
import time
from typing import Optional, Dict, Any

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Prometheus Metrics Definitions
if PROMETHEUS_AVAILABLE:
    API_REQUESTS_TOTAL = Counter("api_requests_total", "Total HTTP requests processed", ["method", "endpoint", "status"])
    API_REQUEST_DURATION = Histogram("api_request_duration_seconds", "HTTP request latency in seconds", ["method", "endpoint"])

    LLM_REQUESTS_TOTAL = Counter("llm_requests_total", "Total LLM API requests", ["provider", "model"])
    LLM_REQUEST_DURATION = Histogram("llm_request_duration_seconds", "LLM request latency in seconds", ["provider", "model"])
    LLM_TOKENS_TOTAL = Counter("llm_tokens_total", "Total LLM tokens processed", ["provider", "model", "token_type"])

    AGENT_FAILURES_TOTAL = Counter("agent_failures_total", "Total swarm agent task failures", ["agent_name"])
    CACHE_HITS_TOTAL = Counter("cache_hits_total", "Total cache hits", ["cache_type"])
    CACHE_MISSES_TOTAL = Counter("cache_misses_total", "Total cache misses", ["cache_type"])

    DB_QUERY_DURATION = Histogram("db_query_duration_seconds", "Database query execution duration")
    EMBEDDING_DURATION = Histogram("embedding_duration_seconds", "Embedding vector calculation duration")

class TelemetryEngine:
    """
    Unified Observability and Telemetry Collector integrating 
    Prometheus metrics, latency tracking, token cost counters, and Sentry hooks.
    """
    def __init__(self):
        self.sentry_dsn = os.environ.get("SENTRY_DSN")
        if self.sentry_dsn:
            try:
                import sentry_sdk
                sentry_sdk.init(dsn=self.sentry_dsn, traces_sample_rate=1.0)
                print("[Telemetry] Sentry exception tracking initialized successfully.")
            except Exception as e:
                print(f"[Telemetry Warning] Failed to initialize Sentry: {e}")

    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        if PROMETHEUS_AVAILABLE:
            API_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=str(status)).inc()
            API_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    def record_llm_request(self, provider: str, model: str, duration: float, prompt_tokens: int = 0, completion_tokens: int = 0):
        if PROMETHEUS_AVAILABLE:
            LLM_REQUESTS_TOTAL.labels(provider=provider, model=model).inc()
            LLM_REQUEST_DURATION.labels(provider=provider, model=model).observe(duration)
            if prompt_tokens > 0:
                LLM_TOKENS_TOTAL.labels(provider=provider, model=model, token_type="prompt").inc(prompt_tokens)
            if completion_tokens > 0:
                LLM_TOKENS_TOTAL.labels(provider=provider, model=model, token_type="completion").inc(completion_tokens)

    def record_agent_failure(self, agent_name: str):
        if PROMETHEUS_AVAILABLE:
            AGENT_FAILURES_TOTAL.labels(agent_name=agent_name).inc()

    def record_cache_hit(self, cache_type: str = "redis_l1"):
        if PROMETHEUS_AVAILABLE:
            CACHE_HITS_TOTAL.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str = "redis_l1"):
        if PROMETHEUS_AVAILABLE:
            CACHE_MISSES_TOTAL.labels(cache_type=cache_type).inc()

    def record_db_query(self, duration: float):
        if PROMETHEUS_AVAILABLE:
            DB_QUERY_DURATION.observe(duration)

    def record_embedding(self, duration: float):
        if PROMETHEUS_AVAILABLE:
            EMBEDDING_DURATION.observe(duration)

    def get_metrics_content(self) -> tuple[bytes, str]:
        """Returns raw Prometheus metrics content and header."""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(), CONTENT_TYPE_LATEST
        return b"# Prometheus client not available\n", "text/plain"

telemetry = TelemetryEngine()
