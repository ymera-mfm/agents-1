# NATS Messaging Documentation

## Overview

NATS is a high-performance, lightweight, and secure messaging system used for inter-agent communication within the multi-agent platform. It provides a publish-subscribe (Pub/Sub) model, enabling agents to communicate asynchronously without direct coupling. This design promotes scalability, resilience, and modularity.

## Key Concepts

*   **Subjects**: Messages in NATS are published to and subscribed from subjects. Subjects are hierarchical and can use wildcards for flexible routing.
*   **Publish/Subscribe**: Agents publish messages to subjects, and any agent subscribed to that subject receives the message.
*   **Request/Reply**: NATS supports a request/reply pattern, allowing agents to send a request and receive a response from another agent.
*   **Queue Groups**: For Pub/Sub, multiple subscribers can form a queue group. When a message is published to a subject, only one member of the queue group will receive the message, distributing the load.

## Agent Communication Pattern

All agents inherit from `BaseAgent`, which provides standardized methods for NATS communication.

### Task Submission (Request/Reply)

Agents submit tasks to other agents using a request/reply pattern. The `BaseAgent`'s `_publish_task` method is used for this purpose.

*   **Subject Pattern**: `agent.<target_agent_name>.task`
*   **Message Format**: A JSON object representing a `TaskRequest` dataclass.

    ```json
    {
        "task_id": "<unique_task_id>",
        "task_type": "<specific_task_type>",
        "payload": { ... },
        "priority": "<priority_enum_value>"
    }
    ```

*   **Response Format**: A JSON object representing a `TaskResponse` dataclass.

    ```json
    {
        "task_id": "<unique_task_id>",
        "status": "<TaskStatus_enum_value>",
        "result": { ... },
        "error": "<error_message>"
    }
    ```

**Example: Orchestrator sending a task to LLM Agent**

```python
await self._publish_task(
    agent_name="llm_agent",
    task_type="generate_text",
    payload={
        "prompt": "Write a short story about an AI agent.",
        "max_tokens": 200
    },
    priority=Priority.NORMAL
)
```

### Event Broadcasting (Publish/Subscribe)

Agents can broadcast events or notifications to other interested agents using the publish-subscribe model. The `BaseAgent`'s `_publish` method is used for this.

*   **Subject Examples**:
    *   `platform.events.agent_registered`
    *   `platform.events.task_completed`
    *   `chat.message.new` (used by `LiveChattingManager`)
    *   `enhancement.feedback` (used by `EnhancementAgent`)

*   **Message Format**: Typically a JSON object containing event-specific data.

**Example: LiveChattingManager broadcasting a new chat message**

```python
await self._publish(
    "chat.message.new",
    json.dumps({
        "session_id": chat_message.session_id,
        "message_id": chat_message.id,
        "content": chat_message.content
    }).encode()
)
```

### Subscribing to Subjects

Agents subscribe to subjects to receive messages. The `BaseAgent`'s `_subscribe` method handles this.

**Example: An agent subscribing to task requests**

```python
await self._subscribe(
    f"agent.{self.config.name}.task",
    self._handle_task_request # Callback function
)
```

## NATS Server Configuration

The NATS server URL is configured via the `NATS_URL` environment variable (e.g., `nats://nats:4222`).

## Best Practices

*   **Clear Subject Naming**: Use descriptive and hierarchical subject names (e.g., `service.component.event`).
*   **Schema Validation**: Define and validate message schemas to ensure data consistency.
*   **Error Handling**: Implement robust error handling for message processing and NATS connection issues.
*   **Idempotency**: Design message handlers to be idempotent where possible, especially for tasks that might be retried.
*   **Security**: NATS supports various security features (TLS, authentication). Ensure these are configured for production deployments.

