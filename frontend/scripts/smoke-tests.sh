#!/bin/bash

# Smoke Tests for Production Deployment
# Run critical path tests to verify deployment success

set -e

echo "======================================"
echo "Running Production Smoke Tests"
echo "======================================"
echo ""

# Configuration
BASE_URL="${PLAYWRIGHT_BASE_URL:-https://yourdomain.com}"
TIMEOUT=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "Target URL: $BASE_URL"
echo ""

# Test 1: Homepage accessibility
run_test "Homepage loads (HTTP 200)" \
    "curl -f -s -o /dev/null -w '%{http_code}' --max-time $TIMEOUT $BASE_URL | grep -q 200"

# Test 2: Homepage contains expected content
run_test "Homepage contains application title" \
    "curl -s --max-time $TIMEOUT $BASE_URL | grep -q 'AgentFlow'"

# Test 3: Static assets loading
run_test "JavaScript bundle loads" \
    "curl -f -s -o /dev/null --max-time $TIMEOUT $BASE_URL/static/js/"

run_test "CSS bundle loads" \
    "curl -f -s -o /dev/null --max-time $TIMEOUT $BASE_URL/static/css/"

# Test 4: SSL certificate validity
if [[ $BASE_URL == https://* ]]; then
    run_test "SSL certificate is valid" \
        "echo | openssl s_client -connect $(echo $BASE_URL | sed 's,https://,,;s,/.*,,'):443 -servername $(echo $BASE_URL | sed 's,https://,,;s,/.*,,') 2>/dev/null | grep -q 'Verify return code: 0'"
fi

# Test 5: Security headers
run_test "Security headers present (X-Content-Type-Options)" \
    "curl -s -I --max-time $TIMEOUT $BASE_URL | grep -q 'X-Content-Type-Options'"

run_test "Security headers present (X-Frame-Options)" \
    "curl -s -I --max-time $TIMEOUT $BASE_URL | grep -q 'X-Frame-Options'"

# Test 6: API health check (if available)
if curl -f -s -o /dev/null --max-time $TIMEOUT "${REACT_APP_API_URL:-https://api.yourdomain.com}/health" 2>/dev/null; then
    run_test "API health endpoint responds" \
        "curl -f -s -o /dev/null --max-time $TIMEOUT ${REACT_APP_API_URL:-https://api.yourdomain.com}/health"
else
    echo -e "${YELLOW}Skipping API health check (endpoint not available)${NC}"
fi

# Test 7: Response time check
response_time=$(curl -o /dev/null -s -w '%{time_total}' --max-time $TIMEOUT $BASE_URL)
if (( $(echo "$response_time < 5.0" | bc -l) )); then
    echo -e "Testing: Page load time < 5s... ${GREEN}✓ PASS${NC} (${response_time}s)"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "Testing: Page load time < 5s... ${RED}✗ FAIL${NC} (${response_time}s)"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 8: Manifest file
run_test "PWA manifest present" \
    "curl -f -s -o /dev/null --max-time $TIMEOUT $BASE_URL/manifest.json"

# Test 9: Robots.txt
run_test "Robots.txt present" \
    "curl -f -s -o /dev/null --max-time $TIMEOUT $BASE_URL/robots.txt"

# Test 10: Favicon
run_test "Favicon present" \
    "curl -f -s -o /dev/null --max-time $TIMEOUT $BASE_URL/favicon.ico"

echo ""
echo "======================================"
echo "Smoke Test Results"
echo "======================================"
echo "Total Tests: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    echo "Deployment verification successful."
    exit 0
else
    echo -e "${RED}✗ Some smoke tests failed!${NC}"
    echo "Please investigate failures before proceeding."
    exit 1
fi
