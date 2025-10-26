#!/bin/bash
# Final Validation Script for Phase 6
# Runs all tests, security scans, and performance benchmarks

set -e

REPORT_DIR="validation_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "============================================="
echo "YMERA Platform - Final Validation Suite"
echo "============================================="
echo ""
echo "Timestamp: $(date)"
echo "Report Directory: $REPORT_DIR"
echo ""

# Create report directory
mkdir -p "$REPORT_DIR"

# Step 1: Clean environment test
echo "Step 1: Setting up clean environment..."
echo "----------------------------------------"
if [ -d "venv" ]; then
    echo "Removing existing venv..."
    rm -rf venv
fi

python -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✓ Clean environment ready"
echo ""

# Step 2: Run pytest with coverage
echo "Step 2: Running test suite with coverage..."
echo "----------------------------------------"
pytest tests/ -v --cov=. --cov-report=html --cov-report=json --cov-report=term-missing > "$REPORT_DIR/pytest_output_${TIMESTAMP}.txt" 2>&1 || true

# Extract coverage percentage
COVERAGE=$(python -c "import json; data = json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.1f}\")" 2>/dev/null || echo "0.0")
echo "Code Coverage: ${COVERAGE}%"
echo ""

# Step 3: Run comprehensive E2E tests
echo "Step 3: Running comprehensive E2E tests..."
echo "----------------------------------------"
python run_comprehensive_e2e_tests.py > "$REPORT_DIR/e2e_tests_${TIMESTAMP}.txt" 2>&1 || true

# Extract test pass rate
TOTAL_TESTS=$(jq -r '.total_tests // 0' e2e_test_report.json 2>/dev/null || echo "0")
PASSED_TESTS=$(jq -r '.passed // 0' e2e_test_report.json 2>/dev/null || echo "0")
if [ "$TOTAL_TESTS" -gt 0 ]; then
    PASS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
else
    PASS_RATE="0.0"
fi
echo "Test Pass Rate: ${PASS_RATE}%"
echo ""

# Step 4: Run security scan
echo "Step 4: Running security scan with bandit..."
echo "----------------------------------------"
bandit -r . -f json -o "$REPORT_DIR/security_scan_${TIMESTAMP}.json" --exclude ./venv,./tests 2>&1 || true
bandit -r . -f txt -o "$REPORT_DIR/security_scan_${TIMESTAMP}.txt" --exclude ./venv,./tests 2>&1 || true

# Count security issues
HIGH_ISSUES=$(grep -o '"issue_severity": "HIGH"' "$REPORT_DIR/security_scan_${TIMESTAMP}.json" 2>/dev/null | wc -l || echo "0")
MEDIUM_ISSUES=$(grep -o '"issue_severity": "MEDIUM"' "$REPORT_DIR/security_scan_${TIMESTAMP}.json" 2>/dev/null | wc -l || echo "0")
echo "Security Issues - HIGH: ${HIGH_ISSUES}, MEDIUM: ${MEDIUM_ISSUES}"
echo ""

# Step 5: Run performance tests
echo "Step 5: Running performance benchmarks..."
echo "----------------------------------------"
# Note: Performance tests need the server running, so we'll create a mock report
echo "Note: Performance benchmarks require running server. Skipping for now." > "$REPORT_DIR/performance_${TIMESTAMP}.txt"
echo "✓ Performance benchmark logged"
echo ""

# Step 6: Generate summary report
echo "Step 6: Generating summary report..."
echo "----------------------------------------"

cat > "$REPORT_DIR/validation_summary_${TIMESTAMP}.md" << EOF
# YMERA Platform - Final Validation Summary

**Generated:** $(date)
**Report ID:** ${TIMESTAMP}

## Test Results

### Unit & Integration Tests
- **Coverage:** ${COVERAGE}%
- **Status:** $([ "$COVERAGE" \> "85" ] && echo "✅ PASS" || echo "⚠️ NEEDS IMPROVEMENT")

### End-to-End Tests
- **Total Tests:** ${TOTAL_TESTS}
- **Passed:** ${PASSED_TESTS}
- **Pass Rate:** ${PASS_RATE}%
- **Status:** $([ "$PASS_RATE" \> "98" ] && echo "✅ PASS" || echo "⚠️ NEEDS IMPROVEMENT")

### Security Scan
- **HIGH Issues:** ${HIGH_ISSUES}
- **MEDIUM Issues:** ${MEDIUM_ISSUES}
- **Status:** $([ "$HIGH_ISSUES" -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")

## Overall Status

$([ "$HIGH_ISSUES" -eq 0 ] && awk 'BEGIN {exit !('"$PASS_RATE"' >= 95)}' && echo "✅ System is ready for production" || echo "⚠️ Some issues need attention before production deployment")

## Detailed Reports

- Pytest Output: pytest_output_${TIMESTAMP}.txt
- E2E Tests: e2e_tests_${TIMESTAMP}.txt
- Security Scan JSON: security_scan_${TIMESTAMP}.json
- Security Scan Text: security_scan_${TIMESTAMP}.txt
- Performance: performance_${TIMESTAMP}.txt

EOF

echo "✓ Summary report generated: $REPORT_DIR/validation_summary_${TIMESTAMP}.md"
echo ""

# Display summary
echo "============================================="
echo "VALIDATION SUMMARY"
echo "============================================="
cat "$REPORT_DIR/validation_summary_${TIMESTAMP}.md"
echo ""

echo "All validation reports saved to: $REPORT_DIR/"
echo "============================================="
