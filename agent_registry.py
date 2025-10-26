"""
Agent Registry - Central registry for all agents in the system
Provides agent discovery, health tracking, and version management
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration"""
    REGISTERING = "registering"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    FAILED = "failed"
    DEREGISTERED = "deregistered"


@dataclass
class AgentRecord:
    """Agent registration record"""
    agent_id: str
    agent_name: str
    agent_type: str
    capabilities: List[str]
    version: str
    host: str
    port: int
    status: AgentStatus = AgentStatus.REGISTERING
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    
    # Health tracking
    last_heartbeat: float = field(default_factory=time.time)
    last_health_check: float = field(default_factory=time.time)
    health_score: float = 1.0
    consecutive_failures: int = 0
    
    # Metrics
    registered_at: float = field(default_factory=time.time)
    tasks_processed: int = 0
    tasks_failed: int = 0
    average_response_time_ms: float = 0.0
    
    # Load balancing
    current_load: int = 0
    max_load: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return (
            self.status == AgentStatus.ACTIVE and
            self.health_score >= 0.5 and
            self.consecutive_failures < 3 and
            time.time() - self.last_heartbeat < 90  # 90 second heartbeat timeout
        )
    
    @property
    def is_available(self) -> bool:
        """Check if agent is available for work"""
        return self.is_healthy and self.current_load < self.max_load


