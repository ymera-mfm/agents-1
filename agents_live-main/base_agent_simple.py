"""
Simple Base Agent - Importable without external dependencies
This is a lightweight version that agents can import successfully.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)


class AgentStatus(Enum):
    """Agent status."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Priority(Enum):
    """Task priority."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentConfig:
    """Agent configuration."""
    name: str
    version: str = "1.0.0"
    agent_type: str = "generic"
    capabilities: List[str] = field(default_factory=list)
    log_level: str = "INFO"


@dataclass
class TaskRequest:
    """Task request."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.MEDIUM


@dataclass
class TaskResponse:
    """Task response."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    
    def dict(self):
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "result": self.result,
            "error": self.error
        }


class BaseAgent:
    """
    Simple base agent class.
    Provides basic functionality without external dependencies.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.logger.setLevel(getattr(logging, config.log_level))
        self._shutdown_event = None  # Placeholder for compatibility
        
        self.logger.info(f"Agent {self.name} initialized")
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """
        Execute task implementation - override in subclasses.
        """
        raise NotImplementedError("Subclasses must implement _execute_task_impl")
    
    async def _subscribe(self, subject: str, handler, queue_group: str = None):
        """Placeholder for compatibility."""
        self.logger.info(f"Subscribe called for {subject}")
    
    async def start(self):
        """Start the agent."""
        self.logger.info(f"Agent {self.name} starting")
    
    async def run(self):
        """Run the agent."""
        await self.start()
        self.logger.info(f"Agent {self.name} running")


# Export for compatibility
__all__ = [
    'BaseAgent',
    'AgentConfig',
    'TaskRequest',
    'TaskResponse',
    'Priority',
    'AgentStatus',
    'TaskStatus'
]
