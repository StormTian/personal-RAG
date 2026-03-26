"""Base exception classes for RAG system."""

from typing import Any, Dict, List, Optional


class RAGError(Exception):
    """Base exception for all RAG system errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self._get_default_error_code()
        self.details = details or {}
        self.status_code = status_code
    
    def _get_default_error_code(self) -> str:
        return "INTERNAL_ERROR"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


class ConfigurationError(RAGError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            status_code=500,
        )


class ValidationError(RAGError):
    """Input validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details or {},
            status_code=400,
        )
        if field:
            self.details["field"] = field


class AuthenticationError(RAGError):
    """Authentication/authorization errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            status_code=401,
        )


class RateLimitError(RAGError):
    """Rate limit exceeded errors."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details or {},
            status_code=429,
        )
        if retry_after:
            self.details["retry_after"] = retry_after


class ResourceNotFoundError(RAGError):
    """Resource not found errors."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            error_code="RESOURCE_NOT_FOUND",
            details=details or {},
            status_code=404,
        )
        self.details["resource_type"] = resource_type
        self.details["resource_id"] = resource_id


class ResourceExistsError(RAGError):
    """Resource already exists errors."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource_type} already exists: {resource_id}",
            error_code="RESOURCE_EXISTS",
            details=details or {},
            status_code=409,
        )
        self.details["resource_type"] = resource_type
        self.details["resource_id"] = resource_id


class ProcessingError(RAGError):
    """Document/text processing errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            details=details or {},
            status_code=500,
        )
        if operation:
            self.details["operation"] = operation


class EmbeddingError(RAGError):
    """Embedding generation errors."""
    
    def __init__(self, message: str, backend: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EMBEDDING_ERROR",
            details=details or {},
            status_code=500,
        )
        if backend:
            self.details["backend"] = backend


class RetrievalError(RAGError):
    """Document retrieval errors."""
    
    def __init__(self, message: str, query: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RETRIEVAL_ERROR",
            details=details or {},
            status_code=500,
        )
        if query:
            self.details["query"] = query


class ExternalServiceError(RAGError):
    """External API/service errors."""
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details or {},
            status_code=status_code,
        )
        if service:
            self.details["service"] = service


class CacheError(RAGError):
    """Cache operation errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details or {},
            status_code=500,
        )
        if operation:
            self.details["operation"] = operation


# File-related exceptions

class FileValidationError(RAGError):
    """File validation errors."""
    
    def __init__(self, message: str, filename: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_VALIDATION_ERROR",
            details=details or {},
            status_code=400,
        )
        if filename:
            self.details["filename"] = filename


class InvalidFileTypeError(FileValidationError):
    """Invalid file type errors."""
    
    def __init__(self, filename: str, allowed_extensions: Optional[List[str]] = None, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid file type: {filename}"
        super().__init__(
            message=message,
            filename=filename,
            details=details or {},
        )
        self.error_code = "INVALID_FILE_TYPE"
        if allowed_extensions:
            self.details["allowed_extensions"] = allowed_extensions


class FileTooLargeError(FileValidationError):
    """File too large errors."""
    
    def __init__(self, filename: str, file_size: int, max_size: int, details: Optional[Dict[str, Any]] = None):
        message = f"File too large: {filename} ({file_size} bytes, max: {max_size} bytes)"
        super().__init__(
            message=message,
            filename=filename,
            details=details or {},
        )
        self.error_code = "FILE_TOO_LARGE"
        self.details["file_size"] = file_size
        self.details["max_size"] = max_size


class FileSecurityError(FileValidationError):
    """File security check errors."""
    
    def __init__(self, message: str, filename: Optional[str] = None, reason: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            filename=filename,
            details=details or {},
        )
        self.error_code = "FILE_SECURITY_ERROR"
        self.status_code = 403
        if reason:
            self.details["reason"] = reason
