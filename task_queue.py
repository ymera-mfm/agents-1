"""
Async Task Queue
Background task processing with priority support
"""

import asyncio
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import structlog

logger = structlog.get_logger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents an async task"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retries: int = 0
    max_retries: int = 3


class AsyncTaskQueue:
    """
    Async task queue with priority support
    
    Features:
    - Priority-based execution
    - Multiple workers
    - Task retry logic
    - Result retrieval
    - Task cancellation
    - Performance metrics
    
    Usage:
        queue = AsyncTaskQueue(workers=5)
        await queue.start()
        
        task_id = await queue.submit(my_func, arg1, arg2, priority=TaskPriority.HIGH)
        result = await queue.get_result(task_id, timeout=60)
    """
    
    def __init__(self, workers: int = 5):
        self.workers = workers
        self.queue = asyncio.PriorityQueue()
        self.tasks: Dict[str, Task] = {}
        self.running = False
        self.worker_tasks: list = []
        
        # Metrics
        self.metrics = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "total_execution_time": 0.0
        }
    
    async def start(self):
        """Start processing tasks"""
        if self.running:
            logger.warning("Task queue already running")
            return
        
        self.running = True
        self.worker_tasks = [
            asyncio.create_task(self._worker(i))
            for i in range(self.workers)
        ]
        
        logger.info(f"Task queue started with {self.workers} workers")
    
    async def stop(self, timeout: float = 30):
        """Stop processing tasks"""
        self.running = False
        
        # Wait for workers to finish with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.worker_tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Task queue shutdown timeout - cancelling workers")
            for task in self.worker_tasks:
                task.cancel()
        
        logger.info("Task queue stopped")
    
    async def submit(
        self,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """
        Submit task to queue
        
        Args:
            func: Async function to execute
            *args: Function arguments
            priority: Task priority
            max_retries: Maximum retry attempts
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        task = Task(
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries
        )
        
        self.tasks[task.task_id] = task
        self.metrics["tasks_submitted"] += 1
        
        # Add to queue (negative priority for correct ordering - higher priority first)
        await self.queue.put((-priority.value, task.task_id))
        
        logger.debug(
            "Task submitted",
            task_id=task.task_id,
            priority=priority.name,
            queue_size=self.queue.qsize()
        )
        
        return task.task_id
    
    async def get_result(self, task_id: str, timeout: float = 60) -> Any:
        """
        Wait for task result
        
        Args:
            task_id: Task ID
            timeout: Maximum wait time
            
        Returns:
            Task result
            
        Raises:
            TimeoutError: If timeout exceeded
            Exception: If task failed
        """
        start = time.time()
        while time.time() - start < timeout:
            task = self.tasks.get(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            if task.status == TaskStatus.COMPLETED:
                return task.result
            elif task.status == TaskStatus.FAILED:
                raise Exception(f"Task failed: {task.error}")
            elif task.status == TaskStatus.CANCELLED:
                raise Exception("Task was cancelled")
            
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"Task {task_id} timeout after {timeout}s")
    
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "priority": task.priority.name,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "retries": task.retries,
            "error": task.error
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            self.metrics["tasks_cancelled"] += 1
            logger.info(f"Task {task_id} cancelled")
            return True
        
        return False
    
    async def _worker(self, worker_id: int):
        """Worker that processes tasks"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get task from queue with timeout
                try:
                    _, task_id = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                task = self.tasks.get(task_id)
                if not task or task.status == TaskStatus.CANCELLED:
                    continue
                
                # Execute task
                await self._execute_task(task, worker_id)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _execute_task(self, task: Task, worker_id: int):
        """Execute a task"""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        logger.info(
            "Task execution started",
            task_id=task.task_id,
            worker_id=worker_id,
            priority=task.priority.name
        )
        
        try:
            # Execute function
            result = await task.func(*task.args, **task.kwargs)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()
            
            execution_time = task.completed_at - task.started_at
            self.metrics["tasks_completed"] += 1
            self.metrics["total_execution_time"] += execution_time
            
            logger.info(
                "Task execution completed",
                task_id=task.task_id,
                worker_id=worker_id,
                execution_time=f"{execution_time:.2f}s"
            )
            
        except Exception as e:
            task.error = str(e)
            task.retries += 1
            
            # Retry if under limit
            if task.retries < task.max_retries:
                task.status = TaskStatus.PENDING
                await self.queue.put((-task.priority.value, task.task_id))
                
                logger.warning(
                    "Task failed, retrying",
                    task_id=task.task_id,
                    error=str(e)[:200],
                    retries=task.retries,
                    max_retries=task.max_retries
                )
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = time.time()
                self.metrics["tasks_failed"] += 1
                
                logger.error(
                    "Task execution failed",
                    task_id=task.task_id,
                    error=str(e)[:200],
                    retries=task.retries
                )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get queue metrics"""
        avg_execution_time = (
            self.metrics["total_execution_time"] / self.metrics["tasks_completed"]
            if self.metrics["tasks_completed"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "queue_size": self.queue.qsize(),
            "active_tasks": sum(
                1 for t in self.tasks.values()
                if t.status == TaskStatus.RUNNING
            ),
            "avg_execution_time": avg_execution_time,
            "workers": self.workers
        }
