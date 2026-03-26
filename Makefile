# RAG Application - Makefile
# Provides convenient shortcuts for common development tasks

.PHONY: help install dev test lint format clean build run deploy docker start-all stop-all frontend-dev

# Default target
help:
	@echo "RAG Application - Available Commands"
	@echo "====================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev           - Install development dependencies"
	@echo "  make init          - Initialize project (setup venv, install deps)"
	@echo ""
	@echo "Development:"
	@echo "  make run           - Run the web application"
	@echo "  make start-all     - Start both backend and frontend"
	@echo "  make stop-all      - Stop all running services"
	@echo "  make frontend-dev  - Start frontend development server"
	@echo "  make cli           - Run CLI interactive mode"
	@echo "  make test          - Run all tests"
	@echo "  make test-quick    - Run quick tests only"
	@echo "  make test-cov      - Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run all linters"
	@echo "  make format        - Format code with Black and isort"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make security      - Run security scans"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run with Docker Compose"
	@echo "  make docker-stop   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy        - Deploy to production"
	@echo "  make deploy-dev    - Deploy to development"
	@echo "  make health        - Check application health"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make clean-all     - Clean everything including venv"
	@echo "  make backup        - Create backup"
	@echo ""

# Setup & Installation
install:
	pip install -r requirements.txt

dev: install
	pip install -r requirements-dev.txt

init:
	chmod +x init.sh
	./init.sh

# Development
run:
	@echo "🚀 Starting FastAPI backend..."
	@uvicorn rag_system.api.server:create_app --factory --host 0.0.0.0 --port 8000 --reload

run-bg:
	@echo "🚀 Starting FastAPI backend in background..."
	@nohup uvicorn rag_system.api.server:create_app --factory --host 0.0.0.0 --port 8000 > /tmp/rag-backend.log 2>&1 &
	@echo "✅ Backend started at http://localhost:8000"
	@echo "📜 Logs: tail -f /tmp/rag-backend.log"

# Start both backend and frontend
start-all:
	@echo "🚀 Starting RAG Application (Backend + Frontend)..."
	@echo "📡 Backend:  http://localhost:8000"
	@echo "🎨 Frontend: http://localhost:5173"
	@echo ""
	@make run-bg
	@sleep 3
	@cd web-new && npm install && npm run dev

# Stop all services
stop-all:
	@echo "🛑 Stopping all services..."
	@pkill -f "uvicorn.*rag_system" || true
	@pkill -f "npm.*run dev" || true
	@pkill -f "vite" || true
	@echo "✅ All services stopped"

cli:
	python app.py

demo:
	python app.py --demo

# Testing
test:
	pytest -v

test-quick:
	pytest -v -m "not slow" --tb=short

test-cov:
	pytest -v --cov=. --cov-report=html --cov-report=term

test-ci:
	pytest -v --cov=. --cov-report=xml --cov-fail-under=80

# Code Quality
lint: lint-black lint-isort lint-flake8 lint-mypy
	@echo "All linting checks passed!"

lint-black:
	black --check .

lint-isort:
	isort --check-only .

lint-flake8:
	flake8 --max-line-length=88 --extend-ignore=E203,W503 .

lint-mypy:
	mypy --config-file mypy.ini app.py web_app.py

format:
	black .
	isort .

type-check:
	mypy --config-file mypy.ini app.py web_app.py

security:
	bandit -c bandit.yaml -r . -f txt
	safety check

pre-commit:
	pre-commit run --all-files

# Docker
docker-build:
	docker build -t rag-demo:latest .

docker-build-dev:
	docker build --target development -t rag-demo:dev .

docker-run:
	docker-compose up -d

docker-run-dev:
	docker-compose up

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Deployment
deploy:
	chmod +x deploy.sh
	./deploy.sh production

deploy-dev:
	chmod +x deploy.sh
	./deploy.sh staging

deploy-docker:
	docker-compose -f docker-compose.prod.yml up -d

health:
	chmod +x health_check.sh
	./health_check.sh

# Maintenance
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .eggs/ .tox/ .nox/ .coverage htmlcov/
	rm -rf .pytest_cache .mypy_cache

clean-all: clean
	rm -rf .venv venv env
	rm -rf .cache .index_cache.pkl
	find . -type f -name ".DS_Store" -delete

backup:
	mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	tar -czf backups/$(shell date +%Y%m%d_%H%M%S)/backup.tar.gz document_library/ config/ logs/ || true

# CI/CD Helpers
ci: lint test-ci security
	@echo "CI checks completed"

release:
	@echo "Creating release..."
	git tag -a v$(shell python -c "import sys; sys.path.insert(0, '.'); from app import __version__; print(__version__)") -m "Release"
	git push origin --tags

# Document Management
docs-list:
	python app.py --list-docs

docs-reload:
	curl -X POST http://localhost:8000/api/reload

docs-stats:
	curl http://localhost:8000/api/library | python -m json.tool

# Monitoring
metrics:
	curl http://localhost:9090/metrics || echo "Prometheus not available"

logs:
	tail -f logs/app.log

logs-error:
	tail -f logs/error.log
