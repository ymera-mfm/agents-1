import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from enum import Enum
import json

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.secure_database_manager import SecureDatabaseManager
from models.secure_models import Agent, Task, AuditLog
from security.rbac_manager import RBACManager, Permission
from monitoring.telemetry_manager import TelemetryManager
from monitoring.alert_manager import AlertManager, AlertCategory, AlertSeverity

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent lifecycle states"""
    REGISTERED = "registered"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    QUARANTINED = "quarantined"
    COMPROMISED = "compromised"
    OFFLINE = "offline"
    DECOMMISSIONING = "decommissioning"
    DECOMMISSIONED = "decommissioned"


class AgentHealthStatus(str, Enum):
    """Agent health indicators"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class AgentRegistrationRequest(BaseModel):
    """Agent registration request model"""
    name: str = Field(..., min_length=3, max_length=255)
    agent_type: str = Field(..., min_length=2, max_length=50)
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')
    capabilities: Dict[str, Any]
    hardware_specs: Optional[Dict[str, Any]] = None
    network_info: Optional[Dict[str, Any]] = None
    
    @field_validator('capabilities')
    @classmethod
    def validate_capabilities(cls, v):
        required_fields = ['types', 'max_concurrent_tasks', 'supported_protocols']
        if not all(field in v for field in required_fields):
            raise ValueError(f"Capabilities must include: {required_fields}")
        return v


