"""Unit tests for ONNXEmbeddingBackend."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from rag_system.backends.onnx_embedding import ONNXEmbeddingBackend
from rag_system.backends.embedding import LocalHashEmbeddingBackend


class TestONNXEmbeddingBackend:
    """Tests for ONNXEmbeddingBackend class."""

    def test_init_with_nonexistent_model(self):
        """Test initialization when model file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            backend = ONNXEmbeddingBackend(model_path=model_path)
            
            assert not backend.is_healthy()
            assert isinstance(backend.get_fallback(), LocalHashEmbeddingBackend)

    def test_init_uses_fallback_when_model_missing(self):
        """Test that fallback is used when model is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            fallback = LocalHashEmbeddingBackend(dimensions=128)
            
            backend = ONNXEmbeddingBackend(
                model_path=model_path,
                fallback_backend=fallback,
            )
            
            assert not backend.is_healthy()
            assert backend.get_fallback() is fallback

    def test_embed_texts_with_fallback(self):
        """Test that embedding falls back when model not loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            backend = ONNXEmbeddingBackend(model_path=model_path)
            
            texts = ["Hello world", "Test document"]
            embeddings = backend.embed_texts(texts)
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 384  # Default dimension
            assert len(embeddings[1]) == 384

    def test_embed_query_with_fallback(self):
        """Test embedding a single query."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            backend = ONNXEmbeddingBackend(model_path=model_path)
            
            embedding = backend.embed_query("Hello")
            
            assert len(embedding) == 384

    def test_async_embedding(self):
        """Test async embedding method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            backend = ONNXEmbeddingBackend(model_path=model_path)
            
            import asyncio
            embeddings = asyncio.run(
                backend.embed_texts_async(["Hello", "World"])
            )
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 384

    def test_custom_dimension(self):
        """Test custom embedding dimension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            fallback = LocalHashEmbeddingBackend(dimensions=256)
            
            backend = ONNXEmbeddingBackend(
                model_path=model_path,
                fallback_backend=fallback,
            )
            
            embeddings = backend.embed_texts(["Test"])
            
            assert len(embeddings[0]) == 256


class TestONNXEmbeddingBackendWithMockModel:
    """Tests with mocked ONNX model."""

    @pytest.fixture
    def mock_model_setup(self, tmp_path):
        """Create a mock ONNX model setup."""
        model_path = tmp_path / "model.onnx"
        model_path.write_bytes(b"mock model data")  # Fake model file
        
        # Create mock tokenizer directory
        tokenizer_dir = tmp_path
        (tokenizer_dir / "tokenizer_config.json").write_text("{}")
        (tokenizer_dir / "vocab.txt").write_text("[PAD]\n[UNK]\n[CLS]\n[SEP]\n[MASK]\nhello\nworld\n")
        
        return model_path

    def test_model_loading_failure_fallback(self, mock_model_setup):
        """Test fallback when model loading fails."""
        # The mock file exists but is not a valid ONNX model
        backend = ONNXEmbeddingBackend(model_path=mock_model_setup)
        
        # Should fall back to LocalHashEmbeddingBackend
        assert not backend.is_healthy()
        embeddings = backend.embed_texts(["Test"])
        assert len(embeddings) == 1

    def test_embed_texts_consistency(self):
        """Test that embedding is deterministic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            backend = ONNXEmbeddingBackend(model_path=model_path)
            
            text = "Hello world"
            emb1 = backend.embed_query(text)
            emb2 = backend.embed_query(text)
            
            assert emb1 == emb2
