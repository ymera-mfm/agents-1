"""
Agent Communicator - Handles inter-agent communication
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
import structlog

from shared.config.settings import Settings
from shared.database.connection_pool import DatabaseManager


logger = structlog.get_logger(__name__)


class AgentCommunicator:
    """Handles communication between agents"""
    
    def __init__(self, db_manager: DatabaseManager, settings: Settings):
        self.db_manager = db_manager
        self.settings = settings
        self.logger = structlog.get_logger(__name__)
        self.message_queue = asyncio.Queue()
        self.subscriptions = {}
    
    async def send_to_agent(self, agent_name: str, message: Dict[str, Any]) -> bool:
        """Send message to specific agent"""
        try:
            message_envelope = {
                'to': agent_name,
                'from': 'system',
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'id': f"msg_{datetime.utcnow().timestamp()}"
            }
            
            await self.message_queue.put(message_envelope)
            
            self.logger.info(f"Message sent to {agent_name}", message_id=message_envelope['id'])
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {agent_name}: {e}", exc_info=True)
            return False
    
    async def send_to_agent_manager(self, message: Dict[str, Any]) -> bool:
        """Send message to agent manager"""
        return await self.send_to_agent('agent_manager', message)
    
    async def broadcast(self, message: Dict[str, Any], exclude: list = None) -> int:
        """Broadcast message to all subscribed agents"""
        exclude = exclude or []
        sent_count = 0
        
        for agent_name in self.subscriptions.keys():
            if agent_name not in exclude:
                if await self.send_to_agent(agent_name, message):
                    sent_count += 1
        
        return sent_count
    
    async def subscribe(self, agent_name: str, callback):
        """Subscribe agent to receive messages"""
        self.subscriptions[agent_name] = callback
        self.logger.info(f"Agent {agent_name} subscribed to messages")
    
    async def unsubscribe(self, agent_name: str):
        """Unsubscribe agent from messages"""
        if agent_name in self.subscriptions:
            del self.subscriptions[agent_name]
            self.logger.info(f"Agent {agent_name} unsubscribed from messages")
