# Static Analysis Agent - Production Migration Guide

## Overview

This guide provides step-by-step instructions for migrating your static analysis agent to the production-ready version with enhanced features, proper error handling, and enterprise-grade capabilities.

---

## Key Improvements

### ✅ What's New

1. **Enhanced Error Handling**
   - Comprehensive try-catch blocks in all critical paths
   - Graceful degradation when services are unavailable
   - Detailed error logging with context

2. **Production-Ready Features**
   - Result caching with TTL to avoid duplicate analysis
   - File signature tracking for change detection
   - Dynamic rule management with DB persistence
   - Background task management
   - Comprehensive metrics and statistics

3. **Performance Optimizations**
   - Batch analysis support
   - Concurrent task processing
   - Efficient cache management
   - Minimal memory footprint

4. **Monitoring & Observability**
   - Real-time statistics publishing
   - Performance metrics tracking
   - Cache hit/miss rates
   - Analysis time tracking

5. **Security**
   - Multiple security pattern engines
   - Customizable security rules
   - Severity-based prioritization
   - Compliance checking

---

## Database Schema

### Required Tables

```sql
-- Static Analysis Rules Table
CREATE TABLE IF NOT EXISTS static_analysis_rules (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    pattern TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rules_type ON static_analysis_rules(rule_type);
CREATE INDEX idx_rules_severity ON static_analysis_rules(severity);
CREATE INDEX idx_rules_enabled ON static_analysis_rules(enabled);

-- Static Analysis Results Table
CREATE TABLE IF NOT EXISTS static_analysis_results (
    id VARCHAR(255) PRIMARY KEY,
    target_path TEXT NOT NULL,
    analysis_types JSONB NOT NULL,
    metrics JSONB DEFAULT '{}',
    execution_time_ms FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    summary JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_results_target ON static_analysis_results(target_path);
CREATE INDEX idx_results_timestamp ON static_analysis_results(timestamp DESC);

-- Static Analysis Findings Table
CREATE TABLE IF NOT EXISTS static_analysis_findings (
    id VARCHAR(255) PRIMARY KEY,
    analysis_id VARCHAR(255) NOT NULL REFERENCES static_analysis_results(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    column_number INTEGER,
    rule_id VARCHAR(255),
    confidence FLOAT DEFAULT 1.0,
    remediation TEXT,
    references JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_findings_analysis ON static_analysis_findings(analysis_id);
CREATE INDEX idx_findings_severity ON static_analysis_findings(severity);
CREATE INDEX idx_findings_type ON static_analysis_findings(type);
CREATE INDEX idx_findings_file ON static_analysis_findings(file_path);
```

### Seed Data (Default Rules)

```sql
-- Insert default security rules
INSERT INTO static_analysis_rules (id, name, description, rule_type, severity, pattern, metadata) VALUES
('sec_sql_injection', 'SQL Injection Vulnerability', 'Detects potential SQL injection vulnerabilities', 'security', 'critical', 
 'execute\s*\([^)]*\%[^)]*\)|cursor\.execute\s*\([^)]*\+[^)]*\)',
 '{"remediation": "Use parameterized queries", "references": ["https://owasp.org/www-community/attacks/SQL_Injection"]}'),

('sec_hardcoded_secret', 'Hardcoded Secret', 'Identifies hardcoded passwords or API keys', 'security', 'high',
 '(password|api_key|secret|token)\s*=\s*[''"][^''"]{8,}[''"]',
 '{"remediation": "Use environment variables or secret vaults", "references": ["https://owasp.org/www-project-top-ten/"]}'),

('sec_command_injection', 'Command Injection Risk', 'Detects potential command injection vulnerabilities', 'security', 'critical',
 'os\.system\s*\([^)]*\+[^)]*\)|subprocess\.call\s*\([^)]*\+[^)]*\)',
 '{"remediation": "Avoid concatenating user input in system commands", "references": ["https://owasp.org/www-community/attacks/Command_Injection"]}'),

('sec_eval_usage', 'Dangerous eval() Usage', 'Use of eval() can lead to code injection', 'security', 'high',
 '\beval\s*\(',
 '{"remediation": "Use ast.literal_eval() for safe evaluation", "references": []}'),

('qual_line_length', 'Line Too Long', 'Line exceeds recommended length', 'quality', 'low',
 '^.{89,},
 '{"remediation": "Keep lines under 88 characters", "references": ["https://pep8.org/"]}');
```

