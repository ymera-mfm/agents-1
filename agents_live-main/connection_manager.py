# websocket/connection_manager.py
"""
WebSocket connection manager for real-time communication with agents
and administrative interfaces
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime
import json
import uuid
from fastapi import WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket connection manager with authentication and secure messaging"""
    
    def __init__(self, redis_client):
        """Initialize with Redis for cross-instance communication"""
        self.redis = redis_client
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.agent_connections: Dict[str, Set[str]] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        # Start pubsub listener for cross-instance communication
        asyncio.create_task(self._start_redis_listener())
        
        logger.info("WebSocket ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, entity_id: str, 
                    connection_type: str, metadata: Dict[str, Any] = None) -> str:
        """Accept WebSocket connection and register it"""
        connection_id = str(uuid.uuid4())
        
        await websocket.accept()
        
        # Store connection
        if entity_id not in self.active_connections:
            self.active_connections[entity_id] = {}
        self.active_connections[entity_id][connection_id] = websocket
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            "entity_id": entity_id,
            "type": connection_type,
            "connected_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        # Map to appropriate collections
        if connection_type == "user":
            if entity_id not in self.user_connections:
                self.user_connections[entity_id] = set()
            self.user_connections[entity_id].add(connection_id)
        elif connection_type == "agent":
            if entity_id not in self.agent_connections:
                self.agent_connections[entity_id] = set()
            self.agent_connections[entity_id].add(connection_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"WebSocket connected: {connection_type}={entity_id}, connection={connection_id}")
        return connection_id
    
    async def disconnect(self, connection_id: str) -> None:
        """Disconnect and unregister WebSocket connection"""
        if connection_id not in self.connection_metadata:
            return
        
        # Get connection info
        metadata = self.connection_metadata[connection_id]
        entity_id = metadata["entity_id"]
        connection_type = metadata["type"]
        
        # Remove from mappings
        if connection_type == "user" and entity_id in self.user_connections:
            self.user_connections[entity_id].discard(connection_id)
            if not self.user_connections[entity_id]:
                del self.user_connections[entity_id]
        
        elif connection_type == "agent" and entity_id in self.agent_connections:
            self.agent_connections[entity_id].discard(connection_id)
            if not self.agent_connections[entity_id]:
                del self.agent_connections[entity_id]
        
        # Remove from active connections
        if entity_id in self.active_connections:
            if connection_id in self.active_connections[entity_id]:
                del self.active_connections[entity_id][connection_id]
            
            if not self.active_connections[entity_id]:
                del self.active_connections[entity_id]
        
        # Remove metadata
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_type}={entity_id}, connection={connection_id}")
    
    async def send_to_agent(self, agent_id: str, message: Dict) -> bool:
        """Send message to specific agent"""
        success = False
        
        # First try direct send if agent is connected to this instance
        if agent_id in self.active_connections:
            disconnected = []
            for connection_id, websocket in self.active_connections[agent_id].items():
                try:
                    await websocket.send_json(message)
                    success = True
                except Exception as e:
                    logger.error(f"Failed to send to agent {agent_id}: {e}")
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for conn_id in disconnected:
                await self.disconnect(conn_id)
        
        # Also publish to Redis for cross-instance delivery
        await self.redis.publish(
            f"agent_message:{agent_id}",
            json.dumps(message)
        )
        
        return success
    
    async def send_to_user(self, user_id: str, message: Dict) -> bool:
        """Send message to specific user"""
        success = False
        
        # First try direct send if user is connected to this instance
        if user_id in self.active_connections:
            disconnected = []
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_json(message)
                    success = True
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for conn_id in disconnected:
                await self.disconnect(conn_id)
        
        # Also publish to Redis for cross-instance delivery
        await self.redis.publish(
            f"user_message:{user_id}",
            json.dumps(message)
        )
        
        return success
    
    async def broadcast_to_all_agents(self, message: Dict) -> None:
        """Broadcast message to all connected agents"""
        for agent_id in list(self.agent_connections.keys()):
            await self.send_to_agent(agent_id, message)
    
    async def broadcast_to_all_users(self, message: Dict) -> None:
        """Broadcast message to all connected users"""
        for user_id in list(self.user_connections.keys()):
            await self.send_to_user(user_id, message)
    
    async def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register handler for specific message types"""
        self.message_handlers[message_type] = handler
    
    async def handle_message(self, connection_id: str, message: Dict) -> None:
        """Process incoming WebSocket message"""
        try:
            # Get connection metadata
            metadata = self.connection_metadata.get(connection_id)
            if not metadata:
                logger.warning(f"Message from unknown connection: {connection_id}")
                return
            
            entity_id = metadata["entity_id"]
            connection_type = metadata["type"]
            
            # Add metadata to message
            message["_connection_id"] = connection_id
            message["_entity_id"] = entity_id
            message["_type"] = connection_type
            
            # Log message receipt
            logger.debug(f"WebSocket message from {connection_type}={entity_id}: {message.get('type', 'unknown')}")
            
            # Process message based on type
            message_type = message.get("type", "unknown")
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](message)
            else:
                logger.warning(f"No handler for message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def _start_redis_listener(self) -> None:
        """Listen for messages from Redis pubsub"""
        try:
            # Create pubsub connection
            pubsub = self.redis.pubsub()
            
            # Subscribe to relevant channels
            await pubsub.subscribe("broadcast_all")
            await pubsub.psubscribe("agent_message:*")
            await pubsub.psubscribe("user_message:*")
            
            # Start listening
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    try:
                        # Parse message
                        channel = message["channel"].decode()
                        data = json.loads(message["data"].decode())
                        
                        # Process based on channel
                        if channel == "broadcast_all":
                            if data.get("target") == "agents":
                                await self.broadcast_to_all_agents(data["message"])
                            elif data.get("target") == "users":
                                await self.broadcast_to_all_users(data["message"])
                        
                        elif channel.startswith("agent_message:"):
                            agent_id = channel[len("agent_message:"):]
                            if agent_id in self.active_connections:
                                for connection_id, websocket in self.active_connections[agent_id].items():
                                    if self.connection_metadata.get(connection_id, {}).get("type") == "agent":
                                        await websocket.send_json(data)
                        
                        elif channel.startswith("user_message:"):
                            user_id = channel[len("user_message:"):]
                            if user_id in self.active_connections:
                                for connection_id, websocket in self.active_connections[user_id].items():
                                    if self.connection_metadata.get(connection_id, {}).get("type") == "user":
                                        await websocket.send_json(data)
                    
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
                
                # Sleep briefly to reduce CPU usage
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
            # Try to reconnect
            await asyncio.sleep(5)
            asyncio.create_task(self._start_redis_listener())