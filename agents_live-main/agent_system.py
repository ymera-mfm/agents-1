# main.py - Production-Ready Agent Management System
"""
Enterprise Agent Management Platform
Focus: Simplicity, Reliability, Performance
"""

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Text, ForeignKey, select, Index
from sqlalchemy.orm import declarative_base, relationship, selectinload
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import asyncio
import logging
import os
import json
import uuid
import hashlib
import bcrypt
from jose import JWTError, jwt
import redis.asyncio as aioredis
from prometheus_client import Counter, Histogram, generate_latest
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# MODELS & SCHEMAS
# =============================================================================

Base = declarative_base()

class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents = relationship("Agent", back_populates="owner")
    tasks = relationship("Task", back_populates="user")

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    capabilities = Column(JSON, default=list)
    status = Column(String(20), default=AgentStatus.INACTIVE)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    config = Column(JSON, default=dict)
    last_heartbeat = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="agents")
    tasks = relationship("Task", back_populates="agent")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)
    parameters = Column(JSON, default=dict)
    priority = Column(String(20), default=TaskPriority.NORMAL)
    status = Column(String(20), default=TaskStatus.PENDING, index=True)
    result = Column(JSON)
    error_message = Column(Text)
    
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    agent = relationship("Agent", back_populates="tasks")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_task_user_status', 'user_id', 'status'),
        Index('idx_task_status_created', 'status', 'created_at'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), default='success')
    details = Column(JSON, default=dict)

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    capabilities: List[str]
    status: AgentStatus
    last_heartbeat: Optional[datetime]
    created_at: datetime

class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: str = Field(..., min_length=1, max_length=50)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    agent_id: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    task_type: str
    parameters: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

# =============================================================================
# CORE SERVICES
# =============================================================================

class DatabaseManager:
    def __init__(self, database_url: str):
        # Configure connection pool for production use
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,              # Maintain 20 connections in the pool
            max_overflow=40,           # Allow up to 40 additional connections under load
            pool_pre_ping=True,        # Verify connections before using them
            pool_recycle=3600,         # Recycle connections after 1 hour
            connect_args={
                "server_settings": {
                    "application_name": "ymera_agent_system",
                },
                "timeout": 30,
                "command_timeout": 30,
            }
        )
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session
    
    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

# =============================================================================
# AUDIT LOGGING
# =============================================================================