---

## Step-by-Step Migration

### Step 1: Backup Current System

```bash
# Backup database
pg_dump -h localhost -U user agentdb > static_analysis_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup current code
cp static_analysis_agent.py static_analysis_agent.py.backup

# Tag current version
git tag -a static-analysis-v1.0 -m "Pre-migration backup"
git push origin static-analysis-v1.0
```

### Step 2: Apply Database Migrations

```bash
# Connect to database
psql -h localhost -U user agentdb

# Run the schema creation script
\i schema/static_analysis_schema.sql

# Verify tables created
\dt static_analysis*

# Verify indexes
\di static_analysis*

# Insert seed data
\i schema/static_analysis_seed.sql
```

### Step 3: Update Dependencies

Ensure your `requirements.txt` includes:

```txt
# Core dependencies (already in base_agent)
nats-py>=2.6.0
asyncpg>=0.29.0
redis>=5.0.0

# Additional for static analysis
# In production, you would install these:
# bandit>=1.7.5
# pylint>=2.17.0
# flake8>=6.0.0
# mypy>=1.4.0
# radon>=6.0.0
# semgrep>=1.30.0
# safety>=2.3.0
```

### Step 4: Update Configuration

Create/update `.env` file:

```env
# Agent Configuration
AGENT_ID=static_analysis_001
AGENT_NAME=static_analysis_agent
AGENT_TYPE=static_analysis
AGENT_VERSION=2.0.0

# Connection URLs
NATS_URL=nats://localhost:4222
POSTGRES_URL=postgresql://user:password@localhost:5432/agentdb
REDIS_URL=redis://localhost:6379

# Static Analysis Specific
ANALYSIS_CACHE_TTL=3600
RULES_REFRESH_INTERVAL=300
MAX_CONCURRENT_TASKS=50

# Performance
REQUEST_TIMEOUT_SECONDS=30
SHUTDOWN_TIMEOUT_SECONDS=30

# Monitoring
STATUS_PUBLISH_INTERVAL=30
HEARTBEAT_INTERVAL=10
LOG_LEVEL=INFO
```

### Step 5: Replace Agent Code

```bash
# Replace with new production-ready version
cp static_analysis_agent_v2.py static_analysis_agent.py

# Review changes
git diff static_analysis_agent.py.backup static_analysis_agent.py
```

### Step 6: Update Tests

Create comprehensive tests:

