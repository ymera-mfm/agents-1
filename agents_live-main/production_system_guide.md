# Production-Ready Agent Engines - Complete Deployment Guide

## Critical Issues Found in Your Original Code

### 1. **Connection Management**
- ❌ No retry logic or circuit breakers
- ❌ Connections not properly closed on shutdown
- ❌ No health check mechanisms
- ✅ Fixed: Added retry with exponential backoff and circuit breaker pattern

### 2. **Error Handling**
- ❌ Silent failures in database operations
- ❌ No error recovery mechanisms
- ❌ Missing validation
- ✅ Fixed: Comprehensive try-catch with logging

### 3. **Resource Leaks**
- ❌ Tasks not properly cleaned up
- ❌ Background loops not cancellable
- ❌ No timeout mechanisms
- ✅ Fixed: Proper task tracking and cancellation

### 4. **Scalability Issues**
- ❌ No request queuing
- ❌ Unbounded concurrent tasks
- ❌ No backpressure handling
- ✅ Fixed: PriorityQueue with size limits

### 5. **Observability**
- ❌ Minimal logging
- ❌ No metrics collection
- ❌ No tracing support
- ✅ Fixed: OpenTelemetry integration with structured logging

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   NATS Message Bus                          │
│              (Central Communication Hub)                     │
└────┬──────────────┬──────────────┬───────────────┬──────────┘
     │              │              │               │
     ▼              ▼              ▼               ▼
┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐
│Intelligence│ Performance  │ Optimizing│ Custom Engines
│   Engine  │   Engine     │  Engine   │
└──────────┘ └──────────────┘ └──────────┘ └──────────────┘
     │              │              │               │
     └──────────────┼──────────────┼───────────────┘
                    ▼
         ┌────────────────────────┐
         │  PostgreSQL Database   │
         │  (Task Results, State) │
         └────────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    ┌─────────┐         ┌──────────┐
    │Redis    │         │Consul    │
    │(Cache)  │         │(Discovery)
    └─────────┘         └──────────┘
```

## Deployment Checklist

### Infrastructure Requirements

```yaml
PostgreSQL:
  - Minimum: 5 connections per agent
  - Connection pool: 5-20 per agent
  - Storage: 100GB+ (depends on task volume)
  - Backup: Daily snapshots + WAL archiving

NATS:
  - Cluster mode recommended
  - JetStream enabled for persistence
  - At least 3 nodes for HA

Redis:
  - Cluster mode for >50GB data
  - AOF persistence enabled
  - Replication: Master + 2 Slaves

Consul:
  - 3+ nodes for production
  - Backup enabled

Resource Limits per Agent:
  - CPU: 2+ cores
  - Memory: 1GB minimum, 4GB recommended
  - Disk: 50GB+ for logs and cache
```

### Database Schema

```sql
-- Agents table
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'healthy',
    capabilities JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP
);

-- Task results table
CREATE TABLE task_results (
    task_id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    result JSONB,
    error TEXT,
    execution_time_ms FLOAT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (agent_id) REFERENCES agents(name)
);

