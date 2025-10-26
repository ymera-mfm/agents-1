# workers/task_worker.py
"""
Distributed task worker for consuming Kafka events and executing tasks.
"""

import asyncio
import json
import logging
from kafka import KafkaConsumer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
import signal
import sys

# Add parent directory to path for imports
sys.path.insert(0, '/home/ubuntu/ymera_project_agent_enhanced')

from app.config import settings
from app.database import TaskModel
from app.schemas import TaskStatus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskWorker:
    """Distributed task worker for processing tasks from Kafka"""
    
    def __init__(self):
        self.running = False
        self.consumer = None
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Initialize worker components"""
        # Initialize database
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            'tasks',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        logger.info("Task worker initialized")
    
    async def process_task(self, task_id: str, task_type: str, parameters: dict):
        """Process a single task based on its type"""
        logger.info(f"Processing task {task_id} of type {task_type}")
        
        # Simulate task processing
        await asyncio.sleep(2)
        
        # Task-specific logic would go here
        if task_type == "data_processing":
            result = await self._process_data_task(parameters)
        elif task_type == "ml_training":
            result = await self._process_ml_task(parameters)
        elif task_type == "report_generation":
            result = await self._process_report_task(parameters)
        else:
            result = {"status": "completed", "message": f"Task type {task_type} processed"}
        
        return result
    
    async def _process_data_task(self, parameters: dict):
        """Process data processing tasks"""
        logger.info("Processing data task")
        # Implement data processing logic
        return {"status": "success", "records_processed": 1000}
    
    async def _process_ml_task(self, parameters: dict):
        """Process ML training tasks"""
        logger.info("Processing ML task")
        # Implement ML training logic
        return {"status": "success", "model_accuracy": 0.95}
    
    async def _process_report_task(self, parameters: dict):
        """Process report generation tasks"""
        logger.info("Processing report task")
        # Implement report generation logic
        return {"status": "success", "report_url": "https://example.com/report.pdf"}
    
    async def update_task_status(self, task_id: str, status: TaskStatus, result: dict = None, error: str = None):
        """Update task status in database"""
        async with self.session_factory() as session:
            try:
                task = await session.get(TaskModel, task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return
                
                task.status = status
                task.updated_at = datetime.utcnow()
                
                if status == TaskStatus.RUNNING:
                    task.started_at = datetime.utcnow()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = datetime.utcnow()
                
                if result:
                    task.result = result
                
                if error:
                    task.error_message = error
                
                await session.commit()
                logger.info(f"Task {task_id} status updated to {status}")
                
            except Exception as e:
                logger.error(f"Failed to update task status: {e}")
                await session.rollback()
    
    async def handle_task_event(self, event: dict):
        """Handle a task event from Kafka"""
        event_type = event.get("event_type")
        task_id = event.get("task_id")
        
        logger.info(f"Received event: {event_type} for task {task_id}")
        
        if event_type == "task.created":
            # Update status to running
            await self.update_task_status(task_id, TaskStatus.RUNNING)
            
            try:
                # Process the task
                result = await self.process_task(
                    task_id,
                    event.get("task_type"),
                    event.get("parameters", {})
                )
                
                # Update status to completed
                await self.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
                
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                await self.update_task_status(task_id, TaskStatus.FAILED, error=str(e))
    
    async def run(self):
        """Main worker loop"""
        self.running = True
        logger.info("Task worker started")
        
        try:
            while self.running:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            event = message.value
                            await self.handle_task_event(event)
                            
                            # Commit offset after successful processing
                            self.consumer.commit()
                            
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            # Don't commit offset on error, message will be reprocessed
                
                # Small sleep to prevent tight loop
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Worker error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown worker gracefully"""
        logger.info("Shutting down task worker")
        self.running = False
        
        if self.consumer:
            self.consumer.close()
        
        if self.engine:
            await self.engine.dispose()
        
        logger.info("Task worker shutdown complete")


# Global worker instance
worker = TaskWorker()


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    asyncio.create_task(worker.shutdown())


async def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize and run worker
    await worker.initialize()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
