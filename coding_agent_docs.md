# Coding Agent Documentation

## Overview

The **Coding Agent** is a production-ready, secure code execution service built on the Enhanced Base Agent framework. It provides safe, isolated code execution across multiple programming languages with comprehensive monitoring, caching, and security features.

## Key Features

### 🔒 Security
- **Code validation and sanitization** before execution
- **Sandboxed execution** with resource limits
- **Security pattern detection** for dangerous operations
- **Optional network and filesystem restrictions**
- **Resource limits** (CPU, memory, processes)

### 🚀 Performance
- **Redis caching** for repeated executions
- **Concurrent task handling** with semaphore control
- **Circuit breakers** for fault tolerance
- **Exponential backoff** retry logic

### 📊 Monitoring
- **Comprehensive metrics** tracking
- **Execution history** in PostgreSQL
- **Health checks** and status reporting
- **Distributed tracing** with correlation IDs

### 🌐 Multi-Language Support
- Python
- JavaScript (Node.js)
- Bash
- SQL (with database connection)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Coding Agent                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Security   │  │    Code      │  │    Cache     │  │
│  │  Validator   │→ │  Executor    │→ │   Manager    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │          │
│         ↓                  ↓                  ↓          │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Enhanced Base Agent                      │  │
│  │  • NATS Messaging  • Circuit Breakers            │  │
│  │  • PostgreSQL      • Health Monitoring           │  │
│  │  • Redis           • Graceful Shutdown           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

```bash
# Python dependencies
pip install nats-py asyncpg redis

# System dependencies
# Node.js (for JavaScript execution)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# PostgreSQL
sudo apt-get install -y postgresql postgresql-contrib

# Redis
sudo apt-get install -y redis-server

# NATS Server
wget https://github.com/nats-io/nats-server/releases/latest/download/nats-server-linux-amd64.zip
unzip nats-server-linux-amd64.zip
sudo mv nats-server /usr/local/bin/
```

### Setup

```bash
# Clone or download the agent files
git clone <repository>
cd coding-agent

# Install Python dependencies
pip install -r requirements.txt

# Start services
sudo systemctl start postgresql
sudo systemctl start redis
nats-server &

# Initialize database
psql -U postgres -c "CREATE DATABASE agentdb;"
psql -U postgres -c "CREATE USER user WITH PASSWORD 'password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE agentdb TO user;"
```

---

## Configuration

### Basic Configuration

```python
from enhanced_base_agent import AgentConfig
from coding_agent import CodingAgent

config = AgentConfig(
    agent_id="coding-001",
    name="coding_agent",
    agent_type="coding",
    version="1.0.0",
    
    # Connections
    nats_url="nats://localhost:4222",
    postgres_url="postgresql://user:password@localhost:5432/agentdb",
    redis_url="redis://localhost:6379",
    
    # Performance tuning
    max_concurrent_tasks=50,
    request_timeout_seconds=30.0,
    
    # Coding-specific settings
    config_data={
        'cache_ttl_seconds': 3600,
        'enable_caching': True,
        'default_timeout_seconds': 30,
        'max_timeout_seconds': 300,
        'default_memory_mb': 512,
        'max_memory_mb': 2048
    }
)
```

### Advanced Configuration

```python
config = AgentConfig(
    # ... basic config ...
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold=5,
    circuit_breaker_timeout_seconds=60,
    circuit_breaker_half_open_max_calls=3,
    
    # Retry settings
    max_retry_attempts=3,
    retry_base_delay_seconds=1.0,
    retry_max_delay_seconds=60.0,
    
    # Health monitoring
    status_publish_interval_seconds=30,
    heartbeat_interval_seconds=10,
    health_check_interval_seconds=60,
    
    # Logging
    log_level="INFO",
    log_format="json"
)
```

---

## Usage Examples

### Starting the Agent

```python
import asyncio
from coding_agent import CodingAgent, main

# Run the agent
asyncio.run(main())
```

### Example 1: Execute Python Code