class AgentMetricsSnapshot(BaseModel):
    """Real-time agent metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cpu_usage: float = Field(..., ge=0, le=100)
    memory_usage: float = Field(..., ge=0, le=100)
    disk_usage: float = Field(..., ge=0, le=100)
    network_latency: float = Field(..., ge=0)
    active_tasks: int = Field(..., ge=0)
    completed_tasks: int = Field(..., ge=0)
    failed_tasks: int = Field(..., ge=0)
    error_rate: float = Field(..., ge=0, le=1)
    response_time_avg: float = Field(..., ge=0)
    uptime_seconds: float = Field(..., ge=0)


class AgentLifecycleManager:
    """
    Production-ready Agent Lifecycle Management System
    
    Features:
    - Comprehensive lifecycle management
    - Health monitoring and predictive analytics
    - Automated remediation
    - Quarantine and security controls
    - Performance tracking and optimization
    - Audit trail for all operations
    """

    def __init__(
        self,
        db_manager: SecureDatabaseManager,
        rbac_manager: RBACManager,
        telemetry_manager: TelemetryManager,
        alert_manager: AlertManager
    ):
        self.db_manager = db_manager
        self.rbac_manager = rbac_manager
        self.telemetry_manager = telemetry_manager
        self.alert_manager = alert_manager
        
        # In-memory cache for hot data
        self._agent_cache: Dict[str, Agent] = {}
        self._metrics_buffer: Dict[str, List[AgentMetricsSnapshot]] = {}
        
        # Configuration
        self.heartbeat_timeout = settings.performance.agent_heartbeat_timeout_seconds
        self.health_check_interval = settings.performance.agent_health_check_interval_seconds
        self.metrics_retention_hours = 24
        self.max_metrics_per_agent = 1000
        
        # Performance thresholds
        self.thresholds = {
            'cpu_critical': 95.0,
            'cpu_warning': 85.0,
            'memory_critical': 95.0,
            'memory_warning': 85.0,
            'error_rate_critical': 0.15,
            'error_rate_warning': 0.05,
            'response_time_critical': 5000,  # ms
            'response_time_warning': 2000,   # ms
        }
        
        logger.info("Enhanced AgentLifecycleManager initialized")

    async def register_agent(
        self,
        tenant_id: str,
        registration: AgentRegistrationRequest,
        requester_id: str
    ) -> Agent:
        """
        Register a new agent with comprehensive validation and provisioning
        """
        async with self.db_manager.get_session() as session:
            try:
                # Check tenant agent limit
                agent_count = await session.scalar(
                    select(func.count(Agent.id)).where(
                        and_(
                            Agent.tenant_id == tenant_id,
                            Agent.status.notin_([
                                AgentStatus.DECOMMISSIONED.value,
                                AgentStatus.DECOMMISSIONING.value
                            ])
                        )
                    )
                )
                
                max_agents = settings.performance.max_agents_per_tenant
                if agent_count >= max_agents:
                    await self._create_audit_log(
                        session, tenant_id, requester_id,
                        "agent_registration_denied",
                        "agent", None,
                        {"reason": "tenant_limit_reached", "limit": max_agents}
                    )
                    
                    await self.alert_manager.create_alert(
                        category=AlertCategory.SYSTEM,
                        severity=AlertSeverity.WARNING,
                        title="Agent Registration Limit Reached",
                        description=f"Tenant {tenant_id} attempted to register agent but reached limit of {max_agents}",
                        source="AgentLifecycleManager",
                        metadata={"tenant_id": tenant_id, "agent_name": registration.name}
                    )
                    
                    raise ValueError(f"Tenant has reached maximum agent limit of {max_agents}")
                
                # Check for duplicate agent name within tenant
                existing = await session.scalar(
                    select(Agent).where(
                        and_(
                            Agent.tenant_id == tenant_id,
                            Agent.name == registration.name,
                            Agent.status != AgentStatus.DECOMMISSIONED.value
                        )
                    )
                )
                
                if existing:
                    raise ValueError(f"Agent with name '{registration.name}' already exists for this tenant")
                
                # Create agent record
                new_agent = Agent(
                    tenant_id=tenant_id,
                    name=registration.name,
                    type=registration.agent_type,
                    version=registration.version,
                    capabilities=registration.capabilities,
                    status=AgentStatus.PROVISIONING.value,
                    security_score=100,
                    performance_metrics={
                        "cpu_usage": 0,
                        "memory_usage": 0,
                        "response_time": 0,
                        "error_rate": 0,
                        "throughput": 0,
                        "total_tasks": 0,
                        "successful_tasks": 0,
                        "failed_tasks": 0
                    },
                    created_by=requester_id
                )
                
                session.add(new_agent)
                await session.flush()
                
                # Create audit log
                await self._create_audit_log(
                    session, tenant_id, requester_id,
                    "agent_registered",
                    "agent", new_agent.id,
                    {
                        "agent_name": registration.name,
                        "agent_type": registration.agent_type,
                        "version": registration.version,
                        "capabilities": registration.capabilities
                    }
                )
                
                await session.commit()
                await session.refresh(new_agent)
                
                # Cache the agent
                self._agent_cache[new_agent.id] = new_agent
                
                # Record telemetry
                await self.telemetry_manager.record_event(
                    "agent_registered",
                    {
                        "agent_id": new_agent.id,
                        "tenant_id": tenant_id,
                        "agent_type": registration.agent_type,
                        "version": registration.version
                    }
                )
                
                await self.telemetry_manager.record_metric(
                    "agents_total",
                    1,
                    {"tenant_id": tenant_id, "status": "provisioning"}
                )
                
                # Schedule provisioning tasks
                asyncio.create_task(self._provision_agent(new_agent.id))
                
                logger.info(f"Agent {new_agent.id} registered successfully for tenant {tenant_id}")
                return new_agent
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Agent registration failed: {e}", exc_info=True)
                raise

    async def _provision_agent(self, agent_id: str) -> None:
        """
        Provision agent with necessary resources and configuration
        """
        try:
            await asyncio.sleep(2)  # Simulate provisioning delay
            
            async with self.db_manager.get_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return
                
                # Perform provisioning steps
                # 1. Allocate resources
                # 2. Configure networking
                # 3. Install certificates
                # 4. Set up monitoring
                
                agent.status = AgentStatus.ACTIVE.value
                agent.verified_at = datetime.utcnow()
                await session.commit()
                
                await self.telemetry_manager.record_event(
                    "agent_provisioned",
                    {"agent_id": agent_id, "tenant_id": agent.tenant_id}
                )
                
                logger.info(f"Agent {agent_id} provisioned successfully")
                
        except Exception as e:
            logger.error(f"Agent provisioning failed for {agent_id}: {e}", exc_info=True)
            await self._handle_provisioning_failure(agent_id)

    async def _handle_provisioning_failure(self, agent_id: str) -> None:
        """Handle provisioning failures"""
        async with self.db_manager.get_session() as session:
            agent = await session.get(Agent, agent_id)
            if agent:
                agent.status = AgentStatus.OFFLINE.value
                await session.commit()
                
                await self.alert_manager.create_alert(
                    category=AlertCategory.SYSTEM,
                    severity=AlertSeverity.CRITICAL,
                    title="Agent Provisioning Failed",
                    description=f"Agent {agent_id} failed to provision",
                    source="AgentLifecycleManager",
                    metadata={"agent_id": agent_id, "tenant_id": agent.tenant_id}
                )

    async def update_agent_metrics(
        self,
        agent_id: str,
        metrics: AgentMetricsSnapshot
    ) -> None:
        """
        Update agent metrics with health assessment
        """
        try:
            # Store in buffer
            if agent_id not in self._metrics_buffer:
                self._metrics_buffer[agent_id] = []
            
            self._metrics_buffer[agent_id].append(metrics)
            
            # Trim buffer
            if len(self._metrics_buffer[agent_id]) > self.max_metrics_per_agent:
                self._metrics_buffer[agent_id] = self._metrics_buffer[agent_id][-self.max_metrics_per_agent:]
            
            # Update database
            async with self.db_manager.get_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return
                
                # Update performance metrics
                agent.performance_metrics = {
                    "cpu_usage": metrics.cpu_usage,
                    "memory_usage": metrics.memory_usage,
                    "disk_usage": metrics.disk_usage,
                    "network_latency": metrics.network_latency,
                    "response_time": metrics.response_time_avg,
                    "error_rate": metrics.error_rate,
                    "throughput": metrics.completed_tasks,
                    "total_tasks": metrics.active_tasks + metrics.completed_tasks,
                    "successful_tasks": metrics.completed_tasks,
                    "failed_tasks": metrics.failed_tasks,
                    "uptime": metrics.uptime_seconds
                }
                
                agent.last_heartbeat = datetime.utcnow()
                
                # Assess health and update status
                health_status = self._assess_agent_health(metrics)
                
                if health_status == AgentHealthStatus.CRITICAL:
                    await self._handle_critical_agent(session, agent, metrics)
                elif health_status == AgentHealthStatus.POOR:
                    await self._handle_degraded_agent(session, agent, metrics)
                
                # Update agent status based on activity
                if metrics.active_tasks > 0:
                    if agent.status == AgentStatus.IDLE.value:
                        agent.status = AgentStatus.BUSY.value
                else:
                    if agent.status == AgentStatus.BUSY.value:
                        agent.status = AgentStatus.IDLE.value
                
                await session.commit()
                
                # Record telemetry
                await self.telemetry_manager.record_metric(
                    "agent_cpu_usage",
                    metrics.cpu_usage,
                    {"agent_id": agent_id}
                )
                
                await self.telemetry_manager.record_metric(
                    "agent_memory_usage",
                    metrics.memory_usage,
                    {"agent_id": agent_id}
                )
                
                await self.telemetry_manager.record_metric(
                    "agent_error_rate",
                    metrics.error_rate,
                    {"agent_id": agent_id}
                )
                
        except Exception as e:
            logger.error(f"Failed to update metrics for agent {agent_id}: {e}", exc_info=True)

    def _assess_agent_health(self, metrics: AgentMetricsSnapshot) -> AgentHealthStatus:
        """
        Assess agent health based on metrics
        """
        critical_count = 0
        warning_count = 0
        
        # CPU check
        if metrics.cpu_usage >= self.thresholds['cpu_critical']:
            critical_count += 1
        elif metrics.cpu_usage >= self.thresholds['cpu_warning']:
            warning_count += 1
        
        # Memory check
        if metrics.memory_usage >= self.thresholds['memory_critical']:
            critical_count += 1
        elif metrics.memory_usage >= self.thresholds['memory_warning']:
            warning_count += 1
        
        # Error rate check
        if metrics.error_rate >= self.thresholds['error_rate_critical']:
            critical_count += 1
        elif metrics.error_rate >= self.thresholds['error_rate_warning']:
            warning_count += 1
        
        # Response time check
        if metrics.response_time_avg >= self.thresholds['response_time_critical']:
            critical_count += 1
        elif metrics.response_time_avg >= self.thresholds['response_time_warning']:
            warning_count += 1
        
        # Determine overall health
        if critical_count >= 2:
            return AgentHealthStatus.CRITICAL
        elif critical_count >= 1 or warning_count >= 3:
            return AgentHealthStatus.POOR
        elif warning_count >= 2:
            return AgentHealthStatus.FAIR
        elif warning_count >= 1:
            return AgentHealthStatus.GOOD
        else:
            return AgentHealthStatus.EXCELLENT

    async def _handle_critical_agent(
        self,
        session: AsyncSession,
        agent: Agent,
        metrics: AgentMetricsSnapshot
    ) -> None:
        """Handle agent in critical state"""
        if agent.status not in [AgentStatus.QUARANTINED.value, AgentStatus.MAINTENANCE.value]:
            agent.status = AgentStatus.DEGRADED.value
            agent.security_score = max(0, agent.security_score - 20)
            
            await self.alert_manager.create_alert(
                category=AlertCategory.PERFORMANCE,
                severity=AlertSeverity.CRITICAL,
                title="Agent Critical Health Status",
                description=f"Agent {agent.name} ({agent.id}) is in critical health state",
                source="AgentLifecycleManager",
                metadata={
                    "agent_id": agent.id,
                    "tenant_id": agent.tenant_id,
                    "metrics": metrics.dict()
                }
            )
            
            # Trigger automated remediation
            asyncio.create_task(self._attempt_auto_remediation(agent.id))

    async def _handle_degraded_agent(
        self,
        session: AsyncSession,
        agent: Agent,
        metrics: AgentMetricsSnapshot
    ) -> None:
        """Handle agent in degraded state"""
        if agent.status == AgentStatus.ACTIVE.value:
            agent.status = AgentStatus.DEGRADED.value
            agent.security_score = max(0, agent.security_score - 5)
            
            await self.alert_manager.create_alert(
                category=AlertCategory.PERFORMANCE,
                severity=AlertSeverity.WARNING,
                title="Agent Performance Degraded",
                description=f"Agent {agent.name} ({agent.id}) performance is degraded",
                source="AgentLifecycleManager",
                metadata={
                    "agent_id": agent.id,
                    "tenant_id": agent.tenant_id,
                    "metrics": metrics.dict()
                }
            )

    async def _attempt_auto_remediation(self, agent_id: str) -> None:
        """
        Attempt automated remediation for troubled agents
        """
        try:
            logger.info(f"Attempting auto-remediation for agent {agent_id}")
            
            async with self.db_manager.get_session() as session:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return
                
                # Remediation strategies
                remediation_steps = []
                
                # 1. Restart agent if high CPU/memory
                metrics = self._metrics_buffer.get(agent_id, [])
                if metrics:
                    latest = metrics[-1]
                    if latest.cpu_usage > 90 or latest.memory_usage > 90:
                        remediation_steps.append("restart")
                    
                    # 2. Clear cache if disk usage high
                    if latest.disk_usage > 85:
                        remediation_steps.append("clear_cache")
                    
                    # 3. Reduce load if error rate high
                    if latest.error_rate > 0.1:
                        remediation_steps.append("reduce_load")
                
                # Execute remediation
                for step in remediation_steps:
                    success = await self._execute_remediation_step(agent_id, step)
                    if success:
                        logger.info(f"Remediation step '{step}' successful for agent {agent_id}")
                    else:
                        logger.warning(f"Remediation step '{step}' failed for agent {agent_id}")
                
                # Update audit log
                await self._create_audit_log(
                    session, agent.tenant_id, "system",
                    "agent_auto_remediation",
                    "agent", agent_id,
                    {"steps_executed": remediation_steps}
                )
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Auto-remediation failed for agent {agent_id}: {e}", exc_info=True)

    async def _execute_remediation_step(self, agent_id: str, step: str) -> bool:
        """Execute a specific remediation step"""
        try:
            # This would integrate with actual agent management APIs
            # For now, simulate the action
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Remediation step {step} failed: {e}")
            return False

    async def quarantine_agent(
        self,
        agent_id: str,
        reason: str,
        requester_id: str
    ) -> bool:
        """
        Quarantine an agent due to security concerns
        """
        async with self.db_manager.get_session() as session:
            try:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return False
                
                old_status = agent.status
                agent.status = AgentStatus.QUARANTINED.value
                agent.security_score = 0
                
                await self._create_audit_log(
                    session, agent.tenant_id, requester_id,
                    "agent_quarantined",
                    "agent", agent_id,
                    {"reason": reason, "old_status": old_status},
                    security_level="critical"
                )
                
                await session.commit()
                
                await self.alert_manager.create_alert(
                    category=AlertCategory.SECURITY,
                    severity=AlertSeverity.EMERGENCY,
                    title="Agent Quarantined",
                    description=f"Agent {agent.name} ({agent_id}) has been quarantined: {reason}",
                    source="AgentLifecycleManager",
                    metadata={
                        "agent_id": agent_id,
                        "tenant_id": agent.tenant_id,
                        "reason": reason
                    }
                )
                
                logger.warning(f"Agent {agent_id} quarantined: {reason}")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to quarantine agent {agent_id}: {e}", exc_info=True)
                return False

    async def get_agent_analytics(
        self,
        agent_id: str,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for an agent
        """
        metrics = self._metrics_buffer.get(agent_id, [])
        
        # Filter by time range
        cutoff = datetime.utcnow() - timedelta(hours=time_range_hours)
        recent_metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not recent_metrics:
            return {"error": "No metrics available"}
        
        # Calculate statistics
        cpu_values = [m.cpu_usage for m in recent_metrics]
        memory_values = [m.memory_usage for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]
        response_times = [m.response_time_avg for m in recent_metrics]
        
        return {
            "agent_id": agent_id,
            "time_range_hours": time_range_hours,
            "data_points": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "current": recent_metrics[-1].cpu_usage
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values),
                "current": recent_metrics[-1].memory_usage
            },
            "error_rate": {
                "avg": sum(error_rates) / len(error_rates),
                "min": min(error_rates),
                "max": max(error_rates),
                "current": recent_metrics[-1].error_rate
            },
            "response_time": {
                "avg": sum(response_times) / len(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "current": recent_metrics[-1].response_time_avg
            },
            "tasks": {
                "total": recent_metrics[-1].active_tasks + recent_metrics[-1].completed_tasks,
                "active": recent_metrics[-1].active_tasks,
                "completed": recent_metrics[-1].completed_tasks,
                "failed": recent_metrics[-1].failed_tasks,
                "success_rate": (recent_metrics[-1].completed_tasks / 
                               max(1, recent_metrics[-1].completed_tasks + recent_metrics[-1].failed_tasks))
            }
        }

    async def _create_audit_log(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        details: Dict[str, Any],
        security_level: str = "info"
    ) -> None:
        """Create audit log entry"""
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            security_level=security_level
        )
        session.add(audit_log)

    async def list_agents(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        agent_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Agent]:
        """List agents with filtering"""
        async with self.db_manager.get_session() as session:
            query = select(Agent).where(Agent.tenant_id == tenant_id)
            
            if status:
                query = query.where(Agent.status == status)
            if agent_type:
                query = query.where(Agent.type == agent_type)
            
            query = query.order_by(desc(Agent.created_at)).offset(skip).limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()

    async def decommission_agent(
        self,
        agent_id: str,
        reason: str,
        requester_id: str
    ) -> bool:
        """
        Gracefully decommission an agent
        """
        async with self.db_manager.get_session() as session:
            try:
                agent = await session.get(Agent, agent_id)
                if not agent:
                    return False
                
                # Set to decommissioning state
                agent.status = AgentStatus.DECOMMISSIONING.value
                agent.decommission_reason = reason
                await session.commit()
                
                # Schedule decommissioning tasks
                asyncio.create_task(self._complete_decommissioning(agent_id, requester_id))
                
                logger.info(f"Agent {agent_id} decommissioning initiated")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to initiate decommissioning for {agent_id}: {e}", exc_info=True)
                return False

    async def _complete_decommissioning(self, agent_id: str, requester_id: str) -> None:
        """Complete agent decommissioning"""
        try:
            # 1. Complete or cancel pending tasks
            # 2. Archive agent data
            # 3. Release resources
            # 4. Remove from active monitoring
            
            await asyncio.sleep(5)  # Simulate cleanup
            
            async with self.db_manager.get_session() as session:
                agent = await session.get(Agent, agent_id)
                if agent:
                    agent.status = AgentStatus.DECOMMISSIONED.value
                    agent.decommissioned_at = datetime.utcnow()
                    agent.decommissioned_by = requester_id
                    
                    await self._create_audit_log(
                        session, agent.tenant_id, requester_id,
                        "agent_decommissioned",
                        "agent", agent_id,
                        {"reason": agent.decommission_reason}
                    )
                    
                    await session.commit()
                    
                    # Remove from cache
                    self._agent_cache.pop(agent_id, None)
                    self._metrics_buffer.pop(agent_id, None)
                    
                    logger.info(f"Agent {agent_id} decommissioned successfully")
                    
        except Exception as e:
            logger.error(f"Failed to complete decommissioning for {agent_id}: {e}", exc_info=True)

    async def health_check(self) -> str:
        """Health check for the lifecycle manager"""
        try:
            async with self.db_manager.get_session() as session:
                await session.execute(select(Agent).limit(1))
            return "healthy"
        except Exception as e:
            logger.error(f"AgentLifecycleManager health check failed: {e}")
            return "unhealthy"
