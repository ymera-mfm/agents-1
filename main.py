"""
Main Application Entry Point for YMERA Multi-Agent AI System
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, List
import uvicorn
import json
import asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from database import init_db, close_db
from logger import logger
from base_agent import AgentState


class ConnectionManager:
    """WebSocket connection manager with optimized broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.broadcast_timeout = 5.0  # seconds
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients with timeout and error handling"""
        message_str = json.dumps(message)
        
        async def send_to_client(connection: WebSocket) -> bool:
            """Send message to a single client with timeout"""
            try:
                await asyncio.wait_for(
                    connection.send_text(message_str),
                    timeout=self.broadcast_timeout
                )
                return True
            except asyncio.TimeoutError:
                logger.warning(f"Broadcast timeout for client, removing connection")
                return False
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                return False
        
        # Send to all clients concurrently with timeout
        if self.active_connections:
            results = await asyncio.gather(
                *[send_to_client(conn) for conn in self.active_connections],
                return_exceptions=True
            )
            
            # Remove failed connections
            failed_connections = [
                conn for conn, success in zip(self.active_connections, results)
                if not success or isinstance(success, Exception)
            ]
            
            for conn in failed_connections:
                self.disconnect(conn)


manager = ConnectionManager()

# Initialize rate limiter with Redis backend
limiter = Limiter(key_func=get_remote_address, storage_uri=f"redis://{settings.redis_host}:{settings.redis_port}")


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

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # HSTS header for HTTPS enforcement
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Additional security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


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
@limiter.limit("100/minute")
async def list_agents(request: Request) -> Dict[str, Any]:
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
@limiter.limit("100/minute")
async def create_agent(request: Request, agent_data: Dict[str, Any]) -> Dict[str, Any]:
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


@app.get(f"{settings.api_prefix}/agents/search")
async def search_agents(q: str = "") -> Dict[str, Any]:
    """Search agents by query"""
    # This would search the database for agents matching the query
    return {
        "success": True,
        "data": {
            "agents": [],
            "query": q,
            "total": 0
        }
    }


@app.post(f"{settings.api_prefix}/agents/bulk")
async def bulk_create_agents(bulk_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create multiple agents in batch"""
    agents = bulk_data.get("agents", [])
    created_ids = []
    
    for agent in agents:
        agent_id = agent.get("agent_id")
        if agent_id:
            created_ids.append(agent_id)
            # Broadcast bulk agent creation event
            await manager.broadcast({
                "event": "agent:bulk_created",
                "data": {
                    "id": agent_id,
                    "name": agent.get("name", "Bulk Agent"),
                    "type": agent.get("type", "coder")
                }
            })
    
    return {
        "success": True,
        "data": {
            "created": len(created_ids),
            "agent_ids": created_ids
        }
    }


