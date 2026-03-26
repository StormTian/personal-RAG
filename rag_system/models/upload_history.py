from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class UploadStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    DELETED = "DELETED"


@dataclass
class UploadRecord:
    id: Optional[int] = None
    original_name: str = ""
    saved_name: str = ""
    file_path: str = ""
    file_size: int = 0
    file_type: str = ""
    status: UploadStatus = UploadStatus.PENDING
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    error_message: Optional[str] = None
    auto_reloaded: bool = False
    chunks_created: int = 0

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'original_name': self.original_name,
            'saved_name': self.saved_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'status': self.status.value,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'error_message': self.error_message,
            'auto_reloaded': self.auto_reloaded,
            'chunks_created': self.chunks_created
        }
