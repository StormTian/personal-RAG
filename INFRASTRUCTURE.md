# RAG Application - Production Configuration

This document describes the complete production infrastructure setup for the RAG (Retrieval-Augmented Generation) application.

## Project Structure

```
.
├── app.py                      # Main RAG logic
├── web_app.py                  # Web interface
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Project configuration (Black, isort, flake8, mypy, pytest)
├── setup.py                    # Package setup
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production environment
├── .dockerignore               # Docker build exclusions
├── .pre-commit-config.yaml     # Pre-commit hooks
├── mypy.ini                    # Type checking configuration
├── bandit.yaml                 # Security scanning configuration
├── Makefile                    # Common commands
├── .env.example                # Environment template
├── .gitignore                  # Git exclusions
├── LICENSE                     # MIT License
├── SECURITY.md                 # Security policy
│
├── deploy.sh                   # Deployment script
├── init.sh                     # Initialization script
├── health_check.sh             # Health check script
│
├── config/                     # Configuration files
│   ├── prometheus.yml          # Monitoring configuration
│   ├── nginx.conf              # Reverse proxy configuration
│   ├── logging.conf            # Logging configuration
│   ├── settings.development.py # Development settings
│   └── settings.production.py  # Production settings
│
├── .github/                    # GitHub Actions
│   └── workflows/
│       ├── ci.yml              # Continuous Integration
│       └── cd.yml              # Continuous Deployment
│
├── web/                        # Web frontend
├── document_library/           # Document storage
└── logs/                       # Application logs
```

## Configuration Categories

### 1. Docker Configuration

- **Dockerfile**: Multi-stage build (builder, production, development)
- **docker-compose.yml**: Development environment with monitoring
- **docker-compose.prod.yml**: Production with Nginx, Prometheus, SSL
- **.dockerignore**: Build exclusions

### 2. Dependency Management

- **requirements.txt**: Production dependencies (pypdf)
- **requirements-dev.txt**: Development dependencies (testing, linting)
- **pyproject.toml**: Modern Python project configuration
- **setup.py**: Package installation

### 3. Code Quality

- **.pre-commit-config.yaml**: Pre-commit hooks
- **pyproject.toml**: Black, isort, flake8, pytest, coverage
- **mypy.ini**: Type checking
- **bandit.yaml**: Security scanning

### 4. CI/CD

- **.github/workflows/ci.yml**: Automated testing, linting, security scans
- **.github/workflows/cd.yml**: Docker builds, deployments

### 5. Deployment Scripts

- **deploy.sh**: Production deployment with health checks
- **init.sh**: Development environment setup
- **health_check.sh**: Application monitoring

### 6. Configuration

- **config/prometheus.yml**: Metrics collection
- **config/nginx.conf**: Reverse proxy, SSL, rate limiting
- **config/logging.conf**: Log rotation and formatting
- **.env.example**: Environment variables template

### 7. Security & Compliance

- **LICENSE**: MIT License
- **SECURITY.md**: Security policy and reporting
- **.gitignore**: Secret exclusions

### 8. Development Tools

- **Makefile**: Common task automation

## Quick Start

### Development Setup

```bash
# Initialize project
./init.sh

# Or manually
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Run tests
make test

# Start development server
make run
```

### Docker Development

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Deployment

```bash
# Configure environment
cp .env.example .env.production
# Edit .env.production with your settings

# Deploy
./deploy.sh production

# Check health
./health_check.sh
```

## Commands Reference

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make install` | Install production dependencies |
| `make dev` | Install development dependencies |
| `make run` | Start web application |
| `make test` | Run all tests |
| `make test-cov` | Run tests with coverage |
| `make lint` | Run all linters |
| `make format` | Format code (Black + isort) |
| `make security` | Run security scans |
| `make docker-build` | Build Docker image |
| `make deploy` | Deploy to production |
| `make health` | Check application health |
| `make clean` | Clean build artifacts |

### Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start development environment |
| `docker-compose -f docker-compose.prod.yml up -d` | Start production environment |
| `docker-compose logs -f` | View logs |
| `docker-compose down` | Stop containers |

## Security Features

- Non-root Docker containers
- Input validation and sanitization
- Rate limiting (Nginx)
- HTTPS/SSL support
- Secret detection (pre-commit hooks)
- Security scanning (Bandit, Safety)
- Dependency vulnerability checking

## Monitoring

- Prometheus metrics collection
- Health check endpoints
- Structured logging
- Resource monitoring
- Alert configuration ready

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `APP_ENV`: development/production
- `OPENAI_API_KEY`: For cloud embeddings (optional)
- `SECRET_KEY`: For session security
- `ALLOWED_HOSTS`: Host whitelist

## License

MIT License - see LICENSE file

## Security

See SECURITY.md for security policy and reporting procedures.
