# tests/e2e/test_user_journeys.py
import pytest
from fastapi import status
from datetime import datetime, timedelta

class TestUserRegistrationJourney:
    """End-to-end test for user registration journey"""
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self, test_client):
        """Test complete user journey from registration to project creation"""
        # 1. Register new user
        register_response = test_client.post("/auth/register", json={
            "email": "journey@example.com",
            "username": "journeyuser",
            "password": "SecurePass123!",
            "full_name": "Journey User"
        })
        
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["id"]
        
        # 2. Login with new user
        login_response = test_client.post("/auth/login", json={
            "username": "journeyuser",
            "password": "SecurePass123!"
        })
        
        assert login_response.status_code == status.HTTP_200_OK
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Create a project
        project_response = test_client.post("/projects", json={
            "name": "Journey Project",
            "description": "Project created during user journey test",
            "status": "planning"
        }, headers=headers)
        
        assert project_response.status_code == status.HTTP_201_CREATED
        project_id = project_response.json()["id"]
        
        # 4. Create tasks for the project
        tasks_data = [
            {"name": "Research", "priority": "high"},
            {"name": "Design", "priority": "medium"},
            {"name": "Implementation", "priority": "high"}
        ]
        
        for task_data in tasks_data:
            task_response = test_client.post("/tasks", json={
                **task_data,
                "project_id": project_id
            }, headers=headers)
            
            assert task_response.status_code == status.HTTP_201_CREATED
        
        # 5. Get project with tasks
        project_details = test_client.get(f"/projects/{project_id}", headers=headers)
        assert project_details.status_code == status.HTTP_200_OK
        assert project_details.json()["name"] == "Journey Project"
        
        # 6. Get project statistics
        stats_response = test_client.get(f"/projects/{project_id}/stats", headers=headers)
        assert stats_response.status_code == status.HTTP_200_OK
        assert stats_response.json()["total_tasks"] == 3
        assert stats_response.json()["completed_tasks"] == 0
        
        # 7. Complete a task
        tasks_list = test_client.get("/tasks", headers=headers, params={"project_id": project_id})
        task_id = tasks_list.json()["items"][0]["id"]
        
        complete_response = test_client.post(f"/tasks/{task_id}/complete", headers=headers)
        assert complete_response.status_code == status.HTTP_200_OK
        
        # 8. Verify updated statistics
        updated_stats = test_client.get(f"/projects/{project_id}/stats", headers=headers)
        assert updated_stats.json()["completed_tasks"] == 1
        assert updated_stats.json()["completion_rate"] == 1/3

class TestPerformanceJourney:
    """End-to-end performance testing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self, test_client):
        """Test concurrent user operations for performance"""
        import asyncio
        
        # Create multiple users and projects concurrently
        async def create_user_and_project(user_index):
            # Register user
            register_response = test_client.post("/auth/register", json={
                "email": f"user{user_index}@example.com",
                "username": f"testuser{user_index}",
                "password": "Password123!",
                "full_name": f"Test User {user_index}"
            })
            
            if register_response.status_code != 201:
                return None
            
            # Login
            login_response = test_client.post("/auth/login", json={
                "username": f"testuser{user_index}",
                "password": "Password123!"
            })
            
            if login_response.status_code != 200:
                return None
            
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Create project
            project_response = test_client.post("/projects", json={
                "name": f"Project {user_index}",
                "status": "active"
            }, headers=headers)
            
            return project_response.status_code
        
        # Run concurrent operations
        tasks = [create_user_and_project(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify most operations succeeded
        success_count = sum(1 for result in results if result == 201)
        assert success_count >= 8  # Allow for some failures in load test