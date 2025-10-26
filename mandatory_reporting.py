# reporting/mandatory_reporting.py
"""
Mandatory Agent Reporting Enforcer
Implements escalating consequences for non-compliant agents
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from sqlalchemy import select, and_, or_, not_
from models import Agent, AgentStatus, AgentReportStatus, AuditLog, AgentAction

logger = logging.getLogger(__name__)

class MandatoryReportingEnforcer:
    """
    Enforces mandatory agent reporting with escalating consequences
    for non-compliant agents.
    """
    
    def __init__(self, manager):
        """Initialize with reference to the manager"""
        self.manager = manager
        
        # Get configuration
        config = manager.config.get("reporting", {})
        self.reporting_interval = timedelta(minutes=config.get("interval_minutes", 5))
        self.warning_threshold = config.get("warning_threshold", 3)
        self.suspend_threshold = config.get("suspend_threshold", 5)
        self.non_compliant_threshold = config.get("non_compliant_threshold", 10)
        
        logger.info(f"MandatoryReportingEnforcer initialized with thresholds: "
                  f"warning={self.warning_threshold}, suspend={self.suspend_threshold}, "
                  f"non_compliant={self.non_compliant_threshold}")
    
    async def start_monitoring(self):
        """Start background monitoring of agent reports"""
        logger.info("Starting mandatory reporting monitoring")
        
        while self.manager.running:
            try:
                await self._check_all_agents()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Reporting monitoring error: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error
    
    async def _check_all_agents(self):
        """Check reporting compliance for all agents"""
        now = datetime.utcnow()
        
        async with self.manager.get_db_session() as session:
            # Get active agents that are not exempt from reporting
            result = await session.execute(
                select(Agent).where(
                    and_(
                        Agent.status != AgentStatus.DELETED.value,
                        Agent.reporting_exemption == False
                    )
                )
            )
            
            agents = result.scalars().all()
            
            for agent in agents:
                # Skip if agent reported recently
                if agent.last_heartbeat and now - agent.last_heartbeat < self.reporting_interval:
                    continue
                
                # Calculate new missed count
                new_missed_count = agent.missed_report_count + 1
                
                # Apply escalating consequences
                await self._enforce_reporting_compliance(agent.id, new_missed_count, agent.reporting_status)
                
                # Update missed count in database
                agent.missed_report_count = new_missed_count
                
            await session.commit()
    
    async def _enforce_reporting_compliance(self, agent_id: str, missed_count: int, current_status: str):
        """Apply escalating consequences based on missed report count"""
        
        # Agent missed too many reports - mark non-compliant and initiate admin review
        if missed_count >= self.non_compliant_threshold and current_status != AgentReportStatus.NON_COMPLIANT.value:
            await self._handle_non_compliant_agent(agent_id, missed_count)
            
        # Agent missed enough reports for suspension
        elif missed_count >= self.suspend_threshold and current_status != AgentReportStatus.SUSPENDED.value:
            await self._suspend_agent(agent_id, missed_count)
            
        # Agent missed enough reports for warning
        elif missed_count >= self.warning_threshold and current_status != AgentReportStatus.WARNED.value:
            await self._warn_agent(agent_id, missed_count)
    
    async def _warn_agent(self, agent_id: str, missed_count: int):
        """Send warning to agent about missed reports"""
        logger.warning(f"Agent {agent_id} has missed {missed_count} reports - sending warning")
        
        # Update agent reporting status
        async with self.manager.get_db_session() as session:
            agent = await session.get(Agent, agent_id)
            if not agent:
                return
                
            agent.reporting_status = AgentReportStatus.WARNED.value
            agent.last_warning_at = datetime.utcnow()
            
            # Create audit log
            audit_log = AuditLog(
                event_type="reporting_warning",
                resource_type="agent",
                resource_id=agent_id,
                action="warn",
                performed_by="system",
                details={"missed_count": missed_count}
            )
            session.add(audit_log)
            
            await session.commit()
        
        # Send warning message to agent if connected
        if agent_id in self.manager.active_connections:
            for ws in self.manager.active_connections[agent_id]:
                try:
                    await ws.send_json({
                        "type": "warning",
                        "reason": "missed_reports",
                        "count": missed_count,
                        "timestamp": datetime.utcnow().isoformat(),
                        "action_required": "resume_reporting"
                    })
                except Exception as e:
                    logger.error(f"Failed to send warning to agent {agent_id}: {e}")
        
        # Update metrics
        self.manager.REPORTING_STATUS.labels(status=AgentReportStatus.COMPLIANT.value).dec()
        self.manager.REPORTING_STATUS.labels(status=AgentReportStatus.WARNED.value).inc()
    
    async def _suspend_agent(self, agent_id: str, missed_count: int):
        """Temporarily suspend non-reporting agent"""
        logger.warning(f"Agent {agent_id} has missed {missed_count} reports - suspending")
        
        # Update agent status
        async with self.manager.get_db_session() as session:
            agent = await session.get(Agent, agent_id)
            if not agent:
                return
                
            agent.reporting_status = AgentReportStatus.SUSPENDED.value
            agent.status = AgentStatus.SUSPENDED.value
            agent.suspended_at = datetime.utcnow()
            agent.suspended_by = "system"
            agent.suspended_reason = f"Missed {missed_count} required reports"
            
            # Create audit log
            audit_log = AuditLog(
                event_type="agent_suspended",
                resource_type="agent",
                resource_id=agent_id,
                action="suspend",
                performed_by="system",
                details={
                    "reason": "missed_reports",
                    "missed_count": missed_count
                }
            )
            session.add(audit_log)
            
            await session.commit()
        
        # Send suspension message to agent if connected
        if agent_id in self.manager.active_connections:
            for ws in self.manager.active_connections[agent_id]:
                try:
                    await ws.send_json({
                        "type": "control",
                        "action": "suspend",
                        "reason": "missed_reports",
                        "count": missed_count,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Failed to notify agent {agent_id} of suspension: {e}")
        
        # Send notification to admins
        await self.manager.notification_manager.send_notification(
            "admin",
            {
                "type": "agent_suspended",
                "title": f"Agent {agent_id} automatically suspended",
                "message": f"Agent automatically suspended after missing {missed_count} required reports",
                "severity": "high",
                "action_required": True
            }
        )
        
        # Update metrics
        self.manager.AGENT_COUNT.labels(status=AgentStatus.ACTIVE.value).dec()
        self.manager.AGENT_COUNT.labels(status=AgentStatus.SUSPENDED.value).inc()
        self.manager.REPORTING_STATUS.labels(status=AgentReportStatus.WARNED.value).dec()
        self.manager.REPORTING_STATUS.labels(status=AgentReportStatus.SUSPENDED.value).inc()
    
    async def _handle_non_compliant_agent(self, agent_id: str, missed_count: int):
        """Handle severely non-compliant agent - request admin action for deletion"""
        logger.error(f"Agent {agent_id} is non-compliant with {missed_count} missed reports")
        
        # Update agent status
        async with self.manager.get_db_session() as session:
            agent = await session.get(Agent, agent_id)
            if not agent:
                return
                
            agent.reporting_status = AgentReportStatus.NON_COMPLIANT.value
            
            # Create security event
            from models import SecurityEvent
            security_event = SecurityEvent(
                event_type="reporting_violation",
                severity="high",
                source="mandatory_reporting",
                description=f"Agent severely violated reporting requirements",
                agent_id=agent_id,
                details={
                    "missed_count": missed_count
                }
            )
            session.add(security_event)
            
            await session.commit()
        
        # Create admin approval request for agent deletion
        result = await self.manager.request_agent_action(
            agent_id=agent_id,
            action=AgentAction.DELETE.value,
            reason=f"Non-compliant with reporting requirements. Missed {missed_count} reports.",
            requested_by="system"
        )
        
        # Update metrics
        self.manager.SECURITY_EVENTS.labels(
            event_type="reporting_violation",
            severity="high"
        ).inc()
        self.manager.REPORTING_STATUS.labels(status=AgentReportStatus.SUSPENDED.value).dec()
        self.manager.REPORTING_STATUS.labels(status=AgentReportStatus.NON_COMPLIANT.value).inc()
    
    async def process_agent_report(self, agent_id: str, report: Dict[str, Any]):
        """Process incoming agent report"""
        # Reset reporting status if agent was previously warned or suspended
        async with self.manager.get_db_session() as session:
            agent = await session.get(Agent, agent_id)
            if not agent:
                return
                
            old_status = agent.reporting_status
                
            if old_status in [
                AgentReportStatus.WARNED.value,
                AgentReportStatus.SUSPENDED.value,
                AgentReportStatus.NON_COMPLIANT.value
            ]:
                # Reset missed report count
                agent.reporting_status = AgentReportStatus.COMPLIANT.value
                agent.missed_report_count = 0
                
                # If agent was suspended, request unsuspend
                if agent.status == AgentStatus.SUSPENDED.value:
                    await self._request_unsuspend_agent(agent_id)
                    
                # Update metrics
                self.manager.REPORTING_STATUS.labels(status=old_status).dec()
                self.manager.REPORTING_STATUS.labels(status=AgentReportStatus.COMPLIANT.value).inc()
                
            await session.commit()
    
    async def _request_unsuspend_agent(self, agent_id: str):
        """Request admin approval to unsuspend agent"""
        # Request action through the lifecycle manager
        await self.manager.request_agent_action(
            agent_id=agent_id,
            action=AgentAction.UNFREEZE.value,
            reason="Agent has resumed reporting",
            requested_by="system"
        )