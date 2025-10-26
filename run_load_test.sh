#!/bin/bash
# Quick Load Test Runner for YMERA API
# This script starts the API server and runs various load tests

set -e

echo "====================================="
echo "YMERA API Load Testing Runner"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_HOST=${API_HOST:-http://localhost:8000}
API_PORT=${API_PORT:-8000}

# Function to check if API is running
check_api() {
    echo -n "Checking if API is running... "
    if curl -s "${API_HOST}/api/v1/health" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}NOT RUNNING${NC}"
        return 1
    fi
}

# Function to start API server
start_api() {
    echo "Starting API server on port ${API_PORT}..."
    python main.py > /tmp/ymera_api.log 2>&1 &
    API_PID=$!
    echo "API server started with PID: ${API_PID}"
    
    # Wait for API to be ready
    echo -n "Waiting for API to be ready"
    for i in {1..30}; do
        if check_api > /dev/null 2>&1; then
            echo -e " ${GREEN}Ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e " ${RED}Failed to start${NC}"
    echo "Check logs at /tmp/ymera_api.log"
    return 1
}

# Function to stop API server
stop_api() {
    if [ ! -z "$API_PID" ]; then
        echo "Stopping API server (PID: ${API_PID})..."
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
    fi
    pkill -f "python main.py" 2>/dev/null || true
    pkill -f "uvicorn main:app" 2>/dev/null || true
}

# Trap to ensure cleanup
trap stop_api EXIT

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${YELLOW}Warning: Locust is not installed${NC}"
    echo "Installing locust..."
    pip install locust==2.31.8
fi

# Main menu
show_menu() {
    echo ""
    echo "Select load test type:"
    echo "1) Quick Test (10 users, 10 seconds)"
    echo "2) Light Test (50 users, 1 minute)"
    echo "3) Medium Test (100 users, 2 minutes)"
    echo "4) Heavy Test (500 users, 5 minutes)"
    echo "5) Stress Test (1000 users, 10 minutes)"
    echo "6) Simple Endpoint Validation"
    echo "7) Web UI Mode"
    echo "8) Custom Test"
    echo "9) Exit"
    echo ""
}

# Run load test
run_load_test() {
    local users=$1
    local spawn_rate=$2
    local run_time=$3
    local test_name=$4
    
    echo ""
    echo -e "${GREEN}Running ${test_name}${NC}"
    echo "Users: ${users}, Spawn Rate: ${spawn_rate}, Duration: ${run_time}"
    echo "====================================="
    
    locust -f locust_api_load_test.py \
        --host="${API_HOST}" \
        --users="${users}" \
        --spawn-rate="${spawn_rate}" \
        --run-time="${run_time}" \
        --headless \
        --html="load_test_${test_name}_$(date +%Y%m%d_%H%M%S).html" \
        --csv="load_test_${test_name}_$(date +%Y%m%d_%H%M%S)"
    
    echo ""
    echo -e "${GREEN}Test completed!${NC}"
    echo "Reports generated in current directory"
}

# Start API if not running
if ! check_api; then
    echo "API is not running. Starting it now..."
    if ! start_api; then
        echo -e "${RED}Failed to start API server${NC}"
        exit 1
    fi
fi

# Main loop
while true; do
    show_menu
    read -p "Enter your choice [1-9]: " choice
    
    case $choice in
        1)
            run_load_test 10 2 "10s" "quick"
            ;;
        2)
            run_load_test 50 5 "1m" "light"
            ;;
        3)
            run_load_test 100 10 "2m" "medium"
            ;;
        4)
            run_load_test 500 50 "5m" "heavy"
            ;;
        5)
            run_load_test 1000 100 "10m" "stress"
            ;;
        6)
            echo ""
            echo -e "${GREEN}Running Simple Endpoint Validation${NC}"
            echo "====================================="
            python test_api_simple.py
            ;;
        7)
            echo ""
            echo -e "${GREEN}Starting Locust Web UI${NC}"
            echo "====================================="
            echo "Open http://localhost:8089 in your browser"
            echo "Press Ctrl+C to stop"
            locust -f locust_api_load_test.py --host="${API_HOST}"
            ;;
        8)
            echo ""
            read -p "Number of users: " users
            read -p "Spawn rate (users/sec): " spawn_rate
            read -p "Run time (e.g., 10s, 1m, 5m): " run_time
            run_load_test "$users" "$spawn_rate" "$run_time" "custom"
            ;;
        9)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please select 1-9${NC}"
            ;;
    esac
done
