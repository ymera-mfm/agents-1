"""
YMERA Message Broker
Event-driven messaging with Kafka
"""

import asyncio
import logging
import json
from typing import Dict, Any, Callable, List
from datetime import datetime
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)


class MessageBroker:
    """Message broker for event-driven architecture"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize message broker"""
        self.config = config
        self.bootstrap_servers = config.get("bootstrap_servers", ["localhost:9092"])
        self.consumer_group = config.get("consumer_group", "ymera-consumers")
        
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.handlers: Dict[str, List[Callable]] = {}
        
        self.initialized = False
        
        logger.info(f"Message broker initialized with servers: {self.bootstrap_servers}")
    
    async def initialize(self):
        """Initialize Kafka connections"""
        try:
            # Initialize producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            
            self.initialized = True
            logger.info("Message broker initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize message broker: {str(e)}")
            raise
    
    async def publish(self, topic: str, message: Dict[str, Any]):
        """Publish a message to a topic"""
        if not self.initialized or not self.producer:
            logger.warning("Message broker not initialized, skipping publish")
            return
        
        try:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()
            
            # Send message
            await self.producer.send_and_wait(topic, message)
            logger.debug(f"Published message to topic: {topic}")
            
        except KafkaError as e:
            logger.error(f"Failed to publish message to {topic}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {str(e)}")
    
    async def subscribe(self, topic: str, handler: Callable):
        """Subscribe to a topic with a handler"""
        if not self.initialized:
            logger.warning("Message broker not initialized")
            return
        
        try:
            # Add handler
            if topic not in self.handlers:
                self.handlers[topic] = []
            self.handlers[topic].append(handler)
            
            # Create consumer if not exists
            if topic not in self.consumers:
                consumer = AIOKafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.consumer_group,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                )
                await consumer.start()
                self.consumers[topic] = consumer
                
                # Start consumption task
                asyncio.create_task(self._consume_messages(topic))
            
            logger.info(f"Subscribed to topic: {topic}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {str(e)}")
    
    async def _consume_messages(self, topic: str):
        """Consume messages from a topic"""
        consumer = self.consumers.get(topic)
        if not consumer:
            return
        
        try:
            async for message in consumer:
                # Call all handlers for this topic
                handlers = self.handlers.get(topic, [])
                for handler in handlers:
                    try:
                        await handler(message.value)
                    except Exception as e:
                        logger.error(f"Error in message handler: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error consuming messages from {topic}: {str(e)}")
    
    async def close(self):
        """Close all connections"""
        if self.producer:
            await self.producer.stop()
        
        for consumer in self.consumers.values():
            await consumer.stop()
        
        self.initialized = False
        logger.info("Message broker closed")
