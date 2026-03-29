"""Audit logging system for RAG service."""

import json
import logging
import logging.handlers
import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from rag_system.config.settings import get_settings

settings = get_settings()


class AuditEventType(Enum):
    """Audit event types."""
    SEARCH = "search"
    UPLOAD = "upload"
    DELETE = "delete"
    DOWNLOAD = "download"
    LOGIN = "login"
    LOGOUT = "logout"
    CONFIG_CHANGE = "config_change"
    SYSTEM_ERROR = "system_error"


class AuditEventSeverity(Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_type: AuditEventType
    timestamp: str
    user_id: Optional[str]
    ip_address: Optional[str]
    severity: AuditEventSeverity
    action: str
    resource: str
    status: str  # "success", "failure", "blocked"
    details: Dict[str, Any]
    request_id: Optional[str] = None
    user_agent: Optional[str] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None


class AuditLogger:
    """Audit logger for security events."""
    
    def __init__(self, log_dir: str = "logs/audit", max_bytes: int = 10_000_000, backup_count: int = 5):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # File handler with rotation
        log_file = self.log_dir / "audit.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(file_handler)
    
    def _serialize_event(self, event: AuditEvent) -> str:
        """Serialize audit event to JSON."""
        event_dict = {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp,
            "user_id": event.user_id,
            "ip_address": event.ip_address,
            "severity": event.severity.value,
            "action": event.action,
            "resource": event.resource,
            "status": event.status,
            "details": event.details,
            "request_id": event.request_id,
            "user_agent": event.user_agent,
            "duration_ms": event.duration_ms,
            "error_message": event.error_message,
        }
        return json.dumps(event_dict, ensure_ascii=False)
    
    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event."""
        event_json = self._serialize_event(event)
        self.logger.info(event_json)
    
    async def log_event_async(self, event: AuditEvent) -> None:
        """Log an audit event asynchronously."""
        await asyncio.to_thread(self.log_event, event)
    
    def log_search(
        self,
        query: str,
        ip_address: str,
        user_id: Optional[str] = None,
        status: str = "success",
        hits_count: int = 0,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a search event."""
        event = AuditEvent(
            event_type=AuditEventType.SEARCH,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditEventSeverity.LOW,
            action="search",
            resource="rag_search",
            status=status,
            details={"query": query[:1000], "hits_count": hits_count},  # Truncate query
            duration_ms=duration_ms,
            error_message=error_message,
        )
        self.log_event(event)
    
    def log_upload(
        self,
        filename: str,
        file_size: int,
        ip_address: str,
        user_id: Optional[str] = None,
        status: str = "success",
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a file upload event."""
        event = AuditEvent(
            event_type=AuditEventType.UPLOAD,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditEventSeverity.MEDIUM,
            action="upload",
            resource=f"file:{filename}",
            status=status,
            details={"filename": filename, "file_size": file_size},
            duration_ms=duration_ms,
            error_message=error_message,
        )
        self.log_event(event)
    
    def log_delete(
        self,
        filename: str,
        ip_address: str,
        user_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> None:
        """Log a file deletion event."""
        event = AuditEvent(
            event_type=AuditEventType.DELETE,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditEventSeverity.HIGH,  # High severity for delete
            action="delete",
            resource=f"file:{filename}",
            status=status,
            details={"filename": filename},
            error_message=error_message,
        )
        self.log_event(event)
    
    def log_auth(
        self,
        action: str,  # "login", "logout", "failed_login"
        ip_address: str,
        user_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> None:
        """Log an authentication event."""
        severity = AuditEventSeverity.HIGH if action == "failed_login" else AuditEventSeverity.MEDIUM
        event = AuditEvent(
            event_type=AuditEventType.LOGIN if action in ["login", "failed_login"] else AuditEventType.LOGOUT,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            ip_address=ip_address,
            severity=severity,
            action=action,
            resource="auth",
            status=status,
            details={},
            error_message=error_message,
        )
        self.log_event(event)
    
    def log_security_event(
        self,
        action: str,
        ip_address: str,
        details: Dict[str, Any],
        severity: AuditEventSeverity = AuditEventSeverity.HIGH,
        user_id: Optional[str] = None,
    ) -> None:
        """Log a security event (rate limit exceeded, suspicious activity, etc.)."""
        event = AuditEvent(
            event_type=AuditEventType.SYSTEM_ERROR,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            ip_address=ip_address,
            severity=severity,
            action=action,
            resource="security",
            status="blocked" if severity in [AuditEventSeverity.HIGH, AuditEventSeverity.CRITICAL] else "warning",
            details=details,
        )
        self.log_event(event)


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def init_audit_logging():
    """Initialize audit logging."""
    get_audit_logger()
