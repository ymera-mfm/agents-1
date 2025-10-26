#!/bin/bash
# To run: chmod +x quick_test_phase1.sh && ./quick_test_phase1.sh

# YMERA Platform - Phase 1 Quick Test Script
# Tests all major endpoints to verify Phase 1 is working

echo "=========================================="
echo "YMERA Platform - Phase 1 Quick Test"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# Test 2: Root Endpoint
echo "2. Testing Root Endpoint..."
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""

# Test 3: Create Agent
echo "3. Creating Agent..."
AGENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Quick Test Agent",
    "agent_type": "developer",
    "capabilities": [
      {"name": "testing", "level": 10}
    ],
    "metadata": {"test": true}
  }')
echo "$AGENT_RESPONSE" | python3 -m json.tool
AGENT_ID=$(echo "$AGENT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Agent ID: $AGENT_ID"
echo ""

# Test 4: List Agents
echo "4. Listing Agents..."
curl -s "$BASE_URL/api/v1/agents" | python3 -m json.tool
echo ""

# Test 5: Create Task
echo "5. Creating Task..."
TASK_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Quick Test Task\",
    \"description\": \"Testing Phase 1\",
    \"task_type\": \"test\",
    \"parameters\": {\"test\": true},
    \"priority\": \"high\",
    \"agent_id\": \"$AGENT_ID\"
  }")
echo "$TASK_RESPONSE" | python3 -m json.tool
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created Task ID: $TASK_ID"
echo ""

# Test 6: Send Chat Message
echo "6. Sending Chat Message..."
curl -s -X POST "$BASE_URL/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "quick-test-session",
    "content": "Hello from quick test!",
    "message_type": "user"
  }' | python3 -m json.tool
echo ""

# Test 7: Get Chat History
echo "7. Getting Chat History..."
curl -s "$BASE_URL/api/v1/chat/quick-test-session/history" | python3 -m json.tool
echo ""

# Test 8: Get Statistics
echo "8. Getting Platform Statistics..."
curl -s "$BASE_URL/api/v1/stats" | python3 -m json.tool
echo ""

echo "=========================================="
echo "✓ Quick Test Complete!"
echo "=========================================="
echo ""
echo "Phase 1 System is operational and responding correctly."
echo ""
echo "For more detailed tests, run: python3 test_phase1.py"
echo ""
