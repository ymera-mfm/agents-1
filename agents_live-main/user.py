"""
User Models
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"


class User(BaseModel):
    """User model"""
    model_config = ConfigDict(use_enum_values=True)
    
    id: Optional[UUID] = None
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v.lower()
