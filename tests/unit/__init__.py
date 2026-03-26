"""
Test fixtures and utilities for unit tests.
"""

import pytest


@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return [
        "Machine learning is a subset of artificial intelligence.",
        "Python is a popular programming language.",
        "The quick brown fox jumps over the lazy dog.",
    ]


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "What is machine learning?"
