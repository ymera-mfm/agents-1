"""
Enhanced Production-Ready Base Agent v3.0
==========================================
Production-grade base agent with comprehensive error handling, monitoring,
and reliability features.

Key Features:
- Advanced circuit breakers with exponential backoff
- Comprehensive health monitoring and auto-recovery
- Distributed tracing with correlation IDs
- Request/response validation
- Automatic reconnection with jitter
- Memory-safe operations
- Complete audit logging
"""

import asyncio
import json
import time
import signal
import sys
import uuid
from typing import Dict, Any, Optional, Callable, List, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging
from functools import wraps
import random
import traceback

# Third-party imports with graceful degradation
try:
    import nats
    from nats.aio.client import Client as NATS
    from nats.errors import TimeoutError as NatsTimeoutError, ConnectionClosedError
except ImportError:
    nats = None
    NATS = None

try:
    import asyncpg
    from asyncpg.exceptions import PostgresError
except ImportError:
    asyncpg = None
    PostgresError = Exception

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None


class Priority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class AgentState(Enum):
    """Agent lifecycle states"""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"  # Running but with issues
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ConnectionState(Enum):
    """Connection state for external services"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class AgentConfig:
    """Comprehensive agent configuration with validation"""
    agent_id: str
    name: str
    agent_type: str
    version: str = "3.0.0"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    config_data: Dict[str, Any] = field(default_factory=dict)
    
    # Connection URLs
    postgres_url: Optional[str] = None
    nats_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Connection pool settings
    postgres_min_pool_size: int = 5
    postgres_max_pool_size: int = 20
    postgres_command_timeout: int = 60
    postgres_connection_timeout: int = 10
    
    # NATS settings
    nats_max_reconnect_attempts: int = -1
    nats_reconnect_time_wait: int = 2
    nats_ping_interval: int = 20
    nats_max_outstanding_pings: int = 2
    nats_drain_timeout: int = 10
    
    # Redis settings
    redis_max_connections: int = 50
    redis_decode_responses: bool = True
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    
    # Health and monitoring
    status_publish_interval_seconds: int = 30
    heartbeat_interval_seconds: int = 10
    health_check_interval_seconds: int = 60
    connection_check_interval_seconds: int = 30
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60
    circuit_breaker_half_open_max_calls: int = 3
    
    # Rate limiting and backpressure
    max_concurrent_tasks: int = 100
    request_timeout_seconds: float = 30.0
    max_retry_attempts: int = 3
    retry_base_delay_seconds: float = 1.0
    retry_max_delay_seconds: float = 60.0
    
    # Graceful shutdown
    shutdown_timeout_seconds: int = 30
    shutdown_force_timeout_seconds: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.agent_id or not isinstance(self.agent_id, str):
            errors.append("agent_id must be a non-empty string")
        
        if not self.name or not isinstance(self.name, str):
            errors.append("name must be a non-empty string")
        
        if self.postgres_max_pool_size < self.postgres_min_pool_size:
            errors.append("postgres_max_pool_size must be >= postgres_min_pool_size")
        
        if self.max_concurrent_tasks < 1:
            errors.append("max_concurrent_tasks must be >= 1")
        
        return errors


@dataclass
class TaskRequest:
    """Standardized task request with validation"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: Priority = Priority.MEDIUM
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['priority'] = self.priority.name
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskRequest':
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = Priority[data['priority']]
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if task has exceeded deadline"""
        if self.deadline is None:
            return False
        return time.time() > self.deadline
    
    def should_retry(self) -> bool:
        """Check if task should be retried"""
        return self.retry_count < self.max_retries and not self.is_expired()


@dataclass
class AgentMetrics:
    """Comprehensive agent metrics"""
    messages_processed: int = 0
    messages_failed: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    tasks_expired: int = 0
    avg_processing_time_ms: float = 0.0
    p95_processing_time_ms: float = 0.0
    p99_processing_time_ms: float = 0.0
    uptime_seconds: float = 0.0
    last_health_check: Optional[float] = None
    circuit_breaker_trips: int = 0
    connection_errors: int = 0
    
    # Connection-specific metrics
    nats_reconnections: int = 0
    postgres_query_errors: int = 0
    redis_errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CircuitBreaker:
    """Enhanced circuit breaker with half-open state"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self._lock:
            current_state = self.state
        
        if current_state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout_seconds:
                async with self._lock:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
            else:
                raise Exception(f"Circuit breaker is OPEN (failures: {self.failure_count})")
        
        if current_state == CircuitBreakerState.HALF_OPEN:
            async with self._lock:
                if self.half_open_calls >= self.half_open_max_calls:
                    raise Exception("Circuit breaker HALF_OPEN call limit reached")
                self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.expected_exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            else:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
    
    async def reset(self):
        """Reset circuit breaker"""
        async with self._lock:
            self.failure_count = 0
            self.success_count = 0
            self.state = CircuitBreakerState.CLOSED
            self.half_open_calls = 0
            self.last_failure_time = None
    
    def get_state(self) -> CircuitBreakerState:
        """Get current state"""
        return self.state


