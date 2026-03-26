# Test Suite for RAG Demo

This directory contains the complete test suite for the RAG (Retrieval Augmented Generation) demo project.

## Directory Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_tokenizer.py       # Text tokenization tests
│   ├── test_embedding.py       # Embedding backend tests
│   ├── test_reranker.py        # Reranker tests
│   ├── test_parser.py          # Document parser tests
│   └── test_utils.py           # Utility function tests
├── integration/                # Integration tests
│   ├── __init__.py
│   └── test_rag_pipeline.py    # End-to-end RAG tests
├── api/                        # API tests
│   ├── __init__.py
│   └── test_web_api.py         # Web API tests
├── benchmark/                  # Benchmark tests
│   ├── __init__.py
│   └── test_benchmarks.py      # Performance benchmarks
└── performance/                # Performance tests
    ├── __init__.py
    └── test_performance.py     # Stress tests
```

## Configuration

- `pytest.ini` - Pytest configuration
- `conftest.py` - Shared fixtures and test configuration

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test categories
```bash
# Unit tests only
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# API tests
pytest tests/api -v

# Benchmarks
pytest tests/benchmark -v

# Performance tests
pytest tests/performance -v
```

### Run with coverage
```bash
pytest --cov=app --cov=web_app --cov-report=html --cov-report=term-missing
```

### Run specific markers
```bash
# Skip slow tests
pytest -m "not slow"

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only API tests
pytest -m api

# Run only benchmark tests
pytest -m benchmark
```

### Run with different verbosity
```bash
# Quiet mode
pytest -q

# Verbose mode
pytest -v

# Very verbose
pytest -vv
```

## Test Markers

- `slow` - Slow tests (excluded by default)
- `unit` - Unit tests
- `integration` - Integration tests
- `api` - API tests
- `benchmark` - Benchmark tests
- `performance` - Performance tests

## Fixtures

### Core Fixtures

- `sample_library_dir` - Sample document library with test files
- `empty_library_dir` - Empty library for error testing
- `single_doc_library` - Library with single document
- `local_embedding_backend` - Local hash embedding backend
- `local_reranker` - Local heuristic reranker
- `rag_instance` - TinyRAG instance with sample library
- `sample_chunks` - Sample chunk objects
- `sample_candidate_scores` - Sample candidate scores
- `minimal_snapshot` - Minimal index snapshot

### Utility Fixtures

- `temp_dir` - Temporary directory for test files
- `project_root` - Project root directory
- `clean_env` - Clean environment variables
- `mock_openai_env` - Mock OpenAI environment variables

## Writing Tests

### Basic Test Structure

```python
import pytest

def test_example():
    """Test description."""
    result = some_function()
    assert result == expected_value

class TestClass:
    """Test class description."""
    
    def test_method(self):
        """Test method description."""
        assert True
```

### Using Fixtures

```python
def test_with_fixture(rag_instance):
    """Test using RAG instance fixture."""
    documents = rag_instance.list_documents()
    assert len(documents) > 0
```

### Marking Tests

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """A slow test."""
    pass

@pytest.mark.unit
def test_unit_test():
    """A unit test."""
    pass
```

## Coverage Reports

Coverage reports are generated in multiple formats:

- `tests/reports/coverage_html/` - HTML report
- `tests/reports/coverage.xml` - XML report for CI integration
- `tests/reports/lcov.info` - LCOV report

View HTML report:
```bash
open tests/reports/coverage_html/index.html
```
