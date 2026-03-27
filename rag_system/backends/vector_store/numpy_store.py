"""Numpy-based vector store implementation."""

from typing import List, Tuple
import numpy as np
from .base import VectorStore


class NumpyVectorStore(VectorStore):
    """Simple numpy-based vector store using brute-force search."""
    
    def __init__(self, dimension: int = 256):
        self._dimension = dimension
        self._vectors: np.ndarray = np.array([]).reshape(0, dimension)
    
    def add(self, vectors: np.ndarray) -> None:
        """Add vectors to the index."""
        vectors = np.atleast_2d(vectors)
        if vectors.shape[1] != self._dimension:
            raise ValueError(
                f"Vector dimension mismatch: expected {self._dimension}, got {vectors.shape[1]}"
            )
        self._vectors = np.vstack([self._vectors, vectors]) if self._vectors.size else vectors
    
    def search(self, query: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for k nearest neighbors using cosine similarity.
        
        Note: Batch queries (multiple query vectors) are not supported.
        Only single query vector searches are handled.
        """
        query = np.atleast_2d(query)
        if query.shape[0] > 1:
            raise ValueError(
                f"Batch queries are not supported. Expected single query vector, "
                f"got {query.shape[0]} vectors. Call search() once per query."
            )
        if self._vectors.size == 0:
            return np.array([]), np.array([])
        
        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(self._vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normalized = self._vectors / norms
        
        query_norms = np.linalg.norm(query, axis=1, keepdims=True)
        query_norms = np.where(query_norms == 0, 1, query_norms)
        normalized_query = query / query_norms
        
        # Compute similarities
        similarities = normalized_query @ normalized.T
        
        # Get top k
        k = min(k, len(self._vectors))
        if k <= 0:
            return np.array([]), np.array([])
        
        indices = np.argsort(-similarities[0])[:k]
        distances = 1 - similarities[0][indices]  # Convert similarity to distance
        
        return distances, indices
    
    def save(self, path: str) -> None:
        """Save vectors to numpy file."""
        np.savez(path, vectors=self._vectors, dimension=np.array([self._dimension]))
    
    def load(self, path: str) -> None:
        """Load vectors from numpy file."""
        data = np.load(path)
        self._vectors = data["vectors"]
        self._dimension = int(data["dimension"][0])
    
    def clear(self) -> None:
        """Clear all vectors from the index."""
        self._vectors = np.array([]).reshape(0, self._dimension)
    
    @property
    def size(self) -> int:
        """Number of vectors in the index."""
        return len(self._vectors)
    
    @property
    def dimension(self) -> int:
        """Dimension of vectors."""
        return self._dimension