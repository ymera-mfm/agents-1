# YMERA Platform - System Overview

## Quick Tour (15 minutes)

### 1. Architecture Overview (3 minutes)

#### System Components and Their Roles

The YMERA platform is a multi-agent AI system built on a microservices architecture with the following key components:

1. **Project Agent (Port 8001)** - Central coordinator that manages project lifecycle, quality verification, and integration
2. **Manager Agent (Port 8000)** - Task delegation and agent orchestration
3. **Specialized Agents (20+)** - Domain-specific agents including:
   - Coding Agent (8010) - Code generation and editing
   - Enhancement Agent (8020) - Code optimization
   - Examination Agent (8030) - Testing and QA
   - Security Agent (8050) - Security scanning
   - Database Agent (8070) - Database operations
   - And 15+ more specialized agents

#### Data Flow Through the System

```
User Request → API Gateway (FastAPI) → Authentication Middleware
    ↓
Manager Agent → Task Queue (Redis) → Agent Assignment
    ↓
Specialized Agents (parallel processing) → Results Aggregation
    ↓
Quality Verification → Project Integration → Response to User
```

#### Integration Points

- **Database Layer**: PostgreSQL 15+ with async support (asyncpg)
- **Cache Layer**: Redis 7+ for task queuing and session management
- **Message Queue**: Apache Kafka 3.5+ for asynchronous task processing (optional)
- **File Storage**: Multi-backend support (Local/S3/Azure/GCS)
- **Monitoring**: Prometheus metrics + Jaeger tracing
- **Service Mesh**: Istio for inter-agent communication

#### Technology Stack

**Backend Framework**
- FastAPI 0.104+ (Python 3.11+)
- Pydantic 2.5+ for data validation
- SQLAlchemy 2.0+ with async support

**Database & Caching**
- PostgreSQL 15+ (production)
- Redis 7+ (caching & queuing)
- SQLite (development/testing)

**Security**
- JWT authentication (RS256/HS256)
- Role-based access control (RBAC)
- Rate limiting per user/IP
- Encryption at rest and in transit

**DevOps**
- Docker & Docker Compose
- Kubernetes with Helm charts
- Istio service mesh
- CI/CD with GitHub Actions

---

### 2. Core Components (5 minutes)

#### Configuration System

Located in `core/config.py`, the configuration system uses Pydantic Settings for type-safe configuration:

```python
from core.config import Settings, get_settings

settings = get_settings()  # Singleton instance with caching
```

**Key Configuration Areas:**
- **Database**: Connection URLs, pool settings, timeouts
- **Security**: JWT secrets, CORS origins, rate limits
- **Agents**: URLs and timeouts for 20+ agents
- **Features**: Feature flags for toggling functionality
- **Monitoring**: Prometheus, Jaeger, logging settings

**Environment Variables** (`.env` file):
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ymera

# Security
JWT_SECRET_KEY=your-256-bit-secret-key

# Redis
REDIS_URL=redis://localhost:6379/0

# Agent URLs
MANAGER_AGENT_URL=http://manager-agent:8000
CODING_AGENT_URL=http://coding-agent:8010
```

#### Authentication & Authorization

**Authentication Flow** (`core/auth.py`):
1. User registers/logs in via `/auth/register` or `/auth/login`
2. System returns JWT access token (expires in 60 minutes)
3. Client includes token in `Authorization: Bearer <token>` header
4. Middleware validates token and extracts user context

**Authorization Levels:**
- **User**: Basic access to create tasks and agents
- **Admin**: Full system access, user management
- **Service**: Inter-agent communication

**Implementation:**
```python
from core.auth import AuthService
from fastapi import Depends

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    payload = auth_service.decode_access_token(token.credentials)
    # Returns user object or raises 401
```

#### Database Layer

**Database Architecture** (`core/database.py`):
- Async connection pooling with asyncpg
- Repository pattern for data access
- Automatic retry logic with exponential backoff
- Health monitoring and statistics

**Key Models** (`core/sqlalchemy_models.py`):
- **User**: Authentication and profile data
- **Agent**: Agent registration and status
- **Task**: Task definitions and results
- **Project**: Project metadata
- **Submission**: Code submissions and quality scores
- **File**: File storage with versioning

**Usage Pattern:**
```python
from core.database import Database, get_db
from fastapi import Depends

