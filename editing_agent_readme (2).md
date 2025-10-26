# Editing Agent v2.0 - Production Ready

## 📋 Overview

The Editing Agent v2.0 is a fully upgraded, production-ready agent built on the enhanced BaseAgent framework. It provides comprehensive content editing, analysis, and collaborative features with enterprise-grade reliability.

## ✨ Key Features

### Core Capabilities
- ✅ **Grammar & Spelling**: Advanced checking using LanguageTool
- ✅ **Content Analysis**: Readability, sentiment, tone analysis
- ✅ **Style Improvement**: AI-powered content enhancement
- ✅ **Collaborative Editing**: Real-time multi-user editing
- ✅ **Version Control**: Complete history tracking and rollback
- ✅ **Multi-format Support**: Articles, emails, reports, marketing copy

### Production Features (from BaseAgent v2.0)
- ✅ **Resilient Connections**: Auto-reconnection with exponential backoff
- ✅ **Circuit Breakers**: Automatic failure detection and recovery
- ✅ **Connection Pooling**: Optimized database connection management
- ✅ **Health Monitoring**: Comprehensive health checks and status reporting
- ✅ **Graceful Shutdown**: Clean resource cleanup with timeout handling
- ✅ **Metrics & Observability**: Detailed performance metrics
- ✅ **Error Handling**: Structured error reporting and recovery
- ✅ **Rate Limiting**: Concurrent task management with semaphores

## 🚀 Quick Start

### Prerequisites

```bash
# System requirements
- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 15+
- NATS Server 2.10+
- Redis 7+

# Or use the provided docker-compose setup
```

### Installation

1. **Clone and Setup**
```bash
git clone <repository>
cd editing-agent
```

2. **Install Dependencies**
```bash
pip install -r requirements_editing.txt
python -m spacy download en_core_web_sm
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Initialize Database**
```bash
# Using Docker Compose (recommended)
docker-compose up -d postgres
sleep 10  # Wait for PostgreSQL to be ready

# Initialize schema
docker-compose exec postgres psql -U agent -d agentdb -f /docker-entrypoint-initdb.d/01_init.sql
```

5. **Start the Agent**
```bash
# Local development
python editing_agent.py

# Or with Docker
docker-compose up -d editing_agent

# With full monitoring stack
docker-compose --profile monitoring up -d
```

## 📊 Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────┐
│                  Client Applications                 │
└───────────────┬─────────────────────────────────────┘
                │
                │ NATS Messages
                ▼
┌─────────────────────────────────────────────────────┐
│              Editing Agent v2.0                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  BaseAgent Core (Enhanced)                   │   │
│  │  - Connection Management                     │   │
│  │  - Health Monitoring                         │   │
│  │  - Task Processing                           │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  Editing Features                            │   │
│  │  - Grammar Checking (LanguageTool)           │   │
│  │  - Content Analysis (spaCy, NLTK)            │   │
│  │  - Collaborative Editing                     │   │
│  │  - Version Control                           │   │
│  └──────────────────────────────────────────────┘   │
└─────┬───────────────┬──────────────┬────────────────┘
      │               │              │
      │ PostgreSQL    │ NATS         │ Redis
      ▼               ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Database │   │Messaging │   │  Cache   │
│ - Sessions│  │- Events  │   │ - State  │
│ - History│   │- Tasks   │   │          │
└──────────┘   └──────────┘   └──────────┘
```

### Component Flow
```
1. Client Request → NATS → Editing Agent
2. Task Processing → Language Tools (Grammar, NLP)
3. Analysis Results → Database Storage
4. Suggestions Generated → Returned to Client
5. Edit Application → Version Control → Database
6. Collaborative Events → Real-time Broadcasting
```

## 🔧 Configuration

### Environment Variables

