"""
YMERA Project Agent - Production-Ready Implementation
Version: 2.0.0
Purpose: Orchestrate multi-agent collaboration for software development projects

Core Responsibilities:
1. Quality Verification - Validate outputs from all agents
2. Project Integration - Merge verified modules into active projects
3. Agent Orchestration - Coordinate 20+ specialized agents
4. User Communication - Natural language chat interface
5. File Management - Handle uploads, downloads, versioning
6. Reporting - Generate comprehensive project reports
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
from pathlib import Path
import json
import hashlib

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator
import aiofiles
import httpx

# Core imports
from core.config import ProjectAgentSettings
from core.database import ProjectDatabase
from core.auth import AuthService
from core.quality_verifier import QualityVerificationEngine
from core.project_integrator import ProjectIntegrator
from core.agent_orchestrator import AgentOrchestrator
from core.file_manager import FileManager
from core.chat_interface import ChatInterface
from core.report_generator import ReportGenerator

# Middleware
from middleware.rate_limiting import RateLimitMiddleware
from middleware.monitoring import MetricsMiddleware, prometheus_metrics
from middleware.security import SecurityHeadersMiddleware

# Models
from models.project import Project, ProjectStatus, ProjectPhase
from models.submission import AgentSubmission, SubmissionStatus, QualityFeedback
from models.user import User, UserRole
from models.file import FileMetadata, FileVersion

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(trace_id)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('project_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, str]
    version: str = "2.0.0"

class SubmitOutputRequest(BaseModel):
    agent_id: str = Field(..., description="ID of the submitting agent")
    project_id: str = Field(..., description="Project ID")
    module_name: str = Field(..., description="Module/component name")
    output_type: str = Field(..., description="Type: code, documentation, test, config")
    files: List[Dict[str, Any]] = Field(..., description="List of files with content")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SubmissionResponse(BaseModel):
    submission_id: str
    status: SubmissionStatus
    quality_score: Optional[float] = None
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    message: str
    estimated_verification_time: Optional[int] = None

class ProjectStatusResponse(BaseModel):
    project_id: str
    name: str
    status: ProjectStatus
    progress: float
    phases: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]
    estimated_completion: Optional[datetime]

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime

# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

# Global service instances
settings: Optional[ProjectAgentSettings] = None
database: Optional[ProjectDatabase] = None
auth_service: Optional[AuthService] = None
quality_verifier: Optional[QualityVerificationEngine] = None
project_integrator: Optional[ProjectIntegrator] = None
agent_orchestrator: Optional[AgentOrchestrator] = None
file_manager: Optional[FileManager] = None
chat_interface: Optional[ChatInterface] = None
report_generator: Optional[ReportGenerator] = None
connection_manager: Optional['ConnectionManager'] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global settings, database, auth_service, quality_verifier, project_integrator
    global agent_orchestrator, file_manager, chat_interface, report_generator, connection_manager
    
    logger.info("=" * 80)
    logger.info("YMERA PROJECT AGENT - STARTING UP")
    logger.info("=" * 80)
    
    try:
        # Initialize configuration
        settings = ProjectAgentSettings()
        logger.info("✓ Configuration loaded")
        
        # Initialize database
        database = ProjectDatabase(settings.database_url)
        await database.initialize()
        logger.info("✓ Database connected")
        
        # Initialize authentication service
        auth_service = AuthService(database, settings)
        await auth_service.initialize()
        logger.info("✓ Authentication service initialized")
        
        # Initialize quality verification engine
        quality_verifier = QualityVerificationEngine(settings, database)
        await quality_verifier.initialize()
        logger.info("✓ Quality verification engine initialized")
        
        # Initialize project integrator
        project_integrator = ProjectIntegrator(settings, database, quality_verifier)
        await project_integrator.initialize()
        logger.info("✓ Project integrator initialized")
        
        # Initialize agent orchestrator
        agent_orchestrator = AgentOrchestrator(settings, database)
        await agent_orchestrator.initialize()
        logger.info("✓ Agent orchestrator initialized")
        
        # Initialize file manager
        file_manager = FileManager(settings, database)
        await file_manager.initialize()
        logger.info("✓ File manager initialized")
        
        # Initialize chat interface
        chat_interface = ChatInterface(settings, database, agent_orchestrator)
        await chat_interface.initialize()
        logger.info("✓ Chat interface initialized")
        
        # Initialize report generator
        report_generator = ReportGenerator(settings, database)
        await report_generator.initialize()
        logger.info("✓ Report generator initialized")
        
        # Initialize WebSocket connection manager
        connection_manager = ConnectionManager()
        logger.info("✓ Connection manager initialized")
        
        # Start background tasks
        asyncio.create_task(quality_verifier.start_background_processing())
        asyncio.create_task(project_integrator.start_background_integration())
        asyncio.create_task(agent_orchestrator.start_health_monitoring())
        logger.info("✓ Background tasks started")
        
        logger.info("=" * 80)
        logger.info("PROJECT AGENT READY - Listening on port %s", settings.port)
        logger.info("=" * 80)
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
        
    finally:
        logger.info("Shutting down Project Agent...")
        
        # Cleanup
        if quality_verifier:
            await quality_verifier.shutdown()
        if project_integrator:
            await project_integrator.shutdown()
        if agent_orchestrator:
            await agent_orchestrator.shutdown()
        if file_manager:
            await file_manager.shutdown()
        if chat_interface:
            await chat_interface.shutdown()
        if report_generator:
            await report_generator.shutdown()
        if database:
            await database.close()
        
        logger.info("Project Agent shutdown complete")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="YMERA Project Agent",
    description="Advanced multi-agent orchestration platform for software development",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Configure in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, redis_url="redis://localhost:6379")

# Security
security = HTTPBearer()

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Dependency: Get current authenticated user"""
    try:
        user = await auth_service.verify_token(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency: Require admin role"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

# ============================================================================
# HEALTH & MONITORING ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Basic health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        components={
            "database": "connected" if database and await database.health_check() else "disconnected",
            "redis": "connected",  # Add actual Redis check
            "kafka": "connected"   # Add actual Kafka check
        }
    )

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check(user: User = Depends(require_admin)):
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check all components
    components = {
        "database": database,
        "quality_verifier": quality_verifier,
        "project_integrator": project_integrator,
        "agent_orchestrator": agent_orchestrator,
        "file_manager": file_manager,
        "chat_interface": chat_interface,
    }
    
    for name, component in components.items():
        try:
            if component and hasattr(component, 'health_check'):
                is_healthy = await component.health_check()
                health_status["components"][name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                health_status["components"][name] = {"status": "unknown"}
        except Exception as e:
            health_status["components"][name] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    if any(c.get("status") == "unhealthy" for c in health_status["components"].values()):
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/metrics", tags=["Monitoring"])
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/login", tags=["Authentication"])
async def login(email: str, password: str):
    """User login"""
    user = await auth_service.authenticate_user(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token_data = await auth_service.create_access_token(user)
    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer",
        "expires_in": token_data["expires_in"],
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
    }

@app.post("/api/v1/auth/logout", tags=["Authentication"])
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: User = Depends(get_current_user)
):
    """User logout"""
    await auth_service.revoke_token(user.id, credentials.credentials)
    return {"message": "Successfully logged out"}

