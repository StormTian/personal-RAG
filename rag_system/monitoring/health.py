"""Health check system."""

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    timestamp: float
    details: Dict[str, object] = field(default_factory=dict)
    latency_ms: float = 0.0


class HealthCheck:
    """Health check manager."""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._results: Dict[str, HealthCheckResult] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._check_thread: Optional[threading.Thread] = None
        self._last_check_time: float = 0.0
    
    def register_check(
        self,
        name: str,
        check_fn: Callable[[], HealthCheckResult],
    ) -> None:
        """Register a health check."""
        with self._lock:
            self._checks[name] = check_fn
    
    def check(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks."""
        results = {}
        with self._lock:
            for name, check_fn in self._checks.items():
                start = time.time()
                try:
                    result = check_fn()
                    result.latency_ms = (time.time() - start) * 1000
                except Exception as e:
                    result = HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {str(e)}",
                        timestamp=time.time(),
                    )
                results[name] = result
                self._results[name] = result
        
        self._last_check_time = time.time()
        return results
    
    def get_status(self) -> Dict[str, object]:
        """Get overall health status."""
        # Refresh checks if stale
        if time.time() - self._last_check_time > self.check_interval:
            self.check()
        
        with self._lock:
            if not self._results:
                return {
                    "status": HealthStatus.UNKNOWN.value,
                    "checks": {},
                    "timestamp": time.time(),
                }
            
            # Determine overall status
            statuses = [r.status for r in self._results.values()]
            if HealthStatus.UNHEALTHY in statuses:
                overall = HealthStatus.UNHEALTHY
            elif HealthStatus.DEGRADED in statuses:
                overall = HealthStatus.DEGRADED
            else:
                overall = HealthStatus.HEALTHY
            
            return {
                "status": overall.value,
                "checks": {
                    name: {
                        "status": result.status.value,
                        "message": result.message,
                        "latency_ms": result.latency_ms,
                        "details": result.details,
                    }
                    for name, result in self._results.items()
                },
                "timestamp": time.time(),
            }
    
    def start_monitoring(self) -> None:
        """Start background health check monitoring."""
        if self._check_thread is not None:
            return
        
        def monitor():
            while not self._stop_event.is_set():
                self.check()
                self._stop_event.wait(self.check_interval)
        
        self._check_thread = threading.Thread(target=monitor, daemon=True)
        self._check_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._stop_event.set()
        if self._check_thread:
            self._check_thread.join(timeout=1.0)
            self._check_thread = None


def create_basic_health_checks(
    rag_engine: object,
    embedding_backend: object,
    reranker_backend: object,
) -> Dict[str, Callable[[], HealthCheckResult]]:
    """Create basic health checks for RAG system."""
    
    def check_library():
        try:
            stats = rag_engine.stats()
            return HealthCheckResult(
                name="library",
                status=HealthStatus.HEALTHY,
                message=f"Library contains {stats.get('documents', 0)} documents",
                timestamp=time.time(),
                details={"stats": stats},
            )
        except Exception as e:
            return HealthCheckResult(
                name="library",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                timestamp=time.time(),
            )
    
    def check_embedding():
        try:
            # Test embedding with a simple query
            test_embedding = embedding_backend.embed_query("test")
            return HealthCheckResult(
                name="embedding",
                status=HealthStatus.HEALTHY,
                message=f"Embedding backend '{embedding_backend.name}' is operational",
                timestamp=time.time(),
                details={"backend": embedding_backend.name, "dimensions": len(test_embedding)},
            )
        except Exception as e:
            return HealthCheckResult(
                name="embedding",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                timestamp=time.time(),
            )
    
    def check_reranker():
        try:
            return HealthCheckResult(
                name="reranker",
                status=HealthStatus.HEALTHY,
                message=f"Reranker backend '{reranker_backend.name}' is operational",
                timestamp=time.time(),
                details={"backend": reranker_backend.name, "strategy": reranker_backend.strategy},
            )
        except Exception as e:
            return HealthCheckResult(
                name="reranker",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                timestamp=time.time(),
            )
    
    return {
        "library": check_library,
        "embedding": check_embedding,
        "reranker": check_reranker,
    }


# Global health check instance
_health_checker: Optional[HealthCheck] = None


def get_health_checker() -> HealthCheck:
    """Get or create global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthCheck()
    return _health_checker
