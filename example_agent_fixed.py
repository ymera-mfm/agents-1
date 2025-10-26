"""
Example Agent - Demonstrates the fixed agent pattern

Status: FIXED
Last Modified: 2025-10-20
Dependencies: agents.agent_base (Level 1)
"""

# Standard library imports
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local imports from agents package
from agents.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    TaskRequest,
    TaskResponse,
    Priority,
    TaskStatus
)


class ExampleAgent(BaseAgent):
    """
    Example Agent demonstrating the fixed pattern.
    
    Capabilities:
    - Process simple tasks
    - Return formatted results
    
    Dependencies:
    - agents.agent_base (BaseAgent)
    
    Supported Task Types:
    - example_task: Process example data
    - echo_task: Echo back input data
    """
    
    def __init__(self, agent_id: str = None):
        # Define capabilities
        capabilities = [
            AgentCapability(
                name="example_processing",
                description="Process example tasks",
                task_types=["example_task"],
                required_params=["data"]
            ),
            AgentCapability(
                name="echo_service",
                description="Echo back provided input",
                task_types=["echo_task"],
                required_params=["message"]
            )
        ]
        
        # Create config
        config = AgentConfig(
            agent_id=agent_id,
            name="ExampleAgent",
            description="Demonstrates fixed agent pattern",
            capabilities=capabilities,
            max_concurrent_tasks=5,
            task_timeout=300
        )
        
        # Initialize base
        super().__init__(config)
        
        self.logger.info(f"{self.name} initialized with {len(capabilities)} capabilities")
    
    def _execute_task(self, task: TaskRequest) -> Any:
        """Execute task based on type."""
        task_type = task.task_type
        
        if task_type == "example_task":
            return self._handle_example_task(task)
        elif task_type == "echo_task":
            return self._handle_echo_task(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _handle_example_task(self, task: TaskRequest) -> Any:
        """Handle example_task."""
        payload = task.payload
        
        # Validate required params
        if "data" not in payload:
            raise ValueError("Missing required parameter: data")
        
        # Process task
        result = {
            "processed": True,
            "task_type": task.task_type,
            "input": payload["data"],
            "output": {
                "status": "success",
                "data_length": len(str(payload["data"])),
                "timestamp": task.created_at.isoformat()
            }
        }
        
        return result
    
    def _handle_echo_task(self, task: TaskRequest) -> Any:
        """Handle echo_task."""
        payload = task.payload
        
        # Validate required params
        if "message" not in payload:
            raise ValueError("Missing required parameter: message")
        
        # Process task
        result = {
            "processed": True,
            "task_type": task.task_type,
            "echo": payload["message"],
            "metadata": {
                "priority": task.priority.name,
                "timestamp": task.created_at.isoformat()
            }
        }
        
        return result


# Standalone test
if __name__ == "__main__":
    print("=" * 70)
    print("Testing ExampleAgent")
    print("=" * 70)
    
    # Create agent
    agent = ExampleAgent()
    
    # Test 1: Health check
    print("\n1. Health Check:")
    health = agent.health_check()
    print(json.dumps(health, indent=2))
    
    # Test 2: Get info
    print("\n2. Agent Info:")
    info = agent.get_info()
    print(json.dumps(info, indent=2))
    
    # Test 3: Process example_task
    print("\n3. Test example_task:")
    task1 = TaskRequest(
        task_type="example_task",
        priority=Priority.MEDIUM,
        payload={
            "data": "Sample data for processing"
        }
    )
    response1 = agent.process_task(task1)
    print(json.dumps(response1.to_dict(), indent=2))
    
    # Test 4: Process echo_task
    print("\n4. Test echo_task:")
    task2 = TaskRequest(
        task_type="echo_task",
        priority=Priority.HIGH,
        payload={
            "message": "Hello from ExampleAgent!"
        }
    )
    response2 = agent.process_task(task2)
    print(json.dumps(response2.to_dict(), indent=2))
    
    # Test 5: Error handling
    print("\n5. Test error handling (invalid task type):")
    task3 = TaskRequest(
        task_type="invalid_type",
        priority=Priority.LOW,
        payload={}
    )
    response3 = agent.process_task(task3)
    print(json.dumps(response3.to_dict(), indent=2))
    
    # Test 6: Error handling (missing required param)
    print("\n6. Test error handling (missing parameter):")
    task4 = TaskRequest(
        task_type="example_task",
        priority=Priority.MEDIUM,
        payload={}  # Missing 'data' parameter
    )
    response4 = agent.process_task(task4)
    print(json.dumps(response4.to_dict(), indent=2))
    
    # Test 7: Statistics
    print("\n7. Agent Statistics:")
    print(json.dumps(agent.stats, indent=2))
    
    print("\n" + "=" * 70)
    print("All tests completed")
    print("=" * 70)