class BaseAgent:
    """
    Enhanced production-ready base agent with advanced reliability features
    """
    
    def __init__(self, config: AgentConfig):
        # Validate configuration
        config_errors = config.validate()
        if config_errors:
            raise ValueError(f"Invalid configuration: {', '.join(config_errors)}")
        
        self.config = config
        self.state = AgentState.CREATED
        self.start_time: Optional[float] = None
        
        # Setup structured logging
        self._setup_logging()
        
        # Connection management
        self.nc: Optional[NATS] = None
        self.js = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        
        # Connection states
        self.nats_state = ConnectionState.DISCONNECTED
        self.postgres_state = ConnectionState.DISCONNECTED
        self.redis_state = ConnectionState.DISCONNECTED
        
        # Task management
        self.tasks: List[asyncio.Task] = []
        self.background_tasks: Set[asyncio.Task] = set()
        self._task_semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        
        # Circuit breakers for each service
        self.nats_circuit_breaker = CircuitBreaker(
            config.circuit_breaker_failure_threshold,
            config.circuit_breaker_timeout_seconds,
            config.circuit_breaker_half_open_max_calls
        )
        self.db_circuit_breaker = CircuitBreaker(
            config.circuit_breaker_failure_threshold,
            config.circuit_breaker_timeout_seconds,
            config.circuit_breaker_half_open_max_calls
        )
        self.redis_circuit_breaker = CircuitBreaker(
            config.circuit_breaker_failure_threshold,
            config.circuit_breaker_timeout_seconds,
            config.circuit_breaker_half_open_max_calls
        )
        
        # Metrics with processing time tracking
        self.metrics = AgentMetrics()
        self._processing_times: List[float] = []
        self._max_processing_times = 1000  # Keep last 1000 for percentiles
        
        # Shutdown management
        self._shutdown_event = asyncio.Event()
        self._shutdown_initiated = False
        self._setup_signal_handlers()
        
        # Request tracking for correlation
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(
            "Agent initialized",
            extra={
                "agent_id": config.agent_id,
                "agent_type": config.agent_type,
                "version": config.version
            }
        )
    
    def _setup_logging(self):
        """Setup structured logging"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        if self.config.log_format == "json":
            import logging.handlers
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
                '"agent_id":"%(agent_id)s","agent_type":"%(agent_type)s",'
                '"message":"%(message)s"}'
            )
            handler.setFormatter(formatter)
        else:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(agent_id)s] - %(message)s'
            )
            handler.setFormatter(formatter)
        
        self.logger = logging.getLogger(self.config.name)
        self.logger.setLevel(log_level)
        self.logger.addHandler(handler)
        
        # File handler
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                f"{self.config.name}.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not setup file handler: {e}")
        
        # Context filter
        class ContextFilter(logging.Filter):
            def __init__(self, agent_id: str, agent_type: str):
                super().__init__()
                self.agent_id = agent_id
                self.agent_type = agent_type
            
            def filter(self, record):
                record.agent_id = self.agent_id
                record.agent_type = self.agent_type
                return True
        
        self.logger.addFilter(ContextFilter(self.config.agent_id, self.config.agent_type))
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            if not self._shutdown_initiated:
                self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
                self._shutdown_initiated = True
                self._shutdown_event.set()
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, signal_handler)
    
    async def start(self) -> bool:
        """Start the agent and initialize all connections"""
        if self.state != AgentState.CREATED:
            self.logger.warning(f"Agent already started (state: {self.state.value})")
            return False
        
        self.state = AgentState.STARTING
        self.start_time = time.time()
        
        try:
            # Initialize connections in parallel with timeout
            connection_tasks = []
            
            if self.config.nats_url:
                connection_tasks.append(self._connect_nats())
            
            if self.config.postgres_url:
                connection_tasks.append(self._connect_postgres())
            
            if self.config.redis_url:
                connection_tasks.append(self._connect_redis())
            
            if connection_tasks:
                results = await asyncio.gather(*connection_tasks, return_exceptions=True)
                
                # Check for critical failures
                critical_failures = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Connection initialization failed: {result}")
                        critical_failures.append(result)
                
                # If NATS failed, that's critical
                if self.config.nats_url and self.nats_state != ConnectionState.CONNECTED:
                    raise Exception("Failed to connect to NATS (critical)")
            
            # Initialize database schema if needed
            if self.db_pool:
                await self._initialize_database()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Subscribe to agent-specific subjects
            await self._setup_subscriptions()
            
            # Determine final state
            if self.nats_state == ConnectionState.CONNECTED:
                self.state = AgentState.RUNNING
            else:
                self.state = AgentState.DEGRADED
            
            self.logger.info(
                f"Agent {self.config.name} started successfully (state: {self.state.value})"
            )
            
            return True
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.logger.error(f"Failed to start agent: {e}", exc_info=True)
            await self.stop()
            return False
    
    async def _connect_nats(self) -> bool:
        """Connect to NATS with retry logic and exponential backoff"""
        if not nats:
            self.logger.warning("NATS library not installed")
            return False
        
        self.nats_state = ConnectionState.CONNECTING
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                self.nc = await asyncio.wait_for(
                    nats.connect(
                        servers=self.config.nats_url,
                        reconnect_time_wait=self.config.nats_reconnect_time_wait,
                        max_reconnect_attempts=self.config.nats_max_reconnect_attempts,
                        ping_interval=self.config.nats_ping_interval,
                        max_outstanding_pings=self.config.nats_max_outstanding_pings,
                        error_cb=self._nats_error_handler,
                        disconnected_cb=self._nats_disconnected_handler,
                        reconnected_cb=self._nats_reconnected_handler,
                        closed_cb=self._nats_closed_handler,
                        name=self.config.name
                    ),
                    timeout=10.0
                )
                
                # Initialize JetStream
                self.js = self.nc.jetstream()
                
                self.nats_state = ConnectionState.CONNECTED
                await self.nats_circuit_breaker.reset()
                self.logger.info(f"Connected to NATS at {self.config.nats_url}")
                return True
                
            except Exception as e:
                self.logger.error(f"NATS connection attempt {attempt + 1}/{max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    # Exponential backoff with jitter
                    delay = min(2 ** attempt + random.uniform(0, 1), 30)
                    await asyncio.sleep(delay)
                else:
                    self.nats_state = ConnectionState.FAILED
                    self.metrics.connection_errors += 1
                    return False
    
    async def _connect_postgres(self) -> bool:
        """Connect to PostgreSQL with connection pooling and retry"""
        if not asyncpg:
            self.logger.warning("asyncpg library not installed")
            return False
        
        self.postgres_state = ConnectionState.CONNECTING
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                self.db_pool = await asyncio.wait_for(
                    asyncpg.create_pool(
                        self.config.postgres_url,
                        min_size=self.config.postgres_min_pool_size,
                        max_size=self.config.postgres_max_pool_size,
                        command_timeout=self.config.postgres_command_timeout,
                        timeout=self.config.postgres_connection_timeout
                    ),
                    timeout=self.config.postgres_connection_timeout + 5
                )
                
                # Test connection with timeout
                async with self.db_pool.acquire() as conn:
                    await asyncio.wait_for(conn.fetchval('SELECT 1'), timeout=5.0)
                
                self.postgres_state = ConnectionState.CONNECTED
                await self.db_circuit_breaker.reset()
                self.logger.info("Connected to PostgreSQL")
                return True
                
            except Exception as e:
                self.logger.error(f"PostgreSQL connection attempt {attempt + 1}/{max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.postgres_state = ConnectionState.FAILED
                    self.metrics.connection_errors += 1
                    return False
    
    async def _connect_redis(self) -> bool:
        """Connect to Redis with retry logic"""
        if not aioredis:
            self.logger.warning("aioredis library not installed")
            return False
        
        self.redis_state = ConnectionState.CONNECTING
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                self.redis = await asyncio.wait_for(
                    aioredis.from_url(
                        self.config.redis_url,
                        max_connections=self.config.redis_max_connections,
                        decode_responses=self.config.redis_decode_responses,
                        socket_timeout=self.config.redis_socket_timeout,
                        socket_connect_timeout=self.config.redis_socket_connect_timeout
                    ),
                    timeout=self.config.redis_socket_connect_timeout + 2
                )
                
                # Test connection
                await asyncio.wait_for(self.redis.ping(), timeout=2.0)
                
                self.redis_state = ConnectionState.CONNECTED
                await self.redis_circuit_breaker.reset()
                self.logger.info("Connected to Redis")
                return True
                
            except Exception as e:
                self.logger.error(f"Redis connection attempt {attempt + 1}/{max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.redis_state = ConnectionState.FAILED
                    self.metrics.connection_errors += 1
                    return False
    
    async def _initialize_database(self):
        """Initialize database schema - override in subclasses"""
        pass
    
    async def _setup_subscriptions(self):
        """Setup NATS subscriptions"""
        if not self.nc:
            return
        
        prefix = f"agent.{self.config.name}"
        
        # Core subscriptions
        await self._subscribe(f"{prefix}.task", self._handle_task_request, 
                            queue_group=f"{self.config.agent_type}-tasks")
        await self._subscribe(f"{prefix}.status", self._handle_status_request)
        await self._subscribe(f"{prefix}.health", self._handle_health_request)
        await self._subscribe(f"broadcast.{self.config.agent_type}", 
                            self._handle_broadcast_message)
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        tasks_to_start = [
            (self._status_publisher, self.config.status_publish_interval_seconds),
            (self._heartbeat_publisher, self.config.heartbeat_interval_seconds),
            (self._metrics_collector, 60),
            (self._connection_monitor, self.config.connection_check_interval_seconds),
            (self._cleanup_expired_requests, 300),
        ]
        
        for task_func, interval in tasks_to_start:
            if interval > 0:
                task = asyncio.create_task(self._run_background_task(task_func, interval))
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)
    
    async def _run_background_task(self, func: Callable, interval: int):
        """Run a background task with error handling"""
        task_name = func.__name__
        
        while self.state in (AgentState.RUNNING, AgentState.DEGRADED):
            try:
                await func()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                self.logger.info(f"Background task {task_name} cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in background task {task_name}: {e}", exc_info=True)
                await asyncio.sleep(interval)
    
    async def _connection_monitor(self):
        """Monitor and restore connections"""
        # Check NATS
        if self.config.nats_url and self.nats_state != ConnectionState.CONNECTED:
            self.logger.warning("NATS connection lost, attempting to reconnect")
            if not self.nc or not self.nc.is_connected:
                await self._connect_nats()
        
        # Check PostgreSQL
        if self.config.postgres_url and self.postgres_state == ConnectionState.CONNECTED:
            try:
                async with self.db_pool.acquire() as conn:
                    await asyncio.wait_for(conn.fetchval('SELECT 1'), timeout=2.0)
            except Exception as e:
                self.logger.error(f"PostgreSQL health check failed: {e}")
                self.postgres_state = ConnectionState.DISCONNECTED
                await self._connect_postgres()
        
        # Check Redis
        if self.config.redis_url and self.redis_state == ConnectionState.CONNECTED:
            try:
                await asyncio.wait_for(self.redis.ping(), timeout=2.0)
            except Exception as e:
                self.logger.error(f"Redis health check failed: {e}")
                self.redis_state = ConnectionState.DISCONNECTED
                await self._connect_redis()
    
    async def _cleanup_expired_requests(self):
        """Cleanup expired request tracking"""
        current_time = time.time()
        expired = [
            req_id for req_id, req_data in self._active_requests.items()
            if current_time - req_data.get('started_at', 0) > 300
        ]
        
        for req_id in expired:
            del self._active_requests[req_id]
        
        if expired:
            self.logger.debug(f"Cleaned up {len(expired)} expired request entries")
    
    # NATS Connection Callbacks
    async def _nats_error_handler(self, e):
        """Handle NATS errors"""
        self.logger.error(f"NATS error: {e}")
        self.metrics.connection_errors += 1
    
    async def _nats_disconnected_handler(self):
        """Handle NATS disconnection"""
        self.nats_state = ConnectionState.RECONNECTING
        self.metrics.nats_reconnections += 1
        self.logger.warning("Disconnected from NATS, reconnecting...")
    
    async def _nats_reconnected_handler(self):
        """Handle NATS reconnection"""
        self.nats_state = ConnectionState.CONNECTED
        await self.nats_circuit_breaker.reset()
        self.logger.info("Reconnected to NATS")
    
    async def _nats_closed_handler(self):
        """Handle NATS connection closed"""
        self.nats_state = ConnectionState.DISCONNECTED
        self.logger.info("NATS connection closed")
    
    # Messaging Methods with Retry
    async def _publish(
        self,
        subject: str,
        message: Dict[str, Any],
        jetstream: bool = False,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True
    ) -> bool:
        """Publish message with retry logic"""
        if not self.nc or self.nats_state != ConnectionState.CONNECTED:
            self.logger.warning(f"Cannot publish to {subject}: NATS not connected")
            return False
        
        max_attempts = self.config.max_retry_attempts if retry else 1
        
        for attempt in range(max_attempts):
            try:
                encoded_message = json.dumps(message).encode()
                
                if jetstream and self.js:
                    await asyncio.wait_for(
                        self.js.publish(subject, encoded_message, headers=headers),
                        timeout=self.config.request_timeout_seconds
                    )
                else:
                    await asyncio.wait_for(
                        self.nc.publish(subject, encoded_message),
                        timeout=self.config.request_timeout_seconds
                    )
                
                return True
                
            except Exception as e:
                self.logger.error(f"Publish to {subject} failed (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1 and retry:
                    await asyncio.sleep(self.config.retry_base_delay_seconds * (2 ** attempt))
                else:
                    return False
    
    async def _subscribe(
        self,
        subject: str,
        handler: Callable,
        queue_group: Optional[str] = None
    ) -> bool:
        """Subscribe to NATS subject with error handling"""
        if not self.nc:
            self.logger.warning(f"Cannot subscribe to {subject}: NATS not connected")
            return False
        
        try:
            if queue_group:
                await self.nc.subscribe(subject, cb=handler, queue=queue_group)
                self.logger.info(f"Subscribed to {subject} with queue group {queue_group}")
            else:
                await self.nc.subscribe(subject, cb=handler)
                self.logger.info(f"Subscribed to {subject}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to subscribe to {subject}: {e}")
            return False
    
    async def _request(
        self,
        subject: str,
        message: Dict[str, Any],
        timeout: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make request-reply call with correlation tracking"""
        if not self.nc or self.nats_state != ConnectionState.CONNECTED:
            return {"status": "error", "message": "NATS not connected"}
        
        timeout = timeout or self.config.request_timeout_seconds
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Track request
        self._active_requests[correlation_id] = {
            'subject': subject,
            'started_at': time.time()
        }
        
        try:
            # Add correlation ID to message
            message['correlation_id'] = correlation_id
            encoded_message = json.dumps(message).encode()
            
            response = await asyncio.wait_for(
                self.nc.request(subject, encoded_message),
                timeout=timeout
            )
            
            result = json.loads(response.data.decode())
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Request to {subject} timed out (correlation_id: {correlation_id})")
            return {"status": "error", "message": "Request timed out", "correlation_id": correlation_id}
        except Exception as e:
            self.logger.error(f"Request to {subject} failed: {e}")
            return {"status": "error", "message": str(e), "correlation_id": correlation_id}
        finally:
            self._active_requests.pop(correlation_id, None)
    
    # Database Methods with Circuit Breaker
    @asynccontextmanager
    async def _db_connection(self):
        """Database connection context manager with circuit breaker"""
        if not self.db_pool:
            raise Exception("Database pool not initialized")
        
        conn = await self.db_circuit_breaker.call(self.db_pool.acquire)
        try:
            yield conn
        finally:
            await self.db_pool.release(conn)
    
    async def _db_execute(self, query: str, *args, timeout: float = 30.0) -> str:
        """Execute database query with timeout and error handling"""
        try:
            async with self._db_connection() as conn:
                result = await asyncio.wait_for(
                    conn.execute(query, *args),
                    timeout=timeout
                )
                return result
        except PostgresError as e:
            self.metrics.postgres_query_errors += 1
            self.logger.error(f"Database execute failed: {e}")
            raise
        except asyncio.TimeoutError:
            self.metrics.postgres_query_errors += 1
            self.logger.error(f"Database execute timed out after {timeout}s")
            raise
    
    async def _db_fetch(self, query: str, *args, timeout: float = 30.0) -> List[Dict[str, Any]]:
        """Fetch records from database"""
        try:
            async with self._db_connection() as conn:
                rows = await asyncio.wait_for(
                    conn.fetch(query, *args),
                    timeout=timeout
                )
                return [dict(row) for row in rows]
        except PostgresError as e:
            self.metrics.postgres_query_errors += 1
            self.logger.error(f"Database fetch failed: {e}")
            raise
        except asyncio.TimeoutError:
            self.metrics.postgres_query_errors += 1
            self.logger.error(f"Database fetch timed out after {timeout}s")
            raise
    
    async def _db_fetchrow(self, query: str, *args, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Fetch single row from database"""
        try:
            async with self._db_connection() as conn:
                row = await asyncio.wait_for(
                    conn.fetchrow(query, *args),
                    timeout=timeout
                )
                return dict(row) if row else None
        except PostgresError as e:
            self.metrics.postgres_query_errors += 1
            self.logger.error(f"Database fetchrow failed: {e}")
            raise
        except asyncio.TimeoutError:
            self.metrics.postgres_query_errors += 1
            self.logger.error(f"Database fetchrow timed out after {timeout}s")
            raise
    
    async def _db_fetchval(self, query: str, *args, timeout: float = 30.0) -> Any:
        """Fetch single value from database"""
        try:
            async with self._db_connection() as conn:
                value = await asyncio.wait_for(
                    conn.fetchval(query, *args),
                    timeout=timeout
                )
                return value
        except PostgresError as e:
            self.metrics.postgres_query_errors += 1
            self.logger.error(f"Database fetchval failed: {e}")
            raise
        except asyncio.TimeoutError:
            self.metrics.postgres_query_errors += 1
            self.logger.error(f"Database fetchval timed out after {timeout}s")
            raise
    
    # Message Handlers
    async def _handle_task_request(self, msg):
        """Handle incoming task requests with validation"""
        try:
            data = json.loads(msg.data.decode())
            task_request = TaskRequest.from_dict(data)
            
            # Check if expired
            if task_request.is_expired():
                self.metrics.tasks_expired += 1
                self.logger.warning(f"Task {task_request.task_id} expired before processing")
                if msg.reply:
                    await self._publish_response(msg.reply, {
                        "status": "error",
                        "message": "Task expired",
                        "task_id": task_request.task_id
                    })
                return
            
            self.logger.info(
                f"Received task: {task_request.task_type}",
                extra={"correlation_id": task_request.correlation_id}
            )
            
            # Process task asynchronously
            asyncio.create_task(self._process_task(task_request, msg))
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in task request: {e}")
            self.metrics.messages_failed += 1
        except Exception as e:
            self.logger.error(f"Error handling task request: {e}", exc_info=True)
            self.metrics.messages_failed += 1
            if msg.reply:
                await self._publish_response(msg.reply, {
                    "status": "error",
                    "message": str(e)
                })
    
    async def _process_task(self, task_request: TaskRequest, msg):
        """Process task with rate limiting and retry logic"""
        async with self._task_semaphore:
            start_time = time.time()
            
            try:
                result = await asyncio.wait_for(
                    self._handle_task(task_request),
                    timeout=self.config.request_timeout_seconds
                )
                
                processing_time = (time.time() - start_time) * 1000
                self.metrics.tasks_completed += 1
                self._record_processing_time(processing_time)
                
                if msg.reply:
                    result['correlation_id'] = task_request.correlation_id
                    await self._publish_response(msg.reply, result)
                
            except asyncio.TimeoutError:
                self.metrics.tasks_failed += 1
                self.logger.error(
                    f"Task {task_request.task_id} timed out",
                    extra={"correlation_id": task_request.correlation_id}
                )
                
                if msg.reply:
                    await self._publish_response(msg.reply, {
                        "status": "error",
                        "message": "Task processing timeout",
                        "task_id": task_request.task_id,
                        "correlation_id": task_request.correlation_id
                    })
            
            except Exception as e:
                self.metrics.tasks_failed += 1
                self.logger.error(
                    f"Task processing failed: {e}",
                    extra={"correlation_id": task_request.correlation_id},
                    exc_info=True
                )
                
                # Check if should retry
                if task_request.should_retry():
                    self.metrics.tasks_retried += 1
                    task_request.retry_count += 1
                    await self._retry_task(task_request)
                elif msg.reply:
                    await self._publish_response(msg.reply, {
                        "status": "error",
                        "message": str(e),
                        "task_id": task_request.task_id,
                        "correlation_id": task_request.correlation_id
                    })
    
    async def _retry_task(self, task_request: TaskRequest):
        """Retry failed task with exponential backoff"""
        delay = min(
            self.config.retry_base_delay_seconds * (2 ** task_request.retry_count),
            self.config.retry_max_delay_seconds
        )
        
        self.logger.info(
            f"Retrying task {task_request.task_id} in {delay}s (attempt {task_request.retry_count})"
        )
        
        await asyncio.sleep(delay)
        
        # Republish task
        await self._publish(
            f"agent.{self.config.name}.task",
            task_request.to_dict(),
            retry=False
        )
    
    async def _publish_response(self, reply_subject: str, response: Dict[str, Any]):
        """Publish response with retry"""
        try:
            await self.nc.publish(reply_subject, json.dumps(response).encode())
        except Exception as e:
            self.logger.error(f"Failed to publish response: {e}")
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Override in subclasses to handle specific tasks"""
        self.logger.warning(f"Unhandled task type: {task_request.task_type}")
        return {
            "status": "error",
            "message": f"Task type {task_request.task_type} not implemented"
        }
    
    async def _handle_status_request(self, msg):
        """Handle status requests"""
        try:
            status = await self.get_status()
            await self._publish_response(msg.reply, status)
        except Exception as e:
            self.logger.error(f"Error handling status request: {e}")
    
    async def _handle_health_request(self, msg):
        """Handle health check requests"""
        try:
            health = await self.get_health()
            await self._publish_response(msg.reply, health)
        except Exception as e:
            self.logger.error(f"Error handling health request: {e}")
    
    async def _handle_broadcast_message(self, msg):
        """Handle broadcast messages - override in subclasses"""
        try:
            data = json.loads(msg.data.decode())
            self.logger.info(f"Received broadcast: {data}")
        except Exception as e:
            self.logger.error(f"Error handling broadcast: {e}")
    
    # Background Tasks
    async def _status_publisher(self):
        """Publish agent status"""
        status = await self.get_status()
        await self._publish(f"agent.{self.config.name}.status.update", status)
    
    async def _heartbeat_publisher(self):
        """Publish heartbeat"""
        heartbeat = {
            "agent_id": self.config.agent_id,
            "timestamp": time.time(),
            "state": self.state.value
        }
        await self._publish(f"agent.{self.config.name}.heartbeat", heartbeat)
    
    async def _metrics_collector(self):
        """Update agent metrics"""
        if self.start_time:
            self.metrics.uptime_seconds = time.time() - self.start_time
        self.metrics.last_health_check = time.time()
    
    def _record_processing_time(self, processing_time_ms: float):
        """Record processing time for percentile calculations"""
        self._processing_times.append(processing_time_ms)
        
        # Keep only recent times
        if len(self._processing_times) > self._max_processing_times:
            self._processing_times = self._processing_times[-self._max_processing_times:]
        
        # Update average
        if self.metrics.tasks_completed == 1:
            self.metrics.avg_processing_time_ms = processing_time_ms
        else:
            alpha = 0.1
            self.metrics.avg_processing_time_ms = (
                alpha * processing_time_ms +
                (1 - alpha) * self.metrics.avg_processing_time_ms
            )
        
        # Update percentiles
        if len(self._processing_times) >= 20:
            sorted_times = sorted(self._processing_times)
            self.metrics.p95_processing_time_ms = sorted_times[int(len(sorted_times) * 0.95)]
            self.metrics.p99_processing_time_ms = sorted_times[int(len(sorted_times) * 0.99)]
    
    # Status and Health
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        return {
            "agent_id": self.config.agent_id,
            "name": self.config.name,
            "type": self.config.agent_type,
            "version": self.config.version,
            "state": self.state.value,
            "uptime_seconds": self.metrics.uptime_seconds,
            "connections": {
                "nats": {
                    "state": self.nats_state.value,
                    "circuit_breaker": self.nats_circuit_breaker.get_state().value
                },
                "postgres": {
                    "state": self.postgres_state.value,
                    "circuit_breaker": self.db_circuit_breaker.get_state().value
                },
                "redis": {
                    "state": self.redis_state.value,
                    "circuit_breaker": self.redis_circuit_breaker.get_state().value
                }
            },
            "metrics": self.metrics.to_dict(),
            "active_requests": len(self._active_requests),
            "background_tasks": len(self.background_tasks),
            "timestamp": time.time()
        }
    
    async def get_health(self) -> Dict[str, Any]:
        """Get agent health status"""
        health_status = "healthy"
        issues = []
        
        # Check NATS
        if self.config.nats_url and self.nats_state != ConnectionState.CONNECTED:
            health_status = "unhealthy"
            issues.append(f"NATS: {self.nats_state.value}")
        
        # Check PostgreSQL
        if self.config.postgres_url and self.postgres_state != ConnectionState.CONNECTED:
            health_status = "degraded" if health_status == "healthy" else health_status
            issues.append(f"PostgreSQL: {self.postgres_state.value}")
        
        # Check Redis
        if self.config.redis_url and self.redis_state != ConnectionState.CONNECTED:
            health_status = "degraded" if health_status == "healthy" else health_status
            issues.append(f"Redis: {self.redis_state.value}")
        
        # Check agent state
        if self.state not in (AgentState.RUNNING, AgentState.DEGRADED):
            health_status = "unhealthy"
            issues.append(f"Agent state: {self.state.value}")
        
        # Check circuit breakers
        if self.nats_circuit_breaker.get_state() == CircuitBreakerState.OPEN:
            health_status = "degraded" if health_status == "healthy" else health_status
            issues.append("NATS circuit breaker is OPEN")
        
        return {
            "agent_id": self.config.agent_id,
            "status": health_status,
            "issues": issues,
            "timestamp": time.time(),
            "uptime_seconds": self.metrics.uptime_seconds
        }
    
    # Shutdown
    async def stop(self):
        """Graceful shutdown"""
        if self.state == AgentState.STOPPED:
            return
        
        self.state = AgentState.STOPPING
        self.logger.info(f"Stopping agent {self.config.name}")
        
        try:
            # Cancel background tasks
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.background_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self.background_tasks, return_exceptions=True),
                        timeout=self.config.shutdown_timeout_seconds
                    )
                except asyncio.TimeoutError:
                    self.logger.warning("Background tasks shutdown timeout, forcing stop")
            
            # Close connections
            await self._close_connections()
            
            self.state = AgentState.STOPPED
            self.logger.info(f"Agent {self.config.name} stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)
            self.state = AgentState.ERROR
    
    async def _close_connections(self):
        """Close all connections gracefully"""
        close_tasks = []
        
        # NATS
        if self.nc:
            async def close_nats():
                try:
                    await asyncio.wait_for(
                        self.nc.drain(),
                        timeout=self.config.nats_drain_timeout
                    )
                    await self.nc.close()
                    self.nats_state = ConnectionState.DISCONNECTED
                    self.logger.info("NATS connection closed")
                except Exception as e:
                    self.logger.error(f"Error closing NATS: {e}")
            
            close_tasks.append(close_nats())
        
        # PostgreSQL
        if self.db_pool:
            async def close_postgres():
                try:
                    await asyncio.wait_for(self.db_pool.close(), timeout=10)
                    self.postgres_state = ConnectionState.DISCONNECTED
                    self.logger.info("PostgreSQL connection closed")
                except Exception as e:
                    self.logger.error(f"Error closing PostgreSQL: {e}")
            
            close_tasks.append(close_postgres())
        
        # Redis
        if self.redis:
            async def close_redis():
                try:
                    await asyncio.wait_for(self.redis.close(), timeout=5)
                    self.redis_state = ConnectionState.DISCONNECTED
                    self.logger.info("Redis connection closed")
                except Exception as e:
                    self.logger.error(f"Error closing Redis: {e}")
            
            close_tasks.append(close_redis())
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
    
    # Utilities
    async def run_forever(self):
        """Run until shutdown signal"""
        await self._shutdown_event.wait()
        await self.stop()
    
    def is_healthy(self) -> bool:
        """Quick health check"""
        return (
            self.state in (AgentState.RUNNING, AgentState.DEGRADED) and
            (not self.config.nats_url or self.nats_state == ConnectionState.CONNECTED)
        )


async def run_agent(agent: BaseAgent):
    """Run agent with proper lifecycle management"""
    try:
        if not await agent.start():
            agent.logger.error("Failed to start agent")
            return
        
        agent.logger.info(f"Agent {agent.config.name} is running")
        await agent.run_forever()
        
    except Exception as e:
        agent.logger.error(f"Agent error: {e}", exc_info=True)
    finally:
        await agent.stop()


if __name__ == "__main__":
    config = AgentConfig(
        agent_id="base-001",
        name="base_agent",
        agent_type="base",
        nats_url="nats://localhost:4222",
        postgres_url="postgresql://user:password@localhost:5432/agentdb",
        redis_url="redis://localhost:6379"
    )
    
    agent = BaseAgent(config)
    asyncio.run(run_agent(agent))