# ============================================================================
# AGENT OUTPUT SUBMISSION
# ============================================================================

@app.post("/api/v1/outputs/submit", response_model=SubmissionResponse, tags=["Outputs"])
async def submit_agent_output(
    request: SubmitOutputRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Submit output from an agent for quality verification
    
    Flow:
    1. Validate submission format
    2. Create submission record
    3. Queue for quality verification
    4. Return submission ID and status
    """
    try:
        # Create submission ID
        submission_id = str(uuid4())
        
        # Store submission in database
        submission = await database.create_submission(
            submission_id=submission_id,
            agent_id=request.agent_id,
            project_id=request.project_id,
            module_name=request.module_name,
            output_type=request.output_type,
            files=request.files,
            metadata=request.metadata,
            user_id=user.id
        )
        
        # Queue for background verification
        background_tasks.add_task(
            quality_verifier.verify_submission,
            submission_id,
            request
        )
        
        logger.info(
            f"Submission {submission_id} received from {request.agent_id} "
            f"for project {request.project_id}"
        )
        
        return SubmissionResponse(
            submission_id=submission_id,
            status=SubmissionStatus.VERIFYING,
            message="Output submitted for quality verification",
            estimated_verification_time=120  # seconds
        )
        
    except Exception as e:
        logger.error(f"Submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Submission processing failed: {str(e)}"
        )

@app.get("/api/v1/outputs/{submission_id}", response_model=SubmissionResponse, tags=["Outputs"])
async def get_submission_status(
    submission_id: str,
    user: User = Depends(get_current_user)
):
    """Get submission status and quality feedback"""
    try:
        submission = await database.get_submission(submission_id)
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        # Check authorization
        if str(submission.user_id) != str(user.id) and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return SubmissionResponse(
            submission_id=submission_id,
            status=submission.status,
            quality_score=submission.quality_score,
            issues=submission.issues or [],
            message=submission.message or "Processing..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submission status"
        )

@app.get("/api/v1/outputs/{submission_id}/feedback", tags=["Outputs"])
async def get_detailed_feedback(
    submission_id: str,
    user: User = Depends(get_current_user)
):
    """Get detailed quality feedback for a submission"""
    try:
        feedback = await quality_verifier.get_detailed_feedback(submission_id)
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        return feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback"
        )

# ============================================================================
# PROJECT MANAGEMENT
# ============================================================================

@app.get("/api/v1/projects/{project_id}/status", response_model=ProjectStatusResponse, tags=["Projects"])
async def get_project_status(
    project_id: str,
    user: User = Depends(get_current_user)
):
    """Get comprehensive project status"""
    try:
        project = await database.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get phases
        phases = await database.get_project_phases(project_id)
        
        # Get quality metrics
        quality_metrics = await quality_verifier.get_project_metrics(project_id)
        
        # Calculate overall progress
        progress = await project_integrator.calculate_project_progress(project_id)
        
        # Estimate completion
        estimated_completion = await project_integrator.estimate_completion(project_id)
        
        return ProjectStatusResponse(
            project_id=project_id,
            name=project.name,
            status=project.status,
            progress=progress,
            phases=[phase.dict() for phase in phases],
            quality_metrics=quality_metrics,
            estimated_completion=estimated_completion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project status"
        )

@app.get("/api/v1/projects", tags=["Projects"])
async def list_projects(
    user: User = Depends(get_current_user),
    status: Optional[ProjectStatus] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all projects accessible to the user"""
    try:
        projects = await database.list_projects(
            user_id=user.id if user.role != UserRole.ADMIN else None,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return {
            "projects": [project.dict() for project in projects],
            "total": len(projects),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )

@app.post("/api/v1/projects/{project_id}/integrate/{submission_id}", tags=["Projects"])
async def trigger_integration(
    project_id: str,
    submission_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """Manually trigger integration of a verified submission"""
    try:
        # Verify submission is approved
        submission = await database.get_submission(submission_id)
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        if submission.status != SubmissionStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only approved submissions can be integrated"
            )
        
        # Queue integration
        background_tasks.add_task(
            project_integrator.integrate_submission,
            project_id,
            submission_id
        )
        
        return {
            "message": "Integration queued",
            "project_id": project_id,
            "submission_id": submission_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration trigger failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger integration"
        )

# ============================================================================
# FILE MANAGEMENT
# ============================================================================

@app.post("/api/v1/files/upload", tags=["Files"])
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    category: str = "general",
    description: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Upload a file"""
    try:
        # Read file content
        content = await file.read()
        
        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()
        
        # Store file
        file_metadata = await file_manager.upload_file(
            filename=file.filename,
            content=content,
            project_id=project_id,
            category=category,
            description=description,
            user_id=user.id,
            checksum=checksum
        )
        
        return {
            "file_id": str(file_metadata.id),
            "filename": file_metadata.filename,
            "size": file_metadata.size,
            "checksum": file_metadata.checksum,
            "upload_time": file_metadata.created_at.isoformat(),
            "download_url": f"/api/v1/files/download/{file_metadata.id}"
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

@app.get("/api/v1/files/download/{file_id}", tags=["Files"])
async def download_file(
    file_id: str,
    user: User = Depends(get_current_user)
):
    """Download a file"""
    try:
        # Get file metadata
        file_metadata = await file_manager.get_file_metadata(file_id)
        
        if not file_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check authorization
        if not await file_manager.check_file_access(file_id, user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get file content
        file_path = await file_manager.get_file_path(file_id)
        
        return FileResponse(
            path=file_path,
            filename=file_metadata.filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File download failed"
        )

@app.get("/api/v1/files/{file_id}/versions", tags=["Files"])
async def list_file_versions(
    file_id: str,
    user: User = Depends(get_current_user)
):
    """List all versions of a file"""
    try:
        versions = await file_manager.get_file_versions(file_id)
        
        return {
            "file_id": file_id,
            "versions": [version.dict() for version in versions],
            "total_versions": len(versions)
        }
        
    except Exception as e:
        logger.error(f"Failed to list file versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file versions"
        )

# ============================================================================
# CHAT INTERFACE (WebSocket)
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat"""
    await connection_manager.connect(user_id, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message
            message_text = data.get("message", "")
            context = data.get("context", {})
            
            # Generate response
            response = await chat_interface.process_message(
                user_id=user_id,
                message=message_text,
                context=context
            )
            
            # Send response back
            await websocket.send_json({
                "type": "response",
                "content": response["response"],
                "suggestions": response.get("suggestions", []),
                "attachments": response.get("attachments", []),
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        connection_manager.disconnect(user_id)

# ============================================================================
# REPORTING & ANALYTICS
# ============================================================================

@app.get("/api/v1/reports/project/{project_id}", tags=["Reports"])
async def generate_project_report(
    project_id: str,
    report_type: str = "comprehensive",
    format: str = "json",
    user: User = Depends(get_current_user)
):
    """Generate a comprehensive project report"""
    try:
        report = await report_generator.generate_project_report(
            project_id=project_id,
            report_type=report_type,
            format=format
        )
        
        if format == "json":
            return report
        elif format == "pdf":
            return StreamingResponse(
                report,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=project_{project_id}_report.pdf"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report generation failed"
        )

@app.get("/api/v1/analytics/quality-trends", tags=["Analytics"])
async def get_quality_trends(
    project_id: Optional[str] = None,
    days: int = 30,
    user: User = Depends(require_admin)
):
    """Get quality trends over time"""
    try:
        trends = await quality_verifier.get_quality_trends(
            project_id=project_id,
            days=days
        )
        
        return {
            "period_days": days,
            "project_id": project_id,
            "trends": trends,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quality trends"
        )

# ============================================================================
# AGENT ORCHESTRATION
# ============================================================================

@app.get("/api/v1/agents", tags=["Agents"])
async def list_registered_agents(user: User = Depends(require_admin)):
    """List all registered agents"""
    try:
        agents = await agent_orchestrator.list_agents()
        return {
            "agents": agents,
            "total": len(agents),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents"
        )

@app.get("/api/v1/agents/{agent_id}/health", tags=["Agents"])
async def get_agent_health(
    agent_id: str,
    user: User = Depends(require_admin)
):
    """Get health status of a specific agent"""
    try:
        health_status = await agent_orchestrator.check_agent_health(agent_id)
        return {
            "agent_id": agent_id,
            "health": health_status,
            "checked_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to check agent health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check agent health"
        )

# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_project_agent:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Set to True for development
        workers=4,
        log_level="info",
        access_log=True
    )
