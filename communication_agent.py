
"""
Communication and Coordination Agent - Complete Implementation
Advanced inter-agent communication, message routing, and coordination
"""

import asyncio
import json
import time
import re
import hashlib
import zlib
import ast  # Added for safe evaluation
import traceback # Added for detailed error logging
import os # Added for environment variables
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from dataclasses import dataclass, field, asdict # Added asdict for easier serialization
from enum import Enum
from collections import defaultdict, deque
import uuid

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus, TaskStatus # Added TaskStatus
from opentelemetry import trace

class MessageType(Enum):
    DIRECT = "direct"
    BROADCAST = "broadcast" 
    MULTICAST = "multicast"
    PUBLISH = "publish"
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    COMMAND = "command"

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class DeliveryMode(Enum):
    FIRE_AND_FORGET = "fire_and_forget"
    ACKNOWLEDGMENT = "acknowledgment"
    RELIABLE = "reliable"
    TRANSACTIONAL = "transactional"

@dataclass
class Message:
    id: str
    type: MessageType
    priority: MessagePriority
    sender: str
    recipients: List[str]
    subject: str
    payload: Dict[str, Any]
    delivery_mode: DeliveryMode = DeliveryMode.FIRE_AND_FORGET
    ttl_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MessageRoute:
    pattern: str
    target_agents: List[str]
    transformation: Optional[str] = None
    filter_condition: Optional[str] = None
    priority: int = 0