```python
import asyncio
import json
import nats

async def execute_python_example():
    nc = await nats.connect("nats://localhost:4222")
    
    # Prepare task request
    task = {
        "task_id": "exec-001",
        "task_type": "execute_code",
        "payload": {
            "code": """
print("Hello from Python!")
for i in range(5):
    print(f"Count: {i}")
            """,
            "language": "python",
            "timeout_seconds": 10,
            "max_memory_mb": 256
        },
        "priority": "MEDIUM"
    }
    
    # Send request and wait for response
    response = await nc.request(
        "agent.coding_agent.task",
        json.dumps(task).encode(),
        timeout=15
    )
    
    result = json.loads(response.data.decode())
    print("Execution Result:")
    print(json.dumps(result, indent=2))
    
    await nc.close()

asyncio.run(execute_python_example())
```

**Expected Output:**
```json
{
  "status": "success",
  "result": {
    "status": "success",
    "stdout": "Hello from Python!\nCount: 0\nCount: 1\nCount: 2\nCount: 3\nCount: 4\n",
    "stderr": "",
    "exit_code": 0,
    "execution_time_ms": 45.2,
    "memory_used_mb": 12.5,
    "output_truncated": false,
    "cached": false
  },
  "task_id": "exec-001"
}
```

### Example 2: Execute JavaScript Code

```python
async def execute_javascript_example():
    nc = await nats.connect("nats://localhost:4222")
    
    task = {
        "task_id": "exec-002",
        "task_type": "execute_code",
        "payload": {
            "code": """
const numbers = [1, 2, 3, 4, 5];
const sum = numbers.reduce((a, b) => a + b, 0);
console.log('Sum:', sum);

const squared = numbers.map(n => n * n);
console.log('Squared:', squared);
            """,
            "language": "javascript",
            "timeout_seconds": 10
        }
    }
    
    response = await nc.request(
        "agent.coding_agent.task",
        json.dumps(task).encode(),
        timeout=15
    )
    
    result = json.loads(response.data.decode())
    print("JavaScript Result:", result['result']['stdout'])
    
    await nc.close()
```

### Example 3: Validate Code Security

```python
async def validate_code_example():
    nc = await nats.connect("nats://localhost:4222")
    
    # Test potentially dangerous code
    task = {
        "task_id": "validate-001",
        "task_type": "validate_code",
        "payload": {
            "code": """
import os
os.system('rm -rf /')
            """,
            "language": "python",
            "allow_filesystem": False
        }
    }
    
    response = await nc.request(
        "agent.coding_agent.task",
        json.dumps(task).encode(),
        timeout=5
    )
    
    result = json.loads(response.data.decode())
    print("Validation Result:")
    print(f"Is Safe: {result['result']['is_safe']}")
    print(f"Issues: {result['result']['issues']}")
    
    await nc.close()
```

**Expected Output:**
```json
{
  "status": "success",
  "result": {
    "is_safe": false,
    "issues": [
      "Potentially dangerous pattern detected: import\\s+os\\s*$",
      "Potentially dangerous pattern detected: open\\s*\\("
    ],
    "language": "python"
  }
}
```

### Example 4: Execute with Environment Variables

```python
async def execute_with_env_example():
    task = {
        "task_id": "exec-003",
        "task_type": "execute_code",
        "payload": {
            "code": """
import os
api_key = os.getenv('API_KEY', 'not_found')
db_url = os.getenv('DATABASE_URL', 'not_found')
print(f'API Key: {api_key}')
print(f'Database: {db_url}')
            """,
            "language": "python",
            "environment_vars": {
                "API_KEY": "secret-key-123",
                "DATABASE_URL": "postgresql://localhost:5432/mydb"
            }
        }
    }
    
    nc = await nats.connect("nats://localhost:4222")
    response = await nc.request(
        "agent.coding_agent.task",
        json.dumps(task).encode(),
        timeout=15
    )
    result = json.loads(response.data.decode())
    print(result['result']['stdout'])
    await nc.close()
```

### Example 5: Get Execution History

