# Implementation & Migration Checklist

## Executive Summary

Your original engine system had solid architectural concepts but critical production issues. The provided implementations fix:

1. **Connection Management**: Added retry logic, circuit breakers, health checks
2. **Error Handling**: Comprehensive exception handling with proper logging
3. **Resource Management**: Task queues, timeouts, proper cleanup
4. **Scalability**: Request queuing, backpressure handling
5. **Observability**: Structured logging, metrics, tracing support

## Pre-Migration Tasks

- [ ] **Audit Current System**
  - [ ] Document all custom agents and their dependencies
  - [ ] Identify all external service integrations
  - [ ] Map all data flows and message patterns
  - [ ] Document all database schemas and queries
  
- [ ] **Infrastructure Assessment**
  - [ ] Verify PostgreSQL version and replication setup
  - [ ] Check NATS cluster configuration
  - [ ] Review Redis setup and persistence
  - [ ] Document current resource allocation

- [ ] **Testing Plan**
  - [ ] Create test suite for each engine
  - [ ] Set up performance baseline metrics
  - [ ] Prepare rollback procedures
  - [ ] Document acceptable downtime window

## Migration Phase

### Week 1: Foundation Setup

- [ ] **1.1 Deploy Infrastructure**
  - [ ] Create new PostgreSQL cluster with backup
  - [ ] Set up NATS cluster (3+ nodes)
  - [ ] Configure Redis with persistence
  - [ ] Verify all connections and failover

- [ ] **1.2 Database Migration**
  - [ ] Back up existing database
  - [ ] Create new schema with updated structure
  - [ ] Migrate historical data
  - [ ] Verify data integrity
  - [ ] Set up replication

- [ ] **1.3 Base Agent Framework**
  - [ ] Deploy BaseAgent v3.0
  - [ ] Verify connection pooling
  - [ ] Test graceful shutdown
  - [ ] Validate health checks

### Week 2: Engine Migration

- [ ] **2.1 Intelligence Engine**
  - [ ] Deploy IntelligenceEngine v2.1
  - [ ] Test agent discovery and registration
  - [ ] Validate routing decisions
  - [ ] Monitor circuit breaker functionality
  - [ ] Measure routing latency

- [ ] **2.2 Performance Engine**
  - [ ] Deploy PerformanceEngineAgent
  - [ ] Configure monitoring thresholds
  - [ ] Set up alert channels
  - [ ] Test alert generation
  - [ ] Validate metrics collection

- [ ] **2.3 Optimization Engine**
  - [ ] Deploy OptimizationEngineAgent
  - [ ] Configure optimization rules
  - [ ] Test rule execution
  - [ ] Measure optimization impact

### Week 3: Analysis & Validation

- [ ] **3.1 Analysis Engine**
  - [ ] Deploy AnalysisEngineAgent
  - [ ] Implement validation rules
  - [ ] Test data analysis pipelines
  - [ ] Verify insight generation

- [ ] **3.2 Integration Testing**
  - [ ] Test end-to-end workflows
  - [ ] Verify inter-engine communication
  - [ ] Load testing (target: 1000+ req/sec)
  - [ ] Chaos testing (network issues, service failures)

- [ ] **3.3 Production Readiness**
  - [ ] Security audit
  - [ ] Performance profiling
  - [ ] Disaster recovery drill
  - [ ] Documentation review

## Custom Engine Adaptation

### For Each Custom Engine

```python
# 1. Update imports
from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority

# 2. Inherit from BaseAgent
class YourCustomEngine(BaseAgent):
    async def _setup_subscriptions(self):
        # Register your NATS subscriptions here
        pass
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        # Implement your task handling
        pass

# 3. Use connection methods
await self._publish("subject", data)
await self._publish_to_stream("stream", data)
rows = await self._db_fetch("SELECT * FROM table")
await self._db_execute("INSERT ...")

# 4. Use metrics
self.metrics.tasks_completed += 1
self.metrics.avg_processing_time_ms = calculation

# 5. Proper error handling
try:
    result = await self._handle_task(task_request)
except asyncio.TimeoutError:
    self.logger.error("Task timeout")
except Exception as e:
    self.logger.error(f"Task error: {e}", exc_info=True)
```

## Rollback Plan

### If Critical Issues Arise

