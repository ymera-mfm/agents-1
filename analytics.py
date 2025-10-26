"""
Reporting Analytics
Analyzes agent reports for insights and trends
"""

import structlog
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.cache_manager import CacheManager
from ..core.models import AgentReportModel

logger = structlog.get_logger(__name__)


class ReportingAnalytics:
    """Analyzes agent reporting data"""
    
    def __init__(self, db_session: AsyncSession, cache_manager: CacheManager):
        self.db = db_session
        self.cache = cache_manager
    
    async def get_agent_report_stats(
        self,
        agent_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get reporting statistics for an agent"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            stmt = select(func.count(AgentReportModel.report_id)).where(
                AgentReportModel.agent_id == agent_id,
                AgentReportModel.timestamp >= cutoff
            )
            result = await self.db.execute(stmt)
            report_count = result.scalar() or 0
            
            expected_reports = (days * 24 * 60 * 60) // 60  # Assuming 60s interval
            compliance_rate = (report_count / expected_reports * 100) if expected_reports > 0 else 0
            
            return {
                "agent_id": agent_id,
                "period_days": days,
                "total_reports": report_count,
                "expected_reports": expected_reports,
                "compliance_rate": round(compliance_rate, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get report stats", agent_id=agent_id, error=str(e))
            return {}
