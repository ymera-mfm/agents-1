"""
Agent Manager API Routes
FastAPI endpoints for agent management operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/agent-manager", tags=["Agent Manager"])


# Request/Response Models
class AgentRegistrationRequest(BaseModel):
    agent_id: str
    agent_type: str
    capabilities: List[str]
    config: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class AgentReportRequest(BaseModel):
    agent_id: str
    metrics: Dict[str, Any]
    issues: List[Dict[str, Any]] = []
    data: Dict[str, Any] = {}


class TaskAssignmentRequest(BaseModel):
    agent_id: str
    task_type: str
    task_data: Dict[str, Any]
    priority: int = 5
    deadline: Optional[str] = None


class ApprovalRequest(BaseModel):
    approval_id: str
    approved_by: str
    approval_token: str


# Placeholder dependency - will be injected by main app
async def get_agent_manager():
    """Dependency to get agent manager instance"""
    # This will be overridden by the main application
    raise HTTPException(status_code=500, detail="Agent Manager not initialized")


@router.post("/agents/register", status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: AgentRegistrationRequest,
    agent_manager=Depends(get_agent_manager)
):
    """Register a new agent"""
    try:
        result = await agent_manager.register_agent(
            agent_id=request.agent_id,
            agent_type=request.agent_type,
            capabilities=request.capabilities,
            config=request.config,
            metadata=request.metadata
        )
        return result
    except Exception as e:
        logger.error("Agent registration failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/activate")
async def activate_agent(
    agent_id: str,
    activated_by: str,
    agent_manager=Depends(get_agent_manager)
):
    """Activate an agent"""
    try:
        result = await agent_manager.activate_agent(agent_id, activated_by)
        return result
    except Exception as e:
        logger.error("Agent activation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: str,
    reason: str,
    deactivated_by: str,
    agent_manager=Depends(get_agent_manager)
):
    """Deactivate an agent"""
    try:
        result = await agent_manager.deactivate_agent(agent_id, reason, deactivated_by)
        return result
    except Exception as e:
        logger.error("Agent deactivation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/suspend")
async def suspend_agent(
    agent_id: str,
    reason: str,
    suspended_by: str,
    duration: Optional[int] = None,
    agent_manager=Depends(get_agent_manager)
):
    """Suspend an agent"""
    try:
        result = await agent_manager.suspend_agent(agent_id, reason, suspended_by, duration)
        return result
    except Exception as e:
        logger.error("Agent suspension failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/freeze")
async def freeze_agent(
    agent_id: str,
    reason: str,
    frozen_by: str,
    agent_manager=Depends(get_agent_manager)
):
    """Freeze an agent"""
    try:
        result = await agent_manager.freeze_agent(agent_id, reason, frozen_by)
        return result
    except Exception as e:
        logger.error("Agent freeze failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    reason: str,
    deleted_by: str,
    approval_token: str,
    agent_manager=Depends(get_agent_manager)
):
    """Delete an agent (requires admin approval)"""
    try:
        result = await agent_manager.delete_agent(agent_id, reason, deleted_by, approval_token)
        return result
    except Exception as e:
        logger.error("Agent deletion failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}/status")
async def get_agent_status(
    agent_id: str,
    agent_manager=Depends(get_agent_manager)
):
    """Get agent status and metrics"""
    try:
        status_data = await agent_manager.get_agent_status(agent_id)
        return status_data
    except Exception as e:
        logger.error("Failed to get agent status", error=str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/agents/{agent_id}/report")
async def receive_agent_report(
    agent_id: str,
    report: AgentReportRequest,
    agent_manager=Depends(get_agent_manager)
):
    """Receive periodic report from agent"""
    try:
        result = await agent_manager.receive_agent_report(
            agent_id=agent_id,
            report_data={
                "metrics": report.metrics,
                "issues": report.issues,
                **report.data
            }
        )
        return result
    except Exception as e:
        logger.error("Failed to process report", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/assign")
async def assign_task(
    request: TaskAssignmentRequest,
    agent_manager=Depends(get_agent_manager)
):
    """Assign a task to an agent"""
    try:
        deadline = datetime.fromisoformat(request.deadline) if request.deadline else None
        
        result = await agent_manager.assign_task(
            agent_id=request.agent_id,
            task_type=request.task_type,
            task_data=request.task_data,
            priority=request.priority,
            deadline=deadline
        )
        return result
    except Exception as e:
        logger.error("Task assignment failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/approve")
async def approve_action(
    request: ApprovalRequest,
    agent_manager=Depends(get_agent_manager)
):
    """Approve a pending agent action"""
    try:
        result = await agent_manager.approve_pending_action(
            approval_id=request.approval_id,
            approved_by=request.approved_by,
            approval_token=request.approval_token
        )
        return result
    except Exception as e:
        logger.error("Approval failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/system/overview")
async def get_system_overview(
    agent_manager=Depends(get_agent_manager)
):
    """Get system overview for admin"""
    try:
        overview = await agent_manager.get_system_overview()
        return overview
    except Exception as e:
        logger.error("Failed to get system overview", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent_manager",
        "timestamp": datetime.utcnow().isoformat()
    }