class AgentRegistry:
    """
    Central Agent Registry
    
    Features:
    - Agent registration and deregistration
    - Health tracking and monitoring
    - Version management
    - Capability-based discovery
    - Load-aware agent selection
    - Automatic cleanup of dead agents
    """
    
    def __init__(
        self,
        heartbeat_timeout: int = 90,
        health_check_interval: int = 30,
        cleanup_interval: int = 300
    ):
        self.heartbeat_timeout = heartbeat_timeout
        self.health_check_interval = health_check_interval
        self.cleanup_interval = cleanup_interval
        
        # Registry storage
        self._agents: Dict[str, AgentRecord] = {}
        self._agents_by_type: Dict[str, Set[str]] = {}
        self._agents_by_capability: Dict[str, Set[str]] = {}
        
        # Locks
        self._lock = asyncio.Lock()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("Agent Registry initialized")
    
    async def start(self):
        """Start background tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Agent Registry background tasks started")
    
    async def stop(self):
        """Stop background tasks"""
        self._shutdown_event.set()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            await asyncio.gather(self._cleanup_task, return_exceptions=True)
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            await asyncio.gather(self._monitoring_task, return_exceptions=True)
        
        logger.info("Agent Registry stopped")
    
    # =========================================================================
    # REGISTRATION
    # =========================================================================
    
    async def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        capabilities: List[str],
        version: str,
        host: str,
        port: int,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        max_load: int = 10
    ) -> AgentRecord:
        """Register a new agent"""
        async with self._lock:
            if agent_id in self._agents:
                logger.warning(f"Agent {agent_id} already registered, updating record")
                return await self._update_agent(agent_id, metadata, tags)
            
            record = AgentRecord(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_type=agent_type,
                capabilities=capabilities,
                version=version,
                host=host,
                port=port,
                metadata=metadata or {},
                tags=tags or {},
                max_load=max_load,
                status=AgentStatus.ACTIVE
            )
            
            self._agents[agent_id] = record
            
            # Index by type
            if agent_type not in self._agents_by_type:
                self._agents_by_type[agent_type] = set()
            self._agents_by_type[agent_type].add(agent_id)
            
            # Index by capabilities
            for capability in capabilities:
                if capability not in self._agents_by_capability:
                    self._agents_by_capability[capability] = set()
                self._agents_by_capability[capability].add(agent_id)
            
            logger.info(
                f"Agent registered",
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities
            )
            
            return record
    
    async def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an agent"""
        async with self._lock:
            if agent_id not in self._agents:
                logger.warning(f"Agent {agent_id} not found for deregistration")
                return False
            
            record = self._agents[agent_id]
            record.status = AgentStatus.DEREGISTERED
            
            # Remove from indices
            self._agents_by_type.get(record.agent_type, set()).discard(agent_id)
            for capability in record.capabilities:
                self._agents_by_capability.get(capability, set()).discard(agent_id)
            
            # Remove from registry
            del self._agents[agent_id]
            
            logger.info(f"Agent deregistered", agent_id=agent_id)
            return True
    
    async def _update_agent(
        self,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> AgentRecord:
        """Update agent record"""
        record = self._agents[agent_id]
        
        if metadata:
            record.metadata.update(metadata)
        if tags:
            record.tags.update(tags)
        
        record.last_heartbeat = time.time()
        record.status = AgentStatus.ACTIVE
        record.consecutive_failures = 0
        
        logger.debug(f"Agent updated", agent_id=agent_id)
        return record
    
    # =========================================================================
    # HEARTBEAT AND HEALTH
    # =========================================================================
    
    async def heartbeat(
        self,
        agent_id: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record agent heartbeat"""
        async with self._lock:
            if agent_id not in self._agents:
                logger.warning(f"Heartbeat from unknown agent {agent_id}")
                return False
            
            record = self._agents[agent_id]
            record.last_heartbeat = time.time()
            
            if metrics:
                record.current_load = metrics.get('current_load', record.current_load)
                record.tasks_processed = metrics.get('tasks_processed', record.tasks_processed)
                record.tasks_failed = metrics.get('tasks_failed', record.tasks_failed)
                record.average_response_time_ms = metrics.get('avg_response_time', record.average_response_time_ms)
            
            # Update health status
            if record.status != AgentStatus.ACTIVE:
                record.status = AgentStatus.ACTIVE
                record.consecutive_failures = 0
                logger.info(f"Agent recovered", agent_id=agent_id)
            
            return True
    
    async def update_health(
        self,
        agent_id: str,
        health_score: float,
        status: Optional[AgentStatus] = None
    ) -> bool:
        """Update agent health"""
        async with self._lock:
            if agent_id not in self._agents:
                return False
            
            record = self._agents[agent_id]
            record.health_score = max(0.0, min(1.0, health_score))
            record.last_health_check = time.time()
            
            if status:
                old_status = record.status
                record.status = status
                
                if old_status != status:
                    logger.info(
                        f"Agent status changed",
                        agent_id=agent_id,
                        old_status=old_status.value,
                        new_status=status.value
                    )
            
            return True
    
    async def record_failure(self, agent_id: str):
        """Record agent failure"""
        async with self._lock:
            if agent_id not in self._agents:
                return
            
            record = self._agents[agent_id]
            record.consecutive_failures += 1
            record.health_score = max(0.0, record.health_score - 0.2)
            
            if record.consecutive_failures >= 3:
                record.status = AgentStatus.FAILED
                logger.error(f"Agent marked as failed", agent_id=agent_id)
            elif record.consecutive_failures >= 2:
                record.status = AgentStatus.DEGRADED
                logger.warning(f"Agent degraded", agent_id=agent_id)
    
    # =========================================================================
    # DISCOVERY
    # =========================================================================
    
    async def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        """Get agent by ID"""
        return self._agents.get(agent_id)
    
    async def get_agents_by_type(
        self,
        agent_type: str,
        only_healthy: bool = True
    ) -> List[AgentRecord]:
        """Get all agents of a specific type"""
        agent_ids = self._agents_by_type.get(agent_type, set())
        agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]
        
        if only_healthy:
            agents = [a for a in agents if a.is_healthy]
        
        return agents
    
    async def get_agents_by_capability(
        self,
        capability: str,
        only_available: bool = True
    ) -> List[AgentRecord]:
        """Get all agents with a specific capability"""
        agent_ids = self._agents_by_capability.get(capability, set())
        agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]
        
        if only_available:
            agents = [a for a in agents if a.is_available]
        
        # Sort by load (least loaded first)
        agents.sort(key=lambda a: (a.current_load / a.max_load, -a.health_score))
        
        return agents
    
    async def get_all_agents(
        self,
        only_healthy: bool = False
    ) -> List[AgentRecord]:
        """Get all registered agents"""
        agents = list(self._agents.values())
        
        if only_healthy:
            agents = [a for a in agents if a.is_healthy]
        
        return agents
    
    async def find_best_agent(
        self,
        capability: str,
        exclude_agents: Optional[Set[str]] = None
    ) -> Optional[AgentRecord]:
        """Find best available agent for a capability"""
        agents = await self.get_agents_by_capability(capability, only_available=True)
        
        if exclude_agents:
            agents = [a for a in agents if a.agent_id not in exclude_agents]
        
        return agents[0] if agents else None
    
    # =========================================================================
    # LOAD MANAGEMENT
    # =========================================================================
    
    async def increment_load(self, agent_id: str) -> bool:
        """Increment agent load"""
        async with self._lock:
            if agent_id not in self._agents:
                return False
            
            record = self._agents[agent_id]
            record.current_load += 1
            return True
    
    async def decrement_load(self, agent_id: str) -> bool:
        """Decrement agent load"""
        async with self._lock:
            if agent_id not in self._agents:
                return False
            
            record = self._agents[agent_id]
            record.current_load = max(0, record.current_load - 1)
            return True
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        agents = list(self._agents.values())
        
        return {
            'total_agents': len(agents),
            'active_agents': sum(1 for a in agents if a.status == AgentStatus.ACTIVE),
            'degraded_agents': sum(1 for a in agents if a.status == AgentStatus.DEGRADED),
            'failed_agents': sum(1 for a in agents if a.status == AgentStatus.FAILED),
            'healthy_agents': sum(1 for a in agents if a.is_healthy),
            'available_agents': sum(1 for a in agents if a.is_available),
            'total_load': sum(a.current_load for a in agents),
            'agent_types': len(self._agents_by_type),
            'capabilities': len(self._agents_by_capability),
            'average_health_score': sum(a.health_score for a in agents) / len(agents) if agents else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # =========================================================================
    # BACKGROUND TASKS
    # =========================================================================
    
    async def _cleanup_loop(self):
        """Cleanup dead agents"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_dead_agents()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_dead_agents(self):
        """Remove agents that haven't sent heartbeat"""
        current_time = time.time()
        dead_agents = []
        
        async with self._lock:
            for agent_id, record in list(self._agents.items()):
                time_since_heartbeat = current_time - record.last_heartbeat
                
                if time_since_heartbeat > self.heartbeat_timeout:
                    logger.warning(
                        f"Agent timeout, removing",
                        agent_id=agent_id,
                        timeout_seconds=time_since_heartbeat
                    )
                    dead_agents.append(agent_id)
        
        for agent_id in dead_agents:
            await self.deregister_agent(agent_id)
        
        if dead_agents:
            logger.info(f"Cleaned up {len(dead_agents)} dead agents")
    
    async def _monitoring_loop(self):
        """Monitor agent health"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.health_check_interval)
                stats = await self.get_statistics()
                logger.info("Agent registry status", **stats)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
