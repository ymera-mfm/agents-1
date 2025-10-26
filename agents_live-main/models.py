
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[UUID] = None
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        import re
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Invalid email format")
        return v.lower()


class AgentStatus(str, Enum):
    """Agent status enum"""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class Agent(BaseModel):
    """Agent model for compatibility"""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[UUID] = None
    name: str
    type: str
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[str] = []
    config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Task model for compatibility"""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    agent_id: Optional[UUID] = None
    priority: int = 0
    parameters: Dict[str, Any] = {}
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Experience(BaseModel):
    id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    feedback_score: Optional[int] = None
    metadata: Dict[str, Any] = {}
    processed: bool = False
    created_at: Optional[datetime] = None
    
    @field_validator("feedback_score")
    @classmethod
    def validate_feedback(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Feedback score must be between 1 and 5")
        return v

class KnowledgeItem(BaseModel):
    id: Optional[UUID] = None
    title: str
    content: str
    tags: List[str] = []
    category: Optional[str] = None
    confidence_score: float = 0.0
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

