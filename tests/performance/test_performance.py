"""
Performance tests for stress testing.
"""

import pytest
import time
import threading
import concurrent.futures
from pathlib import Path


class TestEmbeddingPerformance:
    """Performance tests for embedding generation."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_embedding_throughput(self, local_embedding_backend):
        """Test embedding generation throughput."""
        batch_sizes = [1, 5, 10, 20]
        texts_per_batch = 100
        
        for batch_size in batch_sizes:
            texts = [f"Text {i}" for i in range(texts_per_batch)]
            
            start = time.time()
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                local_embedding_backend.embed_texts(batch)
            elapsed = time.time() - start
            
            throughput = texts_per_batch / elapsed
            print(f"\nBatch size {batch_size}: {throughput:.2f} texts/sec")
            
            # Should maintain reasonable throughput
            assert throughput > 10  # At least 10 texts per second
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_embedding_latency_distribution(self, local_embedding_backend):
        """Test embedding latency distribution."""
        latencies = []
        text = "This is a test sentence."
        
        for _ in range(100):
            start = time.time()
            local_embedding_backend.embed_texts([text])
            elapsed = time.time() - start
            latencies.append(elapsed * 1000)  # Convert to ms
        
        latencies.sort()
        p50 = latencies[50]
        p95 = latencies[95]
        p99 = latencies[99]
        
        print(f"\nLatency distribution (ms):")
        print(f"  P50: {p50:.2f}")
        print(f"  P95: {p95:.2f}")
        print(f"  P99: {p99:.2f}")
        
        # Should have reasonable latency
        assert p50 < 50  # 50ms for P50
        assert p95 < 100  # 100ms for P95


class TestSearchPerformance:
    """Performance tests for search operations."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_search_latency_under_load(self, rag_instance):
        """Test search latency under load."""
        queries = [
            "product features",
            "architecture design",
            "vacation policy",
            "deployment guide",
            "API documentation",
        ]
        
        latencies = []
        
        for query in queries * 20:  # 100 total searches
            start = time.time()
            rag_instance.search(query, top_k=3)
            elapsed = time.time() - start
            latencies.append(elapsed * 1000)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        print(f"\nSearch latency:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  Maximum: {max_latency:.2f}ms")
        
        # Should have reasonable latency
        assert avg_latency < 200  # 200ms average
        assert max_latency < 500  # 500ms maximum
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_searches(self, rag_instance):
        """Test concurrent search operations."""
        num_threads = 10
        searches_per_thread = 20
        
        def search_worker():
            for i in range(searches_per_thread):
                rag_instance.search(f"query {i}", top_k=3)
            return True
        
        start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(search_worker) for _ in range(num_threads)]
            results = [f.result() for f in futures]
        
        elapsed = time.time() - start
        total_searches = num_threads * searches_per_thread
        throughput = total_searches / elapsed
        
        print(f"\nConcurrent searches:")
        print(f"  Total: {total_searches}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.2f} searches/sec")
        
        assert all(results)
        assert throughput > 10  # At least 10 searches per second
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_answer_performance(self, rag_instance):
        """Test answer generation performance."""
        queries = [
            "What are the features?",
            "How does the system work?",
            "What is the architecture?",
        ]
        
        latencies = []
        
        for query in queries * 10:
            start = time.time()
            response = rag_instance.answer(query, top_k=3)
            elapsed = time.time() - start
            latencies.append(elapsed * 1000)
            
            assert response.query == query
        
        avg_latency = sum(latencies) / len(latencies)
        
        print(f"\nAnswer generation latency:")
        print(f"  Average: {avg_latency:.2f}ms")
        
        assert avg_latency < 300  # 300ms average


class TestMemoryPerformance:
    """Memory usage performance tests."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_with_large_library(self, temp_dir, local_embedding_backend, local_reranker):
        """Test memory usage with large library."""
        from app import TinyRAG
        import gc
        
        # Create a library with multiple documents
        lib_dir = temp_dir / "large_lib"
        lib_dir.mkdir()
        
        for i in range(10):
            content = f"# Document {i}\n\n" + "Content.\n" * 100
            (lib_dir / f"doc{i}.md").write_text(content, encoding="utf-8")
        
        gc.collect()
        
        # Measure memory before
        import sys
        before_objects = len(gc.get_objects())
        
        rag = TinyRAG(
            library_dir=lib_dir,
            embedding_backend=local_embedding_backend,
            reranker_backend=local_reranker
        )
        
        # Perform operations
        for _ in range(10):
            rag.search("test", top_k=3)
        
        gc.collect()
        after_objects = len(gc.get_objects())
        
        # Memory growth should be reasonable
        print(f"\nMemory usage:")
        print(f"  Objects before: {before_objects}")
        print(f"  Objects after: {after_objects}")
        
        stats = rag.stats()
        print(f"  Documents: {stats['documents']}")
        print(f"  Chunks: {stats['chunks']}")


class TestScalability:
    """Scalability tests."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_scalability_with_increasing_chunks(self, temp_dir, local_embedding_backend, local_reranker):
        """Test scalability with increasing number of chunks."""
        from app import TinyRAG
        
        chunk_counts = [10, 50, 100]
        latencies = []
        
        for target_chunks in chunk_counts:
            # Create library with appropriate size
            lib_dir = temp_dir / f"lib_{target_chunks}"
            lib_dir.mkdir()
            
            doc_size = target_chunks // 5 + 1
            for i in range(5):
                content = f"# Doc {i}\n\n" + "Paragraph.\n\n" * doc_size
                (lib_dir / f"doc{i}.md").write_text(content, encoding="utf-8")
            
            rag = TinyRAG(
                library_dir=lib_dir,
                embedding_backend=local_embedding_backend,
                reranker_backend=local_reranker
            )
            
            # Measure search latency
            start = time.time()
            for _ in range(10):
                rag.search("test query", top_k=3)
            elapsed = time.time() - start
            
            avg_latency = elapsed / 10 * 1000
            latencies.append((target_chunks, avg_latency))
            
            print(f"\nChunks: {target_chunks}, Avg latency: {avg_latency:.2f}ms")
        
        # Latency should scale reasonably
        for i in range(1, len(latencies)):
            ratio = latencies[i][1] / latencies[i-1][1]
            chunks_ratio = latencies[i][0] / latencies[i-1][0]
            print(f"  Latency scaling: {ratio:.2f}x for {chunks_ratio:.2f}x chunks")


class TestLoadTests:
    """Load testing."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_sustained_load(self, rag_instance):
        """Test system under sustained load."""
        duration = 10  # seconds
        queries = [
            "features",
            "architecture",
            "deployment",
            "configuration",
        ]
        
        start = time.time()
        count = 0
        errors = []
        
        while time.time() - start < duration:
            try:
                query = queries[count % len(queries)]
                rag_instance.search(query, top_k=3)
                count += 1
            except Exception as e:
                errors.append(str(e))
        
        elapsed = time.time() - start
        throughput = count / elapsed
        
        print(f"\nSustained load test:")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Queries: {count}")
        print(f"  Throughput: {throughput:.2f} queries/sec")
        print(f"  Errors: {len(errors)}")
        
        assert len(errors) == 0
        assert throughput > 5  # At least 5 queries per second
