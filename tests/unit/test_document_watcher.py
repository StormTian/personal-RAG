"""Unit tests for DocumentWatcher."""

import pytest
import tempfile
import time
import threading
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from rag_system.index.watcher import DocumentWatcher, FileChange


class TestDocumentWatcher:
    """Tests for DocumentWatcher class."""

    def test_init_default_values(self):
        """Test DocumentWatcher initialization with default values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_dir = Path(tmpdir)
            mock_index_manager = Mock()

            watcher = DocumentWatcher(
                library_dir=library_dir,
                index_manager=mock_index_manager,
            )

            assert watcher._library_dir == library_dir
            assert watcher._index_manager == mock_index_manager
            assert watcher._mode == "scan"
            assert watcher._scan_interval == 30
            assert watcher._running is False
            assert watcher._thread is None
            assert watcher._file_hashes == {}

    def test_init_custom_values(self):
        """Test DocumentWatcher initialization with custom values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_dir = Path(tmpdir)
            mock_index_manager = Mock()

            watcher = DocumentWatcher(
                library_dir=library_dir,
                index_manager=mock_index_manager,
                mode="watch",
                scan_interval=60,
            )

            assert watcher._mode == "watch"
            assert watcher._scan_interval == 60

    def test_supported_extensions(self):
        """Test that supported extensions are defined."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            expected_extensions = {".md", ".markdown", ".txt", ".doc", ".docx", ".pdf"}
            assert hasattr(watcher, "SUPPORTED_EXTENSIONS")
            assert watcher.SUPPORTED_EXTENSIONS == expected_extensions


class TestDocumentWatcherFileHash:
    """Tests for file hash calculation."""

    def test_get_file_hash_md5(self):
        """Test MD5 hash calculation for a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_content = b"Hello, World!"
            test_file.write_bytes(test_content)

            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            hash_result = watcher._get_file_hash(test_file)

            # Verify it's a valid MD5 hash (32 hex characters)
            assert len(hash_result) == 32
            assert all(c in "0123456789abcdef" for c in hash_result)

            # Verify consistency
            hash_result2 = watcher._get_file_hash(test_file)
            assert hash_result == hash_result2

    def test_get_file_hash_different_content(self):
        """Test that different content produces different hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.md"
            file2 = Path(tmpdir) / "file2.md"
            file1.write_text("Content A", encoding="utf-8")
            file2.write_text("Content B", encoding="utf-8")

            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            hash1 = watcher._get_file_hash(file1)
            hash2 = watcher._get_file_hash(file2)

            assert hash1 != hash2

    def test_get_file_hash_nonexistent_file(self):
        """Test handling of non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            nonexistent = Path(tmpdir) / "nonexistent.md"

            with pytest.raises(FileNotFoundError):
                watcher._get_file_hash(nonexistent)


