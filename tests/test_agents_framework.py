#!/usr/bin/env python3
"""
Test the agents framework with pytest
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_agents_package_imports():
    """Test that agents package can be imported."""
    from agents import agent_base, shared_utils
    assert agent_base is not None
    assert shared_utils is not None

def test_base_agent_classes():
    """Test BaseAgent classes."""
    from agents.agent_base import (
        BaseAgent,
        AgentConfig,
        TaskRequest,
        TaskResponse,
        Priority,
        TaskStatus
    )
    
    # Test AgentConfig
    config = AgentConfig(
        name="TestAgent",
        description="Test agent"
    )
    assert config.name == "TestAgent"
    
    # Test TaskRequest
    task = TaskRequest(
        task_type="test",
        priority=Priority.MEDIUM
    )
    assert task.task_type == "test"
    assert task.priority == Priority.MEDIUM

def test_example_agent():
    """Test example agent."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from agents.agent_base import (
        BaseAgent,
        AgentConfig,
        AgentCapability,
        TaskRequest,
        Priority
    )
    
    # Create simple test agent
    capabilities = [
        AgentCapability(
            name="test",
            description="Test capability",
            task_types=["test"],
            required_params=[]
        )
    ]
    
    config = AgentConfig(
        name="TestAgent",
        description="Test",
        capabilities=capabilities
    )
    
    class TestAgent(BaseAgent):
        def _execute_task(self, task):
            return {"result": "success"}
    
    agent = TestAgent(config)
    assert agent.name == "TestAgent"
    
    # Test task processing
    task = TaskRequest(
        task_type="test",
        priority=Priority.MEDIUM,
        payload={}
    )
    
    response = agent.process_task(task)
    assert response.status.value == "success"

def test_calculator_agent():
    """Test calculator agent imports and works."""
    from agents.calculator_agent import CalculatorAgent
    from agents.agent_base import TaskRequest, Priority
    
    agent = CalculatorAgent()
    
    # Test addition
    task = TaskRequest(
        task_type="add",
        priority=Priority.MEDIUM,
        payload={"a": 5, "b": 3}
    )
    
    response = agent.process_task(task)
    assert response.status.value == "success"
    assert response.result["result"] == 8.0

def test_data_processor_agent():
    """Test data processor agent."""
    from agents.data_processor_agent import DataProcessorAgent
    from agents.agent_base import TaskRequest, Priority
    
    agent = DataProcessorAgent()
    
    # Test count
    task = TaskRequest(
        task_type="count",
        priority=Priority.MEDIUM,
        payload={"data": [1, 2, 3, 4, 5]}
    )
    
    response = agent.process_task(task)
    assert response.status.value == "success"
    assert response.result["count"] == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
