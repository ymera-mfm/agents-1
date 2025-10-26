"""Health Check Utilities"""

import asyncio
from datetime import datetime
from typing import Dict, Any
import structlog

from shared.database.connection_pool import DatabaseManager


class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = structlog.get_logger(__name__)
    
    async def check_all(self) -> Dict[str, Any]:
        """Check health of all components"""
        checks = {}
        
        # Database check
        checks['database'] = await self._check_database()
        
        # Overall status
        all_healthy = all(check['healthy'] for check in checks.values())
        
        return {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            is_healthy = await self.db_manager.health_check()
            return {
                'healthy': is_healthy,
                'message': 'Database is operational' if is_healthy else 'Database check failed'
            }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}", exc_info=True)
            return {
                'healthy': False,
                'message': str(e)
            }
