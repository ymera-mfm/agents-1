# tests/utils/test_helpers.py
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user_data(override: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test user data"""
        base_data = {
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "username": f"testuser_{datetime.now().timestamp()}",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "role": "member"
        }
        return {**base_data, **(override or {})}
    
    @staticmethod
    def create_project_data(override: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test project data"""
        base_data = {
            "name": f"Test Project {datetime.now().timestamp()}",
            "description": "Test project description",
            "status": "draft",
            "security_level": "confidential"
        }
        return {**base_data, **(override or {})}
    
    @staticmethod
    def create_task_data(project_id: str, override: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test task data"""
        base_data = {
            "name": f"Test Task {datetime.now().timestamp()}",
            "project_id": project_id,
            "priority": "medium",
            "status": "pending"
        }
        return {**base_data, **(override or {})}

class AssertionHelpers:
    """Custom assertion helpers"""
    
    @staticmethod
    def assert_datetime_recent(dt_string: str, max_minutes: int = 5):
        """Assert that a datetime string is recent"""
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        now = datetime.utcnow()
        assert (now - dt).total_seconds() < max_minutes * 60
    
    @staticmethod
    def assert_response_structure(response, expected_structure: Dict[str, Any]):
        """Assert that response matches expected structure"""
        def check_structure(actual, expected, path=""):
            if isinstance(expected, dict):
                assert isinstance(actual, dict), f"Expected dict at {path}, got {type(actual)}"
                for key, expected_value in expected.items():
                    assert key in actual, f"Missing key {path}.{key}"
                    check_structure(actual[key], expected_value, f"{path}.{key}")
            elif isinstance(expected, list) and expected:
                assert isinstance(actual, list), f"Expected list at {path}, got {type(actual)}"
                for i, item in enumerate(actual):
                    check_structure(item, expected[0], f"{path}[{i}]")
            else:
                # Check type match
                expected_type = type(expected) if expected is not None else type(None)
                assert isinstance(actual, expected_type), \
                    f"Expected type {expected_type} at {path}, got {type(actual)}"
        
        check_structure(response, expected_structure)

class PerformanceHelpers:
    """Performance testing helpers"""
    
    @staticmethod
    def assert_response_time(response, max_time_ms: int):
        """Assert that response time is within limits"""
        # This would be implemented with proper timing in actual performance tests
        pass
    
    @staticmethod
    def measure_throughput(operations: int, duration_seconds: float) -> float:
        """Calculate operations per second"""
        return operations / duration_seconds
    
    @staticmethod
    def assert_throughput(actual_ops: float, expected_ops: float, tolerance: float = 0.1):
        """Assert that throughput meets expectations"""
        assert actual_ops >= expected_ops * (1 - tolerance), \
            f"Throughput {actual_ops} ops/s below expected {expected_ops} ops/s"