#!/bin/bash

###############################################################################
# Performance Benchmark Script
# Runs various performance tests and generates a comprehensive report
###############################################################################

set -e

echo "🚀 Starting Performance Benchmark..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create reports directory
REPORTS_DIR="./performance-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORTS_DIR}/benchmark_${TIMESTAMP}.txt"

mkdir -p "${REPORTS_DIR}"

echo "📊 Report will be saved to: ${REPORT_FILE}"
echo "" | tee "${REPORT_FILE}"

###############################################################################
# 1. Bundle Size Analysis
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 Bundle Size Analysis${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ ! -d "build" ]; then
    echo "Building application for analysis..."
    npm run build > /dev/null 2>&1
fi

echo "Bundle Size Report:" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

# Get main bundle size
MAIN_JS=$(find build/static/js -name "main.*.js" -type f)
if [ -f "$MAIN_JS" ]; then
    MAIN_SIZE=$(wc -c < "$MAIN_JS" | xargs)
    MAIN_SIZE_KB=$((MAIN_SIZE / 1024))
    echo "Main Bundle: ${MAIN_SIZE_KB} KB" | tee -a "${REPORT_FILE}"
    
    if [ "$MAIN_SIZE_KB" -gt 300 ]; then
        echo -e "${RED}⚠️  Warning: Main bundle exceeds 300KB${NC}" | tee -a "${REPORT_FILE}"
    else
        echo -e "${GREEN}✓ Main bundle size is acceptable${NC}" | tee -a "${REPORT_FILE}"
    fi
fi

# Get total JS size
TOTAL_JS_SIZE=$(find build/static/js -name "*.js" -type f -exec wc -c {} + | awk '{s+=$1} END {print s}')
TOTAL_JS_KB=$((TOTAL_JS_SIZE / 1024))
echo "Total JS: ${TOTAL_JS_KB} KB" | tee -a "${REPORT_FILE}"

# Get total CSS size
TOTAL_CSS_SIZE=$(find build/static/css -name "*.css" -type f -exec wc -c {} + 2>/dev/null | awk '{s+=$1} END {print s}')
TOTAL_CSS_KB=$((TOTAL_CSS_SIZE / 1024))
echo "Total CSS: ${TOTAL_CSS_KB} KB" | tee -a "${REPORT_FILE}"

# Total size
TOTAL_SIZE=$((TOTAL_JS_SIZE + TOTAL_CSS_SIZE))
TOTAL_KB=$((TOTAL_SIZE / 1024))
echo "Total Assets: ${TOTAL_KB} KB" | tee -a "${REPORT_FILE}"

echo "" | tee -a "${REPORT_FILE}"

if [ "$TOTAL_KB" -gt 500 ]; then
    echo -e "${RED}⚠️  Warning: Total bundle size exceeds 500KB budget${NC}" | tee -a "${REPORT_FILE}"
else
    echo -e "${GREEN}✓ Total bundle size is within budget${NC}" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"

###############################################################################
# 2. Dependencies Analysis
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📚 Dependencies Analysis${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Dependency Statistics:" | tee -a "${REPORT_FILE}"
PROD_DEPS=$(jq '.dependencies | length' package.json)
DEV_DEPS=$(jq '.devDependencies | length' package.json)
echo "Production Dependencies: ${PROD_DEPS}" | tee -a "${REPORT_FILE}"
echo "Development Dependencies: ${DEV_DEPS}" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

###############################################################################
# 3. Code Quality Checks
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}✨ Code Quality Analysis${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Count lines of code
echo "Lines of Code:" | tee -a "${REPORT_FILE}"
TOTAL_LINES=$(find src -name "*.js" -o -name "*.jsx" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
echo "Total: ${TOTAL_LINES} lines" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

###############################################################################
# 4. Build Performance
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}⚡ Build Performance${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Running build benchmark..." | tee -a "${REPORT_FILE}"
rm -rf build

BUILD_START=$(date +%s)
npm run build > /dev/null 2>&1
BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))

echo "Build Time: ${BUILD_TIME} seconds" | tee -a "${REPORT_FILE}"

if [ "$BUILD_TIME" -gt 120 ]; then
    echo -e "${YELLOW}⚠️  Build time is slower than expected${NC}" | tee -a "${REPORT_FILE}"
else
    echo -e "${GREEN}✓ Build time is acceptable${NC}" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"

###############################################################################
# 5. Recommendations
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}💡 Recommendations${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Performance Recommendations:" | tee -a "${REPORT_FILE}"

# Bundle size recommendations
if [ "$TOTAL_KB" -gt 500 ]; then
    echo "- Reduce bundle size (current: ${TOTAL_KB}KB, target: <500KB)" | tee -a "${REPORT_FILE}"
    echo "  * Remove unused dependencies" | tee -a "${REPORT_FILE}"
    echo "  * Implement code splitting" | tee -a "${REPORT_FILE}"
    echo "  * Use tree shaking" | tee -a "${REPORT_FILE}"
fi

if [ "$MAIN_SIZE_KB" -gt 300 ]; then
    echo "- Split main bundle (current: ${MAIN_SIZE_KB}KB, target: <300KB)" | tee -a "${REPORT_FILE}"
    echo "  * Use React.lazy for route-based splitting" | tee -a "${REPORT_FILE}"
    echo "  * Lazy load heavy libraries" | tee -a "${REPORT_FILE}"
fi

if [ "$BUILD_TIME" -gt 120 ]; then
    echo "- Optimize build time (current: ${BUILD_TIME}s, target: <120s)" | tee -a "${REPORT_FILE}"
    echo "  * Use build caching" | tee -a "${REPORT_FILE}"
    echo "  * Parallelize builds" | tee -a "${REPORT_FILE}"
fi

# Check for common issues
LODASH_IMPORTS=$(grep -r "import.*from 'lodash'" src --include="*.js" --include="*.jsx" | wc -l)
if [ "$LODASH_IMPORTS" -gt 0 ]; then
    echo "- Use lodash-es or specific imports instead of full lodash" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"

###############################################################################
# Summary
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

SCORE=100
ISSUES=0

if [ "$TOTAL_KB" -gt 500 ]; then
    SCORE=$((SCORE - 20))
    ISSUES=$((ISSUES + 1))
fi

if [ "$MAIN_SIZE_KB" -gt 300 ]; then
    SCORE=$((SCORE - 15))
    ISSUES=$((ISSUES + 1))
fi

if [ "$BUILD_TIME" -gt 120 ]; then
    SCORE=$((SCORE - 10))
    ISSUES=$((ISSUES + 1))
fi

echo "Performance Score: ${SCORE}/100" | tee -a "${REPORT_FILE}"
echo "Issues Found: ${ISSUES}" | tee -a "${REPORT_FILE}"
echo "" | tee -a "${REPORT_FILE}"

if [ "$SCORE" -ge 80 ]; then
    echo -e "${GREEN}✓ Performance is good!${NC}" | tee -a "${REPORT_FILE}"
elif [ "$SCORE" -ge 60 ]; then
    echo -e "${YELLOW}⚠️  Performance needs improvement${NC}" | tee -a "${REPORT_FILE}"
else
    echo -e "${RED}❌ Performance needs significant improvement${NC}" | tee -a "${REPORT_FILE}"
fi

echo "" | tee -a "${REPORT_FILE}"
echo -e "${GREEN}✓ Benchmark complete!${NC}"
echo "Full report saved to: ${REPORT_FILE}"
echo ""

# Open report if running interactively
if [ -t 1 ]; then
    read -p "View full report? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat "${REPORT_FILE}"
    fi
fi
