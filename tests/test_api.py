
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import os
from datetime import datetime
import httpx
from pytest_asyncio import fixture as pytest_asyncio_fixture

# Mock environment variables for testing
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:password@localhost:5432/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["JWT_SECRET_KEY"] = "supersecretkeythatisatleast32characterslong"
os.environ["MANAGER_AGENT_URL"] = "http://mock-manager-agent:8001"

# Import app and lifespan after setting environment variables
from main import app, lifespan

@pytest_asyncio_fixture(scope="module")
async def client():
    # Create mock instances for services that are initialized within lifespan
    mock_db_client_instance = MagicMock()
    mock_db_client_instance.initialize = AsyncMock(return_value=None)
    mock_db_client_instance.close = AsyncMock(return_value=None)
    mock_db_client_instance.execute_query = AsyncMock(return_value=[])
    mock_db_client_instance.execute_single = AsyncMock(return_value=None)
    mock_db_client_instance.execute_command = AsyncMock(return_value="COMMAND_OK")
    mock_db_client_instance.health_check = AsyncMock(return_value=True)

    mock_auth_service_instance = MagicMock()
    mock_auth_service_instance.get_password_hash = MagicMock()
    mock_auth_service_instance.verify_password = MagicMock()
    mock_auth_service_instance.create_access_token = MagicMock()
    mock_auth_service_instance.decode_access_token = MagicMock()

    mock_task_queue_instance = MagicMock()
    mock_manager_client_instance = MagicMock()
    mock_manager_client_instance.shutdown = AsyncMock()
    mock_manager_client_instance.manager_url = os.environ["MANAGER_AGENT_URL"]
    mock_manager_client_instance.client = httpx.AsyncClient()
    mock_manager_client_instance.send_heartbeat = AsyncMock(return_value=True)
    mock_manager_client_instance.register_agent = AsyncMock(return_value="registered_agent_id")

    mock_agent_manager_instance = MagicMock()

    # Patch the classes that are instantiated inside the lifespan function
    with (
        patch("main.Database", return_value=mock_db_client_instance),
        patch("main.AuthService", return_value=mock_auth_service_instance),
        patch("main.TaskQueue", return_value=mock_task_queue_instance),
        patch("main.ManagerClient", return_value=mock_manager_client_instance),
        patch("main.AgentManager", return_value=mock_agent_manager_instance),
        patch("main.aioredis.from_url") as mock_redis_from_url,
        patch("asyncio.create_task", new_callable=AsyncMock) as mock_create_task,
        patch("main.process_tasks", new_callable=AsyncMock) as mock_process_tasks
    ):
        # Configure mocks for Redis
        mock_redis_client = MagicMock()
        mock_redis_client.close = AsyncMock()
        mock_redis_from_url.return_value = mock_redis_client

        # Use the lifespan context manager to initialize the app and its services
        async with lifespan(app):
            # Capture the task created by asyncio.create_task
            task = mock_create_task.return_value = AsyncMock()

            yield TestClient(app), mock_db_client_instance, mock_auth_service_instance, mock_manager_client_instance

            # Ensure the task is cancelled during teardown
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

@pytest.mark.asyncio
async def test_health_endpoint(client):
    test_client, mock_db_client, _, _ = client
    # Verify that the mocked initi    # The db_client is already mocked and passed as part of the client fixture
    mock_db_client.initialize.assert_called_once()

    # Make a simple request to ensure the app is responsive
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "timestamp" in response.json()
    assert response.json()["version"] == "1.0.0"

@pytest.mark.asyncio
async def test_register_user(client):
    test_client, mock_db_client, mock_auth_service, _ = client
    mock_db_client.execute_single.reset_mock()
    mock_auth_service.get_password_hash.reset_mock()
    mock_auth_service.create_access_token.reset_mock()
    # Mock db_client.execute_single to return no existing user
    mock_db_client.execute_single.return_value = None
    mock_auth_service.get_password_hash.return_value = "hashed_password"
    mock_auth_service.create_access_token.return_value = "mock_access_token"

    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword",
        "first_name": "Test",
        "last_name": "User"
    }
    response = test_client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    assert response.json()["access_token"] == "mock_access_token"
    assert "user_id" in response.json()
    mock_db_client.execute_command.assert_called_once()

@pytest.mark.asyncio
async def test_register_user_existing_email(client):
    test_client, mock_db_client, _, _ = client
    mock_db_client.execute_single.reset_mock()
    mock_db_client.execute_command.reset_mock()
    mock_auth_service.get_password_hash.reset_mock()
    mock_auth_service.create_access_token.reset_mock()
    mock_db_client.execute_single.return_value = {"id": "existing_user_id"}

    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword",
        "first_name": "Test",
        "last_name": "User"
    }
    response = test_client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_user_success(client):
    test_client, mock_db_client, mock_auth_service, _ = client
    mock_db_client.execute_single.reset_mock()
    mock_auth_service.verify_password.reset_mock()
    mock_auth_service.create_access_token.reset_mock()
    mock_db_client.execute_single.return_value = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": "hashed_password",
        "role": "user"
    }
    mock_auth_service.verify_password.return_value = True
    mock_auth_service.create_access_token.return_value = "mock_access_token"

    form_data = {"username": "testuser", "password": "securepassword"}
    response = test_client.post("/auth/login", data=form_data)
    assert response.status_code == 200
    assert response.json()["access_token"] == "mock_access_token"
    assert response.json()["user_id"] == "user123"

