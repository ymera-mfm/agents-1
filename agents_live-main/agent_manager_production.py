"""
YMERA Enterprise Agent Manager - Production Implementation
Secure, scalable multi-agent orchestration with mandatory reporting, lifecycle management,
comprehensive monitoring, and enterprise-grade security.
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

# Database and storage
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Text, ForeignKey, select, func, text
import asyncpg

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

# Import custom modules
from performance.queue_manager import (
    AdvancedTaskQueue, QueuePriority, MessageStatus, 
    QueueMessage, QueueMetrics, DeadLetterHandler
)
from performance.caching_manager import (
    CacheManager, QueryOptimizer, DataPartitioner
)
from monitoring.telemetry_manager import (
    TelemetryManager, TelemetryMiddleware, monitor_operation,
    trace_operation, trace_async_operation
)
from monitoring.predictive_analytics import (
    PredictiveAnalyticsEngine, RealTimeAnalyticsProcessor,
    AnomalyType, PredictionResult, CapacityRecommendation
)
from monitoring.alert_manager import (
    AlertManager, SLAMonitor, Alert, Incident,
    AlertSeverity, AlertStatus
)
from security.advanced_authentication import (
    AdvancedAuthenticationManager, WebAuthnManager,
    HSMManager, DynamicPolicyEngine, OAuthManager
)
from security.compliance_manager import (
    ComplianceManager, DataProtectionManager, AuditManager
)
from security.zero_trust_complete import (
    ZeroTrustOrchestrator, MTLSManager, MicrosegmentationManager, 
    IdentityAccessManager, ContinuousAssessmentManager, RealTimeThreatDetector
)
from performance.scaling_manager import (
    AutoScalingManager, ScalingStrategy, ResourceType,
    ScalingDecision, ScalingMetrics, MultiCloudOptimizer
)

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

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    roles = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    api_key_hash = Column(String(255), nullable=True)
    capabilities = Column(JSON, default=list)
    status = Column(String(50), default="inactive")
    health_status = Column(String(20), default="unknown")
    last_heartbeat = Column(DateTime, nullable=True)
    last_report = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    frozen_at = Column(DateTime, nullable=True)
    frozen_by = Column(String(36), nullable=True)
    frozen_reason = Column(Text, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(36), nullable=True)
    suspended_at = Column(DateTime, nullable=True)
    suspended_by = Column(String(36), nullable=True)
    suspended_reason = Column(Text, nullable=True)
    reporting_exemption = Column(Boolean, default=False)
    reporting_exemption_reason = Column(Text, nullable=True)
    resource_usage = Column(JSON, default=dict)
    configuration = Column(JSON, default=dict)
    
    # Additional fields for mandatory reporting tracking
    missed_report_count = Column(Integer, default=0)
    last_warning_at = Column(DateTime, nullable=True)
    reporting_status = Column(String(20), default="compliant")  # compliant, warned, suspended, non_compliant, exempt

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    task_type = Column(String(50), nullable=False)
    priority = Column(String(20), default="normal")
    status = Column(String(20), default="pending")
    parameters = Column(JSON, default=dict)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

class AdminApproval(Base):
    __tablename__ = "admin_approvals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_type = Column(String(50), nullable=False)  # agent_action, security_change, etc.
    resource_id = Column(String(36), nullable=False)   # agent_id, etc.
    resource_type = Column(String(50), nullable=False) # agent, task, etc.
    action = Column(String(50), nullable=False)        # freeze, delete, etc.
    reason = Column(Text, nullable=False)
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")     # pending, approved, rejected, escalated
    processed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

class AuditLog(Base):
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

class SecurityEvent(Base):
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

class AgentReport(Base):
    __tablename__ = "agent_reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    report_type = Column(String(50), default="heartbeat")
    status = Column(String(50), nullable=False)
    health = Column(String(20), nullable=False)
    metrics = Column(JSON, default=dict)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Pydantic models for API
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    roles: List[str] = Field(default_factory=lambda: ["user"])

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)

class TaskCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    agent_id: str = Field(...)
    task_type: str = Field(...)
    priority: str = Field(default="normal")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None

class AdminApprovalUpdate(BaseModel):
    status: str = Field(..., regex="^(approved|rejected|escalated)$")
    notes: Optional[str] = None

class AgentActionRequest(BaseModel):
    action: str = Field(..., regex="^(warn|freeze|unfreeze|delete|audit|isolate)$")
    reason: str = Field(..., min_length=5)

class AgentReportSubmit(BaseModel):
    status: str = Field(...)
    health: str = Field(...)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    details: Dict[str, Any] = Field(default_factory=dict)

# Enums
class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy" 
    FROZEN = "frozen"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    ERROR = "error"
    ISOLATED = "isolated"

class AgentReportStatus(str, Enum):
    COMPLIANT = "compliant"
    WARNED = "warned"
    SUSPENDED = "suspended"
    NON_COMPLIANT = "non_compliant"
    EXEMPT = "exempt"

class AgentAction(str, Enum):
    WARN = "warn"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"
    DELETE = "delete"
    AUDIT = "audit"
    ISOLATE = "isolate"

class AdminApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"

# Main Manager class that ties everything together
class EnterpriseAgentManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = True
        
        # Database setup
        self.db_url = config.get("database_url", "postgresql+asyncpg://user:password@localhost/agent_db")
        self.engine = create_async_engine(self.db_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Redis setup
        self.redis_url = config.get("redis_url", "redis://localhost:6379/0")
        
        # Security
        self.jwt_secret = config.get("jwt_secret", secrets.token_hex(32))
        self.password_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.api_key_salt = config.get("api_key_salt", secrets.token_hex(16))
        
        # Initialize sub-components
        self.init_metrics()
        
        # Track active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        logger.info("EnterpriseAgentManager initialized")
    
    async def startup(self):
        """Initialize all subsystems and connect to services"""
        # Connect to Redis
        self.redis = await aioredis.from_url(self.redis_url)
        
        # Create database tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Initialize components
        self.task_queue = await self.init_task_queue()
        self.cache_manager = await self.init_cache_manager()
        self.telemetry = await self.init_telemetry()
        self.alerts = await self.init_alerts()
        self.security = await self.init_security()
        self.compliance = await self.init_compliance()
        self.analytics = await self.init_analytics()
        
        # Create mandatory reporting enforcer
        self.reporting_enforcer = MandatoryReportingEnforcer(self, self.alerts)
        self.lifecycle_manager = AgentLifecycleManager(self, self.security, self.alerts)
        self.security_monitor = EnhancedSecurityMonitor(self, self.alerts)
        self.data_flow_validator = DataFlowValidator(self, self.security)
        self.audit_system = EnhancedAuditSystem(self, self.telemetry)
        
        # Start background tasks
        asyncio.create_task(self.reporting_enforcer.start_monitoring())
        asyncio.create_task(self.security_monitor.start_monitoring())
        asyncio.create_task(self.process_task_queue())
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
    
    async def init_task_queue(self) -> AdvancedTaskQueue:
        """Initialize task queue with dead letter handling"""
        dlq_handler = DeadLetterHandler(self.redis, self.alerts)
        return AdvancedTaskQueue(self.redis, dlq_handler, "agent_tasks")
    
    async def init_cache_manager(self) -> CacheManager:
        """Initialize caching system"""
        return CacheManager(self.redis)
    
    async def init_telemetry(self) -> TelemetryManager:
        """Initialize telemetry and monitoring"""
        return TelemetryManager(
            service_name="agent_manager",
            environment=self.config.get("environment", "production"),
            version=self.config.get("version", "1.0.0")
        )
    
    async def init_alerts(self) -> AlertManager:
        """Initialize alerting system"""
        config = {
            'slack_token': self.config.get("slack_token"),
            'pagerduty_routing_key': self.config.get("pagerduty_routing_key"),
            'dashboard_url': self.config.get("dashboard_url", "http://localhost:8000"),
            'slack_channel': self.config.get("slack_channel", "#alerts")
        }
        return AlertManager(self.redis, config)
    
    async def init_security(self) -> Dict[str, Any]:
        """Initialize security components"""
        components = {}
        
        # Initialize advanced authentication
        components['auth_manager'] = AdvancedAuthenticationManager(
            HSMManager(
                self.config.get("hsm_endpoint", "localhost"),
                self.config.get("hsm_token", "dummy")
            ),
            WebAuthnManager(
                self.config.get("rp_id", "localhost"),
                self.config.get("rp_name", "YMERA"),
                self.config.get("origin", "https://localhost")
            ),
            DynamicPolicyEngine(self.redis),
            self.redis
        )
        
        # Initialize zero-trust components
        ca_path = self.config.get("ca_cert_path", "./ca.pem")
        cert_path = self.config.get("cert_path", "./cert.pem")
        key_path = self.config.get("key_path", "./key.pem")
        
        components['mtls_manager'] = MTLSManager(ca_path, cert_path, key_path)
        components['microsegmentation'] = MicrosegmentationManager(self.redis)
        components['identity_manager'] = IdentityAccessManager(self.redis, 
                                              self.config.get("policy_endpoint", "http://localhost:8000/policy"))
        
        components['security_assessment'] = ContinuousAssessmentManager(self.redis)
        components['threat_detector'] = RealTimeThreatDetector(self.redis)
        
        return components
    
    async def init_compliance(self) -> Dict[str, Any]:
        """Initialize compliance components"""
        components = {}
        
        components['compliance_manager'] = ComplianceManager(self.redis)
        components['data_protection'] = DataProtectionManager(self.redis)
        components['audit_manager'] = AuditManager(self.redis)
        
        return components
    
    async def init_analytics(self) -> Dict[str, Any]:
        """Initialize analytics components"""
        components = {}
        
        components['predictive_engine'] = PredictiveAnalyticsEngine(self.redis)
        components['realtime_processor'] = RealTimeAnalyticsProcessor(components['predictive_engine'])
        
        return components
    
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
    
    @tracer.start_as_current_span("get_db_session")
    async def get_db_session(self) -> AsyncSession:
        """Get database session with tracing"""
        return self.async_session()
    
    @tracer.start_as_current_span("process_task_queue")
    async def process_task_queue(self):
        """Process tasks from the queue"""
        logger.info("Task queue processor started")
        
        while self.running:
            try:
                # Process a batch of tasks
                await self.task_queue.process_messages(
                    self.process_task,
                    concurrency=self.config.get("task_concurrency", 10),
                    batch_size=self.config.get("task_batch_size", 10),
                    poll_timeout=1
                )
                
                # Short sleep to prevent CPU hogging
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Task queue processing failed: {e}")
                await asyncio.sleep(5)  # Backoff on error
    
    @tracer.start_as_current_span("process_task")
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task with proper error handling and metrics"""
        task_id = task_data.get("task_id")
        agent_id = task_data.get("agent_id")
        task_type = task_data.get("task_type")
        
        if not all([task_id, agent_id, task_type]):
            return {"error": "Invalid task data"}
        
        try:
            # Update task status in database
            async with self.get_db_session() as session:
                task = await session.get(Task, task_id)
                if not task:
                    return {"error": "Task not found"}
                
                task.status = "running"
                task.started_at = datetime.utcnow()
                await session.commit()
            
            # Send task to agent via WebSocket if connected
            ws_connections = self.active_connections.get(agent_id, [])
            if not ws_connections:
                raise Exception(f"Agent {agent_id} not connected")
            
            # Send to first active connection
            await ws_connections[0].send_json({
                "type": "task",
                "task_id": task_id,
                "task_type": task_type,
                "parameters": task_data.get("parameters", {})
            })
            
            # Return success (actual result will come via WebSocket)
            return {
                "status": "sent_to_agent",
                "task_id": task_id,
                "agent_id": agent_id
            }
            
        except Exception as e:
            logger.error(f"Task processing error for task {task_id}: {e}")
            
            # Update task status to failed
            async with self.get_db_session() as session:
                task = await session.get(Task, task_id)
                if task:
                    task.status = "failed"
                    task.error = str(e)
                    await session.commit()
            
            return {"error": str(e), "task_id": task_id}
    
    @tracer.start_as_current_span("register_agent")
    async def register_agent(self, agent_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Register a new agent with API key generation"""
        # Generate API key for the agent
        api_key = secrets.token_hex(32)
        api_key_hash = self._hash_api_key(api_key)
        
        # Create agent record
        async with self.get_db_session() as session:
            agent = Agent(
                name=agent_data.get("name"),
                description=agent_data.get("description"),
                owner_id=user_id,
                api_key_hash=api_key_hash,
                capabilities=agent_data.get("capabilities", []),
                status="inactive",
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
            self.AGENT_COUNT.labels(status="inactive").inc()
            
            # Return agent info with API key (will only be shown once)
            return {
                "id": agent.id,
                "name": agent.name,
                "api_key": api_key,
                "status": "registered",
                "created_at": agent.created_at
            }
    
    @tracer.start_as_current_span("handle_agent_report")
    async def handle_agent_report(self, agent_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent report/heartbeat with mandatory reporting tracking"""
        try:
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
                    details=report_data
                )
                session.add(report)
                
                await session.commit()
            
            # Update metrics
            self.AGENT_REPORTING.labels(status="success").inc()
            
            # Process report through mandatory reporting enforcer
            await self.reporting_enforcer.process_agent_report(agent_id, report_data)
            
            # Process metrics through analytics
            if "metrics" in report_data:
                await self.analytics['realtime_processor'].process_metrics(report_data["metrics"])
            
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
                api_key_hash = self._hash_api_key(api_key)
                return secrets.compare_digest(api_key_hash, agent.api_key_hash)
                
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            return False
    
    @tracer.start_as_current_span("handle_task_result")
    async def handle_task_result(self, task_id: str, agent_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process task result from agent"""
        try:
            async with self.get_db_session() as session:
                task = await session.get(Task, task_id)
                if not task:
                    return {"error": "Task not found"}
                
                # Verify agent assignment
                if task.agent_id != agent_id:
                    return {"error": "Task not assigned to this agent"}
                
                # Update task
                task.status = "completed"
                task.result = result
                task.completed_at = datetime.utcnow()
                
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
                self.TASK_COUNT.labels(status="active").dec()
                self.TASK_COUNT.labels(status="completed").inc()
                
                return {
                    "status": "success",
                    "message": "Task result processed"
                }
                
        except Exception as e:
            logger.error(f"Error handling task result: {e}")
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
                    requested_by=requested_by
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
                await self.alerts.send_notification(
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
                
                if approval.status != "pending":
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
                if status == "approved" and approval.request_type == "agent_action":
                    result = await self._execute_agent_action(
                        approval.resource_id, approval.action, admin_id, notes
                    )
                    
                    if "error" in result:
                        return {
                            "status": "approval_processed",
                            "action_status": "failed",
                            "error": result["error"]
                        }
                
                # Notify requester
                await self.alerts.send_notification(
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
    
    @tracer.start_as_current_span("execute_agent_action")
    async def _execute_agent_action(
        self, agent_id: str, action: str, admin_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute approved agent action"""
        try:
            async with self.get_db_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return {"error": "Agent not found"}
                
                # Perform action based on type
                if action == "freeze":
                    agent.status = AgentStatus.FROZEN.value
                    agent.frozen_at = datetime.utcnow()
                    agent.frozen_by = admin_id
                    agent.frozen_reason = notes
                    
                elif action == "unfreeze":
                    if agent.status == AgentStatus.FROZEN.value:
                        agent.status = AgentStatus.INACTIVE.value
                    
                elif action == "delete":
                    agent.status = AgentStatus.DELETED.value
                    agent.deleted_at = datetime.utcnow()
                    agent.deleted_by = admin_id
                    
                    # Revoke API key by clearing hash
                    agent.api_key_hash = None
                    
                elif action == "warn":
                    # Just log warning, don't change status
                    pass
                
                elif action == "audit":
                    # Trigger audit, don't change status
                    await self._trigger_agent_audit(agent_id, admin_id)
                
                elif action == "isolate":
                    agent.status = AgentStatus.ISOLATED.value
                
                else:
                    return {"error": f"Unknown action: {action}"}
                
                await session.commit()
                
                # Create audit log
                audit_log = AuditLog(
                    event_type="agent_action",
                    resource_type="agent",
                    resource_id=agent_id,
                    action=action,
                    performed_by=admin_id,
                    details={"notes": notes}
                )
                session.add(audit_log)
                await session.commit()
                
                # Update metrics
                if action == "delete":
                    self.AGENT_COUNT.labels(status=AgentStatus.ACTIVE.value).dec()
                    self.AGENT_COUNT.labels(status=AgentStatus.DELETED.value).inc()
                
                # Notify agent via WebSocket if connected
                if agent_id in self.active_connections:
                    for ws in self.active_connections[agent_id]:
                        try:
                            await ws.send_json({
                                "type": "control",
                                "action": action,
                                "reason": notes or "Admin action",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        except Exception as e:
                            logger.error(f"Failed to notify agent {agent_id}: {e}")
                
                return {
                    "status": "success",
                    "message": f"Action '{action}' executed successfully"
                }
                
        except Exception as e:
            logger.error(f"Error executing agent action: {e}")
            return {"error": str(e)}
    
    async def _trigger_agent_audit(self, agent_id: str, admin_id: str) -> Dict[str, Any]:
        """Trigger comprehensive agent audit"""
        try:
            # This would initiate a deep audit of agent activity, code, etc.
            # For now, we'll just create an audit record
            async with self.get_db_session() as session:
                audit_log = AuditLog(
                    event_type="agent_audit",
                    resource_type="agent",
                    resource_id=agent_id,
                    action="audit",
                    performed_by=admin_id,
                    details={
                        "message": "Comprehensive agent audit triggered",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    severity="high"
                )
                session.add(audit_log)
                await session.commit()
            
            # In a real implementation, this would trigger a comprehensive
            # security review of the agent, potentially involving:
            # 1. Code analysis
            # 2. Activity log review
            # 3. Resource usage patterns
            # 4. Communication patterns
            # 5. Data access patterns
            
            return {
                "status": "success",
                "message": "Agent audit initiated"
            }
            
        except Exception as e:
            logger.error(f"Error triggering agent audit: {e}")
            return {"error": str(e)}
    
    @tracer.start_as_current_span("create_task")
    async def create_task(self, task_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new task with data validation"""
        try:
            # Validate agent exists and is active
            agent_id = task_data.get("agent_id")
            async with self.get_db_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return {"error": "Agent not found"}
                
                if agent.status != AgentStatus.ACTIVE.value:
                    return {"error": f"Agent is not active (status: {agent.status})"}
                
                # Create task
                task = Task(
                    name=task_data.get("name"),
                    description=task_data.get("description"),
                    agent_id=agent_id,
                    user_id=user_id,
                    task_type=task_data.get("task_type"),
                    priority=task_data.get("priority", "normal"),
                    parameters=task_data.get("parameters", {}),
                    deadline=task_data.get("deadline")
                )
                session.add(task)
                await session.commit()
                await session.refresh(task)
                
                # Log audit event
                audit_log = AuditLog(
                    event_type="task_creation",
                    resource_type="task",
                    resource_id=task.id,
                    action="create",
                    performed_by=user_id,
                    details={
                        "task_type": task.task_type,
                        "agent_id": task.agent_id
                    }
                )
                session.add(audit_log)
                await session.commit()
                
                # Update metrics
                self.TASK_COUNT.labels(status="pending").inc()
                
                # Queue task for processing
                await self.task_queue.enqueue_with_retry(
                    {
                        "task_id": task.id,
                        "agent_id": agent_id,
                        "task_type": task.task_type,
                        "parameters": task.parameters
                    },
                    QueuePriority(task.priority)
                )
                
                return {
                    "id": task.id,
                    "status": "created",
                    "message": "Task created and queued"
                }
                
        except Exception as e:
            logger.error(f"Error creating task: {e}")
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
                self.AGENT_COUNT.labels(status=AgentStatus.INACTIVE.value).dec()
                self.AGENT_COUNT.labels(status=AgentStatus.ACTIVE.value).inc()
    
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
    
    @tracer.start_as_current_span("prune_expired_records")
    async def prune_expired_records(self) -> None:
        """Periodically prune expired records for database maintenance"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run once per hour
                
                # Define cut-off dates
                now = datetime.utcnow()
                audit_cutoff = now - timedelta(days=90)  # Keep audit logs for 90 days
                report_cutoff = now - timedelta(days=30)  # Keep reports for 30 days
                task_cutoff = now - timedelta(days=60)    # Keep completed tasks for 60 days
                
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
                    
                    # Prune old completed tasks
                    await session.execute(
                        text("DELETE FROM tasks WHERE status IN ('completed', 'failed') AND completed_at < :cutoff"),
                        {"cutoff": task_cutoff}
                    )
                    
                    await session.commit()
                    
                logger.info("Expired records pruned successfully")
                
            except Exception as e:
                logger.error(f"Error pruning expired records: {e}")
    
    def _hash_api_key(self, api_key: str) -> str:
        """Create secure hash of API key"""
        key = f"{api_key}:{self.api_key_salt}".encode()
        return hashlib.sha256(key).hexdigest()
    
    def _hash_password(self, password: str) -> str:
        """Create secure hash of password"""
        return self.password_ctx.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.password_ctx.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
            
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.jwt_secret, algorithm="HS256")
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


class MandatoryReportingEnforcer:
    """Enforces mandatory agent reporting with escalating consequences"""
    
    def __init__(self, manager: EnterpriseAgentManager, alert_manager: AlertManager):
        self.manager = manager
        self.alert_manager = alert_manager
        
        # Configuration
        self.reporting_interval = timedelta(minutes=5)  # Expected reporting frequency
        self.warning_threshold = 3     # Missed reports before warning
        self.suspend_threshold = 5     # Missed reports before suspension
        self.non_compliant_threshold = 10  # Missed reports before non-compliance
        
        logger.info("MandatoryReportingEnforcer initialized")
    
    async def start_monitoring(self):
        """Start background monitoring of agent reports"""
        logger.info("Starting mandatory reporting monitoring")
        
        while self.manager.running:
            try:
                await self._check_all_agents()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Reporting monitoring error: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error
    
    async def _check_all_agents(self):
        """Check reporting compliance for all agents"""
        now = datetime.utcnow()
        
        async with self.manager.get_db_session() as session:
            # Get active agents that are not exempt from reporting
            result = await session.execute(
                text("""
                    SELECT id, last_heartbeat, missed_report_count, reporting_status
                    FROM agents 
                    WHERE status != 'deleted' 
                    AND reporting_exemption = false
                """)
            )
            
            for row in result:
                agent_id, last_heartbeat, missed_count, reporting_status = row
                
                # Skip if agent reported recently
                if last_heartbeat and now - last_heartbeat < self.reporting_interval:
                    continue
                
                # Calculate new missed count
                new_missed_count = missed_count + 1
                
                # Apply escalating consequences
                await self._enforce_reporting_compliance(agent_id, new_missed_count, reporting_status)
                
                # Update missed count in database
                await session.execute(
                    text("""
                        UPDATE agents 
                        SET missed_report_count = :count
                        WHERE id = :agent_id
                    """),
                    {"count": new_missed_count, "agent_id": agent_id}
                )
                
                await session.commit()
    
    async def _enforce_reporting_compliance(self, agent_id: str, missed_count: int, current_status: str):
        """Apply escalating consequences based on missed report count"""
        
        # Agent missed too many reports - mark non-compliant and initiate admin review
        if missed_count >= self.non_compliant_threshold and current_status != AgentReportStatus.NON_COMPLIANT.value:
            await self._handle_non_compliant_agent(agent_id, missed_count)
            
        # Agent missed enough reports for suspension
        elif missed_count >= self.suspend_threshold and current_status != AgentReportStatus.SUSPENDED.value:
            await self._suspend_agent(agent_id, missed_count)
            
        # Agent missed enough reports for warning
        elif missed_count >= self.warning_threshold and current_status != AgentReportStatus.WARNED.value:
            await self._warn_agent(agent_id, missed_count)
    
    async def _warn_agent(self, agent_id: str, missed_count: int):
        """Send warning to agent about missed reports"""
        logger.warning(f"Agent {agent_id} has missed {missed_count} reports - sending warning")
        
        # Update agent reporting status
        async with self.manager.get_db_session() as session:
            await session.execute(
                text("""
                    UPDATE agents 
                    SET reporting_status = :status,
                        last_warning_at = :now 
                    WHERE id = :agent_id
                """),
                {
                    "status": AgentReportStatus.WARNED.value, 
                    "now": datetime.utcnow(),
                    "agent_id": agent_id
                }
            )
            await session.commit()
        
        # Send warning message to agent if connected
        if agent_id in self.manager.active_connections:
            for ws in self.manager.active_connections[agent_id]:
                try:
                    await ws.send_json({
                        "type": "warning",
                        "reason": "missed_reports",
                        "count": missed_count,
                        "timestamp": datetime.utcnow().isoformat(),
                        "action_required": "resume_reporting"
                    })
                except Exception as e:
                    logger.error(f"Failed to send warning to agent {agent_id}: {e}")
        
        # Create audit log
        async with self.manager.get_db_session() as session:
            audit_log = AuditLog(
                event_type="reporting_warning",
                resource_type="agent",
                resource_id=agent_id,
                action="warn",
                performed_by="system",
                details={"missed_count": missed_count}
            )
            session.add(audit_log)
            await session.commit()
    
    async def _suspend_agent(self, agent_id: str, missed_count: int):
        """Temporarily suspend non-reporting agent"""
        logger.warning(f"Agent {agent_id} has missed {missed_count} reports - suspending")
        
        # Update agent reporting status and overall status
        async with self.manager.get_db_session() as session:
            await session.execute(
                text("""
                    UPDATE agents 
                    SET reporting_status = :rep_status,
                        status = :status,
                        suspended_at = :now,
                        suspended_by = 'system',
                        suspended_reason = :reason
                    WHERE id = :agent_id
                """),
                {
                    "rep_status": AgentReportStatus.SUSPENDED.value, 
                    "status": AgentStatus.SUSPENDED.value,
                    "now": datetime.utcnow(),
                    "reason": f"Missed {missed_count} required reports",
                    "agent_id": agent_id
                }
            )
            
            # Create audit log
            audit_log = AuditLog(
                event_type="agent_suspended",
                resource_type="agent",
                resource_id=agent_id,
                action="suspend",
                performed_by="system",
                details={
                    "reason": "missed_reports",
                    "missed_count": missed_count
                }
            )
            session.add(audit_log)
            await session.commit()
        
        # Send suspension message to agent if connected
        if agent_id in self.manager.active_connections:
            for ws in self.manager.active_connections[agent_id]:
                try:
                    await ws.send_json({
                        "type": "control",
                        "action": "suspend",
                        "reason": "missed_reports",
                        "count": missed_count,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Failed to notify agent {agent_id} of suspension: {e}")
        
        # Send alert to admins
        await self.alert_manager.send_notification(
            "admin",
            {
                "type": "agent_suspended",
                "title": f"Agent {agent_id} automatically suspended",
                "message": f"Agent automatically suspended after missing {missed_count} required reports",
                "severity": AlertSeverity.HIGH,
                "action_required": True
            }
        )
        
        # Update metrics
        self.manager.AGENT_COUNT.labels(status=AgentStatus.ACTIVE.value).dec()
        self.manager.AGENT_COUNT.labels(status=AgentStatus.SUSPENDED.value).inc()
    
    async def _handle_non_compliant_agent(self, agent_id: str, missed_count: int):
        """Handle severely non-compliant agent - request admin action for deletion"""
        logger.error(f"Agent {agent_id} is non-compliant with {missed_count} missed reports")
        
        # Update agent reporting status
        async with self.manager.get_db_session() as session:
            await session.execute(
                text("""
                    UPDATE agents 
                    SET reporting_status = :status
                    WHERE id = :agent_id
                """),
                {"status": AgentReportStatus.NON_COMPLIANT.value, "agent_id": agent_id}
            )
            await session.commit()
        
        # Create admin approval request for agent deletion
        result = await self.manager.request_agent_action(
            agent_id=agent_id,
            action="delete",
            reason=f"Non-compliant with reporting requirements. Missed {missed_count} reports.",
            requested_by="system"
        )
        
        # Create security event
        async with self.manager.get_db_session() as session:
            security_event = SecurityEvent(
                event_type="reporting_violation",
                severity="high",
                source="mandatory_reporting",
                description=f"Agent {agent_id} severely violated reporting requirements",
                details={
                    "missed_count": missed_count,
                    "approval_request_id": result.get("approval_id")
                }
            )
            session.add(security_event)
            await session.commit()
        
        # Update metrics
        self.manager.SECURITY_EVENTS.labels(
            event_type="reporting_violation",
            severity="high"
        ).inc()
    
    async def process_agent_report(self, agent_id: str, report: Dict[str, Any]):
        """Process incoming agent report"""
        # Reset reporting status if agent was previously warned or suspended
        async with self.manager.get_db_session() as session:
            result = await session.execute(
                text("""
                    SELECT reporting_status, status 
                    FROM agents 
                    WHERE id = :agent_id
                """),
                {"agent_id": agent_id}
            )
            row = result.fetchone()
            
            if not row:
                return  # Agent not found
                
            reporting_status, agent_status = row
            
            if reporting_status in [
                AgentReportStatus.WARNED.value,
                AgentReportStatus.SUSPENDED.value,
                AgentReportStatus.NON_COMPLIANT.value
            ]:
                # Reset missed report count and status
                updates = {
                    "reporting_status": AgentReportStatus.COMPLIANT.value,
                    "missed_report_count": 0,
                    "agent_id": agent_id
                }
                
                # If agent was suspended, request unsuspend
                if agent_status == AgentStatus.SUSPENDED.value:
                    await self._request_unsuspend_agent(agent_id)
                else:
                    # Otherwise just update the reporting status
                    await session.execute(
                        text("""
                            UPDATE agents 
                            SET reporting_status = :reporting_status,
                                missed_report_count = :missed_report_count
                            WHERE id = :agent_id
                        """),
                        updates
                    )
                    await session.commit()
    
    async def _request_unsuspend_agent(self, agent_id: str):
        """Request admin approval to unsuspend agent"""
        # Request action through the lifecycle manager
        logger.info(f"Requesting unsuspend for agent {agent_id}")
        # Implementation would notify admin for approval
        pass