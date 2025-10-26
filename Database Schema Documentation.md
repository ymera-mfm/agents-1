# Database Schema Documentation

## Overview

This document details the PostgreSQL database schema used by the multi-agent platform. The schema is designed to support the various functionalities of the agents, including task management, chat sessions, message persistence, and configuration storage. It emphasizes data integrity, scalability, and efficient querying.

## Database Tables

### `agents`

Stores information about each registered agent in the system.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `id`              | `TEXT`      | `PRIMARY KEY`           | Unique identifier for the agent (e.g., agent_name) |
| `name`            | `TEXT`      | `NOT NULL`, `UNIQUE`    | Human-readable name of the agent                 |
| `agent_type`      | `TEXT`      | `NOT NULL`              | Type or category of the agent (e.g., 'orchestrator', 'llm') |
| `status`          | `TEXT`      | `NOT NULL`              | Current operational status (e.g., 'active', 'inactive', 'error') |
| `capabilities`    | `TEXT[]`    | `NOT NULL`              | Array of capabilities the agent possesses        |
| `last_heartbeat`  | `TIMESTAMP WITH TIME ZONE` | `NOT NULL` | Timestamp of the last successful heartbeat from the agent |
| `created_at`      | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp when the agent was registered          |
| `updated_at`      | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp of the last update to agent's record   |
| `metadata`        | `JSONB`     | `DEFAULT '{}'`      | Additional JSON metadata for the agent           |

### `tasks`

Records all tasks submitted to agents, their status, and results.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `id`              | `TEXT`      | `PRIMARY KEY`           | Unique identifier for the task                   |
| `agent_id`        | `TEXT`      | `NOT NULL`, `REFERENCES agents(id)` | ID of the agent assigned to the task             |
| `task_type`       | `TEXT`      | `NOT NULL`              | Type of task being executed                      |
| `status`          | `TEXT`      | `NOT NULL`              | Current status of the task (e.g., 'pending', 'running', 'completed', 'failed') |
| `priority`        | `TEXT`      | `NOT NULL`              | Priority level of the task (e.g., 'low', 'normal', 'high') |
| `payload`         | `JSONB`     | `NOT NULL`              | Input data for the task                          |
| `result`          | `JSONB`     | `DEFAULT NULL`          | Output result of the task upon completion        |
| `error`           | `TEXT`      | `DEFAULT NULL`          | Error message if the task failed                 |
| `created_at`      | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp when the task was created              |
| `started_at`      | `TIMESTAMP WITH TIME ZONE` | `DEFAULT NULL`          | Timestamp when the task started execution        |
| `completed_at`    | `TIMESTAMP WITH TIME ZONE` | `DEFAULT NULL`          | Timestamp when the task completed or failed      |
| `metadata`        | `JSONB`     | `DEFAULT '{}'`      | Additional JSON metadata for the task            |

### `api_keys`

Manages API keys for authentication with the API Gateway.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `api_key`         | `TEXT`      | `PRIMARY KEY`           | The API key string                               |
| `owner_id`        | `TEXT`      | `NOT NULL`              | Identifier of the user or service owning the key |
| `permissions`     | `TEXT[]`    | `NOT NULL`              | Array of permissions associated with the key     |
| `is_active`       | `BOOLEAN`   | `NOT NULL`, `DEFAULT TRUE` | Whether the API key is currently active          |
| `created_at`      | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp when the API key was created           |
| `expires_at`      | `TIMESTAMP WITH TIME ZONE` | `DEFAULT NULL`          | Optional expiration date for the API key         |

### `chat_sessions`

Stores information about live chat sessions.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `id`              | `TEXT`      | `PRIMARY KEY`           | Unique identifier for the chat session           |
| `session_type`    | `TEXT`      | `NOT NULL`              | Type of chat session (e.g., 'individual', 'group', 'support') |
| `status`          | `TEXT`      | `NOT NULL`              | Current status of the session (e.g., 'active', 'idle', 'ended') |
| `title`           | `TEXT`      | `NOT NULL`              | Title of the chat session                        |
| `context`         | `JSONB`     | `DEFAULT '{}'`      | JSON object storing session-specific context     |
| `created_at`      | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp when the session was created           |
| `last_activity`   | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp of the last activity in the session    |
| `ended_at`        | `TIMESTAMP WITH TIME ZONE` | `DEFAULT NULL`          | Timestamp when the session ended                 |
| `settings`        | `JSONB`     | `DEFAULT '{}'`      | JSON object for session-specific settings        |
| `conversation_summary` | `TEXT`   | `DEFAULT ''`      | Summary of the conversation (e.g., generated by an AI) |
| `participants`    | `TEXT[]`    | `NOT NULL`              | Array of user IDs participating in the session   |

### `chat_messages`

