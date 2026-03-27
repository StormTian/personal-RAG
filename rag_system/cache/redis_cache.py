"""Redis-based cache implementation with lazy import."""

import json
from typing import Any, Optional
from .base import QueryCache


class RedisCache(QueryCache):
    """Redis-based cache with TTL support."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "rag:query:",
        default_ttl: int = 3600,
    ):
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._default_ttl = default_ttl
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Redis client."""
        if self._client is None:
            try:
                import redis
                self._client = redis.from_url(self._redis_url)
            except ImportError:
                raise ImportError(
                    "redis is required for Redis cache. "
                    "Install it with: pip install redis"
                )
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self._key_prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result by key."""
        try:
            client = self._get_client()
            value = client.get(self._make_key(key))
            if value is None:
                return None
            return json.loads(value)
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache value with optional TTL."""
        try:
            client = self._get_client()
            ttl_seconds = ttl if ttl is not None else self._default_ttl
            serialized = json.dumps(value)
            full_key = self._make_key(key)
            
            if ttl_seconds > 0:
                client.setex(full_key, ttl_seconds, serialized)
            else:
                client.set(full_key, serialized)
        except Exception:
            pass
    
    def delete(self, key: str) -> None:
        """Delete cached value."""
        try:
            client = self._get_client()
            client.delete(self._make_key(key))
        except Exception:
            pass
    
    def clear(self) -> None:
        """Clear all cached values with this prefix."""
        try:
            client = self._get_client()
            pattern = f"{self._key_prefix}*"
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
        except Exception:
            pass
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            client = self._get_client()
            return bool(client.exists(self._make_key(key)))
        except Exception:
            return False