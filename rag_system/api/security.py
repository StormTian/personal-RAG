"""Security components: API key validation, rate limiting, input validation."""

import hashlib
import re
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set

from ..exceptions import AuthenticationError, RateLimitError, ValidationError
from ..config import get_settings


class APIKeyValidator:
    """API key validation."""
    
    def __init__(self, valid_keys: Optional[Set[str]] = None):
        self._valid_keys = valid_keys or set()
        self._key_usage: Dict[str, int] = defaultdict(int)
    
    def add_key(self, key: str) -> None:
        """Add a valid API key."""
        self._valid_keys.add(key)
    
    def validate(self, key: Optional[str]) -> bool:
        """Validate API key."""
        if not key:
            return False
        if key in self._valid_keys:
            self._key_usage[key] += 1
            return True
        return False
    
    def get_usage(self, key: str) -> int:
        """Get usage count for API key."""
        return self._key_usage[key]


class RateLimiter:
    """Rate limiter with sliding window."""
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = None  # Will use asyncio.Lock in async context
    
    def is_allowed(self, key: str) -> tuple[bool, Optional[int]]:
        """Check if request is allowed. Returns (allowed, retry_after)."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        
        if len(self._requests[key]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self._requests[key][0]))
            return False, max(0, retry_after)
        
        self._requests[key].append(now)
        return True, None
    
    def check_rate_limit(self, key: str) -> None:
        """Check rate limit and raise exception if exceeded."""
        allowed, retry_after = self.is_allowed(key)
        if not allowed:
            raise RateLimitError(
                message="Rate limit exceeded",
                retry_after=retry_after,
                details={"limit": self.max_requests, "window": self.window_seconds},
            )


class InputValidator:
    """Input validation and sanitization."""
    
    def __init__(
        self,
        max_query_length: int = 1000,
        allowed_extensions: Optional[List[str]] = None,
    ):
        self.max_query_length = max_query_length
        self.allowed_extensions = set(allowed_extensions or [".md", ".txt", ".pdf", ".doc", ".docx"])
    
    def validate_query(self, query: str) -> str:
        """Validate and sanitize query string."""
        if not query:
            raise ValidationError(
                message="Query cannot be empty",
                field="query",
            )
        
        if len(query) > self.max_query_length:
            raise ValidationError(
                message=f"Query exceeds maximum length of {self.max_query_length}",
                field="query",
            )
        
        # Sanitize query
        query = self._sanitize_text(query)
        
        return query
    
    def validate_top_k(self, top_k: int, max_top_k: int = 20) -> int:
        """Validate top_k parameter."""
        try:
            top_k = int(top_k)
        except (TypeError, ValueError):
            raise ValidationError(
                message="top_k must be an integer",
                field="top_k",
            )
        
        if top_k < 1:
            raise ValidationError(
                message="top_k must be at least 1",
                field="top_k",
            )
        
        if top_k > max_top_k:
            raise ValidationError(
                message=f"top_k cannot exceed {max_top_k}",
                field="top_k",
            )
        
        return top_k
    
    def validate_file_extension(self, filename: str) -> str:
        """Validate file extension."""
        import os
        _, ext = os.path.splitext(filename.lower())
        
        if ext not in self.allowed_extensions:
            raise ValidationError(
                message=f"File extension '{ext}' not allowed",
                field="filename",
                details={"allowed": list(self.allowed_extensions)},
            )
        
        return filename
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text input."""
        # Remove control characters except newlines and tabs
        text = "".join(char for char in text if char == "\n" or char == "\t" or ord(char) >= 32)
        
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        
        return text.strip()


class SecurityMiddleware:
    """Security middleware combining all security features."""
    
    def __init__(
        self,
        api_key_validator: Optional[APIKeyValidator] = None,
        rate_limiter: Optional[RateLimiter] = None,
        input_validator: Optional[InputValidator] = None,
        require_api_key: bool = False,
    ):
        self.api_key_validator = api_key_validator or APIKeyValidator()
        self.rate_limiter = rate_limiter or RateLimiter()
        self.input_validator = input_validator or InputValidator()
        self.require_api_key = require_api_key
    
    def validate_request(
        self,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> None:
        """Validate incoming request."""
        # Validate API key
        if self.require_api_key:
            if not api_key or not self.api_key_validator.validate(api_key):
                raise AuthenticationError(
                    message="Invalid or missing API key",
                )
        
        # Check rate limit
        rate_limit_key = api_key or client_id or "anonymous"
        self.rate_limiter.check_rate_limit(rate_limit_key)
    
    def validate_query(self, query: str) -> str:
        """Validate query parameter."""
        return self.input_validator.validate_query(query)
    
    def validate_top_k(self, top_k: int) -> int:
        """Validate top_k parameter."""
        return self.input_validator.validate_top_k(top_k)
    
    @classmethod
    def from_settings(cls) -> "SecurityMiddleware":
        """Create security middleware from settings."""
        settings = get_settings()
        
        api_key_validator = APIKeyValidator()
        if settings.security.require_api_key:
            # In production, load keys from secure storage
            api_key_validator.add_key("your-api-key-here")
        
        rate_limiter = RateLimiter(
            max_requests=settings.security.rate_limit_requests,
            window_seconds=settings.security.rate_limit_window,
        )
        
        input_validator = InputValidator(
            max_query_length=settings.security.max_query_length,
            allowed_extensions=settings.security.allowed_file_extensions,
        )
        
        return cls(
            api_key_validator=api_key_validator,
            rate_limiter=rate_limiter,
            input_validator=input_validator,
            require_api_key=settings.security.require_api_key,
        )
