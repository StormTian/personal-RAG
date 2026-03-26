"""Application settings with validation and environment variable support."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
import json


@dataclass
class EmbeddingConfig:
    """Embedding backend configuration."""
    backend: str = "local-hash"
    dimensions: int = 256
    projections_per_token: int = 8
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com"
    timeout: int = 30
    batch_size: int = 32
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class RerankerConfig:
    """Reranker backend configuration."""
    backend: str = "local-heuristic"
    strategy: str = "embedding+lexical-overlap"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 45
    max_candidates: int = 12
    fallback_backend: str = "local-heuristic"


@dataclass
class RetrievalConfig:
    """Retrieval configuration."""
    top_k: int = 3
    candidate_pool_multiplier: int = 6
    min_candidate_pool: int = 8
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    max_lexical_weight: float = 0.30
    max_title_weight: float = 0.10
    max_semantic_weight: float = 0.60


@dataclass
class ChunkingConfig:
    """Text chunking configuration."""
    max_chars: int = 240
    overlap: int = 1
    min_sentence_length: int = 6


@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    cache_dir: str = ".index_cache"
    max_age_hours: int = 168  # 7 days
    compression: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file_path: Optional[str] = None
    max_bytes: int = 10_000_000
    backup_count: int = 5
    enable_console: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""
    enabled: bool = True
    metrics_port: int = 9090
    collect_latency: bool = True
    collect_throughput: bool = True
    health_check_interval: int = 30


@dataclass
class SecurityConfig:
    """Security configuration."""
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    max_query_length: int = 1000
    allowed_file_extensions: List[str] = field(default_factory=lambda: [
        ".md", ".markdown", ".txt", ".doc", ".docx", ".pdf"
    ])
    max_upload_size: int = 104_857_600  # 100MB
    api_key_header: str = "X-API-Key"
    require_api_key: bool = False


@dataclass
class UploadConfig:
    """Upload configuration."""
    max_file_size: int = 104_857_600  # 100MB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".md", ".markdown", ".txt", ".doc", ".docx", ".pdf"
    ])
    auto_reload: bool = True


@dataclass
class HistoryConfig:
    """Upload history configuration."""
    enabled: bool = True
    db_path: str = "data/upload_history.db"


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    timeout: int = 30
    max_request_size: int = 10_000_000
    enable_cors: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


class Settings:
    """Application settings container with validation."""
    
    def __init__(self):
        self.embedding = EmbeddingConfig()
        self.reranker = RerankerConfig()
        self.retrieval = RetrievalConfig()
        self.chunking = ChunkingConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        self.monitoring = MonitoringConfig()
        self.security = SecurityConfig()
        self.server = ServerConfig()
        self.upload = UploadConfig()
        self.history = HistoryConfig()
        self.library_dir: Path = Path("document_library")
        self.debug: bool = False
    
    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Load settings from YAML file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data or {})
    
    @classmethod
    def from_json(cls, path: Path) -> "Settings":
        """Load settings from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Load settings from dictionary."""
        settings = cls()
        
        # Load from environment variables first
        settings._load_from_env()
        
        # Override with config file values
        if "embedding" in data:
            settings.embedding = EmbeddingConfig(**data["embedding"])
        if "reranker" in data:
            settings.reranker = RerankerConfig(**data["reranker"])
        if "retrieval" in data:
            settings.retrieval = RetrievalConfig(**data["retrieval"])
        if "chunking" in data:
            settings.chunking = ChunkingConfig(**data["chunking"])
        if "cache" in data:
            settings.cache = CacheConfig(**data["cache"])
        if "logging" in data:
            settings.logging = LoggingConfig(**data["logging"])
        if "monitoring" in data:
            settings.monitoring = MonitoringConfig(**data["monitoring"])
        if "security" in data:
            settings.security = SecurityConfig(**data["security"])
        if "server" in data:
            settings.server = ServerConfig(**data["server"])
        if "upload" in data:
            settings.upload = UploadConfig(**data["upload"])
        if "history" in data:
            settings.history = HistoryConfig(**data["history"])
        if "library_dir" in data:
            settings.library_dir = Path(data["library_dir"])
        if "debug" in data:
            settings.debug = bool(data["debug"])
        
        settings.validate()
        return settings
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Embedding
        if os.getenv("OPENAI_API_KEY"):
            self.embedding.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_EMBED_MODEL"):
            self.embedding.model = os.getenv("OPENAI_EMBED_MODEL")
            self.embedding.backend = "openai-compatible"
        if os.getenv("OPENAI_BASE_URL"):
            self.embedding.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
        
        # Reranker
        if os.getenv("OPENAI_RERANK_MODEL"):
            self.reranker.model = os.getenv("OPENAI_RERANK_MODEL")
            self.reranker.backend = "openai-compatible"
        if os.getenv("OPENAI_RERANK_BASE_URL"):
            self.reranker.base_url = os.getenv("OPENAI_RERANK_BASE_URL")
        
        # Server
        if os.getenv("RAG_HOST"):
            self.server.host = os.getenv("RAG_HOST", "127.0.0.1")
        if os.getenv("RAG_PORT"):
            self.server.port = int(os.getenv("RAG_PORT", "8000"))
        
        # Security
        if os.getenv("RAG_API_KEY"):
            self.security.require_api_key = True
        
        # Debug
        if os.getenv("RAG_DEBUG"):
            self.debug = os.getenv("RAG_DEBUG", "false").lower() == "true"
    
    def validate(self) -> None:
        """Validate all configuration values."""
        errors = []
        
        # Validate paths
        if not self.library_dir.exists():
            errors.append(f"Library directory does not exist: {self.library_dir}")
        
        # Validate embedding config
        if self.embedding.backend == "openai-compatible":
            if not self.embedding.api_key:
                errors.append("OPENAI_API_KEY required for OpenAI embedding backend")
            if not self.embedding.model:
                errors.append("OPENAI_EMBED_MODEL required for OpenAI embedding backend")
        
        # Validate reranker config
        if self.reranker.backend == "openai-compatible":
            if not self.reranker.api_key:
                self.reranker.api_key = self.embedding.api_key
            if not self.reranker.model:
                errors.append("OPENAI_RERANK_MODEL required for OpenAI reranker backend")
        
        # Validate numeric ranges
        if self.retrieval.top_k < 1:
            errors.append("top_k must be at least 1")
        if self.chunking.max_chars < 100:
            errors.append("max_chars must be at least 100")
        if self.server.port < 1 or self.server.port > 65535:
            errors.append("port must be between 1 and 65535")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "embedding": self.embedding.__dict__,
            "reranker": self.reranker.__dict__,
            "retrieval": self.retrieval.__dict__,
            "chunking": self.chunking.__dict__,
            "cache": self.cache.__dict__,
            "logging": self.logging.__dict__,
            "monitoring": self.monitoring.__dict__,
            "security": self.security.__dict__,
            "server": self.server.__dict__,
            "upload": self.upload.__dict__,
            "history": self.history.__dict__,
            "library_dir": str(self.library_dir),
            "debug": self.debug,
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings._load_from_env()
        _settings.validate()
    return _settings


def reload_settings(config_path: Optional[Path] = None) -> Settings:
    """Reload settings from configuration file."""
    global _settings
    if config_path and config_path.suffix in ['.yaml', '.yml']:
        _settings = Settings.from_yaml(config_path)
    elif config_path and config_path.suffix == '.json':
        _settings = Settings.from_json(config_path)
    else:
        _settings = Settings()
        _settings._load_from_env()
        _settings.validate()
    return _settings
