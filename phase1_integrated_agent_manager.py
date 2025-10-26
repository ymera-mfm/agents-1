"""
YMERA Platform - Phase 1: Core Integration
Unified Agent Management System with Chat and File Management

This module integrates:
- Agent Management API
- Chat System with WebSocket support
- File Management System
- Schema Definitions
"""

from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, 
    HTTPException, Depends, BackgroundTasks, Query, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import asyncio
import json
import uuid
import logging
import aiofiles
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class AgentStatus(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    TERMINATED = "terminated"

class AgentType(str, Enum):
    DEVELOPER = "developer"
    ANALYST = "analyst"
    TESTER = "tester"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

# ============================================================================
# PYDANTIC MODELS - SCHEMAS
# ============================================================================

class AgentCapability(BaseModel):
    """Agent capability definition"""
    name: str
    level: int = Field(ge=1, le=10, default=5)
    description: Optional[str] = None

class AgentCreateRequest(BaseModel):
    """Request model for creating an agent"""
    name: str = Field(..., min_length=1, max_length=100)
    agent_type: AgentType
    capabilities: List[AgentCapability] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name')
    @classmethod
    def name_must_be_valid(cls, v):
        if not v.replace('-', '').replace('_', '').replace(' ', '').isalnum():
            raise ValueError('Name must be alphanumeric with optional hyphens, underscores, or spaces')
        return v

class AgentUpdateRequest(BaseModel):
    """Request model for updating an agent"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[AgentStatus] = None
    capabilities: Optional[List[AgentCapability]] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Response model for agent data"""
    id: str
    name: str
    agent_type: str
    status: str
    capabilities: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    active_tasks: int = 0
    completed_tasks: int = 0
    success_rate: float = 0.0

class TaskCreateRequest(BaseModel):
    """Request model for creating a task"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    agent_id: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)

class TaskResponse(BaseModel):
    """Response model for task data"""
    id: str
    name: str
    description: Optional[str] = None
    task_type: str
    parameters: Dict[str, Any]
    priority: str
    status: str
    agent_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

class ChatMessage(BaseModel):
    """Chat message model"""
    message_id: Optional[str] = None
    session_id: str
    content: str
    message_type: str = "user"  # user, agent, system
    attachments: Optional[List[str]] = None
    timestamp: Optional[datetime] = None

class FileUploadResponse(BaseModel):
    """File upload response model"""
    file_id: str
    filename: str
    size: int
    content_type: str
    upload_timestamp: datetime
    session_id: str
    file_path: str
    
    @classmethod
    def from_metadata(cls, metadata: Dict):
        """Create from metadata dict"""
        return cls(
            file_id=metadata['file_id'],
            filename=metadata['original_filename'],
            size=metadata['size'],
            content_type=metadata['content_type'],
            upload_timestamp=metadata['upload_timestamp'],
            session_id=metadata['session_id'],
            file_path=metadata['file_path']
        )

# ============================================================================
# IN-MEMORY STORAGE (Replace with database in production)
# ============================================================================

class InMemoryStorage:
    """Temporary in-memory storage for Phase 1"""
    
    def __init__(self):
        self.agents: Dict[str, Dict] = {}
        self.tasks: Dict[str, Dict] = {}
        self.sessions: Dict[str, Dict] = {}
        self.files: Dict[str, Dict] = {}
        self.chat_messages: Dict[str, List[Dict]] = {}  # session_id -> messages
        
    def add_agent(self, agent_data: Dict) -> Dict:
        agent_id = str(uuid.uuid4())
        agent_data['id'] = agent_id
        agent_data['created_at'] = datetime.utcnow()
        agent_data['updated_at'] = datetime.utcnow()
        agent_data['active_tasks'] = 0
        agent_data['completed_tasks'] = 0
        agent_data['success_rate'] = 0.0
        self.agents[agent_id] = agent_data
        return agent_data
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        return self.agents.get(agent_id)
    
    def list_agents(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        agents_list = list(self.agents.values())
        return agents_list[skip:skip + limit]
    
    def update_agent(self, agent_id: str, update_data: Dict) -> Optional[Dict]:
        if agent_id not in self.agents:
            return None
        self.agents[agent_id].update(update_data)
        self.agents[agent_id]['updated_at'] = datetime.utcnow()
        return self.agents[agent_id]
    
    def delete_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    def add_task(self, task_data: Dict) -> Dict:
        task_id = str(uuid.uuid4())
        task_data['id'] = task_id
        task_data['created_at'] = datetime.utcnow()
        task_data['updated_at'] = datetime.utcnow()
        task_data['status'] = TaskStatus.PENDING.value
        self.tasks[task_id] = task_data
        return task_data
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        return self.tasks.get(task_id)
    
    def list_tasks(self, agent_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        tasks_list = list(self.tasks.values())
        if agent_id:
            tasks_list = [t for t in tasks_list if t.get('agent_id') == agent_id]
        return tasks_list[skip:skip + limit]
    
    def update_task(self, task_id: str, update_data: Dict) -> Optional[Dict]:
        if task_id not in self.tasks:
            return None
        self.tasks[task_id].update(update_data)
        self.tasks[task_id]['updated_at'] = datetime.utcnow()
        return self.tasks[task_id]
    
    def add_file_metadata(self, file_data: Dict) -> Dict:
        file_id = file_data['file_id']
        self.files[file_id] = file_data
        return file_data
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        return self.files.get(file_id)
    
    def add_chat_message(self, session_id: str, message: Dict):
        if session_id not in self.chat_messages:
            self.chat_messages[session_id] = []
        self.chat_messages[session_id].append(message)
    
    def get_chat_history(self, session_id: str, limit: int = 100) -> List[Dict]:
        messages = self.chat_messages.get(session_id, [])
        return messages[-limit:]

# Global storage instance
storage = InMemoryStorage()

# ============================================================================
# FILE MANAGER
# ============================================================================

class FileManager:
    """Handles file upload, download, and management"""
    
    def __init__(self, upload_directory: str = "uploads", max_file_size: int = 100 * 1024 * 1024):
        self.upload_directory = Path(upload_directory)
        self.upload_directory.mkdir(exist_ok=True)
        self.max_file_size = max_file_size
        
        # Create subdirectories
        (self.upload_directory / "temp").mkdir(exist_ok=True)
        (self.upload_directory / "permanent").mkdir(exist_ok=True)
        (self.upload_directory / "processed").mkdir(exist_ok=True)
    
    async def upload_file(self, file: UploadFile, session_id: str, temporary: bool = False) -> Dict:
        """Upload and store file"""
        try:
            # Read file content
            file_content = await file.read()
            if len(file_content) > self.max_file_size:
                raise HTTPException(status_code=413, detail="File too large")
            
            # Generate unique file ID
            file_id = f"{uuid.uuid4().hex}_{file.filename}"
            
            # Determine storage location
            storage_dir = "temp" if temporary else "permanent"
            file_path = self.upload_directory / storage_dir / file_id
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Create metadata
            metadata = {
                "file_id": file_id,
                "original_filename": file.filename,
                "size": len(file_content),
                "content_type": file.content_type or "application/octet-stream",
                "session_id": session_id,
                "file_path": str(file_path),
                "upload_timestamp": datetime.utcnow(),
                "temporary": temporary
            }
            
            # Store metadata
            storage.add_file_metadata(metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    async def download_file(self, file_id: str) -> Path:
        """Get file path for download"""
        metadata = storage.get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = Path(metadata['file_path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return file_path
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file"""
        metadata = storage.get_file_metadata(file_id)
        if not metadata:
            return False
        
        file_path = Path(metadata['file_path'])
        if file_path.exists():
            file_path.unlink()
        
        return True

# Global file manager instance
file_manager = FileManager()

# ============================================================================
# WEBSOCKET CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected to session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected from session {session_id}")
    
    async def send_message(self, message: str, session_id: str):
        """Send message to all connections in a session"""
        if session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected websockets
            for conn in disconnected:
                self.disconnect(conn, session_id)
    
    async def broadcast_to_session(self, message: Dict, session_id: str):
        """Broadcast a message to all connections in a session"""
        message_str = json.dumps(message, default=str)
        await self.send_message(message_str, session_id)

# Global connection manager
connection_manager = ConnectionManager()

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="YMERA Platform - Phase 1: Core Integration",
    description="Unified Agent Management with Chat and File Support",
    version="1.0.0"
)

