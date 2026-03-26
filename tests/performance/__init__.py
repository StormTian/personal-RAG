"""
Performance test fixtures and utilities.
"""

import pytest


@pytest.fixture
def performance_threshold():
    """Performance thresholds for tests."""
    return {
        "search_max_latency_ms": 200,
        "embedding_max_latency_ms": 50,
        "min_throughput_qps": 10,
    }