@app.get(f"{settings.api_prefix}/agents/export")
async def export_agents(format: str = "json") -> Dict[str, Any]:
    """Export agent data"""
    # This would export all agents to the specified format
    return {
        "success": True,
        "data": {
            "agents": [],
            "format": format,
            "exported_at": "2025-10-26T15:31:17.634Z"
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


@app.put(f"{settings.api_prefix}/agents/{{agent_id}}")
async def update_agent(agent_id: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update agent configuration"""
    # Broadcast agent update event
    await manager.broadcast({
        "event": "agent:updated",
        "data": {
            "id": agent_id,
            "name": agent_data.get("name"),
            "config": agent_data.get("config")
        }
    })
    
    return {
        "success": True,
        "data": {
            "id": agent_id,
            "status": "updated"
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


@app.get(f"{settings.api_prefix}/analytics")
async def get_analytics(
    start_date: str = None,
    end_date: str = None,
    group_by: str = "type",
    metrics: str = "count"
) -> Dict[str, Any]:
    """Get analytics data"""
    # This would calculate analytics based on parameters
    return {
        "success": True,
        "data": {
            "analytics": {
                "count": 0,
                "avg_execution_time": 0.0,
                "success_rate": 0.0
            },
            "group_by": group_by,
            "metrics": metrics.split(","),
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }
    }


@app.get(f"{settings.api_prefix}/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get system metrics"""
    return {
        "success": True,
        "data": {
            "metrics": {
                "total_agents": 0,
                "active_agents": 0,
                "tasks_completed": 0,
                "tasks_pending": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "uptime_seconds": 0
            }
        }
    }


@app.post(f"{settings.api_prefix}/agents/{agent_id}/config")
@limiter.limit("100/minute")
async def update_agent_config(request: Request, agent_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update agent runtime configuration dynamically"""
    try:
        # Validate agent exists (in production, would check database)
        if not agent_id:
            raise HTTPException(status_code=400, detail="agent_id is required")
        
        # Validate configuration against schema (in production, would use JSON Schema)
        # For now, accept any valid JSON configuration
        updated_config = config_data.get("config", {})
        
        logger.info(f"Updating configuration for agent {agent_id}: {updated_config}")
        
        # In production, would:
        # 1. Validate config against agent-specific JSON Schema
        # 2. Update agent runtime configuration
        # 3. Persist to database
        # 4. Notify agent of configuration change via message broker
        
        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "config": updated_config,
                "status": "updated"
            }
        }
    except Exception as e:
        logger.error(f"Error updating agent config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(f"{settings.api_prefix}/agents/{agent_id}/schema")
@limiter.limit("100/minute")
async def get_agent_config_schema(request: Request, agent_id: str) -> Dict[str, Any]:
    """Get JSON Schema for agent configuration parameters"""
    try:
        # In production, would fetch agent-specific schema from database or agent class
        # For now, return a generic schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": f"Configuration for Agent {agent_id}",
            "properties": {
                "checkpoint_interval": {
                    "type": "integer",
                    "title": "Checkpoint Interval",
                    "description": "Interval in seconds between state checkpoints",
                    "default": 60,
                    "minimum": 10,
                    "maximum": 3600
                },
                "max_retries": {
                    "type": "integer",
                    "title": "Max Retries",
                    "description": "Maximum number of retry attempts for failed operations",
                    "default": 3,
                    "minimum": 0,
                    "maximum": 10
                },
                "timeout": {
                    "type": "integer",
                    "title": "Operation Timeout",
                    "description": "Timeout in seconds for operations",
                    "default": 300,
                    "minimum": 10,
                    "maximum": 3600
                },
                "log_level": {
                    "type": "string",
                    "title": "Log Level",
                    "description": "Logging level for this agent",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    "default": "INFO"
                },
                "enable_monitoring": {
                    "type": "boolean",
                    "title": "Enable Monitoring",
                    "description": "Enable performance monitoring for this agent",
                    "default": True
                }
            },
            "required": ["checkpoint_interval"]
        }
        
        return {
            "success": True,
            "data": {
                "agent_id": agent_id,
                "schema": schema
            }
        }
    except Exception as e:
        logger.error(f"Error fetching agent schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{settings.api_prefix}/metrics/frontend")
@limiter.limit("1000/minute")
async def receive_frontend_metrics(request: Request, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Receive and log frontend performance metrics (Web Vitals)"""
    try:
        metric_name = metrics_data.get("name")
        metric_value = metrics_data.get("value")
        metric_id = metrics_data.get("id")
        session_id = metrics_data.get("sessionId", "unknown")
        
        if not metric_name or metric_value is None:
            raise HTTPException(status_code=400, detail="name and value are required")
        
        # Log the metric for analysis
        logger.info(
            f"Frontend Performance Metric - "
            f"Name: {metric_name}, "
            f"Value: {metric_value}, "
            f"ID: {metric_id}, "
            f"Session: {session_id}"
        )
        
        # In production, would:
        # 1. Store metrics in time-series database (e.g., InfluxDB, TimescaleDB)
        # 2. Aggregate metrics for dashboards
        # 3. Alert on poor performance metrics
        # 4. Track metrics by user session
        
        return {
            "success": True,
            "data": {
                "metric_name": metric_name,
                "metric_value": metric_value,
                "status": "recorded"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording frontend metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{settings.api_prefix}/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """User authentication endpoint with strict rate limiting"""
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    # For testing purposes, accept any credentials
    # In production, this would validate against a user database
    return {
        "success": True,
        "access_token": f"test_token_{username}",
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
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
