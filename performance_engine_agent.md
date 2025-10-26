# Performance Engine Agent

The Performance Engine Agent is dedicated to monitoring, profiling, and optimizing the performance of the multi-agent platform. It works proactively to identify performance bottlenecks, analyze resource utilization, and suggest or implement improvements to ensure the system operates at peak efficiency and responsiveness.

## Functionality

*   **System Monitoring**: Continuously collects detailed performance metrics from various system components, including CPU usage, memory consumption, I/O operations, and network traffic.
*   **Application Profiling**: Performs in-depth profiling of agent processes and workflows to identify performance hotspots, inefficient code paths, and resource-intensive operations.
*   **Bottleneck Detection**: Utilizes advanced algorithms and historical data to automatically detect and diagnose performance bottlenecks within the platform.
*   **Performance Optimization**: Collaborates with the Optimizing Engine to apply recommended optimizations, such as adjusting resource limits, optimizing database queries, or fine-tuning agent configurations.
*   **Alerting**: Generates alerts when performance metrics exceed predefined thresholds or when significant performance degradation is detected.
*   **Reporting**: Produces comprehensive performance reports, including profiling results, bottleneck analyses, and the impact of applied optimizations.
*   **Persistence**: Stores all collected performance data, profiling results, and optimization outcomes in the database for historical analysis, trend identification, and capacity planning.

## Integration

*   **`base_agent.py`**: Inherits core functionalities for NATS communication, logging, and database interaction.
*   **`real_time_monitoring_agent.py`**: Receives raw system metrics and health status updates, which it then processes for deeper performance analysis.
*   **`optimizing_engine.py`**: Provides detailed performance insights and bottleneck detections to the Optimizing Engine, which then formulates and applies optimization strategies.
*   **`intelligence_engine.py`**: Feeds performance data and analysis results to the Intelligence Engine to inform adaptive decision-making and predictive analytics.
*   **`config_manager.py`**: Retrieves configuration parameters for monitoring intervals, profiling schedules, and performance thresholds.
*   **`metrics_agent.py`**: Publishes detailed performance metrics, profiling results, and bottleneck reports for aggregation and long-term storage.

## Configuration

The Performance Engine Agent's behavior is configured via the `ConfigManager`. Key configurable parameters include:

| Parameter Name                      | Description                                                                                             | Example Value                                  | Default Value     |
| :---------------------------------- | :------------------------------------------------------------------------------------------------------ | :--------------------------------------------- | :---------------- |
| `monitoring_interval_seconds`       | Frequency (in seconds) at which system metrics are collected.                                             | `10`                                           | `15`              |
| `profiling_schedule`                | Cron-like schedule for triggering application profiling (e.g., `"0 0 * * *"` for daily at midnight).    | `"0 */6 * * *"`                              | `None`            |
| `alert_thresholds`                  | JSON object defining thresholds for various performance metrics that trigger alerts.                      | `{"cpu_usage": {"critical": 90}}`          | `{}`              |
| `enable_auto_profiling`             | Boolean flag to enable or disable automatic profiling when performance degradation is detected.           | `true`                                         | `false`           |
| `data_retention_days`               | Number of days to retain detailed performance data in the database.                                       | `30`                                           | `90`              |

## NATS Communication

*   **Publishes**: `performance.metrics`, `performance.profile_report`, `performance.bottleneck_detected`, `performance.optimization_status`
*   **Subscribes**: `monitoring.realtime_metrics`, `config.performance_engine_agent.updated`, `orchestrator.profile_request`

## Database Schema

Relies on the `performance_profiles`, `bottlenecks`, `system_metrics`, and `alerts` tables in the PostgreSQL database for storing its operational data and analysis results.
