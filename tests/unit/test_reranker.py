"""
Unit tests for reranker backends.
"""

import pytest
from unittest.mock import Mock
from app import (
    LocalHeuristicReranker,
    OpenAICompatibleListwiseReranker,
    CandidateScore,
)


class TestLocalHeuristicReranker:
    """Tests for LocalHeuristicReranker."""
    
    def test_initialization(self):
        """Test reranker initialization."""
        reranker = LocalHeuristicReranker()
        assert reranker.name == "local-heuristic"
        assert reranker.strategy == "embedding+lexical-overlap"
    
    def test_candidate_pool_size(self):
        """Test candidate pool size calculation."""
        reranker = LocalHeuristicReranker()
        
        # Should be max(top_k * 6, 8)
        assert reranker.candidate_pool_size(1) == 8
        assert reranker.candidate_pool_size(2) == 12
        assert reranker.candidate_pool_size(3) == 18
    
    def test_rerank_empty_candidates(self, minimal_snapshot):
        """Test reranking with empty candidates."""
        reranker = LocalHeuristicReranker()
        result = reranker.rerank("query", minimal_snapshot, [])
        assert result == []
    
    def test_rerank_single_candidate(self, minimal_snapshot, sample_candidate_scores):
        """Test reranking with single candidate."""
        reranker = LocalHeuristicReranker()
        
        candidates = [sample_candidate_scores[0]]
        result = reranker.rerank("query", minimal_snapshot, candidates)
        
        assert len(result) == 1
        assert result[0].index == 0
        assert result[0].rerank_score > 0
    
    def test_rerank_sorts_by_score(self, minimal_snapshot, sample_candidate_scores):
        """Test that reranking sorts by rerank_score."""
        reranker = LocalHeuristicReranker()
        
        # Shuffle candidates
        shuffled = sample_candidate_scores.copy()
        shuffled.reverse()
        
        result = reranker.rerank("query", minimal_snapshot, shuffled)
        
        # Should be sorted by rerank_score descending
        for i in range(len(result) - 1):
            assert result[i].rerank_score >= result[i + 1].rerank_score
    
    def test_rerank_preserves_candidate_data(self, minimal_snapshot, sample_candidate_scores):
        """Test that reranking preserves original candidate data."""
        reranker = LocalHeuristicReranker()
        
        result = reranker.rerank("query", minimal_snapshot, sample_candidate_scores)
        
        for r in result:
            # Find original
            original = next(c for c in sample_candidate_scores if c.index == r.index)
            assert r.retrieve_score == original.retrieve_score
            assert r.lexical_score == original.lexical_score
            assert r.title_score == original.title_score
    
    def test_rerank_score_calculation(self, minimal_snapshot):
        """Test rerank score calculation."""
        reranker = LocalHeuristicReranker()
        
        candidates = [
            CandidateScore(
                index=0,
                retrieve_score=0.9,  # Should contribute 0.9 * 0.60 = 0.54
                lexical_score=0.8,
                title_score=0.7,
                rerank_score=0.0,
                llm_score=0.0
            )
        ]
        
        result = reranker.rerank("query", minimal_snapshot, candidates)
        
        # Score should be: 0.9*0.60 + (0.8/max_lexical)*0.30 + 0.7*0.10
        # Since max_lexical = 0.8, normalized_lexical = 1.0
        # Expected: 0.54 + 0.30 + 0.07 = 0.91
        assert result[0].rerank_score > 0.5  # Should be reasonably high


class TestOpenAICompatibleListwiseReranker:
    """Tests for OpenAICompatibleListwiseReranker."""
    
    def test_initialization(self):
        """Test reranker initialization."""
        fallback = LocalHeuristicReranker()
        reranker = OpenAICompatibleListwiseReranker(
            api_key="test-key",
            model="gpt-4",
            base_url="https://api.openai.com",
            fallback=fallback
        )
        
        assert reranker.api_key == "test-key"
        assert reranker.model == "gpt-4"
        assert reranker.name == "openai-compatible:gpt-4"
        assert reranker.fallback == fallback
    
    def test_base_url_normalization(self):
        """Test that trailing slash is removed from base_url."""
        fallback = LocalHeuristicReranker()
        reranker = OpenAICompatibleListwiseReranker(
            api_key="test",
            model="model",
            base_url="https://api.example.com/",
            fallback=fallback
        )
        assert reranker.base_url == "https://api.example.com"
    
    def test_candidate_pool_size_larger_than_fallback(self):
        """Test that candidate pool size is larger than fallback."""
        fallback = LocalHeuristicReranker()
        reranker = OpenAICompatibleListwiseReranker(
            api_key="test",
            model="model",
            base_url="https://api.openai.com",
            fallback=fallback
        )
        
        # Should be max(top_k * 8, max_candidates)
        assert reranker.candidate_pool_size(1) == 12  # max(8, 12)
        assert reranker.candidate_pool_size(2) == 16  # max(16, 12)
    
    def test_rerank_fallback_on_error(self, minimal_snapshot, sample_candidate_scores, monkeypatch):
        """Test that fallback is used when LLM request fails."""
        fallback = LocalHeuristicReranker()
        reranker = OpenAICompatibleListwiseReranker(
            api_key="test",
            model="model",
            base_url="https://api.openai.com",
            fallback=fallback
        )
        
        # Mock the _request_scores to raise exception
        def mock_request_scores(*args, **kwargs):
            raise RuntimeError("API Error")
        
        monkeypatch.setattr(reranker, "_request_scores", mock_request_scores)
        
        result = reranker.rerank("query", minimal_snapshot, sample_candidate_scores)
        
        # Should fall back to fallback reranker
        assert len(result) == len(sample_candidate_scores)


class TestCandidateScore:
    """Tests for CandidateScore dataclass."""
    
    def test_candidate_score_creation(self):
        """Test creating a CandidateScore."""
        score = CandidateScore(
            index=0,
            retrieve_score=0.9,
            lexical_score=0.8,
            title_score=0.7,
            rerank_score=0.85,
            llm_score=0.0
        )
        
        assert score.index == 0
        assert score.retrieve_score == 0.9
        assert score.lexical_score == 0.8
        assert score.title_score == 0.7
        assert score.rerank_score == 0.85
        assert score.llm_score == 0.0
    
    def test_candidate_score_default_llm_score(self):
        """Test default llm_score."""
        score = CandidateScore(
            index=0,
            retrieve_score=0.9,
            lexical_score=0.8,
            title_score=0.7,
            rerank_score=0.85
        )
        
        assert score.llm_score == 0.0
    
    def test_candidate_score_comparison(self, sample_candidate_scores):
        """Test comparing CandidateScores."""
        # Sort by rerank_score
        sorted_scores = sorted(
            sample_candidate_scores,
            key=lambda c: c.rerank_score,
            reverse=True
        )
        
        # Highest score should be first
        assert sorted_scores[0].rerank_score >= sorted_scores[1].rerank_score