async def log_audit_event(
    session: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log an audit event to the database"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        session.add(audit_log)
        await session.commit()
        logger.info(f"Audit log created: {action} on {resource_type} by user {user_id}")
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Don't raise - audit logging should not break the application

# =============================================================================
# AUTHENTICATION & AUTHORIZATION
# =============================================================================

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    async def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

class TaskQueue:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.queue_name = "agent_tasks"
    
    async def enqueue_task(self, task_data: dict, priority: TaskPriority = TaskPriority.NORMAL):
        priority_score = {
            TaskPriority.CRITICAL: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 1
        }[priority]
        
        await self.redis.zadd(
            self.queue_name, 
            {json.dumps(task_data): priority_score}
        )
    
    async def dequeue_task(self) -> Optional[dict]:
        task_data = await self.redis.zpopmax(self.queue_name)
        if task_data:
            return json.loads(task_data[0][0])
        return None

class AgentManager:
    def __init__(self, db_session_factory, task_queue: TaskQueue):
        self.db_session_factory = db_session_factory
        self.task_queue = task_queue
        self.active_agents = {}
    
    async def register_agent(self, agent_data: dict) -> str:
        async with self.db_session_factory() as session:
            agent = Agent(**agent_data)
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
            return agent.id
    
    async def assign_task_to_agent(self, task_id: str, agent_id: Optional[str] = None) -> str:
        async with self.db_session_factory() as session:
            # Get task
            task = await session.get(Task, task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            # Find best agent if not specified
            if not agent_id:
                agent_id = await self._find_best_agent(task, session)
            
            if not agent_id:
                raise HTTPException(status_code=400, detail="No suitable agent available")
            
            # Assign task
            task.agent_id = agent_id
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            
            await session.commit()
            
            # Add to task queue
            await self.task_queue.enqueue_task({
                "task_id": task_id,
                "agent_id": agent_id,
                "task_type": task.task_type,
                "parameters": task.parameters
            }, TaskPriority(task.priority))
            
            return agent_id
    
    async def _find_best_agent(self, task: Task, session: AsyncSession) -> Optional[str]:
        # Simple agent selection based on availability and capabilities
        result = await session.execute(
            select(Agent).where(
                Agent.status == AgentStatus.ACTIVE,
                Agent.capabilities.contains([task.task_type])
            )
        )
        agents = result.scalars().all()
        
        if agents:
            # Return first available agent (can be enhanced with load balancing)
            return agents[0].id
        return None

# =============================================================================
# METRICS & MONITORING
# =============================================================================

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
TASK_COUNT = Counter('tasks_total', 'Total tasks', ['status', 'type'])

# =============================================================================
# APPLICATION SETUP
# =============================================================================

# Global instances
db_manager = None
auth_service = None
task_queue = None
agent_manager = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_manager, auth_service, task_queue, agent_manager, redis_client
    
    # Initialize services
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # JWT Secret must be provided and be at least 32 characters
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise ValueError("JWT_SECRET environment variable is required")
    if len(jwt_secret) < 32:
        raise ValueError("JWT_SECRET must be at least 32 characters long")
    if jwt_secret == "your-secret-key-change-in-production":
        raise ValueError("JWT_SECRET must be changed from the default value")
    
    # Setup database
    db_manager = DatabaseManager(database_url)
    await db_manager.create_tables()
    
    # Setup Redis
    redis_client = await aioredis.from_url(redis_url)
    
    # Initialize services
    auth_service = AuthService(jwt_secret)
    task_queue = TaskQueue(redis_client)
    agent_manager = AgentManager(db_manager.async_session, task_queue)
    
    # Start background task processor
    asyncio.create_task(process_tasks())
    
    logger.info("Agent Management System started")
    yield
    
    # Cleanup
    await redis_client.close()
    await db_manager.engine.dispose()

app = FastAPI(
    title="Agent Management System",
    description="Production-ready enterprise agent management platform",
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with consistent error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": request.url.path,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "path": request.url.path,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# Add CORS middleware with proper security
# Load CORS origins from environment variable
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
# Parse comma-separated list
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Restricted to configured origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# =============================================================================
# METRICS MIDDLEWARE
# =============================================================================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request metrics"""
    import time
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

# =============================================================================
# AUTHENTICATION & SECURITY
# =============================================================================

# Security
security = HTTPBearer()

# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """Simple rate limiter using Redis"""
    def __init__(self, redis_client, max_requests: int = 10, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        key = f"rate_limit:{client_id}"
        current_time = datetime.utcnow().timestamp()
        
        # Remove old entries
        await self.redis.zremrangebyscore(key, '-inf', current_time - self.window_seconds)
        
        # Count requests in window
        count = await self.redis.zcard(key)
        
        if count >= self.max_requests:
            return False
        
        # Add current request
        await self.redis.zadd(key, {str(current_time): current_time})
        await self.redis.expire(key, self.window_seconds)
        return True

# Rate limiter dependency for auth endpoints
async def rate_limit_auth(request: Request):
    """Rate limit authentication endpoints"""
    rate_limiter = RateLimiter(redis_client, max_requests=5, window_seconds=60)
    client_ip = request.client.host if request.client else "unknown"
    
    if not await rate_limiter.check_rate_limit(f"auth:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )

# =============================================================================
# AUTHENTICATION
# =============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = await auth_service.verify_token(credentials.credentials)
    user_id = payload.get("sub")
    
    async with db_manager.async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user

# =============================================================================
# API ROUTES
# =============================================================================

@app.post("/auth/register", response_model=dict, status_code=201)
async def register(
    user_data: UserCreate, 
    request: Request,
    _rate_limit: None = Depends(rate_limit_auth)
):
    async with db_manager.async_session() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(
                (User.username == user_data.username) | (User.email == user_data.email)
            )
        )
        if result.scalar_one_or_none():
            await log_audit_event(
                session=session,
                action="register_failed",
                resource_type="user",
                resource_id=None,
                user_id=None,
                status="failure",
                details={"username": user_data.username, "reason": "already_exists"},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            raise HTTPException(
                status_code=400, 
                detail="Username or email already registered"
            )
        
        # Create user
        hashed_password = auth_service.hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Log successful registration
        await log_audit_event(
            session=session,
            action="user_registered",
            resource_type="user",
            resource_id=user.id,
            user_id=user.id,
            status="success",
            details={"username": user.username, "email": user.email},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Create access token
        access_token = auth_service.create_access_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id
        }

@app.post("/auth/login")
async def login(
    username: str, 
    password: str, 
    request: Request,
    _rate_limit: None = Depends(rate_limit_auth)
):
    async with db_manager.async_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        # Log failed login attempt
        if not user or not auth_service.verify_password(password, user.password_hash):
            await log_audit_event(
                session=session,
                action="login_failed",
                resource_type="auth",
                resource_id=None,
                user_id=None,
                status="failure",
                details={"username": username},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        access_token = auth_service.create_access_token(data={"sub": user.id})
        
        # Log successful login
        await log_audit_event(
            session=session,
            action="login_success",
            resource_type="auth",
            resource_id=user.id,
            user_id=user.id,
            status="success",
            details={"username": username},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id
        }

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/agents", response_model=dict, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    async with db_manager.async_session() as session:
        agent = Agent(
            name=agent_data.name,
            description=agent_data.description,
            capabilities=agent_data.capabilities,
            config=agent_data.config,
            owner_id=current_user.id
        )
        
        session.add(agent)
        await session.commit()
        await session.refresh(agent)
        
        # Log agent creation
        await log_audit_event(
            session=session,
            action="agent_created",
            resource_type="agent",
            resource_id=agent.id,
            user_id=current_user.id,
            status="success",
            details={"name": agent.name, "capabilities": agent.capabilities},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return {"agent_id": agent.id, "status": "created"}

@app.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """
    List agents with pagination and optional filtering
    
    - skip: Number of agents to skip (default: 0)
    - limit: Maximum number of agents to return (default: 100, max: 1000)
    - status: Filter by agent status (optional)
    """
    if limit > 1000:
        limit = 1000
    
    async with db_manager.async_session() as session:
        query = select(Agent).where(Agent.owner_id == current_user.id)
        
        # Add status filter if provided
        if status:
            query = query.where(Agent.status == status)
        
        # Add pagination and ordering
        query = query.order_by(Agent.created_at.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        agents = result.scalars().all()
        return agents

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    async with db_manager.async_session() as session:
        agent = await session.get(Agent, agent_id)
        
        if not agent or agent.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agent

@app.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    status_data: dict,
    current_user: User = Depends(get_current_user)
):
    async with db_manager.async_session() as session:
        agent = await session.get(Agent, agent_id)
        
        if not agent or agent.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent.last_heartbeat = datetime.utcnow()
        agent.status = status_data.get("status", AgentStatus.ACTIVE)
        
        await session.commit()
        
        return {"status": "heartbeat_received"}

@app.post("/tasks", response_model=dict, status_code=201)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    async with db_manager.async_session() as session:
        task = Task(
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            parameters=task_data.parameters,
            priority=task_data.priority,
            user_id=current_user.id,
            agent_id=task_data.agent_id
        )
        
        session.add(task)
        await session.commit()
        await session.refresh(task)
        
        # Assign to agent and queue for processing
        background_tasks.add_task(
            agent_manager.assign_task_to_agent, 
            task.id, 
            task_data.agent_id
        )
        
        TASK_COUNT.labels(status="created", type=task.task_type).inc()
        
        return {"task_id": task.id, "status": "created"}

@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """
    List tasks with pagination and optional filtering
    
    - skip: Number of tasks to skip (default: 0)
    - limit: Maximum number of tasks to return (default: 100, max: 1000)
    - status: Filter by task status (optional)
    """
    if limit > 1000:
        limit = 1000
    
    async with db_manager.async_session() as session:
        query = select(Task).where(Task.user_id == current_user.id)
        
        # Add status filter if provided
        if status:
            query = query.where(Task.status == status)
        
        # Add pagination and ordering
        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
        
        result = await session.execute(query)
        tasks = result.scalars().all()
        return tasks

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    async with db_manager.async_session() as session:
        task = await session.get(Task, task_id)
        
        if not task or task.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Checks database, Redis, and application status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        async with db_manager.async_session() as session:
            await session.execute(select(1))
        health_status["checks"]["database"] = {
            "status": "up",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": "down",
            "message": f"Database error: {str(e)}"
        }
    
    # Check Redis connectivity
    try:
        await redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "up",
            "message": "Redis connection successful"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = {
            "status": "down",
            "message": f"Redis error: {str(e)}"
        }
    
    # Add application info
    health_status["checks"]["application"] = {
        "status": "up",
        "message": "Application running"
    }
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/metrics")
async def get_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# =============================================================================
# BACKGROUND TASK PROCESSOR
# =============================================================================

async def process_tasks():
    """Background task processor"""
    logger.info("Task processor started")
    
    while True:
        try:
            task_data = await task_queue.dequeue_task()
            
            if task_data:
                logger.info(f"Processing task: {task_data['task_id']}")
                
                # Process the task (implement your task processing logic here)
                await process_single_task(task_data)
            else:
                # No tasks, wait a bit
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Task processing error: {e}")
            await asyncio.sleep(5)

async def process_single_task(task_data: dict):
    """Process a single task with improved error handling"""
    task_id = task_data["task_id"]
    max_retries = 3
    retry_count = 0
    
    async with db_manager.async_session() as session:
        task = await session.get(Task, task_id)
        
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        # Mark task as in progress
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        await session.commit()
        
        while retry_count < max_retries:
            try:
                # Simulate task processing
                logger.info(f"Processing task {task_id} of type {task.task_type} (attempt {retry_count + 1})")
                
                # Here you would implement actual task processing logic
                # For demo purposes, we'll simulate some work
                await asyncio.sleep(2)
                
                # Mark task as completed
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = {
                    "status": "success", 
                    "message": "Task completed successfully",
                    "attempts": retry_count + 1
                }
                
                TASK_COUNT.labels(status="completed", type=task.task_type).inc()
                logger.info(f"Task {task_id} completed successfully")
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Task {task_id} failed (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    # Max retries reached, mark as failed
                    task.status = TaskStatus.FAILED
                    task.error_message = f"Failed after {max_retries} attempts: {str(e)}"
                    task.completed_at = datetime.utcnow()
                    TASK_COUNT.labels(status="failed", type=task.task_type).inc()
                    logger.error(f"Task {task_id} permanently failed after {max_retries} attempts")
                else:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** retry_count
                    logger.info(f"Retrying task {task_id} in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
        
        await session.commit()

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Use environment variable for host, default to localhost for security
    # Only bind to 0.0.0.0 in production with proper firewall rules
    host = os.getenv("API_HOST", "127.0.0.1")  # Default to localhost
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
