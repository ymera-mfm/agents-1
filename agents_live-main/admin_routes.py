# api/admin_routes.py
"""
API routes for administrative functions and approval workflows
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import Query, Path, Body
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from models import (
    AdminApproval, AdminApprovalCreate, AdminApprovalUpdate, AdminApprovalResponse,
    AdminApprovalStatus, AuditLogResponse, AuditLogQuery
)

from services import (
    auth_service, agent_manager, lifecycle_manager, audit_system,
    notification_manager
)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/approvals", response_model=List[AdminApprovalResponse])
async def list_approvals(
    status: Optional[List[str]] = Query(None),
    request_type: Optional[str] = None,
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(auth_service.get_admin_user)
):
    """List approval requests with filtering"""
    return await lifecycle_manager.list_approvals(status, request_type, limit, offset)

@router.get("/approvals/{approval_id}", response_model=AdminApprovalResponse)
async def get_approval(
    approval_id: str = Path(...),
    current_user = Depends(auth_service.get_admin_user)
):
    """Get approval request details"""
    approval = await lifecycle_manager.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return approval

@router.post("/approvals/{approval_id}/process", response_model=Dict[str, Any])
async def process_approval(
    approval_id: str = Path(...),
    approval_data: AdminApprovalUpdate = Body(...),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(auth_service.get_admin_user)
):
    """Process approval request (approve/reject)"""
    result = await lifecycle_manager.process_approval(
        approval_id,
        approval_data.status,
        current_user.id,
        approval_data.notes
    )
    
    # Log audit event
    if background_tasks:
        background_tasks.add_task(
            audit_system.log_event,
            "approval_processed",
            "approval",
            approval_id,
            approval_data.status,
            current_user.id,
            {"notes": approval_data.notes}
        )
    
    # Notify requester
    if result.get("requested_by"):
        background_tasks.add_task(
            notification_manager.send_notification,
            result["requested_by"],
            {
                "type": "approval_processed",
                "title": f"Your request has been {approval_data.status}",
                "message": approval_data.notes or f"Your request has been {approval_data.status}",
                "priority": "medium",
                "metadata": {
                    "approval_id": approval_id,
                    "status": approval_data.status
                }
            }
        )
    
    return result

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    performed_by: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(auth_service.get_admin_user)
):
    """Search audit logs with filtering"""
    query = AuditLogQuery(
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        performed_by=performed_by,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return await audit_system.search_audit_logs(query)

@router.post("/agents/{agent_id}/exempt-reporting", response_model=Dict[str, Any])
async def exempt_agent_from_reporting(
    agent_id: str = Path(...),
    exemption_data: Dict[str, Any] = Body(...),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(auth_service.get_admin_user)
):
    """Exempt agent from mandatory reporting requirements"""
    exempt = exemption_data.get("exempt", True)
    reason = exemption_data.get("reason", "Administrative exemption")
    
    result = await agent_manager.set_reporting_exemption(
        agent_id, exempt, reason, current_user.id
    )
    
    # Log audit event
    if background_tasks:
        background_tasks.add_task(
            audit_system.log_event,
            "reporting_exemption",
            "agent",
            agent_id,
            "exempt" if exempt else "unexempt",
            current_user.id,
            {"reason": reason}
        )
    
    return result