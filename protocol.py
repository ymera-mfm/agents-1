# communication/protocol.py
"""
Standardized Agent-Manager Communication Protocol
Ensures consistent, secure, and versioned messaging between components
"""

import json
import uuid
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

class MessageType(str, Enum):
    """Standard message types for agent-manager communication"""
    HEARTBEAT = "heartbeat"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    STATUS_REPORT = "status_report"
    SECURITY_ALERT = "security_alert"
    CONFIGURATION_UPDATE = "configuration_update"
    CONTROL_COMMAND = "control_command"
    SYSTEM_METRICS = "system_metrics"

class ProtocolVersion(str, Enum):
    """Protocol versions with backward compatibility"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"

class AgentMessage(BaseModel):
    """Base message format for agent communication"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: str
    message_type: MessageType
    protocol_version: ProtocolVersion = ProtocolVersion.V2_0
    payload: Dict[str, Any]
    sequence_number: Optional[int] = None
    correlation_id: Optional[str] = None
    ttl: int = 60  # Time to live in seconds
    
    @validator('payload')
    def validate_payload_schema(cls, v, values):
        """Validate payload schema based on message type"""
        msg_type = values.get('message_type')
        if not msg_type:
            return v
            
        # Schema validation based on message type
        if msg_type == MessageType.HEARTBEAT:
            required_fields = {'status', 'health'}
            if not required_fields.issubset(v.keys()):
                missing = required_fields - set(v.keys())
                raise ValueError(f"Missing required fields for {msg_type}: {missing}")
        
        elif msg_type == MessageType.TASK_RESULT:
            required_fields = {'task_id', 'status', 'result'}
            if not required_fields.issubset(v.keys()):
                missing = required_fields - set(v.keys())
                raise ValueError(f"Missing required fields for {msg_type}: {missing}")
        
        return v

class ProtocolManager:
    """Manager for protocol operations and validation"""
    
    @staticmethod
    def create_message(agent_id: str, message_type: MessageType, payload: Dict[str, Any], 
                     correlation_id: Optional[str] = None) -> AgentMessage:
        """Create a properly formatted message"""
        return AgentMessage(
            agent_id=agent_id,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id or str(uuid.uuid4())
        )
    
    @staticmethod
    def validate_message(message_data: Dict[str, Any]) -> AgentMessage:
        """Validate incoming message against protocol standards"""
        try:
            # Parse and validate with Pydantic model
            message = AgentMessage.parse_obj(message_data)
            
            # Additional validation logic can be added here
            return message
        except Exception as e:
            raise ValueError(f"Invalid message format: {e}")
    
    @staticmethod
    async def process_message(message: AgentMessage) -> Dict[str, Any]:
        """Process message based on type and version"""
        # Protocol version handling for backwards compatibility
        if message.protocol_version == ProtocolVersion.V1_0:
            # Legacy processing
            pass
        
        # Default to current version processing
        return {
            "message_id": message.id,
            "processed_timestamp": datetime.utcnow().isoformat(),
            "status": "processed"
        }