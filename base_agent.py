"""
Base Agent - Foundation for all specialized agents in the YMERA Multi-Agent AI System
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
import asyncio
import logging
import json
import pickle
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
        self.created_at = datetime.now(timezone.utc)
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.checkpoint_interval = self.config.get('checkpoint_interval', 60)  # seconds
        self.last_checkpoint = datetime.now(timezone.utc)
        self._storage_backend = None  # Will be set by subclasses
        
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
            
            # Try to load checkpoint if available
            await self.load_checkpoint()
            
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
                    
                    # Periodic checkpointing
                    if await self.should_checkpoint():
                        await self.save_checkpoint()
                    
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Error in execution loop: {e}", exc_info=True)
                    # Save checkpoint before transitioning to error state
                    await self.save_checkpoint()
                    self.state = AgentState.ERROR
                    raise
                    
        except Exception as e:
            self.logger.error(f"Agent {self.agent_id} failed: {e}", exc_info=True)
            self.state = AgentState.ERROR
            raise
    
    async def stop(self) -> None:
        """Stop the agent gracefully"""
        self.logger.info(f"Stopping agent {self.agent_id}")
        # Save final checkpoint before stopping
        await self.save_checkpoint()
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
            "config": self.config,
            "last_checkpoint": self.last_checkpoint.isoformat() if self.last_checkpoint else None
        }
    
    async def save_checkpoint(self, storage_backend=None) -> bool:
        """
        Save agent state checkpoint for recovery.
        
        Args:
            storage_backend: Optional storage backend (Redis, PostgreSQL, etc.)
            
        Returns:
            bool: True if checkpoint saved successfully
        """
        try:
            checkpoint_data = {
                "agent_id": self.agent_id,
                "state": self.state.value,
                "config": self.config,
                "created_at": self.created_at.isoformat(),
                "checkpoint_time": datetime.now(timezone.utc).isoformat(),
                "custom_state": await self.get_checkpoint_state()
            }
            
            # Use provided storage or default
            backend = storage_backend or self._storage_backend
            
            if backend:
                # Save to storage backend (Redis, PostgreSQL, etc.)
                checkpoint_key = f"agent:checkpoint:{self.agent_id}"
                await backend.set(checkpoint_key, json.dumps(checkpoint_data))
                self.logger.info(f"Checkpoint saved for agent {self.agent_id}")
            else:
                # Fallback: save to local file
                checkpoint_file = f"/tmp/agent_checkpoint_{self.agent_id}.json"
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f, indent=2)
                self.logger.info(f"Checkpoint saved to file: {checkpoint_file}")
            
            self.last_checkpoint = datetime.now(timezone.utc)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
            return False
    
    async def load_checkpoint(self, storage_backend=None) -> bool:
        """
        Load agent state from checkpoint for recovery.
        
        Args:
            storage_backend: Optional storage backend (Redis, PostgreSQL, etc.)
            
        Returns:
            bool: True if checkpoint loaded successfully
        """
        try:
            backend = storage_backend or self._storage_backend
            checkpoint_data = None
            
            if backend:
                # Load from storage backend
                checkpoint_key = f"agent:checkpoint:{self.agent_id}"
                data = await backend.get(checkpoint_key)
                if data:
                    checkpoint_data = json.loads(data)
            else:
                # Fallback: load from local file
                checkpoint_file = f"/tmp/agent_checkpoint_{self.agent_id}.json"
                try:
                    with open(checkpoint_file, 'r') as f:
                        checkpoint_data = json.load(f)
                except FileNotFoundError:
                    self.logger.info(f"No checkpoint found for agent {self.agent_id}")
                    return False
            
            if checkpoint_data:
                # Restore state from checkpoint
                self.config = checkpoint_data.get('config', {})
                await self.restore_checkpoint_state(checkpoint_data.get('custom_state', {}))
                self.logger.info(f"Checkpoint loaded for agent {self.agent_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}", exc_info=True)
            return False
    
    async def get_checkpoint_state(self) -> Dict[str, Any]:
        """
        Get custom state to include in checkpoint.
        Override in subclasses to save agent-specific state.
        
        Returns:
            Dictionary containing custom state
        """
        return {}
    
    async def restore_checkpoint_state(self, state: Dict[str, Any]) -> None:
        """
        Restore custom state from checkpoint.
        Override in subclasses to restore agent-specific state.
        
        Args:
            state: Custom state dictionary from checkpoint
        """
        pass
    
    async def should_checkpoint(self) -> bool:
        """
        Determine if checkpoint should be saved now.
        
        Returns:
            bool: True if checkpoint should be saved
        """
        time_since_checkpoint = (datetime.now(timezone.utc) - self.last_checkpoint).total_seconds()
        return time_since_checkpoint >= self.checkpoint_interval
    
    def set_storage_backend(self, backend) -> None:
        """
        Set the storage backend for checkpointing.
        
        Args:
            backend: Storage backend instance (Redis client, DB session, etc.)
        """
        self._storage_backend = backend
