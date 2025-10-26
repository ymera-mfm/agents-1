"""
Event Sourcing Implementation
"""
import os
import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List, Literal
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Event Sourcing Implementation
class BaseEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid.uuid4)
    aggregate_id: UUID
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProjectEvent(BaseEvent):
    event_type: Literal["project_created", "project_updated", "project_deleted",
                       "task_added", "task_completed", "member_added"]

class TaskEvent(BaseEvent):
    event_type: Literal["task_created", "task_assigned", "task_started", 
                       "task_completed", "task_failed"]

class UserEvent(BaseEvent):
    event_type: Literal["user_created", "user_updated", "user_deleted",
                       "user_logged_in", "user_logged_out"]

class EventStore:
    def __init__(self):
        self.db = DatabaseUtils()
        self.kafka_producer = self._init_kafka_producer()
    
    def _init_kafka_producer(self):
        """Initialize Kafka producer"""
        try:
            from kafka import KafkaProducer
            return KafkaProducer(
                bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda v: v.encode('utf-8') if v else None
            )
        except ImportError:
            logger.warning("Kafka not available")
            return None
    
    async def append_event(self, event: BaseEvent) -> None:
        """Store event in database and publish to message queue"""
        # Store in database
        async with self.db.get_session() as session:
            event_record = EventRecord(
                id=str(event.event_id),
                aggregate_id=str(event.aggregate_id),
                event_type=event.event_type,
                event_data=event.event_data,
                timestamp=event.timestamp,
                version=event.version,
                metadata=event.metadata
            )
            session.add(event_record)
            await session.commit()
        
        # Publish to Kafka
        if self.kafka_producer:
            try:
                future = self.kafka_producer.send(
                    topic=f"events-{event.event_type}",
                    value=event.dict(),
                    key=str(event.aggregate_id)
                )
                future.get(timeout=10)  # Wait for confirmation
            except Exception as e:
                logger.error(f"Failed to publish event to Kafka: {e}")
                # Implement dead letter queue or retry logic
    
    async def get_events(self, aggregate_id: UUID, 
                       event_type: str = None, 
                       start_version: int = 0) -> List[BaseEvent]:
        """Retrieve events for an aggregate"""
        async with self.db.get_session() as session:
            query = select(EventRecord).where(
                EventRecord.aggregate_id == str(aggregate_id),
                EventRecord.version >= start_version
            )
            
            if event_type:
                query = query.where(EventRecord.event_type == event_type)
            
            result = await session.execute(
                query.order_by(EventRecord.version.asc())
            )
            events = result.scalars().all()
            
            return [BaseEvent(**event.to_dict()) for event in events]
    
    async def create_snapshot(self, aggregate_id: UUID, snapshot_data: Dict[str, Any]) -> None:
        """Create snapshot for aggregate"""
        snapshot_id = str(uuid.uuid4())
        
        async with self.db.get_session() as session:
            snapshot = SnapshotRecord(
                id=snapshot_id,
                aggregate_id=str(aggregate_id),
                snapshot_data=snapshot_data,
                created_at=datetime.utcnow()
            )
            session.add(snapshot)
            await session.commit()

