"""
Pytest configuration and shared fixtures for RAG test suite.
"""

import os
import sys
import json
import hashlib
import tempfile
import pytest
from pathlib import Path
from typing import Dict, List, Tuple, Generator
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import (
    TinyRAG,
    EmbeddingBackend,
    LocalHashEmbeddingBackend,
    RerankerBackend,
    LocalHeuristicReranker,
    IndexSnapshot,
    Chunk,
    SourceDocument,
    CandidateScore,
    SearchHit,
    RagResponse,
    tokenize,
    chunk_text,
    cosine_similarity,
    normalize_vector,
)


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def sample_library_dir(temp_dir: Path) -> Path:
    """Create a sample document library with various file types."""
    lib_dir = temp_dir / "library"
    lib_dir.mkdir(parents=True)
    
    # Create subdirectories
    (lib_dir / "product").mkdir()
    (lib_dir / "hr").mkdir()
    (lib_dir / "tech").mkdir()
    
    # Markdown file
    (lib_dir / "product" / "overview.md").write_text(
        "# Product Overview\n\n"
        "This is a comprehensive product overview document.\n\n"
        "Key features include:\n"
        "- Feature A: Advanced search capabilities\n"
        "- Feature B: Real-time collaboration\n"
        "- Feature C: Cloud synchronization\n\n"
        "Contact support@example.com for more information.\n",
        encoding="utf-8"
    )
    
    # Text file
    (lib_dir / "hr" / "policy.txt").write_text(
        "HR Policy Document\n\n"
        "Employee vacation policy:\n"
        "All full-time employees are entitled to 20 days of paid vacation per year.\n"
        "Vacation requests must be submitted at least 2 weeks in advance.\n"
        "Unused vacation days can be carried over to the next year (max 5 days).\n\n"
        "Emergency leave:\n"
        "In case of emergency, employees may take up to 3 days without prior notice.\n",
        encoding="utf-8"
    )
    
    # Another markdown with Chinese content
    (lib_dir / "tech" / "architecture.md").write_text(
        "# 系统架构设计\n\n"
        "## 概述\n\n"
        "本文档描述了系统的整体架构设计。\n\n"
        "## 技术栈\n\n"
        "- 后端：Python + FastAPI\n"
        "- 数据库：PostgreSQL\n"
        "- 缓存：Redis\n\n"
        "## 部署架构\n\n"
        "系统采用微服务架构，包含以下服务：\n"
        "1. API Gateway\n"
        "2. Authentication Service\n"
        "3. Document Processing Service\n",
        encoding="utf-8"
    )
    
    return lib_dir


@pytest.fixture(scope="function")
def empty_library_dir(temp_dir: Path) -> Path:
    """Create an empty document library."""
    lib_dir = temp_dir / "empty_library"
    lib_dir.mkdir(parents=True)
    return lib_dir


@pytest.fixture(scope="function")
def single_doc_library(temp_dir: Path) -> Path:
    """Create a library with a single document."""
    lib_dir = temp_dir / "single_lib"
    lib_dir.mkdir(parents=True)
    
    (lib_dir / "doc.md").write_text(
        "# Single Document\n\n"
        "This is the only document in the library.\n"
        "It contains some simple content for testing.\n",
        encoding="utf-8"
    )
    
    return lib_dir


# ============================================================================
# Backend Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def local_embedding_backend() -> LocalHashEmbeddingBackend:
    """Create a local hash embedding backend for testing."""
    return LocalHashEmbeddingBackend(dimensions=128, projections_per_token=4)


@pytest.fixture(scope="function")
def local_reranker() -> LocalHeuristicReranker:
    """Create a local heuristic reranker for testing."""
    return LocalHeuristicReranker()