# Add CORS middleware
# Restrict CORS to trusted origins from environment variable YMERA_ALLOWED_ORIGINS
ALLOWED_ORIGINS = os.environ.get("YMERA_ALLOWED_ORIGINS", "https://yourdomain.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# AGENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "YMERA Platform - Phase 1: Core Integration",
        "version": "1.0.0",
        "status": "operational",
        "phase": "Phase 1 - Core Integration",
        "features": [
            "Agent Management API",
            "Task Management",
            "Chat System with WebSocket",
            "File Upload/Download"
        ],
        "endpoints": {
            "agents": "/api/v1/agents",
            "tasks": "/api/v1/tasks",
            "chat": "/api/v1/chat",
            "files": "/api/v1/files",
            "websocket": "/ws/{session_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "agents_count": len(storage.agents),
        "tasks_count": len(storage.tasks),
        "active_sessions": len(connection_manager.active_connections)
    }

# Agent Management Endpoints

@app.post("/api/v1/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_request: AgentCreateRequest):
    """Create a new agent"""
    try:
        agent_data = {
            "name": agent_request.name,
            "agent_type": agent_request.agent_type.value,
            "status": AgentStatus.IDLE.value,
            "capabilities": [cap.model_dump() for cap in agent_request.capabilities],
            "metadata": agent_request.metadata
        }
        
        agent = storage.add_agent(agent_data)
        logger.info(f"Created agent: {agent['id']}")
        
        return AgentResponse(**agent)
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents", response_model=List[AgentResponse])
async def list_agents(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    """List all agents"""
    agents = storage.list_agents(skip=skip, limit=limit)
    return [AgentResponse(**agent) for agent in agents]

@app.get("/api/v1/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent by ID"""
    agent = storage.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(**agent)

@app.put("/api/v1/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, update_request: AgentUpdateRequest):
    """Update agent"""
    update_data = update_request.model_dump(exclude_none=True)
    
    # Convert capabilities if present
    if 'capabilities' in update_data and update_data['capabilities']:
        update_data['capabilities'] = [cap.model_dump() for cap in update_data['capabilities']]
    
    agent = storage.update_agent(agent_id, update_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    logger.info(f"Updated agent: {agent_id}")
    return AgentResponse(**agent)

@app.delete("/api/v1/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete agent"""
    success = storage.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    logger.info(f"Deleted agent: {agent_id}")
    return {"message": "Agent deleted successfully", "agent_id": agent_id}

# Task Management Endpoints

@app.post("/api/v1/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_request: TaskCreateRequest):
    """Create a new task"""
    try:
        task_data = task_request.model_dump()
        task = storage.add_task(task_data)
        logger.info(f"Created task: {task['id']}")
        
        return TaskResponse(**task)
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks", response_model=List[TaskResponse])
async def list_tasks(
    agent_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List tasks"""
    tasks = storage.list_tasks(agent_id=agent_id, skip=skip, limit=limit)
    return [TaskResponse(**task) for task in tasks]

@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task by ID"""
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task)

@app.put("/api/v1/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: TaskStatus,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
):
    """Update task status"""
    update_data = {"status": status.value}
    
    if result:
        update_data["result"] = result
    if error_message:
        update_data["error_message"] = error_message
    if status == TaskStatus.COMPLETED or status == TaskStatus.FAILED:
        update_data["completed_at"] = datetime.utcnow()
    
    task = storage.update_task(task_id, update_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info(f"Updated task {task_id} status to {status.value}")
    return TaskResponse(**task)

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@app.post("/api/v1/chat/message")
async def send_chat_message(message: ChatMessage):
    """Send a chat message"""
    try:
        # Add message ID and timestamp if not present
        if not message.message_id:
            message.message_id = str(uuid.uuid4())
        if not message.timestamp:
            message.timestamp = datetime.utcnow()
        
        # Store message
        message_data = message.model_dump()
        storage.add_chat_message(message.session_id, message_data)
        
        # Broadcast to WebSocket connections
        await connection_manager.broadcast_to_session(message_data, message.session_id)
        
        logger.info(f"Chat message sent in session {message.session_id}")
        return {"success": True, "message_id": message.message_id}
        
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chat/{session_id}/history")
async def get_chat_history(session_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get chat history for a session"""
    messages = storage.get_chat_history(session_id, limit=limit)
    return {"session_id": session_id, "messages": messages, "count": len(messages)}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await connection_manager.connect(websocket, session_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to session {session_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process and broadcast message
            message = ChatMessage(
                session_id=session_id,
                content=message_data.get("content", ""),
                message_type=message_data.get("message_type", "user"),
                attachments=message_data.get("attachments")
            )
            
            # Store message
            message_dict = message.model_dump()
            message_dict['message_id'] = str(uuid.uuid4())
            message_dict['timestamp'] = datetime.utcnow()
            storage.add_chat_message(session_id, message_dict)
            
            # Broadcast to all connections in session
            await connection_manager.broadcast_to_session(message_dict, session_id)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, session_id)

# ============================================================================
# FILE MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Query(...),
    temporary: bool = Query(False)
):
    """Upload a file"""
    try:
        metadata = await file_manager.upload_file(file, session_id, temporary)
        logger.info(f"File uploaded: {metadata['file_id']}")
        
        return FileUploadResponse.from_metadata(metadata)
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/files/{file_id}")
async def download_file(file_id: str):
    """Download a file"""
    try:
        file_path = await file_manager.download_file(file_id)
        metadata = storage.get_file_metadata(file_id)
        
        return FileResponse(
            path=file_path,
            filename=metadata['original_filename'],
            media_type=metadata['content_type']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/files/{file_id}/metadata")
async def get_file_metadata(file_id: str):
    """Get file metadata"""
    metadata = storage.get_file_metadata(file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    return metadata

@app.delete("/api/v1/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file"""
    success = await file_manager.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    logger.info(f"File deleted: {file_id}")
    return {"message": "File deleted successfully", "file_id": file_id}

# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@app.get("/api/v1/stats")
async def get_statistics():
    """Get platform statistics"""
    return {
        "agents": {
            "total": len(storage.agents),
            "by_status": {
                status.value: sum(1 for a in storage.agents.values() if a.get('status') == status.value)
                for status in AgentStatus
            },
            "by_type": {
                agent_type.value: sum(1 for a in storage.agents.values() if a.get('agent_type') == agent_type.value)
                for agent_type in AgentType
            }
        },
        "tasks": {
            "total": len(storage.tasks),
            "by_status": {
                status.value: sum(1 for t in storage.tasks.values() if t.get('status') == status.value)
                for status in TaskStatus
            },
            "by_priority": {
                priority.value: sum(1 for t in storage.tasks.values() if t.get('priority') == priority.value)
                for priority in TaskPriority
            }
        },
        "chat": {
            "active_sessions": len(storage.chat_messages),
            "total_messages": sum(len(msgs) for msgs in storage.chat_messages.values()),
            "active_connections": len(connection_manager.active_connections)
        },
        "files": {
            "total": len(storage.files),
            "total_size_bytes": sum(f.get('size', 0) for f in storage.files.values())
        }
    }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*80)
    print("YMERA Platform - Phase 1: Core Integration")
    print("="*80)
    print("\nStarting server on http://0.0.0.0:8000")
    print("\nAPI Documentation: http://0.0.0.0:8000/docs")
    print("Health Check: http://0.0.0.0:8000/health")
    print("="*80 + "\n")
    
    uvicorn.run(
        "phase1_integrated_agent_manager:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
