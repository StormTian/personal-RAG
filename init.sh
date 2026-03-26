#!/bin/bash
#
# RAG Application - Initialization Script
# Usage: ./init.sh
# Sets up the development or production environment
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Check Python version
check_python() {
    log_step "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Python version: ${PYTHON_VERSION}"
    
    # Check if Python >= 3.11
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        log_info "Python version is compatible"
    else
        log_error "Python 3.11 or higher is required"
        exit 1
    fi
}

# Create virtual environment
setup_venv() {
    log_step "Setting up virtual environment..."
    
    if [ -d ".venv" ]; then
        log_warn "Virtual environment already exists"
        read -p "Recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .venv
        else
            log_info "Using existing virtual environment"
            return
        fi
    fi
    
    python3 -m venv .venv
    log_info "Virtual environment created"
}

# Install dependencies
install_deps() {
    log_step "Installing dependencies..."
    
    source .venv/bin/activate
    
    pip install --upgrade pip setuptools wheel
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_info "Production dependencies installed"
    fi
    
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
        log_info "Development dependencies installed"
    fi
}

# Install pre-commit hooks
setup_precommit() {
    log_step "Setting up pre-commit hooks..."
    
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        log_info "Pre-commit hooks installed"
    else
        log_warn "pre-commit not found, skipping"
    fi
}

# Create necessary directories
create_directories() {
    log_step "Creating directories..."
    
    mkdir -p document_library
    mkdir -p config
    mkdir -p logs
    mkdir -p backups
    mkdir -p tests
    
    log_info "Directories created"
}

# Create environment files
create_env_files() {
    log_step "Creating environment files..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info ".env file created from template"
        fi
    else
        log_warn ".env file already exists"
    fi
}

# Setup Git hooks
setup_git() {
    log_step "Setting up Git configuration..."
    
    if [ -d ".git" ]; then
        # Setup git hooks directory
        git config core.hooksPath .githooks 2>/dev/null || true
        
        # Setup git attributes
        if [ ! -f ".gitattributes" ]; then
            cat > .gitattributes << 'EOF'
*.py text eol=lf
*.sh text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.md text eol=lf
EOF
            log_info ".gitattributes created"
        fi
        
        log_info "Git configuration completed"
    fi
}

# Check Docker
setup_docker() {
    log_step "Checking Docker..."
    
    if command -v docker &> /dev/null; then
        log_info "Docker is installed: $(docker --version)"
        
        if command -v docker-compose &> /dev/null; then
            log_info "Docker Compose is installed"
        else
            log_warn "Docker Compose not found"
        fi
    else
        log_warn "Docker not found, skipping Docker setup"
    fi
}

# Run tests to verify setup
verify_setup() {
    log_step "Verifying setup..."
    
    source .venv/bin/activate
    
    # Check if imports work
    if python -c "import app; import web_app; print('Imports OK')" 2>/dev/null; then
        log_info "Import check passed"
    else
        log_warn "Import check failed, but continuing..."
    fi
    
    # Run a simple test if pytest is available
    if command -v pytest &> /dev/null; then
        log_info "Running basic tests..."
        pytest -xvs test_app.py -k "test_" --tb=short 2>/dev/null || log_warn "Some tests failed, but setup is complete"
    fi
}

# Print summary
print_summary() {
    echo
    echo "=========================================="
    log_info "Setup completed successfully!"
    echo "=========================================="
    echo
    echo "Next steps:"
    echo "  1. Activate virtual environment: source .venv/bin/activate"
    echo "  2. Configure environment: edit .env file"
    echo "  3. Add documents to document_library/"
    echo "  4. Run CLI: python app.py --help"
    echo "  5. Run Web UI: python web_app.py"
    echo
    echo "Useful commands:"
    echo "  make test       - Run tests"
    echo "  make lint       - Run linters"
    echo "  make format     - Format code"
    echo "  make run        - Start the application"
    echo
}

# Main
main() {
    log_info "Initializing RAG Application..."
    
    check_python
    setup_venv
    install_deps
    create_directories
    create_env_files
    setup_precommit
    setup_git
    setup_docker
    verify_setup
    print_summary
}

main "$@"
