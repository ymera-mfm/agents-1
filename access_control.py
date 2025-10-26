"""
Agent Access Controller
Manages agent permissions and access control
"""

import structlog
import uuid
import secrets
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.security.encryption import EncryptionManager
from ..core.models import AgentPermissionModel, AgentType

logger = structlog.get_logger(__name__)


class AgentAccessController:
    """Controls agent access and permissions"""
    
    def __init__(self, db_session: AsyncSession, encryption_manager: EncryptionManager):
        self.db = db_session
        self.encryption = encryption_manager
    
    async def create_agent_credentials(
        self,
        agent_id: str,
        agent_type: AgentType,
        capabilities: List[str]
    ) -> Dict[str, Any]:
        """Create secure credentials for an agent"""
        try:
            # Generate API key
            api_key = f"ymera_{secrets.token_urlsafe(32)}"
            api_secret = secrets.token_urlsafe(64)
            
            # Encrypt credentials
            encrypted_secret = await self.encryption.encrypt(api_secret)
            
            credentials = {
                "api_key": api_key,
                "api_secret_hash": encrypted_secret,
                "agent_type": agent_type,
                "capabilities": capabilities,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
            }
            
            return {
                "api_key": api_key,
                "api_secret": api_secret,  # Return plaintext only once
                "expires_at": credentials["expires_at"]
            }
            
        except Exception as e:
            logger.error("Failed to create credentials", agent_id=agent_id, error=str(e))
            raise
    
    async def check_permission(
        self,
        agent_id: str,
        resource: str,
        action: str
    ) -> bool:
        """Check if agent has permission for action on resource"""
        try:
            stmt = select(AgentPermissionModel).where(
                and_(
                    AgentPermissionModel.agent_id == agent_id,
                    AgentPermissionModel.resource == resource,
                    AgentPermissionModel.revoked_at.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            permission = result.scalar_one_or_none()
            
            if not permission:
                return False
            
            # Check if permission has expired
            if permission.expires_at and permission.expires_at < datetime.utcnow():
                return False
            
            # Check if action is allowed
            return action in permission.actions
            
        except Exception as e:
            logger.error("Permission check failed", agent_id=agent_id, error=str(e))
            return False
    
    async def grant_permission(
        self,
        agent_id: str,
        resource: str,
        actions: List[str],
        granted_by: str,
        expires_in_days: int = 365
    ) -> Dict[str, Any]:
        """Grant permissions to an agent"""
        try:
            permission = AgentPermissionModel(
                permission_id=str(uuid.uuid4()),
                agent_id=agent_id,
                resource=resource,
                actions=actions,
                granted_at=datetime.utcnow(),
                granted_by=granted_by,
                expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
            )
            
            self.db.add(permission)
            await self.db.commit()
            
            logger.info("Permission granted", agent_id=agent_id, resource=resource)
            
            return {
                "status": "granted",
                "permission_id": permission.permission_id,
                "agent_id": agent_id,
                "resource": resource,
                "actions": actions
            }
            
        except Exception as e:
            logger.error("Failed to grant permission", agent_id=agent_id, error=str(e))
            raise
    
    async def revoke_permission(
        self,
        agent_id: str,
        resource: str,
        actions: List[str],
        revoked_by: str
    ) -> Dict[str, Any]:
        """Revoke permissions from an agent"""
        try:
            stmt = select(AgentPermissionModel).where(
                and_(
                    AgentPermissionModel.agent_id == agent_id,
                    AgentPermissionModel.resource == resource,
                    AgentPermissionModel.revoked_at.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            permission = result.scalar_one_or_none()
            
            if permission:
                permission.revoked_at = datetime.utcnow()
                permission.revoked_by = revoked_by
                permission.revoke_reason = "Manual revocation"
                await self.db.commit()
            
            logger.info("Permission revoked", agent_id=agent_id, resource=resource)
            
            return {
                "status": "revoked",
                "agent_id": agent_id,
                "resource": resource
            }
            
        except Exception as e:
            logger.error("Failed to revoke permission", agent_id=agent_id, error=str(e))
            raise
    
    async def revoke_agent_access(self, agent_id: str):
        """Revoke all access for an agent"""
        try:
            stmt = select(AgentPermissionModel).where(
                and_(
                    AgentPermissionModel.agent_id == agent_id,
                    AgentPermissionModel.revoked_at.is_(None)
                )
            )
            result = await self.db.execute(stmt)
            permissions = result.scalars().all()
            
            for permission in permissions:
                permission.revoked_at = datetime.utcnow()
                permission.revoked_by = "system"
                permission.revoke_reason = "Agent access revoked"
            
            await self.db.commit()
            
            logger.info("All access revoked for agent", agent_id=agent_id)
            
        except Exception as e:
            logger.error("Failed to revoke agent access", agent_id=agent_id, error=str(e))
            raise
    
    async def revoke_all_access(self, agent_id: str):
        """Complete access revocation (alias for revoke_agent_access)"""
        await self.revoke_agent_access(agent_id)
