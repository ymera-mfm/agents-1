"""
Production-Ready Communication and Coordination Agent
Enterprise-grade inter-agent communication with full error handling and monitoring
Version: 2.0.0
"""

import asyncio
import json
import time
import re
import hashlib
import zlib
import traceback
import os
from typing import Dict, List, Optional, Any, Union, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque, Counter
import uuid
from datetime import datetime, timedelta

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus, TaskStatus
from opentelemetry import trace

# Constants
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_QUEUE_SIZE = 10000
MAX_RETRY_ATTEMPTS = 5
MESSAGE_TTL_SECONDS = 3600
CLEANUP_INTERVAL = 300
RATE_LIMIT_WINDOW = 60
DEFAULT_RATE_LIMIT = 100

class MessageType(Enum):
    """Message types for inter-agent communication"""
    DIRECT = "direct"
    BROADCAST = "broadcast"
    MULTICAST = "multicast"
    PUBLISH = "publish"
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    COMMAND = "command"
    HEARTBEAT = "heartbeat"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class DeliveryMode(Enum):
    """Message delivery modes"""
    FIRE_AND_FORGET = "fire_and_forget"
    ACKNOWLEDGMENT = "acknowledgment"
    RELIABLE = "reliable"
    TRANSACTIONAL = "transactional"

class MessageStatus(Enum):
    """Message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"
    RETRYING = "retrying"

@dataclass
class Message:
    """Enhanced message structure with validation"""
    id: str
    type: MessageType
    priority: MessagePriority
    sender: str
    recipients: List[str]
    subject: str
    payload: Dict[str, Any]
    delivery_mode: DeliveryMode = DeliveryMode.FIRE_AND_FORGET
    ttl_seconds: int = MESSAGE_TTL_SECONDS
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    delivery_attempts: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate message after initialization"""
        if not self.sender or not self.sender.strip():
            raise ValueError("Message sender cannot be empty")
        if not self.recipients and self.type not in [MessageType.BROADCAST, MessageType.PUBLISH]:
            raise ValueError("Message recipients cannot be empty for non-broadcast messages")
        if not self.subject or not self.subject.strip():
            raise ValueError("Message subject cannot be empty")
        if self.ttl_seconds <= 0:
            raise ValueError("TTL must be positive")
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        return time.time() - self.created_at > self.ttl_seconds
    
    def should_retry(self) -> bool:
        """Check if message should be retried"""
        return self.retry_count < self.max_retries and not self.is_expired()
    
    def size_bytes(self) -> int:
        """Calculate message size in bytes"""
        return len(json.dumps(asdict(self)).encode('utf-8'))

@dataclass
class MessageRoute:
    """Message routing rule with enhanced matching"""
    pattern: str
    target_agents: List[str]
    transformation: Optional[str] = None
    filter_condition: Optional[str] = None
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, subject: str) -> bool:
        """Check if route matches subject"""
        if not self.enabled:
            return False
        try:
            return bool(re.fullmatch(self.pattern, subject))
        except re.error as e:
            raise ValueError(f"Invalid route pattern '{self.pattern}': {e}")

@dataclass
class ConversationContext:
    """Enhanced conversation context with participant tracking"""
    id: str
    participants: Set[str]
    topic: str
    created_at: float
    last_activity: float
    messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    message_count: int = 0
    
    def is_active(self, timeout_seconds: int = 3600) -> bool:
        """Check if conversation is still active"""
        return (time.time() - self.last_activity < timeout_seconds and 
                self.status == "active")
    
    def add_message(self, message_id: str):
        """Add message to conversation"""
        self.messages.append(message_id)
        self.message_count += 1
        self.last_activity = time.time()

