# RAG System Architecture

## Overview

This document describes the architecture of the production-ready RAG (Retrieval-Augmented Generation) system.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Security   │  │   Validation │  │   Logging    │      │
│  │  Middleware  │  │  Middleware  │  │  Middleware  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      RAG Engine                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Document   │  │   Index      │  │    Search    │      │
│  │    Loader    │  │   Manager    │  │    Engine    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Embedding Backend│ │ Reranker Backend │ │  Cache Layer     │
│ ┌──────────────┐ │ │ ┌──────────────┐ │ │ ┌──────────────┐ │
│ │   Local      │ │ │ │   Local      │ │ │ │   Memory     │ │
│ │   Hash       │ │ │ │  Heuristic   │ │ │ │   Cache      │ │
│ └──────────────┘ │ │ └──────────────┘ │ │ └──────────────┘ │
│ ┌──────────────┐ │ │ ┌──────────────┐ │ │ ┌──────────────┐ │
│ │   OpenAI     │ │ │ │   OpenAI     │ │ │ │   File       │ │
│ │  Compatible  │ │ │ │  Listwise    │ │ │ │   Cache      │ │
│ └──────────────┘ │ │ └──────────────┘ │ │ └──────────────┘ │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

## Module Descriptions

### 1. API Layer (`rag_system/api/`)

**Purpose**: HTTP interface and request handling

**Components**:
- **server.py**: FastAPI application setup
- **security.py**: Authentication, rate limiting, input validation
- **loader.py**: Document loading with registry pattern

**Key Features**:
- RESTful API design
- Async request handling
- CORS support
- Request validation with Pydantic
- Global exception handling

### 2. RAG Engine (`rag_system/rag_engine.py`)

**Purpose**: Core orchestration logic

**Responsibilities**:
- Document indexing pipeline
- Query processing
- Search result ranking
- Answer generation
- Metrics collection

**Design Patterns**:
- Facade pattern for simplified interface
- Observer pattern for metrics
- Strategy pattern for backends

### 3. Backends (`rag_system/backends/`)

**Embedding Backends**:

| Backend | Description | Use Case |
|---------|-------------|----------|
| LocalHashEmbeddingBackend | Local hash-based embeddings | Offline, no API key needed |
| OpenAICompatibleEmbeddingBackend | OpenAI API client | High quality embeddings |
| CachedEmbeddingBackend | Caching decorator | Reduce API calls |

**Reranker Backends**:

| Backend | Description | Use Case |
|---------|-------------|----------|
| LocalHeuristicReranker | Rule-based reranking | Fast, offline |
| OpenAICompatibleListwiseReranker | LLM-based reranking | High accuracy |

**Key Features**:
- Abstract base classes for extensibility
- Connection pooling for HTTP clients
- Retry logic with exponential backoff
- Async/await support

### 4. Configuration (`rag_system/config/`)

**Purpose**: Centralized configuration management

**Features**:
- YAML/JSON configuration files
- Environment variable integration
- Type-safe settings with dataclasses
- Validation on load
- Hot-reload support

**Configuration Hierarchy** (highest to lowest priority):
1. Environment variables
2. Configuration file
3. Default values

### 5. Monitoring (`rag_system/monitoring/`)

**Logging (`logging_config.py`)**:
- Structured JSON logging
- Configurable log levels
- File rotation
- Console output

**Metrics (`metrics.py`)**:
- Performance metrics collection
- Counter and gauge support
- Metric history retention
- Thread-safe operations

**Health Checks (`health.py`)**:
- Component health monitoring
- Configurable check intervals
- Background monitoring thread
- Health status aggregation

### 6. Core (`rag_system/core/`)

**Base Classes (`base.py`)**:
- Abstract base classes for all components
- Data models (dataclasses)
- Type definitions

**Dependency Injection (`dependency_injection.py`)**:
- Clean dependency management
- Singleton and factory providers
- Auto-injection of dependencies
- Global container

### 7. Exceptions (`rag_system/exceptions/`)

**Custom Exceptions (`base.py`)**:
- Hierarchical exception structure
- Error codes and HTTP status codes
- Detailed error context

**Handlers (`handlers.py`)**:
- Global exception handler
- Structured error responses
- Error metrics tracking

### 8. Utilities (`rag_system/utils/`)

**Retry (`retry.py`)**:
- Exponential backoff
- Jitter
- Configurable retry conditions
- Async support

**Text Processing (`text.py`)**:
- Tokenization (English + Chinese)
- Text chunking
- Sentence splitting
- Vector operations

**File Operations (`file.py`)**:
- Multi-encoding text reading
- Word document extraction
- PDF extraction
- Error handling

