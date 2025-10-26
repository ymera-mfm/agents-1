#!/bin/bash

# Template System Validation Script
# Validates all templates and configurations across the system

set -e

echo "🔍 Starting Template System Validation..."
echo "==========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# Check if directory exists
check_dir() {
    if [ -d "$1" ]; then
        success "Directory exists: $1"
    else
        error "Directory missing: $1"
    fi
}

# Check if file exists
check_file() {
    if [ -f "$1" ]; then
        success "File exists: $1"
    else
        error "File missing: $1"
    fi
}

# Validate YAML file
validate_yaml() {
    if [ -f "$1" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('$1'))" 2>/dev/null; then
            success "YAML valid: $1"
        else
            error "YAML invalid: $1"
        fi
    fi
}

echo "1️⃣  Checking GitHub directory structure..."
echo "-------------------------------------------"
check_dir ".github"
check_dir ".github/ISSUE_TEMPLATE"
check_dir ".github/workflows"
echo ""

echo "2️⃣  Checking Issue Templates..."
echo "-------------------------------------------"
check_file ".github/ISSUE_TEMPLATE/bug_report.md"
check_file ".github/ISSUE_TEMPLATE/bug-fix-request.yml"
check_file ".github/ISSUE_TEMPLATE/feature_request.md"
check_file ".github/ISSUE_TEMPLATE/feature-request-enhanced.yml"
check_file ".github/ISSUE_TEMPLATE/system-analysis.yml"
check_file ".github/ISSUE_TEMPLATE/security-vulnerability.yml"
check_file ".github/ISSUE_TEMPLATE/code-refactoring.yml"
check_file ".github/ISSUE_TEMPLATE/performance-optimization.yml"
check_file ".github/ISSUE_TEMPLATE/config.yml"
check_file ".github/ISSUE_TEMPLATE/custom.md"
check_file ".github/ISSUE_TEMPLATE/README.md"
echo ""

echo "3️⃣  Validating Issue Template YAML Syntax..."
echo "-------------------------------------------"
for file in .github/ISSUE_TEMPLATE/*.yml; do
    validate_yaml "$file"
done
echo ""

echo "4️⃣  Checking Pull Request Template..."
echo "-------------------------------------------"
check_file ".github/PULL_REQUEST_TEMPLATE.md"
echo ""

echo "5️⃣  Checking GitHub Actions Workflows..."
echo "-------------------------------------------"
check_file ".github/workflows/ci.yml"
check_file ".github/workflows/e2e.yml"
check_file ".github/workflows/deploy.yml"
check_file ".github/workflows/dependency-updates.yml"
check_file ".github/workflows/code-quality.yml"
echo ""

echo "6️⃣  Validating Workflow YAML Syntax..."
echo "-------------------------------------------"
for file in .github/workflows/*.yml; do
    validate_yaml "$file"
done
echo ""

echo "7️⃣  Checking Documentation..."
echo "-------------------------------------------"
check_file "docs/TEMPLATE_IMPLEMENTATION_GUIDE.md"
check_file "docs/SYSTEM_ANALYSIS_TEMPLATE_GUIDE.md"
check_file "docs/BUG_FIX_TEMPLATE_GUIDE.md"
check_file "docs/FEATURE_REQUEST_TEMPLATE_GUIDE.md"
check_file "docs/GITHUB_TEMPLATES_GUIDE.md"
check_file "CONTRIBUTING.md"
check_file "README.md"
echo ""

echo "8️⃣  Checking Source Code Issues..."
echo "-------------------------------------------"
if npm run lint > /dev/null 2>&1; then
    success "ESLint: No errors found"
else
    error "ESLint: Errors detected"
fi

if npm run format:check > /dev/null 2>&1; then
    success "Prettier: Code is properly formatted"
else
    warning "Prettier: Code formatting issues detected"
fi
echo ""

echo "9️⃣  Checking for Build Issues..."
echo "-------------------------------------------"
if [ -d "build" ]; then
    success "Build directory exists (previous build successful)"
else
    warning "Build directory not found (build may be needed)"
fi
echo ""

echo "🔟  Checking Configuration Files..."
echo "-------------------------------------------"
check_file "package.json"
check_file ".eslintrc.json"
check_file ".prettierrc"
check_file "tailwind.config.js"
if [ -f "tsconfig.json" ]; then
    success "File exists: tsconfig.json"
else
    warning "TypeScript config not found (may not be needed for JS-only project)"
fi
echo ""

echo "==========================================="
echo "📊 Validation Summary"
echo "==========================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Template system is fully implemented and validated.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Template system is complete with ${WARNINGS} warnings.${NC}"
    exit 0
else
    echo -e "${RED}❌ Found ${ERRORS} errors and ${WARNINGS} warnings.${NC}"
    echo "Please fix the errors before proceeding."
    exit 1
fi