@pytest.fixture(scope="function")
def mock_embedding_backend() -> Mock:
    """Create a mock embedding backend."""
    mock = Mock(spec=EmbeddingBackend)
    mock.name = "mock-embedding"
    
    def mock_embed_texts(texts):
        # Return simple normalized vectors
        return [normalize_vector([1.0, 0.5, 0.3, 0.2, 0.1] * 51)[:256]] * len(texts)
    
    mock.embed_texts.side_effect = mock_embed_texts
    mock.embed_query.return_value = normalize_vector([1.0, 0.5, 0.3, 0.2, 0.1] * 51)[:256]
    
    return mock


@pytest.fixture(scope="function")
def mock_reranker() -> Mock:
    """Create a mock reranker backend."""
    mock = Mock(spec=RerankerBackend)
    mock.name = "mock-reranker"
    mock.strategy = "mock-strategy"
    mock.candidate_pool_size.return_value = 10
    
    def mock_rerank(query, snapshot, candidates):
        # Just return candidates sorted by retrieve_score
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.retrieve_score,
            reverse=True
        )
        return sorted_candidates
    
    mock.rerank.side_effect = mock_rerank
    return mock


# ============================================================================
# RAG Instance Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def rag_instance(sample_library_dir: Path, local_embedding_backend, local_reranker) -> TinyRAG:
    """Create a TinyRAG instance with sample library."""
    return TinyRAG(
        library_dir=sample_library_dir,
        embedding_backend=local_embedding_backend,
        reranker_backend=local_reranker
    )


@pytest.fixture(scope="function")
def rag_with_mock_backends(sample_library_dir: Path, mock_embedding_backend, mock_reranker) -> TinyRAG:
    """Create a TinyRAG instance with mock backends."""
    return TinyRAG(
        library_dir=sample_library_dir,
        embedding_backend=mock_embedding_backend,
        reranker_backend=mock_reranker
    )


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def sample_texts() -> List[str]:
    """Return sample texts for embedding tests."""
    return [
        "Machine learning is a subset of artificial intelligence.",
        "Python is a popular programming language for data science.",
        "The quick brown fox jumps over the lazy dog.",
        "Natural language processing enables computers to understand human language.",
        "Deep learning uses neural networks with multiple layers.",
    ]


@pytest.fixture(scope="function")
def sample_query() -> str:
    """Return a sample query for search tests."""
    return "What is machine learning?"


@pytest.fixture(scope="function")
def sample_chunks() -> List[Chunk]:
    """Return sample chunks for testing."""
    return [
        Chunk(chunk_id=0, source="doc1.md", title="Introduction", text="This is the first chunk."),
        Chunk(chunk_id=1, source="doc1.md", title="Introduction", text="This is the second chunk with different content."),
        Chunk(chunk_id=2, source="doc2.md", title="Methods", text="Methods section describes the approach."),
        Chunk(chunk_id=3, source="doc3.md", title="Results", text="Results show significant improvements."),
    ]


@pytest.fixture(scope="function")
def sample_candidate_scores() -> List[CandidateScore]:
    """Return sample candidate scores for reranking tests."""
    return [
        CandidateScore(index=0, retrieve_score=0.9, lexical_score=0.8, title_score=0.7, rerank_score=0.85, llm_score=0.0),
        CandidateScore(index=1, retrieve_score=0.85, lexical_score=0.75, title_score=0.6, rerank_score=0.80, llm_score=0.0),
        CandidateScore(index=2, retrieve_score=0.7, lexical_score=0.9, title_score=0.5, rerank_score=0.75, llm_score=0.0),
        CandidateScore(index=3, retrieve_score=0.6, lexical_score=0.5, title_score=0.4, rerank_score=0.55, llm_score=0.0),
    ]


