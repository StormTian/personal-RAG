"""File security utilities for safe file upload handling."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'.md', '.markdown', '.txt', '.doc', '.docx', '.pdf'}

# Maximum file size: 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing special characters and adding timestamp.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename with timestamp prefix
        
    Example:
        >>> sanitize_filename("my file<script>.txt")
        '20240326_143022_my_file_script_.txt'
    """
    # Get filename without path
    filename = os.path.basename(filename)
    
    # Split into name and extension
    name, ext = os.path.splitext(filename)
    
    # Remove or replace dangerous characters
    # Keep only alphanumeric, spaces, dots, underscores, and hyphens
    sanitized_name = re.sub(r'[^\w\s.-]', '_', name)
    
    # Replace spaces with underscores
    sanitized_name = sanitized_name.replace(' ', '_')
    
    # Remove leading/trailing underscores and dots
    sanitized_name = sanitized_name.strip('._')
    
    # If empty after sanitization, use 'file'
    if not sanitized_name:
        sanitized_name = 'file'
    
    # Add timestamp prefix for uniqueness
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{timestamp}_{sanitized_name}{ext.lower()}"


def validate_file_extension(filename: str) -> bool:
    """
    Validate if file extension is in the allowed list.
    
    Args:
        filename: Filename to validate
        
    Returns:
        True if extension is allowed, False otherwise
        
    Example:
        >>> validate_file_extension("document.pdf")
        True
        >>> validate_file_extension("script.exe")
        False
    """
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """
    Validate if file size is within the allowed limit.
    
    Args:
        file_size: File size in bytes
        
    Returns:
        True if size is within limit, False otherwise
        
    Example:
        >>> validate_file_size(5 * 1024 * 1024)  # 5MB
        True
        >>> validate_file_size(15 * 1024 * 1024)  # 15MB
        False
    """
    return 0 < file_size <= MAX_FILE_SIZE


def get_secure_path(
    filename: str,
    base_directory: str,
    allow_overwrite: bool = False
) -> Path:
    """
    Get a secure path for file storage, preventing path traversal attacks.
    
    Args:
        filename: Sanitized filename
        base_directory: Base directory for file storage
        allow_overwrite: Whether to allow overwriting existing files
        
    Returns:
        Secure file path
        
    Raises:
        ValueError: If path traversal is detected or file exists and overwrite not allowed
        
    Example:
        >>> get_secure_path("doc.txt", "/uploads")
        PosixPath('/uploads/doc.txt')
    """
    # Resolve base directory to absolute path
    base_dir = Path(base_directory).resolve()
    
    # Construct the target path
    target_path = (base_dir / filename).resolve()
    
    # Security check: ensure the resolved path is within base directory
    # This prevents path traversal attacks like "../../../etc/passwd"
    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: '{filename}' attempts to escape base directory"
        )
    
    # Check if file already exists
    if target_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"File already exists: {target_path}. "
            "Set allow_overwrite=True to replace it."
        )
    
    # Ensure parent directories exist
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    return target_path


def get_file_extension(filename: str) -> str:
    """
    Get file extension in lowercase.
    
    Args:
        filename: Filename to process
        
    Returns:
        Lowercase file extension including the dot
        
    Example:
        >>> get_file_extension("document.PDF")
        '.pdf'
    """
    _, ext = os.path.splitext(filename.lower())
    return ext


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename contains potentially dangerous characters.
    
    Args:
        filename: Filename to check
        
    Returns:
        True if filename appears safe, False otherwise
        
    Example:
        >>> is_safe_filename("normal-file.txt")
        True
        >>> is_safe_filename("file<script>.txt")
        False
    """
    # Check for null bytes
    if '\x00' in filename:
        return False
    
    # Check for path traversal sequences
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        return False
    
    # Check for control characters
    if any(ord(char) < 32 for char in filename):
        return False
    
    return True
