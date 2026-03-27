"""Abstract base class for query cache."""

import hashlib
from abc import ABC, abstractmethod
from typing import Any, Optional


class QueryCache(ABC):
    """Abstract base class for query result caching."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get cached result by key.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found/expired.
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache value.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (optional).
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete cached value."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    def make_key(self, query: str, top_k: int) -> str:
        """Generate cache key from query parameters.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            Cache key string
        """
        content = f"{query}:{top_k}"
        return hashlib.md5(content.encode()).hexdigest()