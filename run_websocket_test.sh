#!/bin/bash
# WebSocket Load Testing Runner Script for YMERA

set -e

echo "=========================================="
echo "YMERA WebSocket Load Testing"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    npm install
    echo ""
fi

# Default values
TEST_TYPE="${1:-quick}"
WS_URL="${WS_URL:-ws://localhost:8000/ws}"

echo "Test Type: $TEST_TYPE"
echo "Target URL: $WS_URL"
echo ""

case $TEST_TYPE in
    quick)
        echo -e "${GREEN}Running quick WebSocket stress test (100 connections, 10 messages)${NC}"
        CONNECTIONS=100 MESSAGES=10 WS_URL="$WS_URL" node websocket_stress_test.js
        ;;
    medium)
        echo -e "${GREEN}Running medium WebSocket stress test (500 connections, 20 messages)${NC}"
        CONNECTIONS=500 MESSAGES=20 WS_URL="$WS_URL" node websocket_stress_test.js
        ;;
    heavy)
        echo -e "${GREEN}Running heavy WebSocket stress test (1000 connections, 50 messages)${NC}"
        CONNECTIONS=1000 MESSAGES=50 WS_URL="$WS_URL" node websocket_stress_test.js
        ;;
    artillery-quick)
        echo -e "${GREEN}Running quick Artillery test (localhost)${NC}"
        npx artillery run -e localhost artillery_websocket.yml
        ;;
    artillery-staging)
        echo -e "${GREEN}Running full Artillery test (staging)${NC}"
        npx artillery run -e staging artillery_websocket.yml
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: $0 [TEST_TYPE]"
        echo ""
        echo "Available test types:"
        echo "  quick              - Quick stress test (100 connections, 10 messages)"
        echo "  medium             - Medium stress test (500 connections, 20 messages)"
        echo "  heavy              - Heavy stress test (1000 connections, 50 messages)"
        echo "  artillery-quick    - Quick Artillery test (localhost)"
        echo "  artillery-staging  - Full Artillery test (staging)"
        echo ""
        echo "Environment variables:"
        echo "  WS_URL             - WebSocket URL (default: ws://localhost:8000/ws)"
        echo "  CONNECTIONS        - Number of connections (for stress tests)"
        echo "  MESSAGES           - Messages per connection (for stress tests)"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Test completed!${NC}"
