#!/bin/bash

# Pre-deployment validation script
# Ensures all requirements are met before deploying to production

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Pre-Deployment Validation"
echo "============================"

ERRORS=0
WARNINGS=0

# Function to check requirement
check_requirement() {
    local name=$1
    local check=$2
    local required=$3
    
    echo -n "Checking $name... "
    
    if eval "$check"; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗ FAIL (Required)${NC}"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠ WARNING${NC}"
            ((WARNINGS++))
        fi
        return 1
    fi
}

echo ""
echo "Environment Checks:"
echo "------------------"

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2)
check_requirement "Node.js version >= 18" "[ $(echo $NODE_VERSION | cut -d'.' -f1) -ge 18 ]" true

# Check npm version
NPM_VERSION=$(npm -v | cut -d'.' -f1)
check_requirement "npm version >= 8" "[ $NPM_VERSION -ge 8 ]" true

# Check environment variables
check_requirement "REACT_APP_API_URL set" "[ ! -z \"$REACT_APP_API_URL\" ]" true
check_requirement "REACT_APP_WS_URL set" "[ ! -z \"$REACT_APP_WS_URL\" ]" true

echo ""
echo "Code Quality Checks:"
echo "-------------------"

# Run linter
check_requirement "ESLint passes" "npm run lint" true

# Run prettier check
check_requirement "Code formatting valid" "npm run format:check" true

# Security audit
check_requirement "No critical vulnerabilities" "npm audit --audit-level=critical" false

echo ""
echo "Test Checks:"
echo "-----------"

# Run tests
check_requirement "Unit tests pass" "npm run test:coverage -- --watchAll=false" true

# Check test coverage
COVERAGE=$(cat coverage/coverage-summary.json 2>/dev/null | grep -o '"lines":{[^}]*}' | grep -o '"pct":[0-9.]*' | cut -d':' -f2 | head -1)
if [ ! -z "$COVERAGE" ]; then
    check_requirement "Test coverage >= 70%" "[ $(echo \"$COVERAGE >= 70\" | bc) -eq 1 ]" true
fi

echo ""
echo "Build Checks:"
echo "------------"

# Check if build succeeds
check_requirement "Production build succeeds" "npm run build:prod" true

# Check build size
if [ -d "build" ]; then
    BUILD_SIZE=$(du -sm build | cut -f1)
    check_requirement "Build size < 10MB" "[ $BUILD_SIZE -lt 10 ]" false
fi

echo ""
echo "Configuration Checks:"
echo "--------------------"

# Check .env.production exists
check_requirement ".env.production exists" "[ -f .env.production ]" true

# Check Docker configuration
check_requirement "Dockerfile exists" "[ -f Dockerfile ]" true
check_requirement "docker-compose.prod.yml exists" "[ -f docker-compose.prod.yml ]" true

# Check nginx configuration
check_requirement "nginx config exists" "[ -f nginx/nginx.conf ]" true

echo ""
echo "Documentation Checks:"
echo "--------------------"

# Check documentation
check_requirement "README.md exists" "[ -f README.md ]" true
check_requirement "DEPLOYMENT.md exists" "[ -f DEPLOYMENT.md ]" false
check_requirement "CHANGELOG.md exists" "[ -f CHANGELOG.md ]" false

echo ""
echo "Security Checks:"
echo "---------------"

# Check for secrets in code
if command -v git &> /dev/null; then
    check_requirement "No secrets in git" "! git grep -i 'password\\|secret\\|api_key' -- '*.js' '*.jsx' '*.ts' '*.tsx'" false
fi

# Check HTTPS configuration
if [ -f ".env.production" ]; then
    check_requirement "HTTPS enabled" "grep -q 'REACT_APP_ENABLE_HTTPS_ONLY=true' .env.production" true
fi

echo ""
echo "Performance Checks:"
echo "------------------"

# Check bundle size
if [ -d "build/static/js" ]; then
    MAX_JS=$(find build/static/js -name "*.js" -not -name "*.map" -exec du -k {} \; | sort -n | tail -1 | cut -f1)
    check_requirement "Largest JS bundle < 500KB" "[ $MAX_JS -lt 500 ]" false
fi

echo ""
echo "============================"
echo "Validation Summary:"
echo "------------------"
echo -e "Errors: $ERRORS"
echo -e "Warnings: $WARNINGS"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Validation passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ Validation failed! Fix $ERRORS error(s) before deploying.${NC}"
    exit 1
fi