# ============================================================================
# Snapshot Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def minimal_snapshot(sample_chunks: List[Chunk]) -> IndexSnapshot:
    """Create a minimal index snapshot for testing."""
    from collections import Counter
    from app import chunk_text
    
    # Generate embeddings for chunks
    backend = LocalHashEmbeddingBackend(dimensions=128, projections_per_token=4)
    chunk_embeddings = backend.embed_texts([c.text for c in sample_chunks])
    
    # Generate token counts
    token_counts = [Counter(tokenize(c.text)) for c in sample_chunks]
    
    # Calculate IDF
    all_tokens = set()
    for tc in token_counts:
        all_tokens.update(tc.keys())
    
    import math
    total_chunks = len(sample_chunks)
    idf = {}
    for token in all_tokens:
        freq = sum(1 for tc in token_counts if token in tc)
        idf[token] = math.log((total_chunks + 1) / (freq + 0.5)) + 1.0
    
    avgdl = sum(sum(tc.values()) for tc in token_counts) / total_chunks
    
    return IndexSnapshot(
        library_dir=Path("/tmp/test"),
        documents=tuple(),
        skipped_files=tuple(),
        chunks=tuple(sample_chunks),
        chunk_embeddings=tuple(chunk_embeddings),
        chunk_token_counts=tuple(token_counts),
        chunk_title_token_sets=tuple(frozenset(tokenize(c.title)) for c in sample_chunks),
        idf=idf,
        avgdl=avgdl,
        supported_formats=(".md", ".txt"),
        embedding_backend="test-backend",
        reranker_backend="test-reranker",
        retrieval_strategy="test",
        rerank_strategy="test",
    )


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def clean_env():
    """Clean environment variables for API key tests."""
    old_env = dict(os.environ)
    
    # Remove API-related env vars
    for key in ['OPENAI_API_KEY', 'OPENAI_EMBED_MODEL', 'OPENAI_BASE_URL',
                'OPENAI_RERANK_MODEL', 'OPENAI_RERANK_BASE_URL']:
        os.environ.pop(key, None)
    
    yield
    
    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture(scope="function")
def mock_openai_env():
    """Set up mock OpenAI environment variables."""
    old_values = {}
    env_vars = {
        'OPENAI_API_KEY': 'sk-test-key',
        'OPENAI_EMBED_MODEL': 'text-embedding-3-small',
        'OPENAI_BASE_URL': 'https://api.openai.com',
        'OPENAI_RERANK_MODEL': 'gpt-4',
        'OPENAI_RERANK_BASE_URL': 'https://api.openai.com',
    }
    
    for key, value in env_vars.items():
        old_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    for key, old_value in old_values.items():
        if old_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old_value


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_valid_embedding(vector: Tuple[float, ...], expected_dim: int = None):
    """Assert that a vector is a valid embedding."""
    assert isinstance(vector, tuple), f"Expected tuple, got {type(vector)}"
    assert len(vector) > 0, "Embedding vector should not be empty"
    
    if expected_dim:
        assert len(vector) == expected_dim, f"Expected dimension {expected_dim}, got {len(vector)}"
    
    # Check normalization (L2 norm should be close to 1.0)
    import math
    norm = math.sqrt(sum(x * x for x in vector))
    assert abs(norm - 1.0) < 0.01 or norm < 0.01, f"Vector not normalized: norm={norm}"


def assert_valid_search_hit(hit):
    """Assert that a search hit is valid."""
    assert hit.chunk is not None
    assert isinstance(hit.chunk.text, str)
    assert len(hit.chunk.text) > 0
    assert hit.score >= 0
    assert hit.retrieve_score >= 0
    assert hit.rerank_score >= 0


def assert_valid_rag_response(response: RagResponse):
    """Assert that a RAG response is valid."""
    assert isinstance(response, RagResponse)
    assert isinstance(response.query, str)
    assert isinstance(response.answer_lines, list)
    assert isinstance(response.hits, list)
    
    for hit in response.hits:
        assert_valid_search_hit(hit)


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
    config.addinivalue_line("markers", "benchmark: marks tests as benchmark tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Add markers based on test location
    for item in items:
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        if "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.benchmark)
