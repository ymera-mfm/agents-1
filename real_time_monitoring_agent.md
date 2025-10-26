# Real-Time Monitoring Agent

The Real-Time Monitoring Agent is a critical component of the multi-agent platform, responsible for continuous observation of system health, performance metrics, and agent statuses. It consolidates functionalities previously handled by separate monitoring and health-checking agents, providing a unified view of the platform's operational state.

## Functionality

*   **Metric Collection**: Gathers real-time performance metrics (CPU, memory, network, task queues) from all registered agents and system components.
*   **Health Checks**: Performs periodic health checks on agents and services, reporting their operational status and identifying potential issues.
*   **Alerting**: Detects anomalies and deviations from predefined thresholds, triggering alerts through the NATS messaging system.
*   **Service Discovery**: Maintains an up-to-date registry of active agents and their capabilities, facilitating dynamic routing and load balancing.
*   **Data Persistence**: Stores collected metrics and health status updates in the PostgreSQL database for historical analysis and visualization.
*   **Real-time Updates**: Publishes live status updates and critical alerts via NATS, enabling immediate frontend visualization and proactive responses from other agents.

## Integration

*   **`base_agent.py`**: Inherits core functionalities such as NATS communication, logging, and database interaction.
*   **`metrics_agent.py`**: Feeds collected metrics and health data to the Metrics Agent for aggregation, summarization, and long-term storage.
*   **`config_manager.py`**: Retrieves configuration parameters, including monitoring intervals, alert thresholds, and service discovery settings.
*   **`api_gateway.py`**: Exposes endpoints for querying real-time metrics and health status, allowing external systems and the frontend to access operational data.
*   **`intelligence_engine.py`**: Provides real-time system state and performance data to the Intelligence Engine for informed decision-making and optimization strategies.

## Configuration

The Real-Time Monitoring Agent's behavior is configured via the `ConfigManager`. Key configurable parameters include:

*   `metric_collection_interval_seconds`: Frequency (in seconds) at which metrics are collected.
*   `health_check_interval_seconds`: Frequency (in seconds) at which health checks are performed.
*   `anomaly_detection_enabled`: Boolean flag to enable or disable anomaly detection.
*   `alert_thresholds`: JSON object defining thresholds for various metrics (e.g., CPU usage, memory usage) that trigger alerts.

## NATS Communication

*   **Publishes**: `agent.presence.update`, `metrics.realtime`, `health.status`, `alerts.critical`, `alerts.warning`
*   **Subscribes**: `config.real_time_monitoring_agent.updated`

## Database Schema

Relies on the `agents`, `agent_heartbeats`, `system_metrics`, and `alerts` tables in the PostgreSQL database for storing operational data.
