#!/bin/bash
# YMERA Platform - Quick Start Script
# Verifies system activation and starts the platform

set -e  # Exit on error

echo "======================================================================"
echo "YMERA PLATFORM - QUICK START"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Detect Python command
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.11 or higher."
    exit 1
fi

# Step 1: Verify Python version
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION detected (using $PYTHON_CMD)"
echo ""

# Step 2: Run activation verification
echo "Step 2: Running integration phase activation check..."
echo "----------------------------------------------------------------------"
if $PYTHON_CMD integration_phase_activation.py; then
    print_success "All integration phases verified"
else
    print_warning "Some phases need attention (see above)"
fi
echo ""

# Step 3: Check configuration
echo "Step 3: Verifying configuration..."
if [ -f ".env" ]; then
    print_success ".env file found"
else
    print_error ".env file not found"
    echo "  Creating .env from .env.example..."
    cp .env.example .env
    print_warning "Please edit .env with your configuration"
    exit 1
fi
echo ""

# Step 4: Verify core modules
echo "Step 4: Testing core modules..."
if $PYTHON_CMD -c "from core.config import Settings; from main import app" 2>/dev/null; then
    print_success "Core modules loaded successfully"
else
    print_error "Core modules failed to load"
    echo "  Run: pip install -r requirements.txt"
    exit 1
fi
echo ""

# Step 5: System ready
echo "======================================================================"
print_success "YMERA PLATFORM IS READY!"
echo "======================================================================"
echo ""
echo "Available Commands:"
echo "  1. Start API Server (Development - localhost only):"
echo "     uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
echo ""
echo "  2. Start API Server (Production - all interfaces):"
echo "     uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  3. Run Tests:"
echo "     pytest tests/ -v"
echo ""
echo "  4. View API Documentation (after starting server):"
echo "     http://localhost:8000/docs"
echo ""
echo "  5. Health Check (after starting server):"
echo "     curl http://localhost:8000/health"
echo ""
echo "  6. Re-run Activation Check:"
echo "     $PYTHON_CMD integration_phase_activation.py"
echo ""
echo "======================================================================"
echo ""

# Ask if user wants to start the server
read -p "Start the API server now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    # Ask for development or production mode
    read -p "Start in development mode (localhost only)? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting YMERA Platform API Server (Development Mode)..."
        echo "Server will be available at: http://localhost:8000"
        echo "Press Ctrl+C to stop"
        echo ""
        uvicorn main:app --host 127.0.0.1 --port 8000 --reload
    else
        print_warning "Starting in production mode - server accessible from all interfaces"
        echo "Server will be available at: http://0.0.0.0:8000"
        echo "Press Ctrl+C to stop"
        echo ""
        uvicorn main:app --host 0.0.0.0 --port 8000
    fi
fi
