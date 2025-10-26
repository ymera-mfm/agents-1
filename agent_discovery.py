"""
Agent Discovery - Service discovery and routing
Provides intelligent agent selection and routing based on capabilities
"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import structlog

try:
    from agent_registry import AgentRegistry, AgentRecord
except ImportError:
    # Define stubs if not available
    AgentRegistry = None
    AgentRecord = None

logger = structlog.get_logger(__name__)


class DiscoveryStrategy(Enum):
    """Agent discovery strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"
    HEALTH_WEIGHTED = "health_weighted"
    FASTEST_RESPONSE = "fastest_response"


@dataclass
class DiscoveryRequest:
    """Agent discovery request"""
    capability: str
    strategy: DiscoveryStrategy = DiscoveryStrategy.LEAST_LOADED
    exclude_agents: Optional[Set[str]] = None
    min_health_score: float = 0.5
    prefer_version: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class AgentDiscovery:
    """
    Agent Discovery Service
    
    Features:
    - Multiple discovery strategies
    - Health-aware selection
    - Version-based routing
    - Tag-based filtering
    - Load balancing
    - Circuit breaker integration
    """
    
    def __init__(self, agent_registry: AgentRegistry):
        self.registry = agent_registry
        self._round_robin_index: Dict[str, int] = {}
        
        logger.info("Agent Discovery initialized")
    
    async def discover_agent(
        self,
        request: DiscoveryRequest
    ) -> Optional[AgentRecord]:
        """
        Discover best agent for request
        
        Args:
            request: Discovery request with criteria
            
        Returns:
            Selected agent record or None
        """
        # Get all agents with the capability
        agents = await self.registry.get_agents_by_capability(
            request.capability,
            only_available=True
        )
        
        if not agents:
            logger.warning(f"No agents found with capability: {request.capability}")
            return None
        
        # Apply filters
        agents = self._apply_filters(agents, request)
        
        if not agents:
            logger.warning(f"No agents match criteria for capability: {request.capability}")
            return None
        
        # Apply selection strategy
        selected = await self._apply_strategy(agents, request)
        
        if selected:
            logger.info(
                f"Agent discovered",
                agent_id=selected.agent_id,
                capability=request.capability,
                strategy=request.strategy.value
            )
        
        return selected
    
    async def discover_agents(
        self,
        request: DiscoveryRequest,
        count: int = 1
    ) -> List[AgentRecord]:
        """
        Discover multiple agents
        
        Args:
            request: Discovery request
            count: Number of agents to discover
            
        Returns:
            List of selected agents
        """
        agents = await self.registry.get_agents_by_capability(
            request.capability,
            only_available=True
        )
        
        agents = self._apply_filters(agents, request)
        
        if request.strategy == DiscoveryStrategy.ROUND_ROBIN:
            return self._round_robin_selection(agents, request.capability, count)
        elif request.strategy == DiscoveryStrategy.LEAST_LOADED:
            return agents[:count]  # Already sorted by load
        elif request.strategy == DiscoveryStrategy.HEALTH_WEIGHTED:
            return self._health_weighted_selection(agents, count)
        elif request.strategy == DiscoveryStrategy.FASTEST_RESPONSE:
            return self._fastest_response_selection(agents, count)
        else:
            import random
            return random.sample(agents, min(count, len(agents)))
    
    def _apply_filters(
        self,
        agents: List[AgentRecord],
        request: DiscoveryRequest
    ) -> List[AgentRecord]:
        """Apply filters to agent list"""
        filtered = agents
        
        # Exclude specific agents
        if request.exclude_agents:
            filtered = [a for a in filtered if a.agent_id not in request.exclude_agents]
        
        # Min health score
        filtered = [a for a in filtered if a.health_score >= request.min_health_score]
        
        # Prefer version
        if request.prefer_version:
            versioned = [a for a in filtered if a.version == request.prefer_version]
            if versioned:
                filtered = versioned
        
        # Tag matching
        if request.tags:
            filtered = [
                a for a in filtered
                if all(a.tags.get(k) == v for k, v in request.tags.items())
            ]
        
        return filtered
    
    async def _apply_strategy(
        self,
        agents: List[AgentRecord],
        request: DiscoveryRequest
    ) -> Optional[AgentRecord]:
        """Apply selection strategy"""
        if not agents:
            return None
        
        if request.strategy == DiscoveryStrategy.ROUND_ROBIN:
            return self._round_robin_selection(agents, request.capability, 1)[0]
        elif request.strategy == DiscoveryStrategy.LEAST_LOADED:
            return agents[0]  # Already sorted by load
        elif request.strategy == DiscoveryStrategy.HEALTH_WEIGHTED:
            return self._health_weighted_selection(agents, 1)[0]
        elif request.strategy == DiscoveryStrategy.FASTEST_RESPONSE:
            return self._fastest_response_selection(agents, 1)[0]
        else:
            import random
            return random.choice(agents)
    
    def _round_robin_selection(
        self,
        agents: List[AgentRecord],
        capability: str,
        count: int
    ) -> List[AgentRecord]:
        """Round-robin selection"""
        if not agents:
            return []
        
        if capability not in self._round_robin_index:
            self._round_robin_index[capability] = 0
        
        selected = []
        for _ in range(min(count, len(agents))):
            idx = self._round_robin_index[capability] % len(agents)
            selected.append(agents[idx])
            self._round_robin_index[capability] += 1
        
        return selected
    
    def _health_weighted_selection(
        self,
        agents: List[AgentRecord],
        count: int
    ) -> List[AgentRecord]:
        """Health-weighted selection"""
        if not agents:
            return []
        
        # Sort by health score descending, then by load ascending
        sorted_agents = sorted(
            agents,
            key=lambda a: (-a.health_score, a.current_load / a.max_load)
        )
        
        return sorted_agents[:count]
    
    def _fastest_response_selection(
        self,
        agents: List[AgentRecord],
        count: int
    ) -> List[AgentRecord]:
        """Fastest response time selection"""
        if not agents:
            return []
        
        # Sort by average response time
        sorted_agents = sorted(
            agents,
            key=lambda a: (a.average_response_time_ms, a.current_load / a.max_load)
        )
        
        return sorted_agents[:count]
    
    async def health_check_agent(self, agent_id: str) -> bool:
        """Check if specific agent is healthy"""
        agent = await self.registry.get_agent(agent_id)
        return agent is not None and agent.is_healthy
    
    async def get_agent_address(self, agent_id: str) -> Optional[str]:
        """Get agent network address"""
        agent = await self.registry.get_agent(agent_id)
        if agent:
            return f"http://{agent.host}:{agent.port}"
        return None
    
    async def get_available_capabilities(self) -> List[str]:
        """Get list of all available capabilities"""
        agents = await self.registry.get_all_agents(only_healthy=True)
        capabilities = set()
        for agent in agents:
            capabilities.update(agent.capabilities)
        return sorted(list(capabilities))
    
    async def get_agents_for_workflow(
        self,
        required_capabilities: List[str]
    ) -> Dict[str, Optional[AgentRecord]]:
        """
        Get agents for all required capabilities
        
        Args:
            required_capabilities: List of required capabilities
            
        Returns:
            Dict mapping capability to selected agent
        """
        result = {}
        
        for capability in required_capabilities:
            request = DiscoveryRequest(
                capability=capability,
                strategy=DiscoveryStrategy.LEAST_LOADED
            )
            agent = await self.discover_agent(request)
            result[capability] = agent
        
        return result
