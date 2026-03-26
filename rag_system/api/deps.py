"""Dependencies for API routes to avoid circular imports."""

from typing import Optional
from fastapi import Request, Depends

from ..rag_engine import RAGEngine
from ..config import get_settings
from .security import SecurityMiddleware

# Global state
_rag_engine: Optional[RAGEngine] = None
_security_middleware: Optional[SecurityMiddleware] = None


def get_rag_engine() -> RAGEngine:
    """Get or create RAG engine."""
    global _rag_engine
    if _rag_engine is None:
        settings = get_settings()
        _rag_engine = RAGEngine(settings.library_dir)
    return _rag_engine


def get_security() -> SecurityMiddleware:
    """Get or create security middleware."""
    global _security_middleware
    if _security_middleware is None:
        _security_middleware = SecurityMiddleware.from_settings()
    return _security_middleware


async def get_api_key(request: Request) -> Optional[str]:
    """Extract API key from request headers."""
    settings = get_settings()
    header_name = settings.security.api_key_header
    return request.headers.get(header_name)


async def get_client_id(request: Request) -> str:
    """Get client identifier from request."""
    # Use X-Forwarded-For if behind proxy, else client host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
