"""
File Models
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class FileMetadata(BaseModel):
    """File metadata model"""
    id: Optional[UUID] = None
    filename: str
    size: int = Field(..., ge=0)
    checksum: str
    mime_type: Optional[str] = None
    project_id: Optional[UUID] = None
    category: str = "general"
    description: Optional[str] = None
    user_id: Optional[UUID] = None
    storage_path: str
    storage_backend: str = "local"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FileVersion(BaseModel):
    """File version model"""
    id: Optional[UUID] = None
    file_id: UUID
    version_number: int = Field(..., ge=1)
    size: int = Field(..., ge=0)
    checksum: str
    storage_path: str
    user_id: Optional[UUID] = None
    change_description: Optional[str] = None
    created_at: Optional[datetime] = None