```python
# tests/test_static_analysis_agent.py
import pytest
import asyncio
from static_analysis_agent import StaticAnalysisAgent, AnalysisType, Severity
from base_agent import AgentConfig

@pytest.fixture
def agent_config():
    return AgentConfig(
        agent_id="test-static-001",
        name="static_analysis_agent",
        agent_type="static_analysis",
        nats_url="nats://localhost:4222",
        postgres_url="postgresql://test:test@localhost:5432/testdb",
        redis_url="redis://localhost:6379",
        status_publish_interval_seconds=0,
        heartbeat_interval_seconds=0
    )

@pytest.mark.asyncio
async def test_security_analysis(agent_config, mock_connections):
    agent = StaticAnalysisAgent(agent_config)
    await agent.start()
    
    code = """
    password = "hardcoded_secret_123"
    query = "SELECT * FROM users WHERE id = " + user_id
    """
    
    result = await agent._analyze_code({
        "source_code": code,
        "file_path": "test.py",
        "analysis_types": [AnalysisType.SECURITY.value]
    })
    
    assert result["status"] == "success"
    assert len(result["findings"]) > 0
    assert any(f["severity"] == "critical" for f in result["findings"])
    
    await agent.stop()

@pytest.mark.asyncio
async def test_quality_analysis(agent_config, mock_connections):
    agent = StaticAnalysisAgent(agent_config)
    await agent.start()
    
    code = """
    def very_long_line_that_exceeds_the_maximum_recommended_length_for_python_code_quality_standards():
        pass
    """
    
    result = await agent._analyze_code({
        "source_code": code,
        "file_path": "test.py",
        "analysis_types": [AnalysisType.QUALITY.value]
    })
    
    assert result["status"] == "success"
    quality_findings = [f for f in result["findings"] if f["type"] == "quality"]
    assert len(quality_findings) > 0
    
    await agent.stop()

@pytest.mark.asyncio
async def test_caching(agent_config, mock_connections):
    agent = StaticAnalysisAgent(agent_config)
    await agent.start()
    
    code = "print('hello world')"
    payload = {
        "source_code": code,
        "file_path": "test.py",
        "analysis_types": [AnalysisType.QUALITY.value]
    }
    
    # First analysis
    result1 = await agent._analyze_code(payload)
    initial_cache_misses = agent.analysis_stats["cache_misses"]
    
    # Second analysis (should hit cache)
    result2 = await agent._analyze_code(payload)
    
    assert agent.analysis_stats["cache_hits"] > 0
    assert result1["analysis_result"]["analysis_id"] != result2["analysis_result"]["analysis_id"]
    
    await agent.stop()

@pytest.mark.asyncio
async def test_rule_management(agent_config, mock_connections):
    agent = StaticAnalysisAgent(agent_config)
    await agent.start()
    
    # Add custom rule
    custom_rule = {
        "id": "custom_test_rule",
        "name": "Test Rule",
        "description": "Test rule description",
        "rule_type": "security",
        "severity": "medium",
        "pattern": r"dangerous_function\(",
        "metadata": {"remediation": "Don't use dangerous_function"}
    }
    
    # This would normally come via NATS message
    agent.static_analysis_rules[custom_rule["id"]] = custom_rule
    
    assert custom_rule["id"] in agent.static_analysis_rules
    
    await agent.stop()

@pytest.mark.asyncio
async def test_batch_analysis(agent_config, mock_connections):
    agent = StaticAnalysisAgent(agent_config)
    await agent.start()
    
    files = [
        {"source_code": "print('file1')", "file_path": "file1.py"},
        {"source_code": "print('file2')", "file_path": "file2.py"},
        {"source_code": "password = 'secret'", "file_path": "file3.py"}
    ]
    
    result = await agent._batch_analysis({
        "files": files,
        "analysis_types": [AnalysisType.SECURITY.value]
    })
    
    assert result["status"] == "success"
    assert result["batch_summary"]["analyzed"] == 3
    assert result["batch_summary"]["total_findings"] > 0
    
    await agent.stop()
```

### Step 7: Deployment

#### Option A: Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  static_analysis_agent:
    build:
      context: .
      dockerfile: Dockerfile
    image: static-analysis-agent:2.0.0
    container_name: static_analysis_agent
    environment:
      - AGENT_ID=static_analysis_001
      - AGENT_NAME=static_analysis_agent
      - AGENT_TYPE=static_analysis
      - NATS_URL=nats://nats:4222
      - POSTGRES_URL=postgresql://user:password@postgres:5432/agentdb
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
      - MAX_CONCURRENT_TASKS=50
    depends_on:
      - nats
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - agent_network
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  agent_network:
    external: true
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY static_analysis_agent.py .
COPY base_agent.py .

# Create log directory
RUN mkdir -p /var/log/agents

# Run agent
CMD ["python", "static_analysis_agent.py"]
```

#### Option B: Kubernetes Deployment

```yaml
# k8s/static-analysis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: static-analysis-agent
  labels:
    app: static-analysis-agent
    version: v2.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: static-analysis-agent
  template:
    metadata:
      labels:
        app: static-analysis-agent
        version: v2.0.0
    spec:
      containers:
      - name: static-analysis-agent
        image: your-registry/static-analysis-agent:2.0.0
        env:
        - name: AGENT_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: AGENT_NAME
          value: "static_analysis_agent"
        - name: NATS_URL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: nats_url
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: postgres_url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: redis_url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import sys; sys.exit(0)"
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "import sys; sys.exit(0)"
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Step 8: Testing in Staging

