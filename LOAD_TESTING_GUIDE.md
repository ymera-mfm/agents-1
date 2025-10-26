# YMERA API Load Testing Guide

## Overview

This document describes the load testing implementation for the YMERA Multi-Agent AI System API using Locust.

## Files Created

1. **locust_api_load_test.py** - Main Locust load testing script
2. **test_api_simple.py** - Simple API endpoint validation script

## Issues Found and Fixed

### 1. Missing API Endpoints

The following endpoints were missing from the API and have been implemented:

#### Authentication
- `POST /api/v1/auth/login` - User authentication endpoint
  - Accepts username and password
  - Returns JWT access token for authenticated requests

#### Agent Management (Extended)
- `PUT /api/v1/agents/{agent_id}` - Update agent configuration
- `GET /api/v1/agents/search?q=<query>` - Search agents by query
- `POST /api/v1/agents/bulk` - Create multiple agents in batch
- `GET /api/v1/agents/export?format=<format>` - Export agent data

#### System Monitoring
- `GET /api/v1/metrics` - Get system metrics (agents, tasks, performance)
- `GET /api/v1/analytics` - Get analytics data with date range and grouping

### 2. Route Ordering Issue

**Problem**: FastAPI routes are matched in order. Specific routes like `/agents/search` were defined AFTER the dynamic route `/agents/{agent_id}`, causing the dynamic route to match first and treating "search" as an agent ID.

**Solution**: Reordered routes so specific endpoints are defined before dynamic endpoints:
- `/agents/search` - defined before
- `/agents/bulk` - defined before
- `/agents/export` - defined before  
- `/agents/{agent_id}` - defined after specific routes

### 3. Dependencies Added

Added `locust==2.31.8` to `requirements.txt` for load testing support.

## Running Load Tests

### Simple Endpoint Validation

```bash
# Start the API server
python main.py

# In another terminal, run the simple test
python test_api_simple.py
```

### Locust Load Testing

#### Headless Mode (Command Line)
```bash
# Small load test (10 users for 10 seconds)
locust -f locust_api_load_test.py \
    --host=http://localhost:8000 \
    --users=10 \
    --spawn-rate=2 \
    --run-time=10s \
    --headless \
    --html=load_test_report.html

# Medium load test (100 users for 1 minute)
locust -f locust_api_load_test.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=1m \
    --headless \
    --html=load_test_report.html \
    --csv=load_test_results

# Large load test (1000 users for 5 minutes)
locust -f locust_api_load_test.py \
    --host=http://localhost:8000 \
    --users=1000 \
    --spawn-rate=100 \
    --run-time=5m \
    --headless \
    --html=load_test_report.html \
    --csv=load_test_results
```

#### Web UI Mode
```bash
# Start Locust web interface on port 8089
locust -f locust_api_load_test.py --host=http://localhost:8000

# Then open http://localhost:8089 in your browser
# Enter number of users and spawn rate
# Click "Start Swarming" to begin the test
```

## Load Test Scenarios

### YMERAUser (Regular User)
Simulates typical user behavior with weighted tasks:
- Weight 10: Health check (most common)
- Weight 8: System info
- Weight 7: List agents
- Weight 6: List projects
- Weight 5: Get agent details
- Weight 4: Get metrics
- Weight 3: Create agent, search agents
- Weight 2: Update agent
- Weight 1: Delete agent

### HeavyUser (Power User)
Simulates resource-intensive operations:
- Weight 3: Bulk agent creation (10 agents at once)
- Weight 2: Export large datasets
- Weight 1: Complex analytics queries

## Performance Metrics Collected

The load test collects and reports:
- Total requests made
- Total failures
- Average response time
- P95 response time (95th percentile)
- P99 response time (99th percentile)
- Requests per second (RPS)

## Expected Results

For a healthy system under moderate load (100 users):
- Health endpoint: < 50ms average response time
- List endpoints: < 200ms average response time
- Create operations: < 500ms average response time
- P95 response time: < 1000ms
- Success rate: > 99%

## Troubleshooting

### Endpoint Returns 404
- Check that the API server is running
- Verify the API prefix is `/api/v1`
- Ensure route ordering is correct (specific before dynamic)

### High Failure Rate
- Check database connection
- Monitor system resources (CPU, memory)
- Verify WebSocket connections aren't exhausted
- Check application logs for errors

### Slow Response Times
- Check database query performance
- Monitor concurrent connections
- Review WebSocket broadcast performance
- Check for resource contention

## API Endpoint Summary

All endpoints now implemented:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/system/info` | System information |
| POST | `/api/v1/auth/login` | User authentication |
| GET | `/api/v1/agents` | List all agents |
| POST | `/api/v1/agents` | Create agent |
| GET | `/api/v1/agents/search` | Search agents |
| POST | `/api/v1/agents/bulk` | Bulk create agents |
| GET | `/api/v1/agents/export` | Export agents |
| GET | `/api/v1/agents/{agent_id}` | Get agent details |
| PUT | `/api/v1/agents/{agent_id}` | Update agent |
| DELETE | `/api/v1/agents/{agent_id}` | Delete agent |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/metrics` | System metrics |
| GET | `/api/v1/analytics` | Analytics data |
| WS | `/ws` | WebSocket endpoint |

## Next Steps

1. Implement proper authentication/authorization with JWT validation
2. Add database persistence for agents and metrics
3. Implement rate limiting to prevent abuse
4. Add caching for frequently accessed endpoints
5. Set up monitoring and alerting for production
6. Configure auto-scaling based on load metrics
