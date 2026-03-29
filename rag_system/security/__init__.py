"""Security module for RAG system."""

from .audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditEventSeverity,
    get_audit_logger,
    init_audit_logging,
)
from .middleware import (
    AuditMiddleware,
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
)
from .rate_limiter import (
    limiter,
    get_limiter,
    RateLimitMiddleware,
    RateLimitConfig,
    apply_rate_limits,
)
from .validators import (
    SearchQuery,
    FileUpload,
    DocumentId,
    InputValidator,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    MAX_QUERY_LENGTH,
    sanitize_html,
    sanitize_markdown,
)

__all__ = [
    # Audit logging
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditEventSeverity",
    "get_audit_logger",
    "init_audit_logging",
    # Middleware
    "AuditMiddleware",
    "SecurityHeadersMiddleware",
    "RequestSizeLimitMiddleware",
    # Rate limiting
    "limiter",
    "get_limiter",
    "RateLimitMiddleware",
    "RateLimitConfig",
    "apply_rate_limits",
    # Validation
    "SearchQuery",
    "FileUpload",
    "DocumentId",
    "InputValidator",
    "ALLOWED_EXTENSIONS",
    "MAX_FILE_SIZE",
    "MAX_QUERY_LENGTH",
    "sanitize_html",
    "sanitize_markdown",
]
