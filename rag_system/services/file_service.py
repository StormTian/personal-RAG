"""File service for managing uploaded documents."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, BinaryIO
from uuid import uuid4

from rag_system.utils.file_security import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    get_secure_path,
    get_file_extension,
)
from rag_system.exceptions.file_exceptions import (
    InvalidFileTypeError,
    FileTooLargeError,
    FileSecurityError,
    FileNotFoundError,
    FileProcessingError,
    DuplicateFileError,
)


class FileInfo:
    """Information about a stored file."""
    
    def __init__(
        self,
        file_id: str,
        original_name: str,
        stored_name: str,
        file_path: str,
        file_size: int,
        file_type: str,
        created_at: datetime,
        metadata: Optional[Dict] = None,
    ):
        self.file_id = file_id
        self.original_name = original_name
        self.stored_name = stored_name
        self.file_path = file_path
        self.file_size = file_size
        self.file_type = file_type
        self.created_at = created_at
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """Convert file info to dictionary."""
        return {
            "file_id": self.file_id,
            "original_name": self.original_name,
            "stored_name": self.stored_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_size_human": self._human_readable_size(self.file_size),
            "file_type": self.file_type,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @staticmethod
    def _human_readable_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"


class FileService:
    """Service for managing file uploads and storage."""
    
    def __init__(
        self,
        upload_dir: str = "document_library",
        max_file_size: int = MAX_FILE_SIZE,
        allowed_extensions: Optional[set] = None,
    ):
        """
        Initialize file service.
        
        Args:
            upload_dir: Base directory for file uploads
            max_file_size: Maximum allowed file size in bytes
            allowed_extensions: Set of allowed file extensions
        """
        self.upload_dir = Path(upload_dir)
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or ALLOWED_EXTENSIONS
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage for file metadata (in production, use database)
        self._files: Dict[str, FileInfo] = {}
        self._load_existing_files()
    
    def _load_existing_files(self):
        """Load existing files from upload directory."""
        if not self.upload_dir.exists():
            return
        
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                file_id = str(uuid4())
                file_info = FileInfo(
                    file_id=file_id,
                    original_name=file_path.name,
                    stored_name=file_path.name,
                    file_path=str(file_path),
                    file_size=stat.st_size,
                    file_type=get_file_extension(file_path.name),
                    created_at=datetime.fromtimestamp(stat.st_mtime),
                )
                self._files[file_id] = file_info
    
    def save_uploaded_file(
        self,
        file: BinaryIO,
        filename: str,
        metadata: Optional[Dict] = None,
        allow_overwrite: bool = False,
    ) -> FileInfo:
        """
        Save an uploaded file after validation.
        
        Args:
            file: File object to save (supports read() method)
            filename: Original filename
            metadata: Optional metadata to store with file
            allow_overwrite: Whether to allow overwriting existing files
            
        Returns:
            FileInfo object with file details
            
        Raises:
            InvalidFileTypeError: If file extension is not allowed
            FileTooLargeError: If file size exceeds limit
            FileSecurityError: If filename contains dangerous characters
            FileProcessingError: If file cannot be saved
            DuplicateFileError: If file exists and overwrite not allowed
        """
        # Validate filename
        if not filename or not isinstance(filename, str):
            raise FileSecurityError(
                filename=str(filename),
                reason="Invalid filename",
            )
        
        # Check for dangerous characters
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            raise FileSecurityError(
                filename=filename,
                reason="Path traversal attempt detected",
            )
        
        # Validate file extension
        if not validate_file_extension(filename):
            raise InvalidFileTypeError(
                filename=filename,
                allowed_extensions=list(self.allowed_extensions),
            )
        
        # Read file content
        try:
            content = file.read()
        except Exception as e:
            raise FileProcessingError(
                filename=filename,
                operation="read",
                reason=str(e),
            )
        
        # Validate file size
        file_size = len(content)
        if not validate_file_size(file_size):
            raise FileTooLargeError(
                filename=filename,
                file_size=file_size,
                max_size=self.max_file_size,
            )
        
        # Sanitize filename
        stored_name = sanitize_filename(filename)
        
        # Get secure path
        try:
            file_path = get_secure_path(
                stored_name,
                str(self.upload_dir),
                allow_overwrite=allow_overwrite,
            )
        except FileExistsError as e:
            raise DuplicateFileError(
                filename=filename,
                details={"stored_name": stored_name},
            ) from e
        except ValueError as e:
            raise FileSecurityError(
                filename=filename,
                reason=str(e),
            ) from e
        
        # Save file
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
        except Exception as e:
            raise FileProcessingError(
                filename=filename,
                operation="save",
                reason=str(e),
            ) from e
        
        # Create file info
        file_id = str(uuid4())
        file_info = FileInfo(
            file_id=file_id,
            original_name=filename,
            stored_name=stored_name,
            file_path=str(file_path),
            file_size=file_size,
            file_type=get_file_extension(filename),
            created_at=datetime.now(),
            metadata=metadata,
        )
        
        # Store metadata
        self._files[file_id] = file_info
        
        return file_info
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file by its ID.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            True if file was deleted, False otherwise
            
        Raises:
            FileNotFoundError: If file does not exist
            FileProcessingError: If file cannot be deleted
        """
        if file_id not in self._files:
            raise FileNotFoundError(filename=file_id)
        
        file_info = self._files[file_id]
        file_path = Path(file_info.file_path)
        
        try:
            if file_path.exists():
                file_path.unlink()
            del self._files[file_id]
            return True
        except Exception as e:
            raise FileProcessingError(
                filename=file_info.original_name,
                operation="delete",
                reason=str(e),
            ) from e
    
    def list_files(
        self,
        file_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[FileInfo]:
        """
        List all stored files.
        
        Args:
            file_type: Filter by file type (extension with dot)
            sort_by: Field to sort by (created_at, filename, size)
            sort_order: Sort order (asc, desc)
            
        Returns:
            List of FileInfo objects
        """
        files = list(self._files.values())
        
        # Filter by file type
        if file_type:
            files = [f for f in files if f.file_type == file_type.lower()]
        
        # Sort
        reverse = sort_order.lower() == "desc"
        if sort_by == "created_at":
            files.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_by == "filename":
            files.sort(key=lambda x: x.original_name.lower(), reverse=reverse)
        elif sort_by == "size":
            files.sort(key=lambda x: x.file_size, reverse=reverse)
        
        return files
    
    def get_file(self, file_id: str) -> FileInfo:
        """
        Get file information by ID.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            FileInfo object
            
        Raises:
            FileNotFoundError: If file does not exist
        """
        if file_id not in self._files:
            raise FileNotFoundError(filename=file_id)
        
        return self._files[file_id]
    
    def get_file_path(self, file_id: str) -> Path:
        """
        Get the file system path for a file.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            Path object
            
        Raises:
            FileNotFoundError: If file does not exist
        """
        file_info = self.get_file(file_id)
        path = Path(file_info.file_path)
        
        if not path.exists():
            raise FileNotFoundError(filename=file_info.original_name)
        
        return path
    
    def file_exists(self, file_id: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            True if file exists, False otherwise
        """
        if file_id not in self._files:
            return False
        
        return Path(self._files[file_id].file_path).exists()
    
    def get_total_size(self) -> int:
        """
        Get total size of all stored files in bytes.
        
        Returns:
            Total size in bytes
        """
        return sum(f.file_size for f in self._files.values())
    
    def get_statistics(self) -> Dict:
        """
        Get file storage statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_files = len(self._files)
        total_size = self.get_total_size()
        
        # Count by file type
        type_counts = {}
        for file_info in self._files.values():
            ext = file_info.file_type
            type_counts[ext] = type_counts.get(ext, 0) + 1
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_human": FileInfo._human_readable_size(total_size),
            "upload_directory": str(self.upload_dir),
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "allowed_extensions": list(self.allowed_extensions),
            "files_by_type": type_counts,
        }
    
    def cleanup_orphaned_files(self) -> List[str]:
        """
        Remove files from disk that are not in the metadata store.
        
        Returns:
            List of removed file paths
        """
        removed = []
        tracked_paths = {f.file_path for f in self._files.values()}
        
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file() and str(file_path) not in tracked_paths:
                try:
                    file_path.unlink()
                    removed.append(str(file_path))
                except Exception:
                    pass  # Ignore errors during cleanup
        
        return removed
