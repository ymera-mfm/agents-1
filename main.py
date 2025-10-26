# main.py - Production-Ready Agent Management System
"""
Enterprise Agent Management Platform
Focus: Simplicity, Reliability, Performance
"""

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import asyncio
import logging
import os
import json
import uuid
import redis.asyncio as aioredis
from prometheus_client import Counter, Histogram, generate_latest
import uvicorn

from core.config import Settings
from core.sqlalchemy_models import Base, User, Agent, Task, AgentStatus, TaskStatus, TaskPriority
from core.auth import AuthService
from core.database import Database
from middleware.rate_limiter import RateLimitMiddleware
from core.manager_client import ManagerClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# MODELS & SCHEMAS
# =============================================================================



# Pydantic Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
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
    def __init__(self, db_client: Database, task_queue: TaskQueue, manager_client: ManagerClient):
        self.db_client = db_client
        self.task_queue = task_queue
        self.manager_client = manager_client
        self.active_agents = {}
    
    async def register_agent(self, agent_data: dict) -> str:
        new_agent_id = uuid.uuid4()
        await self.db_client.execute_command(
            "INSERT INTO agents (id, name, description, capabilities, config, owner_id, status) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            new_agent_id, agent_data["name"], agent_data["description"], json.dumps(agent_data["capabilities"]), json.dumps(agent_data["config"]), agent_data["owner_id"], AgentStatus.INACTIVE.value
        )
        # Register with Manager Agent if URL is configured
        if self.manager_client:
            manager_agent_id = await self.manager_client.register_agent({
                "id": str(new_agent_id),
                "name": agent_data["name"],
                "description": agent_data["description"],
                "capabilities": agent_data["capabilities"],
                "config": agent_data["config"],
                "owner_id": agent_data["owner_id"]
            })
            if manager_agent_id:
                logger.info(f"Agent {new_agent_id} successfully registered with Manager Agent as {manager_agent_id}")
            else:
                logger.warning(f"Failed to register agent {new_agent_id} with Manager Agent.")
        return str(new_agent_id)

    
    async def assign_task_to_agent(self, task_id: str, agent_id: Optional[str] = None) -> str:
        # Get task
        task_record = await self.db_client.execute_single("SELECT * FROM tasks WHERE id = $1", task_id)
        if not task_record:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Find best agent if not specified
        if not agent_id:
            agent_id = await self._find_best_agent(task_record)
        
        if not agent_id:
            raise HTTPException(status_code=400, detail="No suitable agent available")
        
        # Assign task
        await self.db_client.execute_command(
            "UPDATE tasks SET agent_id = $1, status = $2, started_at = NOW() WHERE id = $3",
            agent_id, TaskStatus.RUNNING.value, task_id
        )
        
        # Add to task queue
        await self.task_queue.enqueue_task({
            "task_id": task_id,
            "agent_id": agent_id,
            "task_type": task_record["task_type"],
            "parameters": task_record["parameters"]
        }, TaskPriority(task_record["priority"]))
        
        return agent_id
    
    async def _find_best_agent(self, task_record: dict) -> Optional[str]:
        # Simple agent selection based on availability and capabilities
        agents = await self.db_client.execute_query(
            "SELECT id FROM agents WHERE status = $1 AND capabilities @> $2::jsonb",
            AgentStatus.ACTIVE.value, json.dumps([task_record["task_type"]])
        )
        
        if agents:
            # Return first available agent (can be enhanced with load balancing)
            return str(agents[0]["id"])
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
settings = Settings()
db_client: Optional[Database] = None
auth_service: Optional[AuthService] = None
task_queue: Optional[TaskQueue] = None
agent_manager: Optional[AgentManager] = None
manager_client: Optional[ManagerClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, auth_service, task_queue, agent_manager, manager_client
    
    # Initialize services
    db_client = Database(settings.database_url)
    await db_client.initialize()
    
    auth_service = AuthService(settings)
    task_queue = TaskQueue(aioredis.from_url(settings.redis_url))
    manager_client = ManagerClient(settings)
    agent_manager = AgentManager(db_client, task_queue, manager_client)
    
    # Start background task processor
    asyncio.create_task(process_tasks())
    
    logger.info("Agent Management System started")
    try:
        yield
    finally:
        logger.info("Agent Management System shutting down...")
        # Cleanup
        if db_client:
            await db_client.close()
        if task_queue and task_queue.redis:
            await task_queue.redis.close()
        if manager_client:
            await manager_client.shutdown()
        logger.info("Agent Management System shutdown complete.")

app = FastAPI(
    title="Agent Management System",
    description="Production-ready enterprise agent management platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add security middleware
from middleware.security import (
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    RequestLoggingMiddleware,
    RequestTimeoutMiddleware
)

# Order matters - add in correct sequence
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestTimeoutMiddleware, timeout_seconds=30)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)  # 10MB
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware with proper configuration
# In production, restrict origins to specific domains
allowed_origins = settings.cors_origins if hasattr(settings, 'cors_origins') and settings.cors_origins else ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Configure from settings, not wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Security
security = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    payload = auth_service.decode_access_token(token.credentials)
    user_id = payload.get("id")
    
    user_data = await db_client.execute_single("SELECT * FROM users WHERE id = $1", user_id)
        
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return UserResponse(**user_data) # Convert dictionary to UserResponse Pydantic model