```bash
# Core Agent Settings
AGENT_ID=editing-001                    # Unique agent identifier
AGENT_NAME=editing_agent                # Agent name (snake_case)
AGENT_TYPE=editing                      # Agent type
AGENT_VERSION=2.0.0                     # Version

# Connection URLs
NATS_URL=nats://localhost:4222
POSTGRES_URL=postgresql://user:pass@localhost:5432/agentdb
REDIS_URL=redis://localhost:6379

# Performance Tuning
MAX_CONCURRENT_TASKS=100                # Max parallel tasks
REQUEST_TIMEOUT_SECONDS=30              # Request timeout
SHUTDOWN_TIMEOUT_SECONDS=30             # Graceful shutdown timeout

# Database Connection Pool
POSTGRES_MIN_POOL_SIZE=5                # Minimum pool connections
POSTGRES_MAX_POOL_SIZE=20               # Maximum pool connections
POSTGRES_COMMAND_TIMEOUT=60             # Query timeout

# NATS Settings
NATS_MAX_RECONNECT_ATTEMPTS=-1          # -1 for infinite
NATS_RECONNECT_TIME_WAIT=2              # Seconds between reconnects
NATS_PING_INTERVAL=20                   # Ping interval

# Monitoring
STATUS_PUBLISH_INTERVAL=30              # Status update interval
HEARTBEAT_INTERVAL=10                   # Heartbeat interval
METRICS_COLLECTION_INTERVAL=60          # Metrics collection

# Editing-Specific
SESSION_TIMEOUT_HOURS=24                # Session idle timeout
ANALYSIS_INTERVAL_SECONDS=60            # Re-analysis interval
MAX_CONTENT_LENGTH=100000               # Max content size

# Logging
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/var/log/agents/editing.log   # Log file path
```

## 💻 Usage Examples

### Python Client

```python
import asyncio
import nats
import json

async def edit_document():
    nc = await nats.connect("nats://localhost:4222")
    
    # 1. Start editing session
    request = {
        "task_id": "edit-123",
        "task_type": "start_editing_session",
        "payload": {
            "document_id": "doc-456",
            "user_id": "user-789",
            "content": "This is my document with some errrors and poor style.",
            "content_type": "article",
            "editing_mode": "moderate"
        },
        "priority": "high"
    }
    
    response = await nc.request(
        "agent.editing_agent.task",
        json.dumps(request).encode(),
        timeout=10
    )
    
    result = json.loads(response.data.decode())
    session_id = result["result"]["session_id"]
    
    print(f"Session created: {session_id}")
    print(f"Readability score: {result['result']['content_analysis']['readability']['score']}")
    print(f"Suggestions: {len(result['result']['initial_suggestions'])}")
    
    # 2. Apply first 3 suggestions
    if result['result']['initial_suggestions']:
        edit_ids = [s['id'] for s in result['result']['initial_suggestions'][:3]]
        
        apply_request = {
            "task_id": "apply-123",
            "task_type": "apply_edits",
            "payload": {
                "session_id": session_id,
                "edit_ids": edit_ids
            },
            "priority": "high"
        }
        
        apply_response = await nc.request(
            "agent.editing_agent.task",
            json.dumps(apply_request).encode(),
            timeout=10
        )
        
        apply_result = json.loads(apply_response.data.decode())
        print(f"Applied {apply_result['result']['applied_count']} edits")
    
    # 3. Save version
    version_request = {
        "task_id": "version-123",
        "task_type": "version_control",
        "payload": {
            "session_id": session_id,
            "operation": "save_version",
            "message": "First revision"
        },
        "priority": "medium"
    }
    
    await nc.request(
        "agent.editing_agent.task",
        json.dumps(version_request).encode(),
        timeout=5
    )
    
    print("Version saved")
    
    await nc.close()

asyncio.run(edit_document())
```

### REST API Integration (via Gateway)

```python
import requests

# Start editing session
response = requests.post(
    "http://api-gateway:8000/editing/sessions",
    json={
        "document_id": "doc-123",
        "content": "Content to edit...",
        "content_type": "article",
        "editing_mode": "moderate"
    }
)

session = response.json()
session_id = session["session_id"]

# Get suggestions
suggestions = requests.get(
    f"http://api-gateway:8000/editing/sessions/{session_id}/suggestions"
).json()

# Apply edits
requests.post(
    f"http://api-gateway:8000/editing/sessions/{session_id}/apply",
    json={"edit_ids": [suggestions[0]["id"]]}
)

# Get updated content
result = requests.get(
    f"http://api-gateway:8000/editing/sessions/{session_id}"
).json()

print(result["current_content"])
```

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest test_editing_agent.py -v

