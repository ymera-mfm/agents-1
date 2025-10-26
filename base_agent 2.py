
import time
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AgentConfig:
    agent_id: str
    name: str
    agent_type: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    config_data: Dict[str, Any] = field(default_factory=dict)
    # Add database connection string
    postgres_url: Optional[str] = None
    nats_url: Optional[str] = None
    redis_url: Optional[str] = None
    system_metrics_interval_seconds: int = 15
    health_check_interval_seconds: int = 60
    alert_processing_interval_seconds: int = 5
    anomaly_detection_interval_seconds: int = 60
    dashboard_aggregation_interval_seconds: int = 30
    cleanup_interval_seconds: int = 3600
    alert_rule_refresh_interval_seconds: int = 3000

@dataclass
class TaskRequest:
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: Priority = Priority.MEDIUM
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(self.config.name)


        self.tracer = None # Placeholder, will be set by actual agent

    async def start(self):
        raise NotImplementedError

    async def stop(self):
        if self.nc:
            await self.nc.close()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.logger.info(f"Agent {self.config.name} stopped.")

    async def _publish(self, topic: str, message: Dict[str, Any]):
        # Placeholder for message publishing logic
        print(f"Publishing to {topic}: {message}")

    async def _subscribe(self, topic: str, handler, queue_group: Optional[str] = None):
        if self.nc:
            if queue_group:
                await self.nc.subscribe(topic, cb=handler, queue=queue_group)
            else:
                await self.nc.subscribe(topic, cb=handler)
            self.logger.info(f"Subscribed to {topic} with queue group {queue_group}" if queue_group else f"Subscribed to {topic}")
        else:
            self.logger.warning(f"NATS client not initialized, cannot subscribe to {topic}")

    async def _handle_message(self, msg):
        # Placeholder for message handling logic
        print(f"Handling message: {msg}")


