"""
API test fixtures and utilities.
"""

import pytest


@pytest.fixture
def api_base_url():
    """Base URL for API tests."""
    return "http://localhost:8000"
