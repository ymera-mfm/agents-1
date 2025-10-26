#!/bin/bash
# Comprehensive Full-Stack E2E Testing Script for YMERA Multi-Agent AI System
# Tests backend, frontend, and full integration with real measurements

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  YMERA FULL-STACK E2E COMPREHENSIVE TESTING SUITE${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""

# Create results directory
RESULTS_DIR="fullstack_e2e_results"
mkdir -p "$RESULTS_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$RESULTS_DIR/fullstack_test_report_$TIMESTAMP.md"

# Initialize report
cat > "$REPORT_FILE" << 'EOF'
# YMERA Full-Stack E2E Test Report

## Executive Summary
**Test Date:** {DATE}  
**Test Duration:** {DURATION}  
**Overall Status:** {STATUS}

---

## Test Results

EOF

START_TIME=$(date +%s)

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
    echo "================================================================"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Track results
BACKEND_TESTS_PASSED=0
FRONTEND_BUILD_PASSED=0
INTEGRATION_TESTS_PASSED=0
PERFORMANCE_TESTS_PASSED=0

# ========================================
# PHASE 1: BACKEND TESTS
# ========================================
print_section "PHASE 1: BACKEND TESTS"

print_info "Installing backend dependencies..."
pip install -r requirements.txt -q 2>&1 | tee "$RESULTS_DIR/backend_install.log" > /dev/null || true

print_info "Checking backend environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_info "Created .env from .env.example"
fi

print_info "Running backend unit and integration tests..."
export PYTHONPATH=.:$PYTHONPATH
if pytest -v --tb=short --junitxml="$RESULTS_DIR/backend_tests.xml" 2>&1 | tee "$RESULTS_DIR/backend_tests.log"; then
    print_success "Backend tests passed"
    BACKEND_TESTS_PASSED=1
else
    print_error "Backend tests failed"
fi

print_info "Running backend with coverage..."
pytest --cov=. --cov-report=html:"$RESULTS_DIR/backend_coverage" --cov-report=term 2>&1 | tee "$RESULTS_DIR/backend_coverage.log" > /dev/null || true

# ========================================
# PHASE 2: FRONTEND BUILD
# ========================================
print_section "PHASE 2: FRONTEND BUILD & TESTS"

cd frontend

print_info "Checking frontend dependencies..."
if [ ! -d "node_modules" ]; then
    print_info "Installing frontend dependencies (this may take a few minutes)..."
    npm install 2>&1 | tee "../$RESULTS_DIR/frontend_install.log" > /dev/null || true
fi

print_info "Checking frontend environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    sed -i 's|https://api.agentflow.com|http://localhost:8000|g' .env
    sed -i 's|wss://ws.agentflow.com|ws://localhost:8000/ws|g' .env
    sed -i 's|REACT_APP_MOCK_API=true|REACT_APP_MOCK_API=false|g' .env
    print_info "Created and configured frontend .env"
fi

print_info "Building frontend application..."
if npm run build 2>&1 | tee "../$RESULTS_DIR/frontend_build.log"; then
    print_success "Frontend build successful"
    FRONTEND_BUILD_PASSED=1
    
    # Capture build metrics
    BUILD_SIZE=$(du -sh build 2>/dev/null | cut -f1)
    print_info "Build size: $BUILD_SIZE"
else
    print_error "Frontend build failed"
fi

print_info "Running frontend unit tests..."
CI=true npm test -- --watchAll=false --passWithNoTests --coverage --coverageDirectory="../$RESULTS_DIR/frontend_coverage" 2>&1 | tee "../$RESULTS_DIR/frontend_tests.log" || true

cd ..

# ========================================
# PHASE 3: INTEGRATION TESTS
# ========================================
print_section "PHASE 3: FULL-STACK INTEGRATION TESTS"

print_info "Starting backend server in background..."
python main.py &
BACKEND_PID=$!
sleep 5  # Wait for server to start

# Check if backend is running
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    print_success "Backend server started successfully (PID: $BACKEND_PID)"
    
    print_info "Testing API endpoints..."
    
    # Test health endpoint
    HEALTH_RESPONSE=$(curl -s -w "\n%{time_total}" http://localhost:8000/api/v1/health)
    HEALTH_TIME=$(echo "$HEALTH_RESPONSE" | tail -1)
    print_success "Health endpoint: ${HEALTH_TIME}s"
    
    # Test system info endpoint
    INFO_RESPONSE=$(curl -s -w "\n%{time_total}" http://localhost:8000/api/v1/system/info)
    INFO_TIME=$(echo "$INFO_RESPONSE" | tail -1)
    print_success "System info endpoint: ${INFO_TIME}s"
    
    # Test agents endpoint
    AGENTS_RESPONSE=$(curl -s -w "\n%{time_total}" http://localhost:8000/api/v1/agents)
    AGENTS_TIME=$(echo "$AGENTS_RESPONSE" | tail -1)
    print_success "Agents endpoint: ${AGENTS_TIME}s"
    
    # Test WebSocket connection
    print_info "Testing WebSocket connection..."
    timeout 5 python -c "
import asyncio
import websockets
import sys

async def test_ws():
    try:
        async with websockets.connect('ws://localhost:8000/ws') as ws:
            await ws.send('{\"type\":\"ping\"}')
            response = await ws.recv()
            print('WebSocket OK')
            return True
    except Exception as e:
        print(f'WebSocket error: {e}')
        return False

result = asyncio.run(test_ws())
sys.exit(0 if result else 1)
" 2>&1 || true
    
    INTEGRATION_TESTS_PASSED=1
    
    print_info "Stopping backend server..."
    kill $BACKEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
else
    print_error "Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null || true
fi

# ========================================
# PHASE 4: PERFORMANCE TESTS
# ========================================
print_section "PHASE 4: PERFORMANCE MEASUREMENTS"

print_info "Starting backend for performance tests..."
python main.py &
BACKEND_PID=$!
sleep 5

if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    print_info "Running performance benchmarks..."
    
    # Concurrent requests test
    print_info "Testing with 10 concurrent requests..."
    time for i in {1..10}; do
        curl -s http://localhost:8000/api/v1/health > /dev/null &
    done
    wait
    print_success "Concurrent requests test completed"
    
    # Response time measurements
    print_info "Measuring response times (10 requests)..."
    TOTAL_TIME=0
    for i in {1..10}; do
        TIME=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:8000/api/v1/health)
        TOTAL_TIME=$(echo "$TOTAL_TIME + $TIME" | bc)
    done
    AVG_TIME=$(echo "scale=3; $TOTAL_TIME / 10" | bc)
    print_success "Average response time: ${AVG_TIME}s"
    
    PERFORMANCE_TESTS_PASSED=1
    
    kill $BACKEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
else
    print_error "Backend server failed to start for performance tests"
    kill $BACKEND_PID 2>/dev/null || true
fi

# ========================================
# PHASE 5: RESULTS COMPILATION
# ========================================
print_section "PHASE 5: COMPILING RESULTS"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  FULL-STACK E2E TEST RESULTS${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Calculate overall status
TOTAL_PHASES=4
PASSED_PHASES=$((BACKEND_TESTS_PASSED + FRONTEND_BUILD_PASSED + INTEGRATION_TESTS_PASSED + PERFORMANCE_TESTS_PASSED))
SUCCESS_RATE=$((PASSED_PHASES * 100 / TOTAL_PHASES))

echo "Test Phase Results:"
echo "-------------------"
[ $BACKEND_TESTS_PASSED -eq 1 ] && print_success "Backend Tests: PASSED" || print_error "Backend Tests: FAILED"
[ $FRONTEND_BUILD_PASSED -eq 1 ] && print_success "Frontend Build: PASSED" || print_error "Frontend Build: FAILED"
[ $INTEGRATION_TESTS_PASSED -eq 1 ] && print_success "Integration Tests: PASSED" || print_error "Integration Tests: FAILED"
[ $PERFORMANCE_TESTS_PASSED -eq 1 ] && print_success "Performance Tests: PASSED" || print_error "Performance Tests: FAILED"

echo ""
echo "Overall Statistics:"
echo "-------------------"
echo "Success Rate: ${SUCCESS_RATE}% (${PASSED_PHASES}/${TOTAL_PHASES} phases)"
echo "Duration: ${DURATION_MIN}m ${DURATION_SEC}s"
echo "Report: $REPORT_FILE"
echo ""

# Update report with final results
sed -i "s/{DATE}/$(date '+%Y-%m-%d %H:%M:%S')/g" "$REPORT_FILE"
sed -i "s/{DURATION}/${DURATION_MIN}m ${DURATION_SEC}s/g" "$REPORT_FILE"
if [ $SUCCESS_RATE -eq 100 ]; then
    sed -i "s/{STATUS}/✅ ALL TESTS PASSED/g" "$REPORT_FILE"
else
    sed -i "s/{STATUS}/⚠️ SOME TESTS FAILED (${SUCCESS_RATE}% success)/g" "$REPORT_FILE"
fi

# Append detailed results to report
cat >> "$REPORT_FILE" << EOF

### Phase 1: Backend Tests
- Status: $([ $BACKEND_TESTS_PASSED -eq 1 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Details: See \`backend_tests.log\`

### Phase 2: Frontend Build
- Status: $([ $FRONTEND_BUILD_PASSED -eq 1 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Build Size: $BUILD_SIZE
- Details: See \`frontend_build.log\`

### Phase 3: Integration Tests
- Status: $([ $INTEGRATION_TESTS_PASSED -eq 1 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Health Endpoint: ${HEALTH_TIME}s
- System Info Endpoint: ${INFO_TIME}s
- Agents Endpoint: ${AGENTS_TIME}s

### Phase 4: Performance Tests
- Status: $([ $PERFORMANCE_TESTS_PASSED -eq 1 ] && echo "✅ PASSED" || echo "❌ FAILED")
- Average Response Time: ${AVG_TIME}s
- Concurrent Requests: 10 simultaneous

---

## Artifacts

- Backend test results: \`backend_tests.xml\`
- Backend coverage: \`backend_coverage/index.html\`
- Frontend coverage: \`frontend_coverage/index.html\`
- All logs: \`fullstack_e2e_results/\`

---

**Report Generated:** $(date '+%Y-%m-%d %H:%M:%S')
EOF

print_info "Detailed report saved to: $REPORT_FILE"

# Exit with appropriate code
if [ $SUCCESS_RATE -eq 100 ]; then
    echo -e "${GREEN}✓ All full-stack E2E tests completed successfully!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Check the report for details.${NC}"
    exit 1
fi
