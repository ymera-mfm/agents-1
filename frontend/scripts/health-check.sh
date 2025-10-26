#!/bin/bash

# Health Check Script for AgentFlow
# This script performs comprehensive health checks on the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_URL="${APP_URL:-http://localhost:3000}"
API_URL="${API_URL:-http://localhost:3001}"
TIMEOUT=5

echo "🏥 AgentFlow Health Check"
echo "=========================="

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name... "
    
    if curl -sf --max-time $TIMEOUT "$url" > /dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to check service
check_service() {
    local name=$1
    local command=$2
    
    echo -n "Checking $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Track failures
FAILURES=0

# Check application endpoint
if ! check_endpoint "$APP_URL" "Application"; then
    ((FAILURES++))
fi

# Check API endpoint
if ! check_endpoint "$API_URL/health" "API Health"; then
    ((FAILURES++))
fi

# Check dependencies
echo ""
echo "Dependency Checks:"
echo "-----------------"

# Node.js
if ! check_service "Node.js" "node --version"; then
    ((FAILURES++))
fi

# npm
if ! check_service "npm" "npm --version"; then
    ((FAILURES++))
fi

# Docker (optional)
check_service "Docker" "docker --version" || true

# Check disk space
echo ""
echo "System Checks:"
echo "-------------"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
echo -n "Disk usage: $DISK_USAGE%... "
if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ WARNING${NC}"
fi

# Check memory
MEMORY_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
echo -n "Memory usage: $MEMORY_USAGE%... "
if [ "$MEMORY_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ WARNING${NC}"
fi

# Check application logs for errors
echo ""
echo "Log Checks:"
echo "----------"
if [ -f "logs/error.log" ]; then
    ERROR_COUNT=$(wc -l < logs/error.log)
    echo -n "Error log entries: $ERROR_COUNT... "
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${YELLOW}⚠ $ERROR_COUNT errors found${NC}"
    fi
else
    echo "No error log found"
fi

# Performance checks
echo ""
echo "Performance Checks:"
echo "------------------"

# Check response time
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}\n' "$APP_URL")
echo -n "Response time: ${RESPONSE_TIME}s... "
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ SLOW${NC}"
fi

# Summary
echo ""
echo "=========================="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILURES check(s) failed${NC}"
    exit 1
fi
