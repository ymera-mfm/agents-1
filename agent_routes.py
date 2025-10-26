# api/agent_routes.py
"""
API routes for agent management, reporting, and task handling
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi import Query, Path, Body, BackgroundTasks
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid
import json

from models import (
    Agent, AgentCreate, AgentUpdate, AgentResponse, AgentStatus,
    Task, TaskCreate, TaskUpdate, TaskResponse, TaskStatus, TaskPriority,
    AdminApproval, AdminApprovalCreate, AdminApprovalUpdate, AdminApprovalResponse
)

from services import (
    auth_service, agent_manager, task_manager, 
    reporting_enforcer, security_monitor, audit_system,
    notification_manager, connection_manager
)

router = APIRouter(prefix="/agents", tags=["agents"])

# Agent management routes
@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(auth_service.get_current_user)
):
    """Register a new agent"""
    agent_result = await agent_manager.register_agent({
        "name": agent_data.name,
        "description": agent_data.description,
        "owner_id": current_user.id,
        "capabilities": agent_data.capabilities,
        "configuration": agent_data.configuration
    })
    
    # Log audit event
    background_tasks.add_task(
        audit_system.log_event,
        "agent_creation",
        "agent",
        agent_result["id"],
        "create",
        current_user.id,
        {"name": agent_data.name}
    )
    
    return agent_result

@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    status: Optional[str] = None,
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(auth_service.get_current_user)
):
    """List user's agents with optional filtering"""
    return await agent_manager.list_agents(current_user.id, status, limit, offset)

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str = Path(...),
    current_user = Depends(auth_service.get_current_user)
):
    """Get agent details"""
    agent = await agent_manager.get_agent(agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str = Path(...),
    agent_data: AgentUpdate = Body(...),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(auth_service.get_current_user)
):
    """Update agent details"""
    agent = await agent_manager.update_agent(agent_id, agent_data.dict(), current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Log audit event
    if background_tasks:
        background_tasks.add_task(
            audit_system.log_event,
            "agent_update",
            "agent",
            agent_id,
            "update",
            current_user.id,
            {"updated_fields": [k for k, v in agent_data.dict(exclude_unset=True).items()]}
        )
    
    return agent

@router.post("/{agent_id}/action", response_model=Dict[str, Any])
async def request_agent_action(
    agent_id: str = Path(...),
    action_data: Dict[str, Any] = Body(...),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(auth_service.get_current_user)
):
    """Request action on agent (freeze, unfreeze, delete, etc.)"""
    action = action_data.get("action")
    reason = action_data.get("reason", "No reason provided")
    
    result = await agent_manager.request_agent_action(
        agent_id, action, reason, current_user.id
    )
    
    # Log audit event
    if background_tasks:
        background_tasks.add_task(
            audit_system.log_event,
            "agent_action_request",
            "agent",
            agent_id,
            f"request_{action}",
            current_user.id,
            {"reason": reason, "approval_id": result.get("approval_id")}
        )
    
    return result

@router.post("/{agent_id}/report", response_model=Dict[str, Any])
async def submit_agent_report(
    agent_id: str = Path(...),
    report_data: Dict[str, Any] = Body(...),
    background_tasks: BackgroundTasks = None,
    request_ip: str = None,
    current_agent = Depends(auth_service.get_current_agent)
):
    """Submit agent report/heartbeat"""
    # Verify agent identity
    if current_agent["id"] != agent_id:
        raise HTTPException(status_code=403, detail="Not authorized to report for this agent")
    
    # Process report
    result = await agent_manager.handle_agent_report(
        agent_id, report_data, ip_address=request_ip
    )
    
    # Schedule security analysis in background
    if background_tasks:
        background_tasks.add_task(
            security_monitor.analyze_agent_report,
            agent_id, report_data
        )
    
    return result

# WebSocket endpoint
@router.websocket("/{agent_id}/ws")
async def agent_websocket(
    websocket: WebSocket,
    agent_id: str = Path(...),
    api_key: str = Query(...)
):
    """WebSocket connection for real-time agent communication"""
    try:
        # Authenticate agent
        valid = await agent_manager.verify_agent_api_key(agent_id, api_key)
        if not valid:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Validate that the agent isn't deleted or suspended
        agent_status = await agent_manager.get_agent_status(agent_id)
        if agent_status in [AgentStatus.DELETED.value, AgentStatus.SUSPENDED.value]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Register connection
        connection_id = await connection_manager.connect(
            websocket, agent_id, "agent", {"agent_id": agent_id}
        )
        
        # Register agent as connected
        await agent_manager.register_ws_connection(agent_id, websocket)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_json()
                
                # Handle message
                await connection_manager.handle_message(connection_id, data)
                
        except WebSocketDisconnect:
            # Normal disconnect
            pass
            
        except Exception as e:
            # Error handling
            logger.error(f"Agent WebSocket error: {e}")
            
        finally:
            # Unregister connection
            await agent_manager.unregister_ws_connection(agent_id, websocket)
            await connection_manager.disconnect(connection_id)
            
    except Exception as e:
        logger.error(f"Agent WebSocket connection error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)