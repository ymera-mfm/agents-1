"""
Simple Base Agent - Importable without external dependencies
This is a lightweight version that agents can import successfully.
"""

import logging
import uuid
import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime
from contextlib import asynccontextmanager

# Optional dependencies - NATS messaging
# Optional dependencies - gracefully handle missing packages
try:
    import nats
    from nats.aio.client import Client as NATS
    from nats.js.api import StreamConfig, ConsumerConfig
    HAS_NATS = True
except ImportError:
    nats = None
    NATS = None
    StreamConfig = None
    ConsumerConfig = None
    HAS_NATS = False

# Optional dependencies - Redis
try:
    from redis import asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    aioredis = None
    HAS_REDIS = False

# Optional dependencies - PostgreSQL
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    asyncpg = None
    HAS_ASYNCPG = False

# Optional dependencies - Consul
try:
    import consul
    HAS_CONSUL = True
except ImportError:
    consul = None
    HAS_CONSUL = False

# Optional dependencies - OpenTelemetry
try:
    import opentelemetry.trace as trace
    from opentelemetry import metrics
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    metrics = None
    JaegerExporter = None
    PrometheusMetricReader = None
    TracerProvider = None
    BatchSpanProcessor = None
    MeterProvider = None
    Resource = None
    HAS_OPENTELEMETRY = False

# Optional dependencies - Prometheus
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    Counter = None
    Histogram = None
    Gauge = None
    start_http_server = None
    HAS_PROMETHEUS = False

# Optional dependencies - Structured logging
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    structlog = None
    HAS_STRUCTLOG = False
# Setup logging
logging.basicConfig(level=logging.INFO)


class AgentStatus(Enum):
    """Agent status."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Priority(Enum):
    """Task priority."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentConfig:
    """Agent configuration."""
    name: str
    version: str = "1.0.0"
    agent_type: str = "generic"
    capabilities: List[str] = field(default_factory=list)
    log_level: str = "INFO"


@dataclass
class TaskRequest:
    """Task request."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.MEDIUM


@dataclass
class TaskResponse:
    """Task response."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    
    def dict(self):
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "result": self.result,
            "error": self.error
        }


