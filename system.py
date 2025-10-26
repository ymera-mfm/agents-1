"""
YMERA Production System - Main Orchestrator
Integrates all components into a cohesive production-ready system
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid

try:
    from config import Settings as Config
except ImportError:
    Config = None

try:
    from logger import setup_logging
except ImportError:
    def setup_logging(*args, **kwargs):
        pass
from learning.engine import LearningEngine, LearningTaskType
from learning.knowledge_base import KnowledgeBase
from learning.pattern_recognition import PatternRecognitionEngine
from learning.continuous_learning import ContinuousLearningEngine
from learning.external_learning import ExternalLearningIntegrator
from infrastructure.monitoring import MonitoringService
from infrastructure.message_broker import MessageBroker

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """System status enumeration"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class SystemMetrics:
    """System-level metrics"""
    uptime_seconds: float
    total_tasks_processed: int
    active_tasks: int
    patterns_detected: int
    knowledge_entries: int
    error_rate: float
    avg_task_duration: float
    cpu_usage: float
    memory_usage: float
    

class YMERASystem:
    """
    YMERA Production Learning System
    Main orchestrator that integrates all components
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the YMERA system"""
        self.config = config or Config()
        self.logger = setup_logging(self.config)
        self.system_id = str(uuid.uuid4())
        self.status = SystemStatus.INITIALIZING
        self.start_time = None
        
        # Core components
        self.learning_engine: Optional[LearningEngine] = None
        self.knowledge_base: Optional[KnowledgeBase] = None
        self.pattern_recognition: Optional[PatternRecognitionEngine] = None
        self.continuous_learning: Optional[ContinuousLearningEngine] = None
        self.external_learning: Optional[ExternalLearningIntegrator] = None
        
        # Infrastructure components
        self.monitoring: Optional[MonitoringService] = None
        self.message_broker: Optional[MessageBroker] = None
        
        # Metrics
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_patterns": 0,
            "total_knowledge_entries": 0
        }
        
        logger.info(f"YMERA System {self.system_id} created with config")
    
    async def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing YMERA Production System...")
            self.status = SystemStatus.INITIALIZING
            self.start_time = datetime.utcnow()
            
            # Initialize infrastructure first
            await self._initialize_infrastructure()
            
            # Initialize learning components
            await self._initialize_learning_components()
            
            # Wire components together
            await self._wire_components()
            
            # Perform health checks
            await self._health_check()
            
            self.status = SystemStatus.RUNNING
            logger.info("YMERA System initialized successfully")
            
            # Publish system ready event
            if self.message_broker:
                await self.message_broker.publish("system.initialized", {
                    "system_id": self.system_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "config": self.config.to_dict()
                })
            
        except Exception as e:
            self.status = SystemStatus.ERROR
            logger.error(f"Failed to initialize system: {str(e)}", exc_info=True)
            raise
    
    async def _initialize_infrastructure(self):
        """Initialize infrastructure components"""
        logger.info("Initializing infrastructure...")
        
        # Initialize monitoring
        self.monitoring = MonitoringService(self.config.monitoring)
        await self.monitoring.initialize()
        
        # Initialize message broker
        self.message_broker = MessageBroker(self.config.kafka)
        await self.message_broker.initialize()
        
        logger.info("Infrastructure initialized")
    
    async def _initialize_learning_components(self):
        """Initialize learning components"""
        logger.info("Initializing learning components...")
        
        # Learning Engine
        self.learning_engine = LearningEngine(self.config.learning_engine.to_dict())
        
        # Knowledge Base
        self.knowledge_base = KnowledgeBase(self.config.knowledge_base.to_dict())
        await self.knowledge_base.initialize_storage()
        
        # Pattern Recognition
        self.pattern_recognition = PatternRecognitionEngine(self.config.pattern_recognition.to_dict())
        
        # Continuous Learning
        self.continuous_learning = ContinuousLearningEngine(self.config.continuous_learning.to_dict())
        
        # External Learning
        self.external_learning = ExternalLearningIntegrator(self.config.external_learning.to_dict())
        
        logger.info("Learning components initialized")
    
    async def _wire_components(self):
        """Wire components together"""
        logger.info("Wiring components...")
        
        # Inject dependencies into learning engine
        self.learning_engine.set_pattern_recognizer(self.pattern_recognition)
        self.learning_engine.set_knowledge_base(self.knowledge_base)
        self.learning_engine.set_message_broker(self.message_broker)
        
        # Inject dependencies into continuous learning
        self.continuous_learning.set_learning_engine(self.learning_engine)
        self.continuous_learning.set_knowledge_base(self.knowledge_base)
        self.continuous_learning.set_pattern_recognizer(self.pattern_recognition)
        
        # Inject dependencies into external learning
        self.external_learning.set_learning_engine(self.learning_engine)
        self.external_learning.set_knowledge_base(self.knowledge_base)
        
        logger.info("Components wired successfully")
    
    async def _health_check(self):
        """Perform system health check"""
        logger.info("Performing health check...")
        
        checks = {
            "learning_engine": self.learning_engine is not None,
            "knowledge_base": self.knowledge_base is not None,
            "pattern_recognition": self.pattern_recognition is not None,
            "continuous_learning": self.continuous_learning is not None,
            "external_learning": self.external_learning is not None,
            "monitoring": self.monitoring is not None,
            "message_broker": self.message_broker is not None
        }
        
        failed_checks = [name for name, passed in checks.items() if not passed]
        
        if failed_checks:
            raise RuntimeError(f"Health check failed for: {', '.join(failed_checks)}")
        
        logger.info("Health check passed")
    
    async def submit_learning_task(
        self, 
        task_type: str,
        data: Any,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit a learning task to the system
        
        Args:
            task_type: Type of learning task
            data: Input data
            config: Task configuration
            
        Returns:
            Task ID
        """
        if self.status != SystemStatus.RUNNING:
            raise RuntimeError(f"System is not running (status: {self.status.value})")
        
        try:
            # Convert string to enum
            task_type_enum = LearningTaskType(task_type)
            
            # Submit to learning engine
            task_id = await self.learning_engine.submit_task(task_type_enum, data, config)
            
            # Update metrics
            self.metrics["total_tasks"] += 1
            
            # Record in monitoring
            if self.monitoring:
                await self.monitoring.record_metric("tasks_submitted", 1, {"task_type": task_type})
            
            logger.info(f"Task {task_id} submitted successfully")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit task: {str(e)}", exc_info=True)
            self.metrics["failed_tasks"] += 1
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = await self.learning_engine.get_task_status(task_id)
        if task:
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "type": task.task_type.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "metrics": task.metrics,
                "error": task.error
            }
        return None
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result"""
        task = await self.learning_engine.get_task_status(task_id)
        if task and task.status.value == "completed":
            return {
                "task_id": task.task_id,
                "success": True,
                "metrics": task.metrics,
                "model_path": f"/models/{task.task_id}/model.pkl"
            }
        elif task and task.status.value == "failed":
            return {
                "task_id": task.task_id,
                "success": False,
                "error": task.error
            }
        return None
    
    async def query_knowledge(
        self, 
        query: Dict[str, Any],
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base"""
        results = await self.knowledge_base.search(query, category, tags, limit)
        return [entry.to_dict() for entry in results]
    
    async def get_patterns(
        self,
        pattern_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get detected patterns"""
        from learning.pattern_recognition import PatternType
        
        pattern_type_enum = PatternType(pattern_type) if pattern_type else None
        patterns = await self.pattern_recognition.get_all_patterns(pattern_type_enum)
        return [pattern.to_dict() for pattern in patterns]
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get comprehensive system metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        
        learning_metrics = await self.learning_engine.get_metrics_summary()
        pattern_stats = await self.pattern_recognition.get_pattern_statistics()
        knowledge_stats = await self.knowledge_base.get_statistics()
        
        # Calculate error rate
        total_tasks = self.metrics["total_tasks"]
        failed_tasks = self.metrics["failed_tasks"]
        error_rate = failed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        return SystemMetrics(
            uptime_seconds=uptime,
            total_tasks_processed=total_tasks,
            active_tasks=learning_metrics.get("running", 0),
            patterns_detected=pattern_stats.get("total_patterns", 0),
            knowledge_entries=knowledge_stats.get("total_entries", 0),
            error_rate=error_rate,
            avg_task_duration=0.0,  # Would calculate from task history
            cpu_usage=0.0,  # Would get from monitoring
            memory_usage=0.0  # Would get from monitoring
        )
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        metrics = await self.get_system_metrics()
        
        return {
            "system_id": self.system_id,
            "status": self.status.value,
            "version": "2.0.0",
            "uptime_seconds": metrics.uptime_seconds,
            "components": {
                "learning_engine": "active" if self.learning_engine else "inactive",
                "knowledge_base": "active" if self.knowledge_base else "inactive",
                "pattern_recognition": "active" if self.pattern_recognition else "inactive",
                "continuous_learning": "active" if self.continuous_learning else "inactive",
                "external_learning": "active" if self.external_learning else "inactive",
            },
            "metrics": {
                "total_tasks": metrics.total_tasks_processed,
                "active_tasks": metrics.active_tasks,
                "patterns_detected": metrics.patterns_detected,
                "knowledge_entries": metrics.knowledge_entries,
                "error_rate": metrics.error_rate
            }
        }
    
    async def enable_continuous_learning(self):
        """Enable continuous learning"""
        if self.continuous_learning:
            await self.continuous_learning.start()
            logger.info("Continuous learning enabled")
    
    async def enable_external_learning(self):
        """Enable external learning integration"""
        if self.external_learning:
            await self.external_learning.start()
            logger.info("External learning enabled")
    
    async def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Shutting down YMERA System...")
        self.status = SystemStatus.STOPPED
        
        # Stop continuous learning
        if self.continuous_learning:
            await self.continuous_learning.stop()
        
        # Stop external learning
        if self.external_learning:
            await self.external_learning.stop()
        
        # Publish shutdown event
        if self.message_broker:
            await self.message_broker.publish("system.shutdown", {
                "system_id": self.system_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Close infrastructure connections
        if self.message_broker:
            await self.message_broker.close()
        
        if self.monitoring:
            await self.monitoring.close()
        
        logger.info("YMERA System shutdown complete")


# Global system instance for singleton access
_system_instance: Optional[YMERASystem] = None


def get_system() -> YMERASystem:
    """Get the global system instance"""
    global _system_instance
    if _system_instance is None:
        _system_instance = YMERASystem()
    return _system_instance
