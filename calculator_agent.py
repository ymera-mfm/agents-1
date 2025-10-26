"""
Calculator Agent - Simple utility agent for mathematical operations

Status: FIXED
Last Modified: 2025-10-20
Dependencies: agents.agent_base (Level 1)
Fixed Pattern: Level 1 Agent
"""

# Standard library imports
import json
import sys
from pathlib import Path
from typing import Dict, Any

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


class CalculatorAgent(BaseAgent):
    """
    Calculator Agent for mathematical operations.
    
    Capabilities:
    - Basic arithmetic (add, subtract, multiply, divide)
    - Advanced operations (power, square root, modulo)
    
    Dependencies:
    - agents.agent_base (BaseAgent)
    
    Supported Task Types:
    - add: Addition of two numbers
    - subtract: Subtraction of two numbers
    - multiply: Multiplication of two numbers
    - divide: Division of two numbers
    - power: Power operation
    - sqrt: Square root
    - modulo: Modulo operation
    """
    
    def __init__(self, agent_id: str = None):
        # Define capabilities
        capabilities = [
            AgentCapability(
                name="basic_arithmetic",
                description="Basic arithmetic operations",
                task_types=["add", "subtract", "multiply", "divide"],
                required_params=["a", "b"]
            ),
            AgentCapability(
                name="advanced_math",
                description="Advanced mathematical operations",
                task_types=["power", "sqrt", "modulo"],
                required_params=["a"]
            )
        ]
        
        # Create config
        config = AgentConfig(
            agent_id=agent_id,
            name="CalculatorAgent",
            description="Performs mathematical calculations",
            capabilities=capabilities,
            max_concurrent_tasks=20,
            task_timeout=60
        )
        
        # Initialize base
        super().__init__(config)
        
        self.logger.info(f"{self.name} initialized with {len(capabilities)} capabilities")
    
    def _execute_task(self, task: TaskRequest) -> Any:
        """Execute task based on type."""
        task_type = task.task_type
        payload = task.payload
        
        # Validate that we have numbers
        if task_type in ["add", "subtract", "multiply", "divide", "power", "modulo"]:
            if "a" not in payload or "b" not in payload:
                raise ValueError("Both 'a' and 'b' parameters required")
            
            try:
                a = float(payload["a"])
                b = float(payload["b"])
            except (ValueError, TypeError):
                raise ValueError("Parameters 'a' and 'b' must be numbers")
        
        # Execute based on task type
        if task_type == "add":
            result = self._add(payload)
        elif task_type == "subtract":
            result = self._subtract(payload)
        elif task_type == "multiply":
            result = self._multiply(payload)
        elif task_type == "divide":
            result = self._divide(payload)
        elif task_type == "power":
            result = self._power(payload)
        elif task_type == "sqrt":
            result = self._sqrt(payload)
        elif task_type == "modulo":
            result = self._modulo(payload)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
        
        return result
    
    def _add(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform addition."""
        a = float(payload["a"])
        b = float(payload["b"])
        result = a + b
        
        return {
            "operation": "add",
            "a": a,
            "b": b,
            "result": result,
            "formula": f"{a} + {b} = {result}"
        }
    
    def _subtract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform subtraction."""
        a = float(payload["a"])
        b = float(payload["b"])
        result = a - b
        
        return {
            "operation": "subtract",
            "a": a,
            "b": b,
            "result": result,
            "formula": f"{a} - {b} = {result}"
        }
    
    def _multiply(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform multiplication."""
        a = float(payload["a"])
        b = float(payload["b"])
        result = a * b
        
        return {
            "operation": "multiply",
            "a": a,
            "b": b,
            "result": result,
            "formula": f"{a} × {b} = {result}"
        }
    
    def _divide(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform division."""
        a = float(payload["a"])
        b = float(payload["b"])
        
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        
        result = a / b
        
        return {
            "operation": "divide",
            "a": a,
            "b": b,
            "result": result,
            "formula": f"{a} ÷ {b} = {result}"
        }
    
    def _power(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform power operation."""
        a = float(payload["a"])
        b = float(payload["b"])
        result = a ** b
        
        return {
            "operation": "power",
            "base": a,
            "exponent": b,
            "result": result,
            "formula": f"{a}^{b} = {result}"
        }
    
    def _sqrt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate square root."""
        a = float(payload["a"])
        
        if a < 0:
            raise ValueError("Square root of negative number is not supported")
        
        result = a ** 0.5
        
        return {
            "operation": "sqrt",
            "value": a,
            "result": result,
            "formula": f"√{a} = {result}"
        }
    
    def _modulo(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform modulo operation."""
        a = float(payload["a"])
        b = float(payload["b"])
        
        if b == 0:
            raise ValueError("Modulo by zero is not allowed")
        
        result = a % b
        
        return {
            "operation": "modulo",
            "a": a,
            "b": b,
            "result": result,
            "formula": f"{a} mod {b} = {result}"
        }


# Standalone test
if __name__ == "__main__":
    print("=" * 70)
    print("Testing CalculatorAgent")
    print("=" * 70)
    
    # Create agent
    agent = CalculatorAgent()
    
    # Test 1: Health check
    print("\n1. Health Check:")
    health = agent.health_check()
    print(json.dumps(health, indent=2))
    
    # Test 2: Addition
    print("\n2. Test Addition:")
    task1 = TaskRequest(
        task_type="add",
        priority=Priority.MEDIUM,
        payload={"a": 10, "b": 5}
    )
    response1 = agent.process_task(task1)
    print(json.dumps(response1.to_dict(), indent=2))
    
    # Test 3: Division
    print("\n3. Test Division:")
    task2 = TaskRequest(
        task_type="divide",
        priority=Priority.MEDIUM,
        payload={"a": 20, "b": 4}
    )
    response2 = agent.process_task(task2)
    print(json.dumps(response2.to_dict(), indent=2))
    
    # Test 4: Power
    print("\n4. Test Power:")
    task3 = TaskRequest(
        task_type="power",
        priority=Priority.MEDIUM,
        payload={"a": 2, "b": 8}
    )
    response3 = agent.process_task(task3)
    print(json.dumps(response3.to_dict(), indent=2))
    
    # Test 5: Square Root
    print("\n5. Test Square Root:")
    task4 = TaskRequest(
        task_type="sqrt",
        priority=Priority.MEDIUM,
        payload={"a": 16}
    )
    response4 = agent.process_task(task4)
    print(json.dumps(response4.to_dict(), indent=2))
    
    # Test 6: Error - Division by zero
    print("\n6. Test Error Handling (Division by zero):")
    task5 = TaskRequest(
        task_type="divide",
        priority=Priority.MEDIUM,
        payload={"a": 10, "b": 0}
    )
    response5 = agent.process_task(task5)
    print(json.dumps(response5.to_dict(), indent=2))
    
    # Test 7: Statistics
    print("\n7. Agent Statistics:")
    print(json.dumps(agent.stats, indent=2))
    
    print("\n" + "=" * 70)
    print("All tests completed")
    print("=" * 70)
