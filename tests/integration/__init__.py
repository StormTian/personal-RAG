"""
Integration test fixtures and utilities.
"""

import pytest


@pytest.fixture(scope="module")
def integration_library():
    """Library for integration tests."""
    # Setup code if needed
    yield None
    # Teardown code if needed
