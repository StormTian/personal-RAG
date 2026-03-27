"""FAISS-based vector store implementation with lazy import."""

from typing import Tuple
import numpy as np
from .base import VectorStore


class FaissVectorStore(VectorStore):
    """FAISS-based vector store for efficient similarity search."""
    
    def __init__(self, dimension: int = 256, index_type: str = "flat"):
        self._dimension = dimension
        self._index_type = index_type
        self._index = None
        self._size = 0
        self._faiss = None
    
    def _ensure_faiss(self):
        """Lazy import of FAISS."""
        if self._faiss is None:
            try:
                import faiss
                self._faiss = faiss
            except ImportError:
                raise ImportError(
                    "faiss-cpu is required for FAISS vector store. "
                    "Install it with: pip install faiss-cpu"
                )
    
    def _ensure_index(self, n_vectors: int = 0):
        """Create index if needed."""
        if self._index is not None:
            return
        
        self._ensure_faiss()
        
        if self._index_type == "flat":
            self._index = self._faiss.IndexFlatIP(self._dimension)
        elif self._index_type == "ivf":
            nlist = max(1, min(n_vectors // 39, 100))
            quantizer = self._faiss.IndexFlatIP(self._dimension)
            self._index = self._faiss.IndexIVFFlat(quantizer, self._dimension, nlist)
        else:
            self._index = self._faiss.IndexFlatIP(self._dimension)
    
    def add(self, vectors: np.ndarray) -> None:
        """Add vectors to the index."""
        vectors = np.atleast_2d(vectors).astype(np.float32)
        if vectors.shape[1] != self._dimension:
            raise ValueError(
                f"Vector dimension mismatch: expected {self._dimension}, got {vectors.shape[1]}"
            )
        
        self._ensure_index(n_vectors=len(vectors))
        
        # Normalize for cosine similarity (FAISS IP = cosine on normalized vectors)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normalized = vectors / norms
        
        # Train IVF index if needed
        if self._index_type == "ivf" and not self._index.is_trained:
            self._index.train(normalized)
        
        self._index.add(normalized)
        self._size += len(vectors)
    
    def search(self, query: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for k nearest neighbors."""
        if self._index is None or self._size == 0:
            return np.array([]), np.array([])
        
        query = np.atleast_2d(query).astype(np.float32)
        
        # Normalize query
        norms = np.linalg.norm(query, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normalized_query = query / norms
        
        k = min(k, self._size)
        if k <= 0:
            return np.array([]), np.array([])
        
        similarities, indices = self._index.search(normalized_query, k)
        
        # Convert similarity to distance
        distances = 1 - similarities[0]
        
        return distances, indices[0]
    
    def save(self, path: str) -> None:
        """Save index to disk."""
        if self._index is None:
            return
        self._ensure_faiss()
        self._faiss.write_index(self._index, path)
    
    def load(self, path: str) -> None:
        """Load index from disk."""
        self._ensure_faiss()
        self._index = self._faiss.read_index(path)
        self._size = self._index.ntotal
        self._dimension = self._index.d
    
    def clear(self) -> None:
        """Clear all vectors from the index."""
        self._index = None
        self._size = 0
    
    @property
    def size(self) -> int:
        """Number of vectors in the index."""
        return self._size
    
    @property
    def dimension(self) -> int:
        """Dimension of vectors."""
        return self._dimension