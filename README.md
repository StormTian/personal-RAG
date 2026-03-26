# RAG System - Production Ready

A production-ready Retrieval-Augmented Generation system with modular architecture, async support, and comprehensive monitoring.

## Features

- **Modular Architecture**: Clean separation of concerns with abstract base classes
- **Async/Await Support**: Full async I/O for better performance
- **Connection Pooling**: Efficient HTTP connection management
- **Retry Mechanism**: Exponential backoff for resilient external API calls
- **Structured Logging**: JSON-formatted logs for observability
- **Health Checks**: Comprehensive system health monitoring
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Security-focused input sanitization
- **Configuration Management**: YAML/JSON config with hot-reload
- **Dependency Injection**: Clean dependency management

## Architecture

```
rag_system/
├── api/                    # API layer (FastAPI)
│   ├── loader.py          # Document loaders
│   ├── security.py        # Security middleware
│   └── server.py          # HTTP server
├── backends/              # Backend implementations
│   ├── embedding.py       # Embedding backends
│   └── reranker.py        # Reranker backends
├── config/                # Configuration management
│   ├── settings.py        # Settings classes
│   └── loader.py          # Config loader with hot-reload
├── core/                  # Core abstractions
│   ├── base.py            # Base classes
│   └── dependency_injection.py  # DI container
├── exceptions/            # Exception handling
│   ├── base.py            # Custom exceptions
│   └── handlers.py        # Exception handlers
├── monitoring/            # Monitoring & logging
│   ├── logging_config.py  # Structured logging
│   ├── metrics.py         # Metrics collection
│   └── health.py          # Health checks
├── utils/                 # Utilities
│   ├── retry.py           # Retry logic
│   ├── text.py            # Text processing
│   ├── file.py            # File operations
│   └── json_utils.py      # JSON utilities
├── __init__.py            # Package exports
└── rag_engine.py          # Main RAG engine
```

## Installation

```bash
# Clone the repository
cd rag_system

# Install dependencies
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Configuration

Create a `config.yaml` file:

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  workers: 1

embedding:
  backend: "local-hash"  # or "openai-compatible"
  dimensions: 256
  projections_per_token: 8
  # For OpenAI backend:
  # api_key: "${OPENAI_API_KEY}"
  # model: "text-embedding-3-small"
  # base_url: "https://api.openai.com"

reranker:
  backend: "local-heuristic"  # or "openai-compatible"
  # For OpenAI backend:
  # api_key: "${OPENAI_API_KEY}"
  # model: "gpt-4"

retrieval:
  top_k: 3
  bm25_k1: 1.5
  bm25_b: 0.75

chunking:
  max_chars: 240
  overlap: 1

cache:
  enabled: true
  cache_dir: ".index_cache"

logging:
  level: "INFO"
  format: "json"

monitoring:
  enabled: true
  health_check_interval: 30

security:
  rate_limit_enabled: true
  rate_limit_requests: 100
  rate_limit_window: 60
  max_query_length: 1000
```

## Usage

### CLI

```bash
# Run with default settings
python -m rag_system

# Run with custom library directory
python -m rag_system --library-dir ./my_docs

# Run in interactive mode
python -m rag_system --interactive
```

### API Server

```bash
# Start the API server
python -m rag_system.api.server

# Or use uvicorn directly
uvicorn rag_system.api.server:create_app --factory --reload
```

### Python API

```python
from rag_system import RAGEngine

# Initialize engine
engine = RAGEngine(library_dir="./documents")

# Ask a question
response = engine.answer("What is machine learning?")
print(response.answer_lines)

# Search documents
hits = engine.search("neural networks", top_k=5)
for hit in hits:
    print(f"{hit.score:.3f}: {hit.chunk.text[:100]}...")

# Async usage
import asyncio

async def main():
    response = await engine.answer_async("Your question?")
    print(response.answer_lines)

asyncio.run(main())
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?", "top_k": 3}'

# Search
curl "http://localhost:8000/api/search?q=machine+learning&top_k=5"

# Get stats
curl http://localhost:8000/api/stats

# Reload library
curl -X POST http://localhost:8000/api/reload
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_EMBED_MODEL` | OpenAI embedding model | - |
| `OPENAI_RERANK_MODEL` | OpenAI reranker model | - |
| `OPENAI_BASE_URL` | OpenAI API base URL | https://api.openai.com |
| `RAG_HOST` | Server host | 127.0.0.1 |
| `RAG_PORT` | Server port | 8000 |
| `RAG_DEBUG` | Debug mode | false |

## Docker

```bash
# Build image
docker build -t rag-system .

# Run container
docker run -p 8000:8000 -v $(pwd)/documents:/app/document_library rag-system

# Run with docker-compose
docker-compose up -d
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=rag_system

# Run linter
flake8 rag_system
mypy rag_system

# Format code
black rag_system
isort rag_system
```

## License

MIT License
