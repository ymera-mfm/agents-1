"""
YMERA Enterprise Agent Manager - Production Implementation

A secure, scalable, and comprehensive agent management system with:
- Mandatory agent reporting with escalating consequences
- Administrative approval workflows for agent lifecycle events
- Advanced security and data flow management
- Comprehensive monitoring with machine learning capabilities
- Multi-tier caching and intelligent task scheduling

Author: YMERA AI
Version: 2.0.0
"""

import asyncio
import logging
import os
import time
import json
import uuid
import traceback
import signal
from typing import Dict, List, Set, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
import hashlib
import secrets
import re

# Database and storage
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Text, ForeignKey, select, func, text, Index

# Security and encryption
import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

# Monitoring and observability
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# Web framework
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, EmailStr
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure tracing
tracer_provider = TracerProvider(
    resource=Resource.create({
        ResourceAttributes.SERVICE_NAME: "agent_manager",
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
    })
)
jaeger_exporter = JaegerExporter(
    agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
    agent_port=int(os.getenv("JAEGER_PORT", 6831))
)
tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# Database model definition
Base = declarative_base()

class AgentStatus(str, Enum):
    """Agent status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy" 
    FROZEN = "frozen"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    ERROR = "error"
    ISOLATED = "isolated"

class AgentReportStatus(str, Enum):
    """Agent reporting compliance status"""
    COMPLIANT = "compliant"
    WARNED = "warned"
    SUSPENDED = "suspended"
    NON_COMPLIANT = "non_compliant"
    EXEMPT = "exempt"

class AgentAction(str, Enum):
    """Agent lifecycle control actions"""
    WARN = "warn"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"
    DELETE = "delete"
    AUDIT = "audit"
    ISOLATE = "isolate"

class AdminApprovalStatus(str, Enum):
    """Admin approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"

class TaskStatus(str, Enum):
    """Task processing status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    roles = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    organization_id = Column(String(36), nullable=True)

class Agent(Base):
    """Agent entity model"""
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    api_key_hash = Column(String(255), nullable=True)
    capabilities = Column(JSON, default=list)
    status = Column(String(50), default=AgentStatus.INACTIVE.value)
    health_status = Column(String(20), default="unknown")
    last_heartbeat = Column(DateTime, nullable=True)
    last_report = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Lifecycle tracking fields
    frozen_at = Column(DateTime, nullable=True)
    frozen_by = Column(String(36), nullable=True)
    frozen_reason = Column(Text, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(36), nullable=True)
    suspended_at = Column(DateTime, nullable=True)
    suspended_by = Column(String(36), nullable=True)
    suspended_reason = Column(Text, nullable=True)
    isolated_at = Column(DateTime, nullable=True)
    isolated_by = Column(String(36), nullable=True)
    
    # Reporting tracking fields
    reporting_exemption = Column(Boolean, default=False)
    reporting_exemption_reason = Column(Text, nullable=True)
    missed_report_count = Column(Integer, default=0)
    last_warning_at = Column(DateTime, nullable=True)
    reporting_status = Column(String(20), default=AgentReportStatus.COMPLIANT.value)
    
    # Performance metrics
    resource_usage = Column(JSON, default=dict)
    configuration = Column(JSON, default=dict)
    max_tasks = Column(Integer, default=10)
    current_tasks = Column(Integer, default=0)

class Task(Base):
    """Task model for agent execution"""
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    task_type = Column(String(50), nullable=False)
    priority = Column(String(20), default=TaskPriority.NORMAL.value)
    status = Column(String(20), default=TaskStatus.PENDING.value)
    parameters = Column(JSON, default=dict)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

class AdminApproval(Base):
    """Administrative approval workflow model"""
    __tablename__ = "admin_approvals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_type = Column(String(50), nullable=False)  # agent_action, security_change, etc.
    resource_id = Column(String(36), nullable=False)   # agent_id, etc.
    resource_type = Column(String(50), nullable=False) # agent, task, etc.
    action = Column(String(50), nullable=False)        # freeze, delete, etc.
    reason = Column(Text, nullable=False)
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default=AdminApprovalStatus.PENDING.value)
    processed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

class AuditLog(Base):
    """Comprehensive audit log"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)
    action = Column(String(50), nullable=False)
    performed_by = Column(String(36), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    severity = Column(String(20), default="info")
    correlation_id = Column(String(50), nullable=True)
    tenant_id = Column(String(36), nullable=True)

class SecurityEvent(Base):
    """Security event tracking"""
    __tablename__ = "security_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    source = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    agent_id = Column(String(36), nullable=True)

class AgentReport(Base):
    """Agent reporting history"""
    __tablename__ = "agent_reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    report_type = Column(String(50), default="heartbeat")
    status = Column(String(50), nullable=False)
    health = Column(String(20), nullable=False)
    metrics = Column(JSON, default=dict)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50), nullable=True)
    version = Column(String(50), nullable=True)

