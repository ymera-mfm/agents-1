# tests/unit/test_security.py
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from src.core.security import SecurityUtils, get_current_user, require_role
from src.models.user import UserRecord

class TestSecurityUtils:
    """Unit tests for security utilities"""
    
    def test_hash_password(self):
        """Test password hashing and verification"""
        password = "securepassword123"
        hashed = SecurityUtils.hash_password(password)
        
        assert SecurityUtils.verify_password(password, hashed)
        assert not SecurityUtils.verify_password("wrongpassword", hashed)
    
    def test_generate_verify_jwt(self):
        """Test JWT generation and verification"""
        payload = {"user_id": "123", "username": "testuser"}
        token = SecurityUtils.generate_jwt(payload)
        
        decoded = SecurityUtils.verify_jwt(token)
        assert decoded["user_id"] == "123"
        assert decoded["username"] == "testuser"
    
    def test_generate_api_key(self):
        """Test API key generation"""
        key, key_hash = SecurityUtils.generate_api_key()
        
        assert len(key) == 43  # 32 bytes base64 encoded
        assert len(key_hash) == 64  # SHA256 hex digest
    
    def test_encrypt_decrypt_data(self):
        """Test data encryption and decryption"""
        original_data = b"sensitive data"
        encrypted = SecurityUtils.encrypt_data(original_data)
        decrypted = SecurityUtils.decrypt_data(encrypted)
        
        assert decrypted == original_data
    
    def test_mfa_verification(self):
        """Test MFA code verification"""
        secret = SecurityUtils.generate_mfa_secret()
        # Mock TOTP generation for testing
        with patch('pyotp.TOTP.now', return_value="123456"):
            assert SecurityUtils.verify_mfa_code(secret, "123456")

class TestAuthentication:
    """Unit tests for authentication"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, test_session, test_user):
        """Test getting current user with valid token"""
        user = await test_user()
        token = SecurityUtils.generate_jwt({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value
        })
        
        current_user = await get_current_user(token)
        assert current_user.id == user.id
        assert current_user.username == user.username
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_require_role_admin(self, test_session, test_user):
        """Test role requirement for admin"""
        user = await test_user()
        user.role = "admin"
        
        # Should not raise exception for admin
        await require_role("admin")(user)
    
    @pytest.mark.asyncio
    async def test_require_role_unauthorized(self, test_session, test_user):
        """Test role requirement for unauthorized user"""
        user = await test_user()
        user.role = "member"
        
        with pytest.raises(HTTPException) as exc_info:
            await require_role("admin")(user)
        
        assert exc_info.value.status_code == 403