async def endpoint(db: Database = Depends(get_db)):
    user = await db.execute_single("SELECT * FROM users WHERE id = $1", user_id)
    users = await db.execute_query("SELECT * FROM users WHERE active = $1", True)
    await db.execute_command("UPDATE users SET last_login = NOW() WHERE id = $1", user_id)
```

**Migrations** (Alembic):
```bash
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
alembic downgrade -1
```

#### Caching Layer

**Redis Integration** (`redis.asyncio`):
- Task queue with priority support
- Session storage
- Rate limiting counters
- Cache for frequently accessed data

**Task Queue Implementation:**
```python
class TaskQueue:
    async def enqueue_task(self, task_data: dict, priority: TaskPriority):
        # Priority queue using Redis sorted sets
        await self.redis.zadd(queue_name, {json.dumps(task_data): priority_score})
    
    async def dequeue_task(self) -> Optional[dict]:
        # Pop highest priority task
        return await self.redis.zpopmax(queue_name)
```

#### API Gateway

**FastAPI Application** (`main.py`):
- RESTful API with automatic OpenAPI documentation
- WebSocket support for real-time updates
- Request/response middleware chain
- Automatic request validation via Pydantic

**Middleware Stack** (order matters):
1. `RequestLoggingMiddleware` - Log all requests
2. `RequestTimeoutMiddleware` - 30-second timeout
3. `RequestSizeLimitMiddleware` - 10MB max
4. `SecurityHeadersMiddleware` - HSTS, CSP, etc.
5. `RateLimitMiddleware` - Rate limiting
6. `CORSMiddleware` - Cross-origin requests

**API Documentation:**
- Interactive docs: http://localhost:8000/docs (Swagger UI)
- ReDoc: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

---

### 3. Agents & Engines (4 minutes)

#### Agent Architecture

**Base Agent Pattern** (`base_agent.py`):
All agents inherit from `BaseAgent` and implement:

```python
class BaseAgent:
    async def initialize(self):
        """Initialize agent resources"""
        
    async def process(self, task: Task) -> TaskResult:
        """Process a task and return result"""
        
    async def cleanup(self):
        """Clean up resources"""
        
    async def health_check(self) -> HealthStatus:
        """Report agent health"""
```

**Agent Lifecycle:**
1. **Registration**: Agent registers with Manager Agent
2. **Heartbeat**: Periodic health checks (every 60 seconds)
3. **Task Assignment**: Manager assigns tasks based on capabilities
4. **Task Processing**: Agent processes task and returns result
5. **Status Updates**: Real-time status updates via WebSocket

**Agent Communication:**
- Synchronous: HTTP/REST for request-response
- Asynchronous: Kafka for fire-and-forget tasks
- Real-time: WebSocket for streaming updates

#### Engine Architecture

**Specialized Processing Engines:**

1. **Intelligence Engine** (`intelligence_engine.py`)
   - Natural language understanding
   - Context extraction and analysis
   - Decision making and recommendations

2. **Optimization Engine** (`optimizing_engine.py`)
   - Code optimization
   - Performance analysis
   - Resource allocation

3. **Learning Engine** (`learning_engine.py`)
   - Machine learning model training
   - Pattern recognition
   - Continuous improvement

4. **Performance Engine** (`performance_engine.py`)
   - Performance benchmarking
   - Load testing
   - Bottleneck identification

**Engine Usage Pattern:**
```python
from intelligence_engine import IntelligenceEngine

engine = IntelligenceEngine()
await engine.initialize()

result = await engine.analyze_code(
    code=submission.code,
    context=project.context
)

analysis = result.to_dict()
```

#### How They Interact

**Typical Workflow:**

```
1. User submits code via API
   ↓
2. Project Agent receives submission
   ↓
3. Quality Verification Engine analyzes code
   - Code quality (static analysis)
   - Security scanning
   - Performance benchmarking
   - Documentation coverage
   ↓
