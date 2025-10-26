# Metrics Agent Documentation

## Overview

The `MetricsAgent` is responsible for collecting, aggregating, and exposing operational metrics from all agents within the multi-agent platform. It acts as a central hub for platform observability, providing insights into agent performance, resource utilization, and overall system health. This agent is crucial for monitoring, debugging, and optimizing the platform.

## Features

*   **Metric Collection**: Receives metrics published by other agents via NATS.
*   **Aggregation**: Aggregates metrics over time or by specific tags.
*   **Persistence**: Stores metrics in the PostgreSQL database for historical analysis and dashboarding.
*   **Exposure**: Can expose metrics via a Prometheus-compatible endpoint or other monitoring interfaces.
*   **Alerting Integration**: Can be integrated with alerting systems to notify on anomalies or thresholds.
*   **Real-time Monitoring**: Provides near real-time visibility into platform operations.

## How it Works

1.  **Agent Metric Publication**: All agents, inheriting from `BaseAgent`, publish their operational metrics (e.g., task counts, processing times, errors) to a designated NATS subject.
2.  **Metrics Agent Subscription**: The `MetricsAgent` subscribes to this NATS subject to receive all incoming metrics.
3.  **Processing and Storage**: Upon receiving a metric, the `MetricsAgent` processes it (e.g., adds timestamps, normalizes data) and stores it in the `metrics` table in the PostgreSQL database.
4.  **Querying and Visualization**: Stored metrics can then be queried for dashboards, reports, or used by other agents for decision-making.

## NATS Communication

### Subjects

*   **`metrics.publish`**: Agents publish their metrics to this subject.

### Message Format (for `metrics.publish`)

*   **Payload**: A JSON object representing the metric data.

    ```json
    {
        "agent_name": "<agent_name>",
        "metric_name": "<metric_name>",
        "metric_value": <numeric_value>,
        "timestamp": <unix_timestamp_float>,
        "tags": { "key": "value" } # Optional JSON object for additional context
    }
    ```

## Database Schema

The `MetricsAgent` primarily interacts with the `metrics` table:

### `metrics`

Stores operational metrics collected from agents.

| Column Name       | Type        | Constraints             | Description                                      |
|-------------------|-------------|-------------------------|--------------------------------------------------|
| `id`              | `SERIAL`    | `PRIMARY KEY`           | Auto-incrementing unique ID                      |
| `agent_name`      | `TEXT`      | `NOT NULL`              | Name of the agent reporting the metric           |
| `metric_name`     | `TEXT`      | `NOT NULL`              | Name of the metric (e.g., \'tasks_processed\', \'cpu_usage\') |
| `metric_value`    | `NUMERIC`   | `NOT NULL`              | The value of the metric                          |
| `timestamp`       | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP` | Timestamp when the metric was recorded           |
| `tags`            | `JSONB`     | `DEFAULT \'{}\''`      | Optional JSON tags for filtering/grouping metrics |

## Configuration

The `MetricsAgent` uses the `AgentConfig` for its base configuration. Specific settings related to metric retention, aggregation intervals, or external monitoring system integrations can be managed via the `ConfigManager`.

**Example `ConfigManager` settings for `metrics_agent`:**

| `config_key`      | `config_value`                                                              |
|-------------------|-----------------------------------------------------------------------------|
| `metric_retention_days` | `30`                                                                        |
| `prometheus_port` | `9090`                                                                      |

## Deployment

The `MetricsAgent` should be deployed as a standalone service. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections, and can be dynamically updated via the `ConfigManager`.

```bash
python metrics_agent.py
```

Refer to `README.md` for Docker Compose deployment examples.

