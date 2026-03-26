"""Core data models and abstract base classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple
from collections import Counter


@dataclass(frozen=True)
class SourceDocument:
    """Source document model."""
    source: str
    title: str
    text: str
    file_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    """Text chunk model."""
    chunk_id: int
    source: str
    title: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateScore:
    """Candidate scoring model."""
    index: int
    retrieve_score: float
    lexical_score: float
    title_score: float
    rerank_score: float
    llm_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchHit:
    """Search result model."""
    chunk: Chunk
    score: float
    retrieve_score: float
    rerank_score: float
    lexical_score: float
    title_score: float
    llm_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RagResponse:
    """RAG response model."""
    query: str
    answer_lines: List[str]
    hits: List[SearchHit]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, object]:
        """Convert response to dictionary."""
        return {
            "query": self.query,
            "answer_lines": self.answer_lines,
            "hits": [
                {
                    "score": round(hit.score, 4),
                    "retrieve_score": round(hit.retrieve_score, 4),
                    "rerank_score": round(hit.rerank_score, 4),
                    "lexical_score": round(hit.lexical_score, 4),
                    "title_score": round(hit.title_score, 4),
                    "llm_score": round(hit.llm_score, 4),
                    "source": hit.chunk.source,
                    "title": hit.chunk.title,
                    "text": hit.chunk.text,
                    "chunk_id": hit.chunk.chunk_id,
                    "metadata": hit.metadata,
                }
                for hit in self.hits
            ],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class IndexSnapshot:
    """Index snapshot for retrieval."""
    library_dir: Path
    documents: Tuple[SourceDocument, ...]
    skipped_files: Tuple[Tuple[str, str], ...]
    chunks: Tuple[Chunk, ...]
    chunk_embeddings: Tuple[Tuple[float, ...], ...]
    chunk_token_counts: Tuple[Counter, ...]
    chunk_title_token_sets: Tuple[FrozenSet[str], ...]
    idf: Dict[str, float]
    avgdl: float
    supported_formats: Tuple[str, ...]
    embedding_backend: str
    reranker_backend: str
    retrieval_strategy: str
    rerank_strategy: str
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingBackend(ABC):
    """Abstract base class for embedding backends."""
    
    name: str = "embedding-backend"
    
    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Embed multiple texts into vectors."""
        pass
    
    def embed_query(self, text: str) -> Tuple[float, ...]:
        """Embed a single query text."""
        return self.embed_texts([text])[0]
    
    @abstractmethod
    async def embed_texts_async(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        """Async version of embed_texts."""
        pass
    
    async def embed_query_async(self, text: str) -> Tuple[float, ...]:
        """Async version of embed_query."""
        return (await self.embed_texts_async([text]))[0]


class RerankerBackend(ABC):
    """Abstract base class for reranker backends."""
    
    name: str = "reranker-backend"
    strategy: str = "rerank"
    
    def candidate_pool_size(self, top_k: int) -> int:
        """Calculate candidate pool size based on top_k."""
        return max(top_k * 6, 8)
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        """Rerank candidates."""
        pass
    
    @abstractmethod
    async def rerank_async(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        """Async version of rerank."""
        pass


class DocumentLoader(ABC):
    """Abstract base class for document loaders."""
    
    supported_extensions: Set[str] = set()
    
    @abstractmethod
    def load(self, path: Path) -> SourceDocument:
        """Load a document from file path."""
        pass
    
    @abstractmethod
    def can_load(self, path: Path) -> bool:
        """Check if this loader can handle the file."""
        pass


class TextChunker(ABC):
    """Abstract base class for text chunkers."""
    
    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        """Split text into chunks."""
        pass
    
    @abstractmethod
    def chunk_batch(self, texts: Sequence[str]) -> List[List[str]]:
        """Split multiple texts into chunks."""
        pass


class SearchEngine(ABC):
    """Abstract base class for search engines."""
    
    @abstractmethod
    def search(self, query: str, top_k: int = 3) -> List[SearchHit]:
        """Search for relevant documents."""
        pass
    
    @abstractmethod
    def answer(self, query: str, top_k: int = 3) -> RagResponse:
        """Generate answer for query."""
        pass
    
    @abstractmethod
    async def search_async(self, query: str, top_k: int = 3) -> List[SearchHit]:
        """Async version of search."""
        pass
    
    @abstractmethod
    async def answer_async(self, query: str, top_k: int = 3) -> RagResponse:
        """Async version of answer."""
        pass
