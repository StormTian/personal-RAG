"""Custom exceptions for RAG system."""

from .base import (
    RAGError,
    ConfigurationError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ResourceExistsError,
    ProcessingError,
    EmbeddingError,
    RetrievalError,
    ExternalServiceError,
    CacheError,
)
from .file_exceptions import (
    InvalidFileTypeError,
    FileTooLargeError,
    FileSecurityError,
    FileNotFoundError,
    FileProcessingError,
    DuplicateFileError,
)
from .handlers import (
    ExceptionHandler,
    GlobalExceptionHandler,
    format_error_response,
    format_error_for_logging,
)

__all__ = [
    "RAGError",
    "ConfigurationError",
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
    "ResourceNotFoundError",
    "ResourceExistsError",
    "ProcessingError",
    "EmbeddingError",
    "RetrievalError",
    "ExternalServiceError",
    "CacheError",
    "InvalidFileTypeError",
    "FileTooLargeError",
    "FileSecurityError",
    "FileNotFoundError",
    "FileProcessingError",
    "DuplicateFileError",
    "ExceptionHandler",
    "GlobalExceptionHandler",
    "format_error_response",
    "format_error_for_logging",
]
