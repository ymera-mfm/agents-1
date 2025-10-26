"""
Agent Orchestrator
Coordinates communication with all agents in the platform
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from .database import ProjectDatabase

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Agent Orchestration System
    
    Features:
    - Agent registry and discovery
    - Health monitoring
    - Request routing
    - Circuit breaker pattern
    - Retry logic with exponential backoff
    """
    
    def __init__(self, settings, database: ProjectDatabase):
        self.settings = settings
        self.database = database
        self.is_initialized = False
        self.agents = {}
        self.circuit_breakers = {}
        self.http_client = None
        self.health_check_task = None
    
    async def initialize(self):
        """Initialize agent orchestrator"""
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.agent_request_timeout),
            limits=httpx.Limits(max_keepalive_connections=100)
        )
        
        # Register agents
        self._register_agents()
        
        self.is_initialized = True
        logger.info("✓ Agent orchestrator initialized")
    
    def _register_agents(self):
        """Register all agents from configuration"""
        self.agents = {
            "manager": {
                "url": self.settings.manager_agent_url,
                "capabilities": ["task_delegation", "workflow_management"],
                "priority": 1,
                "timeout": 30
            },
            "coding": {
                "url": self.settings.coding_agent_url,
                "capabilities": ["code_generation", "refactoring"],
                "priority": 2,
                "timeout": 60
            },
            "examination": {
                "url": self.settings.examination_agent_url,
                "capabilities": ["testing", "qa", "validation"],
                "priority": 3,
                "timeout": 90
            },
            "enhancement": {
                "url": self.settings.enhancement_agent_url,
                "capabilities": ["optimization", "refactoring"],
                "priority": 4,
                "timeout": 60
            }
        }
        
        # Initialize circuit breakers
        for agent_id in self.agents:
            self.circuit_breakers[agent_id] = {
                "failures": 0,
                "state": "closed",  # closed, open, half-open
                "last_failure": None
            }
    
    async def send_to_agent(
        self,
        agent_id: str,
        endpoint: str,
        data: Dict,
        method: str = "POST"
    ) -> Optional[Dict]:
        """
        Send request to agent with retry logic and circuit breaker
        
        Args:
            agent_id: Agent identifier
            endpoint: API endpoint path
            data: Request data
            method: HTTP method
        
        Returns:
            Response data or None if failed
        """
        if agent_id not in self.agents:
            logger.error(f"Unknown agent: {agent_id}")
            return None
        
        # Check circuit breaker
        if not self._check_circuit_breaker(agent_id):
            logger.warning(f"Circuit breaker open for agent {agent_id}")
            return None
        
        agent = self.agents[agent_id]
        url = f"{agent['url']}{endpoint}"
        
        # Retry logic with exponential backoff
        max_retries = self.settings.agent_max_retries
        backoff = 1
        
        for attempt in range(max_retries):
            try:
                if method == "POST":
                    response = await self.http_client.post(
                        url,
                        json=data,
                        timeout=agent["timeout"]
                    )
                elif method == "GET":
                    response = await self.http_client.get(
                        url,
                        params=data,
                        timeout=agent["timeout"]
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                
                # Reset circuit breaker on success
                self._reset_circuit_breaker(agent_id)
                
                return response.json()
                
            except httpx.HTTPError as e:
                logger.warning(
                    f"Request to {agent_id} failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                
                # Record failure
                self._record_failure(agent_id)
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for agent {agent_id}")
                    return None
        
        return None
    
    def _check_circuit_breaker(self, agent_id: str) -> bool:
        """Check if circuit breaker allows requests"""
        breaker = self.circuit_breakers[agent_id]
        
        if breaker["state"] == "closed":
            return True
        
        if breaker["state"] == "open":
            # Check if enough time has passed to try again
            if breaker["last_failure"]:
                time_since_failure = (
                    datetime.utcnow() - breaker["last_failure"]
                ).seconds
                
                if time_since_failure > 60:  # 60 seconds timeout
                    breaker["state"] = "half-open"
                    return True
            
            return False
        
        if breaker["state"] == "half-open":
            return True
        
        return False
    
    def _record_failure(self, agent_id: str):
        """Record agent failure for circuit breaker"""
        breaker = self.circuit_breakers[agent_id]
        breaker["failures"] += 1
        breaker["last_failure"] = datetime.utcnow()
        
        # Open circuit if threshold reached
        threshold = 5  # Open after 5 failures
        if breaker["failures"] >= threshold and breaker["state"] == "closed":
            breaker["state"] = "open"
            logger.warning(f"Circuit breaker opened for agent {agent_id}")
    
    def _reset_circuit_breaker(self, agent_id: str):
        """Reset circuit breaker on successful request"""
        breaker = self.circuit_breakers[agent_id]
        breaker["failures"] = 0
        breaker["state"] = "closed"
        breaker["last_failure"] = None
    
    async def check_agent_health(self, agent_id: str) -> Dict:
        """Check health of specific agent"""
        if agent_id not in self.agents:
            return {"status": "unknown", "error": "Agent not found"}
        
        agent = self.agents[agent_id]
        
        try:
            response = await self.http_client.get(
                f"{agent['url']}/health",
                timeout=5.0
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "agent_id": agent_id,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "status": "unhealthy",
                    "agent_id": agent_id,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "status": "unreachable",
                "agent_id": agent_id,
                "error": str(e)
            }
    
    async def list_agents(self) -> List[Dict]:
        """List all registered agents"""
        agents_list = []
        
        for agent_id, agent_info in self.agents.items():
            breaker = self.circuit_breakers[agent_id]
            
            agents_list.append({
                "id": agent_id,
                "url": agent_info["url"],
                "capabilities": agent_info["capabilities"],
                "priority": agent_info["priority"],
                "circuit_breaker_state": breaker["state"],
                "failures": breaker["failures"]
            })
        
        return agents_list
    
    async def start_health_monitoring(self):
        """Start background health monitoring"""
        logger.info("Agent health monitoring started")
        
        async def monitor():
            while True:
                try:
                    for agent_id in self.agents:
                        health = await self.check_agent_health(agent_id)
                        
                        if health["status"] != "healthy":
                            logger.warning(
                                f"Agent {agent_id} health check failed: {health}"
                            )
                    
                    await asyncio.sleep(30)  # Check every 30 seconds
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(60)
        
        self.health_check_task = asyncio.create_task(monitor())
    
    async def health_check(self) -> bool:
        """Check orchestrator health"""
        return self.is_initialized and self.http_client is not None
    
    async def shutdown(self):
        """Shutdown agent orchestrator"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.http_client:
            await self.http_client.aclose()
        
        logger.info("Agent orchestrator shutdown complete")

