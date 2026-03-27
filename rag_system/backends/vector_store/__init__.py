"""Vector store backends for efficient similarity search."""

from .base import VectorStore
from .numpy_store import NumpyVectorStore
from .faiss_store import FaissVectorStore

__all__ = ["VectorStore", "NumpyVectorStore", "FaissVectorStore"]


def create_vector_store(backend: str = "numpy", **kwargs) -> VectorStore:
    """Factory function to create vector store."""
    if backend == "faiss":
        return FaissVectorStore(**kwargs)
    return NumpyVectorStore(**kwargs)