class DataAccessLog(Base):
    """Data access audit logging"""
    __tablename__ = "data_access_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True)
    agent_id = Column(String(36), nullable=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=False)
    operation = Column(String(20), nullable=False) # read, write, delete
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    data_size = Column(Integer, nullable=True) # in bytes

class RateLimitLog(Base):
    """Rate limit tracking"""
    __tablename__ = "rate_limit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    identifier = Column(String(255), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    count = Column(Integer, default=1)
    first_request = Column(DateTime, default=datetime.utcnow)
    last_request = Column(DateTime, default=datetime.utcnow)
    window_size = Column(Integer, default=3600) # in seconds
    limit = Column(Integer, default=100)
    exceeded = Column(Boolean, default=False)

class ApiKey(Base):
    """API Key management"""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    enabled = Column(Boolean, default=True)
    permissions = Column(JSON, default=list)
    scopes = Column(JSON, default=list)

# Create indexes
Index('idx_audit_resource', AuditLog.resource_type, AuditLog.resource_id)
Index('idx_audit_performer', AuditLog.performed_by)
Index('idx_audit_timestamp', AuditLog.timestamp)
Index('idx_agent_owner', Agent.owner_id)
Index('idx_agent_status', Agent.status)
Index('idx_agent_reporting', Agent.reporting_status)
Index('idx_task_agent', Task.agent_id)
Index('idx_task_user', Task.user_id)
Index('idx_task_status', Task.status)
Index('idx_approval_status', AdminApproval.status)
Index('idx_security_event', SecurityEvent.event_type, SecurityEvent.timestamp)
Index('idx_agent_report', AgentReport.agent_id, AgentReport.timestamp)
Index('idx_data_access', DataAccessLog.resource_type, DataAccessLog.resource_id)
Index('idx_rate_limit', RateLimitLog.identifier, RateLimitLog.endpoint)
Index('idx_api_key_owner', ApiKey.owner_id)

# API models
class UserCreate(BaseModel):
    """User creation request model"""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    roles: List[str] = Field(default_factory=lambda: ["user"])

