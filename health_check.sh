#!/bin/bash
#
# RAG Application - Health Check Script
# Usage: ./health_check.sh [service]
# Examples:
#   ./health_check.sh           # Check all services
#   ./health_check.sh app       # Check application only
#   ./health_check.sh nginx     # Check nginx only
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_ok() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Configuration
APP_URL="${APP_URL:-http://localhost:8000}"
NGINX_URL="${NGINX_URL:-http://localhost}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
TIMEOUT=5

# Track overall health
OVERALL_HEALTH=0

# Check application health
check_app() {
    echo "Checking Application..."
    
    if ! curl -sf --max-time ${TIMEOUT} "${APP_URL}/api/health" > /dev/null 2>&1; then
        log_error "Application is not responding"
        return 1
    fi
    
    RESPONSE=$(curl -sf --max-time ${TIMEOUT} "${APP_URL}/api/health" 2>/dev/null)
    
    if echo "${RESPONSE}" | grep -q '"status":"ok"'; then
        log_ok "Application is healthy"
        
        # Extract and display stats
        DOCUMENTS=$(echo "${RESPONSE}" | grep -o '"documents":[0-9]*' | cut -d: -f2)
        CHUNKS=$(echo "${RESPONSE}" | grep -o '"chunks":[0-9]*' | cut -d: -f2)
        echo "  Documents: ${DOCUMENTS:-N/A}"
        echo "  Chunks: ${CHUNKS:-N/A}"
        
        return 0
    else
        log_error "Application returned unexpected response"
        echo "  Response: ${RESPONSE}"
        return 1
    fi
}

# Check Nginx health
check_nginx() {
    echo "Checking Nginx..."
    
    if ! curl -sf --max-time ${TIMEOUT} "${NGINX_URL}" > /dev/null 2>&1; then
        log_error "Nginx is not responding"
        return 1
    fi
    
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${TIMEOUT} "${NGINX_URL}")
    
    if [ "${STATUS}" = "200" ] || [ "${STATUS}" = "301" ] || [ "${STATUS}" = "302" ]; then
        log_ok "Nginx is healthy (HTTP ${STATUS})"
        return 0
    else
        log_error "Nginx returned HTTP ${STATUS}"
        return 1
    fi
}

# Check Prometheus health
check_prometheus() {
    echo "Checking Prometheus..."
    
    if ! curl -sf --max-time ${TIMEOUT} "${PROMETHEUS_URL}/-/healthy" > /dev/null 2>&1; then
        log_warn "Prometheus is not responding (optional)"
        return 0
    fi
    
    log_ok "Prometheus is healthy"
    return 0
}

# Check Docker containers
check_containers() {
    echo "Checking Docker Containers..."
    
    if ! command -v docker &> /dev/null; then
        log_warn "Docker not found, skipping container check"
        return 0
    fi
    
    # Check if containers are running
    RUNNING_CONTAINERS=$(docker ps --filter "name=rag" --format "{{.Names}}" 2>/dev/null | wc -l)
    
    if [ "${RUNNING_CONTAINERS}" -eq 0 ]; then
        log_warn "No RAG containers are running"
        return 0
    fi
    
    log_ok "${RUNNING_CONTAINERS} RAG container(s) running"
    
    # Check container health
    UNHEALTHY=$(docker ps --filter "name=rag" --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null)
    
    if [ -n "${UNHEALTHY}" ]; then
        log_error "Unhealthy containers: ${UNHEALTHY}"
        return 1
    fi
    
    # Check container resource usage
    echo "Container resource usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $(docker ps --filter "name=rag" -q) 2>/dev/null || true
    
    return 0
}

# Check system resources
check_resources() {
    echo "Checking System Resources..."
    
    # Check disk space
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "${DISK_USAGE}" -lt 90 ]; then
        log_ok "Disk usage: ${DISK_USAGE}%"
    else
        log_error "Disk usage is critical: ${DISK_USAGE}%"
        return 1
    fi
    
    # Check memory
    if command -v free &> /dev/null; then
        MEM_AVAILABLE=$(free -m | awk 'NR==2{print $7}')
        if [ "${MEM_AVAILABLE}" -gt 500 ]; then
            log_ok "Available memory: ${MEM_AVAILABLE}MB"
        else
            log_warn "Low memory available: ${MEM_AVAILABLE}MB"
        fi
    fi
    
    # Check load average
    if command -v uptime &> /dev/null; then
        LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
        log_ok "Load average: ${LOAD}"
    fi
    
    return 0
}

# Check logs for errors
check_logs() {
    echo "Checking Recent Logs..."
    
    if command -v docker &> /dev/null; then
        # Check for errors in logs
        ERRORS=$(docker logs --since=5m rag-prod 2>&1 | grep -i "error\|exception\|traceback" | wc -l)
        
        if [ "${ERRORS}" -eq 0 ]; then
            log_ok "No errors in recent logs"
        else
            log_warn "${ERRORS} error(s) found in recent logs"
            echo "Recent errors:"
            docker logs --since=5m rag-prod 2>&1 | grep -i "error\|exception" | tail -5 || true
        fi
    fi
    
    return 0
}

# Main check function
check_all() {
    echo "=========================================="
    echo "RAG Application Health Check"
    echo "=========================================="
    echo
    
    check_app || OVERALL_HEALTH=1
    echo
    
    check_nginx || OVERALL_HEALTH=1
    echo
    
    check_prometheus || true
    echo
    
    check_containers || OVERALL_HEALTH=1
    echo
    
    check_resources || OVERALL_HEALTH=1
    echo
    
    check_logs || true
    echo
    
    echo "=========================================="
    if [ ${OVERALL_HEALTH} -eq 0 ]; then
        echo -e "${GREEN}All checks passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some checks failed!${NC}"
        exit 1
    fi
}

# Run specific check or all
SERVICE=${1:-all}

case "${SERVICE}" in
    app)
        check_app
        ;;
    nginx)
        check_nginx
        ;;
    prometheus)
        check_prometheus
        ;;
    containers)
        check_containers
        ;;
    resources)
        check_resources
        ;;
    logs)
        check_logs
        ;;
    all|*)
        check_all
        ;;
esac
