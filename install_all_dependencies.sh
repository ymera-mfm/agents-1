#!/bin/bash
# Install All Dependencies for YMERA Performance Analysis
# This script installs all required dependencies from requirements.txt

set -e  # Exit on error

echo "=========================================================================="
echo "YMERA Dependency Installation"
echo "=========================================================================="
echo ""
echo "This script will install all dependencies required for:"
echo "  - Core agent functionality"
echo "  - AI/ML operations (OpenAI, Anthropic, Transformers, etc.)"
echo "  - NLP & Document processing"
echo "  - Vector databases & cloud services"
echo "  - Integration tools"
echo "  - Performance benchmarking"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"
echo ""

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found!"
    echo "Please run this script from the repository root directory."
    exit 1
fi

echo "Installing dependencies from requirements.txt..."
echo ""

# Install dependencies
pip3 install -r requirements.txt --upgrade

echo ""
echo "=========================================================================="
echo "✅ Installation Complete!"
echo "=========================================================================="
echo ""
echo "Verifying installation..."
python3 dependency_checker.py check

echo ""
echo "To run performance analysis:"
echo "  1. python3 run_comprehensive_benchmarks.py --iterations 100 --operations"
echo "  2. python3 load_testing_framework.py --requests 100 --workers 10"
echo "  3. python3 enhanced_report_generator.py"
echo ""
echo "For more information, see PERFORMANCE_ANALYSIS_GUIDE.md"
echo "=========================================================================="