# Specific test class
pytest test_editing_agent.py::TestContentAnalysis -v

# With coverage
pytest test_editing_agent.py --cov=editing_agent --cov-report=html

# Integration tests only
pytest test_editing_agent.py::TestIntegration -v
```

### Load Testing

```python
# load_test.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def test_load():
    """Test with 1000 concurrent sessions"""
    tasks = []
    
    for i in range(1000):
        task = create_editing_session(f"test-{i}")
        tasks.append(task)
    
    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start
    
    successes = sum(1 for r in results if not isinstance(r, Exception))
    
    print(f"Completed {successes}/1000 sessions in {duration:.2f}s")
    print(f"Throughput: {successes/duration:.2f} sessions/second")

asyncio.run(test_load())
```

## 📈 Monitoring & Observability

### Health Check

```bash
# Check agent health
curl http://localhost:8080/health | jq

# Check via NATS
nats req agent.editing_agent.health "" | jq
```

### Metrics

```bash
# Get agent metrics
curl http://localhost:8080/metrics | jq

# Prometheus metrics (if enabled)
curl http://localhost:9090/api/v1/query?query=agent_tasks_completed
```

### Database Queries

```sql
-- Active sessions
SELECT * FROM v_active_sessions;

-- Session performance
SELECT * FROM v_session_performance 
WHERE date >= CURRENT_DATE - INTERVAL '7 days';

-- Agent health
SELECT * FROM v_agent_health;

-- Session statistics
SELECT * FROM get_session_stats(
    NOW() - INTERVAL '30 days',
    NOW()
);
```

### Log Analysis

```bash
# Follow logs
docker-compose logs -f editing_agent

# Search for errors
docker-compose logs editing_agent | grep ERROR

# Analyze performance
docker-compose logs editing_agent | grep "processing_time"

# Check session creation
docker-compose logs editing_agent | grep "Editing session started"
```

## 🔄 Migration from v1.0

### Step-by-Step Migration

#### 1. Backup Current System

```bash
# Backup database
pg_dump -h localhost -U agent agentdb > backup_$(date +%Y%m%d).sql

# Backup configuration
tar -czf config_backup.tar.gz *.py *.env

# Tag current version
git tag -a v1.0.0 -m "Pre-upgrade backup"
```

#### 2. Update Dependencies

```bash
# Update requirements
pip install -r requirements_editing.txt

# Download new models
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"
```

#### 3. Database Migration

```sql
-- Run migration script
psql -h localhost -U agent agentdb < init-db/01_init.sql

-- Verify tables
\dt

-- Check indexes
\di
```

#### 4. Update Agent Code

**Old Code (v1.0):**
```python
class EditingAgent:
    def __init__(self, config):
        self.config = config
        self.nc = None
        self.db_pool = None
    
    async def start(self):
        self.nc = await nats.connect(self.config.nats_url)
        self.db_pool = await asyncpg.create_pool(self.config.postgres_url)
```

**New Code (v2.0):**
```python
class EditingAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        # Connections handled by BaseAgent
    
    async def _setup_subscriptions(self):
        await super()._setup_subscriptions()
        # Add custom subscriptions
```

#### 5. Update Task Handling

**Old:**
```python
async def handle_message(self, msg):
    data = json.loads(msg.data.decode())
    # Process directly
```

**New:**
```python
async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
    if task_request.task_type == "analyze_content":
        return await self._analyze_content(task_request.payload)
    return await super()._handle_task(task_request)
```

#### 6. Deploy New Version

```bash
# Build new image
docker build -t editing-agent:2.0 -f Dockerfile.editing .

# Update docker-compose
docker-compose up -d editing_agent

