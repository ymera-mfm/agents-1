"""File Handler for upload/download operations"""

import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import structlog

from shared.config.settings import Settings


class FileHandler:
    """Handles file upload and download operations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = structlog.get_logger(__name__)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.file_registry = {}
    
    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Upload a file"""
        try:
            # Validate file size
            if len(file_data) > self.settings.MAX_UPLOAD_SIZE:
                return {
                    'success': False,
                    'error': f"File size exceeds maximum allowed size of {self.settings.MAX_UPLOAD_SIZE} bytes"
                }
            
            # Validate file extension
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.settings.ALLOWED_EXTENSIONS:
                return {
                    'success': False,
                    'error': f"File type {file_ext} not allowed"
                }
            
            # Generate unique file ID
            file_hash = hashlib.sha256(file_data).hexdigest()
            file_id = f"{file_hash[:16]}_{int(datetime.utcnow().timestamp())}"
            
            # Determine storage path
            storage_path = self.upload_dir / file_id / filename
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            storage_path.write_bytes(file_data)
            
            # Register file
            self.file_registry[file_id] = {
                'filename': filename,
                'path': str(storage_path),
                'size': len(file_data),
                'hash': file_hash,
                'uploaded_at': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            self.logger.info(f"File uploaded: {filename} ({file_id})")
            
            return {
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'size': len(file_data),
                'hash': file_hash
            }
            
        except Exception as e:
            self.logger.error(f"File upload error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    async def download_file(self, file_id: str) -> Tuple[Optional[bytes], Optional[str]]:
        """Download a file"""
        try:
            if file_id not in self.file_registry:
                self.logger.warning(f"File not found: {file_id}")
                return None, None
            
            file_info = self.file_registry[file_id]
            file_path = Path(file_info['path'])
            
            if not file_path.exists():
                self.logger.error(f"File path does not exist: {file_path}")
                return None, None
            
            file_data = file_path.read_bytes()
            filename = file_info['filename']
            
            self.logger.info(f"File downloaded: {filename} ({file_id})")
            
            return file_data, filename
            
        except Exception as e:
            self.logger.error(f"File download error: {e}", exc_info=True)
            return None, None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file"""
        try:
            if file_id not in self.file_registry:
                return False
            
            file_info = self.file_registry[file_id]
            file_path = Path(file_info['path'])
            
            if file_path.exists():
                file_path.unlink()
            
            del self.file_registry[file_id]
            
            self.logger.info(f"File deleted: {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"File deletion error: {e}", exc_info=True)
            return False
    
    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        return self.file_registry.get(file_id)
