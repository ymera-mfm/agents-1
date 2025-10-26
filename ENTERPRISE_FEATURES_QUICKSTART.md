# Enterprise Features Quick Reference Guide

Quick reference for developers using the new enterprise production features.

## Rate Limiting

### Configure Rate Limits

```python
# In main.py
from slowapi import Limiter

# Default: 100 requests/minute
@app.get("/api/v1/my-endpoint")
@limiter.limit("100/minute")
async def my_endpoint(request: Request):
    pass

# Strict: 5 requests/minute (for auth)
@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: dict):
    pass
```

### Check Rate Limit Status

```bash
# View current rate limits in Redis
redis-cli --scan --pattern "slowapi:*"

# Clear rate limits for testing
redis-cli FLUSHDB
```

---

## Agent Configuration

### Update Agent Config (API)

```bash
# Get agent configuration schema
curl http://localhost:8000/api/v1/agents/agent_123/schema

# Update agent configuration
curl -X POST http://localhost:8000/api/v1/agents/agent_123/config \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "checkpoint_interval": 120,
      "max_retries": 5,
      "log_level": "DEBUG"
    }
  }'
```

### Use Dynamic Config Form (React)

```jsx
import DynamicAgentConfigForm from './components/DynamicAgentConfigForm';

function AgentSettings() {
  return (
    <DynamicAgentConfigForm
      agentId="agent_123"
      onSuccess={(data) => {
        console.log('Configuration updated:', data);
        // Show success message
      }}
      onError={(error) => {
        console.error('Update failed:', error);
        // Show error message
      }}
    />
  );
}
```

---

## Agent Checkpointing

### Enable Checkpointing

```python
from base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, agent_id, config=None):
        super().__init__(agent_id, config)
        # Set checkpoint interval (seconds)
        self.checkpoint_interval = 60
    
    async def get_checkpoint_state(self):
        """Save custom state"""
        return {
            "task_count": self.task_count,
            "last_action": self.last_action,
            "custom_data": self.custom_data
        }
    
    async def restore_checkpoint_state(self, state):
        """Restore custom state"""
        self.task_count = state.get("task_count", 0)
        self.last_action = state.get("last_action")
        self.custom_data = state.get("custom_data", {})
```

### Set Storage Backend

```python
import redis.asyncio as redis

# Create Redis client
redis_client = redis.from_url("redis://localhost:6379")

# Set storage backend for agent
agent = MyAgent("my_agent_123")
agent.set_storage_backend(redis_client)

# Checkpoints will now save to Redis
await agent.start()
```

### Manual Checkpoint

```python
# Force checkpoint save
await agent.save_checkpoint()

# Force checkpoint load
await agent.load_checkpoint()
```

---

## WebSocket Broadcasting

### Optimized Broadcasting

```python
# Broadcasting is now automatic and optimized
# No code changes needed!

# The ConnectionManager handles:
# - Concurrent sends to all clients
# - 5-second timeout per client
# - Automatic cleanup of failed connections

await manager.broadcast({
    "event": "agent:updated",
    "data": {"id": "agent_123", "status": "running"}
})
```

### Monitor WebSocket Connections

```bash
# Check active connections
curl http://localhost:8000/api/v1/system/info

# Response includes:
# {
#   "websocket_connections": 42
# }
```

---

## Frontend Performance Metrics

### Enable Web Vitals Reporting

```javascript
// In your app entry point (index.js or App.js)
import { initAnalytics } from './utils/analytics';

// Initialize on app load
initAnalytics();

// Web Vitals are now automatically reported!
// No additional code needed.
```

### Manual Metric Reporting

```javascript
import { reportWebVitalsToBackend } from './utils/analytics';

// Report custom metric
reportWebVitalsToBackend({
  name: 'Custom_Metric',
  value: 1234,
  id: 'v3-custom-' + Date.now(),
  sessionId: 'current_session_id'
});
```

### View Metrics (Backend)

```bash
# Metrics are logged automatically
# Check logs for entries like:
# INFO: Frontend Performance Metric - Name: LCP, Value: 2500, ...

# Or integrate with time-series database:
# - InfluxDB
# - TimescaleDB
# - Prometheus
```

---

## Security Headers

### Verify Headers

```bash
# Check security headers on any endpoint
curl -I http://localhost:8000/api/v1/health

# Should include:
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
```

### Headers Applied Automatically

All HTTP responses automatically include security headers. No configuration needed!

---

## Content Security Policy (CSP)

### Production Mode

```bash
# Set environment for production build
export NODE_ENV=production

# Build frontend
npm run build

# CSP will automatically exclude:
# - 'unsafe-inline'
# - 'unsafe-eval'
```

### Development Mode

```bash
# Set environment for development
export NODE_ENV=development

# Start dev server
npm start

# CSP includes unsafe directives for hot-reload
```

### Validate CSP

```bash
# Run validation script
cd frontend
node validate-system.cjs

# Or in build process
npm run build  # Will fail if CSP is unsafe in production
```

---

## NATS JetStream

### Message Publishing

```python
from agent_communication import CommunicationAgent

# Initialize with JetStream enabled
comm_agent = CommunicationAgent(
    agent_id="comm_agent",
    config={
        "nats_servers": ["nats://localhost:4222"],
        "use_jetstream": True,
        "stream_name": "AGENT_MESSAGES"
    }
)

await comm_agent.initialize()

# Publish message (guaranteed delivery)
message = {
    "to": "target_agent",
    "type": "request",
    "payload": {"action": "process", "data": "test"}
}

result = await comm_agent.process_message(message)
# Result includes JetStream sequence number
```

