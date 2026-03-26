"""
Unit tests for embedding backends.
"""

import pytest
import math
from unittest.mock import Mock, patch, MagicMock
from app import (
    LocalHashEmbeddingBackend,
    OpenAICompatibleEmbeddingBackend,
    normalize_vector,
)


class TestLocalHashEmbeddingBackend:
    """Tests for LocalHashEmbeddingBackend."""
    
    def test_initialization(self):
        """Test backend initialization."""
        backend = LocalHashEmbeddingBackend(dimensions=256, projections_per_token=8)
        assert backend.dimensions == 256
        assert backend.projections_per_token == 8
        assert backend.name == "local-hash-256d"
    
    def test_initialization_defaults(self):
        """Test backend initialization with defaults."""
        backend = LocalHashEmbeddingBackend()
        assert backend.dimensions == 256
        assert backend.projections_per_token == 8
    
    def test_token_projection_consistency(self):
        """Test that token projection is consistent."""
        backend = LocalHashEmbeddingBackend()
        
        token = "test"
        proj1 = backend._token_projection(token)
        proj2 = backend._token_projection(token)
        
        # Same token should produce same projection
        assert proj1 == proj2
    
    def test_token_projection_caching(self):
        """Test that token projections are cached."""
        backend = LocalHashEmbeddingBackend()
        
        token = "cached_token"
        backend._token_projection(token)
        
        # Should be in cache
        assert token in backend._token_cache
        
        # Second call should use cache
        backend._token_projection(token)
        assert backend._token_cache[token] is not None
    
    def test_embed_single_text(self):
        """Test embedding a single text."""
        backend = LocalHashEmbeddingBackend(dimensions=128)
        
        text = "This is a test"
        vectors = backend.embed_texts([text])
        
        assert len(vectors) == 1
        vector = vectors[0]
        assert len(vector) == 128
        
        # Check normalization
        norm = math.sqrt(sum(x * x for x in vector))
        assert abs(norm - 1.0) < 0.01
    
    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        backend = LocalHashEmbeddingBackend(dimensions=128)
        
        texts = ["First text", "Second text", "Third text"]
        vectors = backend.embed_texts(texts)
        
        assert len(vectors) == 3
        for vector in vectors:
            assert len(vector) == 128
    
    def test_embed_query(self):
        """Test embedding a query."""
        backend = LocalHashEmbeddingBackend(dimensions=128)
        
        query = "test query"
        vector = backend.embed_query(query)
        
        assert len(vector) == 128
        norm = math.sqrt(sum(x * x for x in vector))
        assert abs(norm - 1.0) < 0.01
    
    def test_embedding_determinism(self):
        """Test that embedding is deterministic."""
        backend = LocalHashEmbeddingBackend(dimensions=128)
        
        text = "Deterministic test"
        vec1 = backend.embed_texts([text])[0]
        vec2 = backend.embed_texts([text])[0]
        
        assert vec1 == vec2
    
    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        backend = LocalHashEmbeddingBackend(dimensions=128)
        
        texts = ["Apple", "Banana", "Cherry"]
        vectors = backend.embed_texts(texts)
        
        # All vectors should be different
        assert vectors[0] != vectors[1]
        assert vectors[1] != vectors[2]
        assert vectors[0] != vectors[2]


class TestOpenAICompatibleEmbeddingBackend:
    """Tests for OpenAICompatibleEmbeddingBackend."""
    
    def test_initialization(self):
        """Test backend initialization."""
        backend = OpenAICompatibleEmbeddingBackend(
            api_key="test-key",
            model="text-embedding-3-small",
            base_url="https://api.openai.com"
        )
        assert backend.api_key == "test-key"
        assert backend.model == "text-embedding-3-small"
        assert backend.base_url == "https://api.openai.com"
        assert backend.name == "openai-compatible:text-embedding-3-small"
    
    def test_base_url_normalization(self):
        """Test that trailing slash is removed from base_url."""
        backend = OpenAICompatibleEmbeddingBackend(
            api_key="test",
            model="model",
            base_url="https://api.example.com/"
        )
        assert backend.base_url == "https://api.example.com"
    
    @patch('app.post_json')
    def test_request_batch_success(self, mock_post_json):
        """Test successful batch request."""
        mock_response = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3, 0.4]},
                {"index": 1, "embedding": [0.2, 0.3, 0.4, 0.5]},
            ]
        }
        mock_post_json.return_value = mock_response
        
        backend = OpenAICompatibleEmbeddingBackend(
            api_key="test",
            model="model",
            base_url="https://api.openai.com"
        )
        
        vectors = backend._request_batch(["text1", "text2"])
        
        assert len(vectors) == 2
        mock_post_json.assert_called_once()
    
    @patch('app.post_json')
    def test_request_batch_normalization(self, mock_post_json):
        """Test that embeddings are normalized."""
        mock_response = {
            "data": [
                {"index": 0, "embedding": [3.0, 4.0]},  # Will be normalized
            ]
        }
        mock_post_json.return_value = mock_response
        
        backend = OpenAICompatibleEmbeddingBackend(
            api_key="test",
            model="model",
            base_url="https://api.openai.com"
        )
        
        vectors = backend._request_batch(["text"])
        
        # Check normalization (3-4-5 triangle)
        vector = vectors[0]
        assert abs(vector[0] - 0.6) < 0.01  # 3/5
        assert abs(vector[1] - 0.8) < 0.01  # 4/5
    
    @patch('app.post_json')
    def test_embed_texts_batches(self, mock_post_json):
        """Test that texts are sent in batches."""
        # Mock needs to return appropriate number of embeddings for each call
        def mock_post_json_impl(url, headers, payload, timeout):
            batch_size = len(payload["input"])
            return {
                "data": [{"index": i, "embedding": [0.1] * 10} for i in range(batch_size)]
            }
        
        mock_post_json.side_effect = mock_post_json_impl
        
        backend = OpenAICompatibleEmbeddingBackend(
            api_key="test",
            model="model",
            base_url="https://api.openai.com"
        )
        
        texts = [f"text{i}" for i in range(50)]
        vectors = backend.embed_texts(texts)
        
        # Should return embeddings for all texts
        assert len(vectors) == 50
        # Should batch into groups of 32
        assert mock_post_json.call_count == 2  # ceil(50/32) = 2


class TestNormalizeVector:
    """Tests for normalize_vector function."""
    
    def test_normalize_simple_vector(self):
        """Test normalizing a simple vector."""
        values = [3.0, 4.0]  # 3-4-5 triangle
        normalized = normalize_vector(values)
        
        assert abs(normalized[0] - 0.6) < 0.01
        assert abs(normalized[1] - 0.8) < 0.01
    
    def test_normalize_zero_vector(self):
        """Test normalizing zero vector."""
        values = [0.0, 0.0, 0.0]
        normalized = normalize_vector(values)
        
        assert normalized == (0.0, 0.0, 0.0)
    
    def test_normalize_already_normalized(self):
        """Test normalizing an already normalized vector."""
        values = [1.0, 0.0, 0.0]
        normalized = normalize_vector(values)
        
        assert normalized == (1.0, 0.0, 0.0)
    
    def test_normalize_tuple_input(self):
        """Test that function handles tuple input."""
        values = (3.0, 4.0)
        normalized = normalize_vector(values)
        
        assert len(normalized) == 2
        assert abs(normalized[0] - 0.6) < 0.01
