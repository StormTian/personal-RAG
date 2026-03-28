"""Tests for BM25Store persistence storage."""

import pytest
import tempfile
from pathlib import Path
from rag_system.index.bm25_store import BM25Store


class TestBM25Store:
    def test_init(self):
        """Test BM25Store initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BM25Store(cache_dir=Path(tmpdir), k1=1.5, b=0.75)
            assert store._k1 == 1.5
            assert store._b == 0.75
            assert len(store._term_freq) == 0
            assert len(store._doc_freq) == 0
            assert store._avg_doc_length == 0.0
            assert store._total_docs == 0

    def test_update_terms(self):
        """Test updating term frequency statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BM25Store(cache_dir=Path(tmpdir))
            
            # Create a simple chunk
            from rag_system.core.base import Chunk
            chunk = Chunk(text="hello world test", source="test.txt", title="Test", chunk_id=0)
            
            store.update_terms(chunk, 0)
            
            # Check term frequency
            assert "hello" in store._term_freq
            assert store._term_freq["hello"][0] == 1
            assert "world" in store._term_freq
            assert "test" in store._term_freq
            
            # Check document frequency
            assert store._doc_freq["hello"] == 1
            assert store._doc_freq["world"] == 1
            
            # Check document length
            assert store._doc_length[0] == 3  # 3 tokens
            assert store._avg_doc_length == 3.0
            assert store._total_docs == 1

    def test_remove_terms(self):
        """Test removing term frequency statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BM25Store(cache_dir=Path(tmpdir))
            
            from rag_system.core.base import Chunk
            chunk1 = Chunk(text="hello world", source="test1.txt", title="Test1", chunk_id=0)
            chunk2 = Chunk(text="hello test", source="test2.txt", title="Test2", chunk_id=1)
            
            store.update_terms(chunk1, 0)
            store.update_terms(chunk2, 1)
            
            assert store._doc_freq["hello"] == 2
            
            # Remove chunk 0
            store.remove_terms([0])
            
            assert 0 not in store._doc_length
            assert "hello" not in store._term_freq or 0 not in store._term_freq.get("hello", {})
            assert store._doc_freq["hello"] == 1  # hello still in chunk 1
            assert store._total_docs == 1

    def test_get_bm25_score(self):
        """Test BM25 score calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BM25Store(cache_dir=Path(tmpdir))
            
            from rag_system.core.base import Chunk
            chunk1 = Chunk(text="hello world python code", source="test1.txt", title="Test1", chunk_id=0)
            chunk2 = Chunk(text="hello python programming", source="test2.txt", title="Test2", chunk_id=1)
            
            store.update_terms(chunk1, 0)
            store.update_terms(chunk2, 1)
            
            score = store.get_bm25_score("hello python", 0)
            
            assert score > 0
            assert isinstance(score, float)

    def test_save_and_load(self):
        """Test persistence save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            # Create and populate store
            store1 = BM25Store(cache_dir=cache_dir)
            from rag_system.core.base import Chunk
            chunk = Chunk(text="hello world test", source="test.txt", title="Test", chunk_id=0)
            store1.update_terms(chunk, 0)
            store1.save()
            
            # Load into new store
            store2 = BM25Store(cache_dir=cache_dir)
            result = store2.load()
            
            assert result is True
            assert store2._term_freq == store1._term_freq
            assert store2._doc_freq == store1._doc_freq
            assert store2._doc_length == store1._doc_length
            assert store2._avg_doc_length == store1._avg_doc_length
            assert store2._total_docs == store1._total_docs

    def test_load_nonexistent(self):
        """Test loading from non-existent cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BM25Store(cache_dir=Path(tmpdir))
            result = store.load()
            assert result is False

    def test_clear(self):
        """Test clearing all statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BM25Store(cache_dir=Path(tmpdir))
            
            from rag_system.core.base import Chunk
            chunk = Chunk(text="hello world", source="test.txt", title="Test", chunk_id=0)
            store.update_terms(chunk, 0)
            
            assert store._total_docs == 1
            
            store.clear()
            
            assert len(store._term_freq) == 0
            assert len(store._doc_freq) == 0
            assert len(store._doc_length) == 0
            assert store._avg_doc_length == 0.0
            assert store._total_docs == 0

    def test_thread_safety(self):
        """Test thread-safe operations."""
        import threading
        
        with tempfile.TemporaryDirectory() as tmpdir:
            store = BM25Store(cache_dir=Path(tmpdir))
            from rag_system.core.base import Chunk
            
            def add_chunks(thread_id):
                for i in range(10):
                    chunk_id = thread_id * 10 + i
                    chunk = Chunk(text=f"word{i} test", source="test.txt", title="Test", chunk_id=chunk_id)
                    store.update_terms(chunk, chunk_id)
            
            threads = [threading.Thread(target=add_chunks, args=(i,)) for i in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            assert store._total_docs == 30