Stores individual messages within chat sessions.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `id`              | `TEXT`      | `PRIMARY KEY`           | Unique identifier for the message                |
| `session_id`      | `TEXT`      | `NOT NULL`, `REFERENCES chat_sessions(id)` | ID of the chat session the message belongs to    |
| `user_id`         | `TEXT`      | `NOT NULL`              | ID of the user who sent the message              |
| `message_type`    | `TEXT`      | `NOT NULL`              | Type of message (e.g., 'user', 'assistant', 'system') |
| `content`         | `TEXT`      | `NOT NULL`              | The actual content of the message                |
| `timestamp`       | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp when the message was sent              |
| `metadata`        | `JSONB`     | `DEFAULT '{}'`      | Additional JSON metadata for the message         |
| `replied_to`      | `TEXT`      | `DEFAULT NULL`          | Optional ID of the message this message is a reply to |
| `edited_at`       | `TIMESTAMP WITH TIME ZONE` | `DEFAULT NULL`          | Timestamp when the message was last edited       |
| `attachments`     | `TEXT[]`    | `DEFAULT '{}'`      | Array of URLs or IDs of attachments              |

### `agent_configurations`

Stores dynamic configuration settings for agents.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `agent_name`      | `TEXT`      | `PRIMARY KEY`           | Name of the agent                                |
| `config_key`      | `TEXT`      | `PRIMARY KEY`           | Configuration key (e.g., 'llm_model', 'rate_limit') |
| `config_value`    | `TEXT`      | `NOT NULL`              | Configuration value (stored as text, parsed by agent) |
| `last_updated`    | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp of the last update                     |
| `is_active`       | `BOOLEAN`   | `NOT NULL`, `DEFAULT TRUE` | Whether the configuration is active              |

### `metrics`

Stores operational metrics collected from agents.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `id`              | `SERIAL`    | `PRIMARY KEY`           | Auto-incrementing unique ID                      |
| `agent_name`      | `TEXT`      | `NOT NULL`              | Name of the agent reporting the metric           |
| `metric_name`     | `TEXT`      | `NOT NULL`              | Name of the metric (e.g., 'tasks_processed', 'cpu_usage') |
| `metric_value`    | `NUMERIC`   | `NOT NULL`              | The value of the metric                          |
| `timestamp`       | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp when the metric was recorded           |
| `tags`            | `JSONB`     | `DEFAULT '{}'`      | Optional JSON tags for filtering/grouping metrics |

## Relationships

*   `tasks.agent_id` references `agents.id`
*   `chat_messages.session_id` references `chat_sessions.id`

## Indexing Strategy

To ensure optimal performance, the following indexes are recommended:

*   `CREATE INDEX idx_tasks_agent_id ON tasks (agent_id);`
*   `CREATE INDEX idx_tasks_status ON tasks (status);`
*   `CREATE INDEX idx_chat_messages_session_id ON chat_messages (session_id);`
*   `CREATE INDEX idx_chat_messages_timestamp ON chat_messages (timestamp);`
*   `CREATE INDEX idx_agent_configurations_agent_name ON agent_configurations (agent_name);`
*   `CREATE INDEX idx_metrics_agent_name_metric_name ON metrics (agent_name, metric_name);`
*   `CREATE INDEX idx_metrics_timestamp ON metrics (timestamp DESC);`

## Example `database_schema.sql` Content

```sql
-- Enable pgcrypto for UUID generation if needed, though Python's uuid module is used
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Table for registered agents
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    agent_type TEXT NOT NULL,
    status TEXT NOT NULL,
    capabilities TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Table for tasks managed by the orchestrator
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id),
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    payload JSONB NOT NULL,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Table for API keys for gateway authentication
CREATE TABLE IF NOT EXISTS api_keys (
    api_key TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    permissions TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Table for chat sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    session_type TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}'::jsonb,
    conversation_summary TEXT DEFAULT '',
    participants TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[]
);

-- Table for chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    replied_to TEXT,
    edited_at TIMESTAMP WITH TIME ZONE,
    attachments TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- Table for agent configurations
CREATE TABLE IF NOT EXISTS agent_configurations (
    agent_name TEXT NOT NULL,
    config_key TEXT NOT NULL,
    config_value TEXT NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    PRIMARY KEY (agent_name, config_key)
);

-- Table for metrics
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    agent_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    tags JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks (agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages (session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_configurations_agent_name ON agent_configurations (agent_name);
CREATE INDEX IF NOT EXISTS idx_metrics_agent_name_metric_name ON metrics (agent_name, metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics (timestamp DESC);

-- Function to update updated_at column automatically
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for agents table
CREATE OR REPLACE TRIGGER update_agents_timestamp
BEFORE UPDATE ON agents
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Trigger for tasks table (if updated_at was added, otherwise not needed)
-- CREATE OR REPLACE TRIGGER update_tasks_timestamp
-- BEFORE UPDATE ON tasks
-- FOR EACH ROW
-- EXECUTE FUNCTION update_timestamp();

-- Trigger for chat_sessions table
CREATE OR REPLACE TRIGGER update_chat_sessions_timestamp
BEFORE UPDATE ON chat_sessions
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Trigger for chat_messages table (if edited_at is used, updated_at might not be needed)
-- CREATE OR REPLACE TRIGGER update_chat_messages_timestamp
-- BEFORE UPDATE ON chat_messages
-- FOR EACH ROW
-- EXECUTE FUNCTION update_timestamp();

-- Trigger for agent_configurations table
CREATE OR REPLACE TRIGGER update_agent_configurations_timestamp
BEFORE UPDATE ON agent_configurations
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

```

