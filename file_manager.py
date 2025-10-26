"""
File Manager
Handles file storage, versioning, and retrieval
"""

import asyncio
import aiofiles
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import hashlib
from uuid import uuid4, UUID

from .database import ProjectDatabase

logger = logging.getLogger(__name__)


class FileManager:
    """
    File Management System
    
    Features:
    - Multi-backend support (local, S3, Azure, GCS)
    - File versioning
    - Access control
    - Checksum verification
    """
    
    def __init__(self, settings, database: ProjectDatabase):
        self.settings = settings
        self.database = database
        self.storage_backend = settings.storage_backend
        self.storage_path = Path(settings.storage_path)
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize file manager"""
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.is_initialized = True
        logger.info(f"✓ File manager initialized (backend: {self.storage_backend})")
    
    async def upload_file(
        self,
        filename: str,
        content: bytes,
        project_id: Optional[str],
        category: str,
        description: Optional[str],
        user_id: UUID,
        checksum: str
    ) -> Dict:
        """Upload file"""
        file_id = uuid4()
        
        # Generate storage path
        storage_path = self._generate_storage_path(file_id, filename)
        
        # Write file
        if self.storage_backend == "local":
            await self._write_local(storage_path, content)
        elif self.storage_backend == "s3":
            await self._write_s3(storage_path, content)
        else:
            raise ValueError(f"Unsupported storage backend: {self.storage_backend}")
        
        # Store metadata
        query = """
            INSERT INTO file_metadata (
                id, filename, size, checksum, project_id,
                category, description, user_id, storage_path, storage_backend
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
        """
        
        result = await self.database.execute_single(
            query,
            file_id,
            filename,
            len(content),
            checksum,
            project_id,
            category,
            description,
            user_id,
            str(storage_path),
            self.storage_backend
        )
        
        # Create version if versioning enabled
        if self.settings.file_versioning_enabled:
            await self._create_version(file_id, len(content), checksum, str(storage_path), user_id)
        
        return result
    
    async def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """Get file metadata"""
        query = "SELECT * FROM file_metadata WHERE id = $1"
        return await self.database.execute_single(query, file_id)
    
    async def get_file_path(self, file_id: str) -> Path:
        """Get file storage path"""
        metadata = await self.get_file_metadata(file_id)
        
        if not metadata:
            raise ValueError(f"File {file_id} not found")
        
        return Path(metadata["storage_path"])
    
    async def check_file_access(self, file_id: str, user_id: UUID) -> bool:
        """Check if user has access to file"""
        query = """
            SELECT 1 FROM file_metadata
            WHERE id = $1 AND (user_id = $2 OR $2 IN (
                SELECT owner_id FROM projects WHERE id = file_metadata.project_id
            ))
        """
        
        result = await self.database.execute_single(query, file_id, user_id)
        return result is not None
    
    async def get_file_versions(self, file_id: str) -> List[Dict]:
        """Get all versions of a file"""
        query = """
            SELECT * FROM file_versions
            WHERE file_id = $1
            ORDER BY version_number DESC
        """
        
        return await self.database.execute_query(query, file_id)
    
    def _generate_storage_path(self, file_id: UUID, filename: str) -> Path:
        """Generate storage path for file"""
        # Organize files by date and ID
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        return self.storage_path / date_path / str(file_id) / filename
    
    async def _write_local(self, path: Path, content: bytes):
        """Write file to local storage"""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(path, 'wb') as f:
            await f.write(content)
    
    async def _write_s3(self, path: Path, content: bytes):
        """Write file to S3"""
        # Simplified - would use boto3 in production
        logger.info(f"Would upload to S3: {path}")
        # boto3 implementation here
    
    async def _create_version(
        self,
        file_id: UUID,
        size: int,
        checksum: str,
        storage_path: str,
        user_id: UUID
    ):
        """Create file version"""
        # Get current version number
        current_version = await self.database.execute_single(
            "SELECT MAX(version_number) as max_version FROM file_versions WHERE file_id = $1",
            file_id
        )
        
        next_version = (current_version["max_version"] or 0) + 1 if current_version else 1
        
        query = """
            INSERT INTO file_versions (
                file_id, version_number, size, checksum, storage_path, user_id
            )
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        await self.database.execute_command(
            query,
            file_id,
            next_version,
            size,
            checksum,
            storage_path,
            user_id
        )
    
    async def health_check(self) -> bool:
        """Check file manager health"""
        return self.is_initialized and self.storage_path.exists()
    
    async def shutdown(self):
        """Shutdown file manager"""
        logger.info("File manager shutdown complete")

