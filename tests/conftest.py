"""
Test configuration
"""
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "test_mode": True,
        "timeout": 10,
        "max_retries": 3
    }
