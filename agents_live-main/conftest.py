"""Test configuration and fixtures"""

import sys
import os
# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient

from main import app
from core.config import Settings
from core.database import Database


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings"""
    import os
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["DEBUG"] = "True"
    os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_purposes_only_32_chars_min"
    return Settings()


@pytest.fixture
async def db_manager(test_settings):
    """Database manager for tests"""
    manager = Database(test_settings.database_url)
    await manager.initialize()
    yield manager
    # Database close if needed


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API tests"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_code():
    """Sample code for testing"""
    return '''
def hello_world():
    """Return hello world message"""
    try:
        return "Hello, World!"
    except Exception as e:
        print(f"Error: {e}")
        return None
'''


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        "module_name": "test_module",
        "test_coverage": 85,
        "complexity": 5,
        "language": "python"
    }