-- Decision history for ML training
CREATE TABLE decision_history (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE,
    task_type VARCHAR(100),
    selected_agent VARCHAR(255),
    confidence FLOAT,
    reasoning TEXT,
    context_data JSONB,
    system_state JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_task_results_agent_time ON task_results(agent_id, created_at DESC);
CREATE INDEX idx_decision_history_task_type ON decision_history(task_type, created_at DESC);
```

## Configuration Examples

### Environment Variables

```bash
# NATS Configuration
NATS_URL=nats://nats.production.svc:4222

# PostgreSQL
POSTGRES_URL=postgresql://user:password@postgres.production.svc:5432/agents_db

# Redis
REDIS_URL=redis://:password@redis.production.svc:6379

# Consul
CONSUL_URL=http://consul.production.svc:8500

# Agent Configuration
AGENT_ID=intelligence-engine-prod-001
AGENT_MAX_CONCURRENT_TASKS=100
AGENT_TASK_TIMEOUT_SECONDS=300
AGENT_HEARTBEAT_INTERVAL=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Observability
ENABLE_METRICS=true
ENABLE_TRACING=true
JAEGER_ENDPOINT=http://jaeger-collector.production.svc:14268/api/traces
```

### Docker Compose (Development/Testing)

```yaml
version: '3.9'

services:
  nats:
    image: nats:alpine
    ports:
      - "4222:4222"
    command: "-js"

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: agents_db
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  consul:
    image: consul:latest
    ports:
      - "8500:8500"
    command: agent -server -ui -bootstrap-expect=1 -client=0.0.0.0

volumes:
  postgres_data:
```

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intelligence-engine
  namespace: agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: intelligence-engine
  template:
    metadata:
      labels:
        app: intelligence-engine
    spec:
      containers:
      - name: intelligence-engine
        image: your-registry/intelligence-engine:latest
        imagePullPolicy: Always
        env:
        - name: NATS_URL
          value: "nats://nats-cluster:4222"
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-string
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

## Monitoring & Observability

### Prometheus Metrics

```python
# Metrics to expose
agent_tasks_total = Counter(
    'agent_tasks_total',
    'Total tasks processed',
    ['agent_name', 'status']
)

agent_task_duration_seconds = Histogram(
    'agent_task_duration_seconds',
    'Task execution duration',
    ['agent_name'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

agent_queue_size = Gauge(
    'agent_queue_size',
    'Current task queue size',
    ['agent_name']
)

routing_decisions_total = Counter(
    'routing_decisions_total',
    'Total routing decisions',
    ['strategy', 'outcome']
)

circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half_open, 2=open)',
    ['agent_id']
)
```

### Logging Standards

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "agent.intelligence_engine",
  "message": "Task routed successfully",
  "context": {
    "task_id": "task-123",
    "task_type": "llm_inference",
    "selected_agent": "llm-engine-001",
    "confidence": 0.95,
    "duration_ms": 250
  },
  "trace_id": "trace-456",
  "span_id": "span-789"
}
```

## Health Checks

### Liveness Check

```python
@app.get("/health")
async def health_check():
    if agent.state == AgentState.STOPPED:
        raise HTTPException(status_code=503)
    
    checks = {
        "nats": agent.nc is not None and agent.nc.is_connected,
        "postgres": agent.db_pool is not None,
        "redis": agent.redis_client is not None
    }
    
    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail=checks)
```

### Readiness Check

```python
@app.get("/ready")
async def readiness_check():
    if agent.state not in [AgentState.RUNNING, AgentState.READY]:
        raise HTTPException(status_code=503)
    
    # Check if agent has received heartbeat from other agents
    if len(agent.agent_registry) == 0:
        raise HTTPException(status_code=503, detail="No agents registered")
    
    return {"status": "ready"}
```

## Graceful Shutdown

```python
async def shutdown_handler(signal_num):
    logger.info(f"Received signal {signal_num}, shutting down gracefully")
    
    # Set shutdown event
    agent.shutdown_event.set()
    
    # Wait for tasks to complete (with timeout)
    try:
        await asyncio.wait_for(
            asyncio.gather(*agent.background_tasks, return_exceptions=True),
            timeout=30
        )
    except asyncio.TimeoutError:
        logger.warning("Background tasks did not complete in time")
    
    # Close connections
    await agent.stop()

# Register signal handlers
for sig in [signal.SIGTERM, signal.SIGINT]:
    signal.signal(sig, shutdown_handler)
```

## Performance Tuning

### Task Queue Optimization

```python
# For high-throughput scenarios
config = AgentConfig(
    agent_id="high-throughput-engine",
    max_concurrent_tasks=200,
    queue_size=5000,
    task_timeout_seconds=60
)

# For low-latency scenarios
config = AgentConfig(
    agent_id="low-latency-engine",
    max_concurrent_tasks=50,
    queue_size=1000,
    task_timeout_seconds=30
)
```

### Database Connection Pooling

```python
# Optimize pool size based on workload
# Pool size = (core_count * 2) + effective_spindle_count
# For 8-core system with SSD: pool_size = 16-20

db_pool = await asyncpg.create_pool(
    postgres_url,
    min_size=10,
    max_size=20,
    max_cached_statement_lifetime=300,
    max_cacheable_statement_size=15000,
    command_timeout=60
)
```

## Common Issues & Solutions

### Issue: Task Timeouts

**Symptom**: Tasks consistently timeout
**Causes**: 
- Under-provisioned agents
- Database connection issues
- Network latency

**Solution**:
```python
# Increase timeout appropriately
config.task_timeout_seconds = 600

# Monitor agent load
if len(active_tasks) > max_concurrent_tasks * 0.8:
    # Scale up or reject new tasks
    logger.warning("Agent approaching capacity")
```

### Issue: Memory Leaks

**Symptom**: Memory usage grows over time
**Causes**:
- Unbounded deques
- Task references not released
- Connection pool leaks

**Solution**:
```python
# Add periodic memory cleanup
async def memory_cleanup_loop():
    while not shutdown_event.is_set():
        # Force garbage collection
        gc.collect()
        
        # Clear old decision history
        cutoff_time = time.time() - 86400  # 24 hours
        decision_history = deque(
            d for d in decision_history
            if d['timestamp'] > cutoff_time
        )
        
        await asyncio.sleep(3600)
```

### Issue: Circuit Breaker Gets Stuck

**Symptom**: Agents unreachable even after recovery
**Causes**:
- Timeout too short
- Failure threshold too low

**Solution**:
```python
# Adjust circuit breaker settings
circuit_breaker = {
    'threshold': 10,  # 10 failures
    'timeout': 120,   # 2 minutes before half-open
    'state': 'closed'
}
```

## Production Runbook

### Daily Checks

```bash
#!/bin/bash
# Check agent status
curl http://intelligence-engine:8080/health

# Check task queue depth
curl http://intelligence-engine:8080/metrics | grep agent_queue_size

# Verify database connectivity
psql postgresql://user:pass@postgres/agents_db -c "SELECT COUNT(*) FROM task_results WHERE created_at > NOW() - INTERVAL '1 hour';"

# Check NATS cluster
nats-cli server list
```

### Scaling Decision Matrix

```
Average Queue Size | Action
0-100            | No action needed
100-500          | Monitor, prepare to scale
500-1000         | Scale up (add 1-2 instances)
>1000            | Emergency scale up (add 3+ instances)
```

## Testing Strategy

### Unit Tests

```python
async def test_task_routing():
    engine = IntelligenceEngine(config)
    
    context = DecisionContext(
        request_id="test-1",
        task_type="validation",
        requirements={}
    )
    
    recommendation = await engine._route_task(context)
    assert recommendation.confidence > 0.0
```

### Integration Tests

```python
async def test_end_to_end():
    # Start all services
    async with start_test_environment():
        engine = IntelligenceEngine(config)
        await engine.start()
        
        # Submit task
        task = TaskRequest(
            task_type="test",
            payload={"test": "data"}
        )
        
        # Verify execution
        result = await asyncio.wait_for(
            engine._handle_task(task),
            timeout=10
        )
        
        assert result["status"] == "success"
```

### Load Testing

```bash
# Using k6
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m30s', target: 100 },
    { duration: '20s', target: 0 },
  ],
};

export default function () {
  let response = http.post(
    'http://intelligence-engine:8080/route-task',
    JSON.stringify({ task_type: 'test' })
  );
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

## Disaster Recovery

### Backup Strategy

```bash
# Daily database backups
pg_dump postgresql://user:pass@postgres/agents_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Redis snapshots
redis-cli BGSAVE

# Keep 30 days of backups
find ./backups -name "backup_*.sql.gz" -mtime +30 -delete
```

### Recovery Procedures

```bash
# Restore from backup
gunzip backup_20240115.sql.gz
psql postgresql://user:pass@postgres/agents_db < backup_20240115.sql

# Verify integrity
SELECT COUNT(*) FROM agents;
SELECT COUNT(*) FROM task_results;
```

## Security Considerations

```python
# TLS for NATS
nats_url = "tls://nats.production.svc:4222"

# Connection string with SSL
postgres_url = "postgresql://user:pass@postgres/agents_db?sslmode=require"

# Redis AUTH
redis_url = "redis://:securepassword@redis:6379"

# API Authentication
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token or not verify_token(token):
        return JSONResponse(status_code=401)
    return await call_next(request)
```

## Support & Troubleshooting

### Enable Debug Logging

```python
# Set environment variable
LOG_LEVEL=DEBUG

# Or programmatically
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Collect Diagnostics

```bash
#!/bin/bash
# Agent logs
kubectl logs -n agents deployment/intelligence-engine

# System metrics
kubectl top nodes
kubectl top pods -n agents

# NATS cluster info
nats-cli server list
nats-cli stream list

# Database statistics
psql -c "SELECT * FROM pg_stat_statements LIMIT 10;"
```