# =============================================================================
# API ROUTES
# =============================================================================

@app.post("/auth/register", response_model=dict, status_code=201)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db_client.execute_single(
        "SELECT id FROM users WHERE email = $1", user_data.email
    )
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = auth_service.get_password_hash(user_data.password)
    new_user_id = uuid.uuid4()
    await db_client.execute_command(
        "INSERT INTO users (id, username, email, first_name, last_name, hashed_password) VALUES ($1, $2, $3, $4, $5, $6)",
        new_user_id, user_data.username, user_data.email, user_data.first_name, user_data.last_name, hashed_password
    )
    
    # Create access token
    access_token = auth_service.create_access_token(data={"user_id": str(new_user_id), "email": user_data.email, "role": "user"})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(new_user_id)
    }

@app.post("/auth/login")
async def login(username: str, password: str):
    user_data = await db_client.execute_single(
        "SELECT * FROM users WHERE username = $1", username
    )
    
    if not user_data or not auth_service.verify_password(password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = auth_service.create_access_token(data={"user_id": str(user_data["id"]), "email": user_data["email"], "role": user_data["role"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user_data["id"])
    }

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@app.post("/agents", response_model=dict, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    new_agent_id = await agent_manager.register_agent({
        "name": agent_data.name,
        "description": agent_data.description,
        "capabilities": agent_data.capabilities,
        "config": agent_data.config,
        "owner_id": current_user.id
    })
    
    return {"agent_id": str(new_agent_id), "status": "created"}
@app.get("/agents", response_model=List[AgentResponse])
async def list_agents(current_user: UserResponse = Depends(get_current_user)):
    agents_data = await db_client.execute_query(
        "SELECT * FROM agents WHERE owner_id = $1", current_user.id
    )
    return [AgentResponse(**agent_data) for agent_data in agents_data]

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    agent_data = await db_client.execute_single(
        "SELECT * FROM agents WHERE id = $1 AND owner_id = $2", agent_id, current_user.id
    )
    
    if not agent_data:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(**agent_data)


@app.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    status_data: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    agent_data = await db_client.execute_single(
        "SELECT id FROM agents WHERE id = $1 AND owner_id = $2", agent_id, current_user.id
    )
    
    if not agent_data:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await db_client.execute_command(
        "UPDATE agents SET last_heartbeat = NOW(), status = $1 WHERE id = $2",
        status_data.get("status", AgentStatus.ACTIVE).value, agent_id
    )
    
    if manager_client:
        await manager_client.send_heartbeat(agent_id, status_data.get("status", AgentStatus.ACTIVE).value)
    
    return {"status": "heartbeat_received"}

@app.post("/tasks", response_model=dict, status_code=201)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    new_task_id = uuid.uuid4()
    await db_client.execute_command(
        "INSERT INTO tasks (id, name, description, task_type, parameters, priority, user_id, agent_id, status) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
        new_task_id, task_data.name, task_data.description, task_data.task_type, json.dumps(task_data.parameters), task_data.priority.value, current_user.id, task_data.agent_id, TaskStatus.PENDING.value
    )
    
    # Assign to agent and queue for processing
    background_tasks.add_task(
        agent_manager.assign_task_to_agent, 
        str(new_task_id), 
        task_data.agent_id
    )
    
    TASK_COUNT.labels(status="created", type=task_data.task_type).inc()
    
    return {"task_id": str(new_task_id), "status": "created"}

@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(current_user: UserResponse = Depends(get_current_user)):
    tasks_data = await db_client.execute_query(
        "SELECT * FROM tasks WHERE user_id = $1 ORDER BY created_at DESC", current_user.id
    )
    return [TaskResponse(**task_data) for task_data in tasks_data]

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    task_data = await db_client.execute_single(
        "SELECT * FROM tasks WHERE id = $1 AND user_id = $2", task_id, current_user.id
    )
    
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(**task_data)


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns detailed status of all system components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {}
    }
    
    # Check database connection
    try:
        await db_client.execute_single("SELECT 1")
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Check Redis connection
    try:
        if redis_client:
            await redis_client.ping()
            health_status["components"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        else:
            health_status["components"]["redis"] = {
                "status": "not_configured",
                "message": "Redis not configured"
            }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
    
    # Check Manager Agent connection (if configured)
    try:
        if manager_client:
            # Simple connectivity check
            health_status["components"]["manager_agent"] = {
                "status": "configured",
                "message": f"Manager agent URL: {manager_client.manager_url}"
            }
        else:
            health_status["components"]["manager_agent"] = {
                "status": "not_configured",
                "message": "Manager agent not configured"
            }
    except Exception as e:
        health_status["components"]["manager_agent"] = {
            "status": "error",
            "message": f"Manager agent check failed: {str(e)}"
        }
    
    # Overall health determination
    component_statuses = [c.get("status") for c in health_status["components"].values()]
    if "unhealthy" in component_statuses:
        health_status["status"] = "unhealthy"
    elif "degraded" in component_statuses:
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/metrics")
async def get_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe
    Returns 200 if application is running, regardless of dependency health
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/ready")
async def readiness_probe():
    """
    Kubernetes readiness probe
    Returns 200 only if application can serve traffic (all dependencies healthy)
    """
    ready = True
    components = {}
    
    # Check database
    try:
        await db_client.execute_single("SELECT 1")
        components["database"] = "ready"
    except Exception as e:
        ready = False
        components["database"] = f"not_ready: {str(e)}"
    
    # Check Redis (optional dependency)
    try:
        if redis_client:
            await redis_client.ping()
            components["redis"] = "ready"
        else:
            components["redis"] = "not_configured"
    except Exception as e:
        # Redis failure doesn't prevent readiness (optional dependency)
        components["redis"] = f"degraded: {str(e)}"
    
    if not ready:
        raise HTTPException(status_code=503, detail={
            "status": "not_ready",
            "components": components
        })
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "components": components
    }

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
    """Process a single task"""
    task_id = task_data["task_id"]
    
    task_record = await db_client.execute_single("SELECT * FROM tasks WHERE id = $1", task_id)
    
    if not task_record:
        logger.error(f"Task {task_id} not found")
        return
    
    try:
        # Simulate task processing
        logger.info(f"Processing task {task_id} of type {task_record['task_type']}")
        
        # Here you would implement actual task processing logic
        # For demo purposes, we\'ll simulate some work
        await asyncio.sleep(2)
        
        # Mark task as completed
        await db_client.execute_command(
            "UPDATE tasks SET status = $1, completed_at = NOW(), result = $2 WHERE id = $3",
            TaskStatus.COMPLETED.value, json.dumps({"status": "success", "message": "Task completed successfully"}), task_id
        )
        
        TASK_COUNT.labels(status="completed", type=task_record['task_type']).inc()
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        await db_client.execute_command(
            "UPDATE tasks SET status = $1, error_message = $2, completed_at = NOW() WHERE id = $3",
            TaskStatus.FAILED.value, str(e), task_id
        )
        
        TASK_COUNT.labels(status="failed", type=task_record['task_type']).inc()

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
"""
YMERA Project Agent - Main Application Entry Point
Version: 2.0.0

This is the main entry point for the Project Agent application.
Run with: python main.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from api.main import app
    from core.config import settings
    
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.worker_count,
        log_level=settings.log_level.lower(),
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
