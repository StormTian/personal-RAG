"""Main RAG Engine implementation."""

import asyncio
import gzip
import math
import pickle
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from .core.base import (
    EmbeddingBackend,
    RerankerBackend,
    SearchEngine,
    SourceDocument,
    Chunk,
    CandidateScore,
    SearchHit,
    RagResponse,
    IndexSnapshot,
)
from .backends.embedding import LocalHashEmbeddingBackend, OpenAICompatibleEmbeddingBackend
from .backends.reranker import LocalHeuristicReranker, OpenAICompatibleListwiseReranker
from .config import Settings, get_settings
from .exceptions import RetrievalError, ConfigurationError
from .monitoring.logging_config import get_logger, log_performance
from .monitoring.metrics import get_metrics_collector
from .utils.text import (
    tokenize,
    split_sentences,
    cosine_similarity,
    chunk_text,
)

logger = get_logger("rag_engine")


class RAGEngine(SearchEngine):
    """Production-ready RAG Engine with async support and metrics."""
    
    def __init__(
        self,
        library_dir: Path,
        settings: Optional[Settings] = None,
        embedding_backend: Optional[EmbeddingBackend] = None,
        reranker_backend: Optional[RerankerBackend] = None,
    ):
        self.library_dir = Path(library_dir)
        self.settings = settings or get_settings()
        self.embedding_backend = embedding_backend or self._build_embedding_backend()
        self.local_reranker = LocalHeuristicReranker()
        self.reranker_backend = reranker_backend or self._build_reranker_backend()
        self._loader_registry = None  # Lazy initialization
        self.metrics = get_metrics_collector()
        
        self._lock = threading.RLock()
        self._snapshot: Optional[IndexSnapshot] = None
        self._cache_path = Path(self.settings.cache.cache_dir) / "index_cache.pkl.gz"
        
        # Build initial index
        self._snapshot = self._build_snapshot()
        logger.info(f"RAG Engine initialized with {len(self._snapshot.chunks)} chunks")
    
    @property
    def loader_registry(self):
        """Lazy initialization of document loader registry to avoid circular imports."""
        if self._loader_registry is None:
            from .api.loader import DocumentLoaderRegistry
            self._loader_registry = DocumentLoaderRegistry()
        return self._loader_registry
    
    def _build_embedding_backend(self) -> EmbeddingBackend:
        """Build embedding backend from settings."""
        config = self.settings.embedding
        
        if config.backend == "openai-compatible":
            if not config.api_key or not config.model:
                logger.warning("OpenAI backend configured but missing API key or model, using local backend")
                return LocalHashEmbeddingBackend(
                    dimensions=config.dimensions,
                    projections_per_token=config.projections_per_token,
                )
            return OpenAICompatibleEmbeddingBackend(
                api_key=config.api_key,
                model=config.model,
                base_url=config.base_url,
                timeout=config.timeout,
                batch_size=config.batch_size,
                max_retries=config.max_retries,
                retry_delay=config.retry_delay,
            )
        
        return LocalHashEmbeddingBackend(
            dimensions=config.dimensions,
            projections_per_token=config.projections_per_token,
        )
    
    def _build_reranker_backend(self) -> RerankerBackend:
        """Build reranker backend from settings."""
        config = self.settings.reranker
        
        if config.backend == "openai-compatible":
            if not config.model:
                logger.warning("OpenAI reranker configured but missing model, using local reranker")
                return self.local_reranker
            
            return OpenAICompatibleListwiseReranker(
                api_key=config.api_key or self.settings.embedding.api_key,
                model=config.model,
                base_url=config.base_url or self.settings.embedding.base_url,
                fallback=self.local_reranker,
                timeout=config.timeout,
                max_candidates=config.max_candidates,
            )
        
        return self.local_reranker
    
    def _discover_source_files(self) -> List[Path]:
        """Discover all supported source files in library directory."""
        supported = self.loader_registry.get_supported_extensions()
        files = []
        
        for ext in supported:
            files.extend(self.library_dir.rglob(f"*{ext}"))
        
        return sorted(files, key=lambda p: str(p.relative_to(self.library_dir)))
    
    def _build_snapshot(self) -> IndexSnapshot:
        """Build index snapshot from documents."""
        start_time = time.time()
        
        source_files = self._discover_source_files()
        if not source_files:
            supported = ", ".join(self.loader_registry.get_supported_extensions())
            raise ConfigurationError(
                message=f"Document library is empty: {self.library_dir} (supported: {supported})",
            )
        
        # Check cache
        if self.settings.cache.enabled:
            cached = self._load_from_cache(source_files)
            if cached:
                logger.info(f"Loaded index from cache: {len(cached.chunks)} chunks")
                return cached
        
        # Build index
        documents: List[SourceDocument] = []
        skipped_files: List[Tuple[str, str]] = []
        chunks: List[Chunk] = []
        chunk_id = 0
        
        for path in source_files:
            relative_path = str(path.relative_to(self.library_dir))
            try:
                document = self.loader_registry.load(path)
                documents.append(document)
                
                # Chunk document
                for text in chunk_text(
                    document.text,
                    max_chars=self.settings.chunking.max_chars,
                    overlap=self.settings.chunking.overlap,
                ):
                    chunks.append(Chunk(
                        chunk_id=chunk_id,
                        source=document.source,
                        title=document.title,
                        text=text,
                    ))
                    chunk_id += 1
                    
            except Exception as e:
                logger.warning(f"Failed to load {relative_path}: {e}")
                skipped_files.append((relative_path, str(e)))
        
        if not chunks:
            raise ConfigurationError(
                message="Document library has no readable content after extraction",
            )
        
        logger.info(f"Extracted {len(chunks)} chunks from {len(documents)} documents")
        
        # Build token statistics
        token_counters: List[Counter] = []
        document_frequencies: Counter = Counter()
        title_token_sets: List[Set[str]] = []
        
        for chunk in chunks:
            counter = Counter(tokenize(chunk.text))
            token_counters.append(counter)
            document_frequencies.update(counter.keys())
            title_token_sets.append(set(tokenize(chunk.title)))
        
        # Calculate IDF
        total_chunks = len(chunks)
        idf: Dict[str, float] = {}
        for token, frequency in document_frequencies.items():
            idf[token] = math.log((total_chunks + 1) / (frequency + 0.5)) + 1.0
        
        # Generate embeddings
        embed_start = time.time()
        chunk_embeddings = tuple(self.embedding_backend.embed_texts(
            [chunk.text for chunk in chunks]
        ))
        embed_time = (time.time() - embed_start) * 1000
        logger.info(f"Generated embeddings in {embed_time:.2f}ms")
        
        # Calculate average document length
        total_tokens = sum(sum(c.values()) for c in token_counters)
        avgdl = total_tokens / total_chunks if total_chunks else 0.0
        
        snapshot = IndexSnapshot(
            library_dir=self.library_dir,
            documents=tuple(documents),
            skipped_files=tuple(skipped_files),
            chunks=tuple(chunks),
            chunk_embeddings=chunk_embeddings,
            chunk_token_counts=tuple(token_counters),
            chunk_title_token_sets=tuple(frozenset(s) for s in title_token_sets),
            idf=idf,
            avgdl=avgdl,
            supported_formats=tuple(self.loader_registry.get_supported_extensions()),
            embedding_backend=self.embedding_backend.name,
            reranker_backend=self.reranker_backend.name,
            retrieval_strategy="dense-embedding-cosine+bm25",
            rerank_strategy=self.reranker_backend.strategy,
        )
        
        # Save to cache
        if self.settings.cache.enabled:
            self._save_to_cache(snapshot)
        
        build_time = (time.time() - start_time) * 1000
        self.metrics.record("index_build_time_ms", build_time)
        self.metrics.gauge("chunk_count", len(chunks))
        self.metrics.gauge("document_count", len(documents))
        
        logger.info(f"Index built in {build_time:.2f}ms")
        return snapshot
    
    def _load_from_cache(self, source_files: List[Path]) -> Optional[IndexSnapshot]:
        """Load snapshot from cache if valid."""
        try:
            if not self._cache_path.exists():
                return None
            
            # Check if cache is stale
            last_modified = max(p.stat().st_mtime for p in source_files)
            if self._cache_path.stat().st_mtime < last_modified:
                return None
            
            with gzip.open(self._cache_path, 'rb') as f:
                cached: IndexSnapshot = pickle.load(f)
            
            # Validate cache compatibility
            if (
                cached.library_dir == self.library_dir
                and cached.embedding_backend == self.embedding_backend.name
                and cached.reranker_backend == self.reranker_backend.name
            ):
                self.metrics.increment("cache_hits")
                return cached
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
        
        self.metrics.increment("cache_misses")
        return None
    
    def _save_to_cache(self, snapshot: IndexSnapshot) -> None:
        """Save snapshot to cache."""
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(self._cache_path, 'wb') as f:
                pickle.dump(snapshot, f)
            logger.info(f"Saved index to cache: {self._cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _weighted_overlap(
        self,
        query_tokens: Set[str],
        candidate_tokens: Set[str],
        idf: Dict[str, float],
    ) -> float:
        """Calculate weighted overlap between query and candidate tokens."""
        if not query_tokens:
            return 0.0
        
        overlap = query_tokens & candidate_tokens
        if not overlap:
            return 0.0
        
        numerator = sum(idf.get(token, 1.0) for token in overlap)
        denominator = sum(idf.get(token, 1.0) for token in query_tokens)
        return numerator / denominator if denominator else 0.0
    
    def _bm25_score(
        self,
        query_tokens: Set[str],
        chunk_tokens: Counter,
        idf: Dict[str, float],
        avgdl: float,
    ) -> float:
        """Calculate BM25 score."""
        import math
        config = self.settings.retrieval
        
        score = 0.0
        doc_len = sum(chunk_tokens.values())
        if avgdl == 0:
            return 0.0
        
        for token in query_tokens:
            if token not in chunk_tokens:
                continue
            tf = chunk_tokens[token]
            idf_val = idf.get(token, 0.0)
            numerator = idf_val * tf * (config.bm25_k1 + 1)
            denominator = tf + config.bm25_k1 * (1 - config.bm25_b + config.bm25_b * doc_len / avgdl)
            score += numerator / denominator
        
        return score
    
    def search(self, query: str, top_k: int = 3) -> List[SearchHit]:
        """Synchronous search."""
        return asyncio.run(self.search_async(query, top_k))
    
    async def search_async(self, query: str, top_k: int = 3) -> List[SearchHit]:
        """Asynchronous search with metrics."""
        start_time = time.time()
        
        with self._lock:
            snapshot = self._snapshot
        
        if not snapshot:
            raise RetrievalError(message="Index not initialized")
        
        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []
        
        try:
            # Embed query
            embed_start = time.time()
            query_embedding = await self.embedding_backend.embed_query_async(query)
            embed_time = (time.time() - embed_start) * 1000
            self.metrics.record("embedding_time_ms", embed_time)
            
            if not any(query_embedding):
                return []
            
            # Dense retrieval
            retrieve_start = time.time()
            retrieve_hits: List[Tuple[int, float]] = []
            for index, chunk_embedding in enumerate(snapshot.chunk_embeddings):
                score = cosine_similarity(query_embedding, chunk_embedding)
                if score > 0:
                    retrieve_hits.append((index, score))
            
            retrieve_hits.sort(key=lambda x: x[1], reverse=True)
            retrieve_time = (time.time() - retrieve_start) * 1000
            self.metrics.record("retrieval_time_ms", retrieve_time)
            
            if not retrieve_hits:
                return []
            
            # Build candidate pool
            candidate_size = min(
                self.reranker_backend.candidate_pool_size(top_k),
                len(retrieve_hits),
            )
            candidates: List[CandidateScore] = []
            
            for index, retrieve_score in retrieve_hits[:candidate_size]:
                candidates.append(CandidateScore(
                    index=index,
                    retrieve_score=retrieve_score,
                    lexical_score=self._bm25_score(
                        query_tokens,
                        snapshot.chunk_token_counts[index],
                        snapshot.idf,
                        snapshot.avgdl,
                    ),
                    title_score=self._weighted_overlap(
                        query_tokens,
                        set(snapshot.chunk_title_token_sets[index]),
                        snapshot.idf,
                    ),
                    rerank_score=retrieve_score,
                ))
            
            # Rerank
            rerank_start = time.time()
            ranked = await self.reranker_backend.rerank_async(query, snapshot, candidates)
            rerank_time = (time.time() - rerank_start) * 1000
            self.metrics.record("rerank_time_ms", rerank_time)
            
            # Build results
            hits: List[SearchHit] = []
            for candidate in ranked[:top_k]:
                hits.append(SearchHit(
                    chunk=snapshot.chunks[candidate.index],
                    score=candidate.rerank_score,
                    retrieve_score=candidate.retrieve_score,
                    rerank_score=candidate.rerank_score,
                    lexical_score=candidate.lexical_score,
                    title_score=candidate.title_score,
                    llm_score=candidate.llm_score,
                ))
            
            total_time = (time.time() - start_time) * 1000
            self.metrics.record("search_total_time_ms", total_time)
            self.metrics.increment("search_queries")
            
            return hits
            
        except Exception as e:
            self.metrics.increment("search_errors")
            if isinstance(e, RetrievalError):
                raise
            raise RetrievalError(message=f"Search failed: {str(e)}", query=query) from e
    
    def answer(self, query: str, top_k: int = 3) -> RagResponse:
        """Synchronous answer generation."""
        return asyncio.run(self.answer_async(query, top_k))
    
    async def answer_async(self, query: str, top_k: int = 3) -> RagResponse:
        """Asynchronous answer generation."""
        start_time = time.time()
        
        hits = await self.search_async(query, top_k)
        
        if not hits:
            return RagResponse(
                query=query,
                answer_lines=["Document library does not contain relevant content. Try rephrasing your query or adding more documents."],
                hits=[],
                metadata={"total_time_ms": (time.time() - start_time) * 1000},
            )
        
        # Extract answer sentences
        query_tokens = set(tokenize(query))
        sentence_candidates: List[Tuple[float, str]] = []
        
        for hit in hits:
            for sentence in split_sentences(hit.chunk.text):
                if sentence.rstrip("。！？!? ").strip() == hit.chunk.title.strip():
                    continue
                sentence_tokens = set(tokenize(sentence))
                overlap = len(query_tokens & sentence_tokens)
                if overlap == 0:
                    continue
                score = hit.score * (1 + overlap / max(len(query_tokens), 1))
                sentence_candidates.append((score, sentence.strip()))
        
        sentence_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score = sentence_candidates[0][0] if sentence_candidates else 0.0
        
        # Build answer
        answer_lines: List[str] = []
        seen = set()
        for score, sentence in sentence_candidates:
            if best_score and score < best_score * 0.35:
                continue
            normalized = sentence.strip()
            if len(normalized) < self.settings.chunking.min_sentence_length or normalized in seen:
                continue
            seen.add(normalized)
            answer_lines.append(normalized if normalized.endswith("。") else normalized + "。")
            if len(answer_lines) == 3:
                break
        
        if not answer_lines:
            fallback = hits[0].chunk.text.strip()
            answer_lines = [fallback if fallback.endswith("。") else fallback + "。"]
        
        total_time = (time.time() - start_time) * 1000
        self.metrics.record("answer_generation_time_ms", total_time)
        self.metrics.increment("answers_generated")
        
        return RagResponse(
            query=query,
            answer_lines=answer_lines,
            hits=hits,
            metadata={"total_time_ms": total_time},
        )
    
    def reload(self) -> None:
        """Synchronous index reload."""
        asyncio.run(self.reload_async())
    
    async def reload_async(self) -> None:
        """Asynchronous index reload."""
        start_time = time.time()
        
        with self._lock:
            self._snapshot = self._build_snapshot()
        
        reload_time = (time.time() - start_time) * 1000
        log_performance(logger, "index_reload", reload_time)
        logger.info(f"Index reloaded in {reload_time:.2f}ms")
    
    def list_documents(self) -> List[Dict[str, object]]:
        """List all documents in library."""
        with self._lock:
            snapshot = self._snapshot
        
        return [
            {
                "source": doc.source,
                "title": doc.title,
                "file_type": doc.file_type,
                "chars": len(doc.text),
            }
            for doc in snapshot.documents
        ]
    
    def stats(self) -> Dict[str, object]:
        """Get system statistics."""
        with self._lock:
            snapshot = self._snapshot
        
        return {
            "library_dir": str(snapshot.library_dir),
            "documents": len(snapshot.documents),
            "chunks": len(snapshot.chunks),
            "supported_formats": list(snapshot.supported_formats),
            "files": self.list_documents(),
            "skipped": [{"source": src, "error": err} for src, err in snapshot.skipped_files],
            "embedding_backend": snapshot.embedding_backend,
            "reranker_backend": snapshot.reranker_backend,
            "retrieval_strategy": snapshot.retrieval_strategy,
            "rerank_strategy": snapshot.rerank_strategy,
        }
