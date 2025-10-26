# Config Manager Documentation

## Overview

The `ConfigManager` is a critical component of the multi-agent platform, responsible for centralizing and distributing configuration settings to all agents. It ensures that agents can dynamically fetch and update their operational parameters without requiring restarts, promoting flexibility and ease of management in a microservices architecture.

## Features

*   **Centralized Configuration**: All agent-specific and global configurations are managed in a single location (database).
*   **Dynamic Updates**: Agents can request and receive updated configurations at runtime.
*   **Database Persistence**: Configurations are stored in the PostgreSQL database, ensuring persistence across restarts and easy auditing.
*   **NATS Integration**: Utilizes NATS for broadcasting configuration changes to interested agents.
*   **Consul Integration**: Can optionally integrate with Consul for service discovery and health checks, and potentially for configuration storage (though currently using PostgreSQL for primary config storage).

## How it Works

1.  **Configuration Storage**: Configuration settings are stored in the `agent_configurations` table in the PostgreSQL database.
2.  **Agent Startup**: When an agent starts, it fetches its initial configuration from the `ConfigManager` via a NATS request/reply pattern.
3.  **Dynamic Updates**: The `ConfigManager` can be updated via an API or direct database modification. Upon update, it publishes a `config.update` event to NATS.
4.  **Agent Reaction**: Agents subscribed to `config.update` receive the event and can then request their latest configuration from the `ConfigManager`.

## Database Schema

The `ConfigManager` primarily interacts with the `agent_configurations` table:

### `agent_configurations`

Stores dynamic configuration settings for agents.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `agent_name`      | `TEXT`      | `PRIMARY KEY`           | Name of the agent                                |
| `config_key`      | `TEXT`      | `PRIMARY KEY`           | Configuration key (e.g., \'llm_model\', \'rate_limit\') |
| `config_value`    | `TEXT`      | `NOT NULL`              | Configuration value (stored as text, parsed by agent) |
| `last_updated`    | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp of the last update                     |
| `is_active`       | `BOOLEAN`   | `NOT NULL`, `DEFAULT TRUE` | Whether the configuration is active              |

## NATS Communication

### Subjects

*   **`config.get.<agent_name>`**: Request/Reply subject for an agent to fetch its configuration.
*   **`config.update`**: Publish subject for the `ConfigManager` to broadcast that a configuration has been updated.

### Message Formats

*   **Request (to `config.get.<agent_name>`)**:

    ```json
    {
        "agent_name": "<agent_name>"
    }
    ```

*   **Reply (from `config.get.<agent_name>`)**:

    ```json
    {
        "status": "success",
        "configurations": {
            "config_key_1": "value_1",
            "config_key_2": "value_2"
        }
    }
    ```

*   **Broadcast (to `config.update`)**:

    ```json
    {
        "agent_name": "<agent_name>",
        "updated_keys": ["config_key_1", "config_key_2"],
        "timestamp": <timestamp>
    }
    ```

## Usage by Agents

Agents use the `ConfigManager` through methods provided by the `BaseAgent` class. The `BaseAgent` automatically handles fetching initial configurations and subscribing to updates.

### Example: Getting a setting in an Agent

```python
# In an agent inheriting from BaseAgent
class MyAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.some_setting = self.config.get_setting("my_custom_setting", "default_value")

    async def _handle_config_update(self, msg):
        # This method is automatically called by BaseAgent when a config update is broadcast
        updated_config = await self._get_agent_configurations()
        self.some_setting = updated_config.get("my_custom_setting", self.some_setting)
        self.logger.info(f"Updated my_custom_setting to: {self.some_setting}")
```

## Deployment

The `ConfigManager` runs as a standalone agent. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections. It should be deployed alongside other core infrastructure services.

```bash
python config_manager.py
```

Refer to `README.md` for Docker Compose deployment examples.
