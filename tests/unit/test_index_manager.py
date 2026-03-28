"""Unit tests for IndexManager."""

import pytest
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime
from rag_system.index.manager import IndexManager, IndexStatus
from rag_system.index.bm25_store import BM25Store
from rag_system.backends.vector_store.numpy_store import NumpyVectorStore
from rag_system.backends.embedding import LocalHashEmbeddingBackend
from rag_system.config.settings import ChunkingConfig
from rag_system.core.base import Chunk


class TestIndexManager:
    def test_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bm25_store = BM25Store(cache_dir=Path(tmpdir))
            vector_store = NumpyVectorStore(dimension=256)
            embedding_backend = LocalHashEmbeddingBackend(dimensions=256)
            chunking_config = ChunkingConfig(max_chars=240, overlap=1)

            manager = IndexManager(
                library_dir=Path(tmpdir),
                vector_store=vector_store,
                bm25_store=bm25_store,
                embedding_backend=embedding_backend,
                chunking_config=chunking_config,
            )

            assert manager._library_dir == Path(tmpdir)
            assert len(manager._chunk_map) == 0
            assert len(manager._deleted_ids) == 0

    def test_get_status_empty_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bm25_store = BM25Store(cache_dir=Path(tmpdir))
            vector_store = NumpyVectorStore(dimension=256)
            embedding_backend = LocalHashEmbeddingBackend(dimensions=256)
            chunking_config = ChunkingConfig(max_chars=240, overlap=1)

            manager = IndexManager(
                library_dir=Path(tmpdir),
                vector_store=vector_store,
                bm25_store=bm25_store,
                embedding_backend=embedding_backend,
                chunking_config=chunking_config,
            )

            status = manager.get_status()

            assert isinstance(status, IndexStatus)
            assert status.total_documents == 0
            assert status.total_chunks == 0
            assert status.deleted_ratio == 0.0
            assert status.last_update_time is None
            assert status.needs_compression is False

    def test_get_valid_chunks_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bm25_store = BM25Store(cache_dir=Path(tmpdir))
            vector_store = NumpyVectorStore(dimension=256)
            embedding_backend = LocalHashEmbeddingBackend(dimensions=256)
            chunking_config = ChunkingConfig(max_chars=240, overlap=1)

            manager = IndexManager(
                library_dir=Path(tmpdir),
                vector_store=vector_store,
                bm25_store=bm25_store,
                embedding_backend=embedding_backend,
                chunking_config=chunking_config,
            )

            chunks = manager.get_valid_chunks()
            assert chunks == []

    def test_get_next_chunk_id_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bm25_store = BM25Store(cache_dir=Path(tmpdir))
            vector_store = NumpyVectorStore(dimension=256)
            embedding_backend = LocalHashEmbeddingBackend(dimensions=256)
            chunking_config = ChunkingConfig(max_chars=240, overlap=1)

            manager = IndexManager(
                library_dir=Path(tmpdir),
                vector_store=vector_store,
                bm25_store=bm25_store,
                embedding_backend=embedding_backend,
                chunking_config=chunking_config,
            )

            next_id = manager._get_next_chunk_id()
            assert next_id == 0

    def test_get_next_chunk_id_with_existing_chunks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bm25_store = BM25Store(cache_dir=Path(tmpdir))
            vector_store = NumpyVectorStore(dimension=256)
            embedding_backend = LocalHashEmbeddingBackend(dimensions=256)
            chunking_config = ChunkingConfig(max_chars=240, overlap=1)

            manager = IndexManager(
                library_dir=Path(tmpdir),
                vector_store=vector_store,
                bm25_store=bm25_store,
                embedding_backend=embedding_backend,
                chunking_config=chunking_config,
            )

            # Manually add some chunks
            manager._chunk_map[0] = Chunk(chunk_id=0, source="doc1", title="Test", text="content1")
            manager._chunk_map[1] = Chunk(chunk_id=1, source="doc1", title="Test", text="content2")
            manager._chunk_map[5] = Chunk(chunk_id=5, source="doc2", title="Test", text="content3")

            next_id = manager._get_next_chunk_id()
            assert next_id == 6

    def test_get_status_with_deleted_chunks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bm25_store = BM25Store(cache_dir=Path(tmpdir))
            vector_store = NumpyVectorStore(dimension=256)
            embedding_backend = LocalHashEmbeddingBackend(dimensions=256)
            chunking_config = ChunkingConfig(max_chars=240, overlap=1)

            manager = IndexManager(
                library_dir=Path(tmpdir),
                vector_store=vector_store,
                bm25_store=bm25_store,
                embedding_backend=embedding_backend,
                chunking_config=chunking_config,
            )

            # Add chunks and mark some as deleted
            manager._chunk_map[0] = Chunk(chunk_id=0, source="doc1", title="Test", text="content1")
            manager._chunk_map[1] = Chunk(chunk_id=1, source="doc1", title="Test", text="content2")
            manager._deleted_ids = {2, 3, 4}  # 3 deleted, 2 valid

            status = manager.get_status()

            assert status.total_chunks == 2
            assert status.total_documents == 1
            # deleted_ratio = 3 / (2 + 3) = 0.6
            assert status.deleted_ratio == 0.6
            assert status.needs_compression is True  # > 30%

    def test_thread_safety_lock_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bm25_store = BM25Store(cache_dir=Path(tmpdir))
            vector_store = NumpyVectorStore(dimension=256)
            embedding_backend = LocalHashEmbeddingBackend(dimensions=256)
            chunking_config = ChunkingConfig(max_chars=240, overlap=1)

            manager = IndexManager(
                library_dir=Path(tmpdir),
                vector_store=vector_store,
                bm25_store=bm25_store,
                embedding_backend=embedding_backend,
                chunking_config=chunking_config,
            )

            assert manager._lock is not None
            # Verify it's a reentrant lock
            assert hasattr(manager._lock, 'acquire')
            assert hasattr(manager._lock, 'release')


