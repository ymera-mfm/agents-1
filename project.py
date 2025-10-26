"""
Project Models
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class ProjectPhase(str, Enum):
    """Project phases"""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class Project(BaseModel):
    """Project model"""
    model_config = ConfigDict(use_enum_values=True)
    
    id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    owner_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
