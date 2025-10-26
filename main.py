"""
Main Application Entry Point for YMERA Multi-Agent AI System
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, List
import uvicorn
import json

from config import settings
from database import init_db, close_db
from logger import logger
from base_agent import AgentState


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        message_str = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get(f"{settings.api_prefix}/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get(f"{settings.api_prefix}/system/info")
async def system_info() -> Dict[str, Any]:
    """System information endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "websocket_connections": len(manager.active_connections)
    }


@app.get(f"{settings.api_prefix}/agents")
async def list_agents() -> Dict[str, Any]:
    """List all agents"""
    # This would query the database for active agents
    return {
        "success": True,
        "data": {
            "agents": [],
            "pagination": {
                "page": 1,
                "limit": 20,
                "total": 0,
                "pages": 0
            }
        }
    }


@app.post(f"{settings.api_prefix}/agents")
async def create_agent(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new agent"""
    # This would create a new agent instance
    agent_id = agent_data.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    # Broadcast agent creation event
    await manager.broadcast({
        "event": "agent:created",
        "data": {
            "id": agent_id,
            "name": agent_data.get("name", "New Agent"),
            "type": agent_data.get("type", "coder")
        }
    })
    
    return {
        "success": True,
        "data": {
            "id": agent_id,
            "status": "created"
        }
    }


@app.get(f"{settings.api_prefix}/agents/{{agent_id}}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get agent details"""
    # This would query the database for the specific agent
    return {
        "success": True,
        "data": {
            "id": agent_id,
            "name": f"Agent {agent_id}",
            "type": "coder",
            "status": "active",
            "state": AgentState.INITIALIZED.value,
            "description": "AI Agent",
            "capabilities": ["code_generation", "debugging"],
            "metrics": {
                "tasksCompleted": 0,
                "successRate": 0.0,
                "avgExecutionTime": 0
            }
        }
    }


@app.delete(f"{settings.api_prefix}/agents/{{agent_id}}")
async def delete_agent(agent_id: str) -> Dict[str, Any]:
    """Delete an agent"""
    # This would stop and remove the agent
    
    # Broadcast agent deletion event
    await manager.broadcast({
        "event": "agent:deleted",
        "data": {
            "id": agent_id
        }
    })
    
    return {
        "success": True,
        "message": "Agent deleted successfully"
    }


@app.get(f"{settings.api_prefix}/projects")
async def list_projects() -> Dict[str, Any]:
    """List all projects"""
    return {
        "success": True,
        "data": {
            "projects": []
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "subscribe":
                channel = message.get("channel")
                logger.info(f"Client subscribed to channel: {channel}")
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "channel": channel
                }))
            else:
                # Echo back for now
                await websocket.send_text(json.dumps({
                    "type": "message",
                    "data": message
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
