"""Unit tests for vector store implementations."""

import numpy as np
import pytest
import tempfile
from pathlib import Path

from rag_system.backends.vector_store import (
    VectorStore,
    NumpyVectorStore,
    FaissVectorStore,
    create_vector_store,
)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class TestNumpyVectorStore:
    """Tests for NumpyVectorStore."""
    
    def test_create_store(self):
        """Test creating a numpy vector store."""
        store = NumpyVectorStore(dimension=128)
        assert store.dimension == 128
        assert store.size == 0
    
    def test_add_vectors(self):
        """Test adding vectors to the store."""
        store = NumpyVectorStore(dimension=128)
        vectors = np.random.randn(10, 128).astype(np.float32)
        store.add(vectors)
        assert store.size == 10
    
    def test_add_vectors_in_batches(self):
        """Test adding vectors in multiple batches."""
        store = NumpyVectorStore(dimension=64)
        vectors1 = np.random.randn(5, 64).astype(np.float32)
        vectors2 = np.random.randn(5, 64).astype(np.float32)
        store.add(vectors1)
        store.add(vectors2)
        assert store.size == 10
    
    def test_search(self):
        """Test searching for nearest neighbors."""
        store = NumpyVectorStore(dimension=64)
        vectors = np.random.randn(100, 64).astype(np.float32)
        store.add(vectors)
        
        query = vectors[0]
        distances, indices = store.search(query, k=5)
        
        assert len(distances) == 5
        assert len(indices) == 5
        assert indices[0] == 0  # First result should be the query itself
    
    def test_search_empty_store(self):
        """Test searching an empty store."""
        store = NumpyVectorStore(dimension=64)
        query = np.random.randn(64).astype(np.float32)
        distances, indices = store.search(query, k=5)
        
        assert len(distances) == 0
        assert len(indices) == 0
    
    def test_search_rejects_batch_queries(self):
        """Test that batch queries are rejected."""
        store = NumpyVectorStore(dimension=64)
        vectors = np.random.randn(10, 64).astype(np.float32)
        store.add(vectors)
        
        batch_query = np.random.randn(3, 64).astype(np.float32)
        with pytest.raises(ValueError, match="Batch queries are not supported"):
            store.search(batch_query, k=5)
    
    def test_save_and_load(self):
        """Test saving and loading the store."""
        store = NumpyVectorStore(dimension=64)
        vectors = np.random.randn(50, 64).astype(np.float32)
        store.add(vectors)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_store.npz"
            store.save(str(path))
            
            new_store = NumpyVectorStore()
            new_store.load(str(path))
            
            assert new_store.size == 50
            assert new_store.dimension == 64
    
    def test_dimension_mismatch(self):
        """Test that dimension mismatch raises error."""
        store = NumpyVectorStore(dimension=64)
        vectors = np.random.randn(10, 128).astype(np.float32)
        
        with pytest.raises(ValueError, match="dimension mismatch"):
            store.add(vectors)


class TestFaissVectorStore:
    """Tests for FaissVectorStore."""
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
    def test_create_store(self):
        """Test creating a FAISS vector store."""
        store = FaissVectorStore(dimension=128)
        assert store.dimension == 128
        assert store.size == 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
    def test_add_and_search(self):
        """Test adding vectors and searching."""
        store = FaissVectorStore(dimension=64)
        vectors = np.random.randn(100, 64).astype(np.float32)
        store.add(vectors)
        
        assert store.size == 100
        
        query = vectors[0]
        distances, indices = store.search(query, k=5)
        
        assert len(distances) == 5
        assert len(indices) == 5
        assert indices[0] == 0
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
    def test_save_and_load(self):
        """Test saving and loading FAISS index."""
        store = FaissVectorStore(dimension=64)
        vectors = np.random.randn(50, 64).astype(np.float32)
        store.add(vectors)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_faiss.index"
            store.save(str(path))
            
            new_store = FaissVectorStore()
            new_store.load(str(path))
            
            assert new_store.size == 50
            assert new_store.dimension == 64
    
    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="faiss-cpu not installed")
    def test_ivf_index_type(self):
        """Test IVF index type."""
        store = FaissVectorStore(dimension=64, index_type="ivf")
        vectors = np.random.randn(100, 64).astype(np.float32)
        store.add(vectors)
        
        query = vectors[0]
        distances, indices = store.search(query, k=5)
        
        assert len(indices) == 5


class TestVectorStoreFactory:
    """Tests for vector store factory function."""
    
    def test_create_numpy_store(self):
        """Test creating numpy store via factory."""
        store = create_vector_store(backend="numpy", dimension=128)
        assert isinstance(store, NumpyVectorStore)
    
    def test_create_faiss_store(self):
        """Test creating FAISS store via factory."""
        store = create_vector_store(backend="faiss", dimension=128)
        assert isinstance(store, FaissVectorStore)
    
    def test_default_backend(self):
        """Test default backend is numpy."""
        store = create_vector_store(dimension=128)
        assert isinstance(store, NumpyVectorStore)