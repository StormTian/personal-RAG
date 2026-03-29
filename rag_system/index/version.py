"""Index version management for snapshots and rollback."""

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class SnapshotInfo:
    """Information about an index snapshot."""
    name: str
    timestamp: datetime
    doc_count: int
    chunk_count: int
    checksum: str


class IndexVersion:
    """Manages index snapshots for backup and rollback."""

    def __init__(self, cache_dir: Path, max_snapshots: int = 5):
        """Initialize index version manager.

        Args:
            cache_dir: Directory containing index files
            max_snapshots: Maximum number of snapshots to keep
        """
        self._cache_dir = Path(cache_dir)
        self._snapshots_dir = self._cache_dir / "snapshots"
        self._max_snapshots = max_snapshots

    def create_snapshot(self, name: Optional[str] = None) -> str:
        """Create a snapshot of the current index.

        Args:
            name: Optional snapshot name, auto-generated if not provided

        Returns:
            Snapshot name
        """
        # Generate name if not provided
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"v_{timestamp}"

        # Create snapshot directory
        snapshot_dir = self._snapshots_dir / name
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Copy index files
        index_files = [
            "faiss.index",
            "faiss.ids.pkl",
            "bm25_term_freq.pkl.gz",
            "bm25_doc_freq.pkl.gz",
            "bm25_doc_length.pkl.gz",
            "bm25_metadata.pkl.gz",
            "chunk_map.pkl.gz",
        ]

        for filename in index_files:
            src = self._cache_dir / filename
            if src.exists():
                dst = snapshot_dir / filename
                shutil.copy2(src, dst)

        # Calculate checksum of copied files
        checksum = self._calculate_snapshot_checksum(snapshot_dir)

        # Create metadata
        metadata = {
            "version": name,
            "timestamp": datetime.now().isoformat(),
            "checksum": checksum,
            "config": {},
        }

        # Try to get doc_count and chunk_count from IndexManager if available
        # For now, use placeholder values
        metadata["doc_count"] = 0
        metadata["chunk_count"] = 0

        # Write metadata
        metadata_path = snapshot_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return name

    def list_snapshots(self) -> List[SnapshotInfo]:
        """List all available snapshots.

        Returns:
            List of SnapshotInfo, sorted by timestamp (newest first)
        """
        snapshots = []

        if not self._snapshots_dir.exists():
            return snapshots

        for snapshot_dir in self._snapshots_dir.iterdir():
            if not snapshot_dir.is_dir():
                continue

            metadata_path = snapshot_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)

                snapshot = SnapshotInfo(
                    name=snapshot_dir.name,
                    timestamp=datetime.fromisoformat(metadata["timestamp"]),
                    doc_count=metadata.get("doc_count", 0),
                    chunk_count=metadata.get("chunk_count", 0),
                    checksum=metadata.get("checksum", ""),
                )
                snapshots.append(snapshot)
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted snapshots
                continue

        # Sort by timestamp (newest first)
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)

        return snapshots

    def restore_snapshot(self, name: str) -> bool:
        """Restore index from a snapshot.

        Args:
            name: Snapshot name to restore

        Returns:
            True if successful, False otherwise
        """
        snapshot_dir = self._snapshots_dir / name

        if not snapshot_dir.exists():
            return False

        metadata_path = snapshot_dir / "metadata.json"
        if not metadata_path.exists():
            return False

        try:
            # Verify metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Verify checksum
            expected_checksum = metadata.get("checksum", "")
            actual_checksum = self._calculate_snapshot_checksum(snapshot_dir)

            if expected_checksum and expected_checksum != actual_checksum:
                print(f"Warning: Checksum mismatch for snapshot {name}")

            # Copy files back
            for src_file in snapshot_dir.iterdir():
                if src_file.name == "metadata.json":
                    continue

                dst_file = self._cache_dir / src_file.name
                shutil.copy2(src_file, dst_file)

            return True

        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"Error restoring snapshot {name}: {e}")
            return False

    def delete_snapshot(self, name: str) -> bool:
        """Delete a snapshot.

        Args:
            name: Snapshot name to delete

        Returns:
            True if successful, False otherwise
        """
        snapshot_dir = self._snapshots_dir / name

        if not snapshot_dir.exists():
            return False

        try:
            shutil.rmtree(snapshot_dir)
            return True
        except OSError as e:
            print(f"Error deleting snapshot {name}: {e}")
            return False

    def cleanup_old_snapshots(self) -> int:
        """Remove old snapshots exceeding max_snapshots limit.

        Returns:
            Number of snapshots removed
        """
        snapshots = self.list_snapshots()

        if len(snapshots) <= self._max_snapshots:
            return 0

        # Remove oldest snapshots
        to_remove = snapshots[self._max_snapshots:]
        removed = 0

        for snapshot in to_remove:
            if self.delete_snapshot(snapshot.name):
                removed += 1

        return removed

    def _calculate_snapshot_checksum(self, snapshot_dir: Path) -> str:
        """Calculate checksum of all files in snapshot.

        Args:
            snapshot_dir: Snapshot directory

        Returns:
            MD5 checksum hex string
        """
        hasher = hashlib.md5()

        # Sort files for consistent checksum
        files = sorted(snapshot_dir.iterdir())

        for file_path in files:
            if file_path.name == "metadata.json":
                continue

            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        hasher.update(chunk)

        return hasher.hexdigest()
