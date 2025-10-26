# tests/unit/test_services.py
import pytest
from unittest.mock import AsyncMock, patch
from src.services.project_service import ProjectService
from src.services.task_service import TaskService
from src.models.project import ProjectRecord
from src.models.task import TaskRecord

class TestProjectService:
    """Unit tests for ProjectService"""
    
    @pytest.mark.asyncio
    async def test_create_project(self, test_session, test_user):
        """Test creating a project"""
        user = await test_user()
        service = ProjectService(test_session)
        
        project_data = {
            "name": "New Project",
            "description": "Test project description",
            "status": "draft"
        }
        
        project = await service.create_project(project_data, user.id)
        
        assert project.name == "New Project"
        assert project.owner_id == user.id
        assert project.status == "draft"
    
    @pytest.mark.asyncio
    async def test_get_project_stats(self, test_session, test_user):
        """Test getting project statistics"""
        user = await test_user()
        service = ProjectService(test_session)
        
        # Create a project with tasks
        project = ProjectRecord(
            name="Test Project",
            owner_id=user.id,
            status="active"
        )
        test_session.add(project)
        await test_session.commit()
        
        # Add some tasks
        for i in range(3):
            task = TaskRecord(
                name=f"Task {i}",
                project_id=project.id,
                status="completed" if i < 2 else "pending"
            )
            test_session.add(task)
        
        await test_session.commit()
        
        stats = await service.get_project_stats(project.id, user.id)
        
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 2
        assert stats["completion_rate"] == 2/3

class TestTaskService:
    """Unit tests for TaskService"""
    
    @pytest.mark.asyncio
    async def test_create_task(self, test_session, test_user):
        """Test creating a task"""
        user = await test_user()
        service = TaskService(test_session)
        
        # First create a project
        project = ProjectRecord(
            name="Test Project",
            owner_id=user.id
        )
        test_session.add(project)
        await test_session.commit()
        
        task_data = {
            "name": "New Task",
            "project_id": project.id,
            "priority": "high"
        }
        
        task = await service.create_task(task_data, user.id)
        
        assert task.name == "New Task"
        assert task.project_id == project.id
        assert task.priority == "high"
    
    @pytest.mark.asyncio
    async def test_process_task(self, test_session, test_user):
        """Test processing a task"""
        user = await test_user()
        service = TaskService(test_session)
        
        # Create project and task
        project = ProjectRecord(
            name="Test Project",
            owner_id=user.id
        )
        test_session.add(project)
        await test_session.commit()
        
        task = TaskRecord(
            name="Test Task",
            project_id=project.id,
            status="pending"
        )
        test_session.add(task)
        await test_session.commit()
        
        # Mock external dependencies
        with patch('src.services.task_service.ExternalServiceClient') as mock_client:
            mock_client.process_task = AsyncMock(return_value={"result": "success"})
            
            result = await service.process_task(task.id)
            
            assert result["result"] == "success"
            # Verify task status was updated
            updated_task = await test_session.get(TaskRecord, task.id)
            assert updated_task.status == "completed"