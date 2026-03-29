"""Input validation and sanitization for RAG service."""

import re
import html
from typing import Optional
from pathlib import Path

import bleach
from pydantic import BaseModel, validator, Field


# Allowed file extensions
ALLOWED_EXTENSIONS = {'.md', '.txt', '.doc', '.docx', '.pdf', '.markdown'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_QUERY_LENGTH = 1000
MIN_QUERY_LENGTH = 1


class SearchQuery(BaseModel):
    """Validated search query."""
    query: str = Field(..., min_length=MIN_QUERY_LENGTH, max_length=MAX_QUERY_LENGTH)
    top_k: int = Field(default=3, ge=1, le=20)
    
    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize search query."""
        # Remove null bytes
        v = v.replace('\x00', '')
        
        # Strip whitespace
        v = v.strip()
        
        # HTML escape
        v = html.escape(v)
        
        # Check for SQL injection patterns
        sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(--|#|\/\*|\*\/)',
            r'(;\s*\w+)',
            r'(\bOR\b|\bAND\b)\s*\d+\s*=\s*\d+',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid characters in query")
        
        return v


class FileUpload(BaseModel):
    """Validated file upload."""
    filename: str
    content_type: str
    size: int
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate and sanitize filename."""
        # Remove path traversal
        v = Path(v).name
        
        # Check for invalid characters
        if re.search(r'[<>:"|?*\x00-\x1f]', v):
            raise ValueError("Invalid characters in filename")
        
        # Check extension
        ext = Path(v).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}")
        
        return v
    
    @validator('size')
    def validate_size(cls, v):
        """Validate file size."""
        if v > MAX_FILE_SIZE:
            raise ValueError(f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB")
        if v <= 0:
            raise ValueError("Invalid file size")
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type."""
        allowed_types = [
            'text/markdown',
            'text/plain',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ]
        if v not in allowed_types and not v.startswith('text/'):
            raise ValueError("Invalid content type")
        return v


class DocumentId(BaseModel):
    """Validated document ID."""
    doc_id: str = Field(..., min_length=1, max_length=256)
    
    @validator('doc_id')
    def validate_doc_id(cls, v):
        """Validate document ID."""
        # Remove path traversal
        v = Path(v).name
        
        # Check for invalid characters
        if re.search(r'[<>:"|?*\x00-\x1f\\]', v):
            raise ValueError("Invalid characters in document ID")
        
        return v


def sanitize_html(text: str) -> str:
    """Sanitize HTML content."""
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    allowed_attrs = {}
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)


def sanitize_markdown(text: str) -> str:
    """Sanitize markdown content."""
    # Remove potentially dangerous HTML
    text = bleach.clean(text, tags=[], strip=True)
    
    # Escape HTML entities
    text = html.escape(text)
    
    return text


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format."""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_search_query(query: str) -> Optional[str]:
        """Validate search query and return error message if invalid."""
        try:
            SearchQuery(query=query)
            return None
        except Exception as e:
            return str(e)
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        # Truncate
        text = text[:max_length]
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        
        # HTML escape
        text = html.escape(text)
        
        return text
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """Validate file extension."""
        ext = Path(filename).suffix.lower()
        return ext in ALLOWED_EXTENSIONS
