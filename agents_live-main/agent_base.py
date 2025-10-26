"""
Shared Base Agent Module
All agents should import from this module.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
import json

# Setup logging


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class TaskRequest:
    """Standardized task request format."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    priority: Priority = Priority.MEDIUM
    payload: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300  # seconds
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'priority': self.priority.name,
            'payload': self.payload,
            'timeout': self.timeout,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class TaskResponse:
    """Standardized task response format."""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    completed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'execution_time': self.execution_time,
            'completed_at': self.completed_at.isoformat(),
            'metadata': self.metadata
        }


class AgentCapability:
    """Agent capability descriptor."""
    
    def __init__(
        self,
        name: str,
        description: str,
        task_types: List[str],
        required_params: List[str] = None
    ):
        self.name = name
        self.description = description
        self.task_types = task_types
        self.required_params = required_params or []


@dataclass
class AgentConfig:
    """Agent configuration."""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "UnnamedAgent"
    description: str = ""
    capabilities: List[AgentCapability] = field(default_factory=list)
    max_concurrent_tasks: int = 10
    task_timeout: int = 300
    retry_attempts: int = 3
    log_level: str = "INFO"


class BaseAgent:
    """
    Base Agent class with common functionality.
    All agents should inherit from this class.
    """
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.agent_id = self.config.agent_id
        self.name = self.config.name
        self.capabilities = self.config.capabilities
        
        # Setup logging
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        # Statistics
        self.stats = {
            'tasks_processed': 0,
            'tasks_succeeded': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0
        }
        
        self.logger.info(f"Agent initialized: {self.name} ({self.agent_id})")
    
    def process_task(self, task: TaskRequest) -> TaskResponse:
        """
        Process a task request.
        
        Args:
            task: TaskRequest object
        
        Returns:
            TaskResponse object
        """
        start_time = datetime.now()
        self.logger.info(f"Processing task {task.task_id} of type {task.task_type}")
        
        try:
            # Validate task
            self._validate_task(task)
            
            # Execute task
            result = self._execute_task(task)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update stats
            self.stats['tasks_processed'] += 1
            self.stats['tasks_succeeded'] += 1
            self.stats['total_execution_time'] += execution_time
            
            self.logger.info(
                f"Task {task.task_id} completed in {execution_time:.2f}s"
            )
            
            return TaskResponse(
                task_id=task.task_id,
                status=TaskStatus.SUCCESS,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.stats['tasks_processed'] += 1
            self.stats['tasks_failed'] += 1
            
            self.logger.error(f"Task {task.task_id} failed: {str(e)}")
            
            return TaskResponse(
                task_id=task.task_id,
                status=TaskStatus.ERROR,
                error=str(e),
                execution_time=execution_time
            )
    
    def _validate_task(self, task: TaskRequest):
        """Validate task request."""
        if not task.task_type:
            raise ValueError("Task type is required")
        
        if task.task_type not in self.get_supported_task_types():
            raise ValueError(
                f"Unsupported task type: {task.task_type}. "
                f"Supported types: {self.get_supported_task_types()}"
            )
    
    def _execute_task(self, task: TaskRequest) -> Any:
        """
        Execute the task. Override in subclasses.
        
        Args:
            task: TaskRequest object
        
        Returns:
            Task result
        """
        raise NotImplementedError("Subclasses must implement _execute_task")
    
    def get_supported_task_types(self) -> List[str]:
        """Get list of supported task types."""
        task_types = []
        for cap in self.capabilities:
            task_types.extend(cap.task_types)
        return task_types
    
    def health_check(self) -> Dict[str, Any]:
        """Check agent health and return status."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': 'healthy',
            'capabilities': [cap.name for cap in self.capabilities],
            'supported_task_types': self.get_supported_task_types(),
            'statistics': self.stats.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.config.description,
            'capabilities': [
                {
                    'name': cap.name,
                    'description': cap.description,
                    'task_types': cap.task_types,
                    'required_params': cap.required_params
                }
                for cap in self.capabilities
            ],
            'config': {
                'max_concurrent_tasks': self.config.max_concurrent_tasks,
                'task_timeout': self.config.task_timeout,
                'retry_attempts': self.config.retry_attempts
            }
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            'tasks_processed': 0,
            'tasks_succeeded': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0
        }
        self.logger.info("Statistics reset")


# Export main classes
__all__ = [
    'BaseAgent',
    'AgentConfig',
    'AgentCapability',
    'TaskRequest',
    'TaskResponse',
    'Priority',
    'TaskStatus'
]