```python
async def get_history_example():
    nc = await nats.connect("nats://localhost:4222")
    
    task = {
        "task_id": "history-001",
        "task_type": "get_execution_history",
        "payload": {
            "limit": 10,
            "offset": 0,
            "language": "python",
            "status": "success"
        }
    }
    
    response = await nc.request(
        "agent.coding_agent.task",
        json.dumps(task).encode(),
        timeout=10
    )
    
    result = json.loads(response.data.decode())
    print(f"Found {result['result']['count']} executions")
    for exec in result['result']['executions']:
        print(f"  {exec['execution_id']}: {exec['language']} - {exec['status']}")
    
    await nc.close()
```

### Example 6: List Supported Languages

```python
async def list_languages_example():
    nc = await nats.connect("nats://localhost:4222")
    
    task = {
        "task_id": "list-001",
        "task_type": "list_languages",
        "payload": {}
    }
    
    response = await nc.request(
        "agent.coding_agent.task",
        json.dumps(task).encode(),
        timeout=5
    )
    
    result = json.loads(response.data.decode())
    print("Supported Languages:")
    for lang, info in result['result']['languages'].items():
        status = "✓" if info['available'] else "✗"
        print(f"  {status} {lang}: {info['version']}")
    
    await nc.close()
```

---

## API Reference

### Task Types

#### 1. `execute_code`

Execute code in a sandboxed environment.

**Request Payload:**
```python
{
    "code": str,                    # Code to execute (required)
    "language": str,                # Language: python, javascript, bash, sql
    "timeout_seconds": int,         # Execution timeout (default: 30)
    "max_memory_mb": int,           # Memory limit (default: 512)
    "max_output_size": int,         # Max output size in bytes (default: 1MB)
    "allow_network": bool,          # Allow network access (default: false)
    "allow_filesystem": bool,       # Allow filesystem access (default: false)
    "environment_vars": dict,       # Environment variables
    "stdin_data": str,              # Standard input data
    "dependencies": list            # List of dependencies (future)
}
```

**Response:**
```python
{
    "status": "success" | "error",
    "result": {
        "status": "success" | "error" | "timeout" | "security_violation",
        "stdout": str,              # Standard output
        "stderr": str,              # Standard error
        "exit_code": int,           # Process exit code
        "execution_time_ms": float, # Execution time
        "memory_used_mb": float,    # Memory used
        "output_truncated": bool,   # Output was truncated
        "error_message": str,       # Error message if failed
        "cached": bool              # Result from cache
    }
}
```

#### 2. `validate_code`

Validate code for security issues without executing.

**Request Payload:**
```python
{
    "code": str,
    "language": str,
    "allow_network": bool,
    "allow_filesystem": bool
}
```

**Response:**
```python
{
    "status": "success",
    "result": {
        "is_safe": bool,
        "issues": list[str],
        "language": str
    }
}
```

#### 3. `list_languages`

List supported languages and configuration.

**Response:**
```python
{
    "status": "success",
    "result": {
        "languages": {
            "python": {"available": bool, "version": str},
            "javascript": {"available": bool, "version": str},
            "bash": {"available": bool, "version": str},
            "sql": {"available": bool, "version": str}
        },
        "default_timeout": int,
        "max_timeout": int,
        "default_memory_mb": int,
        "max_memory_mb": int
    }
}
```

#### 4. `get_execution_history`

Retrieve execution history from database.

**Request Payload:**
```python
{
    "limit": int,      # Max results (default: 100, max: 1000)
    "offset": int,     # Pagination offset
    "language": str,   # Filter by language (optional)
    "status": str      # Filter by status (optional)
}
```

---

## Security Considerations

### Dangerous Patterns Detected

The agent automatically detects and blocks:

**Python:**
- File system operations (`open`, `file`)
- Subprocess execution (`subprocess`, `os.system`)
- Dynamic code execution (`eval`, `exec`, `compile`)
- Network operations (`socket`, `requests`, `urllib`)

