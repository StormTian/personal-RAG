"""Document watcher for monitoring file changes in the library."""

import hashlib
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class FileChange:
    """Represents a file change event."""
    path: Path
    change_type: str  # "added", "modified", "deleted"
    old_hash: Optional[str]
    new_hash: Optional[str]


class DocumentWatcher:
    """Watches document library for file changes and triggers index updates."""
    
    SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".doc", ".docx", ".pdf"}
    
    def __init__(
        self,
        library_dir: Path,
        index_manager,
        mode: str = "scan",  # "scan" or "watch"
        scan_interval: int = 30,
    ):
        """Initialize document watcher.
        
        Args:
            library_dir: Directory to watch for documents
            index_manager: IndexManager instance to notify of changes
            mode: Watch mode - "scan" (polling) or "watch" (event-based)
            scan_interval: Seconds between scans in scan mode
        """
        self._library_dir = Path(library_dir)
        self._index_manager = index_manager
        self._mode = mode
        self._scan_interval = scan_interval
        
        self._file_hashes: Dict[str, str] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
    
    def start(self) -> None:
        """Start watching for file changes."""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            
            if self._mode == "scan":
                self._thread = threading.Thread(target=self._scan_loop, daemon=True)
                self._thread.start()
            elif self._mode == "watch":
                # Watchdog mode - would require watchdog library
                # For now, fall back to scan mode
                self._thread = threading.Thread(target=self._scan_loop, daemon=True)
                self._thread.start()
    
    def stop(self) -> None:
        """Stop watching for file changes."""
        with self._lock:
            self._running = False
            
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
    
    def _scan_loop(self) -> None:
        """Background scanning loop."""
        while self._running:
            try:
                changes = self.scan_changes()
                for change in changes:
                    self._handle_change(change)
            except Exception as e:
                print(f"Error in scan loop: {e}")
            
            # Sleep for scan interval
            for _ in range(int(self._scan_interval * 10)):
                if not self._running:
                    break
                time.sleep(0.1)
    
    def scan_changes(self) -> List[FileChange]:
        """Scan for file changes.
        
        Returns:
            List of FileChange objects representing detected changes
        """
        with self._lock:
            changes = []
            current_files: Dict[str, str] = {}
            
            # Find all supported files
            for ext in self.SUPPORTED_EXTENSIONS:
                for file_path in self._library_dir.rglob(f"*{ext}"):
                    if file_path.is_file():
                        try:
                            file_hash = self._get_file_hash(file_path)
                            current_files[str(file_path)] = file_hash
                        except (IOError, OSError):
                            # Skip files that can't be read
                            continue
            
            # Detect added and modified files
            for path_str, file_hash in current_files.items():
                if path_str not in self._file_hashes:
                    # New file
                    changes.append(FileChange(
                        path=Path(path_str),
                        change_type="added",
                        old_hash=None,
                        new_hash=file_hash,
                    ))
                elif self._file_hashes[path_str] != file_hash:
                    # Modified file
                    changes.append(FileChange(
                        path=Path(path_str),
                        change_type="modified",
                        old_hash=self._file_hashes[path_str],
                        new_hash=file_hash,
                    ))
            
            # Detect deleted files
            for path_str in self._file_hashes:
                if path_str not in current_files:
                    changes.append(FileChange(
                        path=Path(path_str),
                        change_type="deleted",
                        old_hash=self._file_hashes[path_str],
                        new_hash=None,
                    ))
            
            # Update stored hashes
            self._file_hashes = current_files
            
            return changes
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 hash as hex string
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _handle_change(self, change: FileChange) -> None:
        """Handle a file change event.
        
        Args:
            change: FileChange object describing the change
        """
        if change.change_type == "added":
            print(f"Document added: {change.path}")
            if hasattr(self._index_manager, 'add_document'):
                # Handle both sync and async
                import asyncio
                if asyncio.iscoroutinefunction(self._index_manager.add_document):
                    asyncio.create_task(self._index_manager.add_document(change.path))
                else:
                    self._index_manager.add_document(change.path)
                    
        elif change.change_type == "modified":
            print(f"Document modified: {change.path}")
            if hasattr(self._index_manager, 'update_document'):
                import asyncio
                if asyncio.iscoroutinefunction(self._index_manager.update_document):
                    asyncio.create_task(self._index_manager.update_document(change.path))
                else:
                    self._index_manager.update_document(change.path)
                    
        elif change.change_type == "deleted":
            print(f"Document deleted: {change.path}")
            if hasattr(self._index_manager, 'remove_document'):
                self._index_manager.remove_document(change.path)