## Data Flow

### Indexing Flow

```
Documents → Load → Chunk → Embed → Build BM25 → Cache
```

1. **Discovery**: Find all supported files in library directory
2. **Loading**: Parse documents using appropriate loaders
3. **Chunking**: Split text into overlapping chunks
4. **Embedding**: Generate vector embeddings
5. **BM25**: Calculate term statistics
6. **Caching**: Save index to compressed file

### Query Flow

```
Query → Validate → Embed → Retrieve → Rerank → Generate Answer
```

1. **Validation**: Sanitize and validate query
2. **Embedding**: Convert query to vector
3. **Dense Retrieval**: Cosine similarity search
4. **BM25 Scoring**: Lexical relevance scoring
5. **Reranking**: Reorder candidates
6. **Answer Generation**: Extract and format answer

## Design Principles

### 1. Separation of Concerns

Each module has a single, well-defined responsibility:
- API layer handles HTTP concerns
- Engine orchestrates business logic
- Backends encapsulate external services
- Utils provide pure functions

### 2. Dependency Inversion

Components depend on abstractions:
```python
class RAGEngine:
    def __init__(self, embedding_backend: EmbeddingBackend):
        self.embedding_backend = embedding_backend
```

### 3. Open/Closed Principle

Open for extension, closed for modification:
- New backends can be added without modifying engine
- New document loaders registered via registry
- Configuration extended without code changes

### 4. Async First

All I/O operations are async:
- HTTP requests use aiohttp
- File operations use asyncio
- Database operations would use async drivers

### 5. Fail Fast

Validate early, fail with clear errors:
- Configuration validated on load
- Input validated at API boundary
- Backend connectivity checked on init

### 6. Observability

Comprehensive logging and metrics:
- Structured JSON logs
- Performance metrics
- Error tracking
- Health checks

## Performance Optimizations

### 1. Connection Pooling

HTTP connections reused across requests:
```python
class EmbeddingConnectionPool:
    async def get_session(self) -> aiohttp.ClientSession:
        # Reuse existing session
```

### 2. Batching

Multiple items processed together:
```python
# Batch embedding requests
embeddings = await backend.embed_texts_async(texts, batch_size=32)
```

### 3. Caching

Multiple cache layers:
- Memory cache for embeddings
- Disk cache for index
- Configurable TTL

### 4. Concurrency

Semaphore-based rate limiting:
```python
semaphore = asyncio.Semaphore(5)
results = await asyncio.gather(*[process_batch(b) for b in batches])
```

### 5. Compression

Index cache compressed with gzip:
```python
with gzip.open(cache_path, 'wb') as f:
    pickle.dump(snapshot, f)
```

## Security Features

### 1. API Key Authentication

```python
api_key = request.headers.get("X-API-Key")
if not api_key_validator.validate(api_key):
    raise AuthenticationError()
```

### 2. Rate Limiting

Sliding window rate limiter:
```python
allowed, retry_after = rate_limiter.is_allowed(client_id)
if not allowed:
    raise RateLimitError(retry_after=retry_after)
```

### 3. Input Validation

```python
query = input_validator.validate_query(query)  # Sanitizes input
top_k = input_validator.validate_top_k(top_k)  # Bounds checking
```

### 4. CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
)
```

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution

### Integration Tests
- Test component interactions
- Use test containers for external services
- Verify data flow

### End-to-End Tests
- Test full API endpoints
- Verify response formats
- Performance benchmarks

## Deployment Options

### 1. Direct Execution

```bash
python -m rag_system.api.server
```

### 2. Docker

```dockerfile
FROM python:3.11-slim
COPY . /app
RUN pip install -e /app
CMD ["python", "-m", "rag_system.api.server"]
```

### 3. Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: rag-api
        image: rag-system:latest
```

## Monitoring & Alerting

### Metrics to Track

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| embedding_time_ms | Embedding latency | > 1000ms |
| retrieval_time_ms | Retrieval latency | > 500ms |
| search_total_time_ms | Total search time | > 2000ms |
| search_errors | Error count | > 5/min |
| cache_hit_rate | Cache efficiency | < 80% |

### Health Checks

- Library connectivity
- Embedding backend availability
- Reranker backend availability
- Disk space

## Future Enhancements

1. **Vector Database Integration**: Pinecone, Weaviate, Qdrant
2. **Multi-modal Support**: Images, audio, video
3. **Streaming Responses**: Real-time answer generation
4. **A/B Testing**: Backend comparison framework
5. **Model Fine-tuning**: Domain-specific embeddings
6. **Graph RAG**: Knowledge graph integration