```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Wait for startup
sleep 30

# Run health check
curl http://localhost:8000/agents/status | jq

# Test security scan
python tests/integration/test_security_scan.py

# Test quality check
python tests/integration/test_quality_check.py

# Monitor logs
docker-compose logs -f static_analysis_agent

# Check metrics
curl http://localhost:8000/static_analysis/stats | jq
```

### Step 9: Production Rollout

```bash
# Blue-Green Deployment
# 1. Deploy new version alongside old
kubectl apply -f k8s/static-analysis-deployment-v2.yaml

# 2. Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=static-analysis-agent,version=v2.0.0 --timeout=120s

# 3. Gradually shift traffic (if using service mesh)
kubectl patch service static-analysis-agent -p '{"spec":{"selector":{"version":"v2.0.0"}}}'

# 4. Monitor for issues
kubectl logs -f -l app=static-analysis-agent,version=v2.0.0

# 5. If successful, scale down old version
kubectl scale deployment static-analysis-agent-v1 --replicas=0

# 6. If issues, rollback
kubectl patch service static-analysis-agent -p '{"spec":{"selector":{"version":"v1.0.0"}}}'
```

---

## Post-Migration Validation

### Functional Testing

```python
# test_production_readiness.py
import asyncio
import json
from nats.aio.client import Client as NATS

async def test_static_analysis():
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    
    # Test security scan
    test_code = """
    password = "hardcoded_secret"
    query = f"SELECT * FROM users WHERE id = {user_id}"
    """
    
    request = {
        "task_type": "security_scan",
        "payload": {
            "source_code": test_code,
            "file_path": "test.py"
        }
    }
    
    response = await nc.request(
        "agent.static_analysis_agent.task",
        json.dumps(request).encode(),
        timeout=10
    )
    
    result = json.loads(response.data.decode())
    print("Security Scan Result:")
    print(json.dumps(result, indent=2))
    
    assert result["status"] == "success"
    assert len(result["findings"]) > 0
    
    await nc.close()

if __name__ == "__main__":
    asyncio.run(test_static_analysis())
```

### Performance Testing

```python
# load_test.py
import asyncio
import time
import json
from nats.aio.client import Client as NATS

async def load_test():
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    
    test_code = "def hello(): print('world')"
    
    tasks = []
    start_time = time.time()
    
    for i in range(100):
        request = {
            "task_type": "analyze_code",
            "payload": {
                "source_code": test_code,
                "file_path": f"test_{i}.py",
                "analysis_types": ["security", "quality"]
            }
        }
        
        task = nc.request(
            "agent.static_analysis_agent.task",
            json.dumps(request).encode(),
            timeout=30
        )
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = time.time() - start_time
    successful = sum(1 for r in responses if not isinstance(r, Exception))
    
    print(f"\nLoad Test Results:")
    print(f"Total Requests: 100")
    print(f"Successful: {successful}")
    print(f"Failed: {100 - successful}")
    print(f"Total Time: {elapsed:.2f}s")
    print(f"Throughput: {successful/elapsed:.2f} req/s")
    
    await nc.close()

if __name__ == "__main__":
    asyncio.run(load_test())
```

### Monitoring Checklist

- [ ] Agent successfully connects to NATS
- [ ] Database connections established
- [ ] Redis connection active
- [ ] Rules loaded from database
- [ ] Heartbeat signals publishing
- [ ] Status updates working
- [ ] Analysis requests processing
- [ ] Cache working correctly
- [ ] Background tasks running
- [ ] No memory leaks after 24h
- [ ] Error rate < 0.1%
- [ ] P95 response time < 500ms
- [ ] P99 response time < 2000ms

---

## Troubleshooting

### Issue: Agent Won't Start

**Symptoms:**
- Agent exits immediately
- Connection errors in logs

**Solutions:**
```bash
# Check service availability
nc -zv localhost 4222  # NATS
nc -zv localhost 5432  # PostgreSQL
nc -zv localhost 6379  # Redis

# Check logs
docker-compose logs static_analysis_agent

# Verify configuration
python -c "from static_analysis_agent import StaticAnalysisAgent; print('OK')"
```

### Issue: Rules Not Loading

**Symptoms:**
- "No rules loaded" in logs
- Default rules being used

