"""Abstract base class for vector stores."""

from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np


class VectorStore(ABC):
    """Abstract base class for vector similarity search."""
    
    @abstractmethod
    def add(self, vectors: np.ndarray) -> None:
        """Add vectors to the index.
        
        Args:
            vectors: Array of shape (n, d) where n is number of vectors, d is dimension.
        """
        pass
    
    @abstractmethod
    def search(self, query: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for k nearest neighbors.
        
        Args:
            query: Query vector of shape (d,) or (n, d).
            k: Number of neighbors to return.
            
        Returns:
            Tuple of (distances, indices) arrays.
        """
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """Save index to disk."""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load index from disk."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all vectors from the index."""
        pass
    
    @property
    @abstractmethod
    def size(self) -> int:
        """Number of vectors in the index."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimension of vectors."""
        pass
    
    def __len__(self) -> int:
        """Return number of vectors in the index."""
        return self.size