"""
Central Intelligence Engine
Advanced orchestration, decision-making, and system optimization
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import hashlib
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref
from datetime import datetime, timedelta

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority
from opentelemetry import trace
from redis import asyncio as aioredis
import asyncpg

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

@dataclass
class SystemMetric:
    name: str
    value: float
    unit: str
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class DecisionContext:
    request_id: str
    task_type: str
    requirements: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.MEDIUM
    deadline: Optional[float] = None
    context_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentRecommendation:
    agent_id: str
    confidence: float
    reasoning: str
    estimated_duration: float
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

class IntelligenceEngine(BaseAgent):
    """
    Central Intelligence Engine that provides:
    - Intelligent agent selection and task routing
    - System-wide optimization and resource management
    - Predictive analytics and pattern recognition
    - Adaptive learning from system behavior
    - Real-time decision making with ML models
    - Cross-agent coordination and conflict resolution
    - Performance optimization and auto-scaling
    - Anomaly detection and self-healing
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Agent registry and capabilities
        self.agent_registry: Dict[str, Dict] = {}
        self.agent_capabilities: Dict[str, List[AgentCapability]] = defaultdict(list)
        self.agent_load: Dict[str, float] = defaultdict(float)
        self.agent_health: Dict[str, Dict] = {}
        
        # Decision engine
        self.decision_strategy = DecisionStrategy.ADAPTIVE
        self.decision_history = deque(maxlen=10000)
        self.decision_models = {}
        
        # System state management
        self.system_state = SystemState.INITIALIZING
        self.system_metrics: Dict[str, SystemMetric] = {}
        self.metric_history = deque(maxlen=50000)
        
        # Learning and optimization
        self.performance_patterns = {}
        self.optimization_rules = {}
        self.anomaly_detectors = {}
        
        # Task coordination
        self.active_workflows: Dict[str, Dict] = {}
        self.task_dependencies: Dict[str, List[str]] = defaultdict(list)
        self.resource_pools: Dict[str, Dict] = defaultdict(dict)
        
        # Predictive analytics
        self.prediction_models = {}
        self.pattern_cache = {}
        self.forecast_horizon = 3600  # 1 hour
        
        # Real-time optimization
        self.optimization_thread = None
        self.optimization_interval = 30  # seconds
        
        # Neural network for decision making (simplified)
        self.decision_network = None
        self._initialize_ml_components()
        
        # Thread pool for CPU-intensive operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
    async def start(self):
        """Start intelligence engine services"""
        # Subscribe to agent registrations
        await self._subscribe(
            "agent.register",
            self._handle_agent_registration
        )
        
        # Subscribe to agent heartbeats
        await self._subscribe(
            "agent.heartbeat",
            self._handle_agent_heartbeat
        )
        
        # Subscribe to task requests
        await self._subscribe(
            "intelligence.task.route",
            self._handle_task_routing
        )
        
        # Subscribe to system metrics
        await self._subscribe(
            "system.metrics",
            self._handle_system_metrics
        )
        
        # Subscribe to workflow requests
        await self._subscribe(
            "intelligence.workflow.execute",
            self._handle_workflow_execution
        )
        
        # Subscribe to optimization requests
        await self._subscribe(
            "intelligence.optimize",
            self._handle_optimization_request
        )
        
        # Start background services
        asyncio.create_task(self._system_monitor_loop())
        asyncio.create_task(self._optimization_loop())
        asyncio.create_task(self._learning_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._prediction_loop())
        
        # Initialize system state
        await self._initialize_system()
        
        self.logger.info("Intelligence Engine started")
    
    def _initialize_ml_components(self):
        """Initialize machine learning components"""
        try:
            # Simple neural network for decision making
            self.decision_network = {
                'weights': {
                    'input': np.random.randn(10, 8) * 0.1,
                    'hidden': np.random.randn(8, 5) * 0.1,
                    'output': np.random.randn(5, 1) * 0.1
                },
                'biases': {
                    'hidden': np.zeros(8),
                    'output': np.zeros(1)
                }
            }
            
            # Pattern recognition models
            self.pattern_recognition = {
                'load_patterns': {},
                'failure_patterns': {},
                'performance_patterns': {}
            }
            
            # Anomaly detection
            self.anomaly_thresholds = {
                'response_time': 5.0,  # seconds
                'error_rate': 0.05,    # 5%
                'load_factor': 0.9,    # 90%
                'memory_usage': 0.85   # 85%
            }
            
        except Exception as e:
            self.logger.warning(f"ML components initialization failed: {e}")
    
    async def _initialize_system(self):
        """Initialize system state and load configurations"""
        try:
            # Load agent registry from database
            if self.db_pool:
                agents_data = await self._db_query(
                    "SELECT id, name, agent_type, status, capabilities, config, metadata FROM agents WHERE status != $1",
                    "inactive"
                )
                
                for agent in agents_data:
                    agent_name = agent["name"]
                    self.agent_registry[agent_name] = {
                        'id': str(agent['id']),
                        'type': agent['agent_type'],
                        'status': agent['status'],
                        'capabilities': json.loads(agent['capabilities']) if agent['capabilities'] else [],
                        'config': json.loads(agent['config']) if agent['config'] else {},
                        'metadata': json.loads(agent['metadata']) if agent['metadata'] else {}
                    }
                    
                    # Initialize capabilities
                    for capability_name in self.agent_registry[agent_name]['capabilities']:
                        self.agent_capabilities[capability_name].append(
                            AgentCapability(
                                agent_id=agent_name,
                                capability=capability_name,
                                confidence=0.8,  # Default confidence
                                load_factor=0.0,
                                success_rate=1.0,
                                avg_response_time=1.0,
                                last_updated=time.time()
                            )
                        )
            
            # Load optimization rules (if any, from OptimizingEngine's perspective)
            # This engine doesn't directly manage optimization rules, but might consume them
            
            # Initialize predictive models
            await self._initialize_predictive_models()
            
            self.system_state = SystemState.HEALTHY
            self.logger.info("System initialization completed")
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            self.system_state = SystemState.CRITICAL
    
    async def _handle_agent_registration(self, msg):
        """Handle new agent registration"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data['name']
            agent_info = data['info']
            
            # Persist agent registration to DB
            await self._db_query(
                """INSERT INTO agents (name, agent_type, status, capabilities, config, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT (name) DO UPDATE SET
                   agent_type = EXCLUDED.agent_type, status = EXCLUDED.status, capabilities = EXCLUDED.capabilities,
                   config = EXCLUDED.config, metadata = EXCLUDED.metadata, updated_at = NOW()""",
                agent_name, agent_info.get('type'), agent_info.get('status', 'healthy'),
                json.dumps(agent_info.get('capabilities', [])), json.dumps(agent_info.get('config', {})),
                json.dumps(agent_info.get('metadata', {}))
            )

            self.agent_registry[agent_name] = agent_info
            self.agent_health[agent_name] = {
                'status': 'healthy',
                'last_seen': time.time(),
                'response_time': 0.0,
                'error_count': 0
            }
            
            # Register capabilities
            for capability in agent_info.get('capabilities', []):
                # Remove old capability entry for this agent if exists
                self.agent_capabilities[capability] = [cap for cap in self.agent_capabilities[capability] if cap.agent_id != agent_name]
                self.agent_capabilities[capability].append(
                    AgentCapability(
                        agent_id=agent_name,
                        capability=capability,
                        confidence=agent_info.get('confidence', 0.8),
                        load_factor=0.0,
                        success_rate=1.0,
                        avg_response_time=1.0,
                        last_updated=time.time()
                    )
                )
            
            self.logger.info(f"Agent registered: {agent_name}", 
                           agent_type=agent_info.get('type'),
                           capabilities=len(agent_info.get('capabilities', [])))
            
            # Trigger system rebalancing
            await self._trigger_optimization("agent_registration")
            
        except Exception as e:
            self.logger.error(f"Agent registration failed: {e}")
        finally:
            await msg.ack()
    
    async def _handle_agent_heartbeat(self, msg):
        """Handle agent heartbeat messages"""
        try:
            data = json.loads(msg.data.decode())
            agent_name = data['agent_name']
            metrics = data.get('metrics', {})
            
            # Update agent health
            if agent_name in self.agent_health:
                self.agent_health[agent_name].update({
                    'status': data.get('status', 'healthy'),
                    'last_seen': time.time(),
                    'load': metrics.get('load', 0.0),
                    'memory_usage': metrics.get('memory_usage', 0.0),
                    'active_tasks': metrics.get('active_tasks', 0),
                    'queue_size': metrics.get('queue_size', 0)
                })
                
                # Update load tracking
                self.agent_load[agent_name] = metrics.get('load', 0.0)
                
                # Update capabilities performance
                await self._update_capability_performance(agent_name, metrics)

                # Persist agent health/status to DB
                await self._db_query(
                    "UPDATE agents SET status = $1, last_seen = $2, metadata = jsonb_set(metadata, '{health_metrics}', $3) WHERE name = $4",
                    data.get('status', 'healthy'), datetime.fromtimestamp(time.time()), json.dumps(metrics), agent_name
                )
            
        except Exception as e:
            self.logger.error(f"Heartbeat processing failed: {e}")
        finally:
            await msg.ack()
    
    async def _handle_task_routing(self, msg):
        """Handle intelligent task routing requests"""
        try:
            data = json.loads(msg.data.decode())
            
            decision_context = DecisionContext(
                request_id=data['request_id'],
                task_type=data['task_type'],
                requirements=data.get('requirements', {}),
                constraints=data.get('constraints', {}),
                priority=Priority(data.get('priority', 'medium')),
                deadline=data.get('deadline'),
                context_data=data.get('context', {})
            )
            
            with self.tracer.start_as_current_span("task_routing") as span:
                span.set_attribute("task_type", decision_context.task_type)
                span.set_attribute("priority", decision_context.priority.value)
                
                # Find best agent for the task
                recommendation = await self._route_task(decision_context)
                
                # Send routing decision
                await self._publish(f"task.{decision_context.request_id}.route", json.dumps({
                    "agent_id": recommendation.agent_id,
                    "confidence": recommendation.confidence,
                    "reasoning": recommendation.reasoning,
                    "estimated_duration": recommendation.estimated_duration,
                    "resource_requirements": recommendation.resource_requirements
                }).encode())
                
                # Record decision for learning
                await self._record_decision(decision_context, recommendation)
                
        except Exception as e:
            self.logger.error(f"Task routing failed: {e}")
        finally:
            await msg.ack()
    
    async def _route_task(self, context: DecisionContext) -> AgentRecommendation:
        """Intelligent task routing using multiple strategies"""
        
        # Get capable agents
        capable_agents = self._find_capable_agents(context.task_type, context.requirements)
        
        if not capable_agents:
            # Fallback to a default agent or raise an error
            self.logger.warning(f"No agents found capable of handling task type: {context.task_type}. Falling back to default.")
            return AgentRecommendation(
                agent_id="default_agent", # A default agent should be defined or handled upstream
                confidence=0.1,
                reasoning=f"No capable agents found for {context.task_type}",
                estimated_duration=60.0,
                resource_requirements={}
            )
        
        # Apply routing strategy
        if self.decision_strategy == DecisionStrategy.ADAPTIVE:
            return await self._adaptive_routing(capable_agents, context)
        elif self.decision_strategy == DecisionStrategy.ML_BASED:
            return await self._ml_based_routing(capable_agents, context)
        elif self.decision_strategy == DecisionStrategy.CONSENSUS:
            return await self._consensus_routing(capable_agents, context)
        else:
            return await self._weighted_routing(capable_agents, context)
    
    def _find_capable_agents(self, task_type: str, requirements: Dict[str, Any]) -> List[str]:
        """Find agents capable of handling the task"""
        capable_agents = []
        
        # Direct capability match
        if task_type in self.agent_capabilities:
            for capability in self.agent_capabilities[task_type]:
                if (capability.agent_id in self.agent_registry and 
                    self.agent_health.get(capability.agent_id, {}).get('status') == 'healthy'):
                    capable_agents.append(capability.agent_id)
        
        # Check for agents with compatible capabilities
        for agent_name, agent_info in self.agent_registry.items():
            if agent_name not in capable_agents:
                agent_capabilities = agent_info.get('capabilities', [])
                
                # Check if agent has required capabilities
                required_caps = requirements.get('required_capabilities', [])
                if all(cap in agent_capabilities for cap in required_caps):
                    if self.agent_health.get(agent_name, {}).get('status') == 'healthy':
                        capable_agents.append(agent_name)
        
        return list(set(capable_agents)) # Remove duplicates
    
    async def _adaptive_routing(self, agents: List[str], context: DecisionContext) -> AgentRecommendation:
        """Adaptive routing that learns from past performance"""
        
        best_agent = None
        best_score = -1
        best_reasoning = ""
        
        for agent_id in agents:
            score = await self._calculate_agent_score(agent_id, context)
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
                best_reasoning = self._generate_routing_reasoning(agent_id, score, context)
        
        if not best_agent:
            best_agent = agents[0]  # Fallback
            best_score = 0.5
            best_reasoning = "Fallback to first available agent."
        
        estimated_duration = await self._estimate_task_duration(best_agent, context)
        resource_requirements = await self._estimate_resource_requirements(best_agent, context)

        return AgentRecommendation(
            agent_id=best_agent,
            confidence=min(1.0, max(0.0, best_score)), # Ensure confidence is between 0 and 1
            reasoning=best_reasoning,
            estimated_duration=estimated_duration,
            resource_requirements=resource_requirements
        )
    
    async def _calculate_agent_score(self, agent_id: str, context: DecisionContext) -> float:
        """Calculate a score for an agent based on various factors"""
        score = 0.0
        
        # Factor 1: Agent Health and Load
        agent_health = self.agent_health.get(agent_id, {})
        if agent_health.get('status') == 'healthy':
            score += 0.3 # Base score for healthy agent
            load = agent_health.get('load', 0.0)
            score += (1.0 - load) * 0.2 # Lower load is better
            queue_size = agent_health.get('queue_size', 0)
            if queue_size < 5: # Prefer agents with smaller queues
                score += 0.1
        else:
            return 0.0 # Unhealthy agents get 0 score
        
        # Factor 2: Capability Match and Performance
        for cap in self.agent_capabilities.get(context.task_type, []):
            if cap.agent_id == agent_id:
                score += cap.confidence * 0.2 # Higher confidence is better
                score += cap.success_rate * 0.2 # Higher success rate is better
                # Inverse of avg_response_time (faster is better)
                score += (1.0 - min(1.0, cap.avg_response_time / 10.0)) * 0.1 # Normalize response time
                break

        # Factor 3: Historical Performance (from DB)
        historical_success_rate = await self._get_historical_performance(agent_id, context.task_type)
        score += historical_success_rate * 0.1

        # Apply contextual modifiers
        score = await self._apply_contextual_modifiers(score, agent_id, context)
        
        return score
    
    async def _apply_contextual_modifiers(self, base_score: float, agent_id: str, context: DecisionContext) -> float:
        """Apply contextual modifiers to agent score"""
        
        modified_score = base_score
        
        # Deadline pressure modifier
        if context.deadline:
            time_remaining = context.deadline - time.time()
            if time_remaining < 300:  # Less than 5 minutes
                # Prefer faster agents under time pressure
                agent_speed = await self._get_agent_speed_factor(agent_id, context.task_type)
                modified_score *= (1.0 + agent_speed * 0.2)
        
        # Resource availability modifier
        agent_health = self.agent_health.get(agent_id, {})
        memory_usage = agent_health.get('memory_usage', 0.0)
        if memory_usage > 0.8:  # High memory usage
            modified_score *= 0.8
        
        # Historical performance modifier
        historical_performance = await self._get_historical_performance(agent_id, context.task_type)
        if historical_performance > 0.9:
            modified_score *= 1.1
        elif historical_performance < 0.7:
            modified_score *= 0.9
        
        return min(1.0, modified_score)
    
    async def _ml_based_routing(self, agents: List[str], context: DecisionContext) -> AgentRecommendation:
        """Machine learning based routing using neural network"""
        
        if not self.decision_network:
            return await self._weighted_routing(agents, context)
        
        best_agent = None
        best_confidence = 0.0
        
        for agent_id in agents:
            # Prepare input features
            features = await self._extract_routing_features(agent_id, context)
            
            # Run through neural network
            confidence = self._predict_agent_suitability(features)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_agent = agent_id
        
        if not best_agent:
            best_agent = agents[0]
            best_confidence = 0.5
        
        estimated_duration = await self._estimate_task_duration(best_agent, context)
        resource_requirements = await self._estimate_resource_requirements(best_agent, context)

        return AgentRecommendation(
            agent_id=best_agent,
            confidence=best_confidence,
            reasoning=f"ML model prediction with {best_confidence:.2f} confidence",
            estimated_duration=estimated_duration,
            resource_requirements=resource_requirements
        )
    
    def _predict_agent_suitability(self, features: np.ndarray) -> float:
        """Use neural network to predict agent suitability"""
        try:
            # Simple feedforward network
            weights = self.decision_network['weights']
            biases = self.decision_network['biases']
            
            # Hidden layer
            hidden = np.tanh(np.dot(features, weights['input']) + biases['hidden'])
            
            # Output layer
            output = np.sigmoid(np.dot(hidden, weights['hidden']) + biases['output'])
            
            return float(output[0])
            
        except Exception as e:
            self.logger.warning(f"ML prediction failed: {e}")
            return 0.5
    
    async def _extract_routing_features(self, agent_id: str, context: DecisionContext) -> np.ndarray:
        """Extract features for ML routing decision"""
        features = np.zeros(10)
        
        try:
            # Feature 0: Agent load
            features[0] = self.agent_load.get(agent_id, 0.0)
            
            # Feature 1: Success rate
            if context.task_type in self.agent_capabilities:
                for cap in self.agent_capabilities[context.task_type]:
                    if cap.agent_id == agent_id:
                        features[1] = cap.success_rate
                        break
            
            # Feature 2: Response time (normalized)
            if context.task_type in self.agent_capabilities:
                for cap in self.agent_capabilities[context.task_type]:
                    if cap.agent_id == agent_id:
                        features[2] = min(1.0, cap.avg_response_time / 10.0)
                        break
            
            # Feature 3: Priority (encoded)
            priority_map = {Priority.LOW: 0.2, Priority.MEDIUM: 0.5, Priority.HIGH: 0.8, Priority.CRITICAL: 1.0}
            features[3] = priority_map.get(context.priority, 0.5)
            
            # Feature 4: Time pressure
            if context.deadline:
                time_remaining = max(0, context.deadline - time.time())
                features[4] = min(1.0, time_remaining / 3600)  # Normalize to hours
            
            # Feature 5: Agent health
            agent_health = self.agent_health.get(agent_id, {})
            if agent_health.get('status') == 'healthy':
                features[5] = 1.0
            else:
                features[5] = 0.0
            
            # Feature 6: Memory usage
            features[6] = agent_health.get('memory_usage', 0.0)
            
            # Feature 7: Queue size
            features[7] = min(1.0, agent_health.get('queue_size', 0) / 10.0)
            
            # Feature 8: Historical performance
            features[8] = await self._get_historical_performance(agent_id, context.task_type)
            
            # Feature 9: Capability confidence
            if context.task_type in self.agent_capabilities:
                for cap in self.agent_capabilities[context.task_type]:
                    if cap.agent_id == agent_id:
                        features[9] = cap.confidence
                        break
            
        except Exception as e:
            self.logger.warning(f"Feature extraction failed: {e}")
        
        return features
    
    async def _weighted_routing(self, agents: List[str], context: DecisionContext) -> AgentRecommendation:
        """Weighted routing based on multiple factors"""
        agent_weights = {}
        
        for agent_id in agents:
            weight = 1.0
            
            # Load factor weight (lower load = higher weight)
            load = self.agent_load.get(agent_id, 0.0)
            weight *= (1.0 - load) * 2
            
            # Success rate weight
            if context.task_type in self.agent_capabilities:
                for cap in self.agent_capabilities[context.task_type]:
                    if cap.agent_id == agent_id:
                        weight *= cap.success_rate * 2
                        break
            
            # Priority weight
            if context.priority == Priority.CRITICAL:
                weight *= 1.5
            elif context.priority == Priority.HIGH:
                weight *= 1.2
            
            agent_weights[agent_id] = weight
        
        # Select agent with highest weight
        if not agent_weights:
            best_agent = agents[0]
            confidence = 0.1
        else:
            best_agent = max(agent_weights, key=agent_weights.get)
            confidence = min(0.95, agent_weights[best_agent] / max(agent_weights.values()))
        
        estimated_duration = await self._estimate_task_duration(best_agent, context)
        resource_requirements = await self._estimate_resource_requirements(best_agent, context)

        return AgentRecommendation(
            agent_id=best_agent,
            confidence=confidence,
            reasoning=f"Weighted selection based on load ({self.agent_load.get(best_agent, 0.0):.2f}) and performance",
            estimated_duration=estimated_duration,
            resource_requirements=resource_requirements
        )
    
    async def _consensus_routing(self, agents: List[str], context: DecisionContext) -> AgentRecommendation:
        """Consensus-based routing using multiple strategies"""
        
        # Get recommendations from different strategies
        adaptive_rec = await self._adaptive_routing(agents, context)
        ml_rec = await self._ml_based_routing(agents, context)
        weighted_rec = await self._weighted_routing(agents, context)
        
        recommendations = [adaptive_rec, ml_rec, weighted_rec]
        
        # Count votes for each agent
        votes = defaultdict(list)
        for rec in recommendations:
            votes[rec.agent_id].append(rec)
        
        # Select agent with most votes, or highest confidence if tie
        best_agent = None
        best_score = -1
        
        for agent_id, recs in votes.items():
            score = len(recs) + sum(rec.confidence for rec in recs) / len(recs)
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        if not best_agent:
            best_agent = recommendations[0].agent_id
        
        # Calculate consensus confidence
        consensus_confidence = best_score / (len(recommendations) + 1)
        
        estimated_duration = await self._estimate_task_duration(best_agent, context)
        resource_requirements = await self._estimate_resource_requirements(best_agent, context)

        return AgentRecommendation(
            agent_id=best_agent,
            confidence=min(0.95, consensus_confidence),
            reasoning=f"Consensus selection from {len(recommendations)} strategies",
            estimated_duration=estimated_duration,
            resource_requirements=resource_requirements
        )
    
    def _generate_routing_reasoning(self, agent_id: str, score: float, context: DecisionContext) -> str:
        """Generate human-readable reasoning for routing decision"""
        reasons = []
        
        # Load factor
        load = self.agent_load.get(agent_id, 0.0)
        if load < 0.3:
            reasons.append("low load")
        elif load > 0.8:
            reasons.append("high load (but best available)")
        
        # Capability match
        if context.task_type in self.agent_capabilities:
            for cap in self.agent_capabilities[context.task_type]:
                if cap.agent_id == agent_id:
                    if cap.confidence > 0.8:
                        reasons.append("high capability confidence")
                    if cap.success_rate > 0.9:
                        reasons.append("excellent success rate")
                    break
        
        # Priority consideration
        if context.priority in [Priority.HIGH, Priority.CRITICAL]:
            reasons.append("priority task requirements")
        
        # Health status
        health = self.agent_health.get(agent_id, {})
        if health.get('status') == 'healthy' and health.get('memory_usage', 0) < 0.7:
            reasons.append("healthy status")
        
        reasoning = f"Selected based on: {', '.join(reasons)} (score: {score:.2f})"
        return reasoning
    
    async def _estimate_task_duration(self, agent_id: str, context: DecisionContext) -> float:
        """Estimate task duration based on historical data"""
        
        base_duration = 30.0  # Default 30 seconds
        
        # Get historical average for this task type
        for cap in self.agent_capabilities.get(context.task_type, []):
            if cap.agent_id == agent_id:
                base_duration = cap.avg_response_time
                break
        
        # Apply complexity modifier
        complexity = context.requirements.get('complexity', 'medium')
        complexity_multiplier = {'low': 0.7, 'medium': 1.0, 'high': 1.5, 'very_high': 2.0}
        base_duration *= complexity_multiplier.get(complexity, 1.0)
        
        # Apply load factor
        load = self.agent_load.get(agent_id, 0.0)
        base_duration *= (1.0 + load * 0.5)  # Higher load = longer duration
        
        return base_duration
    
    async def _estimate_resource_requirements(self, agent_id: str, context: DecisionContext) -> Dict[str, Any]:
        """Estimate resource requirements for task"""
        
        base_memory = 100  # MB
        base_cpu = 0.1     # CPU cores
        
        # Task type modifiers
        task_multipliers = {
            'llm_inference': {'memory': 2.0, 'cpu': 1.5},
            'validation': {'memory': 1.2, 'cpu': 0.8},
            'optimization': {'memory': 1.5, 'cpu': 2.0},
            'analysis': {'memory': 1.8, 'cpu': 1.2}
        }
        
        multipliers = task_multipliers.get(context.task_type, {'memory': 1.0, 'cpu': 1.0})
        
        return {
            'memory_mb': base_memory * multipliers['memory'],
            'cpu_cores': base_cpu * multipliers['cpu'],
            'estimated_duration_seconds': await self._estimate_task_duration(agent_id, context),
            'network_io': context.requirements.get('network_intensive', False),
            'disk_io': context.requirements.get('disk_intensive', False)
        }
    
    async def _get_historical_performance(self, agent_id: str, task_type: str) -> float:
        """Get historical performance metrics for agent and task type"""
        
        if not self.db_pool:
            return 0.8  # Default
        
        try:
            result = await self._db_query(
                """SELECT 
                    AVG(CASE WHEN tr.error_message IS NULL THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(tr.execution_time_ms) as avg_time
                FROM task_results tr
                JOIN tasks t ON tr.task_id = t.id
                JOIN agents a ON tr.agent_id = a.id
                WHERE a.name = $1 AND t.task_type = $2
                AND tr.created_at > NOW() - INTERVAL '7 days'""",
                agent_id, task_type, fetch_one=True
            )
                
            if result and result['success_rate'] is not None:
                return float(result['success_rate'])
        
        except Exception as e:
            self.logger.warning(f"Historical performance query failed: {e}")
        
        return 0.8
    
    async def _get_agent_speed_factor(self, agent_id: str, task_type: str) -> float:
        """Get agent speed factor for task type"""
        
        for cap in self.agent_capabilities.get(task_type, []):
            if cap.agent_id == agent_id:
                # Convert response time to speed factor (inverse relationship)
                return max(0.1, 1.0 / (cap.avg_response_time + 0.1))
        
        return 0.5  # Default speed factor
    
    async def _record_decision(self, context: DecisionContext, recommendation: AgentRecommendation):
        """Record decision for learning and analysis and persist to DB"""
        
        decision_record = {
            'timestamp': time.time(),
            'request_id': context.request_id,
            'task_type': context.task_type,
            'selected_agent': recommendation.agent_id,
            'confidence': recommendation.confidence,
            'reasoning': recommendation.reasoning,
            'context': {
                'priority': context.priority.value,
                'requirements': context.requirements,
                'constraints': context.constraints
            },
            'system_state': {
                'agent_loads': dict(self.agent_load),
                'system_state': self.system_state.value
            }
        }
        
        self.decision_history.append(decision_record)

        if self.db_pool:
            try:
                await self._db_query(
                    """INSERT INTO decision_history (request_id, task_type, selected_agent, confidence, reasoning, context_data, system_state, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                    decision_record['request_id'], decision_record['task_type'], decision_record['selected_agent'],
                    decision_record['confidence'], decision_record['reasoning'],
                    json.dumps(decision_record['context']), json.dumps(decision_record['system_state']),
                    datetime.fromtimestamp(decision_record['timestamp'])
                )
            except Exception as e:
                self.logger.error(f"Failed to persist decision record: {e}", decision_record=decision_record)
    
    async def _handle_system_metrics(self, msg):
        """Handle system metrics updates"""
        try:
            data = json.loads(msg.data.decode())
            
            for metric_data in data.get('metrics', []):
                metric = SystemMetric(
                    name=metric_data['name'],
                    value=metric_data['value'],
                    unit=metric_data.get('unit', ''),
                    timestamp=metric_data.get('timestamp', time.time()),
                    tags=metric_data.get('tags', {})
                )
                
                self.system_metrics[metric.name] = metric
                self.metric_history.append(metric)
                
                # Check for anomalies
                await self._check_metric_anomaly(metric)
        
        except Exception as e:
            self.logger.error(f"Metrics processing failed: {e}")
        finally:
            await msg.ack()
    
    async def _check_metric_anomaly(self, metric: SystemMetric):
        """Check if metric indicates an anomaly"""
        
        threshold = self.anomaly_thresholds.get(metric.name)
        if threshold and metric.value > threshold:
            # Trigger anomaly alert
            self.logger.warning(f"Anomaly detected for metric {metric.name}: {metric.value} > {threshold}")
            await self._publish_to_stream("alerts.anomaly", {
                "metric_name": metric.name,
                "value": metric.value,
                "threshold": threshold,
                "timestamp": metric.timestamp,
                "severity": "high"
            })

    async def _handle_workflow_execution(self, msg):
        """Handle requests to execute complex workflows"""
        try:
            data = json.loads(msg.data.decode())
            workflow_id = data['workflow_id']
            workflow_definition = data['definition']
            
            self.logger.info(f"Executing workflow: {workflow_id}")
            
            # This is a placeholder for a more sophisticated workflow engine
            # For now, it will simply log the workflow and acknowledge.
            self.active_workflows[workflow_id] = {
                "status": "running",
                "definition": workflow_definition,
                "started_at": time.time()
            }
            
            await self._publish_to_stream(f"workflow.{workflow_id}.status", {"status": "started"})
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
        finally:
            await msg.ack()

    async def _handle_optimization_request(self, msg):
        """Handle requests for system optimization"""
        try:
            data = json.loads(msg.data.decode())
            optimization_type = data.get("type", "system_wide")
            
            self.logger.info(f"Received optimization request: {optimization_type}")
            
            # Delegate to OptimizingEngine via NATS
            response = await self._request("optimizing_engine.task", json.dumps({
                "task_type": "optimize_performance",
                "payload": {"service": "all", "level": "standard"}
            }).encode(), timeout=60)

            if response:
                optimization_result = json.loads(response.data.decode())
                self.logger.info("Optimization request completed", result=optimization_result)
                await self._publish_to_stream(msg.reply, json.dumps(optimization_result).encode())
            else:
                self.logger.error("Optimization request timed out or failed.")
                await self._publish_to_stream(msg.reply, json.dumps({"error": "Optimization request failed or timed out"}).encode())

        except Exception as e:
            self.logger.error(f"Handling optimization request failed: {e}")
            if msg.reply:
                await self._publish_to_stream(msg.reply, json.dumps({"error": str(e)}).encode())
        finally:
            await msg.ack()

    async def _system_monitor_loop(self):
        """Periodically monitor system state and update overall health"""
        while not self._shutdown_event.is_set():
            try:
                # Aggregate agent health
                healthy_agents = sum(1 for a in self.agent_health.values() if a.get('status') == 'healthy')
                total_agents = len(self.agent_registry)

                if total_agents == 0:
                    self.system_state = SystemState.INITIALIZING
                elif healthy_agents / total_agents < 0.75:
                    self.system_state = SystemState.DEGRADED
                else:
                    self.system_state = SystemState.HEALTHY

                self.logger.debug(f"System state: {self.system_state.value}, Healthy agents: {healthy_agents}/{total_agents}")
                await self._publish_to_stream("system.state.update", {"state": self.system_state.value, "healthy_agents": healthy_agents, "total_agents": total_agents})

                # Publish aggregated metrics
                await self._publish_to_stream("system.metrics.aggregated", self._aggregate_system_metrics())

            except Exception as e:
                self.logger.error(f"System monitor loop failed: {e}")
            await asyncio.sleep(10) # Check every 10 seconds

    def _aggregate_system_metrics(self) -> Dict[str, Any]:
        """Aggregate system-wide metrics for reporting"""
        aggregated = {
            "timestamp": time.time(),
            "total_agents": len(self.agent_registry),
            "healthy_agents": sum(1 for a in self.agent_health.values() if a.get('status') == 'healthy'),
            "total_load": sum(self.agent_load.values()),
            "avg_memory_usage": np.mean([a.get('memory_usage', 0) for a in self.agent_health.values()]) if self.agent_health else 0,
            "avg_queue_size": np.mean([a.get('queue_size', 0) for a in self.agent_health.values()]) if self.agent_health else 0,
            "system_state": self.system_state.value
        }
        return aggregated

    async def _optimization_loop(self):
        """Periodically trigger system-wide optimization via OptimizingEngine"""
        while not self._shutdown_event.is_set():
            try:
                # Trigger optimization only if system is not critical
                if self.system_state not in [SystemState.CRITICAL, SystemState.EMERGENCY]:
                    self.logger.info("Triggering periodic system optimization.")
                    # Send a request to the OptimizingEngine
                    await self._publish("optimization.request", json.dumps({
                        "request_type": "immediate",
                        "service": "all",
                        "level": "standard"
                    }).encode())
                else:
                    self.logger.warning(f"Skipping periodic optimization due to system state: {self.system_state.value}")

            except Exception as e:
                self.logger.error(f"Optimization loop failed: {e}")
            await asyncio.sleep(300) # Trigger every 5 minutes

    async def _learning_loop(self):
        """Periodically analyze decision history to improve ML models"""
        while not self._shutdown_event.is_set():
            try:
                if len(self.decision_history) > 100: # Only train if enough data
                    self.logger.info("Training ML decision models.")
                    await self._train_decision_models()
                    self.decision_history.clear() # Clear history after training

            except Exception as e:
                self.logger.error(f"Learning loop failed: {e}")
            await asyncio.sleep(3600) # Train every hour

    async def _train_decision_models(self):
        """Train or update ML models for decision making"""
        # This is a placeholder for actual ML model training.
        # In a real system, this would involve feature engineering from decision_history,
        # training a model (e.g., a simple neural network or a decision tree),
        # and updating self.decision_network or other prediction_models.
        self.logger.info("Simulating ML model training...")
        # Example: update weights randomly for demonstration
        if self.decision_network:
            for layer in self.decision_network['weights']:
                self.decision_network['weights'][layer] += np.random.randn(*self.decision_network['weights'][layer].shape) * 0.01
            self.logger.info("ML decision network weights updated.")

        # Persist trained models to disk or a model store
        # For simplicity, we'll just log it.
        await self._db_query(
            "INSERT INTO ml_model_versions (model_name, version, trained_at, metadata) VALUES ($1, $2, $3, $4)",
            "decision_network", str(uuid.uuid4()), datetime.now(), json.dumps({"status": "trained"})
        )

    async def _health_check_loop(self):
        """Periodically check health of registered agents"""
        while not self._shutdown_event.is_set():
            try:
                for agent_name, health_info in list(self.agent_health.items()): # Iterate over a copy
                    if time.time() - health_info.get('last_seen', 0) > 60: # Agent not seen for 60 seconds
                        self.logger.warning(f"Agent {agent_name} is unresponsive. Marking as degraded.")
                        self.agent_health[agent_name]['status'] = 'degraded'
                        # Optionally, remove from active capabilities or trigger restart
                        await self._publish_to_stream("alerts.agent.unresponsive", {"agent_name": agent_name})
                        # Update DB status
                        await self._db_query("UPDATE agents SET status = $1 WHERE name = $2", "degraded", agent_name)

            except Exception as e:
                self.logger.error(f"Health check loop failed: {e}")
            await asyncio.sleep(30) # Check every 30 seconds

    async def _prediction_loop(self):
        """Periodically generate predictions for future system state and needs"""
        while not self._shutdown_event.is_set():
            try:
                self.logger.info("Generating system predictions.")
                # This would involve using self.prediction_models to forecast metrics
                # and potential issues.
                predictions = await self._predict_system_needs(horizon_hours=self.forecast_horizon/3600)
                await self._publish_to_stream("system.predictions", predictions)

            except Exception as e:
                self.logger.error(f"Prediction loop failed: {e}")
            await asyncio.sleep(self.forecast_horizon) # Run every forecast horizon

    async def _predict_system_needs(self, horizon_hours: float) -> Dict[str, Any]:
        """Predict future system needs based on historical data and patterns"""
        # Placeholder for actual ML model prediction
        # In a real scenario, this would use trained models to forecast metrics
        # and identify potential issues before they occur.
        self.logger.info(f"Simulating system prediction for next {horizon_hours} hours.")
        return {
            "timestamp": time.time(),
            "horizon_hours": horizon_hours,
            "predicted_cpu_peak": 95.0,
            "predicted_memory_peak": 90.0,
            "predicted_bottlenecks": ["database_connections", "nats_queue_depth"],
            "recommendations": ["Pre-scale database connections", "Monitor NATS queue depth closely"]
        }

    async def _initialize_predictive_models(self):
        """Load or train predictive models on startup"""
        self.logger.info("Initializing predictive models...")
        # In a real system, this would load pre-trained models from a model store
        # or trigger a lightweight training process.
        self.prediction_models["system_load_forecaster"] = {"model": "dummy_model", "status": "ready"}
        self.logger.info("Predictive models initialized.")


if __name__ == "__main__":
    import os
    
    async def main():
        config = AgentConfig(
            name="intelligence-engine",
            agent_type="intelligence",
            capabilities=[
                "agent_routing",
                "system_optimization",
                "predictive_analytics",
                "adaptive_learning",
                "workflow_coordination",
                "anomaly_detection",
                "resource_management"
            ],
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
            consul_url=os.getenv("CONSUL_URL", "http://consul:8500")
        )
        
        engine = IntelligenceEngine(config)
        await engine.run()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Intelligence Engine stopped.")

