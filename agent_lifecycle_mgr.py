import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from config import settings
from database.secure_database_manager import SecureDatabaseManager
from models.secure_models import Agent, Task
from security.rbac_manager import RBACManager, Permission
from monitoring.telemetry_manager import TelemetryManager
from monitoring.alert_manager import AlertManager, AlertCategory, AlertSeverity

logger = logging.getLogger(__name__)

class AgentStatus(str, Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    COMPROMISED = "compromised"
    DECOMMISSIONED = "decommissioned"
    SUSPENDED = "suspended"  # NEW: For admin-suspended agents
    FROZEN = "frozen"  # NEW: For investigation

class AgentAction(str, Enum):
    """Actions that can be taken on agents"""
    SUSPEND = "suspend"
    FREEZE = "freeze"
    RESUME = "resume"
    DECOMMISSION = "decommission"
    RESTART = "restart"

class AgentActionRequest(BaseModel):
    """Request model for agent actions"""
    action: AgentAction
    reason: str
    admin_id: str
    approval_id: Optional[str] = None  # For tracking admin approvals
    metadata: Optional[Dict[str, Any]] = None

class AgentLifecycleManager:
    """Manages the full lifecycle of agents, from registration to decommissioning.
    
    This manager has enhanced authority to:
    - Monitor all agent activities
    - Enforce security policies
    - Suspend/freeze agents on security violations
    - Control API access and information flow
    - Report to admin for critical decisions
    - Require admin approval for destructive actions
    """

    def __init__(
        self, 
        db_manager: SecureDatabaseManager, 
        rbac_manager: RBACManager, 
        telemetry_manager: TelemetryManager, 
        alert_manager: AlertManager
    ):
        self.db_manager = db_manager
        self.rbac_manager = rbac_manager
        self.telemetry_manager = telemetry_manager
        self.alert_manager = alert_manager
        
        # Authority settings
        self.auto_suspend_on_security_violation = getattr(
            settings.performance, 
            'auto_suspend_on_security_violation', 
            True
        )
        self.require_admin_approval_for_delete = getattr(
            settings.performance,
            'require_admin_approval_for_delete',
            True
        )
        
        logger.info("AgentLifecycleManager initialized with enhanced authority.")

    async def register_agent(
        self, 
        tenant_id: str, 
        name: str, 
        agent_type: str, 
        version: str, 
        capabilities: Dict[str, Any],
        admin_id: Optional[str] = None
    ) -> Agent:
        """Registers a new agent in the system with security validation."""
        async with self.db_manager.get_session() as session:
            # Check tenant agent limit
            agent_count = await session.scalar(
                select(func.count(Agent.id)).where(Agent.tenant_id == tenant_id)
            )
            
            max_agents = getattr(settings.performance, 'max_agents_per_tenant', 100)
            
            if agent_count >= max_agents:
                await self.alert_manager.create_alert(
                    category=AlertCategory.SYSTEM,
                    severity=AlertSeverity.WARNING,
                    title="Agent Registration Limit Reached",
                    description=f"Tenant {tenant_id} attempted to register agent {name} but reached the limit of {max_agents}.",
                    source="AgentLifecycleManager",
                    metadata={"tenant_id": tenant_id, "agent_name": name}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Tenant {tenant_id} has reached maximum agent limit of {max_agents}"
                )

            new_agent = Agent(
                tenant_id=tenant_id,
                name=name,
                type=agent_type,
                version=version,
                capabilities=capabilities,
                status=AgentStatus.REGISTERED.value,
                security_score=100  # Start with perfect score
            )
            session.add(new_agent)
            await session.commit()
            await session.refresh(new_agent)
            
            logger.info(f"Agent {new_agent.id} registered for tenant {tenant_id}.")
            
            await self.telemetry_manager.record_event(
                "agent_registered",
                {
                    "agent_id": str(new_agent.id),
                    "tenant_id": tenant_id,
                    "agent_type": agent_type,
                    "registered_by": admin_id or "system"
                }
            )
            
            return new_agent

    async def update_agent_status(
        self, 
        agent_id: str, 
        new_status: AgentStatus, 
        performance_metrics: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        admin_id: Optional[str] = None
    ) -> Optional[Agent]:
        """Updates the status of an existing agent with audit trail."""
        async with self.db_manager.get_session() as session:
            agent = await session.get(Agent, agent_id)
            if agent:
                old_status = agent.status
                agent.status = new_status.value
                agent.last_heartbeat = datetime.utcnow()
                
                if performance_metrics:
                    agent.performance_metrics = performance_metrics
                
                await session.commit()
                await session.refresh(agent)
                
                logger.info(
                    f"Agent {agent_id} status updated from {old_status} to {new_status.value}. "
                    f"Reason: {reason or 'N/A'}"
                )
                
                await self.telemetry_manager.record_event(
                    "agent_status_updated",
                    {
                        "agent_id": agent_id,
                        "old_status": old_status,
                        "new_status": new_status.value,
                        "reason": reason,
                        "changed_by": admin_id or "system"
                    }
                )
                
                # Critical status changes trigger alerts
                if new_status in [AgentStatus.COMPROMISED, AgentStatus.FROZEN, AgentStatus.SUSPENDED]:
                    await self.alert_manager.create_alert(
                        category=AlertCategory.SECURITY,
                        severity=AlertSeverity.EMERGENCY if new_status == AgentStatus.COMPROMISED else AlertSeverity.CRITICAL,
                        title=f"Agent {new_status.value.title()}",
                        description=f"Agent {agent.id} ({agent.name}) has been marked as {new_status.value}. Reason: {reason or 'Not specified'}",
                        source="AgentLifecycleManager",
                        metadata={
                            "agent_id": agent_id,
                            "tenant_id": agent.tenant_id,
                            "old_status": old_status,
                            "reason": reason
                        }
                    )
                
                return agent
            
            logger.warning(f"Agent {agent_id} not found for status update.")
            return None

    async def execute_agent_action(
        self,
        agent_id: str,
        action_request: AgentActionRequest
    ) -> Dict[str, Any]:
        """Execute administrative action on an agent with proper authorization.
        
        Returns:
            Dict with action result and any required follow-up
        """
        async with self.db_manager.get_session() as session:
            agent = await session.get(Agent, agent_id)
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent {agent_id} not found"
                )
            
            # Check if action requires admin approval
            if action_request.action == AgentAction.DECOMMISSION and self.require_admin_approval_for_delete:
                if not action_request.approval_id:
                    return {
                        "status": "pending_approval",
                        "message": f"Decommissioning agent {agent.name} requires admin approval",
                        "agent_id": agent_id,
                        "action": action_request.action.value
                    }
            
            # Execute the action
            result = await self._execute_action(agent, action_request, session)
            
            # Log the action
            await self.telemetry_manager.record_event(
                "agent_action_executed",
                {
                    "agent_id": agent_id,
                    "action": action_request.action.value,
                    "reason": action_request.reason,
                    "admin_id": action_request.admin_id,
                    "approval_id": action_request.approval_id,
                    "result": result["status"]
                }
            )
            
            return result

    async def _execute_action(
        self,
        agent: Agent,
        action_request: AgentActionRequest,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Internal method to execute specific actions."""
        
        if action_request.action == AgentAction.SUSPEND:
            agent.status = AgentStatus.SUSPENDED.value
            message = f"Agent {agent.name} suspended"
            
        elif action_request.action == AgentAction.FREEZE:
            agent.status = AgentStatus.FROZEN.value
            message = f"Agent {agent.name} frozen for investigation"
            
        elif action_request.action == AgentAction.RESUME:
            if agent.status in [AgentStatus.SUSPENDED.value, AgentStatus.FROZEN.value]:
                agent.status = AgentStatus.ACTIVE.value
                message = f"Agent {agent.name} resumed"
            else:
                return {
                    "status": "error",
                    "message": f"Cannot resume agent in status {agent.status}"
                }
        
        elif action_request.action == AgentAction.DECOMMISSION:
            await session.delete(agent)
            await session.commit()
            
            await self.telemetry_manager.record_event(
                "agent_decommissioned",
                {
                    "agent_id": str(agent.id),
                    "tenant_id": agent.tenant_id,
                    "reason": action_request.reason,
                    "admin_id": action_request.admin_id
                }
            )
            
            return {
                "status": "success",
                "message": f"Agent {agent.name} decommissioned",
                "agent_id": str(agent.id)
            }
        
        elif action_request.action == AgentAction.RESTART:
            agent.status = AgentStatus.ACTIVE.value
            agent.last_heartbeat = datetime.utcnow()
            message = f"Agent {agent.name} restarted"
        
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action_request.action}"
            }
        
        await session.commit()
        await session.refresh(agent)
        
        return {
            "status": "success",
            "message": message,
            "agent_id": str(agent.id),
            "new_status": agent.status
        }

    async def handle_security_violation(
        self,
        agent_id: str,
        violation_type: str,
        severity: AlertSeverity,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle security violations detected by surveillance system.
        
        Can automatically suspend agents based on severity if configured.
        """
        async with self.db_manager.get_session() as session:
            agent = await session.get(Agent, agent_id)
            
            if not agent:
                return {"status": "error", "message": "Agent not found"}
            
            # Reduce security score
            score_reduction = 30 if severity == AlertSeverity.CRITICAL else 15
            agent.security_score = max(0, agent.security_score - score_reduction)
            
            # Auto-suspend on critical violations if enabled
            auto_suspended = False
            if self.auto_suspend_on_security_violation and severity == AlertSeverity.CRITICAL:
                agent.status = AgentStatus.SUSPENDED.value
                auto_suspended = True
            
            await session.commit()
            
            # Create alert for admin
            await self.alert_manager.create_alert(
                category=AlertCategory.SECURITY,
                severity=severity,
                title=f"Security Violation: {violation_type}",
                description=f"Agent {agent.name} ({agent_id}) violated security policy. "
                           f"Auto-suspended: {auto_suspended}. Details: {details}",
                source="AgentLifecycleManager",
                metadata={
                    "agent_id": agent_id,
                    "tenant_id": agent.tenant_id,
                    "violation_type": violation_type,
                    "auto_suspended": auto_suspended,
                    "new_security_score": agent.security_score,
                    **details
                }
            )
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "auto_suspended": auto_suspended,
                "new_security_score": agent.security_score,
                "requires_admin_review": True
            }

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Retrieves an agent by its ID."""
        async with self.db_manager.get_session() as session:
            return await session.get(Agent, agent_id)

    async def list_agents(
        self, 
        tenant_id: str, 
        status: Optional[str] = None, 
        agent_type: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Agent]:
        """Lists agents for a given tenant with filtering and pagination."""
        async with self.db_manager.get_session() as session:
            query = select(Agent).where(Agent.tenant_id == tenant_id)
            
            if status:
                query = query.where(Agent.status == status)
            if agent_type:
                query = query.where(Agent.type == agent_type)
            
            result = await session.execute(query.offset(skip).limit(limit))
            return list(result.scalars().all())

    async def count_agents(
        self, 
        tenant_id: str, 
        status: Optional[str] = None, 
        agent_type: Optional[str] = None
    ) -> int:
        """Counts agents for a given tenant with optional filtering."""
        async with self.db_manager.get_session() as session:
            query = select(func.count(Agent.id)).where(Agent.tenant_id == tenant_id)
            
            if status:
                query = query.where(Agent.status == status)
            if agent_type:
                query = query.where(Agent.type == agent_type)
            
            return await session.scalar(query) or 0

    async def decommission_agent(
        self, 
        agent_id: str,
        admin_id: str,
        reason: str,
        approval_id: Optional[str] = None
    ) -> bool:
        """Decommissions an agent with proper authorization."""
        action_request = AgentActionRequest(
            action=AgentAction.DECOMMISSION,
            reason=reason,
            admin_id=admin_id,
            approval_id=approval_id
        )
        
        result = await self.execute_agent_action(agent_id, action_request)
        return result.get("status") == "success"

    async def monitor_agent_health(self) -> None:
        """Periodically monitors agent health and updates statuses."""
        async with self.db_manager.get_session() as session:
            timeout_seconds = getattr(settings.performance, 'agent_heartbeat_timeout_seconds', 300)
            stale_threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)
            
            result = await session.execute(
                select(Agent).where(
                    Agent.status == AgentStatus.ACTIVE.value,
                    Agent.last_heartbeat < stale_threshold
                )
            )
            stale_agents = result.scalars().all()

            for agent in stale_agents:
                logger.warning(f"Agent {agent.id} detected as stale. Marking as OFFLINE.")
                agent.status = AgentStatus.OFFLINE.value
                await session.commit()
                
                await self.telemetry_manager.record_event(
                    "agent_offline",
                    {
                        "agent_id": str(agent.id),
                        "tenant_id": agent.tenant_id,
                        "reason": "heartbeat_timeout"
                    }
                )
                
                await self.alert_manager.create_alert(
                    category=AlertCategory.SYSTEM,
                    severity=AlertSeverity.CRITICAL,
                    title="Agent Offline",
                    description=f"Agent {agent.id} ({agent.name}) has not sent a heartbeat for over {timeout_seconds} seconds and is now offline.",
                    source="AgentLifecycleManager",
                    metadata={
                        "agent_id": str(agent.id),
                        "tenant_id": agent.tenant_id,
                        "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                    }
                )

    async def start_health_monitoring_loop(self) -> None:
        """Starts a continuous loop for agent health monitoring."""
        check_interval = getattr(settings.performance, 'agent_health_check_interval_seconds', 60)
        
        while True:
            try:
                await self.monitor_agent_health()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                logger.info("Agent health monitoring loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in agent health monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(check_interval)

    async def health_check(self) -> str:
        """Perform a health check on the AgentLifecycleManager."""
        try:
            async with self.db_manager.get_session() as session:
                await session.execute(select(Agent).limit(1))
            return "healthy"
        except Exception as e:
            logger.error(f"AgentLifecycleManager health check failed: {e}", exc_info=True)
            return "unhealthy"
