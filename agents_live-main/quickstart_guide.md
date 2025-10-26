# Coding Agent - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd coding-agent

# 2. Create environment file
cp .env.example .env

# 3. Start all services
make start

# 4. Wait for services to be ready (30-60 seconds)
make status

# 5. Run tests
make test
```

That's it! The agent is now running and ready to execute code.

### Option 2: Manual Setup

```bash
# 1. Install system dependencies
sudo apt-get update
sudo apt-get install -y postgresql redis-server nodejs npm

# 2. Install Python dependencies
pip install nats-py asyncpg redis

# 3. Start NATS
nats-server -js &

# 4. Configure PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE agentdb;"
sudo -u postgres psql -c "CREATE USER agentuser WITH PASSWORD 'changeme123';"
sudo -u postgres psql agentdb < init-db.sql

# 5. Start services
sudo systemctl start postgresql
sudo systemctl start redis

# 6. Run the agent
python coding_agent.py
```

---

## 📋 File Structure

```
coding-agent/
├── enhanced_base_agent.py      # Base agent framework
├── coding_agent.py             # Coding agent implementation
├── test_client.py              # Test suite and examples
├── docker-compose.yml          # Docker setup
├── Dockerfile                  # Container image
├── k8s-deployment.yaml         # Kubernetes manifests
├── requirements.txt            # Python dependencies
├── init-db.sql                 # Database schema
├── prometheus.yml              # Metrics configuration
├── Makefile                    # Convenience commands
├── .env.example                # Environment template
└── README.md                   # Documentation
```

---

## 🧪 Quick Test Examples

### Test 1: Execute Python Code

```python
import asyncio
import json
import nats

async def test_python():
    nc = await nats.connect("nats://localhost:4222")
    
    task = {
        "task_id": "test-001",
        "task_type": "execute_code",
        "payload": {
            "code": "print('Hello from Coding Agent!')",
            "language": "python"
        }
    }
    
    response = await nc.request(
        "agent.coding_agent.task",
        json.dumps(task).encode(),
        timeout=10
    )
    
    result = json.loads(response.data.decode())
    print(json.dumps(result, indent=2))
    
    await nc.close()

asyncio.run(test_python())
```

### Test 2: Using the Test Client

```bash
# Run all tests
python test_client.py

# Run interactive demo
python test_client.py demo
```

### Test 3: Quick Health Check

```python
import asyncio
from test_client import CodingAgentClient

async def health_check():
    client = CodingAgentClient()
    await client.connect()
    
    health = await client.get_health()
    status = await client.get_status()
    
    print(f"Health: {health['status']}")
    print(f"State: {status['state']}")
    print(f"Uptime: {status['uptime_seconds']:.1f}s")
    print(f"Total Executions: {status['coding_metrics']['total_executions']}")
    
    await client.disconnect()

asyncio.run(health_check())
```

---

## 📊 Monitoring

### View Agent Status

```bash
# Using make
make status

# Using Docker
docker-compose logs -f coding-agent

# Using NATS
nats request agent.coding_agent.status '{}'
```

### Check Metrics

```bash
# Agent metrics
curl http://localhost:8222/varz  # NATS metrics

# With monitoring stack
docker-compose --profile monitoring up -d
# Visit http://localhost:3000 (Grafana)
# Visit http://localhost:9090 (Prometheus)
```

### Database Queries

```sql
-- Recent executions
SELECT execution_id, language, status, execution_time_ms, created_at
FROM code_executions
ORDER BY created_at DESC
LIMIT 10;

-- Success rate by language
SELECT 
    language,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM code_executions
GROUP BY language;

-- Average execution time by language
SELECT 
    language,
    ROUND(AVG(execution_time_ms), 2) as avg_time_ms,
    ROUND(MIN(execution_time_ms), 2) as min_time_ms,
    ROUND(MAX(execution_time_ms), 2) as max_time_ms
FROM code_executions
WHERE status = 'success'
GROUP BY language;
```

---

## 🔧 Configuration Examples

### High-Throughput Configuration

```python
config = AgentConfig(
    # ... other settings ...
    max_concurrent_tasks=100,
    postgres_max_pool_size=50,
    redis_max_connections=100,
    circuit_breaker_failure_threshold=10,
    config_data={
        'cache_ttl_seconds': 7200,
        'default_timeout_seconds': 60,
        'max_timeout_seconds': 600,
        'max_memory_mb': 4096
    }
)
```

### Security-Focused Configuration

```python
config = AgentConfig(
    # ... other settings ...
    config_data={
        'enable_caching': False,  # No caching for sensitive code
        'default_timeout_seconds': 15,
        'max_timeout_seconds': 30,
        'default_memory_mb': 256,
        'max_memory_mb': 512
    }
)
```

### Development Configuration

```python
config = AgentConfig(
    # ... other settings ...
    log_level="DEBUG",
    log_format="text",
    config_data={
        'cache_ttl_seconds': 300,  # 5 minutes
        'default_timeout_seconds': 60,
        'max_timeout_seconds': 120
    }
)
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Agent won't start

```bash
# Check services
docker-compose ps

# View logs
docker-compose logs coding-agent

# Check dependencies
docker-compose logs nats
docker-compose logs postgres
docker-compose logs redis
```

#### 2. Connection refused

```bash
# Verify NATS is running
nats server list

# Test PostgreSQL
psql -h localhost -U agentuser -d agentdb

# Test Redis
redis-cli ping
```

#### 3. Code execution fails

```bash
# Check Node.js installation
node --version

# Check Python version
python --version

# View execution logs in database
psql -U agentuser -d agentdb -c "SELECT * FROM code_execution_logs ORDER BY created_at DESC LIMIT 5;"
```

#### 4. Performance issues

```bash
# Check resource usage
docker stats

# View agent metrics
python -c "
import asyncio
from test_client import CodingAgentClient

async def metrics():
    client = CodingAgentClient()
    await client.connect()
    status = await client.get_status()
    metrics = status['coding_metrics']
    print(f\"Avg Execution Time: {metrics['avg_execution_time_ms']:.2f}ms\")
    print(f\"Cache Hit Rate: {metrics['cache_hits']/(metrics['cache_hits']+metrics['cache_misses'])*100:.1f}%\")
    await client.disconnect()

asyncio.run(metrics())
"
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export LOG_FORMAT=text
python coding_agent.py
```

---

## 📦 Production Deployment

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml coding-agent

# Scale agents
docker service scale coding-agent_coding-agent=5

# View services
docker service ls
```

### Kubernetes

```bash
# Deploy to K8s
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods -n coding-agent

# Scale deployment
kubectl scale deployment coding-agent --replicas=5 -n coding-agent

# View logs
kubectl logs -f deployment/coding-agent -n coding-agent
```

### AWS ECS

```bash
# Create task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
    --cluster coding-agent-cluster \
    --service-name coding-agent \
    --task-definition coding-agent:1 \
    --desired-count 3
```

---

## 🔒 Security Checklist

- [ ] Change default passwords
- [ ] Enable TLS for all connections
- [ ] Configure firewall rules
- [ ] Enable SELinux/AppArmor
- [ ] Set resource limits
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Network isolation for code execution
- [ ] Implement rate limiting
- [ ] Monitor for suspicious activity

---

## 📈 Performance Tuning

### Database Optimization

```