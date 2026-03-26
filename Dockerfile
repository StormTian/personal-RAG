# RAG Application - Multi-stage Docker Build
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim AS production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r ragapp && useradd -r -g ragapp ragapp

# Copy Python packages from builder
COPY --from=builder /root/.local /home/ragapp/.local

# Set environment
ENV PATH=/home/ragapp/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8000

# Copy application code
COPY --chown=ragapp:ragapp . .

# Create necessary directories
RUN mkdir -p /app/document_library /app/web /app/config \
    && chown -R ragapp:ragapp /app

# Switch to non-root user
USER ragapp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/health')" || exit 1

# Expose port
EXPOSE ${PORT}

# Run the application
CMD ["python", "web_app.py", "--host", "0.0.0.0", "--port", "8000"]

# Stage 3: Development
FROM python:3.11-slim AS development

WORKDIR /app

# Install system dependencies including tools for development
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=development \
    PORT=8000

# Create necessary directories
RUN mkdir -p /app/document_library /app/web /app/config

# Default command for development
CMD ["python", "web_app.py", "--host", "0.0.0.0", "--port", "8000"]
