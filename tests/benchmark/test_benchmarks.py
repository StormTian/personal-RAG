"""
Benchmark tests for performance measurement.
"""

import pytest


class TestEmbeddingBenchmarks:
    """Benchmark tests for embedding backends."""
    
    @pytest.mark.benchmark
    def test_embed_single_text_benchmark(self, benchmark, local_embedding_backend):
        """Benchmark embedding a single text."""
        text = "This is a test sentence for embedding."
        
        result = benchmark(local_embedding_backend.embed_texts, [text])
        
        assert len(result) == 1
    
    @pytest.mark.benchmark
    def test_embed_multiple_texts_benchmark(self, benchmark, local_embedding_backend):
        """Benchmark embedding multiple texts."""
        texts = [
            f"This is test sentence number {i} with some additional content."
            for i in range(10)
        ]
        
        result = benchmark(local_embedding_backend.embed_texts, texts)
        
        assert len(result) == 10
    
    @pytest.mark.benchmark
    def test_embed_query_benchmark(self, benchmark, local_embedding_backend):
        """Benchmark embedding a query."""
        query = "What is machine learning?"
        
        result = benchmark(local_embedding_backend.embed_query, query)
        
        assert len(result) > 0
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_embed_large_batch_benchmark(self, benchmark, local_embedding_backend):
        """Benchmark embedding a large batch of texts."""
        texts = [
            f"Document {i}: This is a longer document with multiple sentences. "
            "It contains information about various topics. The content is designed "
            "to be representative of real documents."
            for i in range(100)
        ]
        
        result = benchmark(local_embedding_backend.embed_texts, texts)
        
        assert len(result) == 100


class TestSearchBenchmarks:
    """Benchmark tests for search operations."""
    
    @pytest.mark.benchmark
    def test_search_single_word_benchmark(self, benchmark, rag_instance):
        """Benchmark searching with single word query."""
        result = benchmark(rag_instance.search, "features", top_k=3)
        
        assert isinstance(result, list)
    
    @pytest.mark.benchmark
    def test_search_sentence_benchmark(self, benchmark, rag_instance):
        """Benchmark searching with sentence query."""
        result = benchmark(
            rag_instance.search,
            "What are the key features of the product?",
            top_k=3
        )
        
        assert isinstance(result, list)
    
    @pytest.mark.benchmark
    def test_answer_benchmark(self, benchmark, rag_instance):
        """Benchmark answering a query."""
        result = benchmark(
            rag_instance.answer,
            "What are the main features?",
            top_k=3
        )
        
        assert result.query == "What are the main features?"
    
    @pytest.mark.benchmark
    def test_search_with_top_k_3(self, benchmark, rag_instance):
        """Benchmark search with top_k=3."""
        result = benchmark(
            rag_instance.search,
            "test",
            top_k=3
        )
        
        assert isinstance(result, list)


class TestRerankerBenchmarks:
    """Benchmark tests for reranker backends."""
    
    @pytest.mark.benchmark
    def test_local_reranker_benchmark(self, benchmark, local_reranker, minimal_snapshot, sample_candidate_scores):
        """Benchmark local heuristic reranker."""
        result = benchmark(
            local_reranker.rerank,
            "test query",
            minimal_snapshot,
            sample_candidate_scores
        )
        
        assert isinstance(result, list)
    
    @pytest.mark.benchmark
    def test_rerank_with_large_candidate_pool(self, benchmark, local_reranker, minimal_snapshot):
        """Benchmark reranking with large candidate pool."""
        from app import CandidateScore
        
        # Create many candidates
        candidates = [
            CandidateScore(
                index=i,
                retrieve_score=0.9 - (i * 0.01),
                lexical_score=0.8 - (i * 0.01),
                title_score=0.7 - (i * 0.01),
                rerank_score=0.85 - (i * 0.01),
                llm_score=0.0
            )
            for i in range(50)
        ]
        
        result = benchmark(
            local_reranker.rerank,
            "test query",
            minimal_snapshot,
            candidates
        )
        
        assert len(result) == 50


class TestTokenizationBenchmarks:
    """Benchmark tests for tokenization."""
    
    @pytest.mark.benchmark
    def test_tokenize_short_text_benchmark(self, benchmark):
        """Benchmark tokenizing short text."""
        from app import tokenize
        
        text = "The quick brown fox."
        result = benchmark(tokenize, text)
        
        assert len(result) > 0
    
    @pytest.mark.benchmark
    def test_tokenize_long_text_benchmark(self, benchmark):
        """Benchmark tokenizing long text."""
        from app import tokenize
        
        text = " ".join([f"word{i}" for i in range(1000)])
        result = benchmark(tokenize, text)
        
        assert len(result) > 0
    
    @pytest.mark.benchmark
    def test_tokenize_chinese_benchmark(self, benchmark):
        """Benchmark tokenizing Chinese text."""
        from app import tokenize
        
        text = "这是一段用于测试的中文文本。" * 100
        result = benchmark(tokenize, text)
        
        assert len(result) > 0
    
    @pytest.mark.benchmark
    def test_split_sentences_benchmark(self, benchmark):
        """Benchmark splitting sentences."""
        from app import split_sentences
        
        text = "First sentence. Second sentence! Third sentence? " * 20
        result = benchmark(split_sentences, text)
        
        assert len(result) > 0
    
    @pytest.mark.benchmark
    def test_chunk_text_benchmark(self, benchmark):
        """Benchmark chunking text."""
        from app import chunk_text
        
        text = "This is a paragraph.\n\n" * 50
        result = benchmark(chunk_text, text, max_chars=100)
        
        assert len(result) > 0


class TestVectorOperationsBenchmarks:
    """Benchmark tests for vector operations."""
    
    @pytest.mark.benchmark
    def test_normalize_vector_benchmark(self, benchmark):
        """Benchmark vector normalization."""
        from app import normalize_vector
        
        vector = list(range(256))
        result = benchmark(normalize_vector, vector)
        
        assert len(result) == 256
    
    @pytest.mark.benchmark
    def test_cosine_similarity_benchmark(self, benchmark):
        """Benchmark cosine similarity calculation."""
        from app import cosine_similarity
        
        v1 = tuple([1.0] * 256)
        v2 = tuple([0.9] * 256)
        
        result = benchmark(cosine_similarity, v1, v2)
        
        assert isinstance(result, float)


class TestEndToEndBenchmarks:
    """End-to-end benchmark tests."""
    
    @pytest.mark.benchmark
    def test_full_retrieval_pipeline_benchmark(self, benchmark, rag_instance):
        """Benchmark full retrieval pipeline."""
        def full_pipeline():
            hits = rag_instance.search("product features", top_k=3)
            return rag_instance.answer("What are the features?", top_k=3)
        
        result = benchmark(full_pipeline)
        
        assert result.query == "What are the features?"
    
    @pytest.mark.benchmark
    def test_list_documents_benchmark(self, benchmark, rag_instance):
        """Benchmark listing documents."""
        result = benchmark(rag_instance.list_documents)
        
        assert isinstance(result, list)
    
    @pytest.mark.benchmark
    def test_stats_benchmark(self, benchmark, rag_instance):
        """Benchmark getting stats."""
        result = benchmark(rag_instance.stats)
        
        assert "documents" in result
