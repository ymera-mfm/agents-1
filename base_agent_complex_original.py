
"""
Advanced Base Agent Framework
Combines cutting-edge features with operational simplicity
"""

import abc
import asyncio
import logging
import json
import uuid
import time
import signal
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Any, Dict, List, Optional, Callable, Union, Type, TypeVar
from enum import Enum
import traceback

import nats
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig, ConsumerConfig
from redis import asyncio as aioredis
import asyncpg
import consul
import opentelemetry.trace as trace
from opentelemetry import metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

# === CORE DATA STRUCTURES ===

class AgentStatus(Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentConfig:
    name: str
    version: str = "1.0.0"
    agent_type: str = "generic"
    capabilities: List[str] = field(default_factory=list)
    
    # Connection configs
    nats_url: str = "nats://nats:4222"
    postgres_url: str = "postgresql://agent:secure_password@postgres:5432/ymera"
    redis_url: str = "redis://redis:6379"
    consul_url: str = "http://consul:8500"
    
    # Operational configs
    log_level: str = "INFO"
    max_concurrent_tasks: int = 10
    heartbeat_interval: int = 5 # seconds
    health_check_interval: int = 30 # seconds
    graceful_shutdown_timeout: int = 30 # seconds
    config_refresh_interval: int = 60 # seconds
    
    # Observability
    metrics_port: int = 9100
    enable_metrics_server: bool = True  # Enable Prometheus metrics server on startup
    enable_tracing: bool = True
    jaeger_endpoint: str = "http://jaeger:14268/api/traces"
    
    # Advanced features
    enable_circuit_breaker: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: int = 60
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Custom configurations
    custom: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class TaskRequest:
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    timeout_seconds: int = 300
    retry_policy: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    sender_id: Optional[str] = None # Added sender_id

@dataclass
class TaskResponse:
    task_id: str
    success: bool
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthStatus:
    agent_id: str
    agent_name: str
    status: AgentStatus
    version: str
    uptime_seconds: float
    active_tasks: int
    total_tasks_processed: int
    last_error: Optional[str] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    dependencies: Dict[str, bool] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

# === CIRCUIT BREAKER IMPLEMENTATION ===

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"  
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitBreakerState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs):
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
            
            raise e

# === ADVANCED BASE AGENT ===

T = TypeVar("T")