# Message Queue System with Kafka
class MessageQueueSystem:
    def __init__(self):
        self.consumers = {}
        self.init_kafka_consumers()
    
    def init_kafka_consumers(self):
        """Initialize Kafka consumers for different topics"""
        topics = [
            "events-project", "events-task", "events-user",
            "notifications", "audit-logs", "analytics"
        ]
        
        for topic in topics:
            self.consumers[topic] = asyncio.create_task(
                self._kafka_consumer(topic)
            )
    
    async def _kafka_consumer(self, topic: str):
        """Kafka consumer for a specific topic"""
        try:
            from kafka import KafkaConsumer
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(','),
                group_id=f"ymera-{topic}-consumer",
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                enable_auto_commit=False,
                auto_offset_reset='earliest'
            )
            
            for message in consumer:
                try:
                    await self.process_message(topic, message.value)
                    consumer.commit()
                except Exception as e:
                    logger.error(f"Failed to process message from {topic}: {e}")
                    # Send to dead letter queue
                    await self.send_to_dlq(topic, message.value, str(e))
                    
        except ImportError:
            logger.warning("Kafka not available, using in-memory queue")
            # Fallback to in-memory processing
            while True:
                await asyncio.sleep(1)  # Simulate message processing
    
    async def process_message(self, topic: str, message: Dict[str, Any]):
        """Process message based on topic"""
        if topic.startswith("events-"):
            await self.process_event_message(topic, message)
        elif topic == "notifications":
            await self.process_notification_message(message)
        elif topic == "audit-logs":
            await self.process_audit_message(message)
        elif topic == "analytics":
            await self.process_analytics_message(message)
    
    async def process_event_message(self, topic: str, event: Dict[str, Any]):
        """Process event message"""
        event_type = topic.replace("events-", "")
        
        # Update read models, send notifications, trigger workflows
        if event_type == "project_created":
            await self._handle_project_created(event)
        elif event_type == "task_completed":
            await self._handle_task_completed(event)
        # Add other event handlers...
    
    async def _handle_project_created(self, event: Dict[str, Any]):
        """Handle project created event"""
        # Update analytics, send notifications, etc.
        project_id = event["aggregate_id"]
        project_data = event["event_data"]
        
        # Update read model
        await AnalyticsService().index_document("projects", {
            "id": project_id,
            "name": project_data["name"],
            "owner": project_data["owner_id"],
            "created_at": event["timestamp"]
        })
        
        # Send notification to team
        await NotificationService().send_notification(
            project_data["owner_id"],
            f"Project '{project_data['name']}' created successfully",
            channels=["email", "slack"]
        )
    
    async def _handle_task_completed(self, event: Dict[str, Any]):
        """Handle task completed event"""
        task_id = event["aggregate_id"]
        task_data = event["event_data"]
        
        # Update analytics
        await AnalyticsService().index_document("tasks", {
            "id": task_id,
            "project_id": task_data["project_id"],
            "status": "completed",
            "completed_at": event["timestamp"]
        })
        
        # Check if all tasks in project are completed
        # This would trigger project completion workflow
    
    async def send_to_dlq(self, topic: str, message: Dict[str, Any], error: str):
        """Send failed message to dead letter queue"""
        dlq_message = {
            "original_topic": topic,
            "original_message": message,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": 0
        }
        
        # Store in database or publish to DLQ topic
        async with DatabaseUtils.get_session() as session:
            dlq_record = DLQRecord(
                topic=topic,
                message=message,
                error=error,
                retry_count=0
            )
            session.add(dlq_record)
            await session.commit()
    
    async def retry_dlq_messages(self):
        """Retry messages from dead letter queue"""
        while True:
            try:
                async with DatabaseUtils.get_session() as session:
                    # Get messages that haven't been retried too many times
                    result = await session.execute(
                        select(DLQRecord).where(
                            DLQRecord.retry_count < 3,
                            DLQRecord.next_retry_at <= datetime.utcnow()
                        ).order_by(DLQRecord.created_at.asc()).limit(10)
                    )
                    messages = result.scalars().all()
                    
                    for message in messages:
                        try:
                            await self.process_message(message.topic, message.message)
                            await session.delete(message)  # Remove from DLQ
                        except Exception as e:
                            message.retry_count += 1
                            message.next_retry_at = datetime.utcnow() + timedelta(
                                minutes=2 ** message.retry_count  # Exponential backoff
                            )
                            message.last_error = str(e)
                    
                    await session.commit()
                    
            except Exception as e:
                logger.error(f"Failed to retry DLQ messages: {e}")
            
            await asyncio.sleep(60)  # Check every minute

# Saga Pattern Implementation
class SagaManager:
    def __init__(self):
        self.sagas = {}
        self.compensation_actions = {}
    
    async def execute_saga(self, saga_name: str, saga_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a distributed transaction using saga pattern"""
        saga_id = str(uuid.uuid4())
        self.sagas[saga_id] = {
            "name": saga_name,
            "status": "started",
            "current_step": 0,
            "data": saga_data,
            "created_at": datetime.utcnow()
        }
        
        steps = self.get_saga_steps(saga_name)
        compensation_steps = []
        
        try:
            for i, step in enumerate(steps):
                self.sagas[saga_id]["current_step"] = i
                
                # Execute step
                result = await self.execute_saga_step(step, saga_data)
                
                # Store compensation action
                if "compensation" in step:
                    compensation_steps.append({
                        "action": step["compensation"],
                        "data": result
                    })
                
                # Update saga data with step result
                saga_data.update(result)
            
            # Saga completed successfully
            self.sagas[saga_id]["status"] = "completed"
            self.sagas[saga_id]["completed_at"] = datetime.utcnow()
            
            return {"status": "success", "saga_id": saga_id, "data": saga_data}
            
        except Exception as e:
            # Saga failed, execute compensation actions
            logger.error(f"Saga {saga_id} failed at step {i}: {e}")
            self.sagas[saga_id]["status"] = "failed"
            self.sagas[saga_id]["error"] = str(e)
            
            # Execute compensation in reverse order
            for compensation in reversed(compensation_steps):
                try:
                    await self.execute_compensation(compensation["action"], compensation["data"])
                except Exception as comp_error:
                    logger.error(f"Compensation failed: {comp_error}")
                    # Log compensation failure but continue with others
            
            return {"status": "failed", "saga_id": saga_id, "error": str(e)}
    
    def get_saga_steps(self, saga_name: str) -> List[Dict[str, Any]]:
        """Get steps for a saga"""
        sagas = {
            "create_project": [
                {
                    "service": "project-management",
                    "action": "create_project",
                    "compensation": "delete_project"
                },
                {
                    "service": "task-orchestration",
                    "action": "setup_default_tasks",
                    "compensation": "delete_tasks"
                },
                {
                    "service": "notification",
                    "action": "send_project_created_notification"
                }
            ],
            # Add other sagas...
        }
        return sagas.get(saga_name, [])
    
    async def execute_saga_step(self, step: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single saga step"""
        service = MicroService(step["service"])
        action = getattr(service, step["action"])
        
        result = await action(data)
        return result
    
    async def execute_compensation(self, action: str, data: Dict[str, Any]) -> None:
        """Execute compensation action"""
        # Parse service and action from compensation string
        # Format: "service:action"
        service_name, action_name = action.split(":")
        service = MicroService(service_name)
        compensation_action = getattr(service, action_name)
        
        await compensation_action(data)