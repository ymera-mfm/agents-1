# WebSocket Load Testing Guide

This guide explains how to use the WebSocket load testing infrastructure for the YMERA platform.

## Overview

The YMERA WebSocket load testing suite includes:

1. **Artillery-based tests**: Industry-standard load testing with configurable phases
2. **Standalone stress tests**: Custom Node.js script for focused stress testing
3. **Automated scripts**: Easy-to-use shell scripts for common test scenarios

## Prerequisites

### Required Software
- Node.js (v14 or higher)
- npm (comes with Node.js)
- Python 3.8+ (for running the YMERA backend)

### Installation

```bash
# Install Node.js dependencies
npm install

# This will install:
# - ws: WebSocket client library
# - artillery: Professional load testing framework
```

## Quick Start

### 1. Start the YMERA Backend

```bash
# In one terminal, start the backend server
python main.py
```

The backend will start on `http://localhost:8000` with WebSocket endpoint at `/ws`.

### 2. Run a Quick Test

```bash
# Linux/Mac
./run_websocket_test.sh quick

# Windows
run_websocket_test.bat quick
```

## Test Types

### Standalone Stress Tests

These tests create multiple WebSocket connections and send messages concurrently.

#### Quick Test (100 connections, 10 messages each)
```bash
# Linux/Mac
./run_websocket_test.sh quick

# Windows
run_websocket_test.bat quick

# Or directly with Node.js
CONNECTIONS=100 MESSAGES=10 node websocket_stress_test.js
```

#### Medium Test (500 connections, 20 messages each)
```bash
./run_websocket_test.sh medium
```

#### Heavy Test (1000 connections, 50 messages each)
```bash
./run_websocket_test.sh heavy
```

#### Custom Test
```bash
# Set custom parameters
CONNECTIONS=250 MESSAGES=30 WS_URL=ws://localhost:8000/ws node websocket_stress_test.js
```

### Artillery Load Tests

Artillery provides sophisticated load testing with multiple phases.

#### Quick Artillery Test (Local Development)
```bash
./run_websocket_test.sh artillery-quick

# Or directly with Artillery
npx artillery run -e localhost artillery_websocket.yml
```

This runs a quick 10-second test with 5→20 users for rapid validation.

#### Full Artillery Test (Staging/Production)
```bash
./run_websocket_test.sh artillery-staging

# Or for custom target
artillery run -e staging artillery_websocket.yml
```

The full test includes multiple phases:
1. **Warm-up** (60s): 10 → 100 users/sec
2. **Ramp-up** (300s): 100 → 1000 users/sec
3. **Sustained load** (1800s): 1000 users/sec
4. **Peak load** (300s): 1000 → 2000 users/sec
5. **Ramp-down** (180s): 2000 → 100 users/sec

**Total Duration**: ~42 minutes

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WS_URL` | `ws://localhost:8000/ws` | WebSocket endpoint URL |
| `CONNECTIONS` | `100` | Number of concurrent connections |
| `MESSAGES` | `10` | Messages per connection |

### Artillery Configuration

Edit `artillery_websocket.yml` to customize:

```yaml
config:
  target: "ws://localhost:8000"  # Change target URL
  phases:
    - name: "Your phase"
      duration: 60                 # Duration in seconds
      arrivalRate: 10             # Starting users/sec
      rampTo: 100                 # Ending users/sec
```

### Processor Functions

The `websocket_processor.js` file contains test logic:

- `generateUserId`: Creates random user and agent IDs
- `sendAgentMessage`: Sends agent communication messages
- `measureLatency`: Tracks message latency
- `printStats`: Displays performance statistics

## Test Scenarios

### Scenario 1: WebSocket Communication Flow

Each virtual user in the test performs this flow:

1. **Connect** to WebSocket endpoint (`/ws`)
2. **Subscribe** to "agents" channel
3. **Subscribe** to "metrics" channel
4. **Loop 20 times**:
   - Send ping message (expect pong response)
   - Wait 5 seconds
   - Send agent message
   - Wait 3 seconds
5. **Unsubscribe** from "agents" channel
6. **Disconnect** gracefully

### Message Types

The tests send these message types (all handled by the backend):

#### Ping/Pong
```json
// Client sends
{"type": "ping"}

// Server responds
{"type": "pong"}
```

#### Subscribe/Unsubscribe
```json
// Client subscribes
{"type": "subscribe", "channel": "agents"}

// Server confirms
{"type": "subscribed", "channel": "agents"}

// Client unsubscribes
{"type": "unsubscribe", "channel": "agents"}

// Server confirms
{"type": "unsubscribed", "channel": "agents"}
```

#### Agent Messages
```json
// Client sends
{
  "type": "agent_message",
  "from": "user_123",
  "to": "agent_456",
  "payload": {
    "action": "execute",
    "timestamp": 1234567890,
    "data": {"test": true}
  }
}

// Server responds
{
  "type": "agent_response",
  "from": "agent_456",
  "to": "user_123",
  "payload": {
    "status": "processed",
    "action": "execute",
    "data": {"test": true}
  },
  "timestamp": 1234567890  // For latency calculation
}
```

#### Disconnect
```json
// Client requests disconnect
{"type": "disconnect"}

// Server acknowledges
{"type": "disconnect_ack"}
```

## Interpreting Results

### Standalone Stress Test Output

```
========================================
WEBSOCKET STRESS TEST RESULTS
========================================
Duration: 15.23s
Connections attempted: 1000
Connections successful: 998
Connections failed: 2
Success rate: 99.80%
Messages sent: 9980
Messages received: 9980
Messages/sec: 655.22

Latency Statistics:
  Average: 12.34ms
  P50: 10ms
  P95: 25ms
  P99: 45ms

Errors encountered:
  Connection timeout: 2
========================================
```