# Verify deployment
docker-compose ps
docker-compose logs editing_agent | tail -50
```

#### 7. Validate Migration

```bash
# Run health check
curl http://localhost:8080/health

# Check metrics
curl http://localhost:8080/metrics

# Test basic functionality
python -c "
import asyncio
import nats
import json

async def test():
    nc = await nats.connect('nats://localhost:4222')
    response = await nc.request(
        'agent.editing_agent.task',
        json.dumps({
            'task_id': 'test-001',
            'task_type': 'analyze_content',
            'payload': {'content': 'Test content'},
            'priority': 'medium'
        }).encode(),
        timeout=5
    )
    print(json.loads(response.data.decode()))
    await nc.close()

asyncio.run(test())
"
```

### Rollback Plan

If issues occur:

```bash
# Stop new version
docker-compose down

# Restore database
psql -h localhost -U agent agentdb < backup_YYYYMMDD.sql

# Revert to old version
git checkout v1.0.0
docker-compose up -d

# Verify
curl http://localhost:8080/health
```

## 🔒 Security Best Practices

### Network Security

```yaml
# docker-compose.yml security additions
services:
  editing_agent:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

### Secrets Management

```bash
# Use Docker secrets
echo "db_password" | docker secret create postgres_password -

# Update compose file
services:
  editing_agent:
    secrets:
      - postgres_password
    environment:
      - POSTGRES_URL=postgresql://agent:$(cat /run/secrets/postgres_password)@postgres:5432/agentdb

secrets:
  postgres_password:
    external: true
```

### Database Security

```sql
-- Create limited user
CREATE USER editing_agent WITH PASSWORD 'secure_password';

-- Grant minimal permissions
GRANT CONNECT ON DATABASE agentdb TO editing_agent;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO editing_agent;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO editing_agent;

-- Row-level security
ALTER TABLE editing_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_sessions ON editing_sessions
    FOR ALL TO editing_agent
    USING (user_id = current_setting('app.current_user_id'));
```

## 🐛 Troubleshooting

### Common Issues

#### Agent Won't Start

```bash
# Check logs
docker-compose logs editing_agent

# Common causes:
# 1. Database not ready
docker-compose ps postgres
docker-compose logs postgres | grep "ready to accept connections"

# 2. NATS not available
docker-compose ps nats
nc -zv localhost 4222

# 3. Missing dependencies
docker-compose exec editing_agent pip list | grep spacy

# Solution: Wait for dependencies
docker-compose up -d postgres nats redis
sleep 30
docker-compose up -d editing_agent
```

#### High Memory Usage

```bash
# Check memory
docker stats editing_agent

# Solutions:
# 1. Reduce concurrent tasks
export MAX_CONCURRENT_TASKS=50

# 2. Increase container memory limit
docker-compose up -d --scale editing_agent=1 \
  --memory="4g" editing_agent

# 3. Clear old sessions
docker-compose exec postgres psql -U agent -d agentdb \
  -c "SELECT archive_old_sessions(1);"
```

#### Connection Timeouts

```bash
# Check connection pool
SELECT * FROM v_agent_health;

# Increase pool size
export POSTGRES_MAX_POOL_SIZE=50

# Increase timeouts
export REQUEST_TIMEOUT_SECONDS=60
export POSTGRES_COMMAND_TIMEOUT=120
```

#### Grammar Tool Issues

```python
# Reinstall language-tool-python
pip install --upgrade language-tool-python

# Or use online API
export LANGUAGE_TOOL_API=https://api.languagetool.org/v2/
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug
python editing_agent.py

# Or in Docker
docker-compose up editing_agent
docker-compose logs -f editing_agent
```

## 📦 Production Deployment

### Kubernetes Deployment