4. If quality score ≥ threshold:
   - Project Integration Engine integrates code
   - Deployment strategy (hot-reload/blue-green/canary)
   - Git commit and push
   ↓
5. Manager Agent coordinates post-integration tasks
   - Coding Agent: Generate additional code
   - Examination Agent: Run tests
   - Documentation Agent: Update docs
   ↓
6. Results aggregated and returned to user
```

#### Example Workflows

**Workflow 1: Code Submission**
```python
POST /api/submissions
{
    "project_id": "uuid",
    "code": "...",
    "files": [...]
}

→ Quality verification (85/100)
→ Integration (blue-green deployment)
→ Post-integration tests
→ Response with submission ID
```

**Workflow 2: Task Assignment**
```python
POST /tasks
{
    "name": "Generate REST API",
    "task_type": "code_generation",
    "parameters": {...}
}

→ Manager Agent assigns to Coding Agent
→ Coding Agent generates code
→ Enhancement Agent optimizes
→ Examination Agent tests
→ Response with task result
```

---

### 4. Development Workflow (3 minutes)

#### Setting Up Development Environment

**Prerequisites:**
- Python 3.11+
- PostgreSQL 15+ or Docker
- Redis 7+ or Docker
- Git

**Quick Setup:**
```bash
# 1. Clone repository
git clone https://github.com/your-org/ymera.git
cd ymera

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start services (Docker Compose)
docker-compose up -d postgres redis

# 5. Configure environment
cp .env.example .env
# Edit .env with your settings

# 6. Run migrations
alembic upgrade head

# 7. Start application
uvicorn main:app --reload

# 8. Verify
curl http://localhost:8000/health
```

#### Running Tests

**Test Structure:**
```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── e2e/              # End-to-end tests
├── performance/      # Load tests
└── security/         # Security tests
```

**Run Tests:**
```bash
# All tests
pytest

# Specific test type
pytest tests/unit/
pytest tests/integration/

# With coverage
pytest --cov=core --cov=api --cov-report=html

# Specific test file
pytest tests/unit/test_auth.py

# Specific test function
pytest tests/unit/test_auth.py::test_create_access_token
```

#### Making Changes

**Development Process:**

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow code style guidelines (PEP 8, Black formatting)
   - Add type hints to all functions
   - Write tests for new code
   - Update documentation

3. **Run Linters**
   ```bash
   black .              # Format code
   flake8 .             # Check style
   mypy .               # Type checking
   ```

4. **Run Tests**
   ```bash
   pytest --cov=. --cov-report=html
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: Add feature description"
   ```

#### Submitting PRs

**PR Checklist:**
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Code formatted with Black
- [ ] All tests passing
- [ ] Coverage ≥ 80%
- [ ] No linter warnings
- [ ] PR description includes context and testing notes

**PR Process:**
1. Push branch: `git push origin feature/your-feature-name`
2. Open PR on GitHub
3. Fill in PR template
4. Request review from maintainers
5. Address review feedback
6. Merge when approved

---

## Deep Dive Sections

### Database Schema

#### Core Tables

**users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

**agents**
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    capabilities JSONB DEFAULT '[]',
    config JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'inactive',
    last_heartbeat TIMESTAMP,
    owner_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**tasks**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending',
    result JSONB,
    error_message TEXT,
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

**projects**
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    config JSONB DEFAULT '{}',
    owner_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**submissions**
```sql
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    user_id UUID REFERENCES users(id),
    code TEXT NOT NULL,
    quality_score DECIMAL(5,2),
    security_score DECIMAL(5,2),
    performance_score DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'pending',
    integration_strategy VARCHAR(50),
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    integrated_at TIMESTAMP
);
```

#### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_owner_id ON agents(owner_id);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_submissions_project_id ON submissions(project_id);

-- Full-text search
CREATE INDEX idx_projects_name_search ON projects USING GIN(to_tsvector('english', name));
```

#### Relationships

```
users (1) ─── (N) agents
users (1) ─── (N) tasks
users (1) ─── (N) projects
projects (1) ─── (N) submissions
agents (1) ─── (N) tasks
```

