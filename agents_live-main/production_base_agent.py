"""
Production-Ready Base Agent v3.0
Core framework for all specialized agents with enterprise-grade reliability
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from contextlib import asynccontextmanager
import traceback

# Optional dependencies - NATS
# Optional dependencies - gracefully handle missing packages
try:
    import nats
    from nats.errors import Error as NatsError
    HAS_NATS = True
except ImportError:
    nats = None
    NatsError = Exception
    HAS_NATS = False

# Optional dependencies - PostgreSQL
    NatsError = Exception  # Fallback to base Exception
    HAS_NATS = False

try:
    import asyncpg
    from asyncpg.pool import Pool
    HAS_ASYNCPG = True
except ImportError:
    asyncpg = None
    Pool = None
    HAS_ASYNCPG = False

# Optional dependencies - Redis
try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    aioredis = None
    HAS_REDIS = False

# Optional dependencies - OpenTelemetry
try:
    from opentelemetry import trace, metrics
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    metrics = None
    PrometheusMetricReader = None
    MeterProvider = None
    TracerProvider = None
    SimpleSpanProcessor = None
    HAS_OPENTELEMETRY = False


class AgentState(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


class Priority(Enum):
    """Task priority levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class AgentConfig:
    """Agent configuration"""
    agent_id: str
    name: str
    agent_type: str
    capabilities: List[str]
    
    # Connectivity
    nats_url: str = "nats://localhost:4222"
    postgres_url: Optional[str] = None
    redis_url: Optional[str] = None
    consul_url: Optional[str] = None
    
    # Performance
    max_concurrent_tasks: int = 50
    task_timeout_seconds: int = 300
    heartbeat_interval_seconds: int = 30
    status_publish_interval_seconds: int = 60
    queue_size: int = 1000
    
    # Features
    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_caching: bool = True
    
    # Version
    version: str = "3.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class TaskRequest:
    """Task request structure"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.MEDIUM
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: str  # success, failed, timeout, error
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseAgent(ABC):
    """Production-ready base agent with enterprise features"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.INITIALIZING
        
        # Logging
        self.logger = self._setup_logging()
        
        # Connections
        self.nc: Optional[Any] = None
        self.db_pool: Optional[Any] = None
        self.redis_client: Optional[Any] = None
        
        # Observability
        self.tracer = trace.get_tracer(__name__) if HAS_OPENTELEMETRY else None
        self.meter = metrics.get_meter(__name__) if HAS_OPENTELEMETRY else None
        
        # Task management
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=config.queue_size)
        self.background_tasks: Set[asyncio.Task] = set()
        self.shutdown_event = asyncio.Event()
        
        # Metrics
        self.metrics = AgentMetrics(config.name)
        
        # Subscriptions
        self.subscriptions: Dict[str, nats.Subscription] = {}
        
        self.logger.info(f"Agent {config.name} initialized", config=config.to_dict())
    
    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging"""
        logger = logging.getLogger(f"agent.{self.config.name}")
        logger.setLevel(logging.INFO)
        
        # Console handler with structured format
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def start(self) -> bool:
        """Start the agent"""
        try:
            self.logger.info(f"Starting {self.config.name}")
            
            # Connect to NATS
            if not await self._connect_nats():
                return False
            
            # Connect to PostgreSQL
            if self.config.postgres_url:
                if not await self._connect_postgres():
                    return False
            
            # Connect to Redis
            if self.config.redis_url:
                if not await self._connect_redis():
                    return False
            
            # Setup subscriptions
            await self._setup_subscriptions()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.state = AgentState.READY
            self.logger.info(f"{self.config.name} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start {self.config.name}: {e}", exc_info=True)
            self.state = AgentState.DEGRADED
            return False
    
    async def _connect_nats(self) -> bool:
        """Connect to NATS with retry logic"""
        if not HAS_NATS:
            self.logger.warning("NATS not available, skipping connection")
            return False
            
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self.nc = await nats.connect(self.config.nats_url)
                self.logger.info("Connected to NATS")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"NATS connection failed, retrying in {retry_delay}s",
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.logger.error(f"Failed to connect to NATS after {max_retries} attempts")
                    return False
        
        return False
    
    async def _connect_postgres(self) -> bool:
        """Connect to PostgreSQL"""
        if not HAS_ASYNCPG:
            self.logger.warning("asyncpg not available, skipping PostgreSQL connection")
            return False
            
        try:
            self.db_pool = await asyncpg.create_pool(
                self.config.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            self.logger.info("Connected to PostgreSQL")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}", exc_info=True)
            return False
    
    async def _connect_redis(self) -> bool:
        """Connect to Redis"""
        if not HAS_REDIS:
            self.logger.warning("Redis not available, skipping connection")
            return False
            
        try:
            self.redis_client = await aioredis.from_url(self.config.redis_url)
            await self.redis_client.ping()
            self.logger.info("Connected to Redis")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            return False
    
    async def _setup_subscriptions(self):
        """Setup NATS subscriptions - override in subclasses"""
        pass
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Heartbeat task
        task = asyncio.create_task(self._heartbeat_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Status publish task
        task = asyncio.create_task(self._status_publish_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Task processor
        task = asyncio.create_task(self._task_processor())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _subscribe(
        self,
        subject: str,
        callback: Callable,
        queue_group: Optional[str] = None
    ):
        """Subscribe to NATS subject"""
        if not HAS_NATS or not self.nc:
            self.logger.warning(f"Cannot subscribe to {subject}: NATS not available")
            return
        
        async def message_handler(msg):
            try:
                await callback(msg)
            except Exception as e:
                self.logger.error(
                    f"Error in subscription handler for {subject}: {e}",
                    exc_info=True
                )
        
        sub = await self.nc.subscribe(subject, cb=message_handler, queue=queue_group)
        self.subscriptions[subject] = sub
        self.logger.debug(f"Subscribed to {subject}")
    
    async def _publish(self, subject: str, data: Dict[str, Any] | str | bytes):
        """Publish message to NATS"""
        if not self.nc:
            self.logger.warning(f"Cannot publish to {subject}: NATS not connected")
            return
        
        try:
            if isinstance(data, dict):
                data = json.dumps(data).encode()
            elif isinstance(data, str):
                data = data.encode()
            
            await self.nc.publish(subject, data)
            self.metrics.messages_published += 1
            
        except Exception as e:
            self.logger.error(f"Failed to publish to {subject}: {e}")
            self.metrics.publish_errors += 1
    
    async def _publish_to_stream(self, subject: str, data: Dict[str, Any]):
        """Publish to JetStream"""
        if not self.nc:
            return
        
        try:
            js = self.nc.jetstream()
            await js.publish(subject, json.dumps(data).encode())
        except Exception as e:
            self.logger.error(f"Failed to publish to stream {subject}: {e}")
    
    async def _request(
        self,
        subject: str,
        data: bytes | str,
        timeout: int = 30
    ) -> Optional[Any]:
        """
        Send request and wait for reply.

        Note:
            The return type is `Any` (was previously `nats.Msg`) to allow this function
            to work even when NATS is not available (i.e., when the `nats` package is not installed).
            As a result, callers should check the type of the returned value at runtime
            if type safety is required.
        """
        if not HAS_NATS or not self.nc:
            return None
        
        try:
            if isinstance(data, str):
                data = data.encode()
            
            reply = await self.nc.request(subject, data, timeout=timeout)
            return reply
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Request timeout for {subject}")
            return None
        except Exception as e:
            self.logger.error(f"Request failed for {subject}: {e}")
            return None
    
    @abstractmethod
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle incoming task - implement in subclasses"""
        raise NotImplementedError
    
    async def _task_processor(self):
        """Process queued tasks"""
        self.logger.info("Task processor started")
        
        while self.state in [AgentState.RUNNING, AgentState.READY]:
            try:
                # Get task from queue with timeout
                try:
                    priority, task_request = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=5
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check if we can accept more tasks
                if len(self.active_tasks) >= self.config.max_concurrent_tasks:
                    # Re-queue task
                    await self.task_queue.put((priority, task_request))
                    await asyncio.sleep(0.1)
                    continue
                
                # Process task
                task = asyncio.create_task(
                    self._execute_task_with_timeout(task_request)
                )
                self.active_tasks[task_request.task_id] = task
                
            except Exception as e:
                self.logger.error(f"Task processor error: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        self.logger.info("Task processor stopped")
    
    async def _execute_task_with_timeout(self, task_request: TaskRequest):
        """Execute task with timeout handling"""
        task_id = task_request.task_id
        start_time = time.time()
        
        try:
            with self.tracer.start_as_current_span(f"task.{task_request.task_type}") as span:
                span.set_attribute("task_id", task_id)
                span.set_attribute("task_type", task_request.task_type)
                
                # Execute with timeout
                try:
                    result = await asyncio.wait_for(
                        self._handle_task(task_request),
                        timeout=task_request.timeout_seconds
                    )
                    
                    status = "success"
                    error = None
                    
                except asyncio.TimeoutError:
                    self.logger.error(f"Task {task_id} timed out")
                    result = None
                    status = "timeout"
                    error = "Task execution timeout"
                
                # Create result
                execution_time_ms = (time.time() - start_time) * 1000
                task_result = TaskResult(
                    task_id=task_id,
                    status=status,
                    result=result,
                    error=error,
                    execution_time_ms=execution_time_ms,
                    started_at=start_time,
                    completed_at=time.time()
                )
                
                # Persist result
                await self._persist_task_result(task_result)
                
                # Update metrics
                self.metrics.tasks_completed += 1
                self.metrics.tasks_succeeded += 1 if status == "success" else 0
                self.metrics.avg_processing_time_ms = (
                    (self.metrics.avg_processing_time_ms * (self.metrics.tasks_completed - 1) + 
                     execution_time_ms) / self.metrics.tasks_completed
                )
                
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}", exc_info=True)
            
            task_result = TaskResult(
                task_id=task_id,
                status="error",
                error=str(e),
                error_traceback=traceback.format_exc(),
                execution_time_ms=(time.time() - start_time) * 1000,
                started_at=start_time,
                completed_at=time.time()
            )
            
            await self._persist_task_result(task_result)
            
            self.metrics.tasks_completed += 1
            self.metrics.tasks_failed += 1
        
        finally:
            # Remove from active tasks
            self.active_tasks.pop(task_id, None)
    
    async def _persist_task_result(self, result: TaskResult):
        """Persist task result to database"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO task_results 
                       (task_id, agent_id, status, result, error, execution_time_ms, 
                        started_at, completed_at, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                       ON CONFLICT (task_id) DO NOTHING""",
                    result.task_id,
                    self.config.agent_id,
                    result.status,
                    json.dumps(result.result) if result.result else None,
                    result.error,
                    result.execution_time_ms,
                    datetime.fromtimestamp(result.started_at) if result.started_at else None,
                    datetime.fromtimestamp(result.completed_at) if result.completed_at else None,
                    datetime.now()
                )
        except Exception as e:
            self.logger.error(f"Failed to persist task result: {e}")
    
    async def _db_fetch(self, query: str, *args) -> List[Dict]:
        """Fetch rows from database"""
        if not self.db_pool:
            return []
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            return []
    
    async def _db_fetch_one(self, query: str, *args) -> Optional[Dict]:
        """Fetch single row from database"""
        rows = await self._db_fetch(query, *args)
        return rows[0] if rows else None
    
    async def _db_execute(self, query: str, *args) -> Optional[str]:
        """Execute query without returning rows"""
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            self.logger.error(f"Database execute failed: {e}")
            return None
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat"""
        self.logger.info("Heartbeat loop started")
        
        while self.state != AgentState.STOPPED:
            try:
                if self.state == AgentState.RUNNING:
                    heartbeat_data = {
                        "agent_id": self.config.agent_id,
                        "agent_name": self.config.name,
                        "status": self.state.value,
                        "timestamp": time.time(),
                        "metrics": {
                            "tasks_completed": self.metrics.tasks_completed,
                            "tasks_failed": self.metrics.tasks_failed,
                            "active_tasks": len(self.active_tasks),
                            "queue_size": self.task_queue.qsize()
                        }
                    }
                    
                    await self._publish("agent.heartbeat", heartbeat_data)
                
                await asyncio.sleep(self.config.heartbeat_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("Heartbeat loop stopped")
    
    async def _status_publish_loop(self):
        """Publish agent status periodically"""
        self.logger.info("Status publish loop started")
        
        while self.state != AgentState.STOPPED:
            try:
                if self.state == AgentState.RUNNING:
                    status = {
                        "agent_id": self.config.agent_id,
                        "agent_name": self.config.name,
                        "state": self.state.value,
                        "version": self.config.version,
                        "capabilities": self.config.capabilities,
                        "metrics": asdict(self.metrics),
                        "timestamp": time.time()
                    }
                    
                    await self._publish_to_stream(
                        f"agent.status.{self.config.name}",
                        status
                    )
                
                await asyncio.sleep(self.config.status_publish_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Status publish error: {e}")
                await asyncio.sleep(10)
        
        self.logger.info("Status publish loop stopped")
    
    async def run_forever(self):
        """Run agent indefinitely"""
        self.state = AgentState.RUNNING
        self.logger.info(f"{self.config.name} running")
        
        try:
            # Wait for shutdown signal
            await self.shutdown_event.wait()
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the agent"""
        self.logger.info(f"Stopping {self.config.name}")
        self.state = AgentState.SHUTTING_DOWN
        
        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for background tasks
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.cancel()
        
        await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        # Unsubscribe from all subjects
        for sub in self.subscriptions.values():
            await sub.unsubscribe()
        
        # Close connections
        if self.redis_client:
            await self.redis_client.close()
        
        if self.db_pool:
            await self.db_pool.close()
        
        if self.nc:
            await self.nc.close()
        
        self.state = AgentState.STOPPED
        self.logger.info(f"{self.config.name} stopped")


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    agent_name: str
    tasks_completed: int = 0
    tasks_succeeded: int = 0
    tasks_failed: int = 0
    avg_processing_time_ms: float = 0.0
    messages_published: int = 0
    publish_errors: int = 0
    last_update: float = field(default_factory=time.time)


if __name__ == "__main__":
    print("Base agent module - import in your engine implementations")
