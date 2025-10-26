#!/bin/bash
# YMERA Platform - Health Check Script
# Performs comprehensive health checks after deployment

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check HTTP endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint")
    
    if [ "$status_code" -eq "$expected_status" ]; then
        log_info "Endpoint $endpoint returned $status_code"
        return 0
    else
        log_error "Endpoint $endpoint returned $status_code (expected $expected_status)"
        return 1
    fi
}

# Main health check
main() {
    echo "Running health checks..."
    
    # Check health endpoint
    if ! check_endpoint "/health" 200; then
        exit 1
    fi
    
    # Check readiness endpoint
    if ! check_endpoint "/ready" 200; then
        exit 1
    fi
    
    # Check liveness endpoint
    if ! check_endpoint "/live" 200; then
        exit 1
    fi
    
    # Check version endpoint
    if ! check_endpoint "/version" 200; then
        exit 1
    fi
    
    # Check metrics endpoint
    if ! check_endpoint "/metrics" 200; then
        exit 1
    fi
    
    echo ""
    log_info "All health checks passed!"
}

main "$@"