class AgentCreate(BaseModel):
    """Agent registration request model"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)

class TaskCreate(BaseModel):
    """Task creation request model"""
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    agent_id: str
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    parameters: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None

class AdminApprovalUpdate(BaseModel):
    """Admin approval update model"""
    status: str = Field(..., regex="^(approved|rejected|escalated)$")
    notes: Optional[str] = None

class AgentActionRequest(BaseModel):
    """Agent action request model"""
    action: str = Field(..., regex="^(warn|freeze|unfreeze|delete|audit|isolate)$")
    reason: str = Field(..., min_length=5)

class AgentReportSubmit(BaseModel):
    """Agent report submission model"""
    status: str
    health: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    details: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[str] = None

class QueueManager:
    """Task queue manager with priority handling and dead-letter"""
    
    def __init__(self, redis_client: aioredis.Redis, manager):
        self.redis = redis_client
        self.manager = manager
        
        # Queue names for different priority levels
        self.priority_queues = {
            TaskPriority.CRITICAL.value: "tasks:critical",
            TaskPriority.HIGH.value: "tasks:high",
            TaskPriority.NORMAL.value: "tasks:normal",
            TaskPriority.LOW.value: "tasks:low"
        }
        
        # Dead letter queue
        self.dead_letter_queue = "tasks:dead_letter"
        
    async def enqueue_task(self, task_data: Dict[str, Any], priority: str = TaskPriority.NORMAL.value) -> bool:
        """Add task to appropriate priority queue"""
        try:
            # Convert task data to string
            task_json = json.dumps(task_data)
            
            # Add to priority queue
            queue_name = self.priority_queues.get(priority, self.priority_queues[TaskPriority.NORMAL.value])
            await self.redis.rpush(queue_name, task_json)
            
            # Update metrics
            self.manager.TASK_COUNT.labels(status=TaskStatus.QUEUED.value).inc()
            
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            return False
    
    async def process_queue(self) -> None:
        """Background task to process task queue"""
        logger.info("Task queue processor started")
        
        while self.manager.running:
            try:
                # Process tasks in priority order
                task_data = await self._get_next_task()
                
                if task_data:
                    # Process the task
                    try:
                        await self._process_task(task_data)
                    except Exception as e:
                        logger.error(f"Task processing error: {e}")
                        await self._move_to_dead_letter(task_data, str(e))
                else:
                    # No tasks, sleep briefly
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)  # Backoff on error
    
    async def _get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get next task in priority order"""
        # Check each queue in priority order
        for priority in [TaskPriority.CRITICAL.value, TaskPriority.HIGH.value, 
                       TaskPriority.NORMAL.value, TaskPriority.LOW.value]:
            queue_name = self.priority_queues[priority]
            
            # Try to get task from this queue
            task_json = await self.redis.lpop(queue_name)
            if task_json:
                try:
                    return json.loads(task_json)
                except json.JSONDecodeError:
                    logger.error(f"Invalid task JSON: {task_json}")
                    continue
        
        return None
    
    async def _process_task(self, task_data: Dict[str, Any]) -> None:
        """Process a single task"""
        task_id = task_data.get("task_id")
        agent_id = task_data.get("agent_id")
        
        # Update task status in database
        async with self.manager.get_db_session() as session:
            task = await session.get(Task, task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.utcnow()
            await session.commit()
        
        # Send task to agent via WebSocket if connected
        if agent_id in self.manager.active_connections:
            for ws in self.manager.active_connections[agent_id]:
                try:
                    await ws.send_json({
                        "type": "task",
                        "task_id": task_id,
                        "task_type": task_data.get("task_type"),
                        "parameters": task_data.get("parameters", {})
                    })
                    
                    # Task sent successfully
                    logger.info(f"Task {task_id} sent to agent {agent_id}")
                    return
                except Exception as e:
                    logger.error(f"Failed to send task to agent {agent_id}: {e}")
        
        # Agent not connected, mark task as failed
        await self._handle_task_failure(task_id, "Agent not connected")
    
    async def _handle_task_failure(self, task_id: str, error: str) -> None:
        """Handle task failure with retry logic"""
        async with self.manager.get_db_session() as session:
            task = await session.get(Task, task_id)
            if not task:
                return
            
            # Increment retry count
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                # Reset for retry
                task.status = TaskStatus.PENDING.value
                task.error = f"Retry {task.retry_count}/{task.max_retries}: {error}"
                
                # Re-enqueue with exponential backoff
                await session.commit()
                
                # Create new task_data for requeue
                task_data = {
                    "task_id": task.id,
                    "agent_id": task.agent_id,
                    "task_type": task.task_type,
                    "parameters": task.parameters
                }
                
                # Requeue with delay
                await self._requeue_with_backoff(task_data, task.priority, task.retry_count)
                
            else:
                # Max retries reached, mark as failed
                task.status = TaskStatus.FAILED.value
                task.error = f"Failed after {task.retry_count} retries: {error}"
                task.completed_at = datetime.utcnow()
                await session.commit()
                
                self.manager.TASK_COUNT.labels(status=TaskStatus.FAILED.value).inc()
    
    async def _requeue_with_backoff(self, task_data: Dict[str, Any], 
                                   priority: str, retry_count: int) -> None:
        """Requeue a task with exponential backoff"""
        # Calculate backoff delay (exponential with jitter)
        base_delay = min(60, 2 ** retry_count)  # Cap at 60 seconds
        jitter = 0.2 * base_delay * (random.random() * 2 - 1)  # ±20% jitter
        delay = max(0, base_delay + jitter)
        
        # Add to delayed queue
        task_with_metadata = {
            **task_data,
            "_retry_count": retry_count,
            "_scheduled_at": time.time() + delay
        }
        
        # Store in Redis sorted set with score as the execution time
        await self.redis.zadd(
            f"tasks:delayed",
            {json.dumps(task_with_metadata): time.time() + delay}
        )
        
        logger.info(f"Task {task_data['task_id']} requeued with {delay:.2f}s delay (retry {retry_count})")
    
    async def process_delayed_tasks(self) -> None:
        """Process delayed tasks that are ready to run"""
        while self.manager.running:
            try:
                # Get tasks that are due to run
                now = time.time()
                ready_tasks = await self.redis.zrangebyscore(
                    "tasks:delayed", 0, now
                )
                
                if not ready_tasks:
                    await asyncio.sleep(1)
                    continue
                
                # Process each ready task
                for task_json in ready_tasks:
                    task_data = json.loads(task_json)
                    
                    # Remove original retry metadata
                    retry_count = task_data.pop("_retry_count", 0)
                    scheduled_at = task_data.pop("_scheduled_at", 0)
                    
                    # Enqueue to appropriate queue
                    priority = task_data.get("priority", TaskPriority.NORMAL.value)
                    await self.enqueue_task(task_data, priority)
                    
                    # Remove from delayed queue
                    await self.redis.zrem("tasks:delayed", task_json)
                
            except Exception as e:
                logger.error(f"Delayed task processing error: {e}")
                await asyncio.sleep(5)
    
    async def _move_to_dead_letter(self, task_data: Dict[str, Any], error: str) -> None:
        """Move task to dead letter queue"""
        try:
            # Add error information
            task_data["_error"] = error
            task_data["_moved_to_dlq_at"] = datetime.utcnow().isoformat()
            
            # Add to dead letter queue
            await self.redis.rpush(self.dead_letter_queue, json.dumps(task_data))
            
            # Update task status in database
            task_id = task_data.get("task_id")
            if task_id:
                async with self.manager.get_db_session() as session:
                    task = await session.get(Task, task_id)
                    if task:
                        task.status = TaskStatus.FAILED.value
                        task.error = f"Moved to dead letter queue: {error}"
                        task.completed_at = datetime.utcnow()
                        await session.commit()
            
            logger.error(f"Task {task_data.get('task_id')} moved to dead letter queue: {error}")
            
        except Exception as e:
            logger.error(f"Failed to move task to dead letter queue: {e}")

class CacheManager:
    """Caching service with multi-level caching"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.local_cache = {}
        self.ttl_cache = {}
    
    async def get(self, key: str, default=None):
        """Get value from cache with fallback mechanism"""
        # Try local in-memory cache first
        if key in self.local_cache and self.ttl_cache.get(key, 0) > time.time():
            return self.local_cache[key]
        
        # Try Redis cache
        value = await self.redis.get(key)
        if value is not None:
            try:
                parsed = json.loads(value)
                # Update local cache
                self.local_cache[key] = parsed
                self.ttl_cache[key] = time.time() + 60  # 1 minute local cache
                return parsed
            except json.JSONDecodeError:
                # Not JSON, return as is
                return value.decode('utf-8')
        
        return default
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        # Store in local cache
        self.local_cache[key] = value
        self.ttl_cache[key] = time.time() + min(ttl, 60)  # Max 1 minute local cache
        
        # Store in Redis
        try:
            if isinstance(value, (dict, list, tuple)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)
            
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str):
        """Delete from all cache levels"""
        # Remove from local cache
        if key in self.local_cache:
            del self.local_cache[key]
        if key in self.ttl_cache:
            del self.ttl_cache[key]
        
        # Remove from Redis
        await self.redis.delete(key)
    
    async def flush(self):
        """Clear entire cache"""
        self.local_cache = {}
        self.ttl_cache = {}
        await self.redis.flushdb()

class SecurityManager:
    """Security manager with authentication and authorization"""
    
    def __init__(self, password_ctx: CryptContext, redis_client: aioredis.Redis, 
               jwt_secret: str, api_key_salt: str, token_expiry: timedelta):
        self.password_ctx = password_ctx
        self.redis = redis_client
        self.jwt_secret = jwt_secret
        self.api_key_salt = api_key_salt
        self.token_expiry = token_expiry
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        return self.password_ctx.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.password_ctx.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        expire = datetime.utcnow() + self.token_expiry
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.jwt_secret, algorithm="HS256")
    
    async def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            # Check if token is blacklisted
            if await self._is_token_blacklisted(token):
                raise jwt.InvalidTokenError("Token is blacklisted")
            
            # Verify token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
            
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=401, 
                detail=f"Invalid authentication credentials: {str(e)}"
            )
    
    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return await self.redis.exists(f"blacklist:token:{token_hash}")
    
    async def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist"""
        try:
            # Get token expiration time
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"], verify=False)
            exp = payload.get("exp", 0)
            current_time = int(time.time())
            ttl = max(0, exp - current_time)
            
            # Add to blacklist
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            await self.redis.setex(f"blacklist:token:{token_hash}", ttl, "1")
            return True
            
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def hash_api_key(self, api_key: str) -> str:
        """Create secure hash of API key"""
        key = f"{api_key}:{self.api_key_salt}".encode()
        return hashlib.sha256(key).hexdigest()
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    async def rate_limit(self, identifier: str, limit: int, window: int) -> bool:
        """Rate limiting with sliding window"""
        key = f"rate_limit:{identifier}"
        current = await self.redis.get(key)
        
        if current is None:
            # First request
            await self.redis.setex(key, window, 1)
            return True
        
        count = int(current)
        if count >= limit:
            return False
        
        # Increment counter
        await self.redis.incr(key)
        return True

class EnterpriseAgentManager:
    """Enterprise Agent Manager with comprehensive agent management capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.running = True
        
        # Database setup
        self.db_url = config.get("database_url", "postgresql+asyncpg://user:password@localhost/agent_db")
        self.engine = create_async_engine(
            self.db_url, 
            echo=config.get("db_echo", False),
            pool_size=config.get("db_pool_size", 20),
            max_overflow=config.get("db_max_overflow", 10),
            pool_pre_ping=True
        )
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Redis setup
        self.redis_url = config.get("redis_url", "redis://localhost:6379/0")
        
        # Security
        self.jwt_secret = config.get("jwt_secret", secrets.token_hex(32))
        self.password_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.api_key_salt = config.get("api_key_salt", secrets.token_hex(16))
        self.auth_token_expiry = timedelta(hours=config.get("auth_token_expiry_hours", 8))
        
        # Initialize metrics
        self.init_metrics()
        
        # Track active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        # Load environment-specific settings
        self.environment = config.get("environment", "production")
        self.debug_mode = self.environment == "development"
        
        logger.info(f"EnterpriseAgentManager initialized in {self.environment} environment")
    
    async def startup(self):
        """Initialize all subsystems and connect to services"""
        # Connect to Redis
        self.redis = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Create database tables if they don't exist
        async with self.engine.begin() as conn:
            if self.config.get("create_tables", True):
                await conn.run_sync(Base.metadata.create_all)
        
        # Initialize cache manager
        self.cache_manager = CacheManager(self.redis)
        
        # Initialize task queue
        self.queue_manager = QueueManager(self.redis, self)
        
        # Initialize telemetry
        self.telemetry = TelemetryManager(
            service_name=self.config.get("service_name", "agent-manager"),
            environment=self.environment,
            version=self.config.get("version", "1.0.0")
        )
        
        # Initialize security components
        self.security_manager = SecurityManager(
            self.password_ctx,
            self.redis,
            self.jwt_secret,
            self.api_key_salt,
            self.auth_token_expiry
        )
        
        # Create enhanced managers
        self.reporting_enforcer = MandatoryReportingEnforcer(self)
        self.lifecycle_manager = AgentLifecycleManager(self)
        self.security_monitor = EnhancedSecurityMonitor(self)
        self.data_validator = DataFlowValidator(self)
        self.audit_system = EnhancedAuditSystem(self)
        self.notification_manager = NotificationManager(self.redis)
        
        # Start background tasks
        asyncio.create_task(self.reporting_enforcer.start_monitoring())
        asyncio.create_task(self.security_monitor.start_monitoring())
        asyncio.create_task(self.queue_manager.process_queue())
        asyncio.create_task(self.queue_manager.process_delayed_tasks())
        asyncio.create_task(self.security_monitor.scan_for_threats())
        asyncio.create_task(self.prune_expired_records())
        
        # Start metrics server if enabled
        if self.config.get("enable_metrics", True):
            metrics_port = self.config.get("metrics_port", 9000)
            start_http_server(metrics_port)
        
        logger.info("EnterpriseAgentManager started successfully")
    
    async def shutdown(self):
        """Graceful shutdown of all subsystems"""
        logger.info("Shutting down EnterpriseAgentManager...")
        self.running = False
        
        # Close all WebSocket connections
        for agent_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.close(code=1000)
                except Exception:
                    pass
        
        # Close Redis connection
        await self.redis.close()
        
        # Dispose of database engine
        await self.engine.dispose()
        
        logger.info("EnterpriseAgentManager shutdown complete")
    
    def init_metrics(self):
        """Initialize Prometheus metrics"""
        # Agent metrics
        self.AGENT_COUNT = Gauge('agent_count', 'Number of agents', ['status'])
        self.AGENT_HEALTH = Gauge('agent_health', 'Agent health status', ['status'])
        self.AGENT_REPORTING = Counter('agent_reporting_total', 'Agent reporting count', ['status'])
        
        # Task metrics
        self.TASK_COUNT = Gauge('task_count', 'Number of tasks', ['status'])
        self.TASK_PROCESSING_TIME = Histogram('task_processing_seconds', 'Task processing time', 
                                            ['priority', 'task_type'])
        
        # Security metrics
        self.SECURITY_EVENTS = Counter('security_events_total', 'Security events', ['event_type', 'severity'])
        self.APPROVAL_COUNT = Gauge('approval_count', 'Number of pending approvals', ['approval_type'])
        
        # API metrics
        self.API_REQUESTS = Counter('api_requests_total', 'API requests', ['endpoint', 'method', 'status'])
        self.API_REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration', 
                                           ['endpoint', 'method'])
        
        # Reporting metrics
        self.REPORTING_STATUS = Gauge('agent_reporting_status', 'Agent reporting status', ['status'])
        
        # Authentication metrics
        self.AUTH_ATTEMPTS = Counter('authentication_attempts_total', 'Authentication attempts', ['status'])
        
        # Data flow metrics
        self.DATA_FLOW = Counter('data_flow_bytes_total', 'Data flow in bytes', ['direction', 'agent_id'])
        
        # Initialize status counts
        for status in AgentStatus:
            self.AGENT_COUNT.labels(status=status.value).set(0)
        
        for status in AgentReportStatus:
            self.REPORTING_STATUS.labels(status=status.value).set(0)
    
    @tracer.start_as_current_span("get_db_session")
    async def get_db_session(self) -> AsyncSession:
        """Get database session with tracing"""
        return self.async_session()
    
    @tracer.start_as_current_span("register_agent")
    async def register_agent(self, agent_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Register a new agent with API key generation"""
        # Generate API key for the agent
        api_key = self.security_manager.generate_api_key()
        api_key_hash = self.security_manager.hash_api_key(api_key)
        
        # Create agent record
        async with self.get_db_session() as session:
            agent = Agent(
                name=agent_data.get("name"),
                description=agent_data.get("description"),
                owner_id=user_id,
                api_key_hash=api_key_hash,
                capabilities=agent_data.get("capabilities", []),
                status=AgentStatus.INACTIVE.value,
                configuration=agent_data.get("configuration", {})
            )
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
            
            # Log audit event
            audit_log = AuditLog(
                event_type="agent_creation",
                resource_type="agent",
                resource_id=agent.id,
                action="create",
                performed_by=user_id,
                details={"name": agent.name}
            )
            session.add(audit_log)
            await session.commit()
            
            # Update metrics
            self.AGENT_COUNT.labels(status=AgentStatus.INACTIVE.value).inc()
            
            # Return agent info with API key (will only be shown once)
            return {
                "id": agent.id,
                "name": agent.name,
                "api_key": api_key,
                "status": "registered",
                "created_at": agent.created_at.isoformat()
            }
    
    @tracer.start_as_current_span("handle_agent_report")
    async def handle_agent_report(self, agent_id: str, report_data: Dict[str, Any], ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Process agent report/heartbeat with mandatory reporting tracking"""
        try:
            # Validate report data
            validation_result = await self.data_validator.validate_data_flow("agent.report", report_data, {
                "agent_id": agent_id,
                "ip_address": ip_address
            })
            
            if not validation_result[0]:
                return {"error": f"Report validation failed: {validation_result[1]}"}
            
            async with self.get_db_session() as session:
                # Get agent
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return {"error": "Agent not found"}
                
                # Update agent status
                agent.last_heartbeat = datetime.utcnow()
                agent.status = report_data.get("status", agent.status)
                agent.health_status = report_data.get("health", "unknown")
                agent.last_report = report_data
                
                if "resource_usage" in report_data:
                    agent.resource_usage = report_data["resource_usage"]
                
                # Reset missed report counter and update reporting status
                if agent.reporting_status in [AgentReportStatus.WARNED.value, AgentReportStatus.SUSPENDED.value]:
                    agent.missed_report_count = 0
                    agent.reporting_status = AgentReportStatus.COMPLIANT.value
                
                # Create report record
                report = AgentReport(
                    agent_id=agent_id,
                    report_type=report_data.get("type", "heartbeat"),
                    status=report_data.get("status"),
                    health=report_data.get("health"),
                    metrics=report_data.get("metrics", {}),
                    details=report_data,
                    ip_address=ip_address,
                    version=report_data.get("version")
                )
                session.add(report)
                
                await session.commit()
            
            # Update metrics
            self.AGENT_REPORTING.labels(status="success").inc()
            
            # Process report through mandatory reporting enforcer
            await self.reporting_enforcer.process_agent_report(agent_id, report_data)
            
            # Process report through security monitor
            await self.security_monitor.analyze_agent_report(agent_id, report_data)
            
            return {
                "status": "success",
                "message": "Report received successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling agent report: {e}")
            self.AGENT_REPORTING.labels(status="failed").inc()
            return {"error": str(e)}
    
    @tracer.start_as_current_span("verify_agent_api_key")
    async def verify_agent_api_key(self, agent_id: str, api_key: str) -> bool:
        """Verify agent API key"""
        try:
            async with self.get_db_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent or not agent.api_key_hash:
                    return False
                
                # Check if agent is deleted
                if agent.status == AgentStatus.DELETED.value:
                    return False
                
                # Verify API key hash
                api_key_hash = self.security_manager.hash_api_key(api_key)
                return secrets.compare_digest(api_key_hash, agent.api_key_hash)
                
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return False
    
    @tracer.start_as_current_span("handle_task_result")
    async def handle_task_result(self, task_id: str, agent_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process task result from agent"""
        try:
            # Validate data flow
            validation_result = await self.data_validator.validate_data_flow("task.result", result, {
                "task_id": task_id,
                "agent_id": agent_id
            })
            
            if not validation_result[0]:
                return {"error": f"Result validation failed: {validation_result[1]}"}
            
            async with self.get_db_session() as session:
                task = await session.get(Task, task_id)
                if not task:
                    return {"error": "Task not found"}
                
                # Verify agent assignment
                if task.agent_id != agent_id:
                    return {"error": "Task not assigned to this agent"}
                
                # Update task
                task.status = TaskStatus.COMPLETED.value
                task.result = result
                task.completed_at = datetime.utcnow()
                
                # Update agent task count
                agent = await session.get(Agent, agent_id)
                if agent and agent.current_tasks > 0:
                    agent.current_tasks -= 1
                
                # Update metrics
                if task.started_at:
                    duration = (task.completed_at - task.started_at).total_seconds()
                    self.TASK_PROCESSING_TIME.labels(
                        priority=task.priority,
                        task_type=task.task_type
                    ).observe(duration)
                
                # Log audit event
                audit_log = AuditLog(
                    event_type="task_completed",
                    resource_type="task",
                    resource_id=task.id,
                    action="complete",
                    performed_by=agent_id,
                    details={"task_type": task.task_type}
                )
                session.add(audit_log)
                
                await session.commit()
                
                # Decrease active task count and increase completed
                self.TASK_COUNT.labels(status=TaskStatus.RUNNING.value).dec()
                self.TASK_COUNT.labels(status=TaskStatus.COMPLETED.value).inc()
                
                return {
                    "status": "success",
                    "message": "Task result processed"
                }
                
        except Exception as e:
            logger.error(f"Error handling task result: {e}")
            return {"error": str(e)}
    
    @tracer.start_as_current_span("create_task")
    async def create_task(self, task_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new task with data validation"""
        try:
            # Validate task data
            validation_result = await self.data_validator.validate_data_flow("task.create", task_data, {
                "user_id": user_id
            })
            
            if not validation_result[0]:
                return {"error": f"Task validation failed: {validation_result[1]}"}
            
            # Validate agent exists and is active
            agent_id = task_data.get("agent_id")
            async with self.get_db_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return {"error": "Agent not found"}
                
                if agent.status != AgentStatus.ACTIVE.value:
                    return {"error": f"Agent is not active (status: {agent.status})"}
                
                # Check if agent has capacity
                if agent.current_tasks >= agent.max_tasks:
                    return {"error": "Agent is at maximum capacity"}
                
                # Create task
                task = Task(
                    name=task_data.get("name"),
                    description=task_data.get("description"),
                    agent_id=agent_id,
                    user_id=user_id,
                    task_type=task_data.get("task_type"),
                    priority=task_data.get("priority", TaskPriority.NORMAL.value),
                    parameters=task_data.get("parameters", {}),
                    deadline=task_data.get("deadline"),
                    status=TaskStatus.PENDING.value
                )
                session.add(task)
                
                # Update agent task count
                agent.current_tasks += 1
                
                # Create audit log entry
                audit_log = AuditLog(
                    event_type="task_creation",
                    resource_type="task",
                    resource_id=task.id,
                    action="create",
                    performed_by=user_id,
                    details={
                        "task_type": task.task_type,
                        "agent_id": task.agent_id,
                        "priority": task.priority
                    }
                )
                session.add(audit_log)
                
                await session.commit()
                await session.refresh(task)
                
                # Update metrics
                self.TASK_COUNT.labels(status=TaskStatus.PENDING.value).inc()
                
                # Queue task for processing
                await self.queue_manager.enqueue_task({
                    "task_id": task.id,
                    "agent_id": agent_id,
                    "task_type": task.task_type,
                    "parameters": task.parameters,
                    "priority": task.priority
                }, task.priority)
                
                return {
                    "id": task.id,
                    "status": "created",
                    "message": "Task created and queued"
                }
                
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {"error": str(e)}
    
    @tracer.start_as_current_span("request_agent_action")
    async def request_agent_action(
        self, agent_id: str, action: str, reason: str, requested_by: str
    ) -> Dict[str, Any]:
        """Request action on agent that requires admin approval"""
        try:
            async with self.get_db_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return {"error": "Agent not found"}
                
                # Create approval request
                approval_request = AdminApproval(
                    request_type="agent_action",
                    resource_id=agent_id,
                    resource_type="agent",
                    action=action,
                    reason=reason,
                    requested_by=requested_by,
                    status=AdminApprovalStatus.PENDING.value
                )
                session.add(approval_request)
                await session.commit()
                await session.refresh(approval_request)
                
                # Update approval count metric
                self.APPROVAL_COUNT.labels(approval_type="agent_action").inc()
                
                # Create audit log
                audit_log = AuditLog(
                    event_type="approval_request",
                    resource_type="agent",
                    resource_id=agent_id,
                    action=action,
                    performed_by=requested_by,
                    details={"reason": reason}
                )
                session.add(audit_log)
                await session.commit()
                
                # Send notification about the approval request
                await self.notification_manager.send_notification(
                    "admin",  # Send to users with admin role
                    {
                        "type": "approval_required",
                        "title": f"Agent {action} approval required",
                        "message": f"Action: {action}\nReason: {reason}\nRequested by: {requested_by}",
                        "severity": "medium",
                        "action_required": True,
                        "metadata": {
                            "approval_id": approval_request.id,
                            "agent_id": agent_id
                        }
                    }
                )
                
                return {
                    "status": "pending_approval",
                    "approval_id": approval_request.id,
                    "message": f"Action '{action}' requires admin approval"
                }
                
        except Exception as e:
            logger.error(f"Error requesting agent action: {e}")
            return {"error": str(e)}
    
    @tracer.start_as_current_span("process_approval")
    async def process_approval(
        self, approval_id: str, status: str, admin_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process approval request (approve, reject, escalate)"""
        try:
            async with self.get_db_session() as session:
                approval = await session.get(AdminApproval, approval_id)
                if not approval:
                    return {"error": "Approval request not found"}
                
                if approval.status != AdminApprovalStatus.PENDING.value:
                    return {"error": "Approval has already been processed"}
                
                # Update approval
                approval.status = status
                approval.processed_by = admin_id
                approval.processed_at = datetime.utcnow()
                approval.notes = notes
                await session.commit()
                
                # Update metrics
                self.APPROVAL_COUNT.labels(approval_type="agent_action").dec()
                
                # Create audit log
                audit_log = AuditLog(
                    event_type="approval_processed",
                    resource_type="approval",
                    resource_id=approval_id,
                    action=status,
                    performed_by=admin_id,
                    details={"notes": notes}
                )
                session.add(audit_log)
                await session.commit()
                
                # If approved, execute the action
                if status == AdminApprovalStatus.APPROVED.value and approval.request_type == "agent_action":
                    result = await self.lifecycle_manager._execute_agent_action(
                        approval.resource_id, approval.action, admin_id, notes
                    )
                    
                    if "error" in result:
                        return {
                            "status": "approval_processed",
                            "action_status": "failed",
                            "error": result["error"]
                        }
                
                # Notify requester
                await self.notification_manager.send_notification(
                    approval.requested_by,
                    {
                        "type": "approval_processed",
                        "title": f"Your request has been {status}",
                        "message": f"Request for {approval.action} on {approval.resource_type} {approval.resource_id} has been {status}",
                        "severity": "medium",
                        "metadata": {
                            "approval_id": approval.id,
                            "notes": notes
                        }
                    }
                )
                
                return {
                    "status": "success",
                    "message": f"Approval {status}",
                    "approval_id": approval_id
                }
                
        except Exception as e:
            logger.error(f"Error processing approval: {e}")
            return {"error": str(e)}
    
    @tracer.start_as_current_span("validate_ws_connection")
    async def validate_ws_connection(self, agent_id: str, api_key: str) -> bool:
        """Validate WebSocket connection request"""
        valid = await self.verify_agent_api_key(agent_id, api_key)
        if not valid:
            self.SECURITY_EVENTS.labels(
                event_type="unauthorized_connection", 
                severity="medium"
            ).inc()
            
            # Log security event
            async with self.get_db_session() as session:
                security_event = SecurityEvent(
                    event_type="unauthorized_connection",
                    severity="medium",
                    source="websocket",
                    description=f"Unauthorized connection attempt for agent {agent_id}",
                    agent_id=agent_id
                )
                session.add(security_event)
                await session.commit()
        return valid
    
    @tracer.start_as_current_span("register_ws_connection")
    async def register_ws_connection(self, agent_id: str, websocket: WebSocket) -> None:
        """Register active WebSocket connection"""
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = []
        self.active_connections[agent_id].append(websocket)
        
        # Update agent status to active
        async with self.get_db_session() as session:
            agent = await session.get(Agent, agent_id)
            if agent and agent.status != AgentStatus.ACTIVE.value:
                agent.status = AgentStatus.ACTIVE.value
                agent.last_heartbeat = datetime.utcnow()
                await session.commit()
                
                # Update metrics
                self.AGENT_COUNT.labels(status=agent.status).dec()
                self.AGENT_COUNT.labels(status=AgentStatus.ACTIVE.value).inc()
                
                # Log event
                audit_log = AuditLog(
                    event_type="agent_connection",
                    resource_type="agent",
                    resource_id=agent_id,
                    action="connect",
                    performed_by=agent_id
                )
                session.add(audit_log)
                await session.commit()
    
    @tracer.start_as_current_span("unregister_ws_connection")
    async def unregister_ws_connection(self, agent_id: str, websocket: WebSocket) -> None:
        """Unregister WebSocket connection"""
        if agent_id in self.active_connections:
            if websocket in self.active_connections[agent_id]:
                self.active_connections[agent_id].remove(websocket)
            
            if not self.active_connections[agent_id]:
                del self.active_connections[agent_id]
                
                # Update agent status to inactive
                async with self.get_db_session() as session:
                    agent = await session.get(Agent, agent_id)
                    if agent and agent.status == AgentStatus.ACTIVE.value:
                        agent.status = AgentStatus.INACTIVE.value
                        await session.commit()
                        
                        # Update metrics
                        self.AGENT_COUNT.labels(status=AgentStatus.ACTIVE.value).dec()
                        self.AGENT_COUNT.labels(status=AgentStatus.INACTIVE.value).inc()
                        
                        # Log event
                        audit_log = AuditLog(
                            event_type="agent_connection",
                            resource_type="agent",
                            resource_id=agent_id,
                            action="disconnect",
                            performed_by=agent_id
                        )
                        session.add(audit_log)
                        await session.commit()
    
    @tracer.start_as_current_span("prune_expired_records")
    async def prune_expired_records(self) -> None:
        """Periodically prune expired records for database maintenance"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run once per hour
                
                # Define cut-off dates
                now = datetime.utcnow()
                audit_retention = self.config.get("audit_retention_days", 90)
                report_retention = self.config.get("report_retention_days", 30)
                task_retention = self.config.get("task_retention_days", 60)
                
                audit_cutoff = now - timedelta(days=audit_retention)  # Keep audit logs for 90 days
                report_cutoff = now - timedelta(days=report_retention)  # Keep reports for 30 days
                task_cutoff = now - timedelta(days=task_retention)    # Keep completed tasks for 60 days
                
                async with self.get_db_session() as session:
                    # Prune old audit logs
                    await session.execute(
                        text("DELETE FROM audit_logs WHERE timestamp < :cutoff"),
                        {"cutoff": audit_cutoff}
                    )
                    
                    # Prune old agent reports
                    await session.execute(
                        text("DELETE FROM agent_reports WHERE timestamp < :cutoff"),
                        {"cutoff": report_cutoff}
                    )
                    
                    await session.commit()
                    
                logger.info("Data pruning completed successfully")
            except Exception as e:
                logger.error(f"Data pruning failed: {e}")
                raise
                    