---

### API Endpoints

#### Authentication Endpoints

**POST /auth/register**
```json
Request:
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}

Response (201):
{
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user_id": "uuid"
}
```

**POST /auth/login**
```json
Request:
{
    "username": "john_doe",
    "password": "SecurePass123!"
}

Response (200):
{
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user_id": "uuid"
}
```

**GET /users/me**
```json
Headers:
{
    "Authorization": "Bearer eyJhbGc..."
}

Response (200):
{
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2024-01-16T12:00:00Z"
}
```

#### Agent Endpoints

**POST /agents**
```json
Request:
{
    "name": "My Coding Agent",
    "description": "Custom coding agent",
    "capabilities": ["python", "javascript"],
    "config": {"model": "gpt-4"}
}

Response (201):
{
    "agent_id": "uuid",
    "status": "created"
}
```

**GET /agents**
```json
Response (200):
[
    {
        "id": "uuid",
        "name": "My Coding Agent",
        "description": "Custom coding agent",
        "capabilities": ["python", "javascript"],
        "status": "active",
        "last_heartbeat": "2024-01-16T12:05:00Z",
        "created_at": "2024-01-16T12:00:00Z"
    }
]
```

**POST /agents/{agent_id}/heartbeat**
```json
Request:
{
    "status": "active"
}

Response (200):
{
    "status": "heartbeat_received"
}
```

#### Task Endpoints

**POST /tasks**
```json
Request:
{
    "name": "Generate API",
    "description": "Generate REST API for user management",
    "task_type": "code_generation",
    "parameters": {
        "language": "python",
        "framework": "fastapi"
    },
    "priority": "high"
}

Response (201):
{
    "task_id": "uuid",
    "status": "created"
}
```

**GET /tasks**
```json
Response (200):
[
    {
        "id": "uuid",
        "name": "Generate API",
        "task_type": "code_generation",
        "priority": "high",
        "status": "completed",
        "result": {...},
        "created_at": "2024-01-16T12:00:00Z",
        "completed_at": "2024-01-16T12:05:00Z"
    }
]
```

**GET /tasks/{task_id}**
```json
Response (200):
{
    "id": "uuid",
    "name": "Generate API",
    "description": "Generate REST API for user management",
    "task_type": "code_generation",
    "parameters": {...},
    "priority": "high",
    "status": "completed",
    "result": {
        "code": "...",
        "files": [...]
    },
    "created_at": "2024-01-16T12:00:00Z",
    "completed_at": "2024-01-16T12:05:00Z"
}
```

#### Health & Monitoring Endpoints

**GET /health**
```json
Response (200):
{
    "status": "healthy",
    "timestamp": "2024-01-16T12:00:00Z",
    "version": "1.0.0",
    "components": {
        "database": {
            "status": "healthy",
            "message": "Database connection successful"
        },
        "redis": {
            "status": "healthy",
            "message": "Redis connection successful"
        },
        "manager_agent": {
            "status": "configured",
            "message": "Manager agent URL: http://manager-agent:8000"
        }
    }
}
```

**GET /metrics**
```
Response (200):
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health",status="200"} 1523

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 1234
http_request_duration_seconds_sum 456.78
http_request_duration_seconds_count 1234

# HELP tasks_total Total tasks
# TYPE tasks_total counter
tasks_total{status="completed",type="code_generation"} 234
```

---

### Configuration Options

#### Core Settings

**Database Configuration**
```bash
# Connection URL
DATABASE_URL=postgresql://user:pass@host:5432/db

# Pool settings
DB_POOL_SIZE=20                # Number of connections in pool
DB_MAX_OVERFLOW=10            # Additional connections allowed
DB_POOL_TIMEOUT=30            # Timeout to get connection (seconds)
DB_POOL_RECYCLE=3600          # Recycle connections after (seconds)
DB_ECHO=false                 # Log SQL queries
```