```bash
# 1. Immediate Actions (Minutes 0-5)
- Set TRAFFIC_ROUTE=old_system
- Disable new agents: kubectl scale deployment intelligence-engine --replicas=0
- Verify old system traffic is restored

# 2. Investigation (Minutes 5-30)
- Collect logs: kubectl logs deployment/intelligence-engine
- Check database consistency
- Review recent changes

# 3. Restore from Backup (Minutes 30-60)
- Restore database: psql < backup_latest.sql
- Verify data integrity
- Scale up old system

# 4. Post-Mortem
- Review what failed
- Update deployment procedures
- Schedule fixes
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agents'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - agents
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: '.*-engine'
      - source_labels: [__address__]
        target_label: __param_target
      - target_label: __address__
        replacement: localhost:8080
```

### Alert Rules

```yaml
# alert-rules.yml
groups:
  - name: agent_alerts
    rules:
      - alert: AgentDown
        expr: up{job="agents"} == 0
        for: 5m
        annotations:
          summary: "Agent {{ $labels.pod }} is down"
      
      - alert: HighTaskQueueDepth
        expr: agent_queue_size > 1000
        for: 5m
        annotations:
          summary: "Task queue depth {{ $value }} on {{ $labels.agent_name }}"
      
      - alert: TaskFailureRate
        expr: rate(agent_tasks_total{status="failed"}[5m]) > 0.05
        for: 10m
        annotations:
          summary: "High task failure rate on {{ $labels.agent_name }}"
      
      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_activity_count > 18
        for: 5m
        annotations:
          summary: "PostgreSQL connection pool near capacity"
```

### Grafana Dashboards

Key metrics to visualize:
- Task success/failure rates
- Agent routing decisions and confidence
- System resource utilization
- Circuit breaker states
- Database query performance
- NATS message throughput

## Production Checklists

### Daily Operations

```bash
#!/bin/bash
# daily_checks.sh

echo "=== Daily Health Checks ==="

# 1. Pod status
echo "Pod Status:"
kubectl get pods -n agents

# 2. Database
echo "Database Connections:"
psql postgresql://agents:PASSWORD@postgres/agents_db \
  -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# 3. NATS cluster
echo "NATS Status:"
nats-cli server list

# 4. Redis
echo "Redis Memory:"
redis-cli INFO memory | grep used_memory

# 5. Recent errors
echo "Recent Errors:"
kubectl logs deployment/intelligence-engine -n agents --tail=100 | grep -i error

# 6. Task completion
echo "Task Metrics:"
psql postgresql://agents:PASSWORD@postgres/agents_db \
  -c "SELECT status, COUNT(*) FROM task_results WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY status;"
```

### Weekly Maintenance

- [ ] Review error logs and fix recurring issues
- [ ] Check disk usage on all nodes
- [ ] Verify backup integrity
- [ ] Review performance metrics
- [ ] Update agent configurations
- [ ] Test disaster recovery procedure

### Monthly Reviews

- [ ] Performance analysis and tuning
- [ ] Capacity planning
- [ ] Security audit
- [ ] Dependency updates
- [ ] Documentation review
- [ ] Team training

## Troubleshooting Guide

### Issue: Agents Not Registering

**Symptoms:**
- Intelligence engine shows 0 agents
- No heartbeats received

**Investigation:**
```bash
# Check NATS connectivity
kubectl exec -it deployment/intelligence-engine -n agents -- \
  nc -zv nats.agents.svc 4222

# Check agent logs
kubectl logs deployment/performance-engine -n agents | grep -i "connect\|error"

# Verify network policies
kubectl get networkpolicies -n agents
```

**Solution:**
```bash
# Restart agents
kubectl rollout restart deployment/intelligence-engine -n agents
kubectl rollout restart deployment/performance-engine -n agents

# Check for DNS issues
kubectl exec -it deployment/intelligence-engine -- nslookup nats.agents.svc
```

### Issue: Task Queue Growing

**Symptoms:**
- agent_queue_size metric continuously increasing
- Task processing slowing down

**Investigation:**
```bash
# Check agent load
kubectl top pods -n agents

# Examine task types
psql -c "SELECT task_type, COUNT(*) FROM task_results 
          WHERE created_at > NOW() - INTERVAL '1 hour' 
          GROUP BY task_type ORDER BY count DESC;"

# Check for stuck tasks
psql -c "SELECT task_id, started_at FROM task_results 
          WHERE status='processing' AND started_at < NOW() - INTERVAL '30 minutes';"
```

