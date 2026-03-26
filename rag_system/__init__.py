"""RAG System - Production-ready Retrieval-Augmented Generation."""

__version__ = "2.0.0"

from .core import (
    EmbeddingBackend,
    RerankerBackend,
    SearchEngine,
    SourceDocument,
    Chunk,
    SearchHit,
    RagResponse,
)
from .backends import (
    LocalHashEmbeddingBackend,
    OpenAICompatibleEmbeddingBackend,
    LocalHeuristicReranker,
    OpenAICompatibleListwiseReranker,
)
from .config import Settings, get_settings
from .exceptions import RAGError
from .rag_engine import RAGEngine

__all__ = [
    "RAGEngine",
    "EmbeddingBackend",
    "RerankerBackend",
    "SearchEngine",
    "SourceDocument",
    "Chunk",
    "SearchHit",
    "RagResponse",
    "LocalHashEmbeddingBackend",
    "OpenAICompatibleEmbeddingBackend",
    "LocalHeuristicReranker",
    "OpenAICompatibleListwiseReranker",
    "Settings",
    "get_settings",
    "RAGError",
]
