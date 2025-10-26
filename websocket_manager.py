"""
WebSocket Manager
Real-time bidirectional communication for agents and users
"""

import asyncio
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime
from fastapi import WebSocket
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time communication
    
    Features:
    - Project-specific channels
    - Agent communication channels
    - Broadcast capabilities
    - Connection pooling
    - Auto-reconnect handling
    """
    
    def __init__(self, database, agent_orchestrator, log_manager):
        self.database = database
        self.agent_orchestrator = agent_orchestrator
        self.log_manager = log_manager
        
        # Connection tracking
        self.active_connections: Dict[str, WebSocket] = {}
        self.project_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.agent_connections: Dict[str, WebSocket] = {}
        
        # Message queue for offline delivery
        self.pending_messages: Dict[str, list] = defaultdict(list)
        
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize WebSocket manager"""
        self.is_initialized = True
        logger.info("✓ WebSocket manager initialized")
    
    async def connect(self, connection_id: str, websocket: WebSocket):
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        # Send pending messages if any
        if connection_id in self.pending_messages:
            for message in self.pending_messages[connection_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send pending message: {e}")
            
            del self.pending_messages[connection_id]
        
        logger.info(f"WebSocket connected: {connection_id}")
    
    async def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from all subscriptions
        for project_id, connections in self.project_subscriptions.items():
            if connection_id in connections:
                connections.remove(connection_id)
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def subscribe_to_project(self, project_id: str, websocket: WebSocket):
        """Subscribe connection to project updates"""
        connection_id = f"project_{project_id}_{id(websocket)}"
        await self.connect(connection_id, websocket)
        self.project_subscriptions[project_id].add(connection_id)
        
        logger.info(f"Subscribed to project {project_id}: {connection_id}")
    
    async def unsubscribe_from_project(self, project_id: str, websocket: WebSocket):
        """Unsubscribe connection from project updates"""
        connection_id = f"project_{project_id}_{id(websocket)}"
        
        if project_id in self.project_subscriptions:
            self.project_subscriptions[project_id].discard(connection_id)
        
        await self.disconnect(connection_id)
    
    async def register_agent_connection(self, agent_id: str, websocket: WebSocket):
        """Register agent WebSocket connection"""
        await websocket.accept()
        self.agent_connections[agent_id] = websocket
        
        logger.info(f"Agent connected: {agent_id}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                # Queue for later delivery
                self.pending_messages[connection_id].append(message)
        else:
            # Queue for when connection comes online
            self.pending_messages[connection_id].append(message)
    
    async def broadcast_to_project(self, project_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections subscribed to project"""
        if project_id not in self.project_subscriptions:
            return
        
        disconnected = []
        
        for connection_id in self.project_subscriptions[project_id]:
            if connection_id in self.active_connections:
                try:
                    await self.active_connections[connection_id].send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to {connection_id}: {e}")
                    disconnected.append(connection_id)
        
        # Clean up disconnected
        for connection_id in disconnected:
            self.project_subscriptions[project_id].discard(connection_id)
    
    async def send_to_agent(self, agent_id: str, message: Dict[str, Any]):
        """Send message to specific agent"""
        if agent_id in self.agent_connections:
            try:
                await self.agent_connections[agent_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to agent {agent_id}: {e}")
    
    async def broadcast_to_all_agents(self, message: Dict[str, Any]):
        """Broadcast message to all connected agents"""
        disconnected = []
        
        for agent_id, websocket in self.agent_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to agent {agent_id}: {e}")
                disconnected.append(agent_id)
        
        # Clean up disconnected agents
        for agent_id in disconnected:
            del self.agent_connections[agent_id]
    
    async def handle_submission(self, data: Dict[str, Any], websocket: WebSocket):
        """Handle submission received via WebSocket"""
        try:
            # Log submission
            await self.log_manager.log_submission_event(
                submission_id=data.get("submission_id"),
                project_id=data.get("project_id"),
                agent_id=data.get("agent_id"),
                event_type="websocket_submission",
                details=data
            )
            
            # Acknowledge receipt
            await websocket.send_json({
                "type": "submission_acknowledged",
                "submission_id": data.get("submission_id"),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Broadcast to project subscribers
            if data.get("project_id"):
                await self.broadcast_to_project(
                    data["project_id"],
                    {
                        "type": "new_submission",
                        "data": data
                    }
                )
        
        except Exception as e:
            logger.error(f"Failed to handle submission: {e}")
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
    
    async def notify_quality_result(
        self,
        project_id: str,
        submission_id: str,
        quality_score: float,
        status: str,
        issues: list
    ):
        """Notify about quality verification result"""
        message = {
            "type": "quality_result",
            "submission_id": submission_id,
            "quality_score": quality_score,
            "status": status,
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_project(project_id, message)
    
    async def notify_integration_complete(
        self,
        project_id: str,
        submission_id: str,
        result: Dict[str, Any]
    ):
        """Notify about completed integration"""
        message = {
            "type": "integration_complete",
            "submission_id": submission_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_project(project_id, message)
    
    async def notify_build_progress(
        self,
        project_id: str,
        build_id: str,
        progress: float,
        status: str,
        details: Dict[str, Any]
    ):
        """Notify about build progress"""
        message = {
            "type": "build_progress",
            "build_id": build_id,
            "progress": progress,
            "status": status,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_project(project_id, message)
    
    async def health_check(self) -> bool:
        """Check WebSocket manager health"""
        return self.is_initialized
    
    async def shutdown(self):
        """Shutdown WebSocket manager"""
        # Close all connections gracefully
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection {connection_id}: {e}")
        
        for agent_id, websocket in self.agent_connections.items():
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing agent connection {agent_id}: {e}")
        
        logger.info("WebSocket manager shutdown complete")