**Key Metrics**:
- **Success Rate**: Should be >95% for healthy system
- **Messages/sec**: Throughput indicator
- **P95/P99 Latency**: 95th/99th percentile response times
- **Errors**: Connection/message errors

### Artillery Output

Artillery provides real-time metrics:

```
Warm-up [========================] 60s | 100/100 VUs
  Scenarios launched: 6000
  Scenarios completed: 6000
  Requests completed: 120000
  Mean response/sec: 2000
  Response time (msec):
    min: 5
    max: 250
    median: 12
    p95: 45
    p99: 85
  Scenario counts:
    WebSocket Communication: 6000 (100%)
  Codes:
    WebSocket: 120000
```

## Performance Targets

### Healthy System Indicators

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Connection Success Rate | >99% | <99% | <95% |
| Message Throughput | >1000/sec | <1000/sec | <500/sec |
| P50 Latency | <20ms | <50ms | >100ms |
| P95 Latency | <50ms | <100ms | >200ms |
| P99 Latency | <100ms | <200ms | >500ms |
| Error Rate | <0.1% | <1% | >5% |

## Troubleshooting

### Issue: Connection Timeouts

**Symptoms**: High number of failed connections
**Causes**:
- Backend not running
- Firewall blocking connections
- Too many connections at once

**Solutions**:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Reduce concurrent connections
CONNECTIONS=50 node websocket_stress_test.js

# Increase batch delay in websocket_stress_test.js
```

### Issue: High Latency

**Symptoms**: P95/P99 latency >200ms
**Causes**:
- CPU/memory constraints
- Network issues
- Database bottlenecks

**Solutions**:
- Check system resources: `htop` or `top`
- Monitor backend logs
- Profile the backend application

### Issue: Message Loss

**Symptoms**: Messages sent ≠ Messages received
**Causes**:
- Connection drops
- Backend errors
- Message queue overflow

**Solutions**:
- Check backend logs for errors
- Verify WebSocket handlers in `main.py`
- Add retry logic to tests

### Issue: Artillery Installation Fails

**Symptoms**: `npm install` fails for artillery
**Solutions**:
```bash
# Clear npm cache
npm cache clean --force

# Install with legacy peer deps
npm install --legacy-peer-deps

# Or install globally
npm install -g artillery@latest
```

## Advanced Usage

### Custom Test Scenarios

Edit `artillery_websocket.yml` to add custom scenarios:

```yaml
scenarios:
  - name: "Custom Scenario"
    engine: "ws"
    flow:
      - function: "customFunction"
      - connect:
          url: "/ws"
      - send:
          payload: '{"type":"custom","data":"test"}'
```

Add the function to `websocket_processor.js`:

```javascript
function customFunction(context, events, done) {
  context.vars.customData = 'my-data';
  return done();
}
```

### Running Multiple Tests in Parallel

```bash
# Terminal 1: Quick test on port 8000
WS_URL=ws://localhost:8000/ws node websocket_stress_test.js &

# Terminal 2: Medium test on port 8001
WS_URL=ws://localhost:8001/ws CONNECTIONS=500 node websocket_stress_test.js &

# Wait for both to complete
wait
```

### Continuous Load Testing

```bash
# Run tests in a loop
while true; do
  echo "Running test at $(date)"
  CONNECTIONS=100 MESSAGES=5 node websocket_stress_test.js
  sleep 60  # Wait 1 minute between tests
done
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/load-test.yml
name: WebSocket Load Test

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install
      - run: python main.py &
      - run: sleep 10  # Wait for server
      - run: CONNECTIONS=100 MESSAGES=10 node websocket_stress_test.js
```

## Best Practices

1. **Start Small**: Begin with quick tests, then scale up
2. **Monitor Resources**: Watch CPU, memory, network during tests
3. **Baseline First**: Establish performance baseline before changes
4. **Test Incrementally**: Test after each significant backend change
5. **Document Results**: Keep records of test results over time
6. **Use Realistic Data**: Generate realistic user IDs and payloads
7. **Clean Up**: Ensure all connections close properly
8. **Gradual Ramp**: Don't start with maximum load immediately
9. **Error Analysis**: Investigate all errors, even if rate is low
10. **Regular Testing**: Schedule regular load tests to catch regressions

## Integration with Existing Tests

The WebSocket load tests complement existing testing:

- **Unit Tests** (`pytest`): Test individual functions
- **Integration Tests**: Test API endpoints
- **Load Tests** (`locust`): Test HTTP API under load
- **WebSocket Tests** (this): Test real-time communication
- **E2E Tests**: Test complete user flows

Run all tests together:

```bash
# Backend tests
pytest tests/

# API load test
python locust_api_load_test.py

# WebSocket load test
./run_websocket_test.sh quick

# Full system validation
python validate_system.py
```

## Support and Resources

- **Repository**: https://github.com/ymera-mfm/agents-1
- **Issues**: Report issues on GitHub
- **Artillery Docs**: https://www.artillery.io/docs
- **WebSocket Protocol**: https://datatracker.ietf.org/doc/html/rfc6455

## Changelog

### Version 1.0.0 (2024)
- Initial WebSocket load testing infrastructure
- Artillery configuration with multi-phase tests
- Standalone stress test script
- Cross-platform run scripts (Linux/Mac/Windows)
- Comprehensive documentation
- WebSocket endpoint enhancements for test support
