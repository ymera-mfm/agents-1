"""
Base Agent - Foundation for all specialized agents in the YMERA Multi-Agent AI System
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent operational states"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class MessageType(Enum):
    """Types of messages agents can exchange"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class BaseAgent(ABC):
    """
    Base class for all agents in the YMERA system.
    
    Provides core functionality for agent lifecycle management,
    inter-agent communication, and error handling.
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for this agent
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.state = AgentState.INITIALIZED
        self.created_at = datetime.utcnow()
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the agent with necessary resources.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process an incoming message.
        
        Args:
            message: Message dictionary containing type, payload, and metadata
            
        Returns:
            Optional response dictionary
        """
        pass
    
    @abstractmethod
    async def execute(self) -> Any:
        """
        Execute the agent's main task or workflow.
        
        Returns:
            Result of the execution
        """
        pass
    
    async def start(self) -> None:
        """Start the agent's main execution loop"""
        try:
            self.logger.info(f"Starting agent {self.agent_id}")
            self.state = AgentState.RUNNING
            
            # Initialize agent
            if not await self.initialize():
                raise RuntimeError(f"Failed to initialize agent {self.agent_id}")
            
            # Run main execution loop
            while self.state == AgentState.RUNNING:
                try:
                    # Check for incoming messages
                    if not self.message_queue.empty():
                        message = await self.message_queue.get()
                        await self.process_message(message)
                    
                    # Execute main task
                    await self.execute()
                    
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Error in execution loop: {e}", exc_info=True)
                    self.state = AgentState.ERROR
                    raise
                    
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id} failed: {e}", exc_info=True)
            self.state = AgentState.ERROR
            raise
    
    async def stop(self) -> None:
        """Stop the agent gracefully"""
        self.logger.info(f"Stopping agent {self.agent_id}")
        self.state = AgentState.STOPPED
        await self.cleanup()
    
    async def cleanup(self) -> None:
        """Clean up agent resources"""
        self.logger.info(f"Cleaning up agent {self.agent_id}")
        # Override in subclasses for specific cleanup
        pass
    
    async def send_message(
        self,
        target_agent: str,
        message_type: MessageType,
        payload: Dict[str, Any]
    ) -> None:
        """
        Send a message to another agent.
        
        Args:
            target_agent: ID of the target agent
            message_type: Type of message being sent
            payload: Message payload
        """
        message = {
            "from": self.agent_id,
            "to": target_agent,
            "type": message_type.value,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.debug(f"Sending message to {target_agent}: {message_type.value}")
        # This would integrate with the message broker in a real implementation
        # For now, we log the message
        
    async def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Receive a message from another agent.
        
        Args:
            message: Incoming message dictionary
        """
        await self.message_queue.put(message)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "config": self.config
        }
