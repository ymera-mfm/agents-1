'''
Central Intelligence Engine
Advanced orchestration, decision-making, and system optimization
'''

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
import random
import pickle # For serializing/deserializing ML models

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority
from opentelemetry import trace
import asyncpg
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Placeholder for ML model integration (e.g., scikit-learn, tensorflow, pytorch)
# For this example, we'll use a simplified in-memory model.
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import accuracy_score

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Database Schema for Persistence ---
metadata = sa.MetaData()

agents_table = sa.Table(
    "agents",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, unique=True, nullable=False),
    sa.Column("agent_type", sa.String, nullable=False),
    sa.Column("status", sa.String, default="inactive"),
    sa.Column("capabilities", postgresql.ARRAY(sa.String), default=[]),
    sa.Column("config", postgresql.JSONB, default={}),
    sa.Column("metadata", postgresql.JSONB, default={}),
    sa.Column("last_seen", sa.Float, default=time.time),
    sa.Column("created_at", sa.Float, default=time.time),
    sa.Column("updated_at", sa.Float, default=time.time, onupdate=time.time),
)

agent_capabilities_table = sa.Table(
    "agent_capabilities",
    metadata,
    sa.Column("agent_id", sa.String, sa.ForeignKey("agents.id"), primary_key=True),
    sa.Column("capability", sa.String, primary_key=True),
    sa.Column("confidence", sa.Float, default=0.8),
    sa.Column("load_factor", sa.Float, default=0.0),
    sa.Column("success_rate", sa.Float, default=1.0),
    sa.Column("avg_response_time", sa.Float, default=1.0),
    sa.Column("last_updated", sa.Float, default=time.time, onupdate=time.time),
)

decision_history_table = sa.Table(
    "decision_history",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("request_id", sa.String, nullable=False),
    sa.Column("task_type", sa.String, nullable=False),
    sa.Column("chosen_agent_id", sa.String, nullable=False),
    sa.Column("decision_strategy", sa.String, nullable=False),
    sa.Column("confidence", sa.Float, nullable=False),
    sa.Column("reasoning", sa.Text, nullable=True),
    sa.Column("estimated_duration", sa.Float, nullable=True),
    sa.Column("actual_duration", sa.Float, nullable=True),
    sa.Column("success", sa.Boolean, nullable=True),
    sa.Column("timestamp", sa.Float, default=time.time),
    sa.Column("context_data", postgresql.JSONB, default={}),
    sa.Column("requirements", postgresql.JSONB, default={}),
    sa.Column("constraints", postgresql.JSONB, default={}),
)

system_metrics_table = sa.Table(
    "system_metrics",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, nullable=False),
    sa.Column("value", sa.Float, nullable=False),
    sa.Column("unit", sa.String, nullable=True),
    sa.Column("timestamp", sa.Float, default=time.time),
    sa.Column("tags", postgresql.JSONB, default={}),
)

optimization_rules_table = sa.Table(
    "optimization_rules",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, unique=True, nullable=False),
    sa.Column("condition", sa.Text, nullable=False), # Python code snippet or DSL
    sa.Column("action", sa.Text, nullable=False),    # Python code snippet or DSL
    sa.Column("priority", sa.Integer, default=5),
    sa.Column("enabled", sa.Boolean, default=True),
    sa.Column("created_at", sa.Float, default=time.time),
    sa.Column("updated_at", sa.Float, default=time.time, onupdate=time.time),
)