class TestDocumentWatcherScanChanges:
    """Tests for scanning file changes."""

    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            changes = watcher.scan_changes()

            assert isinstance(changes, list)
            assert len(changes) == 0

    def test_scan_detects_added_files(self):
        """Test detecting newly added files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            # Create a file after initialization
            test_file = Path(tmpdir) / "new_doc.md"
            test_file.write_text("# New Document\n\nContent here.", encoding="utf-8")

            changes = watcher.scan_changes()

            assert len(changes) == 1
            assert changes[0].path == test_file
            assert changes[0].change_type == "added"
            assert changes[0].old_hash is None
            assert changes[0].new_hash is not None

    def test_scan_detects_modified_files(self):
        """Test detecting modified files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "doc.md"
            test_file.write_text("Original content", encoding="utf-8")

            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            # First scan to register the file
            changes1 = watcher.scan_changes()
            assert len(changes1) == 1
            assert changes1[0].change_type == "added"

            # Modify the file
            time.sleep(0.1)  # Ensure different timestamp
            test_file.write_text("Modified content", encoding="utf-8")

            # Second scan should detect modification
            changes2 = watcher.scan_changes()

            assert len(changes2) == 1
            assert changes2[0].path == test_file
            assert changes2[0].change_type == "modified"
            assert changes2[0].old_hash is not None
            assert changes2[0].new_hash is not None
            assert changes2[0].old_hash != changes2[0].new_hash

    def test_scan_detects_deleted_files(self):
        """Test detecting deleted files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "doc.md"
            test_file.write_text("Content to be deleted", encoding="utf-8")

            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            # First scan to register the file
            watcher.scan_changes()

            # Delete the file
            test_file.unlink()

            # Second scan should detect deletion
            changes = watcher.scan_changes()

            assert len(changes) == 1
            assert changes[0].path == test_file
            assert changes[0].change_type == "deleted"
            assert changes[0].old_hash is not None
            assert changes[0].new_hash is None

    def test_scan_no_changes(self):
        """Test scanning when no changes occurred."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "doc.md"
            test_file.write_text("Unchanged content", encoding="utf-8")

            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            # First scan
            watcher.scan_changes()

            # Second scan with no changes
            changes = watcher.scan_changes()

            assert len(changes) == 0

    def test_scan_multiple_changes(self):
        """Test detecting multiple changes at once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            # Add multiple files
            for i in range(3):
                (Path(tmpdir) / f"doc{i}.md").write_text(f"Content {i}", encoding="utf-8")

            changes = watcher.scan_changes()

            assert len(changes) == 3
            assert all(c.change_type == "added" for c in changes)

    def test_scan_ignores_unsupported_extensions(self):
        """Test that unsupported file extensions are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            # Create files with supported and unsupported extensions
            (Path(tmpdir) / "supported.md").write_text("content", encoding="utf-8")
            (Path(tmpdir) / "ignored.py").write_text("content", encoding="utf-8")
            (Path(tmpdir) / "ignored.json").write_text("content", encoding="utf-8")

            changes = watcher.scan_changes()

            assert len(changes) == 1
            assert changes[0].path.name == "supported.md"

    def test_scan_recursive_subdirectories(self):
        """Test scanning files in subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            # Create subdirectories with files
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "nested.md").write_text("Nested content", encoding="utf-8")
            (Path(tmpdir) / "root.md").write_text("Root content", encoding="utf-8")

            changes = watcher.scan_changes()

            assert len(changes) == 2
            paths = {c.path.name for c in changes}
            assert paths == {"root.md", "nested.md"}


class TestDocumentWatcherHandleChange:
    """Tests for change handling."""

    def test_handle_added_file(self):
        """Test handling added file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_index_manager = Mock()
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=mock_index_manager,
            )

            test_file = Path(tmpdir) / "doc.md"
            change = FileChange(
                path=test_file,
                change_type="added",
                old_hash=None,
                new_hash="abc123",
            )

            watcher._handle_change(change)

            mock_index_manager.add_document.assert_called_once_with(test_file)

    def test_handle_modified_file(self):
        """Test handling modified file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_index_manager = Mock()
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=mock_index_manager,
            )

            test_file = Path(tmpdir) / "doc.md"
            change = FileChange(
                path=test_file,
                change_type="modified",
                old_hash="old_hash",
                new_hash="new_hash",
            )

            watcher._handle_change(change)

            mock_index_manager.update_document.assert_called_once_with(test_file)

    def test_handle_deleted_file(self):
        """Test handling deleted file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_index_manager = Mock()
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=mock_index_manager,
            )

            test_file = Path(tmpdir) / "doc.md"
            change = FileChange(
                path=test_file,
                change_type="deleted",
                old_hash="old_hash",
                new_hash=None,
            )

            watcher._handle_change(change)

            mock_index_manager.remove_document.assert_called_once_with(test_file)


class TestDocumentWatcherThreading:
    """Tests for threading and lifecycle."""

    def test_thread_safety_with_rlock(self):
        """Test that DocumentWatcher uses RLock for thread safety."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=Mock(),
            )

            assert hasattr(watcher, "_lock")
            assert isinstance(watcher._lock, type(threading.RLock()))

    def test_start_stop_scan_mode(self):
        """Test starting and stopping in scan mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_index_manager = Mock()
            watcher = DocumentWatcher(
                library_dir=Path(tmpdir),
                index_manager=mock_index_manager,
                mode="scan",
                scan_interval=0.1,  # Short interval for testing
            )

            # Create a test file
            (Path(tmpdir) / "test.md").write_text("content", encoding="utf-8")

            watcher.start()
            assert watcher._running is True
            assert watcher._thread is not None
            assert watcher._thread.is_alive()

            # Let it scan once
            time.sleep(0.2)

            watcher.stop()
            assert watcher._running is False
            assert not watcher._thread.is_alive()


class TestFileChange:
    """Tests for FileChange dataclass."""

    def test_file_change_creation(self):
        """Test FileChange dataclass creation."""
        change = FileChange(
            path=Path("/test/doc.md"),
            change_type="added",
            old_hash=None,
            new_hash="abc123def456",
        )

        assert change.path == Path("/test/doc.md")
        assert change.change_type == "added"
        assert change.old_hash is None
        assert change.new_hash == "abc123def456"

    def test_file_change_modified(self):
        """Test FileChange for modified file."""
        change = FileChange(
            path=Path("/test/doc.md"),
            change_type="modified",
            old_hash="old123",
            new_hash="new456",
        )

        assert change.change_type == "modified"
        assert change.old_hash == "old123"
        assert change.new_hash == "new456"

    def test_file_change_deleted(self):
        """Test FileChange for deleted file."""
        change = FileChange(
            path=Path("/test/doc.md"),
            change_type="deleted",
            old_hash="old123",
            new_hash=None,
        )

        assert change.change_type == "deleted"
        assert change.old_hash == "old123"
        assert change.new_hash is None
