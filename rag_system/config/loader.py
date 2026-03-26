"""Configuration loader with hot-reload support."""

import threading
import time
from pathlib import Path
from typing import Callable, Optional
import logging

from .settings import Settings, reload_settings

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Configuration loader with hot-reload capability."""
    
    def __init__(self, config_path: Optional[Path] = None, auto_reload: bool = False):
        self.config_path = config_path
        self.auto_reload = auto_reload
        self._settings: Optional[Settings] = None
        self._last_modified: float = 0.0
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._reload_thread: Optional[threading.Thread] = None
        self._callbacks: list[Callable[[Settings], None]] = []
    
    def load(self) -> Settings:
        """Load configuration from file or environment."""
        with self._lock:
            if self.config_path and self.config_path.exists():
                self._last_modified = self.config_path.stat().st_mtime
                if self.config_path.suffix in ['.yaml', '.yml']:
                    self._settings = Settings.from_yaml(self.config_path)
                elif self.config_path.suffix == '.json':
                    self._settings = Settings.from_json(self.config_path)
                else:
                    raise ValueError(f"Unsupported config format: {self.config_path.suffix}")
            else:
                self._settings = reload_settings()
            
            if self.auto_reload and self._reload_thread is None:
                self._start_reload_watcher()
            
            return self._settings
    
    def get_settings(self) -> Settings:
        """Get current settings."""
        with self._lock:
            if self._settings is None:
                return self.load()
            return self._settings
    
    def reload(self) -> Settings:
        """Force reload configuration."""
        with self._lock:
            old_settings = self._settings
            self._settings = reload_settings(self.config_path)
            
            if old_settings != self._settings:
                logger.info("Configuration reloaded")
                for callback in self._callbacks:
                    try:
                        callback(self._settings)
                    except Exception as e:
                        logger.error(f"Config reload callback failed: {e}")
            
            if self.config_path:
                self._last_modified = self.config_path.stat().st_mtime
            
            return self._settings
    
    def on_reload(self, callback: Callable[[Settings], None]) -> None:
        """Register a callback to be called when config is reloaded."""
        self._callbacks.append(callback)
    
    def _start_reload_watcher(self) -> None:
        """Start background thread to watch for config changes."""
        if self._reload_thread is not None:
            return
        
        self._reload_thread = threading.Thread(target=self._watch_config, daemon=True)
        self._reload_thread.start()
        logger.info(f"Started config reload watcher for {self.config_path}")
    
    def _watch_config(self) -> None:
        """Watch configuration file for changes."""
        while not self._stop_event.is_set():
            time.sleep(5)  # Check every 5 seconds
            
            if not self.config_path or not self.config_path.exists():
                continue
            
            try:
                current_mtime = self.config_path.stat().st_mtime
                if current_mtime > self._last_modified:
                    logger.info(f"Config file changed, reloading: {self.config_path}")
                    self.reload()
            except Exception as e:
                logger.error(f"Error watching config file: {e}")
    
    def stop(self) -> None:
        """Stop the reload watcher."""
        self._stop_event.set()
        if self._reload_thread:
            self._reload_thread.join(timeout=1.0)
            self._reload_thread = None
