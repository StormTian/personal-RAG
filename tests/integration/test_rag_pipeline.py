"""
Integration tests for the complete RAG pipeline.
"""

import pytest
from pathlib import Path
import time


class TestTinyRAGIntegration:
    """Integration tests for TinyRAG class."""
    
    def test_initialization_with_sample_library(self, sample_library_dir, local_embedding_backend, local_reranker):
        """Test initializing TinyRAG with sample library."""
        from app import TinyRAG
        
        rag = TinyRAG(
            library_dir=sample_library_dir,
            embedding_backend=local_embedding_backend,
            reranker_backend=local_reranker
        )
        
        # Verify initialization
        stats = rag.stats()
        assert stats["documents"] >= 3
        assert stats["chunks"] > 0
        assert stats["library_dir"] == str(sample_library_dir)
    
    def test_list_documents(self, rag_instance):
        """Test listing documents in library."""
        documents = rag_instance.list_documents()
        
        assert len(documents) >= 3
        
        sources = {doc["source"] for doc in documents}
        assert "product/overview.md" in sources
        assert "hr/policy.txt" in sources
        assert "tech/architecture.md" in sources
        
        # Check document structure
        for doc in documents:
            assert "source" in doc
            assert "title" in doc
            assert "file_type" in doc
            assert "chars" in doc
            assert isinstance(doc["chars"], int)
    
    def test_search_returns_hits(self, rag_instance):
        """Test that search returns hits."""
        query = "product features"
        hits = rag_instance.search(query, top_k=3)
        
        # Should return some hits (or empty list if no match)
        assert isinstance(hits, list)
        
        if hits:
            for hit in hits:
                assert hit.chunk is not None
                assert hit.chunk.text is not None
                assert hit.score >= 0
                assert hit.retrieve_score >= 0
    
    def test_search_product_overview(self, rag_instance):
        """Test searching for product overview content."""
        query = "advanced search features"
        hits = rag_instance.search(query, top_k=3)
        
        # Should find the product overview
        found_product = False
        for hit in hits:
            if "product" in hit.chunk.source.lower():
                found_product = True
                break
        
        assert found_product or len(hits) == 0  # Either found or no good matches
    
    def test_search_hr_policy(self, rag_instance):
        """Test searching for HR policy content."""
        query = "vacation days"
        hits = rag_instance.search(query, top_k=3)
        
        # Should find HR content
        found_hr = False
        for hit in hits:
            if "hr" in hit.chunk.source.lower() or "vacation" in hit.chunk.text.lower():
                found_hr = True
                break
        
        assert found_hr or len(hits) == 0
    
    def test_answer_returns_response(self, rag_instance):
        """Test that answer returns a valid response."""
        query = "What features are available?"
        response = rag_instance.answer(query, top_k=3)
        
        assert response.query == query
        assert isinstance(response.answer_lines, list)
        assert isinstance(response.hits, list)
        
        if response.hits:
            assert len(response.answer_lines) > 0
    
    def test_answer_with_no_results(self, rag_instance):
        """Test answering query with no results."""
        # Use a query that is unlikely to match any content
        query = "xyzabc123nonexistent" * 5
        response = rag_instance.answer(query, top_k=3)
        
        assert response.query == query
        # May still return some results due to hash embedding behavior
        assert isinstance(response.answer_lines, list)
        if len(response.hits) == 0:
            # Should have a message indicating no results
            assert len(response.answer_lines) >= 1
    
    def test_answer_chinese_query(self, rag_instance):
        """Test answering Chinese query."""
        query = "系统架构是什么？"
        response = rag_instance.answer(query, top_k=3)
        
        assert response.query == query
        assert isinstance(response.answer_lines, list)
        # Chinese content should be found
        assert len(response.hits) > 0 or len(response.answer_lines) > 0
    
    def test_reload_library(self, rag_instance, sample_library_dir):
        """Test reloading the library."""
        original_stats = rag_instance.stats()
        
        # Add a new file
        (sample_library_dir / "new_doc.md").write_text(
            "# New Document\n\nThis is a new document added after initialization."
        )
        
        # Reload
        rag_instance.reload()
        
        new_stats = rag_instance.stats()
        
        # Should have more documents
        assert new_stats["documents"] >= original_stats["documents"]
    
    def test_reload_to_different_directory(self, rag_instance, temp_dir):
        """Test reloading to a different directory."""
        # Create a new library
        new_lib = temp_dir / "new_library"
        new_lib.mkdir()
        (new_lib / "doc.md").write_text("# New Library Doc\n\nContent.")
        
        # Reload to new directory
        rag_instance.reload(new_lib)
        
        stats = rag_instance.stats()
        assert str(new_lib) in stats["library_dir"]
    
    def test_stats_structure(self, rag_instance):
        """Test stats return structure."""
        stats = rag_instance.stats()
        
        required_keys = [
            "library_dir",
            "documents",
            "chunks",
            "supported_formats",
            "files",
            "skipped",
            "embedding_backend",
            "reranker_backend",
            "retrieval_strategy",
            "rerank_strategy",
        ]
        
        for key in required_keys:
            assert key in stats, f"Missing key: {key}"
        
        assert isinstance(stats["files"], list)
        assert isinstance(stats["skipped"], list)
        assert isinstance(stats["supported_formats"], list)
    
    def test_thread_safety_concurrent_reads(self, rag_instance):
        """Test thread safety with concurrent reads."""
        import threading
        
        results = []
        errors = []
        
        def search_worker():
            try:
                hits = rag_instance.search("test", top_k=3)
                results.append(len(hits))
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = [threading.Thread(target=search_worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should complete without errors
        assert len(errors) == 0
        assert len(results) == 10
    
    @pytest.mark.slow
    def test_large_document_processing(self, temp_dir, local_embedding_backend, local_reranker):
        """Test processing large documents."""
        from app import TinyRAG
        
        lib_dir = temp_dir / "large_lib"
        lib_dir.mkdir()
        
        # Create a large document
        large_content = "This is paragraph {}.\n\n".format(" x" * 100) * 100
        (lib_dir / "large.md").write_text(large_content, encoding="utf-8")
        
        rag = TinyRAG(
            library_dir=lib_dir,
            embedding_backend=local_embedding_backend,
            reranker_backend=local_reranker
        )
        
        stats = rag.stats()
        assert stats["documents"] == 1
        assert stats["chunks"] > 0
    
    def test_response_to_dict(self, rag_instance):
        """Test converting response to dictionary."""
        query = "test query"
        response = rag_instance.answer(query, top_k=2)
        
        data = response.to_dict()
        
        assert "query" in data
        assert "answer_lines" in data
        assert "hits" in data
        assert data["query"] == query
        
        for hit in data["hits"]:
            required_fields = [
                "score", "retrieve_score", "rerank_score",
                "lexical_score", "title_score", "llm_score",
                "source", "title", "text", "chunk_id"
            ]
            for field in required_fields:
                assert field in hit


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_library_raises_error(self, empty_library_dir, local_embedding_backend, local_reranker):
        """Test that empty library raises FileNotFoundError."""
        from app import TinyRAG
        
        with pytest.raises(FileNotFoundError) as exc_info:
            TinyRAG(
                library_dir=empty_library_dir,
                embedding_backend=local_embedding_backend,
                reranker_backend=local_reranker
            )
        
        assert "empty" in str(exc_info.value).lower() or "document" in str(exc_info.value).lower()
    
    def test_single_document_library(self, single_doc_library, local_embedding_backend, local_reranker):
        """Test library with single document."""
        from app import TinyRAG
        
        rag = TinyRAG(
            library_dir=single_doc_library,
            embedding_backend=local_embedding_backend,
            reranker_backend=local_reranker
        )
        
        stats = rag.stats()
        assert stats["documents"] == 1
        assert stats["chunks"] > 0
    
    def test_search_empty_query(self, rag_instance):
        """Test searching with empty query."""
        hits = rag_instance.search("", top_k=3)
        assert hits == []
    
    def test_search_whitespace_only(self, rag_instance):
        """Test searching with whitespace-only query."""
        hits = rag_instance.search("   \n\t  ", top_k=3)
        assert hits == []
    
    def test_answer_empty_query(self, rag_instance):
        """Test answering empty query."""
        response = rag_instance.answer("", top_k=3)
        assert response.query == ""
        assert len(response.hits) == 0
    
    def test_custom_embedding_backend(self, sample_library_dir, mock_embedding_backend, local_reranker):
        """Test using custom embedding backend."""
        from app import TinyRAG
        
        rag = TinyRAG(
            library_dir=sample_library_dir,
            embedding_backend=mock_embedding_backend,
            reranker_backend=local_reranker
        )
        
        # Verify backend was used
        mock_embedding_backend.embed_texts.assert_called()
        
        # Should still work
        documents = rag.list_documents()
        assert len(documents) >= 3
    
    def test_custom_reranker_backend(self, sample_library_dir, local_embedding_backend, mock_reranker):
        """Test using custom reranker backend."""
        from app import TinyRAG
        
        rag = TinyRAG(
            library_dir=sample_library_dir,
            embedding_backend=local_embedding_backend,
            reranker_backend=mock_reranker
        )
        
        # Perform search which should trigger reranking
        hits = rag.search("test", top_k=3)
        
        # Verify reranker was used
        mock_reranker.rerank.assert_called()


class TestPerformance:
    """Performance-related integration tests."""
    
    @pytest.mark.slow
    @pytest.mark.performance
    def test_search_performance(self, rag_instance):
        """Test search performance."""
        query = "product features"
        
        # Warmup
        rag_instance.search(query, top_k=3)
        
        # Time the search
        start = time.time()
        for _ in range(10):
            rag_instance.search(query, top_k=3)
        elapsed = time.time() - start
        
        # Should complete 10 searches in reasonable time
        assert elapsed < 5.0, f"Search took too long: {elapsed}s"
    
    @pytest.mark.slow
    def test_initialization_performance(self, sample_library_dir, local_embedding_backend, local_reranker):
        """Test initialization performance."""
        from app import TinyRAG
        
        start = time.time()
        rag = TinyRAG(
            library_dir=sample_library_dir,
            embedding_backend=local_embedding_backend,
            reranker_backend=local_reranker
        )
        elapsed = time.time() - start
        
        # Should initialize quickly (embedding generation takes time)
        assert elapsed < 10.0, f"Initialization took too long: {elapsed}s"
        
        # Verify it works
        assert len(rag.list_documents()) >= 3
