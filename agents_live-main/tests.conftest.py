# tests/conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Generator

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main import app
from src.database import Base, get_db
from src.core.security import SecurityUtils
from src.models.user import UserRecord

# Test database setup
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_ymera"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create test tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop test tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    """Create a fresh database session for each test"""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    AsyncTestingSessionLocal = sessionmaker(
        class_=AsyncSession,
        expire_on_commit=False,
        bind=connection
    )
    
    session = AsyncTestingSessionLocal()
    
    yield session
    
    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest.fixture
def test_client(test_session):
    """Create test client with overridden database dependency"""
    
    def override_get_db():
        try:
            yield test_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(test_session):
    """Create a test user"""
    async def create_user():
        user = UserRecord(
            email="test@example.com",
            username="testuser",
            hashed_password=SecurityUtils.hash_password("testpassword123"),
            full_name="Test User",
            is_active=True,
            is_verified=True
        )
        test_session.add(user)
        await test_session.commit()
        return user
    return create_user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for tests"""
    async def create_headers(user=None):
        if user is None:
            user = await test_user()
        
        token = SecurityUtils.generate_jwt({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        })
        
        return {"Authorization": f"Bearer {token}"}
    return create_headers

# Mock fixtures for external services
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('src.core.cache.redis') as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        mock.incr = AsyncMock(return_value=1)
        yield mock

@pytest.fixture
def mock_kafka():
    """Mock Kafka producer"""
    with patch('src.core.events.kafka_producer') as mock:
        mock.send = AsyncMock(return_value=MagicMock())
        yield mock

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client"""
    with patch('src.core.search.elasticsearch') as mock:
        mock.search = AsyncMock(return_value={'hits': {'hits': [], 'total': {'value': 0}}})
        mock.index = AsyncMock(return_value={})
        yield mock