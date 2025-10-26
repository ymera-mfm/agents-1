"""
Submission Models
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class SubmissionStatus(str, Enum):
    """Submission status"""
    PENDING = "pending"
    VERIFYING = "verifying"
    APPROVED = "approved"
    REJECTED = "rejected"
    INTEGRATED = "integrated"
    ERROR = "error"


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QualityFeedback(BaseModel):
    """Quality feedback model"""
    severity: IssueSeverity
    category: str
    description: str
    file: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None


class AgentSubmission(BaseModel):
    """Agent submission model"""
    model_config = ConfigDict(use_enum_values=True)
    
    id: Optional[UUID] = None
    agent_id: str
    project_id: UUID
    module_name: str
    output_type: str  # code, documentation, test, config
    files: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: SubmissionStatus = SubmissionStatus.PENDING
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    issues: List[QualityFeedback] = Field(default_factory=list)
    message: Optional[str] = None
    user_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
