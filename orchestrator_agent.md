# Orchestrator Agent Documentation

## Overview

The `OrchestratorAgent` is the central coordination unit of the multi-agent platform. Its primary role is to receive high-level task requests, break them down into sub-tasks, and delegate these sub-tasks to the appropriate specialized agents. It monitors the execution of these sub-tasks, aggregates their results, and reports the overall progress and outcome of the original request.

## Features

*   **Task Decomposition**: Breaks down complex user requests into a series of manageable sub-tasks.
*   **Intelligent Delegation**: Routes sub-tasks to the most suitable agents based on their capabilities and current load.
*   **Workflow Management**: Manages the sequence and dependencies of sub-tasks, ensuring proper execution flow.
*   **State Management**: Maintains the state of ongoing tasks and sub-tasks, including progress, results, and errors.
*   **Error Handling & Retries**: Implements strategies for handling failures in sub-tasks, including retries and alternative routing.
*   **Result Aggregation**: Collects and synthesizes results from multiple agents to form a comprehensive final output.
*   **Scalability**: Designed to handle a large volume of concurrent tasks by leveraging asynchronous processing and NATS messaging.

## Task Flow

1.  **Receive Task Request**: The `OrchestratorAgent` receives a `TaskRequest` (typically from the API Gateway) with a high-level `task_type` and `payload`.
2.  **Plan Execution**: Based on the `task_type`, the Orchestrator determines the sequence of agents and sub-tasks required. This can involve predefined workflows or dynamic planning.
3.  **Delegate Sub-tasks**: For each sub-task, the Orchestrator creates a new `TaskRequest` and publishes it to the target agent's NATS subject (e.g., `agent.llm_agent.task`).
4.  **Monitor Progress**: The Orchestrator listens for `TaskResponse` messages from agents, updating the status of its internal tasks.
5.  **Handle Dependencies**: It ensures that dependent sub-tasks are only initiated once their prerequisites are met.
6.  **Aggregate Results**: Once all sub-tasks are completed, the Orchestrator collects their results and combines them into a final `TaskResponse` for the original request.
7.  **Report Status**: Updates the task status in the database and sends a final `TaskResponse` back to the requester.

## NATS Communication

### Subjects

*   **`agent.orchestrator_agent.task`**: Subscribes to this subject to receive new high-level task requests.
*   **`agent.<target_agent_name>.task`**: Publishes `TaskRequest` messages to specific agents.
*   **`agent.<target_agent_name>.response`**: Listens for `TaskResponse` messages from agents.

### Message Formats

Refer to `nats_messaging.md` and `base_agent.md` for detailed `TaskRequest` and `TaskResponse` message formats.

## Database Interactions

The `OrchestratorAgent` interacts with the `tasks` table in the PostgreSQL database to persist the state of all tasks it manages. This ensures that task progress is not lost and can be resumed if the agent restarts.

## Configuration

The `OrchestratorAgent` uses the `AgentConfig` for its base configuration. Specific settings can be managed via the `ConfigManager`.

## Example Workflow (Simplified)

Consider a request to "Generate a blog post about AI ethics and publish it."

1.  **Orchestrator receives `create_blog_post` task.**
2.  **Delegates to `LLMAgent`**: Requests `generate_content` for the blog post draft.
3.  **Delegates to `EnhancementAgent`**: Requests `enhance_content` for grammar, style, and readability.
4.  **Delegates to `ExaminationAgent`**: Requests `review_content` for factual accuracy and tone compliance.
5.  **Delegates to `DraftingAgent`**: Requests `export_document` to format the final blog post.
6.  **Delegates to `CommunicationAgent`**: Requests `publish_content` to a blog platform.
7.  **Orchestrator aggregates results** from each step and returns a final status.

## Deployment

The `OrchestratorAgent` should be deployed as a standalone service. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections.

```bash
python orchestrator_agent.py
```

Refer to `README.md` for Docker Compose deployment examples.

