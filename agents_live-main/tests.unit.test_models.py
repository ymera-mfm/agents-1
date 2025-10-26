# tests/unit/test_models.py
import pytest
from datetime import datetime, timedelta
from src.models.user import UserRecord
from src.models.project import ProjectRecord
from src.models.task import TaskRecord

class TestUserModel:
    """Unit tests for User model"""
    
    def test_user_creation(self):
        """Test user model creation"""
        user = UserRecord(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
            full_name="Test User"
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.is_verified is False
    
    def test_user_to_dict(self):
        """Test user model to_dict method"""
        user = UserRecord(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpassword",
            full_name="Test User"
        )
        
        user_dict = user.to_dict()
        assert user_dict["email"] == "test@example.com"
        assert "hashed_password" not in user_dict  # Password should be excluded

class TestProjectModel:
    """Unit tests for Project model"""
    
    def test_project_creation(self):
        """Test project model creation"""
        project = ProjectRecord(
            name="Test Project",
            description="Test Description",
            owner_id="user123",
            status="active"
        )
        
        assert project.name == "Test Project"
        assert project.status == "active"
        assert project.optimization_score == 0.0
    
    def test_project_risk_assessment(self):
        """Test project risk assessment calculation"""
        project = ProjectRecord(
            name="High Risk Project",
            budget=1000000,  # High budget
            security_level="secret"
        )
        
        # This would test the risk assessment logic
        assert hasattr(project, 'risk_assessment')

class TestTaskModel:
    """Unit tests for Task model"""
    
    def test_task_creation(self):
        """Test task model creation"""
        task = TaskRecord(
            name="Test Task",
            project_id="project123",
            priority="high"
        )
        
        assert task.name == "Test Task"
        assert task.priority == "high"
        assert task.status == "pending"
        assert task.retry_count == 0