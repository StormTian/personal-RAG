"""Query cache backends for caching RAG results."""

from .base import QueryCache
from .memory_cache import MemoryCache
from .redis_cache import RedisCache

__all__ = ["QueryCache", "MemoryCache", "RedisCache"]


def create_query_cache(backend: str = "memory", **kwargs) -> QueryCache:
    """Factory function to create query cache."""
    if backend == "redis":
        redis_kwargs = {
            k: v for k, v in kwargs.items()
            if k in ("redis_url", "key_prefix", "default_ttl")
        }
        return RedisCache(**redis_kwargs)
    
    memory_kwargs = {
        k: v for k, v in kwargs.items()
        if k in ("max_items", "default_ttl", "max_memory_items")
    }
    if "max_memory_items" in memory_kwargs:
        memory_kwargs["max_items"] = memory_kwargs.pop("max_memory_items")
    return MemoryCache(**memory_kwargs)