**JavaScript:**
- File system access (`require('fs')`)
- Child processes (`require('child_process')`)
- Network operations (`require('net')`)
- Dynamic evaluation (`eval`, `Function`)

**Bash:**
- Destructive commands (`rm -rf`)
- Privilege escalation (`sudo`)
- Network tools (`curl`, `wget`, `nc`)

### Resource Limits

```python
# CPU time limit
resource.setrlimit(resource.RLIMIT_CPU, (60, 120))

# Memory limit
memory_bytes = max_memory_mb * 1024 * 1024
resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

# Process limit
resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
```

### Best Practices

1. **Always validate code** before execution
2. **Set appropriate timeouts** to prevent infinite loops
3. **Limit memory** to prevent resource exhaustion
4. **Disable network/filesystem** access unless required
5. **Monitor execution metrics** for anomalies
6. **Use caching** for repeated executions
7. **Review security logs** regularly

---

## Monitoring & Metrics

### Status Endpoint

```python
# Query agent status
response = await nc.request("agent.coding_agent.status", b"{}")
status = json.loads(response.data)
```

**Status Response:**
```json
{
  "agent_id": "coding-001",
  "state": "running",
  "uptime_seconds": 3600.5,
  "connections": {
    "nats": {"state": "connected"},
    "postgres": {"state": "connected"},
    "redis": {"state": "connected"}
  },
  "metrics": {
    "tasks_completed": 1250,
    "tasks_failed": 15,
    "avg_processing_time_ms": 125.5
  },
  "coding_metrics": {
    "total_executions": 1000,
    "successful_executions": 985,
    "failed_executions": 10,
    "timeout_executions": 3,
    "security_violations": 2,
    "cache_hits": 450,
    "cache_misses": 550,
    "language_breakdown": {
      "python": 700,
      "javascript": 250,
      "bash": 50
    }
  }
}
```

### Health Check

```python
response = await nc.request("agent.coding_agent.health", b"{}")
health = json.loads(response.data)
```

---

## Troubleshooting

### Common Issues

**1. Node.js not found**
```bash
# Install Node.js
sudo apt-get install nodejs npm
# Verify
node --version
```

**2. Connection refused (NATS/PostgreSQL/Redis)**
```bash
# Check services
sudo systemctl status postgresql
sudo systemctl status redis
pgrep nats-server

# Restart if needed
sudo systemctl restart postgresql
sudo systemctl restart redis
nats-server &
```

**3. Permission denied errors**
```bash
# Ensure proper permissions
chmod +x coding_agent.py
# Check database permissions
psql -U postgres -c "GRANT ALL ON DATABASE agentdb TO user;"
```

**4. Memory/Resource limits not working**
```python
# Resource limits may not work on all platforms
# Use Docker for better isolation (recommended for production)
```

### Debug Mode

Enable debug logging:
```python
config = AgentConfig(
    # ... other config ...
    log_level="DEBUG",
    log_format="text"  # More readable for debugging
)
```

---

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs npm \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy files
COPY requirements.txt .
COPY enhanced_base_agent.py .
COPY coding_agent.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run agent
CMD ["python", "coding_agent.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coding-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: coding-agent
  template:
    metadata:
      labels:
        app: coding-agent
    spec:
      containers:
      - name: coding-agent
        image: coding-agent:1.0.0
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        env:
        - name: NATS_URL
          value: "nats://nats-service:4222"
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          value: "redis://redis-service:6379"
```

### Performance Tuning

```python
# For high-throughput environments
config = AgentConfig(
    max_concurrent_tasks=100,      # Increase concurrent tasks
    postgres_max_pool_size=50,     # Larger connection pool
    redis_max_connections=100,     # More Redis connections
    cache_ttl_seconds=7200,        # Longer cache TTL
)
```

---

## License

Production-ready Coding Agent - Built on Enhanced Base Agent Framework
Copyright (c) 2024

---

## Support

For issues, questions, or contributions:
- GitHub Issues: <repository-url>/issues
- Documentation: <docs-url>
- Email: support@example.com