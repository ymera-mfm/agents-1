#!/bin/bash

# Post-Deployment Verification Script
# Comprehensive checks after deployment to production

set -e

echo "=========================================="
echo "Post-Deployment Verification"
echo "=========================================="
echo ""

# Configuration
DEPLOYMENT_URL="${1:-https://yourdomain.com}"
API_URL="${REACT_APP_API_URL:-https://api.yourdomain.com}"
EXPECTED_VERSION="${REACT_APP_VERSION:-1.0.0}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Results tracking
declare -a PASSED_CHECKS=()
declare -a FAILED_CHECKS=()
declare -a WARNING_CHECKS=()

# Helper function
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED_CHECKS+=("$1")
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    FAILED_CHECKS+=("$1")
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNING_CHECKS+=("$1")
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

section() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Section 1: Application Accessibility
section "1. Application Accessibility"

info "Checking: $DEPLOYMENT_URL"

# Check if application is accessible
if curl -f -s -o /dev/null -w '%{http_code}' --max-time 30 "$DEPLOYMENT_URL" | grep -q "200"; then
    check_pass "Application is accessible (HTTP 200)"
else
    check_fail "Application is not accessible"
fi

# Check SSL if HTTPS
if [[ $DEPLOYMENT_URL == https://* ]]; then
    DOMAIN=$(echo $DEPLOYMENT_URL | sed 's,https://,,;s,/.*,,')
    
    if echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | grep -q 'Verify return code: 0'; then
        check_pass "SSL certificate is valid"
        
        # Check SSL expiration
        expiry_date=$(echo | openssl s_client -connect $DOMAIN:443 -servername $DOMAIN 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
        expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$expiry_date" +%s 2>/dev/null)
        current_epoch=$(date +%s)
        days_until_expiry=$(( ($expiry_epoch - $current_epoch) / 86400 ))
        
        if [ $days_until_expiry -gt 30 ]; then
            check_pass "SSL certificate valid for $days_until_expiry days"
        else
            check_warn "SSL certificate expires in $days_until_expiry days"
        fi
    else
        check_fail "SSL certificate is invalid or not trusted"
    fi
fi

# Section 2: Security Headers
section "2. Security Headers"

headers=$(curl -s -I --max-time 30 "$DEPLOYMENT_URL")

if echo "$headers" | grep -iq "X-Content-Type-Options"; then
    check_pass "X-Content-Type-Options header present"
else
    check_warn "X-Content-Type-Options header missing"
fi

if echo "$headers" | grep -iq "X-Frame-Options\|Content-Security-Policy"; then
    check_pass "Clickjacking protection header present"
else
    check_warn "X-Frame-Options or CSP header missing"
fi

if echo "$headers" | grep -iq "Strict-Transport-Security"; then
    check_pass "HSTS header present"
else
    check_warn "Strict-Transport-Security header missing"
fi

# Section 3: Application Content
section "3. Application Content"

content=$(curl -s --max-time 30 "$DEPLOYMENT_URL")

if echo "$content" | grep -q "root"; then
    check_pass "React root element present"
else
    check_fail "React root element missing"
fi

if echo "$content" | grep -q "static/js"; then
    check_pass "JavaScript bundle referenced"
else
    check_fail "JavaScript bundle not found"
fi

if echo "$content" | grep -q "static/css"; then
    check_pass "CSS bundle referenced"
else
    check_warn "CSS bundle not found"
fi

# Section 4: Static Assets
section "4. Static Assets"

if curl -f -s -o /dev/null --max-time 30 "$DEPLOYMENT_URL/favicon.ico"; then
    check_pass "Favicon accessible"
else
    check_warn "Favicon not found"
fi

if curl -f -s -o /dev/null --max-time 30 "$DEPLOYMENT_URL/manifest.json"; then
    check_pass "PWA manifest accessible"
else
    check_warn "PWA manifest not found"
fi

if curl -f -s -o /dev/null --max-time 30 "$DEPLOYMENT_URL/robots.txt"; then
    check_pass "robots.txt accessible"
else
    check_warn "robots.txt not found"
fi

# Section 5: Performance Check
section "5. Performance"

response_time=$(curl -o /dev/null -s -w '%{time_total}' --max-time 30 "$DEPLOYMENT_URL")

if (( $(echo "$response_time < 3.0" | bc -l) )); then
    check_pass "Page load time: ${response_time}s (< 3s target)"
elif (( $(echo "$response_time < 5.0" | bc -l) )); then
    check_warn "Page load time: ${response_time}s (3-5s, could be better)"
else
    check_fail "Page load time: ${response_time}s (> 5s, too slow)"
fi

# Section 6: API Health Check
section "6. API Health Check"

if curl -f -s -o /dev/null --max-time 30 "$API_URL/health" 2>/dev/null; then
    check_pass "API health endpoint responding"
else
    check_warn "API health endpoint not accessible (this may be expected)"
fi

# Section 7: Console Errors Check
section "7. JavaScript Console Check"

info "Note: Manual verification recommended for console errors"
check_warn "Please manually verify no console errors in browser DevTools"

# Section 8: Critical Paths
section "8. Critical User Paths"

info "Automated checks complete. Manual verification needed for:"
echo "  - User can access homepage"
echo "  - User can navigate to login page"
echo "  - User can login (if applicable)"
echo "  - Dashboard loads after login"
echo "  - Navigation works correctly"
echo "  - Mobile view is responsive"

# Final Summary
section "Verification Summary"

echo ""
echo -e "${GREEN}Passed Checks: ${#PASSED_CHECKS[@]}${NC}"
for check in "${PASSED_CHECKS[@]}"; do
    echo "  ✓ $check"
done

if [ ${#WARNING_CHECKS[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Warnings: ${#WARNING_CHECKS[@]}${NC}"
    for check in "${WARNING_CHECKS[@]}"; do
        echo "  ⚠ $check"
    done
fi

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed Checks: ${#FAILED_CHECKS[@]}${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  ✗ $check"
    done
fi

echo ""
echo "=========================================="

# Exit code based on failures
if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    echo -e "${RED}Deployment verification completed with failures${NC}"
    echo "Please investigate and resolve failed checks."
    exit 1
elif [ ${#WARNING_CHECKS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Deployment verification completed with warnings${NC}"
    echo "Review warnings and consider improvements."
    exit 0
else
    echo -e "${GREEN}Deployment verification completed successfully!${NC}"
    exit 0
fi