**Solution:**
```bash
# Scale up affected agents
kubectl scale deployment performance-engine --replicas=5 -n agents

# Increase task timeout if legitimate
kubectl set env deployment/intelligence-engine \
  AGENT_TASK_TIMEOUT_SECONDS=600 -n agents
```

### Issue: Database Connection Errors

**Symptoms:**
- "connection pool exhausted" errors
- Task timeouts

**Investigation:**
```bash
# Check active connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check for long-running queries
psql -c "SELECT query, duration FROM pg_stat_statements 
          ORDER BY duration DESC LIMIT 10;"

# Check pool settings
kubectl exec -it deployment/intelligence-engine -- \
  grep -i "pool" application.log
```

**Solution:**
```bash
# Increase pool size in deployment
kubectl set env deployment/intelligence-engine \
  DB_POOL_MAX_SIZE=30 -n agents

# Kill long-running queries if safe
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
          WHERE query_start < NOW() - INTERVAL '10 minutes';"
```

## Performance Tuning

### Task Processing Optimization

```python
# Adjust for your workload
config = AgentConfig(
    # High throughput: many small tasks
    max_concurrent_tasks=200,
    queue_size=5000,
    task_timeout_seconds=30,
    
    # Low latency: few complex tasks
    # max_concurrent_tasks=50,
    # queue_size=500,
    # task_timeout_seconds=300,
)
```

### Database Query Optimization

```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 100; -- 100ms
SELECT pg_reload_conf();

-- Find slow queries
SELECT query, calls, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Analyze table
ANALYZE task_results;

-- View index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan ASC;
```

## Quick-Start Guide for New Team Members

### 1. Local Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/agent-engines.git
cd agent-engines

# Install dependencies
pip install -r requirements.txt

# Start local environment
docker-compose up -d

# Wait for services
sleep 30

# Run tests
pytest tests/ -v

# Start an agent locally
python -m agents.intelligence_engine
```

### 2. Deploying Your First Agent

```python
# 1. Create agent_config.py
from base_agent import AgentConfig

config = AgentConfig(
    agent_id="my-engine-001",
    name="my_engine",
    agent_type="custom",
    capabilities=["processing", "analysis"],
    nats_url="nats://nats:4222",
    postgres_url="postgresql://user:pass@postgres/agents_db"
)

# 2. Create your_engine.py
from base_agent import BaseAgent, TaskRequest

class MyEngine(BaseAgent):
    async def _setup_subscriptions(self):
        await self._subscribe("my.topic", self._handle_message)
    
    async def _handle_task(self, task_request: TaskRequest):
        # Your logic here
        return {"status": "success"}

# 3. Deploy
if __name__ == "__main__":
    import asyncio
    
    async def main():
        engine = MyEngine(config)
        if await engine.start():
            await engine.run_forever()
    
    asyncio.run(main())
```

### 3. Monitoring Your Engine

```bash
# View logs
kubectl logs -f deployment/my-engine -n agents

# Check metrics
kubectl port-forward svc/prometheus 9090:9090
# Visit http://localhost:9090

# View Grafana dashboards
kubectl port-forward svc/grafana 3000:3000
# Visit http://localhost:3000 (admin/admin)

# Manual health check
curl http://my-engine:8080/health
```

### 4. Common Commands

```bash
# Deploy engine
kubectl apply -f deployment.yaml

# View engine status
kubectl describe deployment/my-engine -n agents

# Scale engine
kubectl scale deployment/my-engine --replicas=5 -n agents

# Update engine image
kubectl set image deployment/my-engine \
  my-engine=registry/my-engine:v2.0 -n agents

# View database
psql postgresql://agents:PASSWORD@postgres/agents_db

# Access NATS CLI
kubectl exec -it nats-0 -n agents -- nats-cli
```

## Support Contacts

- **Infrastructure Issues**: #infrastructure-team
- **Agent Development**: #agent-development
- **On-Call**: Check [on-call-schedule](https://pagerduty.com)
- **Documentation**: [Wiki](https://wiki.internal)
- **Issues/PRs**: GitHub Organization

## Additional Resources

- [Complete API Documentation](./docs/api.md)
- [Architecture Diagrams](./docs/architecture.md)
- [Performance Benchmarks](./docs/benchmarks.md)
- [Security Guidelines](./docs/security.md)
- [Troubleshooting FAQ](./docs/faq.md)