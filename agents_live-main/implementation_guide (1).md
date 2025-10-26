# YMERA Project Agent - Complete Implementation Guide

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Agent Communication Flow](#agent-communication-flow)
6. [API Integration Examples](#api-integration-examples)
7. [Deployment Guide](#deployment-guide)
8. [Monitoring & Logging](#monitoring--logging)
9. [Troubleshooting](#troubleshooting)

---

## System Overview

### Purpose
The **Project Agent** is responsible for:
- Receiving files, modules, and code from other agents (Coding, Enhancement, Examination, etc.)
- Quality verification and validation
- Module integration into projects
- Building complete projects from modules
- Comprehensive logging of all activities and file locations
- Knowledge contribution to the Learning Agent
- Communication with the Agent Manager for approvals and coordination

### Key Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                     PROJECT AGENT                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. RECEIVE & VERIFY                                         │
│     ├─ Accept submissions from agents                       │
│     ├─ Quality verification (85%+ threshold)                │
│     └─ Security & performance checks                        │
│                                                              │
│  2. INTEGRATE & BUILD                                        │
│     ├─ Module dependency resolution                         │
│     ├─ File system integration                              │
│     ├─ Project building (hot-reload/blue-green/canary)      │
│     └─ Artifact packaging                                   │
│                                                              │
│  3. LOG & TRACK                                              │
│     ├─ File location tracking                               │
│     ├─ Directory structure management                       │
│     ├─ Integration history                                  │
│     └─ Daily log synchronization                            │
│                                                              │
│  4. COMMUNICATE                                              │
│     ├─ Agent Manager coordination                           │
│     ├─ Learning Agent knowledge flow                        │
│     ├─ Real-time WebSocket updates                          │
│     └─ User chat interface                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Component Structure

```
project-agent/
├── api/
│   └── main.py                 # Complete FastAPI application with all endpoints
│
├── core/
│   ├── config.py               # Settings & configuration
│   ├── database.py             # PostgreSQL async manager
│   ├── agent_orchestrator.py  # Agent communication
│   ├── auth.py                 # JWT authentication
│   ├── chat_interface.py      # Natural language interface
│   ├── file_manager.py         # File storage & versioning
│   ├── quality_verifier.py    # Quality verification engine
│   ├── project_integrator.py  # Module integration
│   └── report_generator.py    # Report generation
│
├── services/
│   └── project_builder_agent.py # Advanced project builder
│
├── utils/
│   ├── websocket_manager.py   # Real-time communication
│   ├── log_manager.py          # Comprehensive logging
│   └── metrics.py              # Performance metrics
│
└── agents/
    └── agent.py                # Legacy agent (can be retired)
```

### Database Schema

```sql
-- Core Tables (from migrations)
users
projects
agent_submissions
file_metadata
chat_messages
user_sessions
quality_metrics
file_versions

-- Logging Tables (from log_manager)
project_event_logs
file_location_logs
module_integration_logs
knowledge_flow_logs
build_process_logs
agent_interaction_logs
directory_structure_snapshots
```

---

## Installation & Setup

### Prerequisites

```bash
# Required
Python 3.11+
PostgreSQL 14+
Redis 7+ (optional, for caching)
Docker & Docker Compose (recommended)

# Optional
Kafka (for event streaming)
Prometheus (for metrics)
Grafana (for dashboards)
```

### Step 1: Environment Setup

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ymera_project_agent
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Server
PROJECT_AGENT_HOST=0.0.0.0
PROJECT_AGENT_PORT=8001
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
WORKER_COUNT=4

# Security
JWT_SECRET_KEY=your-super-secret-key-minimum-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Agent URLs
MANAGER_AGENT_URL=http://manager-agent:8000
CODING_AGENT_URL=http://coding-agent:8010
EXAMINATION_AGENT_URL=http://examination-agent:8030
ENHANCEMENT_AGENT_URL=http://enhancement-agent:8020

# Quality Settings
QUALITY_THRESHOLD=85.0
CODE_COVERAGE_MIN=80.0
SECURITY_SCAN_ENABLED=true

# Quality Weights
QUALITY_CODE_WEIGHT=0.35
QUALITY_SECURITY_WEIGHT=0.30
QUALITY_PERFORMANCE_WEIGHT=0.20
QUALITY_DOCUMENTATION_WEIGHT=0.15

# Storage
STORAGE_BACKEND=local
STORAGE_PATH=./uploads
MAX_UPLOAD_SIZE_MB=100
FILE_VERSIONING_ENABLED=true

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Feature Flags
ENABLE_CHAT_INTERFACE=true
ENABLE_FILE_VERSIONING=true
ENABLE_AUTO_INTEGRATION=true
ENABLE_ROLLBACK=true
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn[standard]
pip install asyncpg sqlalchemy
pip install pydantic pydantic-settings
pip install python-jose[cryptography] passlib[bcrypt]
pip install httpx websockets
pip install structlog python-json-logger
pip install aiofiles
pip install pytest pytest-asyncio  # For testing
```

### Step 3: Initialize Database

```bash
# The application will automatically run migrations on startup
# Or manually:
python -c "
import asyncio
from core.database import ProjectDatabase
from core.config import settings

async def init():
    db = ProjectDatabase(settings.database_url, 20, 10)
    await db.initialize()
    print('Database initialized successfully')

asyncio.run(init())
"
```

### Step 4: Start the Service

```bash
# Development
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## Configuration

### Quality Verification Settings

The quality verification engine uses weighted scoring:

```python
Total Score = (
    0.35 × Code Quality +
    0.30 × Security Score +
    0.20 × Performance Score +
    0.15 × Documentation Score
)

Threshold: 85.0 (configurable)
```

### Integration Strategies

Three deployment strategies available:

1. **Hot-Reload** (default)
   - Immediate integration
   - No downtime
   - Best for: Development, non-critical updates

2. **Blue-Green**
   - Zero downtime
   - Safe rollback
   - Best for: Production, critical updates

3. **Canary**
   - Gradual rollout
   - Risk mitigation
   - Best for: Large changes, high-traffic systems

---

## Agent Communication Flow

### 1. Submission Flow (Agent → Project Agent)

```mermaid
sequenceDiagram
    participant CA as Coding Agent
    participant PA as Project Agent
    participant QV as Quality Verifier
    participant PI as Project Integrator
    participant MA as Manager Agent

    CA->>PA: POST /api/v1/submissions
    PA->>PA: Log submission
    PA->>QV: Verify quality
    QV->>QV: Multi-criteria analysis
    QV-->>PA: Quality score & issues
    
    alt Score >= 85%
        PA->>PI: Integrate module
        PI->>PI: Resolve dependencies
        PI->>PI: Write to filesystem
        PI-->>PA: Success
        PA->>MA: Notify success
    else Score < 85%
        PA->>MA: Notify rejection + report
    end
```

### 2. Knowledge Request Flow

```mermaid
sequenceDiagram
    participant Agent as Any Agent
    participant PA as Project Agent
    participant MA as Manager Agent
    participant LA as Learning Agent

    Agent->>PA: Request knowledge
    PA->>PA: Log request
    PA->>MA: Request approval
    MA->>MA: Validate request
    
    alt Approved
        MA->>LA: Forward request
        LA->>LA: Search knowledge base
        LA-->>MA: Knowledge data
        MA-->>PA: Approved + data
        PA-->>Agent: Knowledge response
    else Rejected / Not found
        MA-->>PA: Rejection / Not found
        PA->>LA: Request data collection
    end
```

### 3. Daily Synchronization Flow

```mermaid
sequenceDiagram
    participant PA as Project Agent
    participant MA as Manager Agent
    participant LA as Learning Agent

    Note over PA: Every 12 hours (00:00, 12:00)
    
    PA->>PA: Collect 24h summary
    PA->>PA: Aggregate logs
    
    PA->>MA: POST /api/v1/logs/daily-sync
    Note right of MA: Full log data
    
    PA->>LA: POST /api/v1/logs/daily-sync
    Note right of LA: Knowledge extraction
```

---

## API Integration Examples

### Example 1: Submit Code from Coding Agent

```python
import httpx
import asyncio

async def submit_code():
    async with httpx.AsyncClient() as client:
        submission = {
            "agent_id": "coding_agent_001",
            "project_id": "proj_abc123",
            "module_name": "user_authentication",
            "output_type": "code",
            "files": [
                {
                    "path": "src/auth/login.py",
                    "content": "# Login module code...",
                    "type": "python"
                },
                {
                    "path": "tests/test_login.py",
                    "content": "# Test code...",
                    "type": "python"
                }
            ],
            "metadata": {
                "test_coverage": 92.5,
                "complexity_score": 7.2,
                "dependencies": ["fastapi", "passlib"]
            }
        }
        
        response = await client.post(
            "http://project-agent:8001/api/v1/submissions",
            json=submission,
            headers={"Authorization": "Bearer <token>"}
        )
        
        result = response.json()
        print(f"Submission ID: {result['submission_id']}")
        print(f"Status: {result['status']}")

asyncio.run(submit_code())
```

### Example 2: Request Knowledge

```python
async def request_knowledge():
    async with httpx.AsyncClient() as client:
        request = {
            "agent_id": "enhancement_agent_002",
            "knowledge_type": "code_patterns",
            "query": "Best practices for async error handling in FastAPI",
            "context": {
                "language": "python",
                "framework": "fastapi"
            }
        }
        
        response = await client.post(
            "http://project-agent:8001/api/v1/knowledge/request",
            json=request,
            headers={"Authorization": "Bearer <token>"}
        )
        
        result = response.json()
        print(f"Request ID: {result['request_id']}")
        print(f"Status: {result['status']}")

asyncio.run(request_knowledge())
```

### Example 3: WebSocket Real-time Updates

```javascript
// JavaScript/TypeScript client
const ws = new WebSocket('ws://project-agent:8001/ws/project/proj_abc123');

ws.onopen = () => {
    console.log('Connected to project updates');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'new_submission':
            console.log('New submission:', data.submission_id);
            break;
        
        case 'quality_result':
            console.log('Quality result:', data.quality_score);
            break;
        
        case 'integration_complete':
            console.log('Integration complete:', data.result);
            break;
        
        case 'build_progress':
            console.log('Build progress:', data.progress);
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

### Example 4: Start Project Build

```python
async def start_build():
    async with httpx.AsyncClient() as client:
        build_request = {
            "project_id": "proj_abc123",
            "modules": [
                {
                    "id": "mod_001",
                    "name": "authentication",
                    "module_type": "backend",
                    "content": "# Module content",
                    "file_path": "src/auth/main.py",
                    "dependencies": [],
                    "validation_score": 95.0,
                    "metadata": {}
                },
                {
                    "id": "mod_002",
                    "name": "user_service",
                    "module_type": "backend",
                    "content": "# User service code",
                    "file_path": "src/services/user.py",
                    "dependencies": ["mod_001"],
                    "validation_score": 88.0,
                    "metadata": {}
                }
            ]
        }
        
        response = await client.post(
            "http://project-agent:8001/api/v1/builds/start",
            json=build_request,
            headers={"Authorization": "Bearer <token>"}
        )
        
        result = response.json()
        print(f"Build ID: {result['build_id']}")
        print(f"Status: {result['status']}")

asyncio.run(start_build())
```

---

## Deployment Guide

### Docker Compose Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: ymera
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: ymera_project_agent
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ymera"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  project-agent:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://ymera:secure_password@postgres:5432/ymera_project_agent
      - REDIS_URL=redis://redis:6379/0
      - MANAGER_AGENT_URL=http://manager-agent:8000
      - CODING_AGENT_URL=http://coding-agent:8010
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p /app/uploads /app/logs

# Expose port
EXPOSE 8001

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: project-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: project-agent
  template:
    metadata:
      labels:
        app: project-agent
    spec:
      containers:
      - name: project-agent
        image: ymera/project-agent:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: project-agent-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: project-agent-secrets
              key: jwt-secret
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
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
```

---

## Monitoring & Logging

### Access Logs

```bash
# View real-time logs
tail -f logs/project_agent.log

# Query specific events
grep "module_integrated" logs/project_agent.log

# View error logs only
grep "ERROR" logs/project_agent.log
```

### Metrics Dashboard

Access Prometheus metrics:
```
GET http://project-agent:8001/api/v1/metrics
```

Key metrics:
- `requests_total` - Total API requests
- `errors_total` - Total errors
- `response_time_*` - Response times per endpoint
- `submissions_total` - Total submissions received
- `quality_verifications_total` - Quality checks performed
- `integrations_total` - Successful integrations
- `builds_total` - Total builds

### Database Queries for Analytics

```sql
-- Project statistics
SELECT 
    p.name,
    COUNT(s.id) as submissions,
    AVG(s.quality_score) as avg_quality,
    COUNT(CASE WHEN s.status = 'integrated' THEN 1 END) as integrated
FROM projects p
LEFT JOIN agent_submissions s ON p.id = s.project_id
GROUP BY p.id, p.name;

-- Recent activity
SELECT * FROM project_event_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- Quality trends
SELECT 
    DATE(created_at) as date,
    AVG(quality_score) as avg_score,
    COUNT(*) as submission_count
FROM agent_submissions
WHERE quality_score IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;
```

---

## Troubleshooting

### Common Issues

1. **Submission Rejected**
   - Check quality score threshold
   - Review issues in response
   - Verify test coverage meets minimum

2. **Integration Failed**
   - Check dependency resolution
   - Verify file paths
   - Review error logs

3. **Build Timeout**
   - Increase build timeout in config
   - Check module count
   - Review build logs

4. **WebSocket Disconnection**
   - Check network connectivity
   - Verify authentication token
   - Review connection logs

### Health Check Endpoints

```bash
# Overall health
curl http://project-agent:8001/health

# Component status
curl http://project-agent:8001/api/v1/agents

# Database health
curl http://project-agent:8001/api/v1/metrics
```

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

---

## Next Steps

1. **Start the service** using the installation guide
2. **Configure agent URLs** in `.env`
3. **Test submissions** using the API examples
4. **Monitor logs** for the first integrations
5. **Set up daily sync** with Manager and Learning agents
6. **Configure WebSocket** for real-time updates
7. **Deploy to production** using Docker/Kubernetes

For questions or issues, check the logs first, then review this guide's troubleshooting section.
