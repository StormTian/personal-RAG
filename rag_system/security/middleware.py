"""Security middleware for RAG service."""

from datetime import datetime
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from rag_system.security.audit_logger import (
    get_audit_logger,
    AuditLogger,
    AuditEventSeverity,
)
from rag_system.monitoring.tracing import get_tracer


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to audit all requests."""
    
    def __init__(self, app: ASGIApp, audit_logger: Optional[AuditLogger] = None):
        super().__init__(app)
        self.audit_logger = audit_logger or get_audit_logger()
    
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        
        # Get request info
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        path = request.url.path
        method = request.method
        
        try:
            response = await call_next(request)
            
            # Log based on endpoint
            if "/search" in path and method == "POST":
                await self._log_search(request, response, ip_address, user_agent)
            elif "/upload" in path and method == "POST":
                await self._log_upload(request, response, ip_address, user_agent)
            elif "/files/" in path and method == "DELETE":
                await self._log_delete(request, response, ip_address, user_agent)
            
            return response
            
        except Exception as e:
            # Log error
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.audit_logger.log_security_event(
                action="request_error",
                ip_address=ip_address,
                details={
                    "path": path,
                    "method": method,
                    "error": str(e),
                },
                severity=AuditEventSeverity.MEDIUM,
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check X-Forwarded-For header
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    async def _log_search(self, request: Request, response: Response, ip_address: str, user_agent: str):
        """Log search request."""
        try:
            body = await request.json()
            query = body.get("query", "")
            
            self.audit_logger.log_search(
                query=query,
                ip_address=ip_address,
                status="success" if response.status_code == 200 else "failure",
            )
        except Exception:
            pass  # Don't fail if logging fails
    
    async def _log_upload(self, request: Request, response: Response, ip_address: str, user_agent: str):
        """Log upload request."""
        try:
            if response.status_code == 200:
                body = await request.json()
                filename = body.get("filename", "unknown")
                file_size = body.get("size", 0)
                
                self.audit_logger.log_upload(
                    filename=filename,
                    file_size=file_size,
                    ip_address=ip_address,
                    status="success",
                )
        except Exception:
            pass
    
    async def _log_delete(self, request: Request, response: Response, ip_address: str, user_agent: str):
        """Log delete request."""
        try:
            filename = request.path_params.get("filename", "unknown")
            
            self.audit_logger.log_delete(
                filename=filename,
                ip_address=ip_address,
                status="success" if response.status_code == 200 else "failure",
            )
        except Exception:
            pass


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # CSP Header (can be customized)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""
    
    def __init__(self, app: ASGIApp, max_size: int = 100 * 1024 * 1024):  # 100MB
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=413,
                        content={"error": "Request body too large", "max_size": self.max_size},
                    )
            except ValueError:
                pass
        
        return await call_next(request)
