#!/bin/bash
#
# RAG Application - Deployment Script
# Usage: ./deploy.sh [environment] [version]
# Example: ./deploy.sh production v1.0.0
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_NAME="rag-demo"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_info "All dependencies are installed"
}

load_environment() {
    log_info "Loading environment configuration..."
    
    if [ -f ".env.${ENVIRONMENT}" ]; then
        export $(cat .env.${ENVIRONMENT} | grep -v '#' | xargs)
        log_info "Loaded environment: ${ENVIRONMENT}"
    elif [ -f ".env" ]; then
        export $(cat .env | grep -v '#' | xargs)
        log_warn "Using default .env file"
    else
        log_error "No environment file found"
        exit 1
    fi
}

backup_data() {
    log_info "Creating backup..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p ${BACKUP_DIR}
    
    # Backup document library
    if [ -d "document_library" ]; then
        tar -czf ${BACKUP_DIR}/document_library.tar.gz document_library/
        log_info "Document library backed up"
    fi
    
    # Backup cache
    if docker volume ls | grep -q "rag-cache"; then
        docker run --rm -v rag-cache:/data -v $(pwd)/${BACKUP_DIR}:/backup alpine tar -czf /backup/cache.tar.gz -C /data .
        log_info "Cache backed up"
    fi
    
    log_info "Backup completed: ${BACKUP_DIR}"
}

pull_images() {
    log_info "Pulling Docker images..."
    
    if [ "${VERSION}" != "latest" ]; then
        export IMAGE_TAG=${VERSION}
    fi
    
    docker-compose -f ${COMPOSE_FILE} pull
}

pre_deploy_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check disk space
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ ${DISK_USAGE} -gt 90 ]; then
        log_error "Disk usage is above 90% (${DISK_USAGE}%)"
        exit 1
    fi
    
    # Check memory
    MEM_AVAILABLE=$(free -m | awk 'NR==2{print $7}')
    if [ ${MEM_AVAILABLE} -lt 512 ]; then
        log_warn "Low memory available: ${MEM_AVAILABLE}MB"
    fi
    
    # Check if required files exist
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "Compose file not found: ${COMPOSE_FILE}"
        exit 1
    fi
    
    log_info "Pre-deployment checks passed"
}

deploy() {
    log_info "Deploying to ${ENVIRONMENT}..."
    
    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose -f ${COMPOSE_FILE} -p ${PROJECT_NAME} down --remove-orphans
    
    # Start new containers
    log_info "Starting new containers..."
    docker-compose -f ${COMPOSE_FILE} -p ${PROJECT_NAME} up -d --remove-orphans
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Health check
    log_info "Running health checks..."
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
        if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
            log_info "Health check passed"
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_warn "Health check failed, retrying (${RETRY_COUNT}/${MAX_RETRIES})..."
        sleep 5
    done
    
    if [ ${RETRY_COUNT} -eq ${MAX_RETRIES} ]; then
        log_error "Health check failed after ${MAX_RETRIES} attempts"
        rollback
        exit 1
    fi
    
    log_info "Deployment completed successfully!"
}

rollback() {
    log_warn "Rolling back deployment..."
    
    docker-compose -f ${COMPOSE_FILE} -p ${PROJECT_NAME} down
    
    # Restore from backup if available
    LATEST_BACKUP=$(ls -td backups/*/ 2>/dev/null | head -1)
    if [ -n "${LATEST_BACKUP}" ]; then
        log_info "Restoring from backup: ${LATEST_BACKUP}"
        # Restore logic here
    fi
    
    log_info "Rollback completed"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Remove old images
    docker image prune -af --filter "until=168h" || true
    
    # Remove old backups (keep last 7 days)
    find backups -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # Clean up Docker volumes
    docker volume prune -f || true
    
    log_info "Cleanup completed"
}

post_deploy() {
    log_info "Running post-deployment tasks..."
    
    # Show container status
    docker-compose -f ${COMPOSE_FILE} -p ${PROJECT_NAME} ps
    
    # Show logs
    log_info "Recent logs:"
    docker-compose -f ${COMPOSE_FILE} -p ${PROJECT_NAME} logs --tail=50
}

# Main execution
main() {
    log_info "Starting deployment to ${ENVIRONMENT} (version: ${VERSION})"
    
    check_dependencies
    load_environment
    backup_data
    pre_deploy_checks
    pull_images
    deploy
    cleanup
    post_deploy
    
    log_info "Deployment finished successfully!"
}

# Handle signals
trap 'log_error "Deployment interrupted"; rollback; exit 1' INT TERM

# Run main
main "$@"
