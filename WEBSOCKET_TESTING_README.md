# WebSocket Load Testing - Quick Start

This directory contains WebSocket load testing infrastructure for YMERA.

## 🚀 Quick Start

### Prerequisites
```bash
npm install  # Install Node.js dependencies (ws package)
```

### Run Tests

```bash
# Quick test (100 connections, 10 messages)
./run_websocket_test.sh quick

# Medium test (500 connections, 20 messages)
./run_websocket_test.sh medium

# Heavy test (1000 connections, 50 messages)
./run_websocket_test.sh heavy
```

### Custom Test
```bash
CONNECTIONS=250 MESSAGES=30 WS_URL=ws://localhost:8000/ws node websocket_stress_test.js
```

## 📋 Components

- **artillery_websocket.yml** - Artillery load test configuration
- **websocket_processor.js** - Artillery test processor functions
- **websocket_stress_test.js** - Standalone stress test script
- **run_websocket_test.sh** - Linux/Mac test runner
- **run_websocket_test.bat** - Windows test runner
- **websocket_test_server.py** - Minimal test server
- **WEBSOCKET_TESTING_GUIDE.md** - Complete documentation

## 📊 Expected Output

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
========================================
```

## 🎯 Performance Targets

| Metric | Target |
|--------|--------|
| Connection Success Rate | >99% |
| Message Throughput | >1000/sec |
| P50 Latency | <20ms |
| P95 Latency | <50ms |
| P99 Latency | <100ms |
| Error Rate | <0.1% |

## 📚 Full Documentation

See [WEBSOCKET_TESTING_GUIDE.md](./WEBSOCKET_TESTING_GUIDE.md) for complete documentation including:
- Detailed setup instructions
- Test scenarios and message types
- Performance tuning
- Troubleshooting guide
- CI/CD integration examples

## 🔧 Troubleshooting

### Server Not Running
```bash
# Verify server is running
curl http://localhost:8000/health

# Start server if needed
python main.py
```

### Connection Timeouts
```bash
# Reduce concurrent connections
CONNECTIONS=50 MESSAGES=10 node websocket_stress_test.js
```

### High Latency
- Check system resources (CPU, memory)
- Monitor backend logs
- Reduce load and test incrementally