class BaseAgent(abc.ABC):
    """
    Advanced base agent with cutting-edge features:
    - Distributed tracing & metrics
    - Circuit breakers & rate limiting  
    - Service discovery & health checks
    - Graceful shutdown & resource management
    - Auto-retry with exponential backoff
    - Stream processing capabilities
    - Dynamic configuration management
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = f"{config.name}-{uuid.uuid4().hex[:8]}"
        self.start_time = time.time()
        self.status = AgentStatus.INITIALIZING
        self.active_tasks = 0
        self.total_tasks_processed = 0
        self.last_error: Optional[str] = None
        
        # Setup structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger(self.id)
        
        # Initialize connections (will be established in connect())
        self.nc: Optional[NATS] = None
        self.js = None  # JetStream context
        self.redis: Optional[aioredis.Redis] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.consul_client = None
        
        # Observability
        self._setup_observability()
        
        # Advanced features
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, Dict] = {}
        
        # Task management
        self._task_semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._subscriptions = []
        
        # Shutdown handling
        self._shutdown_event = asyncio.Event()
        self._cleanup_tasks: List[Callable] = []
        
        # Setup signal handlers
        self._setup_signal_handlers()

        # Metrics for performance tracking
        self._task_response_times: List[float] = []
        self._task_success_rates: List[bool] = []

    def _setup_observability(self):
        """Setup OpenTelemetry tracing and Prometheus metrics"""
        # Resource identification
        resource = Resource.create({
            "service.name": f"ymera-{self.config.name}",
            "service.version": self.config.version,
            "agent.id": self.id,
            "agent.type": self.config.agent_type
        })
        
        # Tracing
        if self.config.enable_tracing:
            tracer_provider = TracerProvider(resource=resource)
            jaeger_exporter = JaegerExporter(
                agent_host_name="jaeger",
                agent_port=6831
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)
            trace.set_tracer_provider(tracer_provider)
            
        self.tracer = trace.get_tracer(__name__)
        
        # Metrics
        prometheus_reader = PrometheusMetricReader()
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[prometheus_reader]
        )
        metrics.set_meter_provider(meter_provider)
        self.meter = metrics.get_meter(__name__)
        
        # Custom metrics
        self.task_counter = self.meter.create_counter(
            "agent_tasks_total",
            description="Total number of tasks processed"
        )
        
        self.task_duration = self.meter.create_histogram(
            "agent_task_duration_seconds",
            description="Task execution duration"
        )
        
        self.active_tasks_gauge = self.meter.create_up_down_counter(
            "agent_active_tasks",
            description="Currently active tasks"
        )
        
        # Start Prometheus metrics server (if enabled and not already running)
        if self.config.enable_metrics_server:
            try:
                start_http_server(self.config.metrics_port)
                self.logger.info("Prometheus metrics server started", port=self.config.metrics_port)
            except OSError as e:
                if e.errno == 98:  # Address already in use
                    self.logger.warning(
                        "Prometheus metrics server port already in use, skipping",
                        port=self.config.metrics_port
                    )
                else:
                    raise
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal", signal=signum)
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def connect(self):
        """Establish all external connections"""
        self.logger.info("Establishing connections...")
        
        try:
            # NATS connection with JetStream
            self.nc = NATS()
            await self.nc.connect(
                self.config.nats_url,
                error_cb=self._nats_error_cb,
                disconnected_cb=self._nats_disconnected_cb,
                reconnected_cb=self._nats_reconnected_cb
            )
            
            # Enable JetStream
            self.js = self.nc.jetstream()
            
            # Ensure required streams exist
            await self._setup_streams()
            
            self.logger.info("NATS connected with JetStream enabled")
            
            # Redis connection
            self.redis = aioredis.from_url(
                self.config.redis_url,
                encoding="utf8",
                decode_responses=True
            )
            await self.redis.ping()
            self.logger.info("Redis connected")
            
            # PostgreSQL connection pool
            self.db_pool = await asyncpg.create_pool(
                self.config.postgres_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            self.logger.info("PostgreSQL pool created")
            
            # Consul client
            self.consul_client = consul.Consul(
                host="consul",
                port=8500
            )
            
            # Register with service discovery
            await self._register_with_consul()
            
            self.logger.info("All connections established")
            
        except Exception as e:
            self.logger.error("Failed to establish connections", error=str(e))
            raise
    
    async def _setup_streams(self):
        """Setup required NATS JetStream streams"""
        streams_config = [
            StreamConfig(
                name="TASKS",
                subjects=["task.*", "agent.*.task"],
                retention="workqueue",
                max_age=86400  # 24 hours
            ),
            StreamConfig(
                name="EVENTS",
                subjects=["event.*", "agent.*.event"],
                retention="limits",
                max_age=604800  # 7 days
            ),
            StreamConfig(
                name="METRICS", 
                subjects=["metrics.*", "agent.*.metrics", "agent.heartbeat", "agent.register"],
                retention="limits",
                max_age=259200  # 3 days
            )
        ]
        
        for stream_config in streams_config:
            try:
                await self.js.add_stream(stream_config)
            except Exception as e:
                if "stream name already in use" not in str(e):
                    self.logger.warning("Failed to create stream", 
                                      stream=stream_config.name, error=str(e))
    
    async def _register_with_consul(self):
        """Register agent with Consul service discovery"""
        service_def = {
            'Name': self.config.name,
            'ID': self.id,
            'Tags': [self.config.agent_type] + self.config.capabilities,
            'Address': 'localhost',  # Will be container IP in real deployment
            'Port': self.config.metrics_port,
            'Check': {
                'HTTP': f'http://localhost:{self.config.metrics_port}/health',
                'Interval': '10s',
                'Timeout': '5s'
            },
            'Meta': {
                'version': self.config.version,
                'agent_type': self.config.agent_type,
                'capabilities': json.dumps(self.config.capabilities)
            }
        }
        
        try:
            self.consul_client.agent.service.register(**service_def)
            self.logger.info("Registered with Consul", service_id=self.id)
        except Exception as e:
            self.logger.warning("Failed to register with Consul", error=str(e))
    
    async def _nats_error_cb(self, e):
        self.logger.error("NATS error", error=str(e))
    
    async def _nats_disconnected_cb(self):
        self.logger.warning("NATS disconnected")
        self.status = AgentStatus.DEGRADED
    
    async def _nats_reconnected_cb(self):
        self.logger.info("NATS reconnected")
        if self.status == AgentStatus.DEGRADED:
            self.status = AgentStatus.ACTIVE
    
    @asynccontextmanager
    async def _rate_limit(self, operation: str):
        """Rate limiting context manager"""
        if not self.config.enable_rate_limiting:
            yield
            return
            
        now = time.time()
        window_start = now - self.config.rate_limit_window
        
        # Clean old entries
        limiter = self.rate_limiters.setdefault(operation, {"requests": [], "count": 0})
        limiter["requests"] = [req_time for req_time in limiter["requests"] if req_time > window_start]
        limiter["count"] = len(limiter["requests"])
        
        if limiter["count"] >= self.config.rate_limit_requests:
            raise Exception(f"Rate limit exceeded for {operation}")
        
        limiter["requests"].append(now)
        limiter["count"] += 1
        yield
    
    def get_circuit_breaker(self, operation: str) -> CircuitBreaker:
        """Get or create circuit breaker for operation"""
        if operation not in self.circuit_breakers:
            self.circuit_breakers[operation] = CircuitBreaker(
                self.config.circuit_breaker_failure_threshold,
                self.config.circuit_breaker_timeout
            )
        return self.circuit_breakers[operation]
    
    async def _subscribe(self, subject: str, callback: Callable, queue_group: Optional[str] = None):
        """Enhanced subscription with error handling and metrics"""
        async def wrapped_callback(msg):
            with self.tracer.start_as_current_span(f"message_received_{subject}") as span:
                span.set_attribute("subject", msg.subject)
                span.set_attribute("agent_id", self.id)
                
                try:
                    await callback(msg)
                except Exception as e:
                    self.logger.error("Message processing failed", 
                                    subject=msg.subject, error=str(e), traceback=traceback.format_exc())
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
        
        if queue_group:
            sub = await self.nc.subscribe(subject, queue=queue_group, cb=wrapped_callback)
        else:
            sub = await self.nc.subscribe(subject, cb=wrapped_callback)
        self._subscriptions.append(sub)
        self.logger.info("Subscribed to NATS subject", subject=subject, queue_group=queue_group)

    async def _publish(self, subject: str, data: bytes, reply_to: Optional[str] = None):
        """Publish a message to NATS"""
        with self.tracer.start_as_current_span(f"message_published_{subject}") as span:
            span.set_attribute("subject", subject)
            span.set_attribute("agent_id", self.id)
            await self.nc.publish(subject, data, reply=reply_to)
            self.logger.debug("Published message", subject=subject)

    async def _publish_to_stream(self, stream_name: str, data: Dict[str, Any]):
        """Publish data to a NATS JetStream stream."""
        with self.tracer.start_as_current_span(f"stream_published_{stream_name}") as span:
            span.set_attribute("stream_name", stream_name)
            span.set_attribute("agent_id", self.id)
            try:
                js = self.nc.jetstream()
                await js.publish(stream_name, json.dumps(data).encode())
                self.logger.debug("Published to stream", stream_name=stream_name)
            except Exception as e:
                self.logger.error("Failed to publish to stream", stream_name=stream_name, error=str(e), traceback=traceback.format_exc())
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))

    async def _request(self, subject: str, data: bytes, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Send a NATS request and wait for a response"""
        with self.tracer.start_as_current_span(f"nats_request_{subject}") as span:
            span.set_attribute("subject", subject)
            span.set_attribute("agent_id", self.id)
            try:
                response = await self.nc.request(subject, data, timeout=timeout)
                decoded_response = json.loads(response.data.decode())
                self.logger.debug("NATS request successful", subject=subject)
                return decoded_response
            except nats.errors.TimeoutError:
                self.logger.warning("NATS request timed out", subject=subject)
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Timeout"))
                return None
            except Exception as e:
                self.logger.error("NATS request failed", subject=subject, error=str(e), traceback=traceback.format_exc())
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                return None

    async def run(self):
        """Main entry point for the agent lifecycle"""
        self.logger.info("Agent starting", agent_id=self.id, agent_name=self.config.name)
        try:
            await self.connect()
            await self._fetch_initial_config()
            await self._register_agent()
            
            # Start agent-specific logic (to be overridden by subclasses)
            await self.start()
            
            # Start background tasks
            asyncio.create_task(self._heartbeat_sender())
            asyncio.create_task(self._metrics_publisher())
            asyncio.create_task(self._config_watcher())

            # Subscribe to agent-specific task queue
            await self._subscribe(
                f"agent.{self.config.name}.task",
                self._handle_task_request,
                queue_group=f"{self.config.name}_workers"
            )

            self.status = AgentStatus.ACTIVE
            self.logger.info("Agent is active", agent_id=self.id, agent_name=self.config.name)
            
            await self._shutdown_event.wait() # Keep agent running until shutdown event is set
        except asyncio.CancelledError:
            self.logger.info("Agent received cancellation signal.", agent_id=self.id)
        except Exception as e:
            self.logger.error("Agent encountered a fatal error", error=str(e), traceback=traceback.format_exc())
            self.status = AgentStatus.ERROR
        finally:
            await self.shutdown()

    @abc.abstractmethod
    async def start(self):
        """Agents should override this method to implement their specific startup logic."""
        pass

    async def shutdown(self):
        """Gracefully shut down the agent."""
        self.logger.info("Shutting down agent", agent_id=self.id, agent_name=self.config.name)
        self.status = AgentStatus.SHUTTING_DOWN
        self._shutdown_event.set()

        # Allow some time for active tasks to complete
        if self._running_tasks:
            self.logger.info(f"Waiting for {len(self._running_tasks)} active tasks to complete...")
            await asyncio.gather(*self._running_tasks.values(), return_exceptions=True)

        # Unsubscribe from NATS subjects
        for sub in self._subscriptions:
            try:
                await sub.unsubscribe()
            except Exception as e:
                self.logger.warning("Failed to unsubscribe from NATS", error=str(e))

        # Close NATS connection
        if self.nc and self.nc.is_connected:
            await self.nc.close()
            self.logger.info("NATS connection closed.")
        
        # Close database pool
        if self.db_pool:
            await self.db_pool.close()
            self.logger.info("PostgreSQL connection pool closed.")

        # Close Redis connection
        if self.redis:
            await self.redis.close()
            self.logger.info("Redis connection closed.")

        # Deregister from Consul
        if self.consul_client:
            try:
                self.consul_client.agent.service.deregister(self.id)
                self.logger.info("Deregistered from Consul.")
            except Exception as e:
                self.logger.warning("Failed to deregister from Consul", error=str(e))

        self.logger.info("Agent stopped.", agent_id=self.id)

    async def _fetch_initial_config(self):
        """Fetch initial configuration from ConfigManager."""
        self.logger.info("Fetching initial configuration from ConfigManager", agent_name=self.config.name)
        try:
            response = await self._request(
                "config.get",
                json.dumps({"agent_name": self.config.name}).encode(),
                timeout=5
            )
            if response and "config" in response:
                # Merge fetched config with current config, prioritizing fetched values
                for key, value in response["config"].items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                self.logger.info("Initial configuration loaded from ConfigManager.", agent_name=self.config.name)
            else:
                self.logger.warning("No specific configuration found for agent in ConfigManager. Using defaults.", agent_name=self.config.name)
        except Exception as e:
            self.logger.error("Failed to fetch initial config", agent_name=self.config.name, error=str(e), traceback=traceback.format_exc())

    async def _config_watcher(self):
        """Watch for dynamic configuration updates from ConfigManager."""
        while not self._shutdown_event.is_set():
            try:
                # Request config periodically, or subscribe to push updates
                # For now, let's implement a pull mechanism for simplicity and robustness
                await asyncio.sleep(self.config.config_refresh_interval)
                self.logger.debug("Checking for config updates", agent_name=self.config.name)
                response = await self._request(
                    "config.get",
                    json.dumps({"agent_name": self.config.name}).encode(),
                    timeout=5
                )
                if response and "config" in response:
                    new_config_data = response["config"]
                    # Compare and apply changes
                    current_config_dict = asdict(self.config)
                    if any(current_config_dict.get(k) != v for k, v in new_config_data.items()):
                        self.logger.info("Applying dynamic configuration update.", agent_name=self.config.name)
                        for key, value in new_config_data.items():
                            if hasattr(self.config, key):
                                setattr(self.config, key, value)
                        if hasattr(self, '_on_config_update'):
                            await self._on_config_update(new_config_data)
            except Exception as e:
                self.logger.error("Error in config watcher", agent_name=self.config.name, error=str(e), traceback=traceback.format_exc())

    async def _register_agent(self):
        """Register agent with the Orchestrator and persist in DB."""
        if not self.db_pool:
            self.logger.warning("DB pool not initialized, skipping agent registration persistence.")

        registration_data = {
            "agent_id": self.id,
            "agent_name": self.config.name,
            "agent_type": self.config.agent_type,
            "capabilities": self.config.capabilities,
            "version": self.config.version,
            "description": f"A {self.config.agent_type} agent named {self.config.name}",
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "status": self.status.value # Initial status
        }
        
        # Publish registration to Orchestrator (which subscribes to agent.register on METRICS stream)
        await self._publish_to_stream("agent.register", registration_data)
        self.logger.info("Agent registered with Orchestrator.", agent_name=self.config.name)

    async def _heartbeat_sender(self):
        """Periodically send heartbeats to the Orchestrator."""
        while not self._shutdown_event.is_set():
            try:
                avg_response_time = sum(self._task_response_times) / len(self._task_response_times) if self._task_response_times else 0.0
                success_rate = sum(1 for s in self._task_success_rates if s) / len(self._task_success_rates) if self._task_success_rates else 1.0
                
                heartbeat_data = {
                    "agent_id": self.id,
                    "agent_name": self.config.name,
                    "agent_type": self.config.agent_type,
                    "capabilities": self.config.capabilities,
                    "status": self.status.value,
                    "current_load": self.active_tasks,
                    "max_load": self.config.max_concurrent_tasks,
                    "health_score": 1.0, # TODO: Implement actual health score calculation
                    "average_response_time": avg_response_time,
                    "success_rate": success_rate,
                    "timestamp": time.time()
                }
                # Publish heartbeat to Orchestrator (which subscribes to agent.heartbeat on METRICS stream)
                await self._publish_to_stream("agent.heartbeat", heartbeat_data)
                self.logger.debug("Heartbeat sent.", agent_name=self.config.name, load=self.active_tasks)
                
                # Clear recent performance metrics to avoid unbounded growth
                self._task_response_times.clear()
                self._task_success_rates.clear()

                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                self.logger.error("Error in heartbeat sender", agent_name=self.config.name, error=str(e), traceback=traceback.format_exc())
                await asyncio.sleep(self.config.heartbeat_interval)

    async def _metrics_publisher(self):
        """Periodically publish agent-specific metrics."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.heartbeat_interval) # Use heartbeat interval for metrics for now
                metrics_data = self._get_agent_metrics()
                if metrics_data:
                    await self._publish_to_stream("metrics.agent.data", {
                        "agent_id": self.id,
                        "agent_name": self.config.name,
                        "agent_type": self.config.agent_type,
                        "timestamp": time.time(),
                        "metrics": metrics_data
                    })
                    self.logger.debug("Published agent metrics.", agent_name=self.config.name)
            except Exception as e:
                self.logger.error("Error in metrics publisher", agent_name=self.config.name, error=str(e), traceback=traceback.format_exc())
                await asyncio.sleep(self.config.heartbeat_interval)

    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Agents should override this to provide specific metrics."""
        return {
            "current_load": self.active_tasks,
            "status": self.status.value,
            "uptime_seconds": time.time() - self.start_time,
            "total_tasks_processed": self.total_tasks_processed,
            "avg_task_response_time": sum(self._task_response_times) / len(self._task_response_times) if self._task_response_times else 0.0,
            "task_success_rate": sum(1 for s in self._task_success_rates if s) / len(self._task_success_rates) if self._task_success_rates else 1.0,
            "last_error": self.last_error
        }

    async def _handle_task_request(self, msg):
        with self.tracer.start_as_current_span("handle_task_request") as span:
            task_start_time = time.time()
            request_data = json.loads(msg.data.decode())
            request = TaskRequest(**request_data)
            
            span.set_attribute("task.id", request.task_id)
            span.set_attribute("task.type", request.task_type)
            span.set_attribute("agent.name", self.config.name)

            self.logger.info("Received task", task_id=request.task_id, task_type=request.task_type)
            
            # Check if agent is overloaded
            if self.active_tasks >= self.config.max_concurrent_tasks:
                error_msg = f"Agent {self.config.name} is overloaded. Max concurrent tasks: {self.config.max_concurrent_tasks}"
                self.logger.warning(error_msg, task_id=request.task_id)
                response = TaskResponse(
                    task_id=request.task_id,
                    success=False,
                    error=error_msg
                )
                await self._publish(msg.reply, json.dumps(asdict(response)).encode())
                return

            self.active_tasks += 1
            self.active_tasks_gauge.add(1, {"agent_name": self.config.name, "agent_type": self.config.agent_type})

            task_response = None
            try:
                # Execute the agent's specific task implementation
                result = await self._execute_task_impl(request)
                task_response = TaskResponse(
                    task_id=request.task_id,
                    success=True,
                    result=result
                )
            except Exception as e:
                self.logger.error("Error processing task", task_id=request.task_id, error=str(e), traceback=traceback.format_exc())
                self.last_error = str(e)
                task_response = TaskResponse(
                    task_id=request.task_id,
                    success=False,
                    error=str(e)
                )
            finally:
                self.active_tasks -= 1
                self.active_tasks_gauge.add(-1, {"agent_name": self.config.name, "agent_type": self.config.agent_type})
                self.total_tasks_processed += 1
                self.task_counter.add(1, {"agent_name": self.config.name, "agent_type": self.config.agent_type, "task_type": request.task_type, "success": str(task_response.success if task_response else False)})

                response_time = (time.time() - task_start_time) * 1000 # in ms
                self._task_response_times.append(response_time)
                self._task_success_rates.append(task_response.success if task_response else False)
                self.task_duration.record(response_time / 1000, {"agent_name": self.config.name, "agent_type": self.config.agent_type, "task_type": request.task_type})

                span.set_attribute("task.success", task_response.success if task_response else False)
                span.set_attribute("task.execution_time_ms", response_time)

                if msg.reply:
                    # Ensure task_response.execution_time_ms is set before sending
                    task_response.execution_time_ms = response_time
                    await self._publish(msg.reply, json.dumps(asdict(task_response)).encode())
                
                # Publish task completion to a stream for Orchestrator/MetricsAgent
                await self._publish_to_stream("task.completed", asdict(task_response))

    @abc.abstractmethod
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Agents MUST override this method with their core logic."""
        pass

    def shutdown(self):
        self._shutdown_event.set()


if __name__ == "__main__":
    # Example of a simple agent inheriting from BaseAgent
    class MySimpleAgent(BaseAgent):
        def __init__(self, config: AgentConfig):
            super().__init__(config)
            self.processed_messages = 0

        async def start(self):
            self.logger.info("MySimpleAgent is ready to process tasks.", agent_name=self.config.name)

        async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
            self.logger.info("MySimpleAgent processing task", task_type=request.task_type, payload=request.payload)
            self.processed_messages += 1
            await asyncio.sleep(1) # Simulate work
            return {"status": "processed", "agent": self.config.name, "processed_count": self.processed_messages}

        def _get_agent_metrics(self) -> Dict[str, Any]:
            base_metrics = super()._get_agent_metrics()
            base_metrics["processed_messages_total"] = self.processed_messages
            return base_metrics

    config = AgentConfig(
        name="simple_agent_1",
        agent_type="simple",
        capabilities=["process_data"],
        nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://user:password@host:port/db"),
        log_level="DEBUG"
    )

    agent = MySimpleAgent(config)
    asyncio.run(agent.run())