class CommunicationAgent(BaseAgent):
    """
    Production-Ready Communication Agent with:
    - Enhanced error handling and recovery
    - Comprehensive monitoring and metrics
    - Security features and validation
    - Performance optimizations
    - Database persistence
    - Health checks and diagnostics
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Message routing and delivery
        self.message_routes: List[MessageRoute] = []
        self.message_queue: Dict[str, deque] = defaultdict(lambda: deque(maxlen=MAX_QUEUE_SIZE))
        self.pending_messages: Dict[str, Union[Message, asyncio.Future]] = {}
        self.message_history: deque = deque(maxlen=10000)
        
        # Agent directory and presence
        self.agent_directory: Dict[str, Dict] = {}
        self.agent_presence: Dict[str, Dict] = {}
        self.agent_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.agent_health: Dict[str, Dict] = {}
        
        # Conversation management
        self.conversations: Dict[str, ConversationContext] = {}
        self.conversation_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Message transformation and filtering
        self.message_transformers: Dict[str, Callable] = {}
        self.message_filters: Dict[str, Callable] = {}
        
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
        
        # Rate limiting with token bucket
        self._rate_limits: Dict[str, deque] = defaultdict(deque)
        self._rate_limit_config: Dict[str, Dict] = {}
        
        # Circuit breaker for failing agents
        self._circuit_breakers: Dict[str, Dict] = {}
        
        # Performance metrics (enhanced)
        self.communication_metrics = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_failed': 0,
            'messages_expired': 0,
            'messages_retried': 0,
            'average_delivery_time': 0.0,
            'p95_delivery_time': 0.0,
            'p99_delivery_time': 0.0,
            'active_conversations': 0,
            'bytes_transferred': 0,
            'queue_depth_max': 0,
            'circuit_breakers_open': 0,
            'rate_limit_hits': 0
        }
        
        # Delivery time tracking
        self._delivery_times: deque = deque(maxlen=1000)
        
        # Load communication protocols
        self._load_communication_protocols()
        
        # Initialize message transformers and filters
        self._register_default_transformers()
        
        # Health check status
        self._health_status = {
            'status': 'initializing',
            'last_check': time.time(),
            'issues': []
        }
    
    async def start(self):
        """Start communication agent services with health checks"""
        try:
            # Subscribe to agent registration
            await self._subscribe(
                "communication.register",
                self._handle_agent_registration
            )
            
            # Subscribe to agent subscriptions
            await self._subscribe(
                "communication.subscribe",
                self._handle_subscription
            )
            
            # Subscribe to conversation management
            await self._subscribe(
                "communication.conversation.start",
                self._handle_start_conversation
            )
            
            # Subscribe to route management
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
            
            # Health check endpoint
            await self._subscribe(
                "communication.health",
                self._handle_health_check
            )
            
            # Diagnostics endpoint
            await self._subscribe(
                "communication.diagnostics",
                self._handle_diagnostics
            )
            
            # Background tasks
            asyncio.create_task(self._message_delivery_loop())
            asyncio.create_task(self._retry_failed_messages())
            asyncio.create_task(self._cleanup_expired_messages())
            asyncio.create_task(self._monitor_conversations())
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._circuit_breaker_monitor())
            asyncio.create_task(self._persist_message_history())
            
            self._health_status['status'] = 'healthy'
            self._health_status['last_check'] = time.time()
            
            self.logger.info("Communication Agent started successfully",
                           routes_loaded=len(self.message_routes),
                           transformers=len(self.message_transformers),
                           filters=len(self.message_filters))
            
        except Exception as e:
            self._health_status['status'] = 'unhealthy'
            self._health_status['issues'].append(f"Startup failed: {str(e)}")
            self.logger.error("Failed to start Communication Agent", error=str(e), traceback=traceback.format_exc())
            raise
    
    def _load_communication_protocols(self):
        """Load communication protocol configurations with validation"""
        try:
            default_routes = [
                MessageRoute(
                    pattern=r"task\..*",
                    target_agents=["orchestrator"],
                    priority=10,
                    metadata={"description": "Task routing to orchestrator"}
                ),
                MessageRoute(
                    pattern=r"alert\..*",
                    target_agents=["monitoring", "health"],
                    priority=20,
                    metadata={"description": "Alert routing to monitoring systems"}
                ),
                MessageRoute(
                    pattern=r"llm\..*",
                    target_agents=["llm_agent"],
                    priority=15,
                    metadata={"description": "LLM request routing"}
                ),
                MessageRoute(
                    pattern=r"validation\..*",
                    target_agents=["validation"],
                    priority=12,
                    metadata={"description": "Validation request routing"}
                ),
                MessageRoute(
                    pattern=r"error\..*",
                    target_agents=["monitoring", "logging"],
                    priority=25,
                    metadata={"description": "Error reporting"}
                )
            ]
            
            self.message_routes.extend(default_routes)
            self.message_routes.sort(key=lambda x: x.priority, reverse=True)
            
            self.logger.info("Communication protocols loaded", route_count=len(self.message_routes))
            
        except Exception as e:
            self.logger.error("Failed to load communication protocols", error=str(e))
            raise
    
    def _register_default_transformers(self):
        """Register default message transformers with error handling"""
        try:
            self.message_transformers.update({
                'json_to_string': lambda payload: json.dumps(payload),
                'string_to_json': lambda payload: json.loads(payload) if isinstance(payload, str) else payload,
                'add_timestamp': lambda payload: {**payload, 'processed_at': time.time()},
                'add_correlation_id': lambda payload: {**payload, 'correlation_id': str(uuid.uuid4())},
                'sanitize_payload': self._sanitize_message_payload,
                'compress_payload': self._compress_message_payload,
                'encrypt_payload': self._encrypt_message_payload,
                'validate_schema': self._validate_payload_schema
            })
            
            self.message_filters.update({
                'priority_filter': self._priority_filter,
                'agent_availability_filter': self._agent_availability_filter,
                'message_size_filter': self._message_size_filter,
                'rate_limit_filter': self._rate_limit_filter,
                'security_filter': self._security_filter,
                'duplicate_filter': self._duplicate_filter
            })
            
            self.logger.info("Message transformers and filters registered",
                           transformers=len(self.message_transformers),
                           filters=len(self.message_filters))
            
        except Exception as e:
            self.logger.error("Failed to register transformers", error=str(e))
            raise
    
    def _sanitize_message_payload(self, payload: Dict) -> Dict:
        """Enhanced sanitization with comprehensive security checks"""
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary")
        
        sanitized = {}
        dangerous_keys = {'_', 'eval', 'exec', '__import__', 'compile', 'globals', 'locals'}
        
        for key, value in payload.items():
            # Remove dangerous keys
            if any(dangerous in str(key).lower() for dangerous in dangerous_keys):
                self.logger.warning("Removed dangerous key from payload", key=key)
                continue
            
            # Sanitize string values
            if isinstance(value, str):
                # XSS prevention
                value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
                value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
                value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
                # SQL injection prevention
                value = value.replace("'", "''").replace(";", "")
                # Limit string length
                if len(value) > 10000:
                    value = value[:10000]
            
            # Recursively sanitize nested dicts
            elif isinstance(value, dict):
                value = self._sanitize_message_payload(value)
            
            # Recursively sanitize lists
            elif isinstance(value, list):
                value = [self._sanitize_message_payload(item) if isinstance(item, dict) else item for item in value]
            
            sanitized[key] = value
        
        return sanitized
    
    def _compress_message_payload(self, payload: Dict) -> Dict:
        """Compress large message payloads with error handling"""
        try:
            payload_str = json.dumps(payload)
            payload_bytes = payload_str.encode('utf-8')
            
            # Only compress if payload is larger than 1KB
            if len(payload_bytes) > 1024:
                compressed = zlib.compress(payload_bytes, level=6)
                compression_ratio = len(compressed) / len(payload_bytes)
                
                self.logger.debug("Payload compressed",
                                original_size=len(payload_bytes),
                                compressed_size=len(compressed),
                                ratio=compression_ratio)
                
                return {
                    '_compressed': True,
                    '_algorithm': 'zlib',
                    '_original_size': len(payload_bytes),
                    '_data': compressed.hex()
                }
            
            return payload
            
        except Exception as e:
            self.logger.error("Payload compression failed", error=str(e))
            return payload
    
    def _decompress_payload(self, payload: Dict) -> Dict:
        """Decompress compressed payload with validation"""
        try:
            if not payload.get('_compressed'):
                return payload
            
            compressed_data = bytes.fromhex(payload['_data'])
            decompressed = zlib.decompress(compressed_data)
            result = json.loads(decompressed.decode('utf-8'))
            
            # Validate decompressed size
            if payload.get('_original_size') and len(decompressed) != payload['_original_size']:
                self.logger.warning("Decompressed size mismatch",
                                  expected=payload['_original_size'],
                                  actual=len(decompressed))
            
            return result
            
        except Exception as e:
            self.logger.error("Payload decompression failed", error=str(e))
            raise ValueError(f"Failed to decompress payload: {e}")
    
    def _encrypt_message_payload(self, payload: Dict) -> Dict:
        """Encrypt sensitive payload data (placeholder for actual encryption)"""
        # In production, use proper encryption like AES-256
        # This is a placeholder showing where encryption would be implemented
        self.logger.debug("Encryption requested (not implemented in this version)")
        return payload
    
    def _validate_payload_schema(self, payload: Dict) -> Dict:
        """Validate payload against expected schema"""
        # In production, use JSON Schema or Pydantic for validation
        required_fields = {'type', 'data'}
        if not all(field in payload for field in required_fields):
            missing = required_fields - set(payload.keys())
            raise ValueError(f"Missing required fields in payload: {missing}")
        return payload
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Enhanced task execution with comprehensive error handling"""
        task_type = request.task_type
        payload = request.payload
        start_time = time.time()
        
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
            elif task_type == "get_message_status":
                result = await self._get_message_status(payload)
            elif task_type == "cancel_message":
                result = await self._cancel_message(payload)
            elif task_type == "get_agent_status":
                result = await self._get_agent_status(payload)
            elif task_type == "update_route":
                result = await self._update_route(payload)
            else:
                raise ValueError(f"Unknown communication task type: {task_type}")
            
            execution_time = time.time() - start_time
            self.logger.info("Task executed successfully",
                           task_type=task_type,
                           execution_time_ms=execution_time * 1000)
            
            return TaskResponse(
                task_id=request.task_id,
                status=TaskStatus.COMPLETED,
                result=result
            ).dict()
        
        except ValueError as e:
            self.logger.error(f"Validation error in task {task_type}", error=str(e))
            return TaskResponse(
                task_id=request.task_id,
                status=TaskStatus.FAILED,
                error=f"Validation error: {str(e)}"
            ).dict()
        
        except asyncio.TimeoutError:
            self.logger.error(f"Task {task_type} timed out")
            return TaskResponse(
                task_id=request.task_id,
                status=TaskStatus.FAILED,
                error="Task execution timeout"
            ).dict()
        
        except Exception as e:
            self.logger.error(f"Error executing communication task {task_type}",
                            error=str(e),
                            traceback=traceback.format_exc())
            return TaskResponse(
                task_id=request.task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            ).dict()
    
    async def _send_message_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a direct message with validation and tracking"""
        try:
            # Validate required fields
            required_fields = ['sender', 'recipients', 'subject', 'payload']
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Create message with validation
            message = Message(
                id=payload.get('id', str(uuid.uuid4())),
                type=MessageType(payload.get('type', 'direct')),
                priority=MessagePriority(payload.get('priority', 2)),
                sender=payload['sender'],
                recipients=payload['recipients'],
                subject=payload['subject'],
                payload=payload['payload'],
                delivery_mode=DeliveryMode(payload.get('delivery_mode', 'fire_and_forget')),
                ttl_seconds=min(payload.get('ttl_seconds', MESSAGE_TTL_SECONDS), MESSAGE_TTL_SECONDS * 2),
                max_retries=min(payload.get('max_retries', 3), MAX_RETRY_ATTEMPTS),
                metadata=payload.get('metadata', {})
            )
            
            # Check message size
            if message.size_bytes() > MAX_MESSAGE_SIZE:
                raise ValueError(f"Message size exceeds maximum allowed ({MAX_MESSAGE_SIZE} bytes)")
            
            # Process and route message
            result = await self._process_and_route_message(message)
            self.communication_metrics['messages_sent'] += 1
            
            return {
                **result,
                'message_id': message.id,
                'size_bytes': message.size_bytes(),
                'created_at': message.created_at
            }
            
        except Exception as e:
            self.logger.error("Failed to send message", error=str(e), traceback=traceback.format_exc())
            self.communication_metrics['messages_failed'] += 1
            raise
    
    async def _broadcast_message_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast message to multiple agents"""
        try:
            recipients = []
            if 'target_groups' in payload:
                for group in payload['target_groups']:
                    recipients.extend(self._get_agents_by_group(group))
            else:
                # Broadcast to all active agents
                recipients = [name for name, info in self.agent_directory.items() 
                            if self.agent_presence.get(name, {}).get('status') == AgentStatus.ACTIVE.value]
            
            if not recipients:
                self.logger.warning("No recipients found for broadcast")
                return {'status': 'no_recipients', 'message_id': None}
            
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.BROADCAST,
                priority=MessagePriority(payload.get('priority', 2)),
                sender=payload['sender'],
                recipients=list(set(recipients)),  # Remove duplicates
                subject=payload['subject'],
                payload=payload['payload'],
                delivery_mode=DeliveryMode(payload.get('delivery_mode', 'fire_and_forget')),
                metadata=payload.get('metadata', {})
            )
            
            result = await self._process_and_route_message(message)
            self.communication_metrics['messages_sent'] += 1
            
            return {
                **result,
                'broadcast_count': len(recipients),
                'message_id': message.id
            }
            
        except Exception as e:
            self.logger.error("Failed to broadcast message", error=str(e))
            self.communication_metrics['messages_failed'] += 1
            raise
    
    async def _multicast_message_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Multicast message to specific groups"""
        try:
            target_groups = payload.get('target_groups', [])
            if not target_groups:
                raise ValueError("Multicast requires 'target_groups'")
            
            recipients = []
            for group in target_groups:
                group_agents = self._get_agents_by_group(group)
                recipients.extend(group_agents)
                self.logger.debug("Added agents from group", group=group, count=len(group_agents))
            
            recipients = list(set(recipients))  # Remove duplicates
            
            if not recipients:
                return {'status': 'no_recipients', 'message_id': None}
            
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
            
            return {
                **result,
                'multicast_groups': target_groups,
                'recipient_count': len(recipients),
                'message_id': message.id
            }
            
        except Exception as e:
            self.logger.error("Failed to multicast message", error=str(e))
            self.communication_metrics['messages_failed'] += 1
            raise
    
    async def _request_response_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request-response pattern with timeout"""
        try:
            sender = payload['sender']
            recipient = payload['recipient']
            subject = payload['subject']
            request_payload = payload['payload']
            timeout = min(payload.get('timeout', 30), 300)  # Max 5 minutes
            
            request_message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
                sender=sender,
                recipients=[recipient],
                subject=subject,
                payload=request_payload,
                delivery_mode=DeliveryMode.ACKNOWLEDGMENT,
                ttl_seconds=timeout,
                metadata=payload.get('metadata', {})
            )
            
            # Create future for response
            response_future = asyncio.Future()
            self.pending_messages[request_message.id] = response_future
            
            # Store request info
            self.communication_patterns['request_response'][request_message.id] = {
                'sender': sender,
                'recipient': recipient,
                'timestamp': time.time(),
                'timeout': timeout
            }
            
            try:
                # Send request
                await self._process_and_route_message(request_message)
                self.communication_metrics['messages_sent'] += 1
                
                # Wait for response with timeout
                response_message = await asyncio.wait_for(response_future, timeout=timeout)
                
                return {
                    'status': 'success',
                    'request_id': request_message.id,
                    'response': response_message.payload,
                    'response_time_ms': (time.time() - request_message.created_at) * 1000
                }
                
            except asyncio.TimeoutError:
                self.logger.warning("Request-response timed out",
                                  message_id=request_message.id,
                                  recipient=recipient,
                                  timeout=timeout)
                return {
                    'status': 'timeout',
                    'request_id': request_message.id,
                    'error': f'Request timed out after {timeout} seconds'
                }
                
            finally:
                # Cleanup
                if request_message.id in self.pending_messages:
                    del self.pending_messages[request_message.id]
                if request_message.id in self.communication_patterns['request_response']:
                    del self.communication_patterns['request_response'][request_message.id]
        
        except Exception as e:
            self.logger.error("Request-response failed", error=str(e), traceback=traceback.format_exc())
            raise
    
    async def _publish_event_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Publish event to subscribers"""
        try:
            subject = payload['subject']
            event_payload = payload['payload']
            sender = payload.get('sender', self.config.name)
            
            event_message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.EVENT,
                priority=MessagePriority.NORMAL,
                sender=sender,
                recipients=[],
                subject=subject,
                payload=event_payload,
                delivery_mode=DeliveryMode.FIRE_AND_FORGET,
                metadata=payload.get('metadata', {})
            )
            
            # Publish to NATS
            message_data = json.dumps(asdict(event_message)).encode('utf-8')
            await self._publish(subject, message_data)
            
            self.communication_metrics['messages_sent'] += 1
            self.communication_metrics['bytes_transferred'] += len(message_data)
            
            # Track event
            if subject not in self.communication_patterns['event_stream']:
                self.communication_patterns['event_stream'][subject] = []
            self.communication_patterns['event_stream'][subject].append({
                'message_id': event_message.id,
                'timestamp': time.time(),
                'size_bytes': len(message_data)
            })
            
            return {
                'status': 'event_published',
                'message_id': event_message.id,
                'subject': subject,
                'subscriber_count': len(self.communication_patterns['publish_subscribe'].get(subject, []))
            }
            
        except Exception as e:
            self.logger.error("Failed to publish event", error=str(e))
            self.communication_metrics['messages_failed'] += 1
            raise
    
    async def _get_message_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a specific message"""
        message_id = payload.get('message_id')
        if not message_id:
            raise ValueError("message_id is required")
        
        # Check in pending messages
        if message_id in self.pending_messages:
            msg = self.pending_messages[message_id]
            if isinstance(msg, Message):
                return {
                    'message_id': message_id,
                    'status': msg.status.value,
                    'retry_count': msg.retry_count,
                    'created_at': msg.created_at,
                    'is_expired': msg.is_expired()
                }
        
        # Check in delivery receipts
        if message_id in self.delivery_receipts:
            receipt = self.delivery_receipts[message_id]
            return {
                'message_id': message_id,
                'status': receipt.get('status', 'unknown'),
                'recipient': receipt.get('recipient'),
                'timestamp': receipt.get('timestamp'),
                'delivery_timestamp': receipt.get('delivery_timestamp')
            }
        
        # Check in failed deliveries
        if message_id in self.failed_deliveries:
            failures = self.failed_deliveries[message_id]
            return {
                'message_id': message_id,
                'status': 'failed',
                'failure_count': len(failures),
                'last_failure': failures[-1] if failures else None
            }
        
        return {
            'message_id': message_id,
            'status': 'not_found'
        }
    
    async def _cancel_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a pending message"""
        message_id = payload.get('message_id')
        if not message_id:
            raise ValueError("message_id is required")
        
        if message_id in self.pending_messages:
            msg = self.pending_messages[message_id]
            if isinstance(msg, Message):
                msg.status = MessageStatus.EXPIRED
                del self.pending_messages[message_id]
                self.logger.info("Message cancelled", message_id=message_id)
                return {'status': 'cancelled', 'message_id': message_id}
        
        return {'status': 'not_found', 'message_id': message_id}
    
    async def _get_agent_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of an agent"""
        agent_name = payload.get('agent_name')
        if not agent_name:
            raise ValueError("agent_name is required")
        
        status = {
            'agent_name': agent_name,
            'exists': agent_name in self.agent_directory,
            'presence': self.agent_presence.get(agent_name),
            'health': self.agent_health.get(agent_name),
            'subscriptions': list(self.agent_subscriptions.get(agent_name, [])),
            'queued_messages': len(self.message_queue.get(agent_name, [])),
            'circuit_breaker': self._circuit_breakers.get(agent_name, {}).get('state', 'closed')
        }
        
        return status
    
    async def _update_route(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update or add a routing rule"""
        try:
            route_data = payload.get('route')
            if not route_data:
                raise ValueError("route data is required")
            
            route = MessageRoute(**route_data)
            
            # Remove existing route with same pattern
            self.message_routes = [r for r in self.message_routes if r.pattern != route.pattern]
            
            # Add new route
            self.message_routes.append(route)
            self.message_routes.sort(key=lambda x: x.priority, reverse=True)
            
            self.logger.info("Route updated", pattern=route.pattern, target_agents=route.target_agents)
            
            return {
                'status': 'success',
                'pattern': route.pattern,
                'total_routes': len(self.message_routes)
            }
            
        except Exception as e:
            self.logger.error("Failed to update route", error=str(e))
            raise
    
    async def _process_and_route_message(self, message: Message) -> Dict[str, Any]:
        """Process and route message with comprehensive error handling"""
        try:
            # Apply transformations
            processed_payload = message.payload
            for transformer_name in message.metadata.get("transformers", []):
                if transformer_name in self.message_transformers:
                    try:
                        processed_payload = self.message_transformers[transformer_name](processed_payload)
                    except Exception as e:
                        self.logger.error(f"Transformer {transformer_name} failed", error=str(e))
                        raise ValueError(f"Message transformation failed: {e}")
                else:
                    self.logger.warning(f"Unknown transformer: {transformer_name}")
            
            # Apply filters
            for filter_name in message.metadata.get("filters", []):
                if filter_name in self.message_filters:
                    try:
                        if not self.message_filters[filter_name](message, processed_payload):
                            self.logger.info(f"Message filtered out by {filter_name}", message_id=message.id)
                            message.status = MessageStatus.FAILED
                            return {
                                'status': 'filtered',
                                'message_id': message.id,
                                'filter': filter_name
                            }
                    except Exception as e:
                        self.logger.error(f"Filter {filter_name} failed", error=str(e))
                        raise ValueError(f"Message filtering failed: {e}")
                else:
                    self.logger.warning(f"Unknown filter: {filter_name}")
            
            message.payload = processed_payload
            
            # Determine recipients
            actual_recipients = set()
            if message.type == MessageType.DIRECT:
                actual_recipients.update(message.recipients)
            elif message.type == MessageType.BROADCAST:
                actual_recipients.update([name for name in self.agent_directory.keys()
                                        if name != message.sender])
            elif message.type == MessageType.MULTICAST:
                actual_recipients.update(message.recipients)
            elif message.type in [MessageType.PUBLISH, MessageType.EVENT]:
                # Events handled via NATS pub/sub
                pass
            elif message.type == MessageType.REQUEST:
                actual_recipients.update(message.recipients)
            
            # Apply routing rules
            for route in self.message_routes:
                if route.matches(message.subject):
                    if route.filter_condition:
                        try:
                            # Safe evaluation of filter condition
                            if not self._evaluate_filter_condition(route.filter_condition, message):
                                continue
                        except Exception as e:
                            self.logger.error(f"Route filter evaluation failed", error=str(e))
                            continue
                    
                    actual_recipients.update(route.target_agents)
                    
                    # Apply transformation
                    if route.transformation == "enrich_subject":
                        message.subject = f"[Routed] {message.subject}"
            
            # Remove sender from recipients
            if message.type in [MessageType.DIRECT, MessageType.BROADCAST, MessageType.MULTICAST]:
                actual_recipients.discard(message.sender)
            
            # Send to recipients
            if message.type in [MessageType.DIRECT, MessageType.BROADCAST, MessageType.MULTICAST, MessageType.REQUEST]:
                delivery_results = await self._deliver_to_recipients(message, actual_recipients)
            elif message.type in [MessageType.PUBLISH, MessageType.EVENT]:
                delivery_results = {'status': 'published'}
            
            # Update message history
            message.status = MessageStatus.SENT
            self.message_history.append(asdict(message))
            
            return {
                'status': 'processed',
                'message_id': message.id,
                'recipients': list(actual_recipients),
                'delivery_results': delivery_results
            }
            
        except Exception as e:
            message.status = MessageStatus.FAILED
            self.logger.error("Message processing failed",
                            message_id=message.id,
                            error=str(e),
                            traceback=traceback.format_exc())
            self.communication_metrics['messages_failed'] += 1
            raise
    
    def _evaluate_filter_condition(self, condition: str, message: Message) -> bool:
        """Safely evaluate filter condition"""
        try:
            # Create safe evaluation context
            safe_context = {
                'message': message,
                'payload': message.payload,
                'sender': message.sender,
                'subject': message.subject,
                'priority': message.priority.value,
                'type': message.type.value
            }
            # Only allow simple comparisons, no function calls
            if any(dangerous in condition for dangerous in ['__', 'import', 'eval', 'exec', 'compile']):
                self.logger.warning("Dangerous filter condition blocked", condition=condition)
                return False
            
            return eval(condition, {"__builtins__": {}}, safe_context)
        except Exception as e:
            self.logger.error("Filter condition evaluation failed", condition=condition, error=str(e))
            return False
    
    async def _deliver_to_recipients(self, message: Message, recipients: Set[str]) -> Dict[str, Any]:
        """Deliver message to all recipients with circuit breaker"""
        delivery_results = {
            'success': [],
            'failed': [],
            'queued': []
        }
        
        for recipient in recipients:
            try:
                # Check circuit breaker
                if self._is_circuit_open(recipient):
                    self.logger.warning("Circuit breaker open for agent", agent=recipient)
                    delivery_results['failed'].append(recipient)
                    continue
                
                # Check agent availability
                if recipient in self.agent_presence and \
                   self.agent_presence[recipient].get("status") == AgentStatus.ACTIVE.value:
                    await self._send_to_agent(recipient, message)
                    delivery_results['success'].append(recipient)
                    self._record_circuit_success(recipient)
                else:
                    # Queue for later delivery
                    self.logger.debug("Agent not active, queuing message",
                                    recipient=recipient,
                                    message_id=message.id)
                    self.message_queue[recipient].append(message)
                    delivery_results['queued'].append(recipient)
                    # Store in pending for retry
                    self.pending_messages[message.id] = message
                    
            except Exception as e:
                self.logger.error("Failed to deliver to recipient",
                                recipient=recipient,
                                message_id=message.id,
                                error=str(e))
                delivery_results['failed'].append(recipient)
                self._record_circuit_failure(recipient)
        
        return delivery_results
    
    def _is_circuit_open(self, agent_name: str) -> bool:
        """Check if circuit breaker is open for an agent"""
        if agent_name not in self._circuit_breakers:
            return False
        
        breaker = self._circuit_breakers[agent_name]
        if breaker['state'] == 'open':
            # Check if should try half-open
            if time.time() - breaker['opened_at'] > breaker['timeout']:
                breaker['state'] = 'half_open'
                self.logger.info("Circuit breaker half-open", agent=agent_name)
                return False
            return True
        
        return False
    
    def _record_circuit_success(self, agent_name: str):
        """Record successful delivery for circuit breaker"""
        if agent_name in self._circuit_breakers:
            breaker = self._circuit_breakers[agent_name]
            breaker['failure_count'] = 0
            breaker['success_count'] += 1
            
            if breaker['state'] == 'half_open' and breaker['success_count'] >= 3:
                breaker['state'] = 'closed'
                self.logger.info("Circuit breaker closed", agent=agent_name)
    
    def _record_circuit_failure(self, agent_name: str):
        """Record failed delivery for circuit breaker"""
        if agent_name not in self._circuit_breakers:
            self._circuit_breakers[agent_name] = {
                'state': 'closed',
                'failure_count': 0,
                'success_count': 0,
                'threshold': 5,
                'timeout': 60,
                'opened_at': None
            }
        
        breaker = self._circuit_breakers[agent_name]
        breaker['failure_count'] += 1
        breaker['success_count'] = 0
        
        if breaker['failure_count'] >= breaker['threshold']:
            breaker['state'] = 'open'
            breaker['opened_at'] = time.time()
            self.communication_metrics['circuit_breakers_open'] += 1
            self.logger.warning("Circuit breaker opened", agent=agent_name)
    
    async def _send_to_agent(self, recipient_agent_name: str, message: Message):
        """Send message to specific agent with retry logic"""
        subject = f"agent.{recipient_agent_name}.inbox"
        delivery_start = time.time()
        
        try:
            message_data = json.dumps(asdict(message)).encode('utf-8')
            
            # Check message size
            if len(message_data) > MAX_MESSAGE_SIZE:
                raise ValueError(f"Message size {len(message_data)} exceeds maximum {MAX_MESSAGE_SIZE}")
            
            # Send message
            if message.type == MessageType.REQUEST:
                reply_to_subject = f"communication.response.{message.id}"
                await self._publish_request(subject, message_data, reply_to_subject)
            else:
                await self._publish(subject, message_data)
            
            # Track delivery
            delivery_time = time.time() - delivery_start
            self._delivery_times.append(delivery_time)
            
            message.delivery_attempts.append({
                'timestamp': time.time(),
                'recipient': recipient_agent_name,
                'success': True,
                'delivery_time': delivery_time
            })
            
            self.logger.debug("Message sent to agent",
                            message_id=message.id,
                            recipient=recipient_agent_name,
                            delivery_time_ms=delivery_time * 1000)
            
            self.communication_metrics['messages_delivered'] += 1
            self.communication_metrics['bytes_transferred'] += len(message_data)
            
            # Handle delivery mode
            if message.delivery_mode == DeliveryMode.ACKNOWLEDGMENT:
                self.delivery_receipts[message.id] = {
                    "status": "pending_ack",
                    "timestamp": time.time(),
                    "recipient": recipient_agent_name
                }
            elif message.id in self.pending_messages and isinstance(self.pending_messages[message.id], Message):
                del self.pending_messages[message.id]
        
        except Exception as e:
            delivery_time = time.time() - delivery_start
            message.delivery_attempts.append({
                'timestamp': time.time(),
                'recipient': recipient_agent_name,
                'success': False,
                'error': str(e),
                'delivery_time': delivery_time
            })
            
            self.logger.error("Failed to send message to agent",
                            message_id=message.id,
                            recipient=recipient_agent_name,
                            error=str(e),
                            traceback=traceback.format_exc())
            
            self.communication_metrics['messages_failed'] += 1
            self.failed_deliveries[message.id].append({
                "timestamp": time.time(),
                "error": str(e),
                "recipient": recipient_agent_name
            })
            
            # Retry logic
            if message.should_retry():
                message.retry_count += 1
                message.status = MessageStatus.RETRYING
                self.message_queue[recipient_agent_name].appendleft(message)
                self.communication_metrics['messages_retried'] += 1
            else:
                message.status = MessageStatus.FAILED
                self.logger.error(f"Message {message.id} failed after {message.retry_count} retries")
                if message.id in self.pending_messages:
                    del self.pending_messages[message.id]
            
            raise
    
    # Background monitoring and cleanup tasks
    
    async def _message_delivery_loop(self):
        """Enhanced message delivery loop with prioritization"""
        while not self._shutdown_event.is_set():
            try:
                for agent_name, queue in list(self.message_queue.items()):
                    if not queue:
                        continue
                    
                    # Check agent availability
                    if self.agent_presence.get(agent_name, {}).get("status") != AgentStatus.ACTIVE.value:
                        continue
                    
                    # Check circuit breaker
                    if self._is_circuit_open(agent_name):
                        continue
                    
                    # Process messages with priority
                    messages_to_send = []
                    while queue and len(messages_to_send) < 10:  # Batch size
                        msg = queue.popleft()
                        if not msg.is_expired():
                            messages_to_send.append(msg)
                        else:
                            msg.status = MessageStatus.EXPIRED
                            self.communication_metrics['messages_expired'] += 1
                            if msg.id in self.pending_messages:
                                del self.pending_messages[msg.id]
                    
                    # Send messages
                    for message in messages_to_send:
                        try:
                            await self._send_to_agent(agent_name, message)
                            await asyncio.sleep(0.01)  # Rate limiting
                        except Exception as e:
                            self.logger.error("Delivery loop send failed", error=str(e))
                
                # Update queue depth metric
                total_queued = sum(len(q) for q in self.message_queue.values())
                self.communication_metrics['queue_depth_max'] = max(
                    self.communication_metrics['queue_depth_max'],
                    total_queued
                )
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error("Message delivery loop failed", error=str(e), traceback=traceback.format_exc())
                await asyncio.sleep(5)
    
    async def _retry_failed_messages(self):
        """Enhanced retry logic with exponential backoff"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                messages_to_retry = []
                
                for msg_id, message in list(self.pending_messages.items()):
                    if not isinstance(message, Message):
                        continue
                    
                    if message.is_expired():
                        message.status = MessageStatus.EXPIRED
                        self.communication_metrics['messages_expired'] += 1
                        if msg_id in self.pending_messages:
                            del self.pending_messages[msg_id]
                        continue
                    
                    if not message.should_retry():
                        continue
                    
                    # Exponential backoff
                    backoff = min(5 * (2 ** message.retry_count), 300)  # Max 5 minutes
                    if current_time - message.created_at > backoff:
                        messages_to_retry.append(message)
                    
                    # Check ACK timeout
                    if message.delivery_mode == DeliveryMode.ACKNOWLEDGMENT:
                        if msg_id in self.delivery_receipts:
                            receipt = self.delivery_receipts[msg_id]
                            if receipt["status"] == "pending_ack" and \
                               current_time - receipt["timestamp"] > 30:
                                self.logger.warning("ACK timeout", message_id=msg_id)
                                messages_to_retry.append(message)
                
                # Retry messages
                for message in messages_to_retry:
                    self.logger.info("Retrying message",
                                   message_id=message.id,
                                   retry_count=message.retry_count)
                    
                    message.retry_count += 1
                    message.status = MessageStatus.RETRYING
                    
                    for recipient in message.recipients:
                        self.message_queue[recipient].appendleft(message)
                    
                    if message.id in self.delivery_receipts:
                        self.delivery_receipts[message.id]["status"] = "retrying"
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error("Retry loop failed", error=str(e), traceback=traceback.format_exc())
                await asyncio.sleep(30)
    
    async def _cleanup_expired_messages(self):
        """Clean up expired messages and old data"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                
                # Clean expired messages
                expired_ids = []
                for msg_id, message in list(self.pending_messages.items()):
                    if isinstance(message, Message) and message.is_expired():
                        expired_ids.append(msg_id)
                
                for msg_id in expired_ids:
                    del self.pending_messages[msg_id]
                    if msg_id in self.delivery_receipts:
                        del self.delivery_receipts[msg_id]
                    self.communication_metrics['messages_expired'] += 1
                
                # Clean old delivery receipts
                old_receipts = [
                    msg_id for msg_id, receipt in self.delivery_receipts.items()
                    if current_time - receipt.get('timestamp', 0) > 3600
                ]
                for msg_id in old_receipts:
                    del self.delivery_receipts[msg_id]
                
                # Clean old failed deliveries
                for msg_id in list(self.failed_deliveries.keys()):
                    failures = self.failed_deliveries[msg_id]
                    if failures and current_time - failures[-1]['timestamp'] > 3600:
                        del self.failed_deliveries[msg_id]
                
                # Clean expired queued messages
                for agent_name, queue in list(self.message_queue.items()):
                    for i in range(len(queue) - 1, -1, -1):
                        if queue[i].is_expired():
                            del queue[i]
                
                self.logger.debug("Cleanup completed",
                                expired_messages=len(expired_ids),
                                old_receipts=len(old_receipts))
                
                await asyncio.sleep(CLEANUP_INTERVAL)
                
            except Exception as e:
                self.logger.error("Cleanup loop failed", error=str(e), traceback=traceback.format_exc())
                await asyncio.sleep(600)
    
    async def _monitor_conversations(self):
        """Monitor and clean up conversations"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                conversation_timeout = 3600 * 24 * 7  # 7 days
                
                conversations_to_remove = []
                for conv_id, conv in self.conversations.items():
                    if not conv.is_active(conversation_timeout):
                        conversations_to_remove.append(conv_id)
                
                for conv_id in conversations_to_remove:
                    conv = self.conversations[conv_id]
                    conv.status = "archived"
                    
                    # Archive to database if available
                    if self.db_pool:
                        await self._archive_conversation(conv)
                    
                    del self.conversations[conv_id]
                    
                    # Clean up index
                    for agent_name in list(self.conversation_index.keys()):
                        if conv_id in self.conversation_index[agent_name]:
                            self.conversation_index[agent_name].remove(conv_id)
                            if not self.conversation_index[agent_name]:
                                del self.conversation_index[agent_name]
                
                self.communication_metrics['active_conversations'] = len(self.conversations)
                
                if conversations_to_remove:
                    self.logger.info("Archived conversations",
                                   count=len(conversations_to_remove))
                
                await asyncio.sleep(3600)
                
            except Exception as e:
                self.logger.error("Conversation monitor failed", error=str(e), traceback=traceback.format_exc())
                await asyncio.sleep(300)
    
    async def _health_check_loop(self):
        """Periodic health checks"""
        while not self._shutdown_event.is_set():
            try:
                issues = []
                
                # Check queue depths
                for agent_name, queue in self.message_queue.items():
                    if len(queue) > MAX_QUEUE_SIZE * 0.8:
                        issues.append(f"Queue for {agent_name} is {len(queue)}/{MAX_QUEUE_SIZE}")
                
                # Check pending messages
                if len(self.pending_messages) > 1000:
                    issues.append(f"High pending message count: {len(self.pending_messages)}")
                
                # Check circuit breakers
                open_breakers = [name for name, breaker in self._circuit_breakers.items()
                               if breaker['state'] == 'open']
                if open_breakers:
                    issues.append(f"Open circuit breakers: {', '.join(open_breakers)}")
                
                # Update health status
                self._health_status['last_check'] = time.time()
                self._health_status['issues'] = issues
                self._health_status['status'] = 'healthy' if not issues else 'degraded'
                
                # Calculate delivery metrics
                if self._delivery_times:
                    sorted_times = sorted(self._delivery_times)
                    self.communication_metrics['average_delivery_time'] = sum(sorted_times) / len(sorted_times)
                    self.communication_metrics['p95_delivery_time'] = sorted_times[int(len(sorted_times) * 0.95)]
                    self.communication_metrics['p99_delivery_time'] = sorted_times[int(len(sorted_times) * 0.99)]
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                self._health_status['status'] = 'unhealthy'
                self._health_status['issues'].append(f"Health check error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _circuit_breaker_monitor(self):
        """Monitor and reset circuit breakers"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                
                for agent_name, breaker in list(self._circuit_breakers.items()):
                    if breaker['state'] == 'open':
                        # Try to recover after timeout
                        if current_time - breaker['opened_at'] > breaker['timeout']:
                            breaker['state'] = 'half_open'
                            breaker['failure_count'] = 0
                            self.logger.info("Circuit breaker attempting recovery",
                                           agent=agent_name)
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error("Circuit breaker monitor failed", error=str(e))
                await asyncio.sleep(60)
    
    async def _persist_message_history(self):
        """Persist message history to database"""
        while not self._shutdown_event.is_set():
            try:
                if not self.db_pool or not self.message_history:
                    await asyncio.sleep(300)
                    continue
                
                # Batch persist messages
                messages_to_persist = []
                while self.message_history and len(messages_to_persist) < 100:
                    messages_to_persist.append(self.message_history.popleft())
                
                if messages_to_persist:
                    await self._batch_persist_messages(messages_to_persist)
                
                await asyncio.sleep(300)  # Persist every 5 minutes
                
            except Exception as e:
                self.logger.error("Message history persistence failed", error=str(e))
                await asyncio.sleep(600)
    
    async def _batch_persist_messages(self, messages: List[Dict]):
        """Batch persist messages to database"""
        try:
            if not self.db_pool:
                return
            
            query = """
                INSERT INTO message_history 
                (message_id, type, sender, recipients, subject, payload, status, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (message_id) DO NOTHING
            """
            
            records = [
                (
                    msg['id'],
                    msg['type'],
                    msg['sender'],
                    json.dumps(msg['recipients']),
                    msg['subject'],
                    json.dumps(msg['payload']),
                    msg.get('status', 'sent'),
                    datetime.fromtimestamp(msg['created_at']),
                    json.dumps(msg.get('metadata', {}))
                )
                for msg in messages
            ]
            
            async with self.db_pool.acquire() as conn:
                await conn.executemany(query, records)
            
            self.logger.debug("Persisted message batch", count=len(messages))
            
        except Exception as e:
            self.logger.error("Batch persist failed", error=str(e))
    
    async def _archive_conversation(self, conv: ConversationContext):
        """Archive conversation to database"""
        try:
            if not self.db_pool:
                return
            
            query = """
                INSERT INTO conversation_archive
                (conversation_id, participants, topic, message_count, created_at, last_activity, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (conversation_id) DO UPDATE SET
                    message_count = EXCLUDED.message_count,
                    last_activity = EXCLUDED.last_activity,
                    metadata = EXCLUDED.metadata
            """
            
            await self._db_query(
                query,
                conv.id,
                json.dumps(list(conv.participants)),
                conv.topic,
                conv.message_count,
                datetime.fromtimestamp(conv.created_at),
                datetime.fromtimestamp(conv.last_activity),
                json.dumps(conv.metadata)
            )
            
            self.logger.debug("Archived conversation", conversation_id=conv.id)
            
        except Exception as e:
            self.logger.error("Conversation archive failed", error=str(e))
    
    # Event handlers
    
    async def _handle_agent_registration(self, msg):
        """Handle agent registration with validation"""
        try:
            data = json.loads(msg.data.decode())
            
            # Validate required fields
            required = ['agent_name', 'agent_type']
            if not all(field in data for field in required):
                raise ValueError(f"Missing required fields: {required}")
            
            agent_name = data["agent_name"]
            agent_type = data["agent_type"]
            capabilities = data.get("capabilities", [])
            status = data.get("status", AgentStatus.ACTIVE.value)
            
            # Register agent
            self.agent_directory[agent_name] = {
                "agent_type": agent_type,
                "capabilities": capabilities,
                "last_seen": time.time(),
                "registered_at": time.time()
            }
            
            self.agent_presence[agent_name] = {
                "status": status,
                "last_update": time.time()
            }
            
            self.agent_health[agent_name] = {
                "status": "healthy",
                "last_check": time.time()
            }
            
            self.logger.info("Agent registered",
                           agent_name=agent_name,
                           agent_type=agent_type,
                           capabilities=capabilities)
            
            # Send response
            if msg.reply:
                response = {
                    "status": "registered",
                    "agent_name": agent_name,
                    "timestamp": time.time()
                }
                await self._publish(msg.reply, json.dumps(response).encode())
        
        except Exception as e:
            self.logger.error("Agent registration failed", error=str(e), traceback=traceback.format_exc())
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "error": str(e),
                    "success": False
                }).encode())
    
    async def _handle_subscription(self, msg):
        """Handle agent subscription to topics"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data["agent_name"]
            topic = data["topic"]
            
            self.agent_subscriptions[agent_name].add(topic)
            self.communication_patterns['publish_subscribe'][topic].add(agent_name)
            
            self.logger.info("Agent subscribed",
                           agent_name=agent_name,
                           topic=topic)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "status": "subscribed",
                    "agent_name": agent_name,
                    "topic": topic
                }).encode())
        
        except Exception as e:
            self.logger.error("Subscription failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "error": str(e),
                    "success": False
                }).encode())
    
    async def _handle_start_conversation(self, msg):
        """Handle conversation start request"""
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
            
            self.logger.info("Conversation started",
                           conversation_id=conv_id,
                           participants=list(participants),
                           topic=topic)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "status": "conversation_started",
                    "conversation_id": conv_id,
                    "participants": list(participants)
                }).encode())
        
        except Exception as e:
            self.logger.error("Start conversation failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "error": str(e),
                    "success": False
                }).encode())
    
    async def _handle_add_route(self, msg):
        """Handle route addition request"""
        try:
            data = json.loads(msg.data.decode())
            route = MessageRoute(**data)
            
            # Validate route pattern
            try:
                re.compile(route.pattern)
            except re.error as e:
                raise ValueError(f"Invalid route pattern: {e}")
            
            self.message_routes.append(route)
            self.message_routes.sort(key=lambda x: x.priority, reverse=True)
            
            self.logger.info("Route added",
                           pattern=route.pattern,
                           target_agents=route.target_agents,
                           priority=route.priority)
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "status": "route_added",
                    "pattern": route.pattern
                }).encode())
        
        except Exception as e:
            self.logger.error("Add route failed", error=str(e))
            if msg.reply:
                await self._publish(msg.reply, json.dumps({
                    "error": str(e),
                    "success": False
                }).encode())
    
    async def _handle_acknowledgment(self, msg):
        """Handle message acknowledgments"""
        try:
            data = json.loads(msg.data.decode())
            original_message_id = data["original_message_id"]
            sender_agent = data["sender_agent"]
            status = data.get("status", "received")
            
            if original_message_id in self.delivery_receipts:
                self.delivery_receipts[original_message_id].update({
                    "status": status,
                    "ack_timestamp": time.time(),
                    "ack_sender": sender_agent
                })
                
                self.logger.debug("ACK received",
                                message_id=original_message_id,
                                sender=sender_agent,
                                status=status)
                
                # Remove from pending if ACK successful
                if status in ["received", "processed"] and original_message_id in self.pending_messages:
                    msg_obj = self.pending_messages[original_message_id]
                    if isinstance(msg_obj, Message):
                        msg_obj.status = MessageStatus.ACKNOWLEDGED
                        del self.pending_messages[original_message_id]
            else:
                self.logger.warning("ACK for unknown message",
                                  message_id=original_message_id)
        
        except Exception as e:
            self.logger.error("Handle ACK failed", error=str(e))
    
    async def _handle_delivery_receipt(self, msg):
        """Handle detailed delivery receipts"""
        try:
            data = json.loads(msg.data.decode())
            original_message_id = data["original_message_id"]
            recipient_agent = data["recipient_agent"]
            delivery_status = data["delivery_status"]
            
            if original_message_id in self.delivery_receipts:
                self.delivery_receipts[original_message_id].update({
                    "delivery_status": delivery_status,
                    "delivery_timestamp": time.time(),
                    "recipient": recipient_agent
                })
                
                self.logger.debug("Delivery receipt received",
                                message_id=original_message_id,
                                recipient=recipient_agent,
                                status=delivery_status)
        
        except Exception as e:
            self.logger.error("Handle delivery receipt failed", error=str(e))
    
    async def _handle_presence_update(self, msg):
        """Handle agent presence updates"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data["agent_name"]
            status = data["status"]
            
            if agent_name in self.agent_presence:
                old_status = self.agent_presence[agent_name]["status"]
                self.agent_presence[agent_name].update({
                    "status": status,
                    "last_update": time.time()
                })
                
                self.logger.info("Agent presence updated",
                               agent_name=agent_name,
                               old_status=old_status,
                               new_status=status)
                
                # If agent became active, trigger message delivery
                if status == AgentStatus.ACTIVE.value and agent_name in self.message_queue:
                    self.logger.info("Agent active, triggering message delivery",
                                   agent=agent_name,
                                   queued_messages=len(self.message_queue[agent_name]))
            else:
                self.logger.warning("Presence update for unknown agent",
                                  agent_name=agent_name)
        
        except Exception as e:
            self.logger.error("Handle presence update failed", error=str(e))
    
    async def _handle_health_check(self, msg):
        """Handle health check requests"""
        try:
            health_data = {
                **self._health_status,
                'metrics': self.communication_metrics,
                'agent_count': len(self.agent_directory),
                'active_agents': len([a for a, p in self.agent_presence.items()
                                    if p.get('status') == AgentStatus.ACTIVE.value]),
                'total_queued': sum(len(q) for q in self.message_queue.values()),
                'pending_count': len(self.pending_messages),
                'circuit_breakers': {
                    name: breaker['state']
                    for name, breaker in self._circuit_breakers.items()
                }
            }
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps(health_data).encode())
        
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
    
    async def _handle_diagnostics(self, msg):
        """Handle diagnostics requests"""
        try:
            diagnostics = {
                'agent_directory': self.agent_directory,
                'agent_presence': self.agent_presence,
                'queue_depths': {name: len(q) for name, q in self.message_queue.items()},
                'routes': [asdict(r) for r in self.message_routes[:10]],  # First 10 routes
                'conversations': len(self.conversations),
                'delivery_receipts': len(self.delivery_receipts),
                'failed_deliveries': {k: len(v) for k, v in list(self.failed_deliveries.items())[:10]}
            }
            
            if msg.reply:
                await self._publish(msg.reply, json.dumps(diagnostics).encode())
        
        except Exception as e:
            self.logger.error("Diagnostics failed", error=str(e))
    
    # Helper methods
    
    def _get_agents_by_group(self, group_name: str) -> List[str]:
        """Get agents by group/type"""
        if group_name == "all":
            return list(self.agent_directory.keys())
        elif group_name == "active":
            return [name for name, info in self.agent_presence.items()
                   if info.get("status") == AgentStatus.ACTIVE.value]
        else:
            # Group by agent type
            return [name for name, info in self.agent_directory.items()
                   if info.get("agent_type") == group_name]
    
    # Filter implementations
    
    def _priority_filter(self, message: Message, payload: Dict) -> bool:
        """Filter based on message priority"""
        min_priority = payload.get("min_priority", MessagePriority.LOW.value)
        return message.priority.value >= min_priority
    
    def _agent_availability_filter(self, message: Message, payload: Dict) -> bool:
        """Filter if recipient agents are not available"""
        for recipient in message.recipients:
            if recipient not in self.agent_presence:
                return False
            if self.agent_presence[recipient].get("status") != AgentStatus.ACTIVE.value:
                return False
        return True
    
    def _message_size_filter(self, message: Message, payload: Dict) -> bool:
        """Filter oversized messages"""
        max_size = payload.get("max_size_bytes", MAX_MESSAGE_SIZE)
        current_size = message.size_bytes()
        
        if current_size > max_size:
            self.logger.warning("Message exceeds size limit",
                              message_id=message.id,
                              size=current_size,
                              limit=max_size)
            return False
        return True
    
    def _rate_limit_filter(self, message: Message, payload: Dict) -> bool:
        """Rate limiting filter"""
        limit_key = f"{message.sender}-{message.type.value}"
        max_requests = payload.get("max_requests", DEFAULT_RATE_LIMIT)
        time_window = payload.get("time_window_seconds", RATE_LIMIT_WINDOW)
        
        current_time = time.time()
        
        # Clean old timestamps
        while self._rate_limits[limit_key] and \
              self._rate_limits[limit_key][0] < current_time - time_window:
            self._rate_limits[limit_key].popleft()
        
        if len(self._rate_limits[limit_key]) >= max_requests:
            self.logger.warning("Rate limit exceeded",
                              sender=message.sender,
                              type=message.type.value)
            self.communication_metrics['rate_limit_hits'] += 1
            return False
        
        self._rate_limits[limit_key].append(current_time)
        return True
    
    def _security_filter(self, message: Message, payload: Dict) -> bool:
        """Security validation filter"""
        # Check for suspicious patterns
        payload_str = json.dumps(payload)
        
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'eval\(',
            r'exec\(',
            r'__import__'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, payload_str, re.IGNORECASE):
                self.logger.warning("Suspicious content detected",
                                  message_id=message.id,
                                  pattern=pattern)
                return False
        
        return True
    
    def _duplicate_filter(self, message: Message, payload: Dict) -> bool:
        """Filter duplicate messages"""
        # Check recent message history for duplicates
        message_hash = hashlib.sha256(
            f"{message.sender}{message.subject}{json.dumps(message.payload)}".encode()
        ).hexdigest()
        
        # Check last 100 messages for duplicates
        for hist_msg in list(self.message_history)[-100:]:
            hist_hash = hashlib.sha256(
                f"{hist_msg['sender']}{hist_msg['subject']}{json.dumps(hist_msg['payload'])}".encode()
            ).hexdigest()
            
            if message_hash == hist_hash:
                time_diff = time.time() - hist_msg['created_at']
                if time_diff < 60:  # Within last minute
                    self.logger.warning("Duplicate message detected",
                                      message_id=message.id)
                    return False
        
        return True
    
    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Enhanced metrics reporting"""
        base_metrics = super()._get_agent_metrics()
        base_metrics.update({
            **self.communication_metrics,
            "queued_messages_count": sum(len(q) for q in self.message_queue.values()),
            "pending_messages_count": len(self.pending_messages),
            "pending_acks_count": len([mid for mid, rec in self.delivery_receipts.items()
                                     if rec.get("status") == "pending_ack"]),
            "registered_agents": len(self.agent_directory),
            "active_agents": len([a for a, p in self.agent_presence.items()
                                if p.get('status') == AgentStatus.ACTIVE.value]),
            "routes_count": len(self.message_routes),
            "active_conversations": len(self.conversations),
            "health_status": self._health_status['status']
        })
        return base_metrics


if __name__ == "__main__":
    import time
    
    config = AgentConfig(
        name="communication_agent",
        agent_type="communication",
        capabilities=[
            "send_message", "broadcast_message", "multicast_message",
            "request_response", "publish_event", "manage_routes",
            "manage_conversations", "agent_presence_monitoring",
            "health_checks", "diagnostics"
        ],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    
    agent = CommunicationAgent(config)
    asyncio.run(agent.run())