# Validation Agent

The Validation Agent is responsible for ensuring the integrity and correctness of data, code, and configurations within the multi-agent platform. It performs various validation checks based on predefined rules and schemas.

## Functionality

*   **Data Validation**: Validates incoming data payloads against specified schemas (e.g., JSON Schema) to ensure they conform to expected structures and types.
*   **Code Validation**: Performs syntax and basic semantic checks on code snippets or entire modules to identify common errors or non-compliance with coding standards.
*   **Configuration Validation**: Verifies agent configurations against defined rules to prevent misconfigurations that could lead to system instability.
*   **Rule Management**: Manages a set of validation rules, allowing for dynamic updates and extensions.
*   **Reporting**: Generates detailed validation reports, highlighting issues and suggesting corrective actions.
*   **Persistence**: Stores validation results and reports in the database for auditing and historical analysis.

## Integration

*   **`base_agent.py`**: Inherits core functionalities such as NATS communication, logging, and database interaction.
*   **`config_manager.py`**: Retrieves validation rules, schemas, and other configuration parameters.
*   **`api_gateway.py`**: Exposes endpoints for triggering data and code validation tasks.
*   **`orchestrator_agent.py`**: Can invoke the Validation Agent as part of a workflow to ensure task inputs or outputs meet quality standards.
*   **`metrics_agent.py`**: Reports validation success/failure rates and other relevant metrics.

## Configuration

The Validation Agent's behavior is configured via the `ConfigManager`. Key configurable parameters include:

*   `validation_rules_path`: Path to a file containing custom validation rules.
*   `default_schema_path`: Path to a default schema used for data validation.
*   `enable_strict_mode`: Boolean flag to enable stricter validation checks.

## NATS Communication

*   **Publishes**: `validation.report`, `validation.alert`
*   **Subscribes**: `validation.validate_code`, `validation.validate_data`, `config.validation_agent.updated`

## Database Schema

Relies on the `validation_reports` (new table) and `system_metrics` tables in the PostgreSQL database for storing validation results and metrics.
