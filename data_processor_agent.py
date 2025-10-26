"""
Data Processor Agent - Simple data transformation agent

Status: FIXED
Last Modified: 2025-10-20
Dependencies: agents.agent_base (Level 1)
Fixed Pattern: Level 1 Agent
"""

# Standard library imports
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


class DataProcessorAgent(BaseAgent):
    """
    Data Processor Agent for data transformations.
    
    Capabilities:
    - Transform data structures
    - Filter data by criteria
    - Aggregate data collections
    
    Dependencies:
    - agents.agent_base (BaseAgent)
    
    Supported Task Types:
    - transform: Transform data format
    - filter: Filter data by criteria
    - aggregate: Aggregate data collections
    - count: Count items in data
    """
    
    def __init__(self, agent_id: str = None):
        # Define capabilities
        capabilities = [
            AgentCapability(
                name="data_transformation",
                description="Transform data formats and structures",
                task_types=["transform"],
                required_params=["data", "operation"]
            ),
            AgentCapability(
                name="data_filtering",
                description="Filter data by various criteria",
                task_types=["filter"],
                required_params=["data", "criteria"]
            ),
            AgentCapability(
                name="data_aggregation",
                description="Aggregate data collections",
                task_types=["aggregate", "count"],
                required_params=["data"]
            )
        ]
        
        # Create config
        config = AgentConfig(
            agent_id=agent_id,
            name="DataProcessorAgent",
            description="Processes and transforms data",
            capabilities=capabilities,
            max_concurrent_tasks=15,
            task_timeout=120
        )
        
        # Initialize base
        super().__init__(config)
        
        self.logger.info(f"{self.name} initialized with {len(capabilities)} capabilities")
    
    def _execute_task(self, task: TaskRequest) -> Any:
        """Execute task based on type."""
        task_type = task.task_type
        
        if task_type == "transform":
            return self._transform(task.payload)
        elif task_type == "filter":
            return self._filter(task.payload)
        elif task_type == "aggregate":
            return self._aggregate(task.payload)
        elif task_type == "count":
            return self._count(task.payload)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _transform(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data."""
        if "data" not in payload or "operation" not in payload:
            raise ValueError("Missing required parameters: data, operation")
        
        data = payload["data"]
        operation = payload["operation"]
        
        if operation == "uppercase":
            if isinstance(data, str):
                result = data.upper()
            elif isinstance(data, list):
                result = [str(item).upper() for item in data]
            else:
                result = str(data).upper()
                
        elif operation == "lowercase":
            if isinstance(data, str):
                result = data.lower()
            elif isinstance(data, list):
                result = [str(item).lower() for item in data]
            else:
                result = str(data).lower()
                
        elif operation == "reverse":
            if isinstance(data, str):
                result = data[::-1]
            elif isinstance(data, list):
                result = data[::-1]
            else:
                result = str(data)[::-1]
                
        elif operation == "sort":
            if isinstance(data, list):
                result = sorted(data)
            else:
                raise ValueError("Sort operation requires a list")
                
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {
            "operation": "transform",
            "transform_type": operation,
            "input": data,
            "output": result
        }
    
    def _filter(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data."""
        if "data" not in payload or "criteria" not in payload:
            raise ValueError("Missing required parameters: data, criteria")
        
        data = payload["data"]
        criteria = payload["criteria"]
        
        if not isinstance(data, list):
            raise ValueError("Filter operation requires a list")
        
        # Simple filtering by criteria type
        if criteria == "non_empty":
            result = [item for item in data if item is not None and item != '']
        elif criteria == "numeric":
            result = [item for item in data if isinstance(item, (int, float))]
        elif criteria == "string":
            result = [item for item in data if isinstance(item, str)]
        elif isinstance(criteria, dict) and "min" in criteria:
            min_val = criteria["min"]
            result = [item for item in data if isinstance(item, (int, float)) and item >= min_val]
        elif isinstance(criteria, dict) and "max" in criteria:
            max_val = criteria["max"]
            result = [item for item in data if isinstance(item, (int, float)) and item <= max_val]
        else:
            raise ValueError(f"Unknown criteria: {criteria}")
        
        return {
            "operation": "filter",
            "criteria": criteria,
            "input_count": len(data),
            "output_count": len(result),
            "output": result
        }
    
    def _aggregate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate data."""
        if "data" not in payload:
            raise ValueError("Missing required parameter: data")
        
        data = payload["data"]
        
        if not isinstance(data, list):
            raise ValueError("Aggregate operation requires a list")
        
        # Calculate various aggregates
        numeric_data = [item for item in data if isinstance(item, (int, float))]
        
        result = {
            "operation": "aggregate",
            "total_items": len(data),
            "numeric_items": len(numeric_data)
        }
        
        if numeric_data:
            result["sum"] = sum(numeric_data)
            result["average"] = sum(numeric_data) / len(numeric_data)
            result["min"] = min(numeric_data)
            result["max"] = max(numeric_data)
        
        return result
    
    def _count(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Count items in data."""
        if "data" not in payload:
            raise ValueError("Missing required parameter: data")
        
        data = payload["data"]
        
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            count = len(data)
        elif isinstance(data, str):
            count = len(data)
        else:
            count = 1
        
        return {
            "operation": "count",
            "data_type": type(data).__name__,
            "count": count
        }


# Standalone test
if __name__ == "__main__":
    print("=" * 70)
    print("Testing DataProcessorAgent")
    print("=" * 70)
    
    # Create agent
    agent = DataProcessorAgent()
    
    # Test 1: Health check
    print("\n1. Health Check:")
    health = agent.health_check()
    print(json.dumps(health, indent=2))
    
    # Test 2: Transform - uppercase
    print("\n2. Test Transform (uppercase):")
    task1 = TaskRequest(
        task_type="transform",
        priority=Priority.MEDIUM,
        payload={
            "data": ["hello", "world", "test"],
            "operation": "uppercase"
        }
    )
    response1 = agent.process_task(task1)
    print(json.dumps(response1.to_dict(), indent=2))
    
    # Test 3: Filter - numeric
    print("\n3. Test Filter (numeric):")
    task2 = TaskRequest(
        task_type="filter",
        priority=Priority.MEDIUM,
        payload={
            "data": [1, "hello", 2, "world", 3, None, 4.5],
            "criteria": "numeric"
        }
    )
    response2 = agent.process_task(task2)
    print(json.dumps(response2.to_dict(), indent=2))
    
    # Test 4: Aggregate
    print("\n4. Test Aggregate:")
    task3 = TaskRequest(
        task_type="aggregate",
        priority=Priority.MEDIUM,
        payload={
            "data": [10, 20, 30, 40, 50]
        }
    )
    response3 = agent.process_task(task3)
    print(json.dumps(response3.to_dict(), indent=2))
    
    # Test 5: Count
    print("\n5. Test Count:")
    task4 = TaskRequest(
        task_type="count",
        priority=Priority.LOW,
        payload={
            "data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        }
    )
    response4 = agent.process_task(task4)
    print(json.dumps(response4.to_dict(), indent=2))
    
    # Test 6: Statistics
    print("\n6. Agent Statistics:")
    print(json.dumps(agent.stats, indent=2))
    
    print("\n" + "=" * 70)
    print("All tests completed")
    print("=" * 70)
