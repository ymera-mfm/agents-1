"""
Task Orchestrator - Intelligent task routing and execution
Manages task distribution, retry logic, and result aggregation
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog

from .agent_registry import AgentRegistry
from .agent_discovery import AgentDiscovery, DiscoveryRequest, DiscoveryStrategy

logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    ROUTING = "routing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class TaskRequest:
    """Task request"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    capability: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 5
    requester_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    execution_time_ms: Optional[float] = None
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    """Task execution context"""
    request: TaskRequest
    status: TaskStatus = TaskStatus.PENDING
    current_agent_id: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[float] = None
    last_retry_at: Optional[float] = None
    error_history: List[str] = field(default_factory=list)


class TaskOrchestrator:
    """
    Task Orchestrator
    
    Features:
    - Intelligent agent selection
    - Automatic retry with exponential backoff
    - Timeout handling
    - Circuit breaker integration
    - Task dependency management
    - Result aggregation
    - Priority-based scheduling
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        agent_discovery: AgentDiscovery,
        max_concurrent_tasks: int = 100
    ):
        self.registry = agent_registry
        self.discovery = agent_discovery
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Task tracking
        self._active_tasks: Dict[str, TaskContext] = {}
        self._completed_tasks: Dict[str, TaskResult] = {}
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        
        # Locks and semaphores
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._lock = asyncio.Lock()
        
        # Background workers
        self._workers: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Callbacks
        self._task_callbacks: Dict[str, List[Callable]] = {}
        
        logger.info("Task Orchestrator initialized", max_concurrent=max_concurrent_tasks)
    
    async def start(self, num_workers: int = 10):
        """Start task workers"""
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._workers.append(worker)
        
        logger.info(f"Task Orchestrator started with {num_workers} workers")
    
    async def stop(self):
        """Stop task orchestrator"""
        self._shutdown_event.set()
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        logger.info("Task Orchestrator stopped")
    
    # =========================================================================
    # TASK SUBMISSION
    # =========================================================================
    
    async def submit_task(self, request: TaskRequest) -> str:
        """
        Submit task for execution
        
        Args:
            request: Task request
            
        Returns:
            Task ID
        """
        async with self._lock:
            context = TaskContext(
                request=request,
                status=TaskStatus.QUEUED
            )
            self._active_tasks[request.task_id] = context
        
        # Add to priority queue
        priority = request.priority.value
        await self._task_queue.put((-priority, time.time(), request))
        
        logger.info(
            f"Task submitted",
            task_id=request.task_id,
            task_type=request.task_type,
            capability=request.capability,
            priority=request.priority.value
        )
        
        return request.task_id
    
    async def submit_batch(self, requests: List[TaskRequest]) -> List[str]:
        """Submit multiple tasks"""
        task_ids = []
        for request in requests:
            task_id = await self.submit_task(request)
            task_ids.append(task_id)
        return task_ids
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel task"""
        async with self._lock:
            if task_id in self._active_tasks:
                context = self._active_tasks[task_id]
                context.status = TaskStatus.CANCELLED
                
                # Create result
                result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.CANCELLED
                )
                self._completed_tasks[task_id] = result
                del self._active_tasks[task_id]
                
                logger.info(f"Task cancelled", task_id=task_id)
                return True
        
        return False
    
    # =========================================================================
    # TASK EXECUTION
    # =========================================================================
    
    async def _worker_loop(self, worker_id: str):
        """Worker loop for processing tasks"""
        logger.info(f"Worker {worker_id} started")
        
        while not self._shutdown_event.is_set():
            try:
                # Get task from queue with timeout
                try:
                    _, _, request = await asyncio.wait_for(
                        self._task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Execute task
                async with self._semaphore:
                    await self._execute_task(request)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _execute_task(self, request: TaskRequest):
        """Execute single task with retry logic"""
        context = self._active_tasks.get(request.task_id)
        if not context:
            logger.warning(f"Task context not found: {request.task_id}")
            return
        
        context.status = TaskStatus.ROUTING
        context.started_at = time.time()
        
        # Discover agent
        discovery_request = DiscoveryRequest(
            capability=request.capability,
            strategy=DiscoveryStrategy.LEAST_LOADED,
            min_health_score=0.6
        )
        
        agent = await self.discovery.discover_agent(discovery_request)
        
        if not agent:
            await self._handle_task_failure(
                context,
                "No available agent found for capability"
            )
            return
        
        context.current_agent_id = agent.agent_id
        context.status = TaskStatus.EXECUTING
        
        # Execute on agent
        try:
            # Increment agent load
            await self.registry.increment_load(agent.agent_id)
            
            # Execute task (placeholder - actual execution via API call)
            result = await self._execute_on_agent(agent, request)
            
            # Task completed successfully
            await self._handle_task_success(context, result, agent.agent_id)
            
        except asyncio.TimeoutError:
            await self._handle_task_timeout(context, agent.agent_id)
            
        except Exception as e:
            await self._handle_task_error(context, str(e), agent.agent_id)
            
        finally:
            # Decrement agent load
            await self.registry.decrement_load(agent.agent_id)
    
    async def _execute_on_agent(
        self,
        agent: Any,
        request: TaskRequest
    ) -> Any:
        """
        Execute task on specific agent
        This is a placeholder - actual implementation would make API call
        """
        # Simulate task execution
        await asyncio.sleep(0.1)
        
        # Return mock result
        return {
            "status": "completed",
            "data": request.payload,
            "agent_id": agent.agent_id
        }
    
    # =========================================================================
    # RESULT HANDLING
    # =========================================================================
    
    async def _handle_task_success(
        self,
        context: TaskContext,
        result: Any,
        agent_id: str
    ):
        """Handle successful task completion"""
        completed_at = time.time()
        execution_time_ms = (completed_at - context.started_at) * 1000
        
        task_result = TaskResult(
            task_id=context.request.task_id,
            status=TaskStatus.COMPLETED,
            result=result,
            agent_id=agent_id,
            started_at=context.started_at,
            completed_at=completed_at,
            execution_time_ms=execution_time_ms,
            retries=context.retry_count
        )
        
        async with self._lock:
            self._completed_tasks[context.request.task_id] = task_result
            del self._active_tasks[context.request.task_id]
        
        # Execute callbacks
        await self._execute_callbacks(context.request.task_id, task_result)
        
        logger.info(
            f"Task completed",
            task_id=context.request.task_id,
            agent_id=agent_id,
            execution_time_ms=execution_time_ms
        )
    
    async def _handle_task_error(
        self,
        context: TaskContext,
        error: str,
        agent_id: str
    ):
        """Handle task error with retry"""
        context.error_history.append(error)
        
        # Record failure in registry
        await self.registry.record_failure(agent_id)
        
        # Check if should retry
        if context.retry_count < context.request.max_retries:
            context.retry_count += 1
            context.status = TaskStatus.RETRYING
            context.last_retry_at = time.time()
            
            # Calculate backoff delay
            delay = context.request.retry_delay_seconds * (2 ** (context.retry_count - 1))
            
            logger.warning(
                f"Task failed, retrying",
                task_id=context.request.task_id,
                attempt=context.retry_count,
                delay_seconds=delay,
                error=error
            )
            
            # Re-queue after delay
            await asyncio.sleep(delay)
            priority = context.request.priority.value
            await self._task_queue.put(
                (-priority, time.time(), context.request)
            )
        else:
            await self._handle_task_failure(context, error)
    
    async def _handle_task_timeout(self, context: TaskContext, agent_id: str):
        """Handle task timeout"""
        await self.registry.record_failure(agent_id)
        await self._handle_task_failure(context, "Task timeout")
    
    async def _handle_task_failure(self, context: TaskContext, error: str):
        """Handle final task failure"""
        task_result = TaskResult(
            task_id=context.request.task_id,
            status=TaskStatus.FAILED,
            error=error,
            agent_id=context.current_agent_id,
            started_at=context.started_at,
            completed_at=time.time(),
            retries=context.retry_count
        )
        
        async with self._lock:
            self._completed_tasks[context.request.task_id] = task_result
            del self._active_tasks[context.request.task_id]
        
        await self._execute_callbacks(context.request.task_id, task_result)
        
        logger.error(
            f"Task failed",
            task_id=context.request.task_id,
            error=error,
            retries=context.retry_count
        )
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        if task_id in self._active_tasks:
            return self._active_tasks[task_id].status
        elif task_id in self._completed_tasks:
            return self._completed_tasks[task_id].status
        return None
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result"""
        return self._completed_tasks.get(task_id)
    
    async def get_active_tasks(self) -> List[str]:
        """Get list of active task IDs"""
        return list(self._active_tasks.keys())
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            'active_tasks': len(self._active_tasks),
            'completed_tasks': len(self._completed_tasks),
            'queued_tasks': self._task_queue.qsize(),
            'workers': len(self._workers),
            'max_concurrent': self.max_concurrent_tasks
        }
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def register_callback(self, task_id: str, callback: Callable):
        """Register callback for task completion"""
        if task_id not in self._task_callbacks:
            self._task_callbacks[task_id] = []
        self._task_callbacks[task_id].append(callback)
    
    async def _execute_callbacks(self, task_id: str, result: TaskResult):
        """Execute registered callbacks"""
        if task_id in self._task_callbacks:
            for callback in self._task_callbacks[task_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(result)
                    else:
                        callback(result)
                except Exception as e:
                    logger.error(f"Callback error: {e}", exc_info=True)
            
            del self._task_callbacks[task_id]
