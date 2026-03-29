"""Rate limiting for RAG service."""

import time
from typing import Optional, Callable
from functools import wraps
from datetime import datetime

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from rag_system.config.settings import get_settings
from rag_system.security.audit_logger import get_audit_logger

settings = get_settings()

# Create rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default: 100 requests per minute
)


def get_limiter() -> Limiter:
    """Get rate limiter instance."""
    return limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to track and limit request rates."""
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests: dict = {}  # Simple in-memory rate tracking
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        path = request.url.path
        
        # Skip rate limiting for health checks
        if path in ["/health", "/ready", "/live"]:
            return await call_next(request)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, path):
            from fastapi.responses import JSONResponse
            
            # Log rate limit hit
            audit_logger = get_audit_logger()
            audit_logger.log_security_event(
                action="rate_limit_exceeded",
                ip_address=client_ip,
                details={
                    "path": path,
                    "method": request.method,
                    "limit": f"{self.requests_per_minute}/minute",
                },
                severity=AuditEventSeverity.MEDIUM,
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60,
                },
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str, path: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        key = f"{client_ip}:{path}"
        
        # Get or create request history
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests (older than 60 seconds)
        cutoff = now - 60
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= self.requests_per_minute:
            return True
        
        # Record this request
        self.requests[key].append(now)
        return False


# Endpoint-specific rate limits
def search_limit():
    """Rate limit for search endpoint."""
    return "30/minute"


def upload_limit():
    """Rate limit for upload endpoint."""
    return "10/minute"


def query_limit():
    """Rate limit for query endpoint."""
    return "60/minute"


def api_limit():
    """Rate limit for general API."""
    return "100/minute"


class RateLimitConfig:
    """Rate limit configuration."""
    
    SEARCH = "30/minute"
    UPLOAD = "10/minute"
    QUERY = "60/minute"
    DELETE = "20/minute"
    HEALTH = "1000/minute"  # High limit for health checks
    DEFAULT = "100/minute"


def apply_rate_limits(app):
    """Apply rate limits to FastAPI app."""
    # Add limiter to app state
    app.state.limiter = limiter
    
    # Add exception handler for rate limit exceeded
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        from fastapi.responses import JSONResponse
        
        client_ip = get_remote_address(request)
        
        # Log rate limit hit
        audit_logger = get_audit_logger()
        audit_logger.log_security_event(
            action="rate_limit_exceeded",
            ip_address=client_ip,
            details={
                "path": request.url.path,
                "method": request.method,
                "limit": str(exc),
            },
            severity=AuditEventSeverity.MEDIUM,
        )
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": 60,
            },
        )
