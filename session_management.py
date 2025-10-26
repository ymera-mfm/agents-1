# security/session_manager.py
"""
Production-ready session management with Redis backend
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from redis import asyncio as aioredis
import secrets
import json
import hashlib
from pydantic import BaseModel

class SessionData(BaseModel):
    user_id: str
    email: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    metadata: Dict[str, Any] = {}

class SessionManager:
    """Secure session management with Redis"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        session_timeout_minutes: int = 30,
        max_sessions_per_user: int = 5
    ):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.max_sessions = max_sessions_per_user
    
    def _generate_session_id(self) -> str:
        """Generate cryptographically secure session ID"""
        return secrets.token_urlsafe(32)
    
    def _session_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"session:{session_id}"
    
    def _user_sessions_key(self, user_id: str) -> str:
        """Get Redis key for user's active sessions"""
        return f"user_sessions:{user_id}"
    
    async def create_session(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[str, SessionData]:
        """Create a new session"""
        
        # Check concurrent session limit
        await self._enforce_session_limit(user_id)
        
        session_id = self._generate_session_id()
        now = datetime.utcnow()
        
        session_data = SessionData(
            user_id=user_id,
            email=email,
            created_at=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        # Store session
        session_key = self._session_key(session_id)
        await self.redis.setex(
            session_key,
            int(self.session_timeout.total_seconds()),
            session_data.model_dump_json()
        )
        
        # Add to user's session list
        user_sessions_key = self._user_sessions_key(user_id)
        await self.redis.sadd(user_sessions_key, session_id)
        await self.redis.expire(user_sessions_key, int(self.session_timeout.total_seconds()))
        
        return session_id, session_data
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Retrieve session data"""
        session_key = self._session_key(session_id)
        data = await self.redis.get(session_key)
        
        if not data:
            return None
        
        return SessionData.model_validate_json(data)
    
    async def update_activity(self, session_id: str) -> bool:
        """Update last activity timestamp and extend session"""
        session = await self.get_session(session_id)
        
        if not session:
            return False
        
        session.last_activity = datetime.utcnow()
        
        session_key = self._session_key(session_id)
        await self.redis.setex(
            session_key,
            int(self.session_timeout.total_seconds()),
            session.model_dump_json()
        )
        
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a specific session"""
        session = await self.get_session(session_id)
        
        if not session:
            return False
        
        # Remove from Redis
        session_key = self._session_key(session_id)
        await self.redis.delete(session_key)
        
        # Remove from user's session list
        user_sessions_key = self._user_sessions_key(session.user_id)
        await self.redis.srem(user_sessions_key, session_id)
        
        return True
    
    async def delete_all_user_sessions(self, user_id: str):
        """Delete all sessions for a user (e.g., on password change)"""
        user_sessions_key = self._user_sessions_key(user_id)
        session_ids = await self.redis.smembers(user_sessions_key)
        
        if session_ids:
            # Delete all session keys
            pipe = self.redis.pipeline()
            for session_id in session_ids:
                pipe.delete(self._session_key(session_id))
            pipe.delete(user_sessions_key)
            await pipe.execute()
    
    async def get_user_sessions(self, user_id: str) -> list[tuple[str, SessionData]]:
        """Get all active sessions for a user"""
        user_sessions_key = self._user_sessions_key(user_id)
        session_ids = await self.redis.smembers(user_sessions_key)
        
        sessions = []
        for session_id in session_ids:
            session = await self.get_session(session_id)
            if session:
                sessions.append((session_id, session))
        
        return sessions
    
    async def _enforce_session_limit(self, user_id: str):
        """Enforce maximum concurrent sessions per user"""
        sessions = await self.get_user_sessions(user_id)
        
        if len(sessions) >= self.max_sessions:
            # Sort by last activity, delete oldest
            sessions.sort(key=lambda x: x[1].last_activity)
            
            # Delete oldest sessions to make room
            to_delete = len(sessions) - self.max_sessions + 1
            for session_id, _ in sessions[:to_delete]:
                await self.delete_session(session_id)
    
    async def validate_session_security(
        self,
        session_id: str,
        current_ip: str,
        current_user_agent: str,
        check_ip: bool = True,
        check_user_agent: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Validate session security (detect hijacking attempts)
        Returns: (is_valid, reason)
        """
        session = await self.get_session(session_id)
        
        if not session:
            return False, "Session not found"
        
        # Check IP address match
        if check_ip and session.ip_address != current_ip:
            return False, "IP address mismatch"
        
        # Check user agent match
        if check_user_agent and session.user_agent != current_user_agent:
            return False, "User agent mismatch"
        
        return True, None


# security/token_manager.py
"""
JWT token management with httpOnly cookies
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import Response, Request, HTTPException, status
from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: str
    email: str
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token revocation

class TokenManager:
    """Secure JWT token management"""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)
        
        # Token blacklist (use Redis in production)
        self.redis = None  # Initialize with Redis connection
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create JWT access token"""
        now = datetime.utcnow()
        claims = {
            "user_id": user_id,
            "email": email,
            "exp": now + self.access_token_expire,
            "iat": now,
            "jti": secrets.token_urlsafe(16),
            "type": "access"
        }
        
        if additional_claims:
            claims.update(additional_claims)
        
        return jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str, email: str) -> str:
        """Create JWT refresh token"""
        now = datetime.utcnow()
        claims = {
            "user_id": user_id,
            "email": email,
            "exp": now + self.refresh_token_expire,
            "iat": now,
            "jti": secrets.token_urlsafe(16),
            "type": "refresh"
        }
        
        return jwt.encode(claims, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            # Check if token is blacklisted
            if self.redis and self._is_blacklisted(payload.get("jti")):
                return None
            
            return payload
        
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def set_auth_cookies(
        self,
        response: Response,
        access_token: str,
        refresh_token: str,
        secure: bool = True
    ):
        """Set authentication cookies (httpOnly for security)"""
        
        # Access token cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure,
            samesite="strict",
            max_age=int(self.access_token_expire.total_seconds())
        )
        
        # Refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure,
            samesite="strict",
            max_age=int(self.refresh_token_expire.total_seconds())
        )
    
    def clear_auth_cookies(self, response: Response):
        """Clear authentication cookies"""
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
    
    def get_token_from_cookie(self, request: Request) -> Optional[str]:
        """Extract token from httpOnly cookie"""
        return request.cookies.get("access_token")
    
    async def blacklist_token(self, jti: str, exp: datetime):
        """Add token to blacklist"""
        if not self.redis:
            return
        
        ttl = int((exp - datetime.utcnow()).total_seconds())
        if ttl > 0:
            await self.redis.setex(f"blacklist:{jti}", ttl, "1")
    
    def _is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis:
            return False
        
        # Synchronous check - implement async version in production
        return False  # Placeholder
