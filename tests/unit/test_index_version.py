"""Unit tests for IndexVersion."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from rag_system.index.version import IndexVersion, SnapshotInfo


class TestIndexVersion:
    """Tests for IndexVersion class."""

    def test_init(self):
        """Test IndexVersion initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir, max_snapshots=5)
            
            assert version._cache_dir == cache_dir
            assert version._snapshots_dir == cache_dir / "snapshots"
            assert version._max_snapshots == 5

    def test_init_default_max_snapshots(self):
        """Test default max_snapshots value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            version = IndexVersion(cache_dir=Path(tmpdir))
            assert version._max_snapshots == 5


class TestIndexVersionCreateSnapshot:
    """Tests for create_snapshot method."""

    def test_create_snapshot_success(self):
        """Test successful snapshot creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir)
            
            # Create some mock index files
            (cache_dir / "faiss.index").write_text("mock index")
            (cache_dir / "bm25_term_freq.pkl.gz").write_text("mock bm25")
            
            snapshot_name = version.create_snapshot("test_snapshot")
            
            assert snapshot_name is not None
            snapshot_dir = version._snapshots_dir / snapshot_name
            assert snapshot_dir.exists()
            assert (snapshot_dir / "faiss.index").exists()
            assert (snapshot_dir / "metadata.json").exists()

    def test_create_snapshot_auto_name(self):
        """Test snapshot creation with auto-generated name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir)
            
            (cache_dir / "faiss.index").write_text("mock index")
            
            snapshot_name = version.create_snapshot()
            
            assert snapshot_name is not None
            assert snapshot_name.startswith("v")  # Should start with 'v'

    def test_create_snapshot_no_files(self):
        """Test snapshot creation when no index files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir)
            
            snapshot_name = version.create_snapshot("empty")
            
            # Should still create snapshot directory with metadata
            snapshot_dir = version._snapshots_dir / "empty"
            assert snapshot_dir.exists()
            assert (snapshot_dir / "metadata.json").exists()


class TestIndexVersionListSnapshots:
    """Tests for list_snapshots method."""

    def test_list_empty(self):
        """Test listing snapshots when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            version = IndexVersion(cache_dir=Path(tmpdir))
            
            snapshots = version.list_snapshots()
            
            assert snapshots == []

    def test_list_multiple_snapshots(self):
        """Test listing multiple snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir)
            
            # Create two snapshots
            (cache_dir / "faiss.index").write_text("index")
            version.create_snapshot("snapshot1")
            version.create_snapshot("snapshot2")
            
            snapshots = version.list_snapshots()
            
            assert len(snapshots) == 2
            names = [s.name for s in snapshots]
            assert "snapshot1" in names
            assert "snapshot2" in names

    def test_list_snapshots_sorted_by_timestamp(self):
        """Test that snapshots are sorted by timestamp (newest first)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir)
            
            (cache_dir / "faiss.index").write_text("index")
            version.create_snapshot("older")
            import time
            time.sleep(0.01)
            version.create_snapshot("newer")
            
            snapshots = version.list_snapshots()
            
            assert snapshots[0].name == "newer"
            assert snapshots[1].name == "older"


class TestIndexVersionRestoreSnapshot:
    """Tests for restore_snapshot method."""

    def test_restore_snapshot_success(self):
        """Test successful snapshot restoration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir)
            
            # Create original file and snapshot
            (cache_dir / "faiss.index").write_text("original content")
            version.create_snapshot("test_restore")
            
            # Modify the original
            (cache_dir / "faiss.index").write_text("modified content")
            
            # Restore
            result = version.restore_snapshot("test_restore")
            
            assert result is True
            restored_content = (cache_dir / "faiss.index").read_text()
            assert restored_content == "original content"

    def test_restore_nonexistent_snapshot(self):
        """Test restoring a non-existent snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            version = IndexVersion(cache_dir=Path(tmpdir))
            
            result = version.restore_snapshot("nonexistent")
            
            assert result is False

    def test_restore_corrupted_metadata(self):
        """Test handling of corrupted metadata file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir)
            
            # Create snapshot with corrupted metadata
            snapshot_dir = version._snapshots_dir / "corrupted"
            snapshot_dir.mkdir(parents=True)
            (snapshot_dir / "metadata.json").write_text("not valid json")
            
            result = version.restore_snapshot("corrupted")
            
            assert result is False


class TestIndexVersionDeleteSnapshot:
    """Tests for delete_snapshot method."""

    def test_delete_snapshot_success(self):
        """Test successful snapshot deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir)
            
            (cache_dir / "faiss.index").write_text("index")
            version.create_snapshot("to_delete")
            
            result = version.delete_snapshot("to_delete")
            
            assert result is True
            assert not (version._snapshots_dir / "to_delete").exists()

    def test_delete_nonexistent_snapshot(self):
        """Test deleting a non-existent snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            version = IndexVersion(cache_dir=Path(tmpdir))
            
            result = version.delete_snapshot("nonexistent")
            
            assert result is False


class TestIndexVersionCleanup:
    """Tests for cleanup_old_snapshots method."""

    def test_cleanup_removes_old_snapshots(self):
        """Test that old snapshots are removed when exceeding max."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir, max_snapshots=2)
            
            (cache_dir / "faiss.index").write_text("index")
            
            # Create 3 snapshots
            version.create_snapshot("snapshot1")
            import time
            time.sleep(0.01)
            version.create_snapshot("snapshot2")
            time.sleep(0.01)
            version.create_snapshot("snapshot3")
            
            # Cleanup should remove the oldest
            removed = version.cleanup_old_snapshots()
            
            assert removed == 1
            snapshots = version.list_snapshots()
            assert len(snapshots) == 2
            names = [s.name for s in snapshots]
            assert "snapshot1" not in names

    def test_cleanup_no_action_needed(self):
        """Test cleanup when under max_snapshots limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            version = IndexVersion(cache_dir=cache_dir, max_snapshots=5)
            
            (cache_dir / "faiss.index").write_text("index")
            version.create_snapshot("snapshot1")
            
            removed = version.cleanup_old_snapshots()
            
            assert removed == 0
            assert len(version.list_snapshots()) == 1


class TestSnapshotInfo:
    """Tests for SnapshotInfo dataclass."""

    def test_snapshot_info_creation(self):
        """Test SnapshotInfo dataclass creation."""
        info = SnapshotInfo(
            name="test_snapshot",
            timestamp=datetime.now(),
            doc_count=42,
            chunk_count=156,
            checksum="abc123",
        )
        
        assert info.name == "test_snapshot"
        assert info.doc_count == 42
        assert info.chunk_count == 156
        assert info.checksum == "abc123"
