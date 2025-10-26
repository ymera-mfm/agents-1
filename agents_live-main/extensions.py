# api_extensions.py - Complete API routes and WebSocket implementation
"""
Extended API routes for the production agent management system
Includes: WebSocket support, advanced features, monitoring, and enterprise endpoints
"""

from fastapi import WebSocket, WebSocketDisconnect, Query, Path, Body
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, List, Optional, Any
import asyncio
import json
import uuid
from datetime import datetime, timedelta
import io
import csv

# Import our advanced features
from advanced_features import (
    connection_manager, cache_manager, security_manager, 
    task_scheduler, health_monitor, notification_manager, 
    analytics_engine, CacheManager, SecurityManager,
    TaskScheduler, HealthMonitor, NotificationManager, AnalyticsEngine
)

# Additional API routes to add to main.py

# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str = Path(...),
    token: str = Query(...)
):
    """WebSocket endpoint for real-time communication"""
    try:
        # Verify token
        payload = await auth_service.verify_token(token)
        if payload.get("sub") != user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        connection_id = str(uuid.uuid4())
        await connection_manager.connect(websocket, user_id, connection_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message["type"] == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                elif message["type"] == "task_update":
                    # Handle task updates from agents
                    await handle_task_update(message, user_id)
                
                elif message["type"] == "agent_status":
                    # Handle agent status updates
                    await handle_agent_status(message, user_id)
                
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            connection_manager.disconnect(user_id, connection_id)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011, reason="Server error")

async def handle_task_update(message: dict, user_id: str):
    """Handle task update from agent"""
    task_id = message.get("task_id")
    status = message.get("status")
    result = message.get("result")
    
    if task_id:
        async with db_manager.async_session() as session:
            task = await session.get(Task, task_id)
            if task and task.user_id == user_id:
                task.status = TaskStatus(status)
                if result:
                    task.result = result
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = datetime.utcnow()
                
                await session.commit()
                
                # Send notification
                await notification_manager.send_notification(user_id, {
                    "type": "task_update",
                    "title": "Task Update",
                    "message": f"Task {task.name} is now {status}",
                    "task_id": task_id
                })

async def handle_agent_status(message: dict, user_id: str):
    """Handle agent status update"""
    agent_id = message.get("agent_id")
    status = message.get("status")
    
    if agent_id:
        async with db_manager.async_session() as session:
            agent = await session.get(Agent, agent_id)
            if agent and agent.owner_id == user_id:
                agent.status = AgentStatus(status)
                agent.last_heartbeat = datetime.utcnow()
                await session.commit()

# =============================================================================
# ADVANCED TASK MANAGEMENT
# =============================================================================

@app.post("/tasks/batch", response_model=dict)
async def create_batch_tasks(
    tasks: List[TaskCreate],
    current_user: User = Depends(get_current_user)
):
    """Create multiple tasks in batch"""
    task_ids = []
    
    async with db_manager.async_session() as session:
        for task_data in tasks:
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
            await session.flush()  # Get ID without committing
            task_ids.append(task.id)
        
        await session.commit()
    
    # Schedule all tasks
    for i, task_id in enumerate(task_ids):
        await task_scheduler.schedule_task({
            "task_id": task_id,
            "task_type": tasks[i].task_type,
            "parameters": tasks[i].parameters
        }, priority=tasks[i].priority.value)
    
    return {"task_ids": task_ids, "count": len(task_ids)}

@app.get("/tasks/stats", response_model=dict)
async def get_task_statistics(
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=90)
):
    """Get task statistics for user"""
    cache_key = f"task_stats:{current_user.id}:{days}"
    
    # Try cache first
    cached_stats = await cache_manager.get(cache_key)
    if cached_stats:
        return cached_stats
    
    # Calculate statistics
    start_date = datetime.utcnow() - timedelta(days=days)
    
    async with db_manager.async_session() as session:
        # Get task counts by status
        result = await session.execute("""
            SELECT status, COUNT(*) as count 
            FROM tasks 
            WHERE user_id = :user_id AND created_at >= :start_date
            GROUP BY status
        """, {"user_id": current_user.id, "start_date": start_date})
        
        status_counts = dict(result.fetchall())
        
        # Get task counts by type
        result = await session.execute("""
            SELECT task_type, COUNT(*) as count 
            FROM tasks 
            WHERE user_id = :user_id AND created_at >= :start_date
            GROUP BY task_type
        """, {"user_id": current_user.id, "start_date": start_date})
        
        type_counts = dict(result.fetchall())
        
        # Calculate average completion time
        result = await session.execute("""
            SELECT AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_time
            FROM tasks 
            WHERE user_id = :user_id AND status = 'completed' AND created_at >= :start_date
        """, {"user_id": current_user.id, "start_date": start_date})
        
        avg_completion_time = result.scalar() or 0
    
    stats = {
        "period_days": days,
        "status_counts": status_counts,
        "type_counts": type_counts,
        "average_completion_time_seconds": float(avg_completion_time),
        "total_tasks": sum(status_counts.values())
    }
    
    # Cache for 1 hour
    await cache_manager.set(cache_key, stats, ttl=3600)
    
    return stats

