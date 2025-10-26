# Base Agent Documentation

## Overview

The `BaseAgent` class serves as the foundational blueprint for all agents within the multi-agent platform. It encapsulates common functionalities and establishes a standardized communication and operational framework. By inheriting from `BaseAgent`, new agents can quickly integrate into the platform, leveraging pre-built features for messaging, logging, metrics, and database interactions.

## Core Responsibilities

*   **NATS Communication**: Provides methods for publishing messages, subscribing to subjects, and handling request/reply patterns via NATS.
*   **Logging**: Integrates a structured logger for consistent and observable logging across all agents.
*   **Metrics**: Collects and publishes operational metrics to the `MetricsAgent` for performance monitoring and analysis.
*   **Database Connectivity**: Manages a connection pool to the PostgreSQL database, enabling agents to persist and retrieve data asynchronously.
*   **Configuration Management**: Fetches and updates agent-specific configurations from the `ConfigManager`.
*   **Lifecycle Management**: Handles agent startup, shutdown, and graceful termination.
*   **Health Checks**: Provides basic health check mechanisms.

## Key Components and Methods

### `AgentConfig` Dataclass

This dataclass defines the configuration parameters for each agent.

| Field Name        | Type        | Description                                                               |
|-------------------|-------------|---------------------------------------------------------------------------|
| `name`            | `str`       | Unique name of the agent (e.g., "orchestrator_agent")                     |
| `agent_type`      | `str`       | General category of the agent (e.g., "orchestration", "llm")              |
| `capabilities`    | `List[str]` | List of specific functionalities the agent can perform                    |
| `nats_url`        | `str`       | URL for the NATS server                                                   |
| `postgres_url`    | `str`       | URL for the PostgreSQL database                                           |
| `redis_url`       | `str`       | URL for the Redis server (for caching/state management)                   |
| `consul_url`      | `str`       | URL for the Consul server (for service discovery/config)                  |
| `log_level`       | `str`       | Logging level (e.g., "INFO", "DEBUG", "ERROR")                          |
| `settings`        | `Dict[str, Any]` | Agent-specific settings, dynamically loaded from `ConfigManager`        |

### `TaskRequest` and `TaskResponse` Dataclasses

These define the standardized format for inter-agent task communication.

*   **`TaskRequest`**:

    | Field Name        | Type        | Description                                                               |
    |-------------------|-------------|---------------------------------------------------------------------------|
    | `task_id`         | `str`       | Unique identifier for the task                                            |
    | `task_type`       | `str`       | Specific operation to be performed by the target agent                    |
    | `payload`         | `Dict[str, Any]` | Input data for the task                                                   |
    | `priority`        | `Priority`  | Priority level of the task (Enum: `LOW`, `NORMAL`, `HIGH`, `CRITICAL`)  |
    | `requester_id`    | `str`       | ID of the agent or service that initiated the task                        |
    | `created_at`      | `float`     | Timestamp of task creation                                                |

*   **`TaskResponse`**:

    | Field Name        | Type        | Description                                                               |
    |-------------------|-------------|---------------------------------------------------------------------------|
    | `task_id`         | `str`       | Corresponding task ID from the request                                    |
    | `status`          | `TaskStatus`| Current status of the task (Enum: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`) |
    | `success`         | `bool`      | Indicates if the task completed successfully                              |
    | `result`          | `Optional[Dict[str, Any]]` | Output data if successful                                             |
    | `error`           | `Optional[str]` | Error message if the task failed                                          |
    | `completed_at`    | `Optional[float]` | Timestamp of task completion                                              |

### NATS Methods

*   `await _publish(subject: str, payload: bytes)`: Publishes a raw byte payload to a NATS subject.
*   `await _subscribe(subject: str, handler: Callable)`: Subscribes to a NATS subject with a given handler function.
*   `await _publish_task(agent_name: str, task_type: str, payload: Dict, priority: Priority = Priority.NORMAL)`: Sends a `TaskRequest` to another agent and awaits a `TaskResponse`.

### Database Methods

*   `self.db_pool`: An `asyncpg` connection pool for asynchronous database operations.

### Metrics Methods

*   `_publish_metric(metric_name: str, value: Union[int, float], tags: Optional[Dict] = None)`: Publishes a metric to the `MetricsAgent`.
*   `_get_agent_metrics()`: Returns a dictionary of common agent metrics (uptime, task counts, etc.).

## Agent Implementation Guide

To create a new agent:

1.  **Inherit from `BaseAgent`**: `class MyNewAgent(BaseAgent):`
2.  **Initialize in `__init__`**: Call `super().__init__(config)` and initialize any agent-specific attributes.
3.  **Implement `start()`**: Override the `start()` method to define agent-specific NATS subscriptions and background tasks.
4.  **Implement `_execute_task_impl(request: TaskRequest)`**: This abstract method must be implemented to define the core logic for handling incoming `TaskRequest`s. It should parse the `task_type` and `payload` to perform the requested operation and return a result.
5.  **Define `AgentConfig`**: Create an `AgentConfig` instance for your agent, specifying its name, type, capabilities, and environment variables.
6.  **Run the Agent**: Use `asyncio.run(agent.run())` in the `if __name__ == "__main__":` block to start the agent.

## Example Usage

```python
import asyncio
import os
from typing import Dict, Any
from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, TaskStatus

class ExampleAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.processed_count = 0

    async def start(self):
        await super().start()
        self.logger.info(f"ExampleAgent {self.config.name} started.")

    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        self.logger.info(f"Received task: {request.task_type} with payload: {request.payload}")
        
        if request.task_type == "process_data":
            data = request.payload.get("data")
            if data:
                processed_data = f"Processed: {data.upper()}"
                self.processed_count += 1
                await self._publish_metric("data_processed_count", 1, {"agent": self.config.name})
                return TaskResponse(task_id=request.task_id, status=TaskStatus.COMPLETED, success=True, result={"processed_data": processed_data}).dict()
            else:
                return TaskResponse(task_id=request.task_id, status=TaskStatus.FAILED, success=False, error="No data provided").dict()
        else:
            return TaskResponse(task_id=request.task_id, status=TaskStatus.FAILED, success=False, error=f"Unknown task type: {request.task_type}").dict()

    def _get_agent_metrics(self) -> Dict[str, Any]:
        base_metrics = super()._get_agent_metrics()
        base_metrics.update({
            "processed_data_total": self.processed_count
        })
        return base_metrics

if __name__ == "__main__":
    config = AgentConfig(
        name="example_agent",
        agent_type="utility",
        capabilities=["process_data"],
        nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://user:password@localhost:5432/db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://localhost:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )
    agent = ExampleAgent(config)
    asyncio.run(agent.run())
```