```yaml
# k8s/editing-agent-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: editing-agent
  namespace: agents
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: editing-agent
  template:
    metadata:
      labels:
        app: editing-agent
        version: v2.0
    spec:
      containers:
      - name: editing-agent
        image: registry.example.com/editing-agent:2.0
        imagePullPolicy: Always
        env:
        - name: AGENT_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: postgres_url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: editing-agent-service
  namespace: agents
spec:
  selector:
    app: editing-agent
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: editing-agent-hpa
  namespace: agents
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: editing-agent
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Monitoring Stack

```yaml
# Prometheus monitoring
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    
    scrape_configs:
    - job_name: 'editing-agent'
      static_configs:
      - targets: ['editing-agent-service:8080']
      metrics_path: /metrics
```

## 📚 API Reference

### Task Types

| Task Type | Description | Payload | Response |
|-----------|-------------|---------|----------|
| `start_editing_session` | Create new session | `content`, `content_type`, `editing_mode` | Session ID, analysis, suggestions |
| `analyze_content` | Analyze content | `content`, `content_type` | Analysis results |
| `generate_suggestions` | Get edit suggestions | `session_id` or `content` | List of suggestions |
| `apply_edits` | Apply suggestions | `session_id`, `edit_ids` | Updated content |
| `check_grammar` | Grammar check only | `content` | Grammar issues |
| `improve_style` | Style improvement | `content`, `style_guide` | Improved content |
| `optimize_readability` | Readability optimization | `content`, `target_grade_level` | Optimized content |
| `collaborative_edit` | Real-time edit | `session_id`, `change_type`, `text` | Updated content |
| `version_control` | Manage versions | `session_id`, `operation` | Version info |
| `get_session_status` | Session info | `session_id` | Session details |
| `close_session` | Close session | `session_id` | Final content |

### Content Types

- `article` - Blog posts, articles
- `email` - Email messages  
- `proposal` - Business proposals
- `report` - Reports and documents
- `creative` - Creative writing
- `technical` - Technical documentation
- `marketing` - Marketing copy
- `academic` - Academic papers

### Editing Modes

- `light` - Grammar and spelling only
- `moderate` - Grammar + clarity improvements
- `heavy` - Significant restructuring
- `collaborative` - Track changes mode

## 🎯 Performance Tuning

### Optimization Tips

```bash
# 1. Increase connection pools
export POSTGRES_MAX_POOL_SIZE=50
export MAX_CONCURRENT_TASKS=200

# 2. Enable caching
export REDIS_CACHE_ENABLED=true
export CACHE_TTL_SECONDS=300

# 3. Batch processing
export BATCH_SIZE=50
export BATCH_TIMEOUT_SECONDS=5

# 4. Async processing
export ASYNC_PROCESSING=true
export WORKER_THREADS=4
```

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_sessions_user_updated 
ON editing_sessions(user_id, updated_at DESC);

-- Vacuum regularly
VACUUM ANALYZE editing_sessions;

-- Update statistics
ANALYZE editing_sessions;

-- Partition large tables
SELECT create_monthly_partitions('editing_sessions_archive', 12);
```

## 📞 Support

### Resources

- Documentation: [docs.example.com/editing-agent](https://docs.example.com)
- Issues: [github.com/yourorg/editing-agent/issues](https://github.com)
- Slack: #editing-agent-support

### Getting Help

1. Check logs: `docker-compose logs editing_agent`
2. Review documentation
3. Search existing issues
4. Create detailed bug report with:
   - Environment details
   - Error messages
   - Steps to reproduce
   - Expected vs actual behavior

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ Agent starts and connects to all services
- ✅ Health checks pass consistently
- ✅ Sessions can be created and managed
- ✅ Grammar checking works correctly
- ✅ Content analysis returns results
- ✅ Edits can be applied successfully
- ✅ Metrics are being collected
- ✅ No memory leaks after 24h
- ✅ Response times < 100ms (P95)
- ✅ Error rate < 0.1%

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built on:
- BaseAgent v2.0 framework
- LanguageTool for grammar checking
- spaCy for NLP analysis
- NLTK for sentiment analysis
- NATS for messaging
- PostgreSQL for persistence

---

**Version:** 2.0.0  
**Last Updated:** 2024-01-09  
**Status:** Production Ready ✅