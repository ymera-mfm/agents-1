# Intelligence Engine

The Intelligence Engine is the brain of the multi-agent platform, responsible for advanced decision-making, learning, and adaptive behavior. It leverages machine learning models and real-time data to optimize agent coordination, task routing, and resource allocation, ensuring the platform operates with maximum efficiency and effectiveness.

## Functionality

*   **Adaptive Task Routing**: Dynamically routes tasks to the most suitable agents based on their capabilities, current load, historical performance, and predicted efficiency.
*   **Predictive Analytics**: Utilizes ML models to predict future system states, potential bottlenecks, or agent performance, enabling proactive adjustments.
*   **Learning and Adaptation**: Continuously learns from past task outcomes, optimization results, and system feedback to refine its decision-making algorithms and improve overall platform intelligence.
*   **Resource Optimization**: Recommends or directly implements adjustments to resource allocation for agents or tasks to maximize throughput and minimize latency.
*   **Anomaly Detection**: Identifies unusual patterns in agent behavior or system metrics, flagging potential issues for further investigation by monitoring agents.
*   **System State Management**: Maintains a comprehensive understanding of the entire platform's state, including agent health, task queues, and workflow progress.
*   **Persistence**: Stores decision history, ML model versions, and learning data in the database for auditability, model retraining, and continuous improvement.

## Integration

*   **`base_agent.py`**: Inherits core functionalities for NATS communication, logging, and database interaction.
*   **`orchestrator_agent.py`**: Provides the Intelligence Engine with task requests and receives optimal agent assignments or workflow adjustments.
*   **`real_time_monitoring_agent.py`**: Feeds real-time system metrics, agent health status, and alerts to the Intelligence Engine for informed decision-making.
*   **`optimizing_engine.py`**: Collaborates to implement system-wide optimizations based on intelligent recommendations.
*   **`config_manager.py`**: Retrieves configuration for ML models, decision-making parameters, and learning algorithms.
*   **`metrics_agent.py`**: Publishes metrics related to decision accuracy, learning progress, and the impact of intelligent interventions.

## Configuration

The Intelligence Engine's behavior is configured via the `ConfigManager`. Key configurable parameters include:

| Parameter Name                      | Description                                                                                             | Example Value                                  | Default Value     |
| :---------------------------------- | :------------------------------------------------------------------------------------------------------ | :--------------------------------------------- | :---------------- |
| `decision_strategy`                 | The primary strategy for task routing and resource allocation (e.g., `adaptive`, `rule_based`, `ml_driven`). | `"adaptive"`                                   | `"adaptive"`      |
| `ml_model_path`                     | Path to the trained machine learning model used for predictive analytics and decision-making.             | `"/app/models/intelligence_engine_model.pkl"` | `None`            |
| `optimization_interval_seconds`     | Frequency (in seconds) at which the engine re-evaluates and applies system-wide optimizations.            | `300`                                          | `600`             |
| `learning_rate`                     | The rate at which the engine adapts its models based on new data and feedback.                          | `0.01`                                         | `0.005`           |
| `enable_self_correction`            | Boolean flag to enable or disable autonomous correction of suboptimal decisions.                        | `true`                                         | `false`           |

## NATS Communication

*   **Publishes**: `intelligence.decision`, `intelligence.prediction`, `system.metrics` (for its own operational metrics)
*   **Subscribes**: `orchestrator.task_request`, `monitoring.realtime_metrics`, `config.intelligence_engine.updated`

## Database Schema

Relies on the `decision_history`, `ml_model_versions`, `system_metrics`, and `agents` tables in the PostgreSQL database for storing operational data, learning artifacts, and system state.
