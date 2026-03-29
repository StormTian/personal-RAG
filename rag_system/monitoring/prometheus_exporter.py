"""Prometheus metrics exporter for RAG system."""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional

from .metrics import get_metrics_collector


# Service information
SERVICE_INFO = Info('rag_service', 'RAG service information')

# Request metrics
REQUEST_COUNT = Counter(
    'rag_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'rag_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Search operation metrics
SEARCH_DURATION = Histogram(
    'rag_search_duration_seconds',
    'Search operation duration',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

SEARCH_HITS = Histogram(
    'rag_search_hits',
    'Number of search hits returned',
    buckets=[1, 3, 5, 10, 20, 50]
)

# Index metrics
INDEX_DOCUMENTS = Gauge(
    'rag_index_documents_total',
    'Number of documents in index'
)

INDEX_CHUNKS = Gauge(
    'rag_index_chunks_total',
    'Number of chunks in index'
)

INDEX_OPERATIONS = Counter(
    'rag_index_operations_total',
    'Total index operations',
    ['operation', 'status']
)

# Embedding metrics
EMBEDDING_DURATION = Histogram(
    'rag_embedding_duration_seconds',
    'Embedding generation duration',
    ['backend'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

EMBEDDING_ERRORS = Counter(
    'rag_embedding_errors_total',
    'Total embedding errors',
    ['backend']
)

# Cache metrics
CACHE_HITS = Counter(
    'rag_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'rag_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Query metrics
QUERY_COUNT = Counter(
    'rag_queries_total',
    'Total number of queries processed',
    ['status']
)

QUERY_LATENCY = Histogram(
    'rag_query_latency_seconds',
    'Query processing latency',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)


class PrometheusExporter:
    """Prometheus metrics exporter."""
    
    def __init__(self):
        self.initialized = False
    
    def init(self, version: str = "1.0.0"):
        """Initialize Prometheus metrics."""
        if not self.initialized:
            SERVICE_INFO.info({'version': version})
            self.initialized = True
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_search(self, duration: float, hits: int):
        """Record search metrics."""
        SEARCH_DURATION.observe(duration)
        SEARCH_HITS.observe(hits)
    
    def record_embedding(self, backend: str, duration: float, error: bool = False):
        """Record embedding metrics."""
        EMBEDDING_DURATION.labels(backend=backend).observe(duration)
        if error:
            EMBEDDING_ERRORS.labels(backend=backend).inc()
    
    def update_index_metrics(self, documents: int, chunks: int):
        """Update index metrics."""
        INDEX_DOCUMENTS.set(documents)
        INDEX_CHUNKS.set(chunks)
    
    def record_index_operation(self, operation: str, status: str):
        """Record index operation."""
        INDEX_OPERATIONS.labels(operation=operation, status=status).inc()
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit."""
        CACHE_HITS.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss."""
        CACHE_MISSES.labels(cache_type=cache_type).inc()
    
    def record_query(self, status: str, latency: float):
        """Record query metrics."""
        QUERY_COUNT.labels(status=status).inc()
        QUERY_LATENCY.observe(latency)
    
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format."""
        return generate_latest()


# Global exporter instance
_prometheus_exporter: Optional[PrometheusExporter] = None


def get_prometheus_exporter() -> PrometheusExporter:
    """Get or create global Prometheus exporter."""
    global _prometheus_exporter
    if _prometheus_exporter is None:
        _prometheus_exporter = PrometheusExporter()
    return _prometheus_exporter


def init_prometheus(version: str = "1.0.0"):
    """Initialize Prometheus metrics."""
    exporter = get_prometheus_exporter()
    exporter.init(version)


# Export constants
__all__ = [
    'PrometheusExporter',
    'get_prometheus_exporter',
    'init_prometheus',
    'CONTENT_TYPE_LATEST',
]