**Solutions:**
```bash
# Check database connection
psql -h localhost -U user agentdb -c "SELECT COUNT(*) FROM static_analysis_rules;"

# Verify rule table
psql -h localhost -U user agentdb -c "\d static_analysis_rules"

# Manual rule check
python -c "
import asyncio
from static_analysis_agent import StaticAnalysisAgent
from base_agent import AgentConfig

async def check():
    config = AgentConfig(
        agent_id='test',
        name='static_analysis_agent',
        agent_type='static_analysis',
        nats_url='nats://localhost:4222',
        postgres_url='postgresql://user:password@localhost:5432/agentdb'
    )
    agent = StaticAnalysisAgent(config)
    await agent._load_rules_from_db()
    print(f'Rules loaded: {len(agent.static_analysis_rules)}')

asyncio.run(check())
"
```

### Issue: High Memory Usage

**Symptoms:**
- Memory grows over time
- OOM errors

**Solutions:**
```python
# Reduce cache TTL
ANALYSIS_CACHE_TTL=1800  # 30 minutes instead of 1 hour

# Limit cache size
# Add to agent.__init__:
self.max_cache_size = 1000

# Modify cache insertion:
if len(self.analysis_cache) >= self.max_cache_size:
    # Remove oldest entry
    oldest_key = min(self.analysis_cache.keys(), 
                     key=lambda k: self.analysis_cache[k].timestamp)
    del self.analysis_cache[oldest_key]
```

### Issue: Slow Analysis

**Symptoms:**
- Analysis takes too long
- Timeout errors

**Solutions:**
```python
# Increase timeout
REQUEST_TIMEOUT_SECONDS=60

# Enable parallel processing
MAX_CONCURRENT_TASKS=100

# Use caching
# Ensure force_refresh=False in requests

# Optimize patterns
# Simplify complex regex patterns in rules
```

---

## Rollback Procedure

If issues arise, follow this rollback procedure:

```bash
# 1. Stop new version
kubectl scale deployment static-analysis-agent-v2 --replicas=0

# 2. Scale up old version
kubectl scale deployment static-analysis-agent-v1 --replicas=3

# 3. Restore database if needed
psql -h localhost -U user agentdb < static_analysis_backup_TIMESTAMP.sql

# 4. Verify old version working
curl http://localhost:8000/agents/status

# 5. Investigate issues
kubectl logs -l app=static-analysis-agent,version=v2.0.0 --tail=1000
```

---

## Success Criteria

### Technical Metrics
- ✅ All unit tests passing (>90% coverage)
- ✅ Integration tests passing
- ✅ Load tests meeting SLAs (>50 req/s)
- ✅ Memory usage stable after 24h
- ✅ No connection leaks
- ✅ Error rate < 0.1%
- ✅ Cache hit rate > 60%
- ✅ P95 response time < 500ms

### Operational Metrics
- ✅ Zero-downtime deployment
- ✅ Monitoring dashboards updated
- ✅ Alerts configured
- ✅ Documentation complete
- ✅ Team trained
- ✅ 48h production stability

---

## Best Practices

### Rule Management

1. **Regular Rule Updates**
   - Review and update rules monthly
   - Add rules for new vulnerability types
   - Disable outdated rules

2. **Custom Rules**
   - Document custom rules thoroughly
   - Test rules before enabling in production
   - Set appropriate severity levels

3. **Performance**
   - Keep patterns simple and efficient
   - Avoid overly broad patterns
   - Test pattern performance

### Caching Strategy

1. **Cache Configuration**
   - Set TTL based on code change frequency
   - Monitor cache hit rates
   - Adjust cache size limits

2. **Cache Invalidation**
   - Clear cache when rules change
   - Implement selective cache invalidation
   - Monitor cache effectiveness

### Monitoring

1. **Key Metrics**
   - Analysis throughput
   - Finding severity distribution
   - Cache performance
   - Error rates

2. **Alerting**
   - High error rates
   - Memory leaks
   - Service unavailability
   - Analysis failures

---

## Support Resources

- Documentation: `/docs/static-analysis-agent.md`
- API Reference: `/docs/api/static-analysis.md`
- Troubleshooting Guide: This document
- Team Contact: devops@company.com