predictive_models_table = sa.Table(
    "predictive_models",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, unique=True, nullable=False),
    sa.Column("model_type", sa.String, nullable=False),
    sa.Column("model_config", postgresql.JSONB, default={}),
    sa.Column("model_data", sa.LargeBinary, nullable=True), # Stored as bytes (e.g., pickled model)
    sa.Column("last_trained", sa.Float, default=time.time),
    sa.Column("accuracy", sa.Float, default=0.0),
    sa.Column("enabled", sa.Boolean, default=True),
    sa.Column("created_at", sa.Float, default=time.time),
    sa.Column("updated_at", sa.Float, default=time.time, onupdate=time.time),
)



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
    '''
    Central Intelligence Engine that provides:
    - Intelligent agent selection and task routing
    - System-wide optimization and resource management
    - Predictive analytics and pattern recognition
    - Adaptive learning from system behavior
    - Real-time decision making with ML models
    - Cross-agent coordination and conflict resolution
    - Performance optimization and auto-scaling
    - Anomaly detection and self-healing
    '''
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        self.db_pool: Optional[asyncpg.Pool] = None

        # Agent registry and capabilities
        self.agent_registry: Dict[str, Dict] = {}
        self.agent_capabilities: Dict[str, List[AgentCapability]] = defaultdict(list)
        self.agent_load: Dict[str, float] = defaultdict(float)
        self.agent_health: Dict[str, Dict] = {}
        
        # Decision engine
        self.decision_strategy = DecisionStrategy.ADAPTIVE
        self.decision_history_cache = deque(maxlen=10000) # In-memory cache
        self.decision_models = {}
        
        # System state management
        self.system_state = SystemState.INITIALIZING
        self.system_metrics_cache: Dict[str, SystemMetric] = {}
        self.metric_history_cache = deque(maxlen=50000) # In-memory cache
        
        # Learning and optimization
        self.performance_patterns = {}
        self.optimization_rules_cache: Dict[str, Dict] = {}
        self.anomaly_detectors = {}
        
        # Task coordination
        self.active_workflows: Dict[str, Dict] = {}
        self.task_dependencies: Dict[str, List[str]] = defaultdict(list)
        self.resource_pools: Dict[str, Dict] = defaultdict(dict)
        
        # Predictive analytics
        self.prediction_models_cache: Dict[str, Any] = {}
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

        # ML model for adaptive routing
        self.routing_model = None
        self.routing_model_training_data = deque(maxlen=10000)

        # Lock for shared resources
        self._lock = threading.Lock()
        
    async def start(self):
        '''Start intelligence engine services'''
        if self.config.postgres_url:
            try:
                self.db_pool = await asyncpg.create_pool(self.config.postgres_url)
                logger.info("Connected to PostgreSQL for intelligence persistence.")
                await self._init_db()
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL or initialize DB for IntelligenceEngine: {e}", exc_info=True)
                self.db_pool = None

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

        await self._subscribe(
            "intelligence.get_agents",
            self._handle_get_agents
        )

        await self._subscribe(
            "intelligence.get_decision_history",
            self._handle_get_decision_history
        )

        await self._subscribe(
            "intelligence.get_optimization_rules",
            self._handle_get_optimization_rules
        )

        await self._subscribe(
            "intelligence.update_optimization_rule",
            self._handle_update_optimization_rule
        )
        
        # Start background services
        asyncio.create_task(self._system_monitor_loop())
        asyncio.create_task(self._optimization_loop())
        asyncio.create_task(self._learning_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._prediction_loop())
        asyncio.create_task(self._cleanup_old_data())
        
        # Initialize system state
        await self._initialize_system()
        
        self.logger.info("Intelligence Engine started")
    
    def _initialize_ml_components(self):
        '''Initialize machine learning components'''
        try:
            # Simple neural network for decision making (can be replaced by a more complex model)
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

            # Initialize ML model for adaptive routing (placeholder)
            # In a production system, this would load a pre-trained model
            # or initialize a model for online learning.
            self.routing_model = {
                "model_type": "RandomForestClassifier",
                "features": ["agent_load", "agent_success_rate", "agent_avg_response_time", "task_priority"],
                "target": "chosen_agent_id",
                "model_data": None # Placeholder for serialized model
            }
            
        except Exception as e:
            self.logger.warning(f"ML components initialization failed: {e}", exc_info=True)

    
    async def _init_db(self):
        '''Initialize database tables if they don\'t exist.'''
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                # Create agents table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS agents (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        agent_type VARCHAR(255) NOT NULL,
                        status VARCHAR(50) DEFAULT \'inactive\',
                        capabilities TEXT[] DEFAULT \'{}\'::TEXT[],
                        config JSONB DEFAULT \'{}\'::JSONB,
                        metadata JSONB DEFAULT \'{}\'::JSONB,
                        last_seen DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                        created_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                        updated_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
                    );
                ''')
                # Create agent_capabilities table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS agent_capabilities (
                        agent_id VARCHAR(255) REFERENCES agents(id) ON DELETE CASCADE,
                        capability VARCHAR(255),
                        confidence DOUBLE PRECISION DEFAULT 0.8,
                        load_factor DOUBLE PRECISION DEFAULT 0.0,
                        success_rate DOUBLE PRECISION DEFAULT 1.0,
                        avg_response_time DOUBLE PRECISION DEFAULT 1.0,
                        last_updated DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                        PRIMARY KEY (agent_id, capability)
                    );
                ''')
                # Create decision_history table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS decision_history (
                        id VARCHAR(255) PRIMARY KEY,
                        request_id VARCHAR(255) NOT NULL,
                        task_type VARCHAR(255) NOT NULL,
                        chosen_agent_id VARCHAR(255) NOT NULL,
                        decision_strategy VARCHAR(50) NOT NULL,
                        confidence DOUBLE PRECISION NOT NULL,
                        reasoning TEXT,
                        estimated_duration DOUBLE PRECISION,
                        actual_duration DOUBLE PRECISION,
                        success BOOLEAN,
                        timestamp DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                        context_data JSONB DEFAULT \'{}\'::JSONB,
                        requirements JSONB DEFAULT \'{}\'::JSONB,
                        constraints JSONB DEFAULT \'{}\'::JSONB
                    );
                ''')
                # Create system_metrics table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        value DOUBLE PRECISION NOT NULL,
                        unit VARCHAR(50),
                        timestamp DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                        tags JSONB DEFAULT \'{}\'::JSONB
                    );
                ''')
                # Create optimization_rules table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS optimization_rules (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        condition TEXT NOT NULL,
                        action TEXT NOT NULL,
                        priority INTEGER DEFAULT 5,
                        enabled BOOLEAN DEFAULT TRUE,
                        created_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                        updated_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
                    );
                ''')
                # Create predictive_models table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS predictive_models (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        model_type VARCHAR(255) NOT NULL,
                        model_config JSONB DEFAULT \'{}\'::JSONB,
                        model_data BYTEA,
                        last_trained DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                        accuracy DOUBLE PRECISION DEFAULT 0.0,
                        enabled BOOLEAN DEFAULT TRUE,
                        created_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW()),
                        updated_at DOUBLE PRECISION DEFAULT EXTRACT(EPOCH FROM NOW())
                    );
                ''')
                self.logger.info("Database tables for IntelligenceEngine initialized.")

    async def _initialize_system(self):
        '''Initialize system state from database'''
        try:
            if not self.db_pool:
                self.logger.warning("Database pool not initialized. System starting with empty state.")
                self.system_state = SystemState.HEALTHY
                return

            async with self.db_pool.acquire() as conn:
                # Load agents
                agent_records = await conn.fetch("SELECT * FROM agents")
                for record in agent_records:
                    agent_id = record['id']
                    self.agent_registry[agent_id] = dict(record)
                    self.agent_health[agent_id] = {
                        'status': record['status'],
                        'last_seen': record['last_seen'],
                        'response_time': 0.0, # Will be updated by heartbeats
                        'error_count': 0
                    }

                # Load agent capabilities
                capability_records = await conn.fetch("SELECT * FROM agent_capabilities")
                for cap_record in capability_records:
                    capability_obj = AgentCapability(
                        agent_id=cap_record['agent_id'],
                        capability=cap_record['capability'],
                        confidence=cap_record['confidence'],
                        load_factor=cap_record['load_factor'],
                        success_rate=cap_record['success_rate'],
                        avg_response_time=cap_record['avg_response_time'],
                        last_updated=cap_record['last_updated']
                    )
                    if capability_obj.capability not in self.agent_capabilities:
                        self.agent_capabilities[capability_obj.capability] = []
                    self.agent_capabilities[capability_obj.capability].append(capability_obj)

                # Load optimization rules
                await self._load_optimization_rules()
                
                # Initialize predictive models
                await self._initialize_predictive_models()
                
                self.system_state = SystemState.HEALTHY
                self.logger.info("System initialization completed")
                
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}", exc_info=True)
            self.system_state = SystemState.CRITICAL
    
    async def _handle_agent_registration(self, msg):
        '''Handle new agent registration'''
        try:
            data = json.loads(msg.data.decode())
            agent_name = data["name"]
            agent_info = data["info"]
            agent_id = str(uuid.uuid4()) # Generate a unique ID for the agent

            if not self.db_pool:
                self.logger.warning("Database pool not initialized. Agent registration will be in-memory only.")
                # In-memory registration
                self.agent_registry[agent_name] = agent_info
                self.agent_health[agent_name] = {
                    "status": "healthy",
                    "last_seen": time.time(),
                    "response_time": 0.0,
                    "error_count": 0
                }
                for capability in agent_info.get("capabilities", []):
                    cap_obj = AgentCapability(
                        agent_id=agent_name,
                        capability=capability,
                        confidence=agent_info.get("confidence", 0.8),
                        load_factor=0.0,
                        success_rate=1.0,
                        avg_response_time=1.0,
                        last_updated=time.time()
                    )
                    if capability not in self.agent_capabilities:
                        self.agent_capabilities[capability] = []
                    self.agent_capabilities[capability].append(cap_obj)
                self.logger.info(f"Agent registered (in-memory): {agent_name}", 
                               agent_type=agent_info.get("type"),
                               capabilities=len(agent_info.get("capabilities", [])))
                await self._trigger_optimization("agent_registration")
                return

            async with self.db_pool.acquire() as conn:
                # Persist agent to database
                await conn.execute('''
                    INSERT INTO agents (id, name, agent_type, status, capabilities, config, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (name) DO UPDATE SET
                        agent_type = EXCLUDED.agent_type,
                        status = EXCLUDED.status,
                        capabilities = EXCLUDED.capabilities,
                        config = EXCLUDED.config,
                        metadata = EXCLUDED.metadata,
                        last_seen = EXTRACT(EPOCH FROM NOW()),
                        updated_at = EXTRACT(EPOCH FROM NOW())
                    RETURNING id;
                ''',
                agent_id, agent_name, agent_info.get("type", "unknown"), "healthy",
                agent_info.get("capabilities", []), json.dumps(agent_info.get("config", {})),
                json.dumps(agent_info.get("metadata", {})))

                # Update in-memory registry
                self.agent_registry[agent_id] = {
                    'id': agent_id,
                    'name': agent_name,
                    'type': agent_info.get("type"),
                    'status': "healthy",
                    'capabilities': agent_info.get("capabilities", []),
                    'config': agent_info.get("config", {}),
                    'metadata': agent_info.get("metadata", {})
                }
                self.agent_health[agent_id] = {
                    'status': "healthy",
                    'last_seen': time.time(),
                    'response_time': 0.0,
                    'error_count': 0
                }

                # Persist capabilities
                for capability_name in agent_info.get("capabilities", []):
                    cap_obj = AgentCapability(
                        agent_id=agent_id,
                        capability=capability_name,
                        confidence=agent_info.get("confidence", 0.8),
                        load_factor=0.0,
                        success_rate=1.0,
                        avg_response_time=1.0,
                        last_updated=time.time()
                    )
                    await conn.execute('''
                        INSERT INTO agent_capabilities (agent_id, capability, confidence, load_factor, success_rate, avg_response_time, last_updated)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (agent_id, capability) DO UPDATE SET
                            confidence = EXCLUDED.confidence,
                            load_factor = EXCLUDED.load_factor,
                            success_rate = EXCLUDED.success_rate,
                            avg_response_time = EXCLUDED.avg_response_time,
                            last_updated = EXCLUDED.last_updated;
                    ''',
                    cap_obj.agent_id, cap_obj.capability, cap_obj.confidence, cap_obj.load_factor,
                    cap_obj.success_rate, cap_obj.avg_response_time, cap_obj.last_updated)
                    
                    # Update in-memory capabilities
                    if capability_name not in self.agent_capabilities:
                        self.agent_capabilities[capability_name] = []
                    # Remove old entry if exists
                    self.agent_capabilities[capability_name] = [c for c in self.agent_capabilities[capability_name] if c.agent_id != agent_id]
                    self.agent_capabilities[capability_name].append(cap_obj)

            self.logger.info(f"Agent registered: {agent_name} (ID: {agent_id})", 
                           agent_type=agent_info.get("type"),
                           capabilities=len(agent_info.get("capabilities", [])))
            
            # Trigger system rebalancing
            await self._trigger_optimization("agent_registration")
            
        except Exception as e:
            self.logger.error(f"Agent registration failed: {e}", exc_info=True)

    
    async def _handle_agent_heartbeat(self, msg):
        '''Handle agent heartbeat messages'''
        try:
            data = json.loads(msg.data.decode())
            agent_id = data["agent_id"]
            agent_name = data["agent_name"]
            metrics = data.get("metrics", {})
            status = data.get("status", "healthy")
            current_time = time.time()

            if not self.db_pool:
                self.logger.warning("Database pool not initialized. Agent heartbeat will be in-memory only.")
                # In-memory update
                if agent_id in self.agent_health:
                    self.agent_health[agent_id].update({
                        "status": status,
                        "last_seen": current_time,
                        "load": metrics.get("load", 0.0),
                        "memory_usage": metrics.get("memory_usage", 0.0),
                        "active_tasks": metrics.get("active_tasks", 0),
                        "queue_size": metrics.get("queue_size", 0)
                    })
                    self.agent_load[agent_id] = metrics.get("load", 0.0)
                    await self._update_capability_performance(agent_id, metrics)
                return

            async with self.db_pool.acquire() as conn:
                # Update agent status and last_seen in agents table
                await conn.execute('''
                    UPDATE agents SET
                        status = $1,
                        last_seen = $2,
                        updated_at = $2
                    WHERE id = $3;
                ''', status, current_time, agent_id)

                # Update in-memory agent health
                if agent_id in self.agent_health:
                    self.agent_health[agent_id].update({
                        "status": status,
                        "last_seen": current_time,
                        "load": metrics.get("load", 0.0),
                        "memory_usage": metrics.get("memory_usage", 0.0),
                        "active_tasks": metrics.get("active_tasks", 0),
                        "queue_size": metrics.get("queue_size", 0)
                    })
                else:
                    # If agent not in in-memory health, fetch from DB or initialize
                    self.agent_health[agent_id] = {
                        "status": status,
                        "last_seen": current_time,
                        "response_time": 0.0,
                        "error_count": 0,
                        "load": metrics.get("load", 0.0),
                        "memory_usage": metrics.get("memory_usage", 0.0),
                        "active_tasks": metrics.get("active_tasks", 0),
                        "queue_size": metrics.get("queue_size", 0)
                    }
                
                # Update load tracking
                self.agent_load[agent_id] = metrics.get("load", 0.0)
                
                # Update capabilities performance in DB and in-memory
                await self._update_capability_performance(agent_id, metrics)

                # Persist system metrics if available in heartbeat
                for metric_name, value in metrics.items():
                    if metric_name in [m.value for m in SystemMetric]: # Only persist known system metrics
                        await self._persist_system_metric(SystemMetric(metric_name), value, "unit", {"agent_id": agent_id})
            
        except Exception as e:
            self.logger.error(f"Heartbeat processing failed for agent {agent_id}: {e}", exc_info=True)

    
    async def _handle_task_routing(self, msg):
        '''Handle intelligent task routing requests'''
        try:
            data = json.loads(msg.data.decode())
            
            decision_context = DecisionContext(
                request_id=data["request_id"],
                task_type=data["task_type"],
                requirements=data.get("requirements", {}),
                constraints=data.get("constraints", {}),
                priority=Priority(data.get("priority", "medium")),
                deadline=data.get("deadline"),
                context_data=data.get("context", {})
            )
            
            with self.tracer.start_as_current_span("task_routing") as span:
                span.set_attribute("task_type", decision_context.task_type)
                span.set_attribute("priority", decision_context.priority.value)
                
                # Find best agent for the task
                recommendation = await self._route_task(decision_context)
                
                # Send routing decision
                await self._publish(f"task.{decision_context.request_id}.route", {
                    "agent_id": recommendation.agent_id,
                    "confidence": recommendation.confidence,
                    "reasoning": recommendation.reasoning,
                    "estimated_duration": recommendation.estimated_duration,
                    "resource_requirements": recommendation.resource_requirements
                })
                
                # Record decision for learning and persistence
                await self._record_decision(decision_context, recommendation)
                
        except Exception as e:
            self.logger.error(f"Task routing failed: {e}", exc_info=True)

    
    async def _route_task(self, context: DecisionContext) -> AgentRecommendation:
        '''Intelligent task routing using multiple strategies'''
        
        # Get capable agents
        capable_agents = await self._find_capable_agents(context.task_type, context.requirements)
        
        if not capable_agents:
            raise ValueError(f"No agents found capable of handling task type: {context.task_type}")
        
        # Apply routing strategy
        if self.decision_strategy == DecisionStrategy.ADAPTIVE:
            return await self._adaptive_routing(capable_agents, context)
        elif self.decision_strategy == DecisionStrategy.ML_BASED:
            return await self._ml_based_routing(capable_agents, context)
        elif self.decision_strategy == DecisionStrategy.CONSENSUS:
            return await self._consensus_routing(capable_agents, context)
        else:
            return await self._weighted_routing(capable_agents, context)
    
    async def _find_capable_agents(self, task_type: str, requirements: Dict[str, Any]) -> List[str]:
        '''Find agents capable of handling the task'''
        capable_agent_ids = set()
        required_caps = requirements.get("required_capabilities", [])

        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                # Query agents that have the primary task_type capability
                query = sa.select(agent_capabilities_table.c.agent_id).where(
                    agent_capabilities_table.c.capability == task_type
                )
                records = await conn.fetch(query)
                for record in records:
                    agent_id = record["agent_id"]
                    # Check if agent is healthy in in-memory cache (or fetch from DB if not present)
                    if self.agent_health.get(agent_id, {}).get("status") == "healthy":
                        capable_agent_ids.add(agent_id)

                # Query agents that have all required_caps
                if required_caps:
                    # This query finds agents that have ALL capabilities in required_caps
                    # It's a bit more complex as we need to group by agent_id and count matches
                    query = sa.text('''
                        SELECT agent_id FROM agent_capabilities
                        WHERE capability = ANY(:required_caps)
                        GROUP BY agent_id
                        HAVING COUNT(DISTINCT capability) = :num_required_caps
                    ''')
                    records = await conn.fetch(query, required_caps=required_caps, num_required_caps=len(required_caps))
                    for record in records:
                        agent_id = record["agent_id"]
                        if self.agent_health.get(agent_id, {}).get("status") == "healthy":
                            capable_agent_ids.add(agent_id)

        else:
            # Fallback to in-memory registry if no DB connection
            if task_type in self.agent_capabilities:
                for capability in self.agent_capabilities[task_type]:
                    if (capability.agent_id in self.agent_registry and 
                        self.agent_health.get(capability.agent_id, {}).get("status") == "healthy"):
                        capable_agent_ids.add(capability.agent_id)
            
            for agent_id, agent_info in self.agent_registry.items():
                if agent_id not in capable_agent_ids:
                    agent_capabilities = agent_info.get("capabilities", [])
                    if all(cap in agent_capabilities for cap in required_caps):
                        if self.agent_health.get(agent_id, {}).get("status") == "healthy":
                            capable_agent_ids.add(agent_id)

        return list(capable_agent_ids)

    async def _record_decision(self, context: DecisionContext, recommendation: AgentRecommendation):
        '''Record the routing decision for learning and auditing'''
        decision_id = str(uuid.uuid4())
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO decision_history (id, request_id, task_type, chosen_agent_id, decision_strategy, confidence, reasoning, estimated_duration, timestamp, context_data, requirements, constraints)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);
                ''',
                decision_id, context.request_id, context.task_type, recommendation.agent_id,
                self.decision_strategy.value, recommendation.confidence, recommendation.reasoning,
                recommendation.estimated_duration, time.time(), json.dumps(context.context_data),
                json.dumps(context.requirements), json.dumps(context.constraints))
        
        # Also cache in-memory
        self.decision_history_cache.append({
            "id": decision_id,
            "request_id": context.request_id,
            "task_type": context.task_type,
            "chosen_agent_id": recommendation.agent_id,
            "decision_strategy": self.decision_strategy.value,
            "confidence": recommendation.confidence,
            "reasoning": recommendation.reasoning,
            "estimated_duration": recommendation.estimated_duration,
            "timestamp": time.time(),
            "context_data": context.context_data,
            "requirements": context.requirements,
            "constraints": context.constraints
        })

    async def _learning_loop(self):
        '''Periodically update models and strategies based on performance'''
        while True:
            await asyncio.sleep(300) # Run every 5 minutes
            try:
                self.logger.info("Starting learning loop...")
                
                # Update agent capability metrics
                await self._update_all_agent_capabilities()
                
                # Retrain ML models if necessary
                await self._retrain_routing_model()
                await self._retrain_prediction_models()
                
                # Adjust optimization rules
                await self._adjust_optimization_rules()
                
                # Update system state based on recent metrics
                await self._update_system_state()
                
                self.logger.info("Learning loop completed.")
            except Exception as e:
                self.logger.error(f"Error in learning loop: {e}", exc_info=True)

    async def _update_all_agent_capabilities(self):
        '''Update performance metrics for all agent capabilities'''
        if not self.db_pool:
            return

        async with self.db_pool.acquire() as conn:
            # Example: Recalculate success rate and avg response time from decision history
            # This is a simplified example. A real implementation would be more sophisticated.
            records = await conn.fetch('''
                SELECT chosen_agent_id, task_type, success, actual_duration
                FROM decision_history
                WHERE timestamp > $1;
            ''', time.time() - 3600) # Last hour

            capability_updates = defaultdict(lambda: {"successes": 0, "failures": 0, "total_duration": 0, "count": 0})

            for record in records:
                agent_id = record['chosen_agent_id']
                task_type = record['task_type']
                if record['success']:
                    capability_updates[(agent_id, task_type)]["successes"] += 1
                else:
                    capability_updates[(agent_id, task_type)]["failures"] += 1
                if record['actual_duration']:
                    capability_updates[(agent_id, task_type)]["total_duration"] += record['actual_duration']
                capability_updates[(agent_id, task_type)]["count"] += 1

            for (agent_id, capability), metrics in capability_updates.items():
                total_tasks = metrics["successes"] + metrics["failures"]
                if total_tasks > 0:
                    new_success_rate = metrics["successes"] / total_tasks
                    new_avg_response_time = metrics["total_duration"] / metrics["count"] if metrics["count"] > 0 else 0

                    # Update in-memory cache
                    if capability in self.agent_capabilities:
                        for cap_obj in self.agent_capabilities[capability]:
                            if cap_obj.agent_id == agent_id:
                                cap_obj.success_rate = (cap_obj.success_rate * 0.9) + (new_success_rate * 0.1) # EMA
                                if new_avg_response_time > 0:
                                    cap_obj.avg_response_time = (cap_obj.avg_response_time * 0.9) + (new_avg_response_time * 0.1) # EMA
                                cap_obj.last_updated = time.time()

                    # Update database
                    await conn.execute('''
                        UPDATE agent_capabilities
                        SET success_rate = $1, avg_response_time = $2, last_updated = $3
                        WHERE agent_id = $4 AND capability = $5;
                    ''', new_success_rate, new_avg_response_time, time.time(), agent_id, capability)

    async def _retrain_routing_model(self):
        '''Retrain the ML-based routing model'''
        if len(self.routing_model_training_data) < 100: # Don't retrain with too little data
            return

        self.logger.info("Retraining routing model...")
        # This is a placeholder for a real ML model training pipeline
        # In a real system, you would use a library like scikit-learn
        # to train a classifier or regressor.
        
        # Example: Create a simple majority-class model for demonstration
        df = pd.DataFrame(self.routing_model_training_data)
        if 'chosen_agent_id' in df.columns:
            most_common_agent = df['chosen_agent_id'].mode()[0]
            self.routing_model['model_data'] = {'most_common_agent': most_common_agent}
            self.logger.info(f"Routing model retrained. New model: {self.routing_model['model_data']}")

    async def _adaptive_routing(self, capable_agents: List[str], context: DecisionContext) -> AgentRecommendation:
        '''Adaptive routing that balances load, performance, and cost'''
        best_agent = None
        best_score = -1
        reasoning = ""

        for agent_id in capable_agents:
            score = 0
            # Get capability object for this agent and task type
            cap_obj = next((c for c in self.agent_capabilities.get(context.task_type, []) if c.agent_id == agent_id), None)
            if not cap_obj:
                continue

            # Factors to consider: load, success rate, response time, confidence
            load_factor = 1 - cap_obj.load_factor
            success_rate_factor = cap_obj.success_rate
            response_time_factor = 1 / (1 + cap_obj.avg_response_time) # Normalize
            confidence_factor = cap_obj.confidence

            # Weights for each factor (can be dynamically adjusted)
            weights = {"load": 0.4, "success_rate": 0.3, "response_time": 0.2, "confidence": 0.1}

            score = (weights["load"] * load_factor +
                     weights["success_rate"] * success_rate_factor +
                     weights["response_time"] * response_time_factor +
                     weights["confidence"] * confidence_factor)

            if score > best_score:
                best_score = score
                best_agent = agent_id
                reasoning = f"Selected based on adaptive scoring: load({load_factor:.2f}), success({success_rate_factor:.2f}), response_time({response_time_factor:.2f}), confidence({confidence_factor:.2f})"

        if not best_agent:
            # Fallback to random choice if no agent scores well
            best_agent = random.choice(capable_agents)
            reasoning = "Fallback to random choice among capable agents."

        return AgentRecommendation(
            agent_id=best_agent,
            confidence=best_score if best_score != -1 else 0.5,
            reasoning=reasoning,
            estimated_duration=cap_obj.avg_response_time if cap_obj else 1.0, # Provide estimate
            resource_requirements={}
        )

    async def _ml_based_routing(self, capable_agents: List[str], context: DecisionContext) -> AgentRecommendation:
        '''ML-based routing using a trained model'''
        if not self.routing_model or not self.routing_model.get("model_data"):
            self.logger.warning("ML routing model not available, falling back to adaptive routing.")
            return await self._adaptive_routing(capable_agents, context)

        # This is a placeholder for feature extraction and prediction
        # In a real system, you would create a feature vector from the context
        # and agent metrics, then use the trained model to predict the best agent.
        
        # Example: Use the simple majority-class model from _retrain_routing_model
        best_agent = self.routing_model["model_data"].get("most_common_agent")
        if best_agent not in capable_agents:
            best_agent = random.choice(capable_agents)

        return AgentRecommendation(
            agent_id=best_agent,
            confidence=0.9, # Confidence from the model
            reasoning="Selected by ML routing model.",
            estimated_duration=1.0,
            resource_requirements={}
        )

    async def _handle_get_agents(self, msg):
        '''Handle request to get information about registered agents'''
        try:
            request = json.loads(msg.data.decode())
            status_filter = request.get("status")
            capability_filter = request.get("capability")

            agents_info = []
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    query = "SELECT * FROM agents"
                    params = []
                    where_clauses = []
                    if status_filter:
                        where_clauses.append(f"status = ${len(params) + 1}")
                        params.append(status_filter)
                    if capability_filter:
                        where_clauses.append(f"${len(params) + 1} = ANY(capabilities)")
                        params.append(capability_filter)
                    
                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)

                    agent_records = await conn.fetch(query, *params)
                    for record in agent_records:
                        agent_info = dict(record)
                        # Get detailed capabilities
                        cap_records = await conn.fetch("SELECT * FROM agent_capabilities WHERE agent_id = $1", record['id'])
                        agent_info['capabilities_detail'] = [dict(r) for r in cap_records]
                        agents_info.append(agent_info)
            else:
                # In-memory fallback
                for agent_id, agent_data in self.agent_registry.items():
                    # Apply filters
                    if status_filter and self.agent_health.get(agent_id, {}).get("status") != status_filter:
                        continue
                    if capability_filter and capability_filter not in agent_data.get("capabilities", []):
                        continue
                    
                    agent_info = agent_data.copy()
                    agent_info['id'] = agent_id
                    agent_info['health'] = self.agent_health.get(agent_id, {})
                    agent_info['capabilities_detail'] = [c.__dict__ for c_list in self.agent_capabilities.values() for c in c_list if c.agent_id == agent_id]
                    agents_info.append(agent_info)

            await self._publish(msg.reply, {"success": True, "agents": agents_info})

        except Exception as e:
            self.logger.error(f"Failed to get agents: {e}", exc_info=True)
            await self._publish(msg.reply, {"success": False, "error": str(e)})

    async def _handle_get_decision_history(self, msg):
        '''Handle request to get decision history'''
        try:
            request = json.loads(msg.data.decode())
            request_id_filter = request.get("request_id")
            agent_id_filter = request.get("agent_id")
            limit = request.get("limit", 100)

            history = []
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    query = "SELECT * FROM decision_history"
                    params = []
                    where_clauses = []
                    if request_id_filter:
                        where_clauses.append(f"request_id = ${len(params) + 1}")
                        params.append(request_id_filter)
                    if agent_id_filter:
                        where_clauses.append(f"chosen_agent_id = ${len(params) + 1}")
                        params.append(agent_id_filter)

                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)
                    
                    query += f" ORDER BY timestamp DESC LIMIT ${len(params) + 1}"
                    params.append(limit)

                    records = await conn.fetch(query, *params)
                    history = [dict(r) for r in records]
            else:
                # In-memory fallback
                filtered_history = [h for h in self.decision_history_cache 
                                  if (not request_id_filter or h['request_id'] == request_id_filter) and 
                                     (not agent_id_filter or h['chosen_agent_id'] == agent_id_filter)]
                history = list(filtered_history)[-limit:]

            await self._publish(msg.reply, {"success": True, "history": history})

        except Exception as e:
            self.logger.error(f"Failed to get decision history: {e}", exc_info=True)
            await self._publish(msg.reply, {"success": False, "error": str(e)})

    async def _handle_get_optimization_rules(self, msg):
        '''Handle request to get optimization rules'''
        try:
            rules = list(self.optimization_rules_cache.values())
            await self._publish(msg.reply, {"success": True, "rules": rules})
        except Exception as e:
            self.logger.error(f"Failed to get optimization rules: {e}", exc_info=True)
            await self._publish(msg.reply, {"success": False, "error": str(e)})

    async def _handle_update_optimization_rule(self, msg):
        '''Handle request to update an optimization rule'''
        try:
            data = json.loads(msg.data.decode())
            rule_id = data["id"]
            updates = data["updates"]

            if rule_id not in self.optimization_rules_cache:
                raise ValueError(f"Rule with ID {rule_id} not found.")

            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    set_clauses = []
                    params = []
                    for i, (key, value) in enumerate(updates.items()):
                        set_clauses.append(f"{key} = ${i + 1}")
                        params.append(value)
                    
                    params.append(time.time())
                    set_clauses.append(f"updated_at = ${len(params)}")
                    params.append(rule_id)

                    query = f"UPDATE optimization_rules SET {', '.join(set_clauses)} WHERE id = ${len(params)};"
                    await conn.execute(query, *params)

            # Update in-memory cache
            self.optimization_rules_cache[rule_id].update(updates)
            self.optimization_rules_cache[rule_id]['updated_at'] = time.time()

            await self._publish(msg.reply, {"success": True, "message": "Rule updated successfully"})

        except Exception as e:
            self.logger.error(f"Failed to update optimization rule: {e}", exc_info=True)
            await self._publish(msg.reply, {"success": False, "error": str(e)})

    async def _load_optimization_rules(self):
        '''Load optimization rules from the database'''
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch("SELECT * FROM optimization_rules WHERE enabled = TRUE")
                self.optimization_rules_cache = {r['id']: dict(r) for r in records}
                self.logger.info(f"Loaded {len(self.optimization_rules_cache)} optimization rules.")

    async def _initialize_predictive_models(self):
        '''Load and initialize predictive models from the database'''
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch("SELECT * FROM predictive_models WHERE enabled = TRUE")
                for record in records:
                    try:
                        model_name = record['name']
                        model_data = record['model_data']
                        if model_data:
                            self.prediction_models_cache[model_name] = pickle.loads(model_data)
                            self.logger.info(f"Loaded predictive model: {model_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to load predictive model {record['name']}: {e}", exc_info=True)

