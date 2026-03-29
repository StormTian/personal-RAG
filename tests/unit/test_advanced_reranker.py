"""Unit tests for CrossEncoderReranker and PRFReranker."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

import numpy as np

from rag_system.backends.cross_encoder_reranker import CrossEncoderReranker
from rag_system.backends.prf_reranker import PRFReranker
from rag_system.core.base import (
    CandidateScore,
    Chunk,
    IndexSnapshot,
    SearchHit,
)


class TestCrossEncoderReranker:
    """Tests for CrossEncoderReranker."""

    def test_init_with_nonexistent_model(self):
        """Test initialization when model file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            reranker = CrossEncoderReranker(model_path=model_path)
            
            assert not reranker.is_healthy()

    def test_rerank_with_fallback(self):
        """Test that reranking falls back when model not loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            reranker = CrossEncoderReranker(model_path=model_path)
            
            # Create mock snapshot and candidates
            snapshot = Mock(spec=IndexSnapshot)
            snapshot.chunks = [Mock(text="Chunk 1"), Mock(text="Chunk 2")]
            
            candidates = [
                CandidateScore(
                    index=0,
                    retrieve_score=0.8,
                    lexical_score=0.3,
                    title_score=0.1,
                    rerank_score=0.0,
                    llm_score=0.0,
                ),
                CandidateScore(
                    index=1,
                    retrieve_score=0.6,
                    lexical_score=0.2,
                    title_score=0.1,
                    rerank_score=0.0,
                    llm_score=0.0,
                ),
            ]
            
            # Should not raise error, uses fallback
            result = reranker.rerank("test query", snapshot, candidates)
            
            assert isinstance(result, list)
            assert len(result) == 2

    def test_max_candidates_limit(self):
        """Test that max_candidates limits the number of reranked items."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "nonexistent.onnx"
            reranker = CrossEncoderReranker(model_path=model_path, max_candidates=5)
            
            assert reranker._max_candidates == 5
            assert reranker.candidate_pool_size(3) <= 5


class TestPRFReranker:
    """Tests for PRFReranker."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        reranker = PRFReranker()
        
        assert reranker._num_terms == 3
        assert reranker._min_doc_freq == 2
        assert reranker._term_weight == 0.3

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        reranker = PRFReranker(num_terms=5, min_doc_freq=3, term_weight=0.5)
        
        assert reranker._num_terms == 5
        assert reranker._min_doc_freq == 3
        assert reranker._term_weight == 0.5

    def test_expand_query_no_results(self):
        """Test query expansion with no initial results."""
        reranker = PRFReranker()
        snapshot = Mock(spec=IndexSnapshot)
        
        query = "machine learning"
        expanded = reranker.expand_query(query, [], snapshot)
        
        # Should return original query
        assert expanded == query

    def test_expand_query_with_results(self):
        """Test query expansion with initial results."""
        reranker = PRFReranker(num_terms=2, min_doc_freq=1)
        
        # Create mock search hits
        hits = [
            SearchHit(
                chunk=Chunk(
                    chunk_id=0,
                    source="doc1.md",
                    title="Doc 1",
                    text="artificial intelligence neural networks",
                ),
                score=0.9,
                retrieve_score=0.8,
                rerank_score=0.9,
                lexical_score=0.3,
                title_score=0.1,
                llm_score=0.0,
            ),
            SearchHit(
                chunk=Chunk(
                    chunk_id=1,
                    source="doc2.md",
                    title="Doc 2",
                    text="deep learning ai algorithms",
                ),
                score=0.8,
                retrieve_score=0.7,
                rerank_score=0.8,
                lexical_score=0.3,
                title_score=0.1,
                llm_score=0.0,
            ),
        ]
        
        snapshot = Mock(spec=IndexSnapshot)
        
        query = "machine learning"
        expanded = reranker.expand_query(query, hits, snapshot)
        
        # Expanded query should include original query
        assert query in expanded
        # Should include some expansion terms
        assert len(expanded) > len(query)

    def test_get_expansion_terms_filters_original(self):
        """Test that original query terms are filtered out."""
        reranker = PRFReranker(num_terms=3, min_doc_freq=1)
        
        hits = [
            SearchHit(
                chunk=Chunk(
                    chunk_id=0,
                    source="doc1.md",
                    title="Doc 1",
                    text="hello world test example",
                ),
                score=0.9,
                retrieve_score=0.8,
                rerank_score=0.9,
                lexical_score=0.3,
                title_score=0.1,
                llm_score=0.0,
            ),
        ]
        
        query = "hello world"
        terms = reranker._get_expansion_terms(query, hits)
        
        # Original terms should not be in expansion
        assert "hello" not in terms
        assert "world" not in terms
        # New terms should be present
        assert len(terms) > 0

    def test_get_expansion_terms_respects_min_doc_freq(self):
        """Test that min_doc_freq is respected."""
        reranker = PRFReranker(num_terms=5, min_doc_freq=2)
        
        hits = [
            SearchHit(
                chunk=Chunk(
                    chunk_id=0,
                    source="doc1.md",
                    title="Doc 1",
                    text="common term rare1",
                ),
                score=0.9,
                retrieve_score=0.8,
                rerank_score=0.9,
                lexical_score=0.3,
                title_score=0.1,
                llm_score=0.0,
            ),
            SearchHit(
                chunk=Chunk(
                    chunk_id=1,
                    source="doc2.md",
                    title="Doc 2",
                    text="common term rare2",
                ),
                score=0.8,
                retrieve_score=0.7,
                rerank_score=0.8,
                lexical_score=0.3,
                title_score=0.1,
                llm_score=0.0,
            ),
        ]
        
        query = "query"
        terms = reranker._get_expansion_terms(query, hits)
        
        # "common" appears in both docs, "term" appears in both
        # "rare1" and "rare2" appear only once
        assert "common" in terms
        assert "term" in terms

    def test_get_expansion_terms_filters_short_terms(self):
        """Test that single character terms are filtered."""
        reranker = PRFReranker(min_doc_freq=1)  # Allow single doc frequency
        
        hits = [
            SearchHit(
                chunk=Chunk(
                    chunk_id=0,
                    source="doc1.md",
                    title="Doc 1",
                    text="a ab abc abcd",
                ),
                score=0.9,
                retrieve_score=0.8,
                rerank_score=0.9,
                lexical_score=0.3,
                title_score=0.1,
                llm_score=0.0,
            ),
        ]
        
        query = "query"
        terms = reranker._get_expansion_terms(query, hits)
        
        # Single char should be filtered
        assert "a" not in terms
        # Two chars should be included
        assert "ab" in terms or "abc" in terms or "abcd" in terms

    def test_get_expansion_terms_with_scores(self):
        """Test getting expansion terms with scores."""
        reranker = PRFReranker(num_terms=3)
        
        hits = [
            SearchHit(
                chunk=Chunk(
                    chunk_id=0,
                    source="doc1.md",
                    title="Doc 1",
                    text="machine learning algorithms",
                ),
                score=0.9,
                retrieve_score=0.8,
                rerank_score=0.9,
                lexical_score=0.3,
                title_score=0.1,
                llm_score=0.0,
            ),
        ]
        
        query = "ai"
        terms_with_scores = reranker.get_expansion_terms_with_scores(query, hits)
        
        assert isinstance(terms_with_scores, list)
        if len(terms_with_scores) > 0:
            assert isinstance(terms_with_scores[0], tuple)
            assert len(terms_with_scores[0]) == 2
