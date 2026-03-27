"""Unit tests for query cache implementations."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from rag_system.cache import (
    QueryCache,
    MemoryCache,
    RedisCache,
    create_query_cache,
)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class TestMemoryCache:
    """Tests for MemoryCache."""
    
    def test_create_cache(self):
        """Test creating a memory cache."""
        cache = MemoryCache(max_items=100, default_ttl=3600)
        assert cache.size == 0
    
    def test_set_and_get(self):
        """Test setting and getting values."""
        cache = MemoryCache()
        cache.set("key1", {"data": "value1"})
        
        result = cache.get("key1")
        assert result == {"data": "value1"}
    
    def test_get_nonexistent_key(self):
        """Test getting a nonexistent key."""
        cache = MemoryCache()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_delete(self):
        """Test deleting a key."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.delete("key1")
        
        assert cache.get("key1") is None
    
    def test_clear(self):
        """Test clearing all cached values."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.size == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_exists(self):
        """Test checking key existence."""
        cache = MemoryCache()
        cache.set("key1", "value1")
        
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False
    
    def test_lru_eviction(self):
        """Test LRU eviction when max items reached."""
        cache = MemoryCache(max_items=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None
    
    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = MemoryCache(default_ttl=1)
        cache.set("key1", "value1")
        
        # Should be present immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        assert cache.get("key1") is None
    
    def test_custom_ttl(self):
        """Test custom TTL for individual items."""
        cache = MemoryCache(default_ttl=3600)
        cache.set("key1", "value1", ttl=1)
        
        time.sleep(1.1)
        
        assert cache.get("key1") is None
    
    def test_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = MemoryCache(default_ttl=1)
        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=1)
        
        time.sleep(1.1)
        
        removed = cache.cleanup_expired()
        assert removed == 2
        assert cache.size == 0


class TestRedisCache:
    """Tests for RedisCache."""
    
    def test_create_cache(self):
        """Test creating a Redis cache."""
        cache = RedisCache(
            redis_url="redis://localhost:6379/0",
            key_prefix="test:",
        )
        assert cache._redis_url == "redis://localhost:6379/0"
        assert cache._key_prefix == "test:"
    
    def test_set_and_get_with_mock(self):
        """Test setting and getting values with mocked Redis."""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.return_value = b'{"data": "value1"}'
        cache._client = mock_client
        
        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")
        
        assert result == {"data": "value1"}
    
    def test_get_nonexistent_key_with_mock(self):
        """Test getting a nonexistent key."""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.get.return_value = None
        cache._client = mock_client
        
        result = cache.get("nonexistent")
        assert result is None
    
    def test_delete_with_mock(self):
        """Test deleting a key."""
        cache = RedisCache()
        mock_client = MagicMock()
        cache._client = mock_client
        
        cache.delete("key1")
        mock_client.delete.assert_called_once()
    
    def test_clear_with_mock(self):
        """Test clearing all cached values."""
        cache = RedisCache(key_prefix="test:")
        mock_client = MagicMock()
        # scan returns (cursor, keys), cursor=0 signals end of iteration
        mock_client.scan.side_effect = [(1, [b"test:key1"]), (0, [b"test:key2"])]
        cache._client = mock_client
        
        cache.clear()
        # delete should be called twice (once per batch)
        assert mock_client.delete.call_count == 2
    
    def test_exists_with_mock(self):
        """Test checking key existence."""
        cache = RedisCache()
        mock_client = MagicMock()
        mock_client.exists.return_value = 1
        cache._client = mock_client
        
        assert cache.exists("key1") is True
        
        mock_client.exists.return_value = 0
        assert cache.exists("nonexistent") is False


class TestQueryCacheFactory:
    """Tests for query cache factory function."""
    
    def test_create_memory_cache(self):
        """Test creating memory cache via factory."""
        cache = create_query_cache(backend="memory", max_items=100)
        assert isinstance(cache, MemoryCache)
    
    def test_create_redis_cache(self):
        """Test creating Redis cache via factory."""
        cache = create_query_cache(backend="redis", redis_url="redis://localhost:6379/0")
        assert isinstance(cache, RedisCache)
    
    def test_default_backend(self):
        """Test default backend is memory."""
        cache = create_query_cache()
        assert isinstance(cache, MemoryCache)