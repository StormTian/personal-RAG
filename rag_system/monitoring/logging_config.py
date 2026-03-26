"""Structured logging configuration."""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "query"):
            log_data["query"] = record.query
        if hasattr(record, "component"):
            log_data["component"] = record.component
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith("_"):
                if key not in ("name", "msg", "args", "levelname", "levelno", "pathname",
                              "filename", "module", "lineno", "funcName", "created",
                              "msecs", "relativeCreated", "thread", "threadName",
                              "processName", "process", "exc_info", "exc_text", "stack_info"):
                    log_data[key] = value
        
        return json.dumps(log_data, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname[:4]
        return f"[{timestamp}] {level} {record.name}: {record.getMessage()}"


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    file_path: Optional[str] = None,
    max_bytes: int = 10_000_000,
    backup_count: int = 5,
    enable_console: bool = True,
) -> None:
    """Setup logging configuration."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        if format_type == "json":
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(ConsoleFormatter())
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_path:
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger with RAG system prefix."""
    return logging.getLogger(f"rag_system.{name}")


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Log performance metric."""
    log_extra = {"duration_ms": duration_ms, "component": operation}
    if extra:
        log_extra.update(extra)
    logger.info(f"Performance: {operation} completed in {duration_ms:.2f}ms", extra=log_extra)
