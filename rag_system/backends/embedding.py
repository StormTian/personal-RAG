"""Embedding backend implementations with async support and retry logic."""

import asyncio
import hashlib
import json
import math
import time
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple
import aiohttp
import urllib.request
import urllib.error

from ..core.base import EmbeddingBackend
from ..exceptions import EmbeddingError, ExternalServiceError
from ..utils.retry import retry_with_backoff, RetryConfig
from ..utils.text import tokenize, normalize_vector


class LocalHashEmbeddingBackend(EmbeddingBackend):
    """Local hash-based embedding backend."""
    
    def __init__(self, dimensions: int = 256, projections_per_token: int = 8) -> None:
        self.dimensions = dimensions
        self.projections_per_token = projections_per_token
        self.name = f"local-hash-{dimensions}d"
        self._token_cache: Dict[str, List[Tuple[int, float]]] = {}
        self._lock = asyncio.Lock()
    
    def _token_projection(self, token: str) -> List[Tuple[int, float]]:
        """Generate deterministic projection for a token."""
        cached = self._token_cache.get(token)
        if cached is not None:
            return cached
        
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        projection: List[Tuple[int, float]] = []
        for offset in range(self.projections_per_token):
            start = offset * 4
            idx = int.from_bytes(digest[start : start + 2], "big") % self.dimensions
            sign = 1.0 if digest[start + 2] % 2 == 0 else -1.0
            magnitude = 0.35 + (digest[start + 3] / 255.0)
            projection.append((idx, sign * magnitude))
        
        self._token_cache[token] = projection
        return projection
    
    def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Embed multiple texts synchronously."""
        vectors: List[Tuple[float, ...]] = []
        for text in texts:
            dense = [0.0] * self.dimensions
            token_counts = Counter(tokenize(text))
            for token, frequency in token_counts.items():
                weight = 1.0 + math.log(frequency)
                for idx, signed_weight in self._token_projection(token):
                    dense[idx] += signed_weight * weight
            vectors.append(normalize_vector(dense))
        return vectors
    
    async def embed_texts_async(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Embed multiple texts asynchronously (runs in thread pool)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_texts, texts)


class EmbeddingConnectionPool:
    """Connection pool for embedding backend HTTP requests."""
    
    def __init__(
        self,
        max_connections: int = 10,
        max_keepalive: int = 5,
        timeout: int = 30,
    ):
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        async with self._lock:
            if self._session is None or self._session.closed:
                connector = aiohttp.TCPConnector(
                    limit=self.max_connections,
                    limit_per_host=self.max_keepalive,
                    enable_cleanup_closed=True,
                    force_close=False,
                )
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                self._session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                )
            return self._session
    
    async def close(self) -> None:
        """Close the connection pool."""
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
    
    async def post(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, object],
    ) -> Dict[str, object]:
        """Make POST request with connection pooling."""
        session = await self.get_session()
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status >= 400:
                text = await response.text()
                raise ExternalServiceError(
                    message=f"HTTP {response.status}: {text}",
                    status_code=response.status,
                )
            return await response.json()


class OpenAICompatibleEmbeddingBackend(EmbeddingBackend):
    """OpenAI-compatible API embedding backend with async and retry support."""
    
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout: int = 30,
        batch_size: int = 32,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.name = f"openai-compatible:{model}"
        self._connection_pool: Optional[EmbeddingConnectionPool] = None
        self._retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=retry_delay,
            max_delay=30.0,
            exponential_base=2.0,
            retryable_exceptions=(ExternalServiceError, asyncio.TimeoutError),
        )
    
    async def _get_connection_pool(self) -> EmbeddingConnectionPool:
        """Get or create connection pool."""
        if self._connection_pool is None:
            self._connection_pool = EmbeddingConnectionPool(timeout=self.timeout)
        return self._connection_pool
    
    def _batch_items(self, items: Sequence[str], batch_size: int) -> List[Sequence[str]]:
        """Split items into batches."""
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    async def _request_batch(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Request embeddings for a batch of texts."""
        pool = await self._get_connection_pool()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": list(texts)}
        
        try:
            data = await pool.post(
                f"{self.base_url}/v1/embeddings",
                headers,
                payload,
            )
            ordered = sorted(data["data"], key=lambda item: item["index"])
            return [normalize_vector(item["embedding"]) for item in ordered]
        except Exception as e:
            raise EmbeddingError(
                message=f"Failed to get embeddings: {str(e)}",
                backend=self.name,
                details={"batch_size": len(texts)},
            ) from e
    
    async def _request_batch_with_retry(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Request embeddings with retry logic."""
        return await retry_with_backoff(
            self._request_batch,
            texts,
            config=self._retry_config,
        )
    
    async def embed_texts_async(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Embed texts asynchronously with batching and retry."""
        embeddings: List[Tuple[float, ...]] = []
        batches = self._batch_items(list(texts), self.batch_size)
        
        # Process batches concurrently with semaphore for rate limiting
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent batches
        
        async def process_batch(batch):
            async with semaphore:
                return await self._request_batch_with_retry(batch)
        
        # Process all batches concurrently
        results = await asyncio.gather(*[process_batch(batch) for batch in batches])
        
        for batch_embeddings in results:
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Sync version - runs async version in event loop."""
        return asyncio.run(self.embed_texts_async(texts))
    
    async def close(self) -> None:
        """Close connection pool."""
        if self._connection_pool:
            await self._connection_pool.close()


class CachedEmbeddingBackend(EmbeddingBackend):
    """Embedding backend with caching layer."""
    
    def __init__(
        self,
        backend: EmbeddingBackend,
        cache_dir: str = ".embedding_cache",
        max_cache_size: int = 10000,
    ):
        self.backend = backend
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size
        self.name = f"cached:{backend.name}"
        self._cache: Dict[str, Tuple[float, ...]] = {}
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.sha256(text.encode()).hexdigest()[:32]
    
    def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Embed texts with caching."""
        results = []
        to_embed = []
        indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                results.append((i, self._cache[cache_key]))
            else:
                to_embed.append(text)
                indices.append(i)
        
        if to_embed:
            embeddings = self.backend.embed_texts(to_embed)
            for idx, text, embedding in zip(indices, to_embed, embeddings):
                cache_key = self._get_cache_key(text)
                if len(self._cache) < self.max_cache_size:
                    self._cache[cache_key] = embedding
                results.append((idx, embedding))
        
        # Sort by original index
        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]
    
    async def embed_texts_async(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Async version with caching."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_texts, texts)