### Fallback to In-Memory

```python
# If NATS is unavailable, automatically falls back to in-memory
# No code changes needed!

# Check current mode
stats = comm_agent.get_statistics()
print(f"Using JetStream: {stats['use_jetstream']}")
print(f"Connected: {stats['jetstream_connected']}")
```

---

## Testing

### Run E2E Tests

```bash
# Run all enterprise feature tests
pytest tests/test_enterprise_features.py -v

# Run specific test class
pytest tests/test_enterprise_features.py::TestRateLimiting -v

# Run with coverage
pytest tests/test_enterprise_features.py --cov=. --cov-report=html
```

### Generate Test Report

```bash
# Generate JSON test report
python tests/test_enterprise_features.py

# Output: e2e_test_report.json
cat e2e_test_report.json
```

---

## Environment Variables

### Required Variables

```env
# Redis (for rate limiting and checkpointing)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional

# NATS (optional, has fallback)
NATS_SERVERS=nats://localhost:4222

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ymera

# Security
SECRET_KEY=your-secret-key-change-in-production

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### Frontend Variables

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# Features
REACT_APP_ENABLE_CSP=true
REACT_APP_ENABLE_PERFORMANCE_MONITORING=true

# Environment
NODE_ENV=production
```

---

## Troubleshooting

### Rate Limiting Not Working

```bash
# 1. Check Redis connection
redis-cli ping
# Should return: PONG

# 2. Check Redis keys
redis-cli --scan --pattern "slowapi:*"
# Should show rate limit keys

# 3. Check logs for rate limit errors
tail -f logs/app.log | grep "rate"
```

### Checkpoints Not Saving

```bash
# 1. Check Redis connection
redis-cli ping

# 2. List checkpoints
redis-cli KEYS "agent:checkpoint:*"

# 3. View checkpoint data
redis-cli GET "agent:checkpoint:my_agent_id"

# 4. Check agent logs
tail -f logs/app.log | grep "checkpoint"
```

### WebSocket Issues

```bash
# 1. Check active connections
curl http://localhost:8000/api/v1/system/info

# 2. Test WebSocket connection
wscat -c ws://localhost:8000/ws

# 3. Send test message
> {"type": "ping"}
< {"type": "pong"}
```

### Frontend Metrics Not Reporting

```javascript
// 1. Check browser console for errors
console.log('Checking Web Vitals...');

// 2. Verify web-vitals is installed
import * as webVitals from 'web-vitals';
console.log(webVitals);

// 3. Check API endpoint
fetch('http://localhost:8000/api/v1/metrics/frontend', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'TEST',
    value: 123,
    id: 'test-123',
    sessionId: 'test-session'
  })
});
```

---

## Performance Tips

### Optimize Checkpoint Interval

```python
# Frequent checkpoints (more overhead, less data loss)
agent = MyAgent("agent_id", config={"checkpoint_interval": 30})

# Infrequent checkpoints (less overhead, more data loss)
agent = MyAgent("agent_id", config={"checkpoint_interval": 300})

# Recommended: 60 seconds (default)
```

### Tune Rate Limits

```python
# High traffic endpoint
@app.get("/api/v1/public-data")
@limiter.limit("1000/minute")
async def public_data(request: Request):
    pass

# Low traffic, expensive operation
@app.post("/api/v1/expensive-operation")
@limiter.limit("10/minute")
async def expensive_op(request: Request):
    pass
```

### WebSocket Connection Limits

```python
# In main.py, adjust ConnectionManager timeout
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.broadcast_timeout = 5.0  # Adjust as needed
```

---

## Monitoring

### Key Metrics to Monitor

1. **Rate Limit Violations**: Track 429 responses
2. **WebSocket Connections**: Monitor active count
3. **Checkpoint Success Rate**: Ensure agents are saving
4. **Frontend Metrics**: CLS, LCP, FID trends
5. **NATS Message Lag**: JetStream consumer lag

### Prometheus Integration

```python
# Add to main.py
from prometheus_client import Counter, Histogram, Gauge

rate_limit_violations = Counter('rate_limit_violations', 'Rate limit violations')
websocket_connections = Gauge('websocket_connections', 'Active WebSocket connections')
checkpoint_duration = Histogram('checkpoint_duration_seconds', 'Checkpoint save duration')
```

---

## Best Practices

### Rate Limiting
- Start with conservative limits (100/min)
- Monitor 429 responses
- Adjust based on usage patterns
- Document limits in API docs

### Checkpointing
- Keep checkpoint data minimal
- Use checkpoint_interval wisely
- Test recovery procedures
- Monitor checkpoint failures

### WebSocket
- Implement client-side reconnection
- Handle connection drops gracefully
- Monitor connection count
- Use heartbeat/ping messages

### Frontend Metrics
- Don't block user experience
- Report asynchronously
- Sample high-frequency metrics
- Analyze trends, not individual values

### Security
- Always use HTTPS in production
- Keep CSP strict (no unsafe-*)
- Review security headers regularly
- Monitor for security issues

---

## Additional Resources

- **Full Documentation**: ENTERPRISE_IMPLEMENTATION_REPORT.md
- **E2E Tests**: tests/test_enterprise_features.py
- **API Docs**: http://localhost:8000/api/v1/docs
- **Grafana Dashboards**: http://localhost:3001

---

**Last Updated**: October 26, 2025  
**Version**: 1.0.0