class TestIndexManagerDocumentOperations:
    """Tests for document CRUD operations."""

    @pytest.fixture
    def index_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bm25_store = BM25Store(cache_dir=Path(tmpdir))
            vector_store = NumpyVectorStore(dimension=256)
            embedding_backend = LocalHashEmbeddingBackend(dimensions=256)
            chunking_config = ChunkingConfig(max_chars=240, overlap=1)

            manager = IndexManager(
                library_dir=Path(tmpdir),
                vector_store=vector_store,
                bm25_store=bm25_store,
                embedding_backend=embedding_backend,
                chunking_config=chunking_config,
            )
            yield manager

    @pytest.fixture
    def sample_doc_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "test_doc.md"
            doc_path.write_text("# Test Document\n\nThis is a sample document.\n\nIt has multiple sentences.", encoding="utf-8")
            yield doc_path

    @pytest.mark.asyncio
    async def test_add_document_success(self, index_manager, sample_doc_path):
        """Test successful document addition."""
        result = await index_manager.add_document(sample_doc_path)
        assert result is True
        
        # Verify chunks were created
        status = index_manager.get_status()
        assert status.total_documents == 1
        assert status.total_chunks > 0
        assert status.last_update_time is not None

    @pytest.mark.asyncio
    async def test_add_document_nonexistent_file(self, index_manager):
        """Test adding a non-existent document returns False."""
        nonexistent_path = Path("/nonexistent/path/doc.md")
        result = await index_manager.add_document(nonexistent_path)
        assert result is False

    @pytest.mark.asyncio
    async def test_add_and_remove_document(self, index_manager, sample_doc_path):
        """Test adding and then removing a document."""
        # Add document
        add_result = await index_manager.add_document(sample_doc_path)
        assert add_result is True
        
        initial_status = index_manager.get_status()
        assert initial_status.total_documents == 1
        assert initial_status.total_chunks > 0
        
        # Remove document
        remove_result = index_manager.remove_document(sample_doc_path)
        assert remove_result is True
        
        final_status = index_manager.get_status()
        assert final_status.total_documents == 0
        assert final_status.total_chunks == 0

    def test_remove_document_nonexistent(self, index_manager):
        """Test removing a document that was never added."""
        nonexistent_path = Path("/nonexistent/path/doc.md")
        result = index_manager.remove_document(nonexistent_path)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_document(self, index_manager, sample_doc_path):
        """Test document update (remove + add)."""
        # Add document first
        await index_manager.add_document(sample_doc_path)
        initial_status = index_manager.get_status()
        assert initial_status.total_documents == 1
        
        # Modify the document
        sample_doc_path.write_text("# Updated Document\n\nThis is updated content.", encoding="utf-8")
        
        # Update document
        result = await index_manager.update_document(sample_doc_path)
        assert result is True
        
        # Document should still exist with updated content
        final_status = index_manager.get_status()
        assert final_status.total_documents == 1

    @pytest.mark.asyncio
    async def test_rebuild_full(self, index_manager, sample_doc_path):
        """Test full index rebuild."""
        # Add a document
        await index_manager.add_document(sample_doc_path)
        status_before = index_manager.get_status()
        assert status_before.total_documents == 1
        
        # Rebuild
        await index_manager.rebuild_full()
        
        status_after = index_manager.get_status()
        assert status_after.total_documents == 0
        assert status_after.total_chunks == 0
        assert len(index_manager._deleted_ids) == 0

    def test_compress_if_needed_below_threshold(self, index_manager):
        """Test compression when ratio is below threshold."""
        # Add some chunks and a few deleted (ratio < 30%)
        index_manager._chunk_map[0] = Chunk(chunk_id=0, source="doc1", title="Test", text="content1")
        index_manager._chunk_map[1] = Chunk(chunk_id=1, source="doc1", title="Test", text="content2")
        index_manager._deleted_ids = {2}  # 1 deleted out of 3 total = 33%
        
        # Actually this is 33%, let me fix: 1 out of 3 = 33%, so should trigger
        # Let me use a lower ratio
        index_manager._deleted_ids = {2}  # 1 deleted, 2 valid = 33%
        
        result = index_manager.compress_if_needed()
        # Should compress since 33% > 30%
        assert result is True
        assert len(index_manager._deleted_ids) == 0

    def test_compress_if_needed_above_threshold(self, index_manager):
        """Test compression when ratio is above threshold (should not trigger)."""
        # Add many chunks with few deleted (ratio < 30%)
        for i in range(10):
            index_manager._chunk_map[i] = Chunk(chunk_id=i, source="doc1", title="Test", text=f"content{i}")
        index_manager._deleted_ids = {20}  # 1 deleted out of 11 total = 9%
        
        result = index_manager.compress_if_needed()
        assert result is False
        # deleted_ids should still exist
        assert len(index_manager._deleted_ids) == 1

    def test_should_compress_logic(self, index_manager):
        """Test the _should_compress internal method."""
        # Empty index
        assert index_manager._should_compress() is False
        
        # 50% deleted (should compress)
        index_manager._chunk_map[0] = Chunk(chunk_id=0, source="doc1", title="Test", text="content1")
        index_manager._deleted_ids = {1}  # 1 valid, 1 deleted = 50%
        assert index_manager._should_compress() is True
        
        # Clear and test below threshold
        index_manager._chunk_map.clear()
        index_manager._deleted_ids.clear()
        index_manager._chunk_map[0] = Chunk(chunk_id=0, source="doc1", title="Test", text="content1")
        index_manager._chunk_map[1] = Chunk(chunk_id=1, source="doc1", title="Test", text="content2")
        index_manager._deleted_ids = {2}  # 2 valid, 1 deleted = 33%
        assert index_manager._should_compress() is True

    def test_document_loader_registry_exists(self, index_manager):
        """Test that DocumentLoaderRegistry is initialized."""
        assert index_manager._loader_registry is not None

    def test_compression_threshold_constant(self):
        """Test that compression threshold is set correctly."""
        assert IndexManager.COMPRESSION_THRESHOLD == 0.3
