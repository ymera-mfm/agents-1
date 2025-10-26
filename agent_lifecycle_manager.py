# lifecycle/agent_lifecycle_manager.py
"""
Agent lifecycle manager with admin approval workflow, comprehensive 
audit trail, and controlled state transitions.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

from models import Agent, AdminApproval, AuditLog, AgentStatus, AdminApprovalStatus, AgentAction
from monitoring.telemetry_manager import tracer

logger = logging.getLogger(__name__)

class AgentLifecycleManager:
    """Agent lifecycle manager with admin approval workflow"""
    
    def __init__(self, manager):
        """Initialize with manager reference"""
        self.manager = manager
        self.pending_actions = {}
        
    @tracer.start_as_current_span("request_lifecycle_action")
    async def request_agent_action(self, agent_id: str, action: AgentAction, 
                                 reason: str, requested_by: str) -> Dict[str, Any]:
        """
        Request a lifecycle action on an agent, requires admin approval
        """
        try:
            # Validate agent exists
            async with self.manager.get_db_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return {"error": "Agent not found", "status": "failed"}
                
                # Validate action is valid for current status
                if not self._validate_action_for_status(action, agent.status):
                    return {
                        "error": f"Action {action} not valid for agent status {agent.status}",
                        "status": "failed"
                    }
                
                # Create admin approval request
                approval = AdminApproval(
                    request_type="agent_action",
                    resource_id=agent_id,
                    resource_type="agent",
                    action=action.value,
                    reason=reason,
                    requested_by=requested_by,
                    status=AdminApprovalStatus.PENDING.value
                )
                session.add(approval)
                
                # Create audit log
                audit_log = AuditLog(
                    event_type="lifecycle_action_request",
                    resource_type="agent",
                    resource_id=agent_id,
                    action=f"request_{action.value}",
                    performed_by=requested_by,
                    details={
                        "reason": reason,
                        "approval_id": approval.id
                    }
                )
                session.add(audit_log)
                
                await session.commit()
                
                # Store pending action
                self.pending_actions[approval.id] = {
                    "agent_id": agent_id,
                    "action": action.value,
                    "requested_by": requested_by,
                    "requested_at": datetime.utcnow().isoformat(),
                    "reason": reason
                }
                
                # Notify admin of pending approval
                await self._notify_admins_of_pending_approval(approval.id, agent_id, action.value, reason)
                
                return {
                    "status": "pending_approval",
                    "message": f"Action {action} requested and pending admin approval",
                    "approval_id": approval.id
                }
                
        except Exception as e:
            logger.error(f"Error requesting agent action: {e}")
            return {"error": str(e), "status": "failed"}
    
    @tracer.start_as_current_span("execute_agent_action")
    async def _execute_agent_action(self, agent_id: str, action: str, 
                                  approver_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute approved agent action
        """
        try:
            async with self.manager.get_db_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return {"error": "Agent not found", "status": "failed"}
                
                result = {"status": "success", "action": action, "agent_id": agent_id}
                
                # Perform action based on type
                if action == AgentAction.FREEZE.value:
                    agent.status = AgentStatus.FROZEN.value
                    agent.frozen_at = datetime.utcnow()
                    agent.frozen_by = approver_id
                    agent.frozen_reason = notes or "Admin action"
                    result["message"] = "Agent frozen successfully"
                    
                elif action == AgentAction.UNFREEZE.value:
                    previous_status = agent.status
                    agent.status = AgentStatus.INACTIVE.value
                    result["message"] = f"Agent unfrozen from {previous_status} to inactive"
                    
                elif action == AgentAction.DELETE.value:
                    agent.status = AgentStatus.DELETED.value
                    agent.deleted_at = datetime.utcnow()
                    agent.deleted_by = approver_id
                    
                    # Revoke API keys
                    agent.api_key_hash = None
                    result["message"] = "Agent deleted successfully"
                    
                elif action == AgentAction.AUDIT.value:
                    # Just log audit event, don't change status
                    result["message"] = f"Agent audit triggered by {approver_id}"
                    
                elif action == AgentAction.ISOLATE.value:
                    agent.status = AgentStatus.ISOLATED.value
                    agent.isolated_at = datetime.utcnow()
                    agent.isolated_by = approver_id
                    result["message"] = "Agent isolated successfully"
                
                # Create audit log
                audit_log = AuditLog(
                    event_type="lifecycle_action_executed",
                    resource_type="agent",
                    resource_id=agent_id,
                    action=action,
                    performed_by=approver_id,
                    details={
                        "notes": notes,
                        "previous_status": agent.status,
                        "new_status": agent.status
                    }
                )
                session.add(audit_log)
                
                await session.commit()
                
                # Notify agent of status change if connected
                await self._notify_agent_of_status_change(agent_id, action)
                
                return result
                
        except Exception as e:
            logger.error(f"Error executing agent action: {e}")
            return {"error": str(e), "status": "failed"}
    
    def _validate_action_for_status(self, action: AgentAction, current_status: str) -> bool:
        """
        Validate if an action is valid for the current agent status
        """
        # Valid status transitions
        valid_transitions = {
            AgentStatus.ACTIVE.value: [
                AgentAction.FREEZE, AgentAction.WARN, AgentAction.AUDIT, AgentAction.ISOLATE
            ],
            AgentStatus.INACTIVE.value: [
                AgentAction.WARN, AgentAction.DELETE, AgentAction.AUDIT
            ],
            AgentStatus.BUSY.value: [
                AgentAction.WARN, AgentAction.FREEZE, AgentAction.AUDIT, AgentAction.ISOLATE
            ],
            AgentStatus.FROZEN.value: [
                AgentAction.UNFREEZE, AgentAction.DELETE, AgentAction.AUDIT
            ],
            AgentStatus.SUSPENDED.value: [
                AgentAction.UNFREEZE, AgentAction.DELETE, AgentAction.AUDIT
            ],
            AgentStatus.ISOLATED.value: [
                AgentAction.UNFREEZE, AgentAction.DELETE, AgentAction.AUDIT
            ],
            AgentStatus.ERROR.value: [
                AgentAction.UNFREEZE, AgentAction.FREEZE, AgentAction.DELETE, AgentAction.AUDIT
            ]
        }
        
        # Check if action is valid for current status
        if current_status in valid_transitions:
            return action in valid_transitions[current_status]
        
        return False
    
    async def _notify_admins_of_pending_approval(self, approval_id: str, agent_id: str, 
                                              action: str, reason: str) -> None:
        """
        Notify administrators of pending approval request
        """
        try:
            # Get admin users
            async with self.manager.get_db_session() as session:
                from sqlalchemy import select
                from models import User
                
                # Find users with admin role
                result = await session.execute(
                    select(User).where(User.roles.contains(['admin']))
                )
                admin_users = result.scalars().all()
                
                # Send notification to each admin
                notification = {
                    "type": "approval_required",
                    "title": f"Agent {action} approval required",
                    "message": f"Action: {action}\nAgent: {agent_id}\nReason: {reason}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "approval_id": approval_id,
                        "agent_id": agent_id,
                        "action": action
                    },
                    "priority": "high"
                }
                
                for admin in admin_users:
                    await self.manager.notification_manager.send_notification(
                        admin.id, notification
                    )
                    
                logger.info(f"Admin approval notifications sent for action {action} on agent {agent_id}")
                
        except Exception as e:
            logger.error(f"Failed to notify admins of approval request: {e}")
    
    async def _notify_agent_of_status_change(self, agent_id: str, action: str) -> None:
        """
        Notify agent of status change via WebSocket if connected
        """
        if agent_id in self.manager.active_connections:
            for ws in self.manager.active_connections[agent_id]:
                try:
                    await ws.send_json({
                        "type": "status_change",
                        "action": action,
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Your status has been changed due to admin action: {action}"
                    })
                except Exception as e:
                    logger.error(f"Failed to notify agent {agent_id} of status change: {e}")
    
    @tracer.start_as_current_span("get_agent_lifecycle_history")
    async def get_agent_lifecycle_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get complete lifecycle history for an agent
        """
        try:
            async with self.manager.get_db_session() as session:
                # Get agent info
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return []
                
                # Get audit logs for this agent
                from sqlalchemy import select
                result = await session.execute(
                    select(AuditLog).where(
                        AuditLog.resource_type == "agent",
                        AuditLog.resource_id == agent_id
                    ).order_by(AuditLog.timestamp.desc())
                )
                audit_logs = result.scalars().all()
                
                # Format history
                history = []
                for log in audit_logs:
                    history.append({
                        "timestamp": log.timestamp.isoformat(),
                        "action": log.action,
                        "performed_by": log.performed_by,
                        "details": log.details
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error fetching agent lifecycle history: {e}")
            return []