class BaseAgent:
    """
    Simple base agent class.
    Provides basic functionality without external dependencies.
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
        if HAS_STRUCTLOG:
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
        else:
            # Fallback to standard logging
            self.logger = logging.getLogger(self.id)
            self.logger.setLevel(getattr(logging, config.log_level, logging.INFO))
        
        # Initialize connections (will be established in connect())
        self.nc: Optional[Any] = None
        self.js = None  # JetStream context
        self.redis: Optional[Any] = None
        self.db_pool: Optional[Any] = None
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
        if not HAS_OPENTELEMETRY:
            if hasattr(self, 'logger'):
                self.logger.warning("OpenTelemetry not available, skipping tracing setup")
            self.tracer = None
            self.meter = None
            self.task_counter = None
            self.task_duration = None
            self.active_tasks_gauge = None
            return
            
        # Resource identification
        resource = Resource.create({
            "service.name": f"ymera-{self.config.name}",
            "service.version": self.config.version,
            "agent.id": self.id,
            "agent.type": self.config.agent_type
        })
        
        # Tracing
        if self.config.enable_tracing and HAS_OPENTELEMETRY:
            tracer_provider = TracerProvider(resource=resource)
            jaeger_exporter = JaegerExporter(
                agent_host_name="jaeger",
                agent_port=6831
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)
            trace.set_tracer_provider(tracer_provider)
            
        self.tracer = trace.get_tracer(__name__) if HAS_OPENTELEMETRY else None
        
        # Metrics
        if HAS_OPENTELEMETRY:
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
        else:
            self.meter = None
            self.task_counter = None
            self.task_duration = None
            self.active_tasks_gauge = None
        
        # Start Prometheus metrics server (if enabled and not already running)
        if self.config.enable_metrics_server and HAS_PROMETHEUS:
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
            if HAS_NATS:
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
            else:
                self.logger.warning("NATS not available, skipping connection")
            
            # Redis connection
            if HAS_REDIS:
                self.redis = aioredis.from_url(
                    self.config.redis_url,
                    encoding="utf8",
                    decode_responses=True
                )
                await self.redis.ping()
                self.logger.info("Redis connected")
            else:
                self.logger.warning("Redis not available, skipping connection")
            
            # PostgreSQL connection pool
            if HAS_ASYNCPG:
                self.db_pool = await asyncpg.create_pool(
                    self.config.postgres_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=30
                )
                self.logger.info("PostgreSQL pool created")
            else:
                self.logger.warning("asyncpg not available, skipping PostgreSQL connection")
            
            # Consul client
            if HAS_CONSUL:
                self.consul_client = consul.Consul(
                    host="consul",
                    port=8500
                )
                
                # Register with service discovery
                await self._register_with_consul()
            else:
                self.logger.warning("Consul not available, skipping service registration")
            
            self.logger.info("All available connections established")
            
        except Exception as e:
            self.logger.error("Failed to establish connections", error=str(e))
            raise
    
    async def _setup_streams(self):
        """Setup required NATS JetStream streams"""
        if not HAS_NATS or not self.js:
            return
            
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
        if not HAS_CONSUL or not self.consul_client:
            return
            
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
        self.name = config.name
        self.logger = logging.getLogger(f"Agent.{self.name}")
        self.logger.setLevel(getattr(logging, config.log_level))
        self._shutdown_event = None  # Placeholder for compatibility
        
        self.logger.info(f"Agent {self.name} initialized")
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """
        Execute task implementation - override in subclasses.
        """
        raise NotImplementedError("Subclasses must implement _execute_task_impl")
    
    async def _subscribe(self, subject: str, handler, queue_group: str = None):
        """Placeholder for compatibility."""
        self.logger.info(f"Subscribe called for {subject}")
    
    async def start(self):
        """Start the agent."""
        self.logger.info(f"Agent {self.name} starting")
    
    @asynccontextmanager
    async def _trace_span(self, name: str):
        """Context manager for optional tracing"""
        if self.tracer and HAS_OPENTELEMETRY:
            async with self.tracer.start_as_current_span(name) as span:
                yield span
        else:
            # Async dummy span-like object for when tracing is disabled
            class AsyncDummySpan:
                async def __aenter__(self): return self
                async def __aexit__(self, exc_type, exc, tb): pass
                def set_attribute(self, *args, **kwargs): pass
                def record_exception(self, *args, **kwargs): pass
                def set_status(self, *args, **kwargs): pass
            async with AsyncDummySpan() as span:
                yield span
    
    async def _subscribe(self, subject: str, callback: Callable, queue_group: Optional[str] = None):
        """Enhanced subscription with error handling and metrics"""
        if not HAS_NATS or not self.nc:
            self.logger.warning("NATS not available, cannot subscribe")
            return
            
        async def wrapped_callback(msg):
            async with self._trace_span(f"message_received_{subject}") as span:
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
        if not HAS_NATS or not self.nc:
            self.logger.warning("NATS not available, cannot publish")
            return
            
        async with self._trace_span(f"message_published_{subject}") as span:
            span.set_attribute("subject", subject)
            span.set_attribute("agent_id", self.id)
            await self.nc.publish(subject, data, reply=reply_to)
            self.logger.debug("Published message", subject=subject)

    async def _publish_to_stream(self, stream_name: str, data: Dict[str, Any]):
        """Publish data to a NATS JetStream stream."""
        if not HAS_NATS or not self.nc:
            self.logger.warning("NATS not available, cannot publish to stream")
            return
            
        async with self._trace_span(f"stream_published_{stream_name}") as span:
            span.set_attribute("stream_name", stream_name)
            span.set_attribute("agent_id", self.id)
            try:
                js = self.nc.jetstream()
                await js.publish(stream_name, json.dumps(data).encode())
                self.logger.debug("Published to stream", stream_name=stream_name)
            except Exception as e:
                self.logger.error("Failed to publish to stream", stream_name=stream_name, error=str(e), traceback=traceback.format_exc())
                span.record_exception(e)
                if HAS_OPENTELEMETRY: span.set_status(trace.Status(trace.StatusCode.ERROR))

    async def _request(self, subject: str, data: bytes, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Send a NATS request and wait for a response"""
        if not HAS_NATS or not self.nc:
            self.logger.warning("NATS not available, cannot send request")
            return None
            
        async with self._trace_span(f"nats_request_{subject}") as span:
            span.set_attribute("subject", subject)
            span.set_attribute("agent_id", self.id)
            try:
                response = await self.nc.request(subject, data, timeout=timeout)
                decoded_response = json.loads(response.data.decode())
                self.logger.debug("NATS request successful", subject=subject)
                return decoded_response
            except Exception as e:
                # Handle nats.errors.TimeoutError if nats is available
                if HAS_NATS and hasattr(nats, 'errors') and isinstance(e, nats.errors.TimeoutError):
                    self.logger.warning("NATS request timed out", subject=subject)
                    if HAS_OPENTELEMETRY: span.set_status(trace.Status(trace.StatusCode.ERROR, "Timeout"))
                else:
                    self.logger.error("NATS request failed", subject=subject, error=str(e), traceback=traceback.format_exc())
                    span.record_exception(e)
                    if HAS_OPENTELEMETRY: span.set_status(trace.Status(trace.StatusCode.ERROR))
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
        async with self._trace_span("handle_task_request") as span:
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
            if self.active_tasks_gauge:
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
                if self.active_tasks_gauge:
                    self.active_tasks_gauge.add(-1, {"agent_name": self.config.name, "agent_type": self.config.agent_type})
                self.total_tasks_processed += 1
                if self.task_counter:
                    self.task_counter.add(1, {"agent_name": self.config.name, "agent_type": self.config.agent_type, "task_type": request.task_type, "success": str(task_response.success if task_response else False)})

                response_time = (time.time() - task_start_time) * 1000 # in ms
                self._task_response_times.append(response_time)
                self._task_success_rates.append(task_response.success if task_response else False)
                if self.task_duration:
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

    async def run(self):
        """Run the agent."""
        await self.start()
        self.logger.info(f"Agent {self.name} running")


# Export for compatibility
__all__ = [
    'BaseAgent',
    'AgentConfig',
    'TaskRequest',
    'TaskResponse',
    'Priority',
    'AgentStatus',
    'TaskStatus'
]