# =============================================================================
# AGENT MANAGEMENT EXTENSIONS
# =============================================================================

@app.post("/agents/{agent_id}/execute", response_model=dict)
async def execute_agent_command(
    agent_id: str,
    command: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Execute a command on an agent"""
    async with db_manager.async_session() as session:
        agent = await session.get(Agent, agent_id)
        
        if not agent or agent.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Agent is not active")
        
        # Execute command via WebSocket or queue
        command_id = str(uuid.uuid4())
        command_data = {
            "command_id": command_id,
            "agent_id": agent_id,
            "command": command,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Try to send via WebSocket first
        await connection_manager.send_to_user(current_user.id, {
            "type": "agent_command",
            "agent_id": agent_id,
            "data": command_data
        })
        
        # Also queue for processing
        await task_scheduler.schedule_task(command_data, priority=2)
        
        return {"command_id": command_id, "status": "sent"}

@app.get("/agents/available", response_model=List[dict])
async def get_available_agents(
    task_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get available agents for task assignment"""
    async with db_manager.async_session() as session:
        query = select(Agent).where(
            Agent.owner_id == current_user.id,
            Agent.status == AgentStatus.ACTIVE
        )
        
        if task_type:
            query = query.where(Agent.capabilities.contains([task_type]))
        
        result = await session.execute(query)
        agents = result.scalars().all()
        
        return [{
            "id": agent.id,
            "name": agent.name,
            "capabilities": agent.capabilities,
            "last_heartbeat": agent.last_heartbeat,
            "load": await _calculate_agent_load(agent.id)
        } for agent in agents]

async def _calculate_agent_load(agent_id: str) -> float:
    """Calculate current load for an agent"""
    async with db_manager.async_session() as session:
        result = await session.execute(
            select(func.count(Task.id)).where(
                Task.agent_id == agent_id,
                Task.status == TaskStatus.RUNNING
            )
        )
        running_tasks = result.scalar() or 0
        return min(running_tasks / 5.0, 1.0)  # Assume max 5 concurrent tasks

# =============================================================================
# MONITORING & ANALYTICS ENDPOINTS
# =============================================================================

@app.get("/monitoring/health", response_model=dict)
async def detailed_health_check():
    """Detailed health check with component status"""
    health_data = await health_monitor.check_system_health()
    return health_data

@app.get("/monitoring/metrics/live", response_model=dict)
async def get_live_metrics():
    """Get live system metrics"""
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "active_websocket_connections": len(connection_manager.active_connections),
            "cache_stats": cache_manager.cache_stats,
            "task_queue_size": await _get_total_queue_size()
        },
        "database": await _get_db_metrics(),
        "redis": await _get_redis_metrics()
    }
    return metrics

async def _get_total_queue_size() -> int:
    """Get total tasks in all queues"""
    try:
        queues = await redis_client.keys("task_queue:*")
        total_size = 0
        for queue in queues:
            size = await redis_client.zcard(queue)
            total_size += size
        return total_size
    except Exception:
        return 0

async def _get_db_metrics() -> dict:
    """Get database performance metrics"""
    try:
        async with db_manager.async_session() as session:
            # Count active connections (this would be database-specific)
            result = await session.execute("SELECT COUNT(*) as total_tasks FROM tasks WHERE status = 'running'")
            running_tasks = result.scalar()
            
            return {
                "running_tasks": running_tasks,
                "connection_status": "healthy"
            }
    except Exception as e:
        return {"error": str(e), "connection_status": "unhealthy"}

