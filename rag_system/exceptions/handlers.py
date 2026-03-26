"""Exception handlers and utilities."""

import logging
import traceback
from typing import Any, Callable, Dict, Optional, Type

from .base import RAGError

logger = logging.getLogger(__name__)


def format_error_response(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """Format exception for API response."""
    if isinstance(error, RAGError):
        response = error.to_dict()
    else:
        response = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(error) or "An unexpected error occurred",
                "details": {},
            }
        }
    
    if include_traceback:
        response["error"]["traceback"] = traceback.format_exc()
    
    return response


def format_error_for_logging(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format exception for structured logging."""
    log_data = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    
    if isinstance(error, RAGError):
        log_data["error_code"] = error.error_code
        log_data["status_code"] = error.status_code
        log_data["details"] = error.details
    
    if context:
        log_data["context"] = context
    
    return log_data


class ExceptionHandler:
    """Base exception handler."""
    
    def __init__(self):
        self._handlers: Dict[Type[Exception], Callable[[Exception], Any]] = {}
    
    def register(self, exception_type: Type[Exception], handler: Callable[[Exception], Any]) -> None:
        """Register a handler for specific exception type."""
        self._handlers[exception_type] = handler
    
    def handle(self, error: Exception) -> Any:
        """Handle exception using registered handler or default."""
        for exc_type, handler in self._handlers.items():
            if isinstance(error, exc_type):
                return handler(error)
        
        return self._default_handler(error)
    
    def _default_handler(self, error: Exception) -> Any:
        """Default handler for unregistered exceptions."""
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        raise error


class GlobalExceptionHandler:
    """Global exception handler with logging and metrics."""
    
    def __init__(self):
        self._handlers: Dict[Type[Exception], Callable[[Exception], Dict[str, Any]]] = {}
        self._error_counts: Dict[str, int] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self) -> None:
        """Setup default exception handlers."""
        self._handlers[RAGError] = self._handle_rag_error
    
    def register(self, exception_type: Type[Exception], handler: Callable[[Exception], Dict[str, Any]]) -> None:
        """Register a custom exception handler."""
        self._handlers[exception_type] = handler
    
    def handle(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle exception and return formatted response."""
        # Track error metrics
        error_type = error.__class__.__name__
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
        
        # Log the error
        log_data = format_error_for_logging(error, context)
        logger.error("Exception occurred", extra=log_data)
        
        # Find and execute appropriate handler
        for exc_type, handler in self._handlers.items():
            if isinstance(error, exc_type):
                return handler(error)
        
        return self._handle_generic_error(error)
    
    def _handle_rag_error(self, error: RAGError) -> Dict[str, Any]:
        """Handle RAG-specific errors."""
        return error.to_dict()
    
    def _handle_generic_error(self, error: Exception) -> Dict[str, Any]:
        """Handle generic/unknown errors."""
        return {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        }
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics."""
        return self._error_counts.copy()
    
    def reset_stats(self) -> None:
        """Reset error statistics."""
        self._error_counts.clear()


# Global exception handler instance
_global_handler: Optional[GlobalExceptionHandler] = None


def get_global_exception_handler() -> GlobalExceptionHandler:
    """Get or create global exception handler."""
    global _global_handler
    if _global_handler is None:
        _global_handler = GlobalExceptionHandler()
    return _global_handler


def handle_exception(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to handle exceptions."""
    return get_global_exception_handler().handle(error, context)