@dataclass
class ConversationContext:
    id: str
    participants: Set[str]
    topic: str
    created_at: float
    last_activity: float
    messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class CommunicationAgent(BaseAgent):
    """
    Communication and Coordination Agent providing:
    - Advanced message routing and delivery
    - Inter-agent communication protocols
    - Conversation management and context tracking
    - Message transformation and filtering
    - Reliable delivery with retry mechanisms
    - Broadcast and multicast capabilities
    - Event-driven communication patterns
    - Message queuing and buffering
    - Communication analytics and monitoring
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Message routing and delivery
        self.message_routes: List[MessageRoute] = []
        self.message_queue: Dict[str, deque] = defaultdict(deque)
        self.pending_messages: Dict[str, Message] = {}
        self.message_history = deque(maxlen=10000)
        
        # Agent directory and presence
        self.agent_directory: Dict[str, Dict] = {}
        self.agent_presence: Dict[str, Dict] = {}
        self.agent_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Conversation management
        self.conversations: Dict[str, ConversationContext] = {}
        self.conversation_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Message transformation and filtering
        self.message_transformers: Dict[str, callable] = {}
        self.message_filters: Dict[str, callable] = {}
        
        # Delivery tracking
        self.delivery_receipts: Dict[str, Dict] = {}
        self.failed_deliveries: Dict[str, List[Dict]] = defaultdict(list)
        
        # Communication patterns
        self.communication_patterns = {
            'request_response': {},
            'publish_subscribe': defaultdict(set),
            'message_queue': defaultdict(deque),
            'event_stream': {}
        }
        
        # Rate limiting
        self._rate_limits = defaultdict(deque)
        
        # Performance metrics
        self.communication_metrics = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_failed': 0,
            'average_delivery_time': 0.0,
            'active_conversations': 0,
            'bytes_transferred': 0
        }
        
        # Load communication protocols
        self._load_communication_protocols()
        
        # Initialize message transformers
        self._register_default_transformers()
    
    async def start(self):
        """Start communication agent services"""
        
        # Core communication endpoints - these are now handled via _execute_task_impl
        # The BaseAgent already subscribes to agent.{self.config.name}.task
        
        # Specialized communication endpoints (can be called via _execute_task_impl)
        await self._subscribe(
            "communication.register",
            self._handle_agent_registration
        )
        
        await self._subscribe(
            "communication.subscribe",
            self._handle_subscription
        )
        
        await self._subscribe(
            "communication.conversation.start",
            self._handle_start_conversation
        )
        
        await self._subscribe(
            "communication.route.add",
            self._handle_add_route
        )
        
        # Delivery and acknowledgment handling
        await self._subscribe(
            "communication.ack",
            self._handle_acknowledgment
        )
        
        await self._subscribe(
            "communication.delivery_receipt",
            self._handle_delivery_receipt
        )
        
        # Agent presence monitoring
        await self._subscribe(
            "agent.presence.update",
            self._handle_presence_update
        )
        
        # Background tasks
        asyncio.create_task(self._message_delivery_loop())
        asyncio.create_task(self._retry_failed_messages())
        asyncio.create_task(self._cleanup_expired_messages())
        # Removed _update_communication_metrics as BaseAgent handles metrics publishing
        asyncio.create_task(self._monitor_conversations())
        
        self.logger.info("Communication Agent started")
    
    def _load_communication_protocols(self):
        """Load communication protocol configurations"""
        
        # Default routing patterns
        default_routes = [
            MessageRoute(
                pattern="task.*",
                target_agents=["orchestrator"],
                priority=10
            ),
            MessageRoute(
                pattern="alert.*",
                target_agents=["monitoring", "health"],
                priority=20
            ),
            MessageRoute(
                pattern="llm.*",
                target_agents=["llm_agent"],
                priority=15 # Changed from llm_manager to llm_agent
            ),
            MessageRoute(
                pattern="validation.*",
                target_agents=["validation"],
                priority=12
            )
        ]
        
        self.message_routes.extend(default_routes)
        
        # Sort routes by priority
        self.message_routes.sort(key=lambda x: x.priority, reverse=True)
    
    def _register_default_transformers(self):
        """Register default message transformers"""
        
        self.message_transformers.update({
            'json_to_string': lambda payload: json.dumps(payload),
            'string_to_json': lambda payload: json.loads(payload) if isinstance(payload, str) else payload,
            'add_timestamp': lambda payload: {**payload, 'processed_at': time.time()},
            'add_correlation_id': lambda payload: {**payload, 'correlation_id': str(uuid.uuid4())},
            'sanitize_payload': self._sanitize_message_payload,
            'compress_payload': self._compress_message_payload
        })
        
        self.message_filters.update({
            'priority_filter': self._priority_filter,
            'agent_availability_filter': self._agent_availability_filter,
            'message_size_filter': self._message_size_filter,
            'rate_limit_filter': self._rate_limit_filter
        })
    
    def _sanitize_message_payload(self, payload: Dict) -> Dict:
        """Sanitize message payload for security"""
        sanitized = {}
        
        for key, value in payload.items():
            # Remove potentially dangerous keys
            if key.startswith('_') or key in ['eval', 'exec', '__']:
                continue
                
            # Sanitize string values
            if isinstance(value, str):
                # Basic XSS prevention
                value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
                value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
                
            sanitized[key] = value
        
        return sanitized
    
    def _compress_message_payload(self, payload: Dict) -> Dict:
        """Compress large message payloads"""
        payload_str = json.dumps(payload)
        
        # Only compress if payload is larger than 1KB
        if len(payload_str.encode()) > 1024:
            compressed = zlib.compress(payload_str.encode())
            return {
                '_compressed': True,
                '_data': compressed.hex()
            }
        
        return payload
    
    def _decompress_payload(self, payload: Dict) -> Dict:
        """Decompress compressed payload"""
        if payload.get('_compressed'):
            compressed_data = bytes.fromhex(payload['_data'])
            decompressed = zlib.decompress(compressed_data)
            return json.loads(decompressed.decode())
        
        return payload
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Implement the actual task logic for the Communication agent"""
        task_type = request.task_type
        payload = request.payload

        try:
            result: Dict[str, Any] = {}
            if task_type == "send_message":
                result = await self._send_message_task(payload)
            elif task_type == "broadcast_message":
                result = await self._broadcast_message_task(payload)
            elif task_type == "multicast_message":
                result = await self._multicast_message_task(payload)
            elif task_type == "request_response":
                result = await self._request_response_task(payload)
            elif task_type == "publish_event":
                result = await self._publish_event_task(payload)
            else:
                raise ValueError(f"Unknown communication task type: {task_type}")
            
            return TaskResponse(task_id=request.task_id, status=TaskStatus.COMPLETED, result=result).dict()

        except Exception as e:
            self.logger.error(f"Error executing communication task {task_type}", error=str(e), traceback=traceback.format_exc())
            return TaskResponse(task_id=request.task_id, status=TaskStatus.FAILED, error=str(e)).dict()

    async def _send_message_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to handle sending a direct message"""
        message = Message(
            id=payload.get('id', str(uuid.uuid4())),
            type=MessageType(payload.get('type', 'direct')),
            priority=MessagePriority(payload.get('priority', 2)),  # NORMAL
            sender=payload['sender'],
            recipients=payload['recipients'],
            subject=payload['subject'],
            payload=payload['payload'],
            delivery_mode=DeliveryMode(payload.get('delivery_mode', 'fire_and_forget')),
            ttl_seconds=payload.get('ttl_seconds', 300),
            max_retries=payload.get('max_retries', 3),
            metadata=payload.get('metadata', {})
        )
        result = await self._process_and_route_message(message)
        self.communication_metrics['messages_sent'] += 1
        return result

    async def _broadcast_message_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to handle broadcasting a message"""
        recipients = []
        if 'target_groups' in payload:
            for group in payload['target_groups']:
                recipients.extend(self._get_agents_by_group(group))
        else:
            recipients = list(self.agent_directory.keys())
        
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.BROADCAST,
            priority=MessagePriority(payload.get('priority', 2)),
            sender=payload['sender'],
            recipients=recipients,
            subject=payload['subject'],
            payload=payload['payload'],
            delivery_mode=DeliveryMode(payload.get('delivery_mode', 'fire_and_forget')),
            metadata=payload.get('metadata', {})
        )
        result = await self._process_and_route_message(message)
        self.communication_metrics['messages_sent'] += 1
        return result

    async def _multicast_message_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to handle multicasting a message to specific groups"""
        target_groups = payload.get('target_groups', [])
        if not target_groups:
            raise ValueError("Multicast message requires 'target_groups'.")
        
        recipients = []
        for group in target_groups:
            recipients.extend(self._get_agents_by_group(group))
        recipients = list(set(recipients)) # Remove duplicates

        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.MULTICAST,
            priority=MessagePriority(payload.get('priority', 2)),
            sender=payload['sender'],
            recipients=recipients,
            subject=payload['subject'],
            payload=payload['payload'],
            delivery_mode=DeliveryMode(payload.get('delivery_mode', 'fire_and_forget')),
            metadata=payload.get('metadata', {})
        )
        result = await self._process_and_route_message(message)
        self.communication_metrics['messages_sent'] += 1
        return result

    async def _request_response_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to handle a request-response pattern"""
        sender = payload['sender']
        recipient = payload['recipient']
        subject = payload['subject']
        request_payload = payload['payload']
        timeout = payload.get('timeout', 10) # seconds

        request_message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.REQUEST,
            priority=MessagePriority.HIGH,
            sender=sender,
            recipients=[recipient],
            subject=subject,
            payload=request_payload,
            delivery_mode=DeliveryMode.ACKNOWLEDGMENT,
            ttl_seconds=timeout
        )

        # Publish the request and wait for a response
        response_subject = f"communication.response.{request_message.id}"
        response_future = asyncio.Future()
        self.pending_messages[request_message.id] = response_future # Store future to resolve later

        await self._process_and_route_message(request_message)
        self.communication_metrics['messages_sent'] += 1

        try:
            response_message = await asyncio.wait_for(response_future, timeout=timeout)
            return {"status": "success", "response": response_message.payload}
        except asyncio.TimeoutError:
            self.logger.warning(f"Request-response timed out for message {request_message.id}")
            return {"status": "timeout", "error": "Recipient did not respond in time."}
        finally:
            if request_message.id in self.pending_messages:
                del self.pending_messages[request_message.id]

    async def _publish_event_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to handle publishing an event"""
        subject = payload['subject']
        event_payload = payload['payload']
        sender = payload.get('sender', self.config.name)

        event_message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.EVENT,
            priority=MessagePriority.NORMAL,
            sender=sender,
            recipients=[], # Events are broadcast to subscribers, not direct recipients
            subject=subject,
            payload=event_payload,
            delivery_mode=DeliveryMode.FIRE_AND_FORGET,
            metadata=payload.get('metadata', {})
        )
        # Events are published directly to NATS subject, not routed via _process_and_route_message
        await self._publish(subject, json.dumps(asdict(event_message)).encode())
        self.communication_metrics['messages_sent'] += 1
        return {"status": "event_published", "message_id": event_message.id}

    async def _process_and_route_message(self, message: Message) -> Dict[str, Any]:
        """Apply transformations, filters, and route the message to appropriate agents"""
        processed_payload = message.payload
        
        # Apply transformations
        for transformer_name in message.metadata.get("transformers", []):
            if transformer_name in self.message_transformers:
                processed_payload = self.message_transformers[transformer_name](processed_payload)
            else:
                self.logger.warning(f"Unknown transformer: {transformer_name}")
        
        # Apply filters
        for filter_name in message.metadata.get("filters", []):
            if filter_name in self.message_filters:
                if not self.message_filters[filter_name](message, processed_payload):
                    self.logger.info(f"Message {message.id} filtered out by {filter_name}")
                    return {"status": "filtered", "message_id": message.id}
            else:
                self.logger.warning(f"Unknown filter: {filter_name}")

        message.payload = processed_payload # Update message with processed payload

        # Determine recipients based on message type and routing rules
        actual_recipients = set()
        if message.type == MessageType.DIRECT:
            actual_recipients.update(message.recipients)
        elif message.type == MessageType.BROADCAST:
            actual_recipients.update(self.agent_directory.keys())
        elif message.type == MessageType.MULTICAST:
            actual_recipients.update(message.recipients) # Recipients already determined by _multicast_message_task
        elif message.type == MessageType.PUBLISH or message.type == MessageType.EVENT:
            # For PUBLISH/EVENT, recipients are determined by subscriptions
            # This is handled by NATS itself, so we just publish to the subject
            pass
        elif message.type == MessageType.REQUEST:
            actual_recipients.update(message.recipients)
        
        # Apply routing rules for additional recipients or subject modification
        for route in self.message_routes:
            if re.fullmatch(route.pattern, message.subject):
                if route.filter_condition:
                    # Use safe evaluation instead of eval()
                    # For now, skip complex filter conditions to avoid security risk
                    # TODO: Implement a proper expression evaluator or use a safe subset
                    try:
                        # Only allow simple literal comparisons for security
                        # Complex filtering should be done with proper expression parser
                        self.logger.warning(f"Filter condition skipped for security (use literal comparisons): {route.filter_condition}")
                        continue
                    except Exception as e:
                        self.logger.error(f"Error evaluating route filter condition for {message.id}: {e}")
                        continue
                
                actual_recipients.update(route.target_agents)
                if route.transformation == "enrich_subject":
                    message.subject = f"[Routed] {message.subject}"

        # Remove sender from recipients for direct/broadcast/multicast to avoid self-delivery unless intended
        if message.type in [MessageType.DIRECT, MessageType.BROADCAST, MessageType.MULTICAST]:
            if message.sender in actual_recipients:
                actual_recipients.remove(message.sender)

        # Enqueue or send message to each recipient
        if message.type in [MessageType.DIRECT, MessageType.BROADCAST, MessageType.MULTICAST, MessageType.REQUEST]:
            for recipient in actual_recipients:
                if recipient in self.agent_presence and self.agent_presence[recipient].get("status") == AgentStatus.ACTIVE.value:
                    await self._send_to_agent(recipient, message)
                else:
                    self.logger.warning(f"Recipient {recipient} not active or found. Enqueuing message {message.id}.")
                    self.message_queue[recipient].append(message)
                    # Store message in pending for retry
                    self.pending_messages[message.id] = message
        elif message.type in [MessageType.PUBLISH, MessageType.EVENT]:
            # For publish/event, the message is already published to NATS subject in _publish_event_task
            pass

        self.message_history.append(asdict(message))
        return {"status": "processed", "message_id": message.id, "recipients": list(actual_recipients)}

    async def _send_to_agent(self, recipient_agent_name: str, message: Message):
        """Send a message to a specific agent via NATS"""
        subject = f"agent.{recipient_agent_name}.inbox"
        try:
            # If it's a request, we need to publish with a reply-to subject
            if message.type == MessageType.REQUEST:
                reply_to_subject = f"communication.response.{message.id}"
                await self._publish_request(subject, json.dumps(asdict(message)).encode(), reply_to_subject)
            else:
                await self._publish(subject, json.dumps(asdict(message)).encode())
            
            self.logger.debug(f"Message {message.id} sent to {recipient_agent_name}")
            self.communication_metrics['messages_delivered'] += 1
            self.communication_metrics['bytes_transferred'] += len(json.dumps(asdict(message)).encode())
            
            # If delivery mode is ACK, expect an acknowledgment
            if message.delivery_mode == DeliveryMode.ACKNOWLEDGMENT:
                self.delivery_receipts[message.id] = {"status": "pending_ack", "timestamp": time.time(), "recipient": recipient_agent_name}
            
            # Remove from pending messages if successfully sent and not awaiting ACK
            if message.id in self.pending_messages and message.delivery_mode != DeliveryMode.ACKNOWLEDGMENT:
                del self.pending_messages[message.id]

        except Exception as e:
            self.logger.error(f"Failed to send message {message.id} to {recipient_agent_name}: {e}", traceback=traceback.format_exc())
            self.communication_metrics['messages_failed'] += 1
            self.failed_deliveries[message.id].append({"timestamp": time.time(), "error": str(e), "recipient": recipient_agent_name})
            # Re-enqueue for retry if max_retries not exceeded
            if message.retry_count < message.max_retries:
                message.retry_count += 1
                self.message_queue[recipient_agent_name].appendleft(message) # Add to front for quicker retry
            else:
                self.logger.error(f"Message {message.id} failed after {message.max_retries} retries.")
                if message.id in self.pending_messages:
                    del self.pending_messages[message.id]

    async def _message_delivery_loop(self):
        """Background task to continuously deliver messages from queues"""
        while not self._shutdown_event.is_set():
            try:
                for agent_name, queue in list(self.message_queue.items()):
                    if self.agent_presence.get(agent_name, {}).get("status") == AgentStatus.ACTIVE.value:
                        while queue:
                            message = queue.popleft()
                            self.logger.debug(f"Attempting to deliver enqueued message {message.id} to {agent_name}")
                            await self._send_to_agent(agent_name, message)
                            await asyncio.sleep(0.01) # Small delay to prevent overwhelming NATS
                    else:
                        self.logger.debug(f"Agent {agent_name} not active, holding messages in queue.")
                await asyncio.sleep(1) # Check queues every second
            except Exception as e:
                self.logger.error(f"Message delivery loop failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(5)

    async def _retry_failed_messages(self):
        """Background task to retry messages that failed delivery or are pending ACK"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                retry_interval = 5 # seconds
                ack_timeout = 30 # seconds

                messages_to_retry = []
                for msg_id, message in list(self.pending_messages.items()):
                    if isinstance(message, Message): # Ensure it's a Message object, not a Future
                        # Check for messages that failed and need retry
                        if message.retry_count < message.max_retries and \
                           (current_time - message.created_at > retry_interval * (message.retry_count + 1)):
                            messages_to_retry.append(message)
                        
                        # Check for messages pending ACK that have timed out
                        if message.delivery_mode == DeliveryMode.ACKNOWLEDGMENT and \
                           msg_id in self.delivery_receipts and \
                           self.delivery_receipts[msg_id]["status"] == "pending_ack" and \
                           (current_time - self.delivery_receipts[msg_id]["timestamp"] > ack_timeout):
                            self.logger.warning(f"Message {msg_id} ACK timed out. Retrying.")
                            messages_to_retry.append(message)

                for message in messages_to_retry:
                    self.logger.info(f"Retrying message {message.id} (attempt {message.retry_count + 1}/{message.max_retries})")
                    # Re-add to queue for delivery attempt
                    for recipient in message.recipients:
                        self.message_queue[recipient].appendleft(message) # Add to front for quicker retry
                    # Update retry count, will be removed from pending_messages on successful send
                    message.retry_count += 1
                    if message.id in self.delivery_receipts:
                        self.delivery_receipts[message.id]["status"] = "retrying"

                await asyncio.sleep(retry_interval) # Check every few seconds
            except Exception as e:
                self.logger.error(f"Retry failed messages loop failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(10)

    async def _cleanup_expired_messages(self):
        """Background task to clean up messages that have exceeded their TTL"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                expired_message_ids = []
                for msg_id, message in list(self.pending_messages.items()):
                    if isinstance(message, Message) and (current_time - message.created_at > message.ttl_seconds):
                        expired_message_ids.append(msg_id)
                        self.logger.warning(f"Message {msg_id} expired (TTL exceeded).")
                
                for msg_id in expired_message_ids:
                    if msg_id in self.pending_messages:
                        del self.pending_messages[msg_id]
                    if msg_id in self.delivery_receipts:
                        del self.delivery_receipts[msg_id]
                    # Also remove from queues if present
                    for queue in self.message_queue.values():
                        # This is inefficient, consider a better data structure if queues are very large
                        for i in range(len(queue) - 1, -1, -1):
                            if queue[i].id == msg_id:
                                del queue[i]

                # Clean up message history (already handled by deque maxlen)
                
                await asyncio.sleep(60) # Check for expired messages every minute
            except Exception as e:
                self.logger.error(f"Cleanup expired messages loop failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(300)

    async def _monitor_conversations(self):
        """Background task to monitor and clean up old conversations"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                conversation_timeout = 3600 * 24 * 7 # 7 days
                
                conversations_to_remove = []
                for conv_id, conv in self.conversations.items():
                    if current_time - conv.last_activity > conversation_timeout:
                        conversations_to_remove.append(conv_id)
                
                for conv_id in conversations_to_remove:
                    del self.conversations[conv_id]
                    # Clean up index entries as well
                    for agent_name in list(self.conversation_index.keys()):
                        if conv_id in self.conversation_index[agent_name]:
                            self.conversation_index[agent_name].remove(conv_id)
                            if not self.conversation_index[agent_name]:
                                del self.conversation_index[agent_name]
                    self.logger.info("Cleaned up stale conversation", conversation_id=conv_id)
                
                self.communication_metrics['active_conversations'] = len(self.conversations)
                await asyncio.sleep(3600) # Check every hour
            except Exception as e:
                self.logger.error(f"Conversation monitor failed: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(300)

    async def _handle_agent_registration(self, msg):
        """Handle agent registration messages"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data["agent_name"]
            agent_type = data["agent_type"]
            capabilities = data.get("capabilities", [])
            status = data.get("status", AgentStatus.ACTIVE.value)
            
            self.agent_directory[agent_name] = {
                "agent_type": agent_type,
                "capabilities": capabilities,
                "last_seen": time.time()
            }
            self.agent_presence[agent_name] = {
                "status": status,
                "last_update": time.time()
            }
            self.logger.info("Agent registered", agent_name=agent_name, agent_type=agent_type)
            
            # Respond to registration request
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"status": "registered", "agent_name": agent_name}).encode())
        except Exception as e:
            self.logger.error("Error handling agent registration", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_subscription(self, msg):
        """Handle agent subscription to topics"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data["agent_name"]
            topic = data["topic"]
            
            self.agent_subscriptions[agent_name].add(topic)
            self.logger.info("Agent subscribed", agent_name=agent_name, topic=topic)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"status": "subscribed", "agent_name": agent_name, "topic": topic}).encode())
        except Exception as e:
            self.logger.error("Error handling subscription", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_start_conversation(self, msg):
        """Handle request to start a new conversation"""
        try:
            data = json.loads(msg.data.decode())
            participants = set(data["participants"])
            topic = data.get("topic", "general")
            metadata = data.get("metadata", {})

            conv_id = str(uuid.uuid4())
            conversation = ConversationContext(
                id=conv_id,
                participants=participants,
                topic=topic,
                created_at=time.time(),
                last_activity=time.time(),
                metadata=metadata
            )
            self.conversations[conv_id] = conversation
            for participant in participants:
                self.conversation_index[participant].add(conv_id)
            
            self.logger.info("Conversation started", conversation_id=conv_id, participants=list(participants))
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"status": "conversation_started", "conversation_id": conv_id}).encode())
        except Exception as e:
            self.logger.error("Error starting conversation", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_add_route(self, msg):
        """Handle request to add a new message routing rule"""
        try:
            data = json.loads(msg.data.decode())
            route = MessageRoute(**data)
            self.message_routes.append(route)
            self.message_routes.sort(key=lambda x: x.priority, reverse=True) # Re-sort by priority
            self.logger.info("Added new message route", pattern=route.pattern, target_agents=route.target_agents)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"status": "route_added", "pattern": route.pattern}).encode())
        except Exception as e:
            self.logger.error("Error adding route", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({"error": str(e), "success": False}).encode())

    async def _handle_acknowledgment(self, msg):
        """Handle message acknowledgments"""
        try:
            data = json.loads(msg.data.decode())
            original_message_id = data["original_message_id"]
            sender_agent = data["sender_agent"]
            status = data.get("status", "received")

            if original_message_id in self.delivery_receipts:
                self.delivery_receipts[original_message_id]["status"] = status
                self.delivery_receipts[original_message_id]["ack_timestamp"] = time.time()
                self.logger.debug(f"Received ACK for message {original_message_id} from {sender_agent} with status {status}")
                
                # If it was a request-response, resolve the future
                if original_message_id in self.pending_messages and isinstance(self.pending_messages[original_message_id], asyncio.Future):
                    # The ACK might not contain the full response, so we need to wait for the actual response message
                    # This ACK just confirms delivery. The actual response will be handled by _handle_response_message
                    pass # Do nothing here, actual response will resolve the future
                elif original_message_id in self.pending_messages:
                    # For non-request-response messages with ACK, remove from pending
                    del self.pending_messages[original_message_id]
            else:
                self.logger.warning(f"Received ACK for unknown or expired message {original_message_id}")
        except Exception as e:
            self.logger.error("Error handling acknowledgment", error=str(e), traceback=traceback.format_exc())

    async def _handle_delivery_receipt(self, msg):
        """Handle delivery receipts (more detailed than simple ACK)"""
        try:
            data = json.loads(msg.data.decode())
            original_message_id = data["original_message_id"]
            recipient_agent = data["recipient_agent"]
            delivery_status = data["delivery_status"] # e.g., "delivered", "read", "processed"
            
            if original_message_id in self.delivery_receipts:
                self.delivery_receipts[original_message_id]["delivery_status"] = delivery_status
                self.delivery_receipts[original_message_id]["delivery_timestamp"] = time.time()
                self.logger.debug(f"Received delivery receipt for message {original_message_id} to {recipient_agent}: {delivery_status}")
            else:
                self.logger.warning(f"Received delivery receipt for unknown or expired message {original_message_id}")
        except Exception as e:
            self.logger.error("Error handling delivery receipt", error=str(e), traceback=traceback.format_exc())

    async def _handle_presence_update(self, msg):
        """Handle agent presence updates"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data["agent_name"]
            status = data["status"]
            
            if agent_name in self.agent_presence:
                self.agent_presence[agent_name]["status"] = status
                self.agent_presence[agent_name]["last_update"] = time.time()
                self.logger.info("Agent presence updated", agent_name=agent_name, status=status)
                
                # If agent becomes active, try to deliver queued messages
                if status == AgentStatus.ACTIVE.value and agent_name in self.message_queue:
                    self.logger.info(f"Agent {agent_name} is now active, attempting to deliver queued messages.")
                    # The _message_delivery_loop will pick this up, no need to explicitly trigger here
            else:
                self.logger.warning(f"Presence update for unknown agent {agent_name}")
        except Exception as e:
            self.logger.error("Error handling presence update", error=str(e), traceback=traceback.format_exc())

    def _get_agents_by_group(self, group_name: str) -> List[str]:
        """Helper to get agents belonging to a certain group/type"""
        # This is a placeholder. In a real system, groups could be defined in Consul or a config service.
        if group_name == "llm_agents":
            return [name for name, info in self.agent_directory.items() if info.get("agent_type") == "llm"]
        elif group_name == "all":
            return list(self.agent_directory.keys())
        # Add more group logic as needed
        return []

    def _priority_filter(self, message: Message, payload: Dict) -> bool:
        """Filter messages based on priority"""
        min_priority = payload.get("min_priority", MessagePriority.LOW.value)
        return message.priority.value >= min_priority

    def _agent_availability_filter(self, message: Message, payload: Dict) -> bool:
        """Filter messages if recipient agent is not available"""
        for recipient in message.recipients:
            if recipient not in self.agent_presence or self.agent_presence[recipient].get("status") != AgentStatus.ACTIVE.value:
                return False
        return True

    def _message_size_filter(self, message: Message, payload: Dict) -> bool:
        """Filter messages based on size"""
        max_size_bytes = payload.get("max_size_bytes", 1024 * 1024) # Default 1MB
        current_size = len(json.dumps(asdict(message)).encode())
        if current_size > max_size_bytes:
            self.logger.warning(f"Message {message.id} exceeds max size ({current_size} > {max_size_bytes} bytes).")
            return False
        return True

    def _rate_limit_filter(self, message: Message, payload: Dict) -> bool:
        """Filter messages based on rate limits per sender/recipient"""
        # This is a simple token bucket or sliding window implementation
        # For production, consider a dedicated rate-limiting service
        limit_key = f"{message.sender}-{message.type.value}"
        max_requests = payload.get("max_requests", 10)
        time_window_seconds = payload.get("time_window_seconds", 60)

        current_time = time.time()
        # Clean up old timestamps
        while self._rate_limits[limit_key] and self._rate_limits[limit_key][0] < current_time - time_window_seconds:
            self._rate_limits[limit_key].popleft()
        
        if len(self._rate_limits[limit_key]) >= max_requests:
            self.logger.warning(f"Rate limit exceeded for {limit_key}.")
            return False
        
        self._rate_limits[limit_key].append(current_time)
        return True

    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Provide Communication agent specific metrics."""
        base_metrics = super()._get_agent_metrics()
        base_metrics.update({
            "messages_sent": self.communication_metrics['messages_sent'],
            "messages_delivered": self.communication_metrics['messages_delivered'],
            "messages_failed": self.communication_metrics['messages_failed'],
            "average_delivery_time": self.communication_metrics['average_delivery_time'],
            "active_conversations": self.communication_metrics['active_conversations'],
            "bytes_transferred": self.communication_metrics['bytes_transferred'],
            "queued_messages_count": sum(len(q) for q in self.message_queue.values()),
            "pending_acks_count": len([mid for mid, rec in self.delivery_receipts.items() if rec.get("status") == "pending_ack"])
        })
        return base_metrics


if __name__ == "__main__":
    config = AgentConfig(
        name="communication_agent",
        agent_type="communication",
        capabilities=[
            "send_message", "broadcast_message", "multicast_message",
            "request_response", "publish_event", "manage_routes",
            "manage_conversations", "agent_presence_monitoring"
        ],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = CommunicationAgent(config)
    asyncio.run(agent.run())

