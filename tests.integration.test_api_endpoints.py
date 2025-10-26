# tests/integration/test_api_endpoints.py
import pytest
from fastapi import status
from src.models.user import UserRecord
from src.models.project import ProjectRecord

class TestAuthEndpoints:
    """Integration tests for authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_client, test_user):
        """Test successful login"""
        user = await test_user()
        
        response = test_client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, test_client, test_user):
        """Test login with invalid credentials"""
        await test_user()
        
        response = test_client.post("/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, test_client, test_user, auth_headers):
        """Test token refresh"""
        user = await test_user()
        headers = await auth_headers(user)
        
        # First get a refresh token
        login_response = test_client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        response = test_client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

class TestProjectEndpoints:
    """Integration tests for project endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_project(self, test_client, test_user, auth_headers):
        """Test creating a project via API"""
        user = await test_user()
        headers = await auth_headers(user)
        
        project_data = {
            "name": "API Test Project",
            "description": "Project created via API test",
            "status": "draft"
        }
        
        response = test_client.post("/projects", json=project_data, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == "API Test Project"
        assert response.json()["owner_id"] == str(user.id)
    
    @pytest.mark.asyncio
    async def test_get_projects(self, test_client, test_user, auth_headers):
        """Test getting projects list"""
        user = await test_user()
        headers = await auth_headers(user)
        
        # Create some test projects
        for i in range(3):
            project = ProjectRecord(
                name=f"Test Project {i}",
                owner_id=user.id,
                status="active"
            )
            test_client.app.state.db.add(project)
        await test_client.app.state.db.commit()
        
        response = test_client.get("/projects", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["items"]) == 3
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self, test_client, test_user, auth_headers):
        """Test getting non-existent project"""
        user = await test_user()
        headers = await auth_headers(user)
        
        response = test_client.get("/projects/99999999-9999-9999-9999-999999999999", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

class TestTaskEndpoints:
    """Integration tests for task endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_task(self, test_client, test_user, auth_headers):
        """Test creating a task via API"""
        user = await test_user()
        headers = await auth_headers(user)
        
        # First create a project
        project_response = test_client.post("/projects", json={
            "name": "Task Test Project",
            "status": "active"
        }, headers=headers)
        project_id = project_response.json()["id"]
        
        task_data = {
            "name": "API Test Task",
            "project_id": project_id,
            "priority": "high"
        }
        
        response = test_client.post("/tasks", json=task_data, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == "API Test Task"
        assert response.json()["project_id"] == project_id