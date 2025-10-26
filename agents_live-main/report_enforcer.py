"""
Reporting Enforcer
Enforces mandatory reporting from all agents
"""

import structlog
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.models import AgentModel, AgentStatus

logger = structlog.get_logger(__name__)


class ReportingEnforcer:
    """Enforces agent reporting requirements"""
    
    def __init__(self, db_session: AsyncSession, agent_manager):
        self.db = db_session
        self.agent_manager = agent_manager
        self.reporting_interval = 60  # seconds
        self.max_missed_reports = 3
    
    async def check_reporting_compliance(self):
        """Check if all agents are reporting as required"""
        try:
            # Get all active agents
            stmt = select(AgentModel).where(
                AgentModel.status.in_([AgentStatus.ACTIVE, AgentStatus.BUSY])
            )
            result = await self.db.execute(stmt)
            agents = result.scalars().all()
            
            now = datetime.utcnow()
            
            for agent in agents:
                if not agent.last_report_at:
                    continue
                
                time_since_report = (now - agent.last_report_at).total_seconds()
                max_interval = self.reporting_interval * self.max_missed_reports
                
                if time_since_report > max_interval:
                    logger.warning(
                        "Agent missed reports",
                        agent_id=agent.agent_id,
                        time_since_report=time_since_report
                    )
                    await self._handle_missed_reports(agent.agent_id, time_since_report)
            
        except Exception as e:
            logger.error("Failed to check reporting compliance", error=str(e))
    
    async def _handle_missed_reports(self, agent_id: str, time_since_report: float):
        """Handle agent that has missed reports"""
        try:
            # Escalating consequences based on how long since last report
            if time_since_report > self.reporting_interval * 10:
                # Freeze agent after 10 missed reports
                await self.agent_manager.freeze_agent(
                    agent_id,
                    f"Failed to report for {int(time_since_report)}s",
                    "reporting_enforcer"
                )
            elif time_since_report > self.reporting_interval * 5:
                # Suspend after 5 missed reports
                await self.agent_manager.suspend_agent(
                    agent_id,
                    f"Failed to report for {int(time_since_report)}s",
                    "reporting_enforcer",
                    duration=3600
                )
            else:
                # Warning notification
                await self.agent_manager._notify_admin("AGENT_MISSED_REPORTS", {
                    "agent_id": agent_id,
                    "time_since_report": time_since_report,
                    "action": "warning"
                })
                
        except Exception as e:
            logger.error("Failed to handle missed reports", agent_id=agent_id, error=str(e))
