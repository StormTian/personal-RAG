"""Core abstractions and interfaces for RAG system."""

from .base import (
    EmbeddingBackend,
    RerankerBackend,
    DocumentLoader,
    TextChunker,
    SearchEngine,
    IndexSnapshot,
    SourceDocument,
    Chunk,
    CandidateScore,
    SearchHit,
    RagResponse,
)
from .dependency_injection import (
    Container,
    DependencyProvider,
    Singleton,
    Factory,
    inject,
)

__all__ = [
    "EmbeddingBackend",
    "RerankerBackend",
    "DocumentLoader",
    "TextChunker",
    "SearchEngine",
    "IndexSnapshot",
    "SourceDocument",
    "Chunk",
    "CandidateScore",
    "SearchHit",
    "RagResponse",
    "Container",
    "DependencyProvider",
    "Singleton",
    "Factory",
    "inject",
]
