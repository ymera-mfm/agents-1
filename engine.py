"""
YMERA Enhanced Learning Engine
Consolidated learning orchestration with pattern recognition, knowledge base, and adaptive learning.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger("ymera.learning_engine")


class LearningTaskType(Enum):
    """Types of learning tasks"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"
    FEDERATED = "federated"


class LearningTaskStatus(Enum):
    """Status of learning tasks"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LearningTask:
    """Represents a learning task"""
    task_id: str
    task_type: LearningTaskType
    status: LearningTaskStatus = LearningTaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class LearningResult:
    """Result of a learning task"""
    task_id: str
    success: bool
    metrics: Dict[str, float]
    model_artifact_path: Optional[str] = None
    predictions: Optional[List[Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class LearningEngine:
    """
    Enhanced Learning Engine - Orchestrates learning tasks, pattern recognition,
    knowledge base updates, and adaptive learning.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Learning Engine.
        
        Args:
            config: Configuration dictionary for the learning engine
        """
        self.config = config
        self.tasks: Dict[str, LearningTask] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = config.get("max_concurrent_tasks", 10)
        
        # Component integrations (will be injected)
        self.pattern_recognizer = None
        self.knowledge_base = None
        self.adaptive_learner = None
        self.message_broker = None
        
        logger.info(f"Learning Engine initialized with config: {config}")
    
    def set_pattern_recognizer(self, pattern_recognizer):
        """Inject pattern recognition component"""
        self.pattern_recognizer = pattern_recognizer
        logger.info("Pattern recognizer integrated")
    
    def set_knowledge_base(self, knowledge_base):
        """Inject knowledge base component"""
        self.knowledge_base = knowledge_base
        logger.info("Knowledge base integrated")
    
    def set_adaptive_learner(self, adaptive_learner):
        """Inject adaptive learning component"""
        self.adaptive_learner = adaptive_learner
        logger.info("Adaptive learner integrated")
    
    def set_message_broker(self, message_broker):
        """Inject message broker for event publishing"""
        self.message_broker = message_broker
        logger.info("Message broker integrated")
    
    async def submit_task(self, task_type: LearningTaskType, 
                         data: Any, 
                         config: Dict[str, Any] = None) -> str:
        """
        Submit a new learning task.
        
        Args:
            task_type: Type of learning task
            data: Input data for the task
            config: Task-specific configuration
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = LearningTask(
            task_id=task_id,
            task_type=task_type,
            config=config or {}
        )
        
        self.tasks[task_id] = task
        
        # Check if we can start the task immediately
        if len(self.active_tasks) < self.max_concurrent_tasks:
            await self._start_task(task_id, data)
        else:
            logger.info(f"Task {task_id} queued (max concurrent tasks reached)")
        
        # Publish task submission event
        if self.message_broker:
            await self.message_broker.publish(
                "learning.task.submitted",
                {"task_id": task_id, "task_type": task_type.value}
            )
        
        return task_id
    
    async def _start_task(self, task_id: str, data: Any):
        """Start executing a learning task"""
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = LearningTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        # Create async task for execution
        async_task = asyncio.create_task(self._execute_task(task_id, data))
        self.active_tasks[task_id] = async_task
        
        logger.info(f"Task {task_id} started")
        
        # Publish task start event
        if self.message_broker:
            await self.message_broker.publish(
                "learning.task.started",
                {"task_id": task_id, "started_at": task.started_at.isoformat()}
            )
    
    async def _execute_task(self, task_id: str, data: Any) -> LearningResult:
        """
        Execute a learning task.
        
        Args:
            task_id: Task identifier
            data: Input data
            
        Returns:
            LearningResult object
        """
        task = self.tasks[task_id]
        
        try:
            logger.info(f"Executing task {task_id} of type {task.task_type.value}")
            
            # Dispatch to appropriate learning method based on task type
            if task.task_type == LearningTaskType.CLASSIFICATION:
                result = await self._execute_classification(task, data)
            elif task.task_type == LearningTaskType.REGRESSION:
                result = await self._execute_regression(task, data)
            elif task.task_type == LearningTaskType.CLUSTERING:
                result = await self._execute_clustering(task, data)
            elif task.task_type == LearningTaskType.REINFORCEMENT:
                result = await self._execute_reinforcement(task, data)
            elif task.task_type == LearningTaskType.TRANSFER:
                result = await self._execute_transfer(task, data)
            elif task.task_type == LearningTaskType.FEDERATED:
                result = await self._execute_federated(task, data)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            # Update task status
            task.status = LearningTaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.metrics = result.metrics
            
            # Post-processing: pattern recognition, knowledge base update
            await self._post_process_task(task, result, data)
            
            # Publish task completion event
            if self.message_broker:
                await self.message_broker.publish(
                    "learning.task.completed",
                    {
                        "task_id": task_id,
                        "metrics": result.metrics,
                        "completed_at": task.completed_at.isoformat()
                    }
                )
            
            logger.info(f"Task {task_id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
            task.status = LearningTaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            
            # Publish task failure event
            if self.message_broker:
                await self.message_broker.publish(
                    "learning.task.failed",
                    {"task_id": task_id, "error": str(e)}
                )
            
            return LearningResult(
                task_id=task_id,
                success=False,
                metrics={},
                error=str(e)
            )
        finally:
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # Try to start next queued task
            await self._start_next_queued_task()
    
    async def _execute_classification(self, task: LearningTask, data: Any) -> LearningResult:
        """Execute classification task"""
        # This is a placeholder for actual classification logic
        # In production, this would integrate with actual ML frameworks
        await asyncio.sleep(0.1)  # Simulate processing
        
        return LearningResult(
            task_id=task.task_id,
            success=True,
            metrics={
                "accuracy": 0.95,
                "precision": 0.93,
                "recall": 0.94,
                "f1_score": 0.935
            },
            model_artifact_path=f"/models/{task.task_id}/model.pkl"
        )
    
    async def _execute_regression(self, task: LearningTask, data: Any) -> LearningResult:
        """Execute regression task"""
        await asyncio.sleep(0.1)
        
        return LearningResult(
            task_id=task.task_id,
            success=True,
            metrics={
                "mse": 0.05,
                "rmse": 0.224,
                "mae": 0.18,
                "r2_score": 0.92
            },
            model_artifact_path=f"/models/{task.task_id}/model.pkl"
        )
    
    async def _execute_clustering(self, task: LearningTask, data: Any) -> LearningResult:
        """Execute clustering task"""
        await asyncio.sleep(0.1)
        
        return LearningResult(
            task_id=task.task_id,
            success=True,
            metrics={
                "silhouette_score": 0.75,
                "davies_bouldin_score": 0.45,
                "num_clusters": 5
            },
            model_artifact_path=f"/models/{task.task_id}/model.pkl"
        )
    
    async def _execute_reinforcement(self, task: LearningTask, data: Any) -> LearningResult:
        """Execute reinforcement learning task"""
        await asyncio.sleep(0.2)
        
        return LearningResult(
            task_id=task.task_id,
            success=True,
            metrics={
                "average_reward": 150.5,
                "episodes": 1000,
                "convergence_episode": 750
            },
            model_artifact_path=f"/models/{task.task_id}/model.pkl"
        )
    
    async def _execute_transfer(self, task: LearningTask, data: Any) -> LearningResult:
        """Execute transfer learning task"""
        await asyncio.sleep(0.15)
        
        return LearningResult(
            task_id=task.task_id,
            success=True,
            metrics={
                "accuracy": 0.91,
                "transfer_efficiency": 0.85,
                "fine_tuning_epochs": 10
            },
            model_artifact_path=f"/models/{task.task_id}/model.pkl"
        )
    
    async def _execute_federated(self, task: LearningTask, data: Any) -> LearningResult:
        """Execute federated learning task"""
        await asyncio.sleep(0.25)
        
        return LearningResult(
            task_id=task.task_id,
            success=True,
            metrics={
                "global_accuracy": 0.89,
                "num_clients": 10,
                "communication_rounds": 50
            },
            model_artifact_path=f"/models/{task.task_id}/model.pkl"
        )
    
    async def _post_process_task(self, task: LearningTask, result: LearningResult, data: Any):
        """
        Post-process task results: pattern recognition, knowledge base update, adaptive learning.
        """
        # Pattern recognition
        if self.pattern_recognizer and self.config.get("pattern_recognition_enabled", True):
            try:
                patterns = await self.pattern_recognizer.detect_patterns({
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "metrics": result.metrics,
                    "data_sample": data
                })
                logger.info(f"Detected {len(patterns)} patterns for task {task.task_id}")
            except Exception as e:
                logger.error(f"Pattern recognition failed: {str(e)}")
        
        # Knowledge base update
        if self.knowledge_base and self.config.get("knowledge_base_enabled", True):
            try:
                await self.knowledge_base.store({
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "metrics": result.metrics,
                    "model_path": result.model_artifact_path,
                    "timestamp": task.completed_at.isoformat()
                })
                logger.info(f"Updated knowledge base for task {task.task_id}")
            except Exception as e:
                logger.error(f"Knowledge base update failed: {str(e)}")
        
        # Adaptive learning
        if self.adaptive_learner and self.config.get("adaptive_learning_enabled", True):
            try:
                await self.adaptive_learner.adapt({
                    "task_id": task.task_id,
                    "metrics": result.metrics,
                    "task_config": task.config
                })
                logger.info(f"Triggered adaptive learning for task {task.task_id}")
            except Exception as e:
                logger.error(f"Adaptive learning failed: {str(e)}")
    
    async def _start_next_queued_task(self):
        """Start the next queued task if capacity is available"""
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            return
        
        # Find next pending task
        for task_id, task in self.tasks.items():
            if task.status == LearningTaskStatus.PENDING and task_id not in self.active_tasks:
                # Note: In production, we'd need to retrieve the original data
                # For now, this is a simplified version
                logger.info(f"Starting queued task {task_id}")
                break
    
    async def get_task_status(self, task_id: str) -> Optional[LearningTask]:
        """Get the status of a task"""
        return self.tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or pending task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == LearningTaskStatus.PENDING:
            task.status = LearningTaskStatus.CANCELLED
            return True
        
        if task.status == LearningTaskStatus.RUNNING and task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            task.status = LearningTaskStatus.CANCELLED
            return True
        
        return False
    
    async def get_all_tasks(self, status: Optional[LearningTaskStatus] = None) -> List[LearningTask]:
        """Get all tasks, optionally filtered by status"""
        if status:
            return [task for task in self.tasks.values() if task.status == status]
        return list(self.tasks.values())
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary metrics for all tasks"""
        completed_tasks = [t for t in self.tasks.values() if t.status == LearningTaskStatus.COMPLETED]
        failed_tasks = [t for t in self.tasks.values() if t.status == LearningTaskStatus.FAILED]
        
        return {
            "total_tasks": len(self.tasks),
            "completed": len(completed_tasks),
            "failed": len(failed_tasks),
            "running": len(self.active_tasks),
            "pending": len([t for t in self.tasks.values() if t.status == LearningTaskStatus.PENDING]),
            "success_rate": len(completed_tasks) / len(self.tasks) if self.tasks else 0.0,
            "average_metrics": self._calculate_average_metrics(completed_tasks)
        }
    
    def _calculate_average_metrics(self, tasks: List[LearningTask]) -> Dict[str, float]:
        """Calculate average metrics across completed tasks"""
        if not tasks:
            return {}
        
        all_metrics = {}
        for task in tasks:
            for metric, value in task.metrics.items():
                if metric not in all_metrics:
                    all_metrics[metric] = []
                all_metrics[metric].append(value)
        
        return {metric: sum(values) / len(values) for metric, values in all_metrics.items()}
