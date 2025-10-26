"""
Encryption Manager for Unified Agent System
Provides encryption/decryption utilities
"""

import base64
import os
from typing import Optional
import structlog

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None

from shared.config.settings import Settings

logger = structlog.get_logger(__name__)


class EncryptionManager:
    """Manages encryption and decryption operations"""
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cipher: Optional[Any] = None
        self.logger = structlog.get_logger(__name__)
        
        if not CRYPTO_AVAILABLE:
            self.logger.warning("Cryptography library not available, encryption disabled")
            return
        
        # Initialize cipher
        self._initialize_cipher()
    
    def _initialize_cipher(self):
        """Initialize Fernet cipher"""
        try:
            # Get or generate encryption key
            key = self.settings.ENCRYPTION_KEY
            
            if not key:
                # Generate a new key (should be stored securely in production)
                key = Fernet.generate_key().decode()
                self.logger.warning("No encryption key provided, generated temporary key")
            
            # Ensure key is bytes
            if isinstance(key, str):
                key = key.encode()
            
            self.cipher = Fernet(key)
            self.logger.info("Encryption initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            self.cipher = None
    
    def encrypt(self, data: str) -> Optional[str]:
        """Encrypt string data"""
        if not CRYPTO_AVAILABLE or not self.cipher:
            self.logger.warning("Encryption not available, returning plaintext")
            return data
        
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            self.logger.error(f"Encryption error: {e}")
            return None
    
    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt string data"""
        if not CRYPTO_AVAILABLE or not self.cipher:
            self.logger.warning("Decryption not available, returning as-is")
            return encrypted_data
        
        try:
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password (one-way)"""
        try:
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()
        except Exception as e:
            self.logger.error(f"Password hashing error: {e}")
            return password
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key"""
        if not CRYPTO_AVAILABLE:
            return "encryption-not-available"
        return Fernet.generate_key().decode()
