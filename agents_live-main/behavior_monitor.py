"""
Agent Behavior Monitor
Monitors agent behavior patterns and detects anomalies
"""

import structlog
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.cache_manager import CacheManager

logger = structlog.get_logger(__name__)


class AgentBehaviorMonitor:
    """Monitors and analyzes agent behavior"""
    
    def __init__(self, db_session: AsyncSession, cache_manager: CacheManager):
        self.db = db_session
        self.cache = cache_manager
        self.behavior_patterns = {}
    
    async def analyze_agent(self, agent_id: str) -> Dict[str, Any]:
        """Analyze agent behavior for anomalies"""
        try:
            # Get behavior history from cache
            history_key = f"agent:behavior:{agent_id}"
            history = await self.cache.get(history_key) or []
            
            # Analyze patterns
            anomalies = self._detect_anomalies(history)
            
            return {
                "agent_id": agent_id,
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Behavior analysis failed", agent_id=agent_id, error=str(e))
            return {"agent_id": agent_id, "error": str(e)}
    
    def _detect_anomalies(self, history: List[Dict]) -> List[Dict]:
        """Detect behavioral anomalies"""
        anomalies = []
        
        # Simple anomaly detection - can be enhanced with ML
        if len(history) > 10:
            recent = history[-10:]
            error_rate = sum(1 for h in recent if h.get('has_errors', False)) / len(recent)
            
            if error_rate > 0.5:
                anomalies.append({
                    "type": "high_error_rate",
                    "severity": "high",
                    "description": f"Error rate of {error_rate:.1%} detected"
                })
        
        return anomalies
    
    async def record_behavior(self, agent_id: str, behavior_data: Dict[str, Any]):
        """Record agent behavior for analysis"""
        try:
            history_key = f"agent:behavior:{agent_id}"
            history = await self.cache.get(history_key) or []
            
            behavior_data['timestamp'] = datetime.utcnow().isoformat()
            history.append(behavior_data)
            
            # Keep last 100 records
            if len(history) > 100:
                history = history[-100:]
            
            await self.cache.set(history_key, history, ttl=86400)
            
        except Exception as e:
            logger.error("Failed to record behavior", agent_id=agent_id, error=str(e))
