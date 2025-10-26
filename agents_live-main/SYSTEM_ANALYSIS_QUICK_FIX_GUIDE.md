# YMERA Platform - Quick Fix Guide

**Purpose:** Step-by-step guide to fix critical issues identified in system analysis  
**Target Audience:** Developers implementing fixes  
**Estimated Time:** Follow phases sequentially

---

## 🚀 Quick Start: Fix Critical Issues First

### Prerequisites
```bash
cd /home/runner/work/Agents-00/Agents-00
source venv/bin/activate
pip install -r requirements.txt
```

---

## Phase 1: Security Fixes (Day 1-2)

### Fix 1: JWT Secret Management (30 minutes)

**Problem:** JWT secret is hardcoded  
**File:** `core/config.py`

**Step 1: Update config.py**
```python
# core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Database
    database_url: str = Field(..., env='DATABASE_URL')
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env='REDIS_URL')
    
    # JWT Configuration
    jwt_secret: str = Field(..., min_length=32, env='JWT_SECRET_KEY')
    jwt_algorithm: str = Field(default="HS256", env='JWT_ALGORITHM')
    jwt_expiration_minutes: int = Field(default=30, env='JWT_EXPIRATION_MINUTES')
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        env='CORS_ORIGINS'
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env='API_HOST')
    api_port: int = Field(default=8000, env='API_PORT')
    debug: bool = Field(default=False, env='DEBUG')
    
    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if v == "your-secret-key-change-in-production":
            raise ValueError("JWT secret must be changed from default value")
        if len(v) < 32:
            raise ValueError("JWT secret must be at least 32 characters")
        return v
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton pattern for settings
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**Step 2: Update .env file**
```bash
# Generate a secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))" > jwt_secret.txt

# Add to .env
cat >> .env << EOF
JWT_SECRET_KEY=$(cat jwt_secret.txt)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
EOF

# Clean up
rm jwt_secret.txt
```

**Step 3: Update main.py to use settings**
```python
# main.py
from core.config import get_settings

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ← Changed from ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Step 4: Test**
```bash
# Should fail with invalid secret
JWT_SECRET_KEY="short" python -c "from core.config import get_settings; get_settings()"

# Should succeed with valid secret
JWT_SECRET_KEY="a_very_long_secret_key_that_is_at_least_32_characters_long" \
python -c "from core.config import get_settings; print('Config loaded successfully')"
```

### Fix 2: Audit Logging (2 hours)

**Problem:** Audit logs defined but not used  
**Files:** Create `core/audit.py`, update route handlers

**Step 1: Create audit logging module**
```python
# core/audit.py
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger()

class AuditLogger:
    """Centralized audit logging"""
    
    @staticmethod
    async def log_event(
        db: AsyncSession,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        status: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log an audit event"""
        try:
            # Log to database
            audit_entry = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "status": status,
                "details": details or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow()
            }
            
            # Insert into audit_logs table
            from core.database import AuditLog
            db.add(AuditLog(**audit_entry))
            await db.commit()
            
            # Also log to application logs
            logger.info(
                "audit_event",
                **audit_entry
            )
            
        except Exception as e:
            logger.error("audit_logging_failed", error=str(e))
            # Don't raise - audit logging should not break the application


# Decorator for automatic audit logging
from functools import wraps
from fastapi import Request

def audit_log(action: str, resource_type: str):
    """Decorator to automatically audit log endpoint calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user from kwargs
            request: Optional[Request] = kwargs.get('request')
            current_user = kwargs.get('current_user')
            
            user_id = current_user.id if current_user else None
            ip_address = request.client.host if request else None
            user_agent = request.headers.get('user-agent') if request else None
            
            # Execute the function
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                if request:
                    db = kwargs.get('db')
                    if db:
                        await AuditLogger.log_event(
                            db=db,
                            user_id=user_id,
                            action=action,
                            resource_type=resource_type,
                            resource_id=getattr(result, 'id', None),
                            status="success",
                            ip_address=ip_address,
                            user_agent=user_agent
                        )
                
                return result
                
            except Exception as e:
                # Log failure
                if request:
                    db = kwargs.get('db')
                    if db:
                        await AuditLogger.log_event(
                            db=db,
                            user_id=user_id,
                            action=action,
                            resource_type=resource_type,
                            resource_id=None,
                            status="failed",
                            details={"error": str(e)},
                            ip_address=ip_address,
                            user_agent=user_agent
                        )
                raise
                
        return wrapper
    return decorator
```

**Step 2: Add AuditLog model to database.py**
```python
# Add to core/database.py or sqlalchemy_models.py
from sqlalchemy import Column, String, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), index=True, nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False)  # success, failed
    details = Column(JSONB, default={})
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
    )
```

