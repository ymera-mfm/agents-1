"""
Communication Agent - Handles inter-agent messaging
"""
from typing import Any, Dict, Optional
import asyncio

from base_agent import BaseAgent, MessageType
from logger import logger


class CommunicationAgent(BaseAgent):
    """
    Agent responsible for managing inter-agent communication.
    Handles message routing, delivery, and queuing.
    """
    
    def __init__(self, agent_id: str = "communication_agent", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.message_broker: Dict[str, asyncio.Queue] = {}
        self.message_history: list = []
        
    async def initialize(self) -> bool:
        """Initialize communication agent"""
        try:
            self.logger.info("Initializing Communication Agent")
            # Setup message broker connections
            # In production, this would connect to NATS/Kafka
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}", exc_info=True)
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and route messages between agents.
        
        Args:
            message: Message to process
            
        Returns:
            Response if message requires one
        """
        try:
            self.logger.debug(f"Processing message: {message}")
            
            # Store in history
            self.message_history.append(message)
            
            # Route to target agent
            target = message.get("to")
            if target and target in self.message_broker:
                await self.message_broker[target].put(message)
            
            return {
                "status": "delivered",
                "message_id": message.get("message_id", "unknown")
            }
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def execute(self) -> Any:
        """Execute communication agent main loop"""
        # Monitor message queues and handle routing
        await asyncio.sleep(1)
        return None
    
    async def register_agent(self, agent_id: str) -> None:
        """Register an agent for message delivery"""
        if agent_id not in self.message_broker:
            self.message_broker[agent_id] = asyncio.Queue()
            self.logger.info(f"Registered agent: {agent_id}")
    
    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.message_broker:
            del self.message_broker[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
    
    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self.message_history)
