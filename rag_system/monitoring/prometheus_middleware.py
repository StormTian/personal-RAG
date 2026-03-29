"""Prometheus metrics middleware for FastAPI."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from rag_system.monitoring.prometheus_exporter import get_prometheus_exporter


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to record Prometheus metrics for requests."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            exporter = get_prometheus_exporter()
            exporter.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration=duration
            )
        
        return response