**Security Configuration**
```bash
# JWT Settings
JWT_SECRET_KEY=your-256-bit-key    # CRITICAL: Change in production
JWT_ALGORITHM=RS256                # RS256 or HS256
JWT_EXPIRE_MINUTES=60              # Token expiration

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

**Agent Registry**
```bash
# Manager Agent
MANAGER_AGENT_URL=http://manager-agent:8000
MANAGER_AGENT_TIMEOUT=30

# Coding Agent
CODING_AGENT_URL=http://coding-agent:8010
CODING_AGENT_TIMEOUT=60

# Agent Communication
AGENT_REQUEST_TIMEOUT=30
AGENT_MAX_RETRIES=3
AGENT_RETRY_BACKOFF=2
AGENT_CIRCUIT_BREAKER_THRESHOLD=5
```

**Quality Verification**
```bash
# Thresholds
QUALITY_THRESHOLD=85.0           # Minimum score (0-100)
CODE_COVERAGE_MIN=80.0           # Minimum coverage %

# Weights (must sum to 1.0)
QUALITY_CODE_WEIGHT=0.35
QUALITY_SECURITY_WEIGHT=0.30
QUALITY_PERFORMANCE_WEIGHT=0.20
QUALITY_DOCUMENTATION_WEIGHT=0.15

# Features
SECURITY_SCAN_ENABLED=true
PERFORMANCE_BENCHMARK_ENABLED=true
DOCUMENTATION_CHECK_ENABLED=true
```

**File Storage**
```bash
# Backend selection
STORAGE_BACKEND=local              # local, s3, azure, gcs
STORAGE_PATH=./uploads
MAX_UPLOAD_SIZE_MB=100

# AWS S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
S3_BUCKET=ymera-files

# Versioning
FILE_VERSIONING_ENABLED=true
FILE_VERSION_RETENTION_DAYS=90
```

**Monitoring**
```bash
# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Jaeger Tracing
JAEGER_ENABLED=true
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
JAEGER_SAMPLER_TYPE=probabilistic
JAEGER_SAMPLER_PARAM=0.1          # 10% sampling

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                   # json or text
LOG_FILE=./logs/app.log
```

---

### Troubleshooting Common Issues

#### Database Connection Issues

**Problem: "Connection refused" or "Could not connect to database"**

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   # or
   systemctl status postgresql
   ```

2. Test connection manually:
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```

3. Verify DATABASE_URL format:
   ```bash
   # Correct format
   postgresql://username:password@host:port/database
   
   # For asyncpg (used by app)
   postgresql+asyncpg://username:password@host:port/database
   ```

4. Check firewall/network:
   ```bash
   telnet localhost 5432
   ```

5. Check connection pool settings:
   ```bash
   # Reduce if hitting connection limits
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=5
   ```

#### Redis Connection Issues

**Problem: "Redis connection failed" or "Connection timeout"**

**Solutions:**
1. Check Redis is running:
   ```bash
   docker ps | grep redis
   redis-cli ping  # Should return PONG
   ```

2. Verify REDIS_URL:
   ```bash
   # Correct format
   redis://localhost:6379/0
   
   # With password
   redis://:password@localhost:6379/0
   ```

3. Test connection:
   ```bash
   redis-cli -u $REDIS_URL ping
   ```

#### Agent Communication Timeouts

**Problem: "Agent timeout" or "No response from agent"**

**Solutions:**
1. Check agent health:
   ```bash
   curl http://coding-agent:8010/health
   ```

2. Verify agent URL configuration:
   ```bash
   echo $CODING_AGENT_URL
   # Should be reachable from Project Agent
   ```

3. Check network policies (Kubernetes):
   ```bash
   kubectl get networkpolicies
   kubectl describe networkpolicy <policy-name>
   ```

4. Increase timeout for slow operations:
   ```bash
   CODING_AGENT_TIMEOUT=120  # Increase from 60 to 120 seconds
   ```

5. Check circuit breaker status:
   ```bash
   # Circuit opens after 5 consecutive failures
   AGENT_CIRCUIT_BREAKER_THRESHOLD=5
   AGENT_CIRCUIT_BREAKER_TIMEOUT=60
   ```

#### Authentication Errors

**Problem: "Invalid token" or "Token expired"**

**Solutions:**
1. Check JWT secret is set:
   ```bash
   echo $JWT_SECRET_KEY
   # Should be at least 32 characters
   ```

2. Verify token format:
   ```bash
   # Should be: Bearer <token>
   Authorization: Bearer eyJhbGc...
   ```

3. Check token expiration:
   ```bash
   JWT_EXPIRE_MINUTES=60  # Default 60 minutes
   ```

4. Regenerate token:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -d '{"username":"user","password":"pass"}'
   ```

