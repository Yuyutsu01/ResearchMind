import time
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class MetricEntry:
    name: str
    duration: float
    success: bool = True
    metadata: Dict = field(default_factory=dict)

class Telemetry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Telemetry, cls).__new__(cls)
            cls._instance.metrics = []
            cls._instance.cache_hits = 0
            cls._instance.cache_misses = 0
        return cls._instance

    def record_metric(self, name: str, duration: float, success: bool = True, metadata: Dict = None):
        entry = MetricEntry(name=name, duration=duration, success=success, metadata=metadata or {})
        self.metrics.append(entry)
        print(f"[Telemetry] Recorded {name}: {duration:.2f}ms (Success: {success})")

    def record_cache_hit(self):
        self.cache_hits += 1
        print(f"[Telemetry] Cache Hit recorded.")

    def record_cache_miss(self):
        self.cache_misses += 1
        print(f"[Telemetry] Cache Miss recorded.")

    def get_summary(self):
        summary = {}
        unique_names = set(m.name for m in self.metrics)
        
        for name in unique_names:
            relevant = [m for m in self.metrics if m.name == name]
            avg_duration = sum(m.duration for m in relevant) / len(relevant)
            success_rate = sum(1 for m in relevant if m.success) / len(relevant)
            summary[name] = {
                "avg_duration_ms": round(avg_duration, 2),
                "success_rate": round(success_rate * 100, 2),
                "count": len(relevant)
            }
        
        total_cache_requests = self.cache_hits + self.cache_misses
        summary["cache"] = {
            "hit_rate": round((self.cache_hits / total_cache_requests * 100), 2) if total_cache_requests > 0 else 0,
            "hits": self.cache_hits,
            "misses": self.cache_misses
        }
        
        return summary

# Singleton instance
telemetry = Telemetry()
