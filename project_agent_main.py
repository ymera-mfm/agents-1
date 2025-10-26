"""
YMERA Project Agent - Complete Main Application
Fully integrated with all components and agents
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID
import logging
import asyncio
import json

from core.config import settings
from core.database import ProjectDatabase
from core.agent_orchestrator import AgentOrchestrator
from core.auth import AuthService
from core.chat_interface import ChatInterface
from core.file_manager import FileManager
from core.quality_verifier import QualityVerificationEngine
from core.project_integrator import ProjectIntegrator
from core.report_generator import ReportGenerator
from services.project_builder_agent import ProjectBuilderAgent
from utils.websocket_manager import WebSocketManager
from utils.log_manager import ProjectLogManager
from utils.metrics import MetricsCollector

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
database: ProjectDatabase = None
agent_orchestrator: AgentOrchestrator = None
auth_service: AuthService = None
chat_interface: ChatInterface = None
file_manager: FileManager = None
quality_verifier: QualityVerificationEngine = None
project_integrator: ProjectIntegrator = None
report_generator: ReportGenerator = None
project_builder: ProjectBuilderAgent = None
websocket_manager: WebSocketManager = None
log_manager: ProjectLogManager = None
metrics_collector: MetricsCollector = None

# Active connections tracking
active_websockets: Dict[str, WebSocket] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global database, agent_orchestrator, auth_service, chat_interface
    global file_manager, quality_verifier, project_integrator, report_generator
    global project_builder, websocket_manager, log_manager, metrics_collector
    
    logger.info("="*80)
    logger.info("YMERA PROJECT AGENT - STARTING UP")
    logger.info("="*80)
    
    try:
        # Initialize metrics collector
        metrics_collector = MetricsCollector()
        await metrics_collector.initialize()
        logger.info("✓ Metrics collector initialized")
        
        # Initialize database
        database = ProjectDatabase(
            settings.database_url,
            settings.database_pool_size,
            settings.database_max_overflow
        )
        await database.initialize()
        logger.info("✓ Database initialized")
        
        # Initialize log manager
        log_manager = ProjectLogManager(database, settings)
        await log_manager.initialize()
        logger.info("✓ Log manager initialized")
        
        # Initialize agent orchestrator
        agent_orchestrator = AgentOrchestrator(settings, database)
        await agent_orchestrator.initialize()
        logger.info("✓ Agent orchestrator initialized")
        
        # Initialize auth service
        auth_service = AuthService(database, settings)
        await auth_service.initialize()
        logger.info("✓ Authentication service initialized")
        
        # Initialize file manager
        file_manager = FileManager(settings, database)
        await file_manager.initialize()
        logger.info("✓ File manager initialized")
        
        # Initialize quality verifier
        quality_verifier = QualityVerificationEngine(settings, database)
        await quality_verifier.initialize()
        logger.info("✓ Quality verifier initialized")
        
        # Initialize project integrator
        project_integrator = ProjectIntegrator(settings, database, quality_verifier)
        await project_integrator.initialize()
        logger.info("✓ Project integrator initialized")
        
        # Initialize report generator
        report_generator = ReportGenerator(settings, database)
        await report_generator.initialize()
        logger.info("✓ Report generator initialized")
        
        # Initialize chat interface
        chat_interface = ChatInterface(settings, database, agent_orchestrator)
        await chat_interface.initialize()
        logger.info("✓ Chat interface initialized")
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketManager(
            database,
            agent_orchestrator,
            log_manager
        )
        await websocket_manager.initialize()
        logger.info("✓ WebSocket manager initialized")
        
        # Initialize project builder
        project_builder = ProjectBuilderAgent(
            agent_id=f"project_builder_{datetime.utcnow().strftime('%Y%m%d')}",
            orchestrator_url=settings.manager_agent_url,
            websocket_url=f"ws://localhost:{settings.port}/ws/builder",
            config={
                'max_concurrent_builds': settings.worker_count,
                'workspace_base': settings.storage_path,
                'enable_docker': True,
                'enable_testing': True
            }
        )
        await project_builder.initialize()
        logger.info("✓ Project builder initialized")
        
        # Start background services
        await agent_orchestrator.start_health_monitoring()
        await quality_verifier.start_background_processing()
        await project_integrator.start_background_integration()
        logger.info("✓ Background services started")
        
        logger.info("="*80)
        logger.info(f"PROJECT AGENT READY - Port {settings.port}")
        logger.info(f"API Documentation: http://{settings.host}:{settings.port}/api/docs")
        logger.info("="*80)
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
        
    finally:
        logger.info("Shutting down Project Agent...")
        
        # Shutdown services in reverse order
        if project_builder:
            await project_builder.shutdown()
        
        if websocket_manager:
            await websocket_manager.shutdown()
        
        if project_integrator:
            await project_integrator.shutdown()
        
        if quality_verifier:
            await quality_verifier.shutdown()
        
        if chat_interface:
            await chat_interface.shutdown()
        
        if file_manager:
            await file_manager.shutdown()
        
        if agent_orchestrator:
            await agent_orchestrator.shutdown()
        
        if log_manager:
            await log_manager.shutdown()
        
        if database:
            await database.close()
        
        logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="YMERA Project Agent",
    description="Advanced multi-agent project building and integration platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================

async def get_current_user(authorization: str = None):
    """Dependency to get current authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    user = await auth_service.verify_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user

# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check all components
    components = {
        "database": database,
        "agent_orchestrator": agent_orchestrator,
        "auth_service": auth_service,
        "file_manager": file_manager,
        "quality_verifier": quality_verifier,
        "project_integrator": project_integrator,
        "chat_interface": chat_interface,
        "log_manager": log_manager
    }
    
    for name, component in components.items():
        try:
            is_healthy = await component.health_check() if component else False
            health_status["components"][name] = "healthy" if is_healthy else "unhealthy"
        except Exception as e:
            health_status["components"][name] = f"error: {str(e)}"
    
    # Overall status
    all_healthy = all(status == "healthy" for status in health_status["components"].values())
    health_status["status"] = "healthy" if all_healthy else "degraded"
    
    return health_status

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "YMERA Project Agent",
        "version": "2.0.0",
        "status": "operational",
        "capabilities": [
            "project_building",
            "module_integration",
            "quality_verification",
            "file_management",
            "agent_communication",
            "real_time_chat",
            "comprehensive_logging"
        ],
        "documentation": "/api/docs",
        "websocket": f"ws://{settings.host}:{settings.port}/ws/agent"
    }

# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/api/v1/auth/register")
async def register_user(
    email: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
):
    """Register new user"""
    try:
        user = await auth_service.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        return {
            "success": True,
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name")
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/v1/auth/login")
async def login(email: str, password: str):
    """User login"""
    user = await auth_service.authenticate_user(email, password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token_data = await auth_service.create_access_token(user)
    
    return {
        "success": True,
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"],
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "role": user["role"]
        }
    }

@app.post("/api/v1/auth/logout")
async def logout(user = Depends(get_current_user)):
    """User logout"""
    # Revoke token logic here
    return {"success": True, "message": "Logged out successfully"}

# =============================================================================
# PROJECT MANAGEMENT ENDPOINTS
# =============================================================================

@app.post("/api/v1/projects")
async def create_project(
    name: str,
    description: Optional[str] = None,
    project_type: str = "web_application",
    user = Depends(get_current_user)
):
    """Create new project"""
    try:
        project_id = str(UUID(int=int(datetime.utcnow().timestamp() * 1000000)))
        
        query = """
            INSERT INTO projects (id, name, description, owner_id, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """
        
        metadata = json.dumps({
            "project_type": project_type,
            "created_by": str(user["id"])
        })
        
        project = await database.execute_single(
            query,
            project_id,
            name,
            description,
            user["id"],
            metadata
        )
        
        # Log project creation
        await log_manager.log_project_event(
            project_id=project_id,
            event_type="project_created",
            details={"name": name, "type": project_type},
            user_id=str(user["id"])
        )
        
        return {
            "success": True,
            "project": {
                "id": str(project["id"]),
                "name": project["name"],
                "description": project["description"],
                "status": project["status"],
                "created_at": project["created_at"].isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Project creation error: {e}")
        raise HTTPException(status_code=500, detail="Project creation failed")

@app.get("/api/v1/projects")
async def list_projects(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user = Depends(get_current_user)
):
    """List user's projects"""
    projects = await database.list_projects(
        user_id=str(user["id"]),
        status=status,
        limit=limit,
        offset=offset
    )
    
    return {
        "success": True,
        "projects": [
            {
                "id": str(p["id"]),
                "name": p["name"],
                "description": p["description"],
                "status": p["status"],
                "progress": float(p.get("progress", 0)),
                "created_at": p["created_at"].isoformat()
            }
            for p in projects
        ],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(projects)
        }
    }

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: str, user = Depends(get_current_user)):
    """Get project details"""
    project = await database.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check ownership
    if str(project["owner_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get project stats
    stats_query = """
        SELECT 
            COUNT(*) as total_submissions,
            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
            COUNT(CASE WHEN status = 'integrated' THEN 1 END) as integrated,
            AVG(quality_score) as avg_quality
        FROM agent_submissions
        WHERE project_id = $1
    """
    stats = await database.execute_single(stats_query, project_id)
    
    return {
        "success": True,
        "project": {
            "id": str(project["id"]),
            "name": project["name"],
            "description": project["description"],
            "status": project["status"],
            "progress": float(project.get("progress", 0)),
            "created_at": project["created_at"].isoformat(),
            "updated_at": project["updated_at"].isoformat(),
            "statistics": dict(stats) if stats else {}
        }
    }

# =============================================================================
# SUBMISSION ENDPOINTS (RECEIVING FROM AGENTS)
# =============================================================================

@app.post("/api/v1/submissions")
async def create_submission(
    agent_id: str,
    project_id: str,
    module_name: str,
    output_type: str,
    files: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    user = Depends(get_current_user)
):
    """Receive submission from agent"""
    try:
        submission_id = str(UUID(int=int(datetime.utcnow().timestamp() * 1000000)))
        
        # Create submission record
        submission = await database.create_submission(
            submission_id=submission_id,
            agent_id=agent_id,
            project_id=project_id,
            module_name=module_name,
            output_type=output_type,
            files=files,
            metadata=metadata or {},
            user_id=user["id"]
        )
        
        # Log submission
        await log_manager.log_submission_event(
            submission_id=submission_id,
            project_id=project_id,
            agent_id=agent_id,
            event_type="submission_received",
            details={"module_name": module_name, "files_count": len(files)}
        )
        
        # Trigger quality verification
        asyncio.create_task(
            quality_verifier.verify_submission(submission_id, {
                "files": files,
                "metadata": metadata or {}
            })
        )
        
        # Notify via WebSocket
        await websocket_manager.broadcast_to_project(
            project_id,
            {
                "type": "new_submission",
                "submission_id": submission_id,
                "agent_id": agent_id,
                "module_name": module_name
            }
        )
        
        return {
            "success": True,
            "submission_id": submission_id,
            "status": "pending_verification"
        }
        
    except Exception as e:
        logger.error(f"Submission creation error: {e}")
        raise HTTPException(status_code=500, detail="Submission failed")

@app.get("/api/v1/submissions/{submission_id}")
async def get_submission(submission_id: str, user = Depends(get_current_user)):
    """Get submission details"""
    submission = await database.get_submission(submission_id)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Get detailed feedback
    feedback = await quality_verifier.get_detailed_feedback(submission_id)
    
    return {
        "success": True,
        "submission": {
            "id": str(submission["id"]),
            "agent_id": submission["agent_id"],
            "project_id": str(submission["project_id"]),
            "module_name": submission["module_name"],
            "status": submission["status"],
            "quality_score": submission.get("quality_score"),
            "created_at": submission["created_at"].isoformat(),
            "feedback": feedback
        }
    }

@app.post("/api/v1/submissions/{submission_id}/integrate")
async def integrate_submission(
    submission_id: str,
    strategy: str = "hot-reload",
    user = Depends(get_current_user)
):
    """Integrate approved submission into project"""
    submission = await database.get_submission(submission_id)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if submission["status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Submission must be approved first (current status: {submission['status']})"
        )
    
    # Trigger integration
    result = await project_integrator.integrate_submission(
        project_id=str(submission["project_id"]),
        submission_id=submission_id,
        strategy=strategy
    )
    
    return {
        "success": result["status"] == "integrated",
        "result": result
    }

# =============================================================================
# FILE MANAGEMENT ENDPOINTS
# =============================================================================

@app.post("/api/v1/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    category: str = "general",
    description: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Upload file"""
    try:
        content = await file.read()
        
        # Calculate checksum
        import hashlib
        checksum = hashlib.sha256(content).hexdigest()
        
        result = await file_manager.upload_file(
            filename=file.filename,
            content=content,
            project_id=project_id,
            category=category,
            description=description,
            user_id=user["id"],
            checksum=checksum
        )
        
        return {
            "success": True,
            "file_id": str(result["id"]),
            "filename": result["filename"],
            "size": result["size"],
            "checksum": result["checksum"]
        }
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/api/v1/files/{file_id}")
async def get_file_info(file_id: str, user = Depends(get_current_user)):
    """Get file metadata"""
    metadata = await file_manager.get_file_metadata(file_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check access
    has_access = await file_manager.check_file_access(file_id, user["id"])
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "success": True,
        "file": {
            "id": str(metadata["id"]),
            "filename": metadata["filename"],
            "size": metadata["size"],
            "checksum": metadata["checksum"],
            "category": metadata.get("category"),
            "created_at": metadata["created_at"].isoformat()
        }
    }

@app.get("/api/v1/files/{file_id}/download")
async def download_file(file_id: str, user = Depends(get_current_user)):
    """Download file"""
    # Check access
    has_access = await file_manager.check_file_access(file_id, user["id"])
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = await file_manager.get_file_path(file_id)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    async def file_generator():
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                yield chunk
    
    return StreamingResponse(
        file_generator(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
    )

# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@app.post("/api/v1/chat")
async def chat_message(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    user = Depends(get_current_user)
):
    """Send chat message"""
    response = await chat_interface.process_message(
        user_id=str(user["id"]),
        message=message,
        context=context
    )
    
    return {
        "success": True,
        "response": response["response"],
        "suggestions": response.get("suggestions", []),
        "attachments": response.get("attachments", [])
    }

# =============================================================================
# REPORTING ENDPOINTS
# =============================================================================

@app.get("/api/v1/projects/{project_id}/report")
async def get_project_report(
    project_id: str,
    report_type: str = "comprehensive",
    format: str = "json",
    user = Depends(get_current_user)
):
    """Generate project report"""
    project = await database.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if str(project["owner_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    report = await report_generator.generate_project_report(
        project_id=project_id,
        report_type=report_type,
        format=format
    )
    
    if format == "json":
        return report
    else:
        # Return PDF as stream
        return StreamingResponse(
            iter([report]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report_{project_id}.pdf"}
        )

@app.get("/api/v1/projects/{project_id}/metrics")
async def get_project_metrics(project_id: str, user = Depends(get_current_user)):
    """Get project quality metrics"""
    metrics = await quality_verifier.get_project_metrics(project_id)
    
    return {
        "success": True,
        "metrics": metrics
    }

# =============================================================================
# AGENT COMMUNICATION ENDPOINTS
# =============================================================================

@app.get("/api/v1/agents")
async def list_agents(user = Depends(get_current_user)):
    """List all registered agents"""
    agents = await agent_orchestrator.list_agents()
    
    return {
        "success": True,
        "agents": agents
    }

@app.get("/api/v1/agents/{agent_id}/health")
async def check_agent_health(agent_id: str, user = Depends(get_current_user)):
    """Check specific agent health"""
    health = await agent_orchestrator.check_agent_health(agent_id)
    
    return {
        "success": True,
        "health": health
    }

@app.post("/api/v1/agents/{agent_id}/send")
async def send_to_agent(
    agent_id: str,
    endpoint: str,
    data: Dict[str, Any],
    method: str = "POST",
    user = Depends(get_current_user)
):
    """Send request to specific agent"""
    result = await agent_orchestrator.send_to_agent(
        agent_id=agent_id,
        endpoint=endpoint,
        data=data,
        method=method
    )
    
    if result is None:
        raise HTTPException(status_code=503, detail="Agent unavailable")
    
    return {
        "success": True,
        "result": result
    }

# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@app.websocket("/ws/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    """WebSocket endpoint for agent communication"""
    await websocket.accept()
    connection_id = f"agent_{datetime.utcnow().timestamp()}"
    active_websockets[connection_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data["type"] == "submission":
                # Process submission via WebSocket
                await websocket_manager.handle_submission(data, websocket)
            
            elif data["type"] == "status_update":
                # Broadcast status update
                await websocket_manager.broadcast_to_project(
                    data["project_id"],
                    data
                )
            
            elif data["type"] == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id in active_websockets:
            del active_websockets[connection_id]

@app.websocket("/ws/project/{project_id}")
async def websocket_project_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for project-specific updates"""
    await websocket.accept()
    await websocket_manager.subscribe_to_project(project_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            # Handle project-specific messages
            if data["type"] == "request_update":
                project = await database.get_project(project_id)
                await websocket.send_json({
                    "type": "project_update",
                    "project": project
                })
    
    except WebSocketDisconnect:
        await websocket_manager.unsubscribe_from_project(project_id, websocket)

# =============================================================================
# LOG MANAGEMENT ENDPOINTS
# =============================================================================

@app.get("/api/v1/logs/project/{project_id}")
async def get_project_logs(
    project_id: str,
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Get project logs"""
    logs = await log_manager.get_project_logs(
        project_id=project_id,
        limit=limit,
        offset=offset,
        event_type=event_type
    )
    
    return {
        "success": True,
        "logs": logs,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(logs)
        }
    }

@app.get("/api/v1/logs/directory/{project_id}")
async def get_directory_structure(project_id: str, user = Depends(get_current_user)):
    """Get project directory structure and file locations"""
    directory_log = await log_manager.get_directory_structure(project_id)
    
    return {
        "success": True,
        "directory_structure": directory_log
    }

@app.get("/api/v1/logs/module/{module_id}")
async def get_module_logs(module_id: str, user = Depends(get_current_user)):
    """Get logs for specific module"""
    logs = await log_manager.get_module_logs(module_id)
    
    return {
        "success": True,
        "logs": logs
    }

# =============================================================================
# BUILD ENDPOINTS (Project Builder Integration)
# =============================================================================

@app.post("/api/v1/builds/start")
async def start_build(
    project_id: str,
    modules: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """Start project build process"""
    project = await database.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Prepare project data
    project_data = {
        "name": project["name"],
        "project_type": json.loads(project.get("metadata", "{}")).get("project_type", "web_application"),
        "workspace_path": f"{settings.storage_path}/projects/{project_id}",
        "tech_stack": json.loads(project.get("metadata", "{}")).get("tech_stack", {}),
        "dependencies": json.loads(project.get("metadata", "{}")).get("dependencies", {})
    }
    
    # Start build
    build_id = await project_builder.start_build(
        project_id=project_id,
        project_data=project_data,
        modules=modules
    )
    
    # Log build start
    await log_manager.log_build_event(
        build_id=build_id,
        project_id=project_id,
        event_type="build_started",
        details={"modules_count": len(modules)}
    )
    
    return {
        "success": True,
        "build_id": build_id,
        "status": "queued",
        "message": "Build started successfully"
    }

@app.get("/api/v1/builds/{build_id}")
async def get_build_status(build_id: str, user = Depends(get_current_user)):
    """Get build status"""
    if build_id not in project_builder.active_builds:
        raise HTTPException(status_code=404, detail="Build not found")
    
    context = project_builder.active_builds[build_id]
    
    return {
        "success": True,
        "build": {
            "build_id": context.build_id,
            "project_id": context.project_id,
            "status": context.status.value,
            "progress": len(context.integrated_modules) / max(1, len(context.module_queue)) * 100,
            "modules_integrated": len(context.integrated_modules),
            "modules_total": len(context.module_queue),
            "failed_modules": context.failed_modules,
            "started_at": context.started_at.isoformat() if context.started_at else None,
            "completed_at": context.completed_at.isoformat() if context.completed_at else None
        }
    }

@app.get("/api/v1/builds/{build_id}/artifacts")
async def get_build_artifacts(build_id: str, user = Depends(get_current_user)):
    """Get build artifacts"""
    if build_id not in project_builder.active_builds:
        raise HTTPException(status_code=404, detail="Build not found")
    
    context = project_builder.active_builds[build_id]
    
    return {
        "success": True,
        "artifacts": context.build_artifacts
    }

# =============================================================================
# KNOWLEDGE & LEARNING ENDPOINTS (Integration with Learning Agent)
# =============================================================================

@app.post("/api/v1/knowledge/request")
async def request_knowledge(
    agent_id: str,
    knowledge_type: str,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    user = Depends(get_current_user)
):
    """Request knowledge from learning agent"""
    # Log knowledge request
    await log_manager.log_knowledge_request(
        agent_id=agent_id,
        knowledge_type=knowledge_type,
        query=query
    )
    
    # Forward to agent manager for approval
    request_data = {
        "source_agent": "project_agent",
        "requesting_agent": agent_id,
        "knowledge_type": knowledge_type,
        "query": query,
        "context": context or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await agent_orchestrator.send_to_agent(
        agent_id="manager",
        endpoint="/api/v1/knowledge/approve",
        data=request_data
    )
    
    return {
        "success": True,
        "request_id": result.get("request_id") if result else None,
        "status": "pending_approval"
    }

@app.post("/api/v1/knowledge/contribute")
async def contribute_knowledge(
    module_id: str,
    knowledge_data: Dict[str, Any],
    user = Depends(get_current_user)
):
    """Contribute knowledge from integrated module"""
    # Log contribution
    await log_manager.log_knowledge_contribution(
        module_id=module_id,
        knowledge_data=knowledge_data
    )
    
    # Forward to learning agent
    result = await agent_orchestrator.send_to_agent(
        agent_id="learning",
        endpoint="/api/v1/knowledge/store",
        data={
            "source": "project_agent",
            "module_id": module_id,
            "knowledge": knowledge_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {
        "success": True,
        "message": "Knowledge contributed successfully"
    }

# =============================================================================
# COMMUNICATION WITH MANAGER AGENT
# =============================================================================

@app.post("/api/v1/manager/notify")
async def notify_manager(
    event_type: str,
    data: Dict[str, Any],
    priority: str = "normal"
):
    """Send notification to manager agent"""
    notification = {
        "source": "project_agent",
        "event_type": event_type,
        "priority": priority,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await agent_orchestrator.send_to_agent(
        agent_id="manager",
        endpoint="/api/v1/notifications",
        data=notification
    )
    
    return {
        "success": result is not None,
        "notification_id": result.get("id") if result else None
    }

@app.post("/api/v1/manager/request-action")
async def request_manager_action(
    action_type: str,
    project_id: str,
    details: Dict[str, Any],
    user = Depends(get_current_user)
):
    """Request action from manager agent"""
    request_data = {
        "source": "project_agent",
        "action_type": action_type,
        "project_id": project_id,
        "details": details,
        "user_id": str(user["id"]),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await agent_orchestrator.send_to_agent(
        agent_id="manager",
        endpoint="/api/v1/actions/request",
        data=request_data
    )
    
    return {
        "success": result is not None,
        "action_id": result.get("action_id") if result else None,
        "status": result.get("status") if result else "unknown"
    }

# =============================================================================
# DAILY LOG SYNCHRONIZATION WITH MANAGER & LEARNING AGENTS
# =============================================================================

@app.post("/api/v1/sync/daily-logs")
async def sync_daily_logs(background_tasks: BackgroundTasks):
    """Trigger daily log synchronization"""
    background_tasks.add_task(perform_daily_sync)
    
    return {
        "success": True,
        "message": "Daily log sync initiated"
    }

async def perform_daily_sync():
    """Perform daily log synchronization"""
    try:
        # Collect all logs from last 24 hours
        daily_logs = await log_manager.get_daily_summary()
        
        # Send to manager agent
        await agent_orchestrator.send_to_agent(
            agent_id="manager",
            endpoint="/api/v1/logs/daily-sync",
            data={
                "source": "project_agent",
                "period": "daily",
                "logs": daily_logs,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Send to learning agent
        await agent_orchestrator.send_to_agent(
            agent_id="learning",
            endpoint="/api/v1/logs/daily-sync",
            data={
                "source": "project_agent",
                "period": "daily",
                "logs": daily_logs,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info("Daily log sync completed successfully")
        
    except Exception as e:
        logger.error(f"Daily log sync failed: {e}")

# =============================================================================
# METRICS & MONITORING
# =============================================================================

@app.get("/api/v1/metrics")
async def get_metrics():
    """Get system metrics"""
    metrics = await metrics_collector.get_all_metrics()
    
    return {
        "success": True,
        "metrics": metrics
    }

@app.get("/api/v1/metrics/project/{project_id}")
async def get_project_specific_metrics(project_id: str, user = Depends(get_current_user)):
    """Get project-specific metrics"""
    metrics = await metrics_collector.get_project_metrics(project_id)
    
    return {
        "success": True,
        "project_id": project_id,
        "metrics": metrics
    }

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.worker_count if not settings.debug else 1
    )