#### High Memory Usage

**Problem: Application consuming excessive memory**

**Solutions:**
1. Check connection pool size:
   ```bash
   DB_POOL_SIZE=20        # Reduce if needed
   REDIS_MAX_CONNECTIONS=50
   ```

2. Review cache settings:
   ```bash
   CACHE_MAX_SIZE_MB=500  # Reduce cache size
   CACHE_TTL_SECONDS=300  # Shorter TTL
   ```

3. Monitor with Prometheus:
   ```bash
   curl http://localhost:8000/metrics | grep memory
   ```

4. Increase worker memory limit (Kubernetes):
   ```yaml
   resources:
     limits:
       memory: "2Gi"
     requests:
       memory: "1Gi"
   ```

#### Slow API Responses

**Problem: API endpoints taking too long to respond**

**Solutions:**
1. Check database query performance:
   ```bash
   # Enable query logging
   DB_ECHO=true
   
   # Check slow queries in PostgreSQL
   SELECT query, mean_exec_time 
   FROM pg_stat_statements 
   ORDER BY mean_exec_time DESC 
   LIMIT 10;
   ```

2. Add database indexes:
   ```sql
   CREATE INDEX idx_tasks_status ON tasks(status);
   CREATE INDEX idx_tasks_user_id ON tasks(user_id);
   ```

3. Enable caching:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   async def get_user(user_id: str):
       # Cached for repeated calls
   ```

4. Check Prometheus metrics:
   ```bash
   curl http://localhost:8000/metrics | grep duration
   ```

#### Migration Failures

**Problem: "Alembic migration failed" or "Database schema error"**

**Solutions:**
1. Check current migration version:
   ```bash
   alembic current
   ```

2. Show migration history:
   ```bash
   alembic history
   ```

3. Manually fix and retry:
   ```bash
   # Downgrade one version
   alembic downgrade -1
   
   # Apply again
   alembic upgrade head
   ```

4. Generate new migration:
   ```bash
   alembic revision --autogenerate -m "Fix schema"
   ```

5. Manual SQL execution:
   ```bash
   psql $DATABASE_URL -f migrations/manual_fix.sql
   ```

#### Docker Compose Issues

**Problem: Services not starting or crashing**

**Solutions:**
1. Check logs:
   ```bash
   docker-compose logs -f postgres
   docker-compose logs -f redis
   ```

2. Verify volumes:
   ```bash
   docker volume ls
   docker volume inspect ymera_postgres_data
   ```

3. Clean restart:
   ```bash
   docker-compose down -v  # Remove volumes
   docker-compose up -d
   ```

4. Check resource limits:
   ```bash
   docker stats
   ```

#### Test Failures

**Problem: Tests failing unexpectedly**

**Solutions:**
1. Run specific test:
   ```bash
   pytest tests/unit/test_auth.py -v
   ```

2. Clear test database:
   ```bash
   pytest --create-db
   ```

3. Check test dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run with debug output:
   ```bash
   pytest -vv -s tests/
   ```

---

## Additional Resources

### Documentation
- **Architecture**: See [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)
- **Deployment**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Implementation**: See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- **API Reference**: http://localhost:8000/docs

### Community
- **GitHub**: https://github.com/ymera-mfm/ymera_y
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code of Conduct**: See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

### Support
- **Issues**: Open issue on GitHub
- **Documentation**: Full docs at http://docs.ymera.com
- **Email**: support@ymera.com

---

**Last Updated**: 2024-01-16
**Version**: 1.0.0
**Status**: Production Ready ✅
