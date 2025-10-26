"""
Database Connection Pool Manager
Handles async PostgreSQL connections with pooling
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional
import structlog

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.orm import declarative_base

from shared.config.settings import Settings

logger = structlog.get_logger(__name__)

Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self._healthy = False
        self.logger = structlog.get_logger(__name__)
    
    async def initialize(self):
        """Initialize database engine and connection pool"""
        try:
            self.logger.info("Initializing database connection pool...")
            
            # Create async engine
            self.engine = create_async_engine(
                self.settings.DATABASE_URL,
                echo=self.settings.DB_ECHO,
                pool_size=self.settings.DB_POOL_SIZE,
                max_overflow=self.settings.DB_MAX_OVERFLOW,
                pool_timeout=self.settings.DB_POOL_TIMEOUT,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,  # Recycle connections after 1 hour
                poolclass=QueuePool if self.settings.DB_POOL_SIZE > 0 else NullPool
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            self._healthy = True
            self.logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}", exc_info=True)
            self._healthy = False
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get a database session"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            self.logger.info("Closing database connections...")
            await self.engine.dispose()
            self._healthy = False
            self.logger.info("Database connections closed")
    
    def is_healthy(self) -> bool:
        """Check if database is healthy"""
        return self._healthy and self.engine is not None
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            self.logger.error(f"Health check failed: {e}", exc_info=True)
            return False
