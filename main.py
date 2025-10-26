"""
Main Application Entry Point for YMERA Multi-Agent AI System
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn

from config import settings
from database import init_db, close_db
from logger import logger
from base_agent import AgentState


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


@app.get(f"{settings.api_prefix}/agents")
async def list_agents() -> Dict[str, Any]:
    """List all agents"""
    # This would query the database for active agents
    return {
        "agents": [],
        "total": 0
    }


@app.post(f"{settings.api_prefix}/agents")
async def create_agent(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new agent"""
    # This would create a new agent instance
    agent_id = agent_data.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    return {
        "agent_id": agent_id,
        "status": "created"
    }


@app.get(f"{settings.api_prefix}/agents/{{agent_id}}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get agent details"""
    # This would query the database for the specific agent
    return {
        "agent_id": agent_id,
        "state": AgentState.INITIALIZED.value,
        "message": "Agent details"
    }


@app.delete(f"{settings.api_prefix}/agents/{{agent_id}}")
async def delete_agent(agent_id: str) -> Dict[str, str]:
    """Delete an agent"""
    # This would stop and remove the agent
    return {
        "agent_id": agent_id,
        "status": "deleted"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
