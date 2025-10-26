"""
Resource Allocator - Dynamic resource management and allocation
Manages compute resources, quotas, and resource-aware scheduling
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import structlog

from .agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


class ResourceType(Enum):
    """Resource types"""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    STORAGE = "storage"
    NETWORK = "network"
    CUSTOM = "custom"


@dataclass
class ResourceQuota:
    """Resource quota definition"""
    cpu_cores: float = 0.0
    memory_mb: float = 0.0
    gpu_count: int = 0
    storage_gb: float = 0.0
    network_mbps: float = 0.0
    custom: Dict[str, float] = field(default_factory=dict)
    
    def __add__(self, other: 'ResourceQuota') -> 'ResourceQuota':
        """Add two quotas"""
        return ResourceQuota(
            cpu_cores=self.cpu_cores + other.cpu_cores,
            memory_mb=self.memory_mb + other.memory_mb,
            gpu_count=self.gpu_count + other.gpu_count,
            storage_gb=self.storage_gb + other.storage_gb,
            network_mbps=self.network_mbps + other.network_mbps,
            custom={**self.custom, **other.custom}
        )
    
    def __sub__(self, other: 'ResourceQuota') -> 'ResourceQuota':
        """Subtract two quotas"""
        return ResourceQuota(
            cpu_cores=self.cpu_cores - other.cpu_cores,
            memory_mb=self.memory_mb - other.memory_mb,
            gpu_count=self.gpu_count - other.gpu_count,
            storage_gb=self.storage_gb - other.storage_gb,
            network_mbps=self.network_mbps - other.network_mbps,
            custom={k: self.custom.get(k, 0) - other.custom.get(k, 0) for k in set(self.custom) | set(other.custom)}
        )
    
    def fits_within(self, limit: 'ResourceQuota') -> bool:
        """Check if this quota fits within a limit"""
        return (
            self.cpu_cores <= limit.cpu_cores and
            self.memory_mb <= limit.memory_mb and
            self.gpu_count <= limit.gpu_count and
            self.storage_gb <= limit.storage_gb and
            self.network_mbps <= limit.network_mbps
        )


@dataclass
class AgentResources:
    """Agent resource allocation"""
    agent_id: str
    total: ResourceQuota
    allocated: ResourceQuota = field(default_factory=ResourceQuota)
    reserved: ResourceQuota = field(default_factory=ResourceQuota)
    
    @property
    def available(self) -> ResourceQuota:
        """Calculate available resources"""
        return self.total - self.allocated - self.reserved
    
    @property
    def utilization_percent(self) -> float:
        """Calculate resource utilization percentage"""
        if self.total.cpu_cores == 0:
            return 0.0
        return (self.allocated.cpu_cores / self.total.cpu_cores) * 100


@dataclass
class ResourceAllocation:
    """Resource allocation record"""
    allocation_id: str
    agent_id: str
    task_id: str
    quota: ResourceQuota
    allocated_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None


class ResourceAllocator:
    """
    Resource Allocator
    
    Features:
    - Dynamic resource tracking
    - Quota management
    - Resource-aware scheduling
    - Automatic cleanup
    - Resource reservations
    - Multi-tenant support
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        cleanup_interval: int = 60
    ):
        self.registry = agent_registry
        self.cleanup_interval = cleanup_interval
        
        # Resource tracking
        self._agent_resources: Dict[str, AgentResources] = {}
        self._allocations: Dict[str, ResourceAllocation] = {}
        self._tenant_quotas: Dict[str, ResourceQuota] = {}
        self._tenant_usage: Dict[str, ResourceQuota] = {}
        
        # Locks
        self._lock = asyncio.Lock()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("Resource Allocator initialized")
    
    async def start(self):
        """Start resource allocator"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource Allocator started")
    
    async def stop(self):
        """Stop resource allocator"""
        self._shutdown_event.set()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            await asyncio.gather(self._cleanup_task, return_exceptions=True)
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            await asyncio.gather(self._monitoring_task, return_exceptions=True)
        
        logger.info("Resource Allocator stopped")
    
    # =========================================================================
    # AGENT RESOURCE MANAGEMENT
    # =========================================================================
    
    async def register_agent_resources(
        self,
        agent_id: str,
        resources: ResourceQuota
    ):
        """Register agent resource capacity"""
        async with self._lock:
            self._agent_resources[agent_id] = AgentResources(
                agent_id=agent_id,
                total=resources
            )
        
        logger.info(
            f"Agent resources registered",
            agent_id=agent_id,
            cpu_cores=resources.cpu_cores,
            memory_mb=resources.memory_mb
        )
    
    async def update_agent_resources(
        self,
        agent_id: str,
        resources: ResourceQuota
    ):
        """Update agent resource capacity"""
        async with self._lock:
            if agent_id in self._agent_resources:
                self._agent_resources[agent_id].total = resources
                logger.info(f"Agent resources updated", agent_id=agent_id)
            else:
                await self.register_agent_resources(agent_id, resources)
    
    async def deregister_agent_resources(self, agent_id: str):
        """Deregister agent resources"""
        async with self._lock:
            if agent_id in self._agent_resources:
                # Release all allocations for this agent
                to_remove = [
                    alloc_id for alloc_id, alloc in self._allocations.items()
                    if alloc.agent_id == agent_id
                ]
                for alloc_id in to_remove:
                    await self._release_allocation(alloc_id)
                
                del self._agent_resources[agent_id]
                logger.info(f"Agent resources deregistered", agent_id=agent_id)
    
    # =========================================================================
    # RESOURCE ALLOCATION
    # =========================================================================
    
    async def allocate_resources(
        self,
        task_id: str,
        required: ResourceQuota,
        tenant_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        preferred_agent: Optional[str] = None
    ) -> Optional[ResourceAllocation]:
        """
        Allocate resources for a task
        
        Args:
            task_id: Task ID
            required: Required resources
            tenant_id: Tenant ID for quota checking
            timeout_seconds: Allocation timeout
            preferred_agent: Preferred agent ID
            
        Returns:
            Resource allocation or None if cannot allocate
        """
        async with self._lock:
            # Check tenant quota
            if tenant_id:
                if not await self._check_tenant_quota(tenant_id, required):
                    logger.warning(
                        f"Tenant quota exceeded",
                        tenant_id=tenant_id,
                        required=required
                    )
                    return None
            
            # Find agent with available resources
            agent_id = await self._find_agent_with_resources(required, preferred_agent)
            
            if not agent_id:
                logger.warning(f"No agent with sufficient resources", required=required)
                return None
            
            # Create allocation
            allocation = ResourceAllocation(
                allocation_id=f"alloc_{task_id}",
                agent_id=agent_id,
                task_id=task_id,
                quota=required,
                expires_at=time.time() + timeout_seconds if timeout_seconds else None
            )
            
            # Update tracking
            self._allocations[allocation.allocation_id] = allocation
            self._agent_resources[agent_id].allocated = (
                self._agent_resources[agent_id].allocated + required
            )
            
            if tenant_id:
                if tenant_id not in self._tenant_usage:
                    self._tenant_usage[tenant_id] = ResourceQuota()
                self._tenant_usage[tenant_id] = self._tenant_usage[tenant_id] + required
            
            logger.info(
                f"Resources allocated",
                allocation_id=allocation.allocation_id,
                agent_id=agent_id,
                task_id=task_id
            )
            
            return allocation
    
    async def release_resources(self, allocation_id: str) -> bool:
        """Release allocated resources"""
        async with self._lock:
            return await self._release_allocation(allocation_id)
    
    async def _release_allocation(self, allocation_id: str) -> bool:
        """Internal release (assumes lock held)"""
        if allocation_id not in self._allocations:
            return False
        
        allocation = self._allocations[allocation_id]
        agent_id = allocation.agent_id
        
        # Update tracking
        if agent_id in self._agent_resources:
            self._agent_resources[agent_id].allocated = (
                self._agent_resources[agent_id].allocated - allocation.quota
            )
        
        del self._allocations[allocation_id]
        
        logger.info(
            f"Resources released",
            allocation_id=allocation_id,
            agent_id=agent_id
        )
        
        return True
    
    async def _find_agent_with_resources(
        self,
        required: ResourceQuota,
        preferred_agent: Optional[str] = None
    ) -> Optional[str]:
        """Find agent with sufficient resources"""
        # Try preferred agent first
        if preferred_agent and preferred_agent in self._agent_resources:
            agent_res = self._agent_resources[preferred_agent]
            if required.fits_within(agent_res.available):
                return preferred_agent
        
        # Find any agent with resources
        candidates = []
        for agent_id, agent_res in self._agent_resources.items():
            if required.fits_within(agent_res.available):
                candidates.append((agent_id, agent_res.utilization_percent))
        
        if not candidates:
            return None
        
        # Return least utilized agent
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    # =========================================================================
    # RESOURCE RESERVATION
    # =========================================================================
    
    async def reserve_resources(
        self,
        agent_id: str,
        quota: ResourceQuota,
        duration_seconds: int
    ) -> Optional[str]:
        """Reserve resources on an agent"""
        async with self._lock:
            if agent_id not in self._agent_resources:
                return None
            
            agent_res = self._agent_resources[agent_id]
            
            if not quota.fits_within(agent_res.available):
                return None
            
            # Create reservation
            reservation_id = f"reserve_{agent_id}_{int(time.time())}"
            agent_res.reserved = agent_res.reserved + quota
            
            # Schedule release
            asyncio.create_task(
                self._release_reservation_after(agent_id, quota, duration_seconds)
            )
            
            logger.info(
                f"Resources reserved",
                reservation_id=reservation_id,
                agent_id=agent_id,
                duration_seconds=duration_seconds
            )
            
            return reservation_id
    
    async def _release_reservation_after(
        self,
        agent_id: str,
        quota: ResourceQuota,
        delay_seconds: int
    ):
        """Release reservation after delay"""
        await asyncio.sleep(delay_seconds)
        
        async with self._lock:
            if agent_id in self._agent_resources:
                self._agent_resources[agent_id].reserved = (
                    self._agent_resources[agent_id].reserved - quota
                )
                logger.info(f"Reservation released", agent_id=agent_id)
    
    # =========================================================================
    # TENANT QUOTAS
    # =========================================================================
    
    async def set_tenant_quota(self, tenant_id: str, quota: ResourceQuota):
        """Set resource quota for tenant"""
        async with self._lock:
            self._tenant_quotas[tenant_id] = quota
        
        logger.info(f"Tenant quota set", tenant_id=tenant_id)
    
    async def get_tenant_usage(self, tenant_id: str) -> ResourceQuota:
        """Get current tenant resource usage"""
        return self._tenant_usage.get(tenant_id, ResourceQuota())
    
    async def _check_tenant_quota(
        self,
        tenant_id: str,
        required: ResourceQuota
    ) -> bool:
        """Check if tenant can allocate resources"""
        if tenant_id not in self._tenant_quotas:
            return True  # No quota set
        
        quota = self._tenant_quotas[tenant_id]
        current_usage = self._tenant_usage.get(tenant_id, ResourceQuota())
        new_usage = current_usage + required
        
        return new_usage.fits_within(quota)
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    async def get_agent_resources(self, agent_id: str) -> Optional[AgentResources]:
        """Get agent resource information"""
        return self._agent_resources.get(agent_id)
    
    async def get_allocation(self, allocation_id: str) -> Optional[ResourceAllocation]:
        """Get allocation information"""
        return self._allocations.get(allocation_id)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get resource allocator statistics"""
        total_resources = ResourceQuota()
        allocated_resources = ResourceQuota()
        
        for agent_res in self._agent_resources.values():
            total_resources = total_resources + agent_res.total
            allocated_resources = allocated_resources + agent_res.allocated
        
        return {
            'total_agents': len(self._agent_resources),
            'active_allocations': len(self._allocations),
            'total_cpu_cores': total_resources.cpu_cores,
            'allocated_cpu_cores': allocated_resources.cpu_cores,
            'total_memory_mb': total_resources.memory_mb,
            'allocated_memory_mb': allocated_resources.memory_mb,
            'cpu_utilization_percent': (
                (allocated_resources.cpu_cores / total_resources.cpu_cores * 100)
                if total_resources.cpu_cores > 0 else 0
            ),
            'memory_utilization_percent': (
                (allocated_resources.memory_mb / total_resources.memory_mb * 100)
                if total_resources.memory_mb > 0 else 0
            )
        }
    
    # =========================================================================
    # BACKGROUND TASKS
    # =========================================================================
    
    async def _cleanup_loop(self):
        """Cleanup expired allocations"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_allocations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired_allocations(self):
        """Remove expired allocations"""
        current_time = time.time()
        expired = []
        
        async with self._lock:
            for alloc_id, alloc in list(self._allocations.items()):
                if alloc.expires_at and current_time > alloc.expires_at:
                    expired.append(alloc_id)
        
        for alloc_id in expired:
            await self.release_resources(alloc_id)
            logger.warning(f"Allocation expired and released", allocation_id=alloc_id)
    
    async def _monitoring_loop(self):
        """Monitor resource usage"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30)
                stats = await self.get_statistics()
                logger.info("Resource allocator status", **stats)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
