"""File-related exceptions for RAG system."""

from typing import Any, Dict, Optional

from .base import RAGError


class InvalidFileTypeError(RAGError):
    """Invalid or unsupported file type error."""
    
    def __init__(
        self,
        filename: str,
        allowed_extensions: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        extensions = allowed_extensions or ['.md', '.markdown', '.txt', '.doc', '.docx', '.pdf']
        message = f"Invalid file type: '{filename}'. Allowed types: {', '.join(extensions)}"
        
        super().__init__(
            message=message,
            error_code="INVALID_FILE_TYPE",
            details=details or {},
            status_code=415,  # Unsupported Media Type
        )
        self.details["filename"] = filename
        self.details["allowed_extensions"] = extensions


class FileTooLargeError(RAGError):
    """File size exceeds maximum allowed size error."""
    
    def __init__(
        self,
        filename: str,
        file_size: int,
        max_size: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        # Convert to human-readable format
        file_size_mb = file_size / (1024 * 1024)
        max_size_mb = max_size / (1024 * 1024)
        
        message = (
            f"File too large: '{filename}' ({file_size_mb:.2f}MB). "
            f"Maximum allowed: {max_size_mb:.0f}MB"
        )
        
        super().__init__(
            message=message,
            error_code="FILE_TOO_LARGE",
            details=details or {},
            status_code=413,  # Payload Too Large
        )
        self.details["filename"] = filename
        self.details["file_size_bytes"] = file_size
        self.details["max_size_bytes"] = max_size
        self.details["file_size_mb"] = round(file_size_mb, 2)
        self.details["max_size_mb"] = round(max_size_mb, 2)


class FileSecurityError(RAGError):
    """File security violation error (path traversal, dangerous filename, etc.)."""
    
    def __init__(
        self,
        filename: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"File security error for '{filename}': {reason}"
        
        super().__init__(
            message=message,
            error_code="FILE_SECURITY_VIOLATION",
            details=details or {},
            status_code=400,  # Bad Request
        )
        self.details["filename"] = filename
        self.details["security_reason"] = reason


class FileNotFoundError(RAGError):
    """File not found error."""
    
    def __init__(
        self,
        filename: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"File not found: '{filename}'"
        
        super().__init__(
            message=message,
            error_code="FILE_NOT_FOUND",
            details=details or {},
            status_code=404,
        )
        self.details["filename"] = filename


class FileProcessingError(RAGError):
    """File processing/parsing error."""
    
    def __init__(
        self,
        filename: str,
        operation: str,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Error processing file '{filename}' during {operation}"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details=details or {},
            status_code=500,
        )
        self.details["filename"] = filename
        self.details["operation"] = operation


class DuplicateFileError(RAGError):
    """Duplicate file upload error."""
    
    def __init__(
        self,
        filename: str,
        existing_file_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"File already exists: '{filename}'"
        
        super().__init__(
            message=message,
            error_code="DUPLICATE_FILE",
            details=details or {},
            status_code=409,  # Conflict
        )
        self.details["filename"] = filename
        if existing_file_id:
            self.details["existing_file_id"] = existing_file_id
