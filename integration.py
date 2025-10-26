"""
Database Integration Layer
Integrates YMERA_DATABASE_SYSTEM_V5 with unified_agent_system
"""

import sys
import os
from pathlib import Path

# Add database system to path
db_system_path = Path(__file__).parent.parent / "YMERA_DATABASE_SYSTEM_V5"
if db_system_path.exists():
    sys.path.insert(0, str(db_system_path))

# Import database core
try:
    from database_core_integrated import (
        DatabaseConfig,
        DatabaseManager,
        Base,
        # Add other imports as needed
    )
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Database system not found: {e}")
    DATABASE_AVAILABLE = False
    DatabaseManager = None
    DatabaseConfig = None


class UnifiedDatabaseManager:
    """
    Unified Database Manager integrating YMERA Database with Agent System
    """
    
    def __init__(self, config=None):
        if not DATABASE_AVAILABLE:
            raise RuntimeError("Database system not available. Check YMERA_DATABASE_SYSTEM_V5 location.")
        
        self.config = config or DatabaseConfig()
        self.db_manager = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize database manager"""
        if DATABASE_AVAILABLE and DatabaseManager:
            self.db_manager = DatabaseManager(self.config)
            await self.db_manager.initialize()
            self.is_initialized = True
            print("✅ Database initialized successfully")
        else:
            print("⚠️  Database not available, running without persistence")
    
    async def close(self):
        """Close database connections"""
        if self.db_manager:
            await self.db_manager.close()
            print("✅ Database closed successfully")
    
    async def get_session(self):
        """Get database session"""
        if self.db_manager:
            return await self.db_manager.get_session()
        return None
    
    async def health_check(self):
        """Check database health"""
        if self.db_manager:
            return await self.db_manager.health_check()
        return {"status": "unavailable", "message": "Database not configured"}


__all__ = [
    'UnifiedDatabaseManager',
    'DATABASE_AVAILABLE',
    'DatabaseConfig',
]