async def _get_redis_metrics() -> dict:
    """Get Redis performance metrics"""
    try:
        info = await redis_client.info()
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/analytics/summary", response_model=dict)
async def get_analytics_summary(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """Get analytics summary"""
    summary = await analytics_engine.get_analytics_summary(hours * 3600)
    
    # Add user-specific analytics
    user_tasks = await _get_user_task_analytics(current_user.id, hours)
    summary["user_analytics"] = user_tasks
    
    return summary

async def _get_user_task_analytics(user_id: str, hours: int) -> dict:
    """Get user-specific task analytics"""
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    async with db_manager.async_session() as session:
        result = await session.execute("""
            SELECT 
                status,
                task_type,
                COUNT(*) as count,
                AVG(CASE WHEN completed_at IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (completed_at - created_at)) 
                    ELSE NULL END) as avg_duration
            FROM tasks 
            WHERE user_id = :user_id AND created_at >= :start_time
            GROUP BY status, task_type
        """, {"user_id": user_id, "start_time": start_time})
        
        analytics_data = {}
        for row in result.fetchall():
            key = f"{row.status}_{row.task_type}"
            analytics_data[key] = {
                "count": row.count,
                "avg_duration": float(row.avg_duration) if row.avg_duration else None
            }
        
        return analytics_data

# =============================================================================
# NOTIFICATION ENDPOINTS
# =============================================================================

@app.get("/notifications", response_model=List[dict])
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get user notifications"""
    notifications = await notification_manager.get_user_notifications(
        current_user.id, limit
    )
    return notifications

@app.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    # Implementation would update notification status
    return {"status": "marked_as_read"}

# =============================================================================
# EXPORT & REPORTING ENDPOINTS
# =============================================================================

@app.get("/export/tasks")
async def export_tasks(
    format: str = Query("csv", regex="^(csv|json)$"),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """Export tasks data"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    async with db_manager.async_session() as session:
        result = await session.execute(
            select(Task).where(
                Task.user_id == current_user.id,
                Task.created_at >= start_date
            ).order_by(Task.created_at.desc())
        )
        tasks = result.scalars().all()
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID", "Name", "Type", "Status", "Priority", 
            "Created", "Completed", "Duration (seconds)"
        ])
        
        # Write data
        for task in tasks:
            duration = None
            if task.completed_at and task.created_at:
                duration = (task.completed_at - task.created_at).total_seconds()
            
            writer.writerow([
                task.id, task.name, task.task_type, task.status, 
                task.priority, task.created_at, task.completed_at, duration
            ])
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=tasks_{days}days.csv"}
        )
    
    else:  # JSON format
        task_data = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "name": task.name,
                "task_type": task.task_type,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "result": task.result
            }
            task_data.append(task_dict)
        
        return JSONResponse(
            content={"tasks": task_data, "exported_at": datetime.utcnow().isoformat()},
            headers={"Content-Disposition": f"attachment; filename=tasks_{days}days.json"}
        )

# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@app.get("/admin/system-info")
async def get_system_info(current_user: User = Depends(get_current_user)):
    """Get system information (admin only)"""
    # In production, add proper admin role checking
    return {
        "version": "1.0.0",
        "uptime": "calculated_uptime_here",
        "total_users": await _count_total_users(),
        "total_agents": await _count_total_agents(),
        "total_tasks": await _count_total_tasks(),
        "system_load": await health_monitor.check_system_health()
    }

async def _count_total_users() -> int:
    async with db_manager.async_session() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar()

async def _count_total_agents() -> int:
    async with db_manager.async_session() as session:
        result = await session.execute(select(func.count(Agent.id)))
        return result.scalar()

async def _count_total_tasks() -> int:
    async with db_manager.async_session() as session:
        result = await session.execute(select(func.count(Task.id)))
        return result.scalar()

# =============================================================================
# RATE-LIMITED ENDPOINTS
# =============================================================================

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Global rate limiting middleware"""
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/metrics"]:
        return await call_next(request)
    
    # Get client identifier
    client_id = request.client.host
    if hasattr(request.state, "user"):
        client_id = f"user:{request.state.user.id}"
    
    # Check rate limit
    allowed = await security_manager.rate_limit(client_id, limit=1000, window=3600)  # 1000/hour
    
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."}
        )
    
    return await call_next(request)

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with logging"""
    await analytics_engine.record_event(
        "http_error",
        getattr(request.state, "user_id", "anonymous"),
        {
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled errors"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    
    await security_manager.log_security_event(
        "system_error",
        {
            "error": str(exc),
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
