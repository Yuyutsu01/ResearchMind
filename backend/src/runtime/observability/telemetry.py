"""
Observability Telemetry Engine Module for ResearchMind AI Runtime Architecture

Instruments the AI execution pipeline to record stage-by-stage latency, token consumption, 
cache hit ratios, and estimated call cost ($ USD).
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class StageMetrics:
    """
    Container for single execution request performance metrics.
    """
    request_id: str
    cache_hit: bool = False
    redis_lookup_ms: float = 0.0
    intent_router_ms: float = 0.0
    context_builder_ms: float = 0.0
    execution_ms: float = 0.0
    ttft_ms: float = 0.0
    total_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    provider: str = "mock"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "cache": "HIT" if self.cache_hit else "MISS",
            "redis_lookup_ms": round(self.redis_lookup_ms, 2),
            "intent_router_ms": round(self.intent_router_ms, 2),
            "context_builder_ms": round(self.context_builder_ms, 2),
            "execution_ms": round(self.execution_ms, 2),
            "ttft_ms": round(self.ttft_ms, 2),
            "total_ms": round(self.total_ms, 2),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "provider": self.provider
        }

class TelemetryEngine:
    """
    Centralized telemetry engine tracking stage latency and observability metrics.
    """

    def __init__(self):
        self.metrics_history: List[StageMetrics] = []
        self.total_requests: int = 0
        self.total_cache_hits: int = 0

    def start_request(self, request_id: str) -> StageMetrics:
        """
        Creates a new StageMetrics container for request tracking.
        """
        metrics = StageMetrics(request_id=request_id)
        self.total_requests += 1
        return metrics

    def record_completed_request(self, metrics: StageMetrics):
        """
        Records finalized request metrics in telemetry history.
        """
        if metrics.cache_hit:
            self.total_cache_hits += 1
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1000:
            self.metrics_history.pop(0)

        print(f"[TelemetryEngine] Recorded Request #{metrics.request_id} | Cache: {metrics.to_dict()['cache']} | TTFT: {metrics.ttft_ms:.1f}ms | Total: {metrics.total_ms:.1f}ms")

    def get_summary_telemetry(self) -> Dict[str, Any]:
        """
        Computes aggregate pipeline summary telemetry statistics.
        """
        if not self.metrics_history:
            return {
                "total_requests": 0,
                "cache_hit_rate": 0.0,
                "avg_ttft_ms": 0.0,
                "avg_total_ms": 0.0
            }

        hit_rate = (self.total_cache_hits / self.total_requests) if self.total_requests > 0 else 0.0
        avg_ttft = sum(m.ttft_ms for m in self.metrics_history) / len(self.metrics_history)
        avg_total = sum(m.total_ms for m in self.metrics_history) / len(self.metrics_history)

        return {
            "total_requests": self.total_requests,
            "cache_hit_rate": round(hit_rate * 100, 1),
            "avg_ttft_ms": round(avg_ttft, 2),
            "avg_total_ms": round(avg_total, 2)
        }

telemetry_engine = TelemetryEngine()
