"""
Production-Ready Intelligence Engine v2.1
Advanced orchestration with enterprise-grade resilience
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import numpy as np
from datetime import datetime, timedelta

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority, TaskResult


class DecisionStrategy(Enum):
    GREEDY = "greedy"
    WEIGHTED = "weighted"
    ML_BASED = "ml_based"
    CONSENSUS = "consensus"
    ADAPTIVE = "adaptive"


class SystemState(Enum):
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


@dataclass
class AgentCapability:
    agent_id: str
    capability: str
    confidence: float
    load_factor: float
    success_rate: float
    avg_response_time: float
    last_updated: float
    error_count: int = 0
    total_requests: int = 0


@dataclass
class DecisionContext:
    request_id: str
    task_type: str
    requirements: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.MEDIUM
    deadline: Optional[float] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0


@dataclass
class AgentRecommendation:
    agent_id: str
    confidence: float
    reasoning: str
    estimated_duration: float
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    alternative_agents: List[str] = field(default_factory=list)


class IntelligenceEngine(BaseAgent):
    """Enterprise-grade Intelligence Engine with production-ready routing"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Agent registry and capabilities
        self.agent_registry: Dict[str, Dict] = {}
        self.agent_capabilities: Dict[str, List[AgentCapability]] = defaultdict(list)
        self.agent_load: Dict[str, float] = defaultdict(float)
        self.agent_health: Dict[str, Dict] = {}
        
        # Routing decision making
        self.decision_strategy = DecisionStrategy.ADAPTIVE
        self.decision_history = deque(maxlen=10000)
        
        # System state
        self.system_state = SystemState.INITIALIZING
        self.system_metrics: Dict[str, float] = {}
        
        # Circuit breakers for fault tolerance
        self.circuit_breakers: Dict[str, Dict] = defaultdict(lambda: {
            'failures': 0,
            'last_failure': 0,
            'state': 'closed',
            'threshold': 5,
            'timeout': 60
        })
        
        # Performance tracking
        self.routing_stats = {
            'total_routes': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'avg_routing_time_ms': 0.0
        }
    
    async def _setup_subscriptions(self):
        """Setup NATS subscriptions"""
        await self._subscribe(
            "agent.register",
            self._handle_agent_registration,
            queue_group="intelligence-registration"
        )
        
        await self._subscribe(
            "agent.heartbeat",
            self._handle_agent_heartbeat,
            queue_group="intelligence-heartbeat"
        )
        
        await self._subscribe(
            "intelligence.task.route",
            self._handle_task_routing_request,
            queue_group="intelligence-routing"
        )
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        await super()._start_background_tasks()
        
        task = asyncio.create_task(self._system_monitor_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        task = asyncio.create_task(self._health_check_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        task = asyncio.create_task(self._circuit_breaker_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle intelligence engine tasks"""
        if task_request.task_type == "route_task":
            return await self._route_task_request(task_request.payload)
        elif task_request.task_type == "get_system_status":
            return await self._get_system_status()
        elif task_request.task_type == "get_agent_recommendations":
            return await self._get_agent_recommendations(task_request.payload)
        else:
            return {"error": f"Unknown task type: {task_request.task_type}"}
    
    async def _handle_agent_registration(self, msg):
        """Handle agent registration"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data['name']
            agent_info = data['info']
            
            self.agent_registry[agent_name] = agent_info
            self.agent_health[agent_name] = {
                'status': 'healthy',
                'last_seen': time.time(),
                'response_time': 0.0,
                'error_count': 0,
                'load': 0.0,
                'active_tasks': 0
            }
            
            # Register capabilities
            for capability in agent_info.get('capabilities', []):
                self._register_agent_capability(
                    agent_name,
                    capability,
                    agent_info.get('confidence', 0.8)
                )
            
            self.logger.info(f"Agent registered: {agent_name}")
            
            # Persist to database
            if self.db_pool:
                await self._db_execute(
                    """INSERT INTO agents (name, agent_type, status, capabilities, metadata)
                       VALUES ($1, $2, $3, $4, $5)
                       ON CONFLICT (name) DO UPDATE SET
                       agent_type = EXCLUDED.agent_type,
                       status = EXCLUDED.status,
                       capabilities = EXCLUDED.capabilities,
                       metadata = EXCLUDED.metadata,
                       updated_at = NOW()""",
                    agent_name,
                    agent_info.get('type'),
                    'healthy',
                    json.dumps(agent_info.get('capabilities', [])),
                    json.dumps(agent_info.get('metadata', {}))
                )
            
        except Exception as e:
            self.logger.error(f"Agent registration failed: {e}", exc_info=True)
        finally:
            await msg.ack()
    
    async def _handle_agent_heartbeat(self, msg):
        """Handle agent heartbeat"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data['agent_name']
            metrics = data.get('metrics', {})
            
            if agent_name in self.agent_health:
                self.agent_health[agent_name].update({
                    'status': data.get('status', 'healthy'),
                    'last_seen': time.time(),
                    'load': metrics.get('load', 0.0),
                    'active_tasks': metrics.get('active_tasks', 0),
                    'error_count': metrics.get('tasks_failed', 0)
                })
                
                self.agent_load[agent_name] = metrics.get('load', 0.0)
                
                # Update capabilities performance
                await self._update_capability_performance(agent_name, metrics)
        
        except Exception as e:
            self.logger.error(f"Heartbeat processing failed: {e}")
        finally:
            await msg.ack()
    
    async def _handle_task_routing_request(self, msg):
        """Handle task routing requests"""
        routing_start = time.time()
        
        try:
            data = json.loads(msg.data.decode())
            
            context = DecisionContext(
                request_id=data.get('request_id'),
                task_type=data['task_type'],
                requirements=data.get('requirements', {}),
                constraints=data.get('constraints', {}),
                priority=Priority(data.get('priority', 'medium')),
                deadline=data.get('deadline'),
                context_data=data.get('context', {})
            )
            
            # Route task
            recommendation = await self._route_task(context)
            
            # Update routing stats
            routing_time_ms = (time.time() - routing_start) * 1000
            self.routing_stats['total_routes'] += 1
            self.routing_stats['successful_routes'] += 1 if recommendation.confidence > 0.5 else 0
            
            # Publish result
            if msg.reply:
                await self._publish(msg.reply, recommendation.__dict__)
            
            self.logger.info(
                f"Task routed to {recommendation.agent_id}",
                confidence=recommendation.confidence
            )
            
        except Exception as e:
            self.logger.error(f"Task routing failed: {e}", exc_info=True)
            self.routing_stats['failed_routes'] += 1
        finally:
            await msg.ack()
    
    def _register_agent_capability(self, agent_id: str, capability: str, confidence: float = 0.8):
        """Register agent capability"""
        self.agent_capabilities[capability] = [
            cap for cap in self.agent_capabilities[capability]
            if cap.agent_id != agent_id
        ]
        
        self.agent_capabilities[capability].append(
            AgentCapability(
                agent_id=agent_id,
                capability=capability,
                confidence=confidence,
                load_factor=0.0,
                success_rate=1.0,
                avg_response_time=1.0,
                last_updated=time.time()
            )
        )
    
    async def _update_capability_performance(self, agent_id: str, metrics: Dict[str, Any]):
        """Update capability performance metrics"""
        try:
            tasks_completed = metrics.get('tasks_completed', 0)
            tasks_failed = metrics.get('tasks_failed', 0)
            avg_response_time = metrics.get('avg_processing_time_ms', 0.0) / 1000.0
            
            total_tasks = tasks_completed + tasks_failed
            success_rate = tasks_completed / total_tasks if total_tasks > 0 else 1.0
            
            for capability_list in self.agent_capabilities.values():
                for cap in capability_list:
                    if cap.agent_id == agent_id:
                        alpha = 0.3
                        cap.success_rate = alpha * success_rate + (1 - alpha) * cap.success_rate
                        cap.avg_response_time = alpha * avg_response_time + (1 - alpha) * cap.avg_response_time
                        cap.load_factor = metrics.get('load', 0.0)
                        cap.error_count = tasks_failed
                        cap.total_requests = total_tasks
                        cap.last_updated = time.time()
        
        except Exception as e:
            self.logger.warning(f"Failed to update capability performance: {e}")
    
    async def _route_task(self, context: DecisionContext) -> AgentRecommendation:
        """Intelligent task routing"""
        
        # Find capable agents
        capable_agents = self._find_capable_agents(context.task_type, context.requirements)
        
        if not capable_agents:
            self.logger.warning(f"No capable agents for {context.task_type}")
            return AgentRecommendation(
                agent_id="unknown",
                confidence=0.0,
                reasoning="No capable agents found",
                estimated_duration=0.0
            )
        
        # Filter by circuit breaker state
        available_agents = [
            agent for agent in capable_agents
            if self._check_circuit_breaker(agent)
        ]
        
        if not available_agents:
            available_agents = capable_agents
        
        # Route based on strategy
        if self.decision_strategy == DecisionStrategy.ADAPTIVE:
            return await self._adaptive_routing(available_agents, context)
        elif self.decision_strategy == DecisionStrategy.WEIGHTED:
            return await self._weighted_routing(available_agents, context)
        else:
            return await self._weighted_routing(available_agents, context)
    
    def _find_capable_agents(self, task_type: str, requirements: Dict[str, Any]) -> List[str]:
        """Find capable agents"""
        capable = set()
        
        if task_type in self.agent_capabilities:
            for cap in self.agent_capabilities[task_type]:
                if cap.agent_id in self.agent_registry:
                    health = self.agent_health.get(cap.agent_id, {})
                    if health.get('status') in ['healthy', 'degraded']:
                        capable.add(cap.agent_id)
        
        return list(capable)
    
    def _check_circuit_breaker(self, agent_id: str) -> bool:
        """Check circuit breaker state"""
        breaker = self.circuit_breakers[agent_id]
        
        if breaker['state'] == 'open':
            if time.time() - breaker['last_failure'] > breaker['timeout']:
                breaker['state'] = 'half_open'
                breaker['failures'] = 0
                return True
            return False
        
        return True
    
    async def _adaptive_routing(self, agents: List[str], context: DecisionContext) -> AgentRecommendation:
        """Adaptive routing strategy"""
        
        best_agent = None
        best_score = -1
        
        for agent_id in agents:
            score = await self._calculate_agent_score(agent_id, context)
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        if not best_agent:
            best_agent = agents[0]
            best_score = 0.5
        
        estimated_duration = await self._estimate_task_duration(best_agent, context)
        
        return AgentRecommendation(
            agent_id=best_agent,
            confidence=min(1.0, max(0.0, best_score)),
            reasoning=f"Selected based on load, success rate, and response time (score: {best_score:.2f})",
            estimated_duration=estimated_duration,
            alternative_agents=[a for a in agents if a != best_agent][:3]
        )
    
    async def _weighted_routing(self, agents: List[str], context: DecisionContext) -> AgentRecommendation:
        """Weighted routing strategy"""
        
        agent_weights = {}
        
        for agent_id in agents:
            weight = 1.0
            
            # Load factor
            load = self.agent_load.get(agent_id, 0.0)
            weight *= (1.0 - load) * 2.0
            
            # Success rate
            for cap in self.agent_capabilities.get(context.task_type, []):
                if cap.agent_id == agent_id:
                    weight *= cap.success_rate * 2.0
                    break
            
            # Priority
            if context.priority in [Priority.HIGH, Priority.CRITICAL]:
                weight *= 1.2
            
            agent_weights[agent_id] = weight
        
        if not agent_weights:
            best_agent = agents[0]
            confidence = 0.1
        else:
            best_agent = max(agent_weights, key=agent_weights.get)
            max_weight = max(agent_weights.values())
            confidence = min(0.95, agent_weights[best_agent] / max_weight if max_weight > 0 else 0.5)
        
        estimated_duration = await self._estimate_task_duration(best_agent, context)
        
        return AgentRecommendation(
            agent_id=best_agent,
            confidence=confidence,
            reasoning=f"Weighted routing: load={self.agent_load.get(best_agent, 0.0):.2f}",
            estimated_duration=estimated_duration,
            alternative_agents=[a for a in agents if a != best_agent][:3]
        )
    
    async def _calculate_agent_score(self, agent_id: str, context: DecisionContext) -> float:
        """Calculate agent score"""
        score = 0.0
        
        health = self.agent_health.get(agent_id, {})
        
        if health.get('status') == 'healthy':
            score += 0.3
            load = health.get('load', 0.0)
            score += (1.0 - load) * 0.2
        elif health.get('status') == 'degraded':
            score += 0.15
        else:
            return 0.0
        
        for cap in self.agent_capabilities.get(context.task_type, []):
            if cap.agent_id == agent_id:
                score += cap.confidence * 0.15
                score += cap.success_rate * 0.15
                score += (1.0 - min(1.0, cap.avg_response_time / 10.0)) * 0.1
                break
        
        return min(1.0, score)
    
    async def _estimate_task_duration(self, agent_id: str, context: DecisionContext) -> float:
        """Estimate task duration"""
        
        base_duration = 30.0
        
        for cap in self.agent_capabilities.get(context.task_type, []):
            if cap.agent_id == agent_id:
                base_duration = cap.avg_response_time
                break
        
        complexity = context.requirements.get('complexity', 'medium')
        multipliers = {'low': 0.7, 'medium': 1.0, 'high': 1.5, 'very_high': 2.0}
        base_duration *= multipliers.get(complexity, 1.0)
        
        load = self.agent_load.get(agent_id, 0.0)
        base_duration *= (1.0 + load * 0.5)
        
        return base_duration
    
    async def _system_monitor_loop(self):
        """Monitor system state"""
        self.logger.info("System monitor loop started")
        
        while not self.shutdown_event.is_set():
            try:
                healthy_agents = sum(
                    1 for h in self.agent_health.values()
                    if h.get('status') == 'healthy'
                )
                total_agents = len(self.agent_registry)
                
                if total_agents == 0:
                    self.system_state = SystemState.INITIALIZING
                elif healthy_agents / max(1, total_agents) < 0.5:
                    self.system_state = SystemState.CRITICAL
                elif healthy_agents / max(1, total_agents) < 0.75:
                    self.system_state = SystemState.DEGRADED
                else:
                    self.system_state = SystemState.HEALTHY
                
                # Publish system state
                await self._publish_to_stream(
                    "system.state.update",
                    {
                        "state": self.system_state.value,
                        "healthy_agents": healthy_agents,
                        "total_agents": total_agents,
                        "timestamp": time.time()
                    }
                )
                
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"System monitor error: {e}")
                await asyncio.sleep(10)
        
        self.logger.info("System monitor loop stopped")
    
    async def _health_check_loop(self):
        """Health check loop"""
        self.logger.info("Health check loop started")
        
        while not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                
                for agent_name, health_info in list(self.agent_health.items()):
                    if current_time - health_info.get('last_seen', 0) > 60:
                        self.logger.warning(f"Agent {agent_name} unresponsive")
                        health_info['status'] = 'degraded'
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(30)
        
        self.logger.info("Health check loop stopped")
    
    async def _circuit_breaker_loop(self):
        """Circuit breaker reset loop"""
        self.logger.info("Circuit breaker loop started")
        
        while not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                
                for agent_id, breaker in self.circuit_breakers.items():
                    if breaker['state'] == 'open':
                        if current_time - breaker['last_failure'] > breaker['timeout']:
                            breaker['state'] = 'half_open'
                            breaker['failures'] = 0
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Circuit breaker error: {e}")
                await asyncio.sleep(30)
        
        self.logger.info("Circuit breaker loop stopped")
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "system_state": self.system_state.value,
            "total_agents": len(self.agent_registry),
            "healthy_agents": sum(
                1 for h in self.agent_health.values()
                if h.get('status') == 'healthy'
            ),
            "routing_stats": self.routing_stats,
            "timestamp": time.time()
        }
    
    async def _get_agent_recommendations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent recommendations"""
        task_type = payload.get('task_type')
        
        context = DecisionContext(
            request_id="rec_" + str(time.time()),
            task_type=task_type,
            requirements=payload.get('requirements', {}),
            priority=Priority(payload.get('priority', 'medium'))
        )
        
        recommendation = await self._route_task(context)
        
        return {
            "status": "success",
            "recommendation": {
                'agent_id': recommendation.agent_id,
                'confidence': recommendation.confidence,
                'reasoning': recommendation.reasoning,
                'estimated_duration': recommendation.estimated_duration,
                'alternative_agents': recommendation.alternative_agents
            }
        }
    
    async def _route_task_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route task request"""
        context = DecisionContext(
            request_id=payload.get('request_id'),
            task_type=payload['task_type'],
            requirements=payload.get('requirements', {}),
            priority=Priority(payload.get('priority', 'medium'))
        )
        
        recommendation = await self._route_task(context)
        
        return {
            "agent_id": recommendation.agent_id,
            "confidence": recommendation.confidence,
            "reasoning": recommendation.reasoning,
            "estimated_duration": recommendation.estimated_duration
        }


if __name__ == "__main__":
    import os
    
    async def main():
        config = AgentConfig(
            agent_id="intelligence-engine-001",
            name="intelligence_engine",
            agent_type="intelligence",
            capabilities=[
                "agent_routing",
                "system_optimization",
                "anomaly_detection",
                "workflow_coordination"
            ],
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            max_concurrent_tasks=200
        )
        
        engine = IntelligenceEngine(config)
        
        if await engine.start():
            await engine.run_forever()
    
    asyncio.run(main())
