"""Metrics collection for performance monitoring."""

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    embedding_time_ms: float = 0.0
    retrieval_time_ms: float = 0.0
    rerank_time_ms: float = 0.0
    total_time_ms: float = 0.0
    chunk_count: int = 0
    document_count: int = 0
    query_count: int = 0
    error_count: int = 0
    cache_hit_rate: float = 0.0


@dataclass
class MetricPoint:
    """Single metric data point."""
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Thread-safe metrics collector."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def record(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value."""
        with self._lock:
            point = MetricPoint(
                value=value,
                timestamp=time.time(),
                tags=tags or {},
            )
            self._metrics[metric_name].append(point)
            
            # Trim history if needed
            if len(self._metrics[metric_name]) > self.max_history:
                self._metrics[metric_name] = self._metrics[metric_name][-self.max_history:]
    
    def increment(self, counter_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter."""
        with self._lock:
            key = f"{counter_name}:{self._tags_to_str(tags)}"
            self._counters[key] += value
    
    def gauge(self, gauge_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge value."""
        with self._lock:
            key = f"{gauge_name}:{self._tags_to_str(tags)}"
            self._gauges[key] = value
    
    def _tags_to_str(self, tags: Optional[Dict[str, str]]) -> str:
        """Convert tags dict to string."""
        if not tags:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
    
    def get_metrics(self, metric_name: str) -> List[MetricPoint]:
        """Get all values for a metric."""
        with self._lock:
            return list(self._metrics.get(metric_name, []))
    
    def get_average(self, metric_name: str, window: int = 100) -> float:
        """Get average of recent values."""
        with self._lock:
            values = self._metrics.get(metric_name, [])
            if not values:
                return 0.0
            recent = values[-window:]
            return sum(p.value for p in recent) / len(recent)
    
    def get_counter(self, counter_name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get counter value."""
        with self._lock:
            key = f"{counter_name}:{self._tags_to_str(tags)}"
            return self._counters[key]
    
    def get_gauge(self, gauge_name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        with self._lock:
            key = f"{gauge_name}:{self._tags_to_str(tags)}"
            return self._gauges.get(key, 0.0)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        with self._lock:
            summary = {
                "averages": {
                    name: self.get_average(name)
                    for name in self._metrics.keys()
                },
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }
            return summary
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
    
    @contextmanager
    def time_operation(self, operation: str, tags: Optional[Dict[str, str]] = None):
        """Context manager to time an operation."""
        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            self.record(f"{operation}_time_ms", duration_ms, tags)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
