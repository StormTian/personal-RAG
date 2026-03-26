# Development Environment Configuration
# Copy this file to .env and fill in your values

# Application Environment
APP_ENV=development
DEBUG=true
PORT=8000
HOST=127.0.0.1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=standard

# OpenAI Configuration (Optional)
# Set these to enable OpenAI embeddings and reranking
# OPENAI_API_KEY=your-api-key-here
# OPENAI_BASE_URL=https://api.openai.com
# OPENAI_EMBED_MODEL=text-embedding-3-small
# OPENAI_RERANK_MODEL=gpt-3.5-turbo

# Reranker Configuration
# OPENAI_RERANK_TIMEOUT=45
# OPENAI_RERANK_MAX_CANDIDATES=12

# Document Library
DOCUMENT_LIBRARY_DIR=./document_library
CHUNK_SIZE=240
CHUNK_OVERLAP=1
TOP_K=3

# Cache Configuration
ENABLE_CACHE=true
CACHE_TTL=3600

# Security
# SECRET_KEY=your-secret-key-here
# ALLOWED_HOSTS=localhost,127.0.0.1

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Rate Limiting
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
