"""
Communication Agent - Handles inter-agent messaging with NATS JetStream support
"""
from typing import Any, Dict, Optional, List
import asyncio
import json
from datetime import datetime, timezone

from base_agent import BaseAgent, MessageType
from logger import logger

try:
    import nats
    from nats.js import JetStreamContext
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    logger.warning("NATS library not available. Using fallback messaging.")


class CommunicationAgent(BaseAgent):
    """
    Agent responsible for managing inter-agent communication.
    Handles message routing, delivery, and queuing with NATS JetStream support.
    
    Features:
    - Guaranteed message delivery with JetStream
    - Message persistence and replay
    - At-least-once delivery semantics
    - Message acknowledgment
    - Dead letter queue for failed messages
    """
    
    def __init__(self, agent_id: str = "communication_agent", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.message_broker: Dict[str, asyncio.Queue] = {}
        self.message_history: List[Dict[str, Any]] = []
        
        # NATS JetStream configuration
        self.nats_client = None
        self.jetstream: Optional[JetStreamContext] = None
        self.nats_servers = config.get("nats_servers", ["nats://localhost:4222"]) if config else ["nats://localhost:4222"]
        self.stream_name = config.get("stream_name", "AGENT_MESSAGES") if config else "AGENT_MESSAGES"
        self.use_jetstream = config.get("use_jetstream", NATS_AVAILABLE) if config else NATS_AVAILABLE
        
        # Message tracking
        self.pending_acks: Dict[str, Dict[str, Any]] = {}
        self.failed_messages: List[Dict[str, Any]] = []
        
    async def initialize(self) -> bool:
        """Initialize communication agent with NATS JetStream"""
        try:
            self.logger.info("Initializing Communication Agent")
            
            if self.use_jetstream and NATS_AVAILABLE:
                await self._initialize_nats_jetstream()
            else:
                self.logger.info("Using in-memory message broker")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}", exc_info=True)
            # Fall back to in-memory broker
            self.use_jetstream = False
            return True
    
    async def _initialize_nats_jetstream(self) -> None:
        """Initialize NATS JetStream connection"""
        try:
            self.logger.info(f"Connecting to NATS servers: {self.nats_servers}")
            
            # Connect to NATS with timeout
            self.nats_client = await asyncio.wait_for(
                nats.connect(
                    servers=self.nats_servers,
                    max_reconnect_attempts=2,
                    reconnect_time_wait=1
                ),
                timeout=3.0  # 3 second timeout
            )
            
            # Get JetStream context
            self.jetstream = self.nats_client.jetstream()
            
            # Create or get stream
            try:
                await self.jetstream.add_stream(
                    name=self.stream_name,
                    subjects=[f"{self.stream_name}.>"],
                    retention="limits",  # Retain based on limits
                    max_msgs=100000,     # Max messages
                    max_age=86400,       # 24 hours retention
                    storage="file"       # Persistent storage
                )
                self.logger.info(f"JetStream stream '{self.stream_name}' created/verified")
            except Exception as e:
                # Stream might already exist
                self.logger.info(f"JetStream stream exists or error: {e}")
            
            # Subscribe to agent messages
            await self._subscribe_to_messages()
            
        except asyncio.TimeoutError:
            self.logger.warning("NATS connection timeout - falling back to in-memory mode")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize JetStream: {e}", exc_info=True)
            raise
    
    async def _subscribe_to_messages(self) -> None:
        """Subscribe to JetStream messages"""
        try:
            subject = f"{self.stream_name}.*"
            
            # Create durable consumer
            await self.jetstream.subscribe(
                subject=subject,
                cb=self._handle_jetstream_message,
                durable="agent_comm_consumer"
            )
            
            self.logger.info(f"Subscribed to JetStream subject: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to messages: {e}", exc_info=True)
    
    async def _handle_jetstream_message(self, msg) -> None:
        """Handle incoming JetStream message"""
        try:
            # Decode message
            message_data = json.loads(msg.data.decode())
            
            # Process message
            await self._route_message(message_data)
            
            # Acknowledge message
            await msg.ack()
            
        except Exception as e:
            self.logger.error(f"Error handling JetStream message: {e}", exc_info=True)
            # Negative acknowledgment - message will be redelivered
            await msg.nak()
    
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
            
            # Add message ID if not present
            if "message_id" not in message:
                message["message_id"] = f"msg_{len(self.message_history) + 1}"
            
            # Add timestamp
            message["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Store in history
            self.message_history.append(message)
            
            # Route message
            if self.use_jetstream and self.jetstream:
                return await self._publish_to_jetstream(message)
            else:
                return await self._route_message(message)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            self.failed_messages.append({
                "message": message,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _publish_to_jetstream(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Publish message to JetStream for guaranteed delivery"""
        try:
            target = message.get("to", "broadcast")
            subject = f"{self.stream_name}.{target}"
            
            # Publish to JetStream
            ack = await self.jetstream.publish(
                subject=subject,
                payload=json.dumps(message).encode()
            )
            
            self.logger.debug(f"Message published to JetStream: {ack.seq}")
            
            return {
                "status": "published",
                "message_id": message["message_id"],
                "sequence": ack.seq,
                "stream": ack.stream
            }
            
        except Exception as e:
            self.logger.error(f"Failed to publish to JetStream: {e}", exc_info=True)
            # Fall back to direct routing
            return await self._route_message(message)
    
    async def _route_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route message directly to target agent (in-memory)"""
        try:
            target = message.get("to")
            
            if target and target in self.message_broker:
                await self.message_broker[target].put(message)
                return {
                    "status": "delivered",
                    "message_id": message.get("message_id", "unknown")
                }
            elif not target:
                # Broadcast to all registered agents
                for agent_queue in self.message_broker.values():
                    await agent_queue.put(message)
                return {
                    "status": "broadcast",
                    "message_id": message.get("message_id", "unknown"),
                    "recipients": len(self.message_broker)
                }
            else:
                return {
                    "status": "error",
                    "error": f"Target agent not found: {target}"
                }
                
        except Exception as e:
            self.logger.error(f"Error routing message: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def execute(self) -> Any:
        """Execute communication agent main loop"""
        # Monitor message queues and handle routing
        # Clean up old message history (keep last 1000)
        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-1000:]
        
        # Clean up old failed messages (keep last 100)
        if len(self.failed_messages) > 100:
            self.failed_messages = self.failed_messages[-100:]
        
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
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.nats_client:
            await self.nats_client.close()
            self.logger.info("NATS connection closed")
    
    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self.message_history)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get communication statistics"""
        return {
            "agent_id": self.agent_id,
            "total_messages": len(self.message_history),
            "failed_messages": len(self.failed_messages),
            "registered_agents": len(self.message_broker),
            "use_jetstream": self.use_jetstream,
            "jetstream_connected": self.jetstream is not None
        }
    
    async def get_checkpoint_state(self) -> Dict[str, Any]:
        """Save custom state for checkpointing"""
        return {
            "message_history_count": len(self.message_history),
            "failed_messages": self.failed_messages[-10:],  # Keep last 10
            "registered_agents": list(self.message_broker.keys())
        }
    
    async def restore_checkpoint_state(self, state: Dict[str, Any]) -> None:
        """Restore custom state from checkpoint"""
        self.failed_messages = state.get("failed_messages", [])
        # Re-register agents
        for agent_id in state.get("registered_agents", []):
            await self.register_agent(agent_id)
