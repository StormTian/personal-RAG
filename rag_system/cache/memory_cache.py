"""In-memory LRU cache implementation."""

import time
from collections import OrderedDict
from threading import RLock
from typing import Any, Optional
from .base import QueryCache


class MemoryCache(QueryCache):
    """Thread-safe in-memory LRU cache with TTL support."""
    
    def __init__(self, max_items: int = 1000, default_ttl: int = 3600):
        self._max_items = max_items
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._lock = RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result by key."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            # Check expiration
            if expiry and time.time() > expiry:
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache value with optional TTL."""
        with self._lock:
            # Evict LRU if at capacity
            while len(self._cache) >= self._max_items:
                self._cache.popitem(last=False)
            
            ttl_seconds = ttl if ttl is not None else self._default_ttl
            expiry = time.time() + ttl_seconds if ttl_seconds > 0 else None
            
            # Remove if exists (to update position)
            if key in self._cache:
                del self._cache[key]
            
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """Delete cached value."""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None
    
    @property
    def size(self) -> int:
        """Current number of cached items."""
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        count = 0
        current_time = time.time()
        with self._lock:
            expired_keys = [
                k for k, (_, expiry) in self._cache.items()
                if expiry and current_time > expiry
            ]
            for key in expired_keys:
                del self._cache[key]
                count += 1
        return count