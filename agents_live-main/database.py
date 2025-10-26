import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
import asyncpg
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url.replace("+asyncpg", ""),
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'ymera_agent'
                }
            )
            logger.info("Database pool initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_query(self, query: str, *args) -> List[Dict]:
        """Execute query and return results"""
        async with self.get_connection() as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
                raise
    
    async def execute_single(self, query: str, *args) -> Optional[Dict]:
        """Execute query and return single result"""
        results = await self.execute_query(query, *args)
        return results[0] if results else None
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute command (INSERT, UPDATE, DELETE)"""
        async with self.get_connection() as conn:
            try:
                result = await conn.execute(command, *args)
                return result
            except Exception as e:
                logger.error(f"Command execution failed: {command[:100]}... Error: {e}")
                raise
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            await self.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed")

