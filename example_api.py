"""
Example: FastAPI Application with YMERA Database Core
Complete REST API implementation
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
import os

from DATABASE_CORE import (
    init_database,
    close_database,
    get_db_session,
    get_database_manager,
    User, Project, Agent, Task,
    BaseRepository
)

# Configuration
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./api_example.db"

# FastAPI app
app = FastAPI(
    title="YMERA API",
    description="Enterprise Multi-Agent System API",
    version="5.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: str = "general"
    programming_language: Optional[str] = None
    framework: Optional[str] = None
    priority: str = "medium"
    tags: List[str] = []

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    project_type: str
    status: str
    priority: str
    progress: float
    total_tasks: int
    completed_tasks: int
    success_rate: float
    tags: List[str]
    created_at: str
    
    class Config:
        from_attributes = True

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: str
    description: Optional[str] = None
    capabilities: List[str] = []
    configuration: dict = {}

class AgentResponse(BaseModel):
    id: str
    name: str
    agent_type: str
    description: Optional[str]
    status: str
    health_status: str
    success_rate: float
    tasks_completed: int
    tasks_failed: int
    capabilities: List[str]
    created_at: str
    
    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    task_type: str
    project_id: Optional[str] = None
    agent_id: Optional[str] = None
    priority: str = "medium"
    urgency: int = Field(5, ge=1, le=10)
    input_data: dict = {}
    tags: List[str] = []

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    task_type: str
    user_id: str
    project_id: Optional[str]
    agent_id: Optional[str]
    status: str
    priority: str
    urgency: int
    progress: float
    execution_time: float
    created_at: str
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str
    healthy: bool
    database_type: str
    timestamp: str
    statistics: dict

# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting YMERA API...")
    await init_database()
    print("✅ Database initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database on shutdown"""
    print("🛑 Shutting down YMERA API...")
    await close_database()
    print("✅ Database closed")

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "name": "YMERA API",
        "version": "5.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Comprehensive health check"""
    db_manager = await get_database_manager()
    health = await db_manager.health_check()
    stats = await db_manager.get_statistics()
    
    return HealthResponse(
        status=health["status"],
        healthy=health["healthy"],
        database_type=health["database_type"],
        timestamp=health["timestamp"],
        statistics=stats
    )

@app.get("/api/stats", tags=["Health"])
async def get_statistics():
    """Get detailed statistics"""
    db_manager = await get_database_manager()
    stats = await db_manager.get_statistics()
    return stats

# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new user"""
    import hashlib
    
    repo = BaseRepository(session, User)
    
    # Check if username already exists
    existing = await session.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Hash password (use bcrypt in production)
    password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    user = await repo.create(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role
    )
    
    return UserResponse(**user.to_dict())

@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get user by ID"""
    repo = BaseRepository(session, User)
    user = await repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user.to_dict())

@app.get("/api/users", response_model=List[UserResponse], tags=["Users"])
async def list_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session)
):
    """List all users"""
    repo = BaseRepository(session, User)
    users = await repo.get_all(limit=limit, offset=offset)
    
    return [UserResponse(**user.to_dict()) for user in users]

# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@app.post("/api/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, tags=["Projects"])
async def create_project(
    project_data: ProjectCreate,
    user_id: str = Query(..., description="Owner user ID"),
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new project"""
    # Verify user exists
    user_repo = BaseRepository(session, User)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    project_repo = BaseRepository(session, Project)
    project = await project_repo.create(
        name=project_data.name,
        description=project_data.description,
        owner_id=user_id,
        project_type=project_data.project_type,
        programming_language=project_data.programming_language,
        framework=project_data.framework,
        priority=project_data.priority,
        tags=project_data.tags
    )
    
    return ProjectResponse(**project.to_dict())

@app.get("/api/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get project by ID"""
    repo = BaseRepository(session, Project)
    project = await repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(**project.to_dict())

@app.get("/api/projects", response_model=List[ProjectResponse], tags=["Projects"])
async def list_projects(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_db_session)
):
    """List all projects"""
    filters = {"status": status_filter} if status_filter else None
    repo = BaseRepository(session, Project)
    projects = await repo.get_all(limit=limit, offset=offset, filters=filters)
    
    return [ProjectResponse(**project.to_dict()) for project in projects]

# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

@app.post("/api/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED, tags=["Agents"])
async def create_agent(
    agent_data: AgentCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new agent"""
    repo = BaseRepository(session, Agent)
    agent = await repo.create(
        name=agent_data.name,
        agent_type=agent_data.agent_type,
        description=agent_data.description,
        capabilities=agent_data.capabilities,
        configuration=agent_data.configuration
    )
    
    return AgentResponse(**agent.to_dict())

@app.get("/api/agents/{agent_id}", response_model=AgentResponse, tags=["Agents"])
async def get_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get agent by ID"""
    repo = BaseRepository(session, Agent)
    agent = await repo.get_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(**agent.to_dict())

@app.get("/api/agents", response_model=List[AgentResponse], tags=["Agents"])
async def list_agents(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_db_session)
):
    """List all agents"""
    filters = {}
    if agent_type:
        filters["agent_type"] = agent_type
    if status_filter:
        filters["status"] = status_filter
    
    repo = BaseRepository(session, Agent)
    agents = await repo.get_all(limit=limit, offset=offset, filters=filters or None)
    
    return [AgentResponse(**agent.to_dict()) for agent in agents]

# ============================================================================
# TASK ENDPOINTS
# ============================================================================

@app.post("/api/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["Tasks"])
async def create_task(
    task_data: TaskCreate,
    user_id: str = Query(..., description="User ID"),
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new task"""
    # Verify user exists
    user_repo = BaseRepository(session, User)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify project exists if provided
    if task_data.project_id:
        project_repo = BaseRepository(session, Project)
        project = await project_repo.get_by_id(task_data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify agent exists if provided
    if task_data.agent_id:
        agent_repo = BaseRepository(session, Agent)
        agent = await agent_repo.get_by_id(task_data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    task_repo = BaseRepository(session, Task)
    task = await task_repo.create(
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type,
        user_id=user_id,
        project_id=task_data.project_id,
        agent_id=task_data.agent_id,
        priority=task_data.priority,
        urgency=task_data.urgency,
        input_data=task_data.input_data,
        tags=task_data.tags
    )
    
    return TaskResponse(**task.to_dict())

@app.get("/api/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get task by ID"""
    repo = BaseRepository(session, Task)
    task = await repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(**task.to_dict())

@app.get("/api/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def list_tasks(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    session: AsyncSession = Depends(get_db_session)
):
    """List all tasks"""
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if project_id:
        filters["project_id"] = project_id
    if agent_id:
        filters["agent_id"] = agent_id
    
    repo = BaseRepository(session, Task)
    tasks = await repo.get_all(limit=limit, offset=offset, filters=filters or None)
    
    return [TaskResponse(**task.to_dict()) for task in tasks]

@app.patch("/api/tasks/{task_id}/status", tags=["Tasks"])
async def update_task_status(
    task_id: str,
    new_status: str = Query(..., description="New status"),
    session: AsyncSession = Depends(get_db_session)
):
    """Update task status"""
    repo = BaseRepository(session, Task)
    task = await repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    updated_task = await repo.update(task_id, status=new_status)
    return TaskResponse(**updated_task.to_dict())

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("YMERA API Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:8000")
    print("API Documentation: http://localhost:8000/api/docs")
    print("Alternative Docs: http://localhost:8000/api/redoc")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "example_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