**Step 3: Use in route handlers**
```python
# Example usage in routes
from core.audit import audit_log, AuditLogger

@app.post("/api/v1/agents")
@audit_log(action="agent_create", resource_type="agent")
async def create_agent(
    agent_data: AgentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Your existing code
    pass

# Or manual logging
@app.post("/api/v1/auth/login")
async def login(
    credentials: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await authenticate_user(db, credentials.email, credentials.password)
        
        # Log successful login
        await AuditLogger.log_event(
            db=db,
            user_id=user.id,
            action="user_login",
            resource_type="auth",
            resource_id=user.id,
            status="success",
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent')
        )
        
        return {"access_token": create_token(user)}
        
    except AuthenticationError:
        # Log failed login
        await AuditLogger.log_event(
            db=db,
            user_id=None,
            action="user_login",
            resource_type="auth",
            resource_id=None,
            status="failed",
            details={"email": credentials.email},
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent')
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

**Step 4: Create migration**
```bash
# Create migration for audit_logs table
alembic revision --autogenerate -m "Add audit_logs table"

# Review the migration file
cat alembic/versions/*_add_audit_logs_table.py

# Apply migration
alembic upgrade head
```

**Step 5: Test**
```bash
# Test audit logging
pytest tests/unit/test_audit.py -v
```

### Fix 3: Database Connection Pooling (30 minutes)

**Problem:** No connection pool configuration  
**File:** `core/database.py`

**Update database.py:**
```python
# core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import get_settings

settings = get_settings()

# Configure engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    
    # Connection pool settings
    pool_size=20,              # Maintain 20 connections
    max_overflow=40,           # Allow up to 40 additional connections
    pool_pre_ping=True,        # Test connections before using
    pool_recycle=3600,         # Recycle connections after 1 hour
    
    # Performance settings
    echo=False,                # Don't log SQL queries in production
    future=True,               # Use SQLAlchemy 2.0 style
    
    # Connection settings
    connect_args={
        "server_settings": {
            "application_name": "ymera_platform",
        },
        "timeout": 30,
        "command_timeout": 30,
    }
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Test connection pooling:**
```python
# Test script: test_connection_pool.py
import asyncio
from core.database import engine

async def test_pool():
    """Test connection pool"""
    print(f"Pool size: {engine.pool.size()}")
    print(f"Checked out: {engine.pool.checkedout()}")
    
    # Create many concurrent connections
    async def query():
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
    
    # Should handle 60 concurrent connections (20 + 40 overflow)
    await asyncio.gather(*[query() for _ in range(60)])
    print("Connection pool test passed!")

asyncio.run(test_pool())
```

---

## Phase 2: Database Schema Fix (Day 3-4)

### Fix 4: Schema Reconciliation (4 hours)

**Problem:** SQLAlchemy models don't match SQL schema

**Step 1: Update User model with security fields**
```python
# core/database.py or sqlalchemy_models.py
from sqlalchemy import Column, String, Boolean, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import JSONB

class User(Base):
    __tablename__ = "users"
    
    # Existing fields
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(50), default="user")
    
    # Security fields (NEW)
    risk_score = Column(Float, default=0.0)
    mfa_enabled = Column(Boolean, default=False)
    mfa_method = Column(String(50), nullable=True)  # 'totp', 'sms', 'email'
    webauthn_credentials = Column(JSONB, default={})
    adaptive_auth_factors = Column(JSONB, default={})
    permissions = Column(JSONB, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="user")
```

**Step 2: Create comprehensive migration**
```bash
# Generate migration
alembic revision --autogenerate -m "Add security fields to users table"

# Review and edit migration if needed
vim alembic/versions/*_add_security_fields_to_users_table.py

# Apply migration
alembic upgrade head
```

**Step 3: Verify schema**
```bash
# Connect to database and verify
psql $DATABASE_URL -c "\d users"
psql $DATABASE_URL -c "\d audit_logs"
psql $DATABASE_URL -c "\d agents"
psql $DATABASE_URL -c "\d tasks"
```

---

## Phase 3: Configuration Consolidation (Day 5)

### Fix 5: Merge Configuration Files (2 hours)

**Problem:** Multiple config files not integrated

**Step 1: Extend Settings class**
```python
# core/config.py (extend existing Settings class)

class Settings(BaseSettings):
    # ... existing fields ...
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env='RATE_LIMIT_ENABLED')
    rate_limit_per_minute: int = Field(default=60, env='RATE_LIMIT_PER_MINUTE')
    
    # Security
    password_min_length: int = Field(default=8, env='PASSWORD_MIN_LENGTH')
    session_timeout_minutes: int = Field(default=30, env='SESSION_TIMEOUT_MINUTES')
    
    # MFA
    mfa_required: bool = Field(default=False, env='MFA_REQUIRED')
    mfa_issuer_name: str = Field(default="YMERA", env='MFA_ISSUER_NAME')
    
    # OAuth2
    oauth_google_client_id: str = Field(default="", env='OAUTH_GOOGLE_CLIENT_ID')
    oauth_google_client_secret: str = Field(default="", env='OAUTH_GOOGLE_CLIENT_SECRET')
    oauth_github_client_id: str = Field(default="", env='OAUTH_GITHUB_CLIENT_ID')
    oauth_github_client_secret: str = Field(default="", env='OAUTH_GITHUB_CLIENT_SECRET')
    
    # Monitoring
    prometheus_enabled: bool = Field(default=True, env='PROMETHEUS_ENABLED')
    sentry_dsn: str = Field(default="", env='SENTRY_DSN')
    
    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        env='KAFKA_BOOTSTRAP_SERVERS'
    )
    kafka_enabled: bool = Field(default=False, env='KAFKA_ENABLED')
```

**Step 2: Remove old config files**
```bash
# After merging into core/config.py, mark old files as deprecated
mv ProductionConfig.py ProductionConfig.py.deprecated
mv ZeroTrustConfig.py ZeroTrustConfig.py.deprecated

# Add deprecation notice
echo "# DEPRECATED: Configuration moved to core/config.py" > ProductionConfig.py
```

**Step 3: Update all imports**
```bash
# Find all files importing old config
grep -r "from ProductionConfig import" . --include="*.py"
grep -r "from ZeroTrustConfig import" . --include="*.py"

# Update to use new config
# Replace with: from core.config import get_settings
```

---

## Phase 4: Testing & Validation

### Run Full Test Suite
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all tests
pytest -v --cov=. --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/security/ -v

# Check coverage
open htmlcov/index.html  # or xdg-open on Linux
```

### Run Security Scans
```bash
# Security linting
bandit -r . -ll

# Dependency audit
pip-audit

# Check for common vulnerabilities
safety check
```

### Run Code Quality Checks
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

---

## Verification Checklist

After completing all fixes, verify:

- [ ] JWT secret is loaded from environment (not hardcoded)
- [ ] CORS origins are restricted (not "*")
- [ ] Audit logging works (check database has audit_logs entries)
- [ ] Database connection pooling configured (check engine settings)
- [ ] Configuration consolidated (only using core/config.py)
- [ ] All tests pass (`pytest` returns 0 exit code)
- [ ] No security issues (`bandit -r . -ll` returns 0 issues)
- [ ] Code formatted (`black . --check` passes)
- [ ] Code linted (`flake8 .` passes)
- [ ] Application starts (`uvicorn main:app` runs without errors)

---

## Testing the Fixes

### Start the Application
```bash
# Set environment variables
export JWT_SECRET_KEY="your_secure_32_plus_character_secret_key_here"
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/ymera"
export REDIS_URL="redis://localhost:6379/0"
export CORS_ORIGINS="http://localhost:3000"

# Start application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Test Endpoints
```bash
# Check health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics

# Test API docs
open http://localhost:8000/docs
```

### Test Authentication
```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepassword123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepassword123"}'

# Check audit logs in database
psql $DATABASE_URL -c "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5;"
```

---

## Common Issues & Solutions

### Issue: "JWT secret must be at least 32 characters"
**Solution:** Set a longer JWT_SECRET_KEY in .env
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Issue: "No module named 'core.config'"
**Solution:** Ensure core/__init__.py exists and imports are correct
```bash
touch core/__init__.py
```

### Issue: Database migration fails
**Solution:** Check database connection and current schema state
```bash
alembic current
alembic history
```

### Issue: Redis connection refused
**Solution:** Start Redis server
```bash
redis-server
# or
docker run -d -p 6379:6379 redis:latest
```

---

## Next Steps

After completing these critical fixes:

1. **Deploy to Staging:** Test in staging environment
2. **Run Load Tests:** Use locust or k6 to test performance
3. **Security Audit:** External security review
4. **Documentation:** Update deployment docs
5. **Production Deploy:** Gradual rollout with monitoring

---

## Support & Resources

- **Full Analysis:** `SYSTEM_ANALYSIS_COMPREHENSIVE.md`
- **Executive Summary:** `SYSTEM_ANALYSIS_EXECUTIVE_SUMMARY.md`
- **API Docs:** http://localhost:8000/docs (when running)
- **GitHub Issues:** For tracking fixes

**Estimated Time to Complete All Fixes:** 16-20 hours (2-3 days)
