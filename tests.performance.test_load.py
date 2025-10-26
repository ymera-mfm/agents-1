# tests/performance/test_load.py
import pytest
import asyncio
from locust import HttpUser, task, between
import json

class YmeraLoadTest(HttpUser):
    """Load testing for Ymera API"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get auth token"""
        response = self.client.post("/auth/login", json={
            "username": "loadtestuser",
            "password": "loadtestpass"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Create test user if it doesn't exist
            self.client.post("/auth/register", json={
                "email": "loadtest@example.com",
                "username": "loadtestuser",
                "password": "loadtestpass",
                "full_name": "Load Test User"
            })
            response = self.client.post("/auth/login", json={
                "username": "loadtestuser",
                "password": "loadtestpass"
            })
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def test_get_projects(self):
        """Test getting projects list"""
        self.client.get("/projects", headers=self.headers)
    
    @task(2)
    def test_create_project(self):
        """Test creating a project"""
        project_data = {
            "name": f"Load Test Project {self._get_timestamp()}",
            "description": "Project created during load test",
            "status": "active"
        }
        self.client.post("/projects", json=project_data, headers=self.headers)
    
    @task(5)
    def test_get_tasks(self):
        """Test getting tasks"""
        self.client.get("/tasks", headers=self.headers)
    
    @task(1)
    def test_create_task(self):
        """Test creating a task"""
        # First get or create a project
        projects = self.client.get("/projects", headers=self.headers)
        if projects.json()["items"]:
            project_id = projects.json()["items"][0]["id"]
            task_data = {
                "name": f"Load Test Task {self._get_timestamp()}",
                "project_id": project_id,
                "priority": "medium"
            }
            self.client.post("/tasks", json=task_data, headers=self.headers)
    
    def _get_timestamp(self):
        """Get current timestamp for unique names"""
        from datetime import datetime
        return datetime.now().strftime("%H%M%S")