@pytest.mark.asyncio
async def test_login_user_invalid_credentials(client):
    test_client, mock_db_client, mock_auth_service, _ = client
    mock_db_client.execute_single.reset_mock()
    mock_auth_service.verify_password.reset_mock()
    mock_auth_service.create_access_token.reset_mock()
    mock_db_client.execute_single.return_value = None
    mock_auth_service.verify_password.return_value = False

    form_data = {"username": "wronguser", "password": "wrongpassword"}
    response = test_client.post("/auth/login", data=form_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"



@pytest.mark.asyncio
async def test_get_current_user_info(client):
    test_client, mock_db_client, mock_auth_service, _ = client
    mock_db_client.execute_single.reset_mock()
    mock_auth_service.verify_password.reset_mock()
    mock_auth_service.create_access_token.reset_mock()
    mock_auth_service.decode_access_token.reset_mock()
    mock_auth_service.decode_access_token.return_value = {"id": "user123"}
    mock_db_client.execute_single.return_value = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "created_at": datetime.now()
    }

    headers = {"Authorization": "Bearer mock_token"}
    response = test_client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert response.json()["email"] == "test@example.com"



@pytest.mark.asyncio
async def test_create_agent(client):
    test_client, mock_db_client, mock_auth_service, mock_manager_client = client
    mock_auth_service.decode_access_token.return_value = {"id": "user123"}
    mock_db_client.execute_single.reset_mock()
    mock_db_client.execute_single.return_value = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "created_at": datetime.now()
    }
    mock_db_client.execute_command.reset_mock()
    mock_manager_client.register_agent.reset_mock()
    mock_manager_client.register_agent.return_value = "new_agent_id"

    agent_data = {
        "name": "My Test Agent",
        "description": "A test agent for development",
        "capabilities": ["data_analysis", "web_browsing"],
        "config": {"model": "gpt-4"}
    }
    headers = {"Authorization": "Bearer mock_token"}
    response = test_client.post("/agents", json=agent_data, headers=headers)

    assert response.status_code == 201
    assert response.json()["agent_id"] == "new_agent_id"
    mock_db_client.execute_command.assert_called_once()
    mock_manager_client.register_agent.assert_called_once()

@pytest.mark.asyncio
async def test_list_agents(client):
    test_client, mock_db_client, mock_auth_service, _ = client
    mock_auth_service.decode_access_token.return_value = {"id": "user123"}
    mock_db_client.execute_single.reset_mock()
    mock_db_client.execute_single.return_value = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "created_at": datetime.now()
    }
    mock_db_client.execute_query.reset_mock()
    mock_db_client.execute_query.return_value = [
        {"id": "agent1", "name": "Agent One", "owner_id": "user123", "capabilities": "[]", "config": "{}", "status": "ACTIVE", "last_heartbeat": datetime.now()},
        {"id": "agent2", "name": "Agent Two", "owner_id": "user123", "capabilities": "[]", "config": "{}", "status": "INACTIVE", "last_heartbeat": datetime.now()}
    ]

    headers = {"Authorization": "Bearer mock_token"}
    response = test_client.get("/agents", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Agent One"
    mock_db_client.execute_query.assert_called_once()

@pytest.mark.asyncio
async def test_get_agent_by_id(client):
    test_client, mock_db_client, mock_auth_service, _ = client
    mock_auth_service.decode_access_token.return_value = {"id": "user123"}
    mock_db_client.execute_single.reset_mock()
    mock_db_client.execute_single.return_value = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "created_at": datetime.now()
    }
    mock_db_client.execute_query.reset_mock()
    mock_db_client.execute_query.return_value = [
        {"id": "agent1", "name": "Agent One", "owner_id": "user123", "capabilities": "[]", "config": "{}", "status": "ACTIVE", "last_heartbeat": datetime.now()}
    ]

    headers = {"Authorization": "Bearer mock_token"}
    response = test_client.get("/agents/agent1", headers=headers)

    assert response.status_code == 200
    assert response.json()["name"] == "Agent One"
    mock_db_client.execute_query.assert_called_once()

@pytest.mark.asyncio
async def test_agent_heartbeat(client):
    test_client, mock_db_client, mock_auth_service, mock_manager_client = client
    mock_auth_service.decode_access_token.return_value = {"id": "user123"}
    mock_db_client.execute_single.reset_mock()
    mock_db_client.execute_single.return_value = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "created_at": datetime.now()
    }
    mock_db_client.execute_command.reset_mock()
    mock_manager_client.send_heartbeat.reset_mock()
    mock_manager_client.send_heartbeat.return_value = True

    headers = {"Authorization": "Bearer mock_token"}
    response = test_client.post("/agents/agent1/heartbeat", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Heartbeat received"
    mock_db_client.execute_command.assert_called_once()
    mock_manager_client.send_heartbeat.assert_called_once()

