# Production Environment Configuration
# Copy this file to .env.production and fill in your values

# Application Environment
APP_ENV=production
DEBUG=false
PORT=8000
HOST=0.0.0.0

# Logging
LOG_LEVEL=WARNING
LOG_FORMAT=detailed

# OpenAI Configuration (Optional but recommended for production)
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://api.openai.com}
OPENAI_EMBED_MODEL=${OPENAI_EMBED_MODEL:-text-embedding-3-small}
OPENAI_RERANK_MODEL=${OPENAI_RERANK_MODEL:-gpt-3.5-turbo}

# Reranker Configuration
OPENAI_RERANK_TIMEOUT=45
OPENAI_RERANK_MAX_CANDIDATES=12

# Document Library
DOCUMENT_LIBRARY_DIR=/app/document_library
CHUNK_SIZE=240
CHUNK_OVERLAP=1
TOP_K=3

# Cache Configuration
ENABLE_CACHE=true
CACHE_TTL=7200

# Security
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=${ALLOWED_HOSTS}

# SSL/TLS
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
PROMETHEUS_RETENTION=15d

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Performance
WORKERS=4
THREADS=2
MAX_REQUESTS=1000
TIMEOUT=60

# Health Check
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10

# Backup
BACKUP_ENABLED=true
BACKUP_INTERVAL=daily
BACKUP_RETENTION_DAYS=30

# Alerting
ALERT_EMAIL=${ALERT_EMAIL}
ALERT_SLACK_WEBHOOK=${ALERT_SLACK_WEBHOOK}
