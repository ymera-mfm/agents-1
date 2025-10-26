"""
Agent Lifecycle Manager
Handles agent activation, deactivation, and state transitions
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import AgentModel, AgentStatus

logger = structlog.get_logger(__name__)


class AgentLifecycleManager:
    """Manages agent lifecycle operations"""
    
    def __init__(self, db_session: AsyncSession, agent_manager):
        self.db = db_session
        self.agent_manager = agent_manager
    
    async def activate_agent(self, agent_id: str) -> Dict[str, Any]:
        """Activate an agent"""
        try:
            logger.info("Activating agent", agent_id=agent_id)
            
            stmt = select(AgentModel).where(AgentModel.agent_id == agent_id)
            result = await self.db.execute(stmt)
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            if agent.status == AgentStatus.ACTIVE:
                return {"status": "already_active", "agent_id": agent_id}
            
            # Perform activation checks
            if agent.status == AgentStatus.FROZEN:
                raise PermissionError("Cannot activate frozen agent - requires admin intervention")
            
            if agent.status == AgentStatus.DELETED:
                raise PermissionError("Cannot activate deleted agent")
            
            # Activate agent
            agent.status = AgentStatus.ACTIVE
            agent.activated_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info("Agent activated successfully", agent_id=agent_id)
            
            return {
                "status": "activated",
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to activate agent", agent_id=agent_id, error=str(e))
            raise
    
    async def deactivate_agent(
        self,
        agent_id: str,
        reason: str,
        deactivated_by: str
    ) -> Dict[str, Any]:
        """Deactivate an agent"""
        try:
            logger.info("Deactivating agent", agent_id=agent_id)
            
            stmt = select(AgentModel).where(AgentModel.agent_id == agent_id)
            result = await self.db.execute(stmt)
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent.status = AgentStatus.INACTIVE
            agent.deactivated_at = datetime.utcnow()
            agent.deactivated_by = deactivated_by
            agent.deactivation_reason = reason
            await self.db.commit()
            
            logger.info("Agent deactivated", agent_id=agent_id)
            
            return {
                "status": "deactivated",
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to deactivate agent", agent_id=agent_id, error=str(e))
            raise
    
    async def transition_state(
        self,
        agent_id: str,
        from_status: AgentStatus,
        to_status: AgentStatus,
        reason: str = None
    ) -> Dict[str, Any]:
        """Transition agent from one state to another"""
        try:
            stmt = select(AgentModel).where(AgentModel.agent_id == agent_id)
            result = await self.db.execute(stmt)
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            if agent.status != from_status:
                raise ValueError(
                    f"Agent is in {agent.status} state, expected {from_status}"
                )
            
            agent.status = to_status
            await self.db.commit()
            
            logger.info(
                "Agent state transitioned",
                agent_id=agent_id,
                from_status=from_status,
                to_status=to_status
            )
            
            return {
                "status": "transitioned",
                "agent_id": agent_id,
                "from_status": from_status,
                "to_status": to_status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("State transition failed", agent_id=agent_id, error=str(e))
            raise
