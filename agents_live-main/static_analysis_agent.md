# Static Analysis Agent

The Static Analysis Agent is designed to perform automated code analysis without executing the code. It identifies potential bugs, security vulnerabilities, code smells, and ensures adherence to coding standards, contributing to higher code quality and maintainability within the multi-agent platform.

## Functionality

The Static Analysis Agent offers a range of capabilities to assess code quality:

*   **Code Linting**: Utilizes various linting tools (e.g., Pylint, Flake8 for Python) to enforce coding style guidelines and detect syntax errors or stylistic inconsistencies.
*   **Vulnerability Detection**: Scans code for common security vulnerabilities, such as SQL injection, cross-site scripting (XSS), and insecure configurations, using specialized static analysis tools.
*   **Complexity Analysis**: Measures code complexity metrics (e.g., cyclomatic complexity) to identify areas that may be difficult to understand, test, or maintain.
*   **Dependency Analysis**: Analyzes project dependencies to identify outdated libraries, licensing issues, or known vulnerabilities in third-party components.
*   **Custom Rule Enforcement**: Supports the integration of custom static analysis rules tailored to specific project requirements or organizational standards.
*   **Reporting**: Generates detailed analysis reports, including identified issues, their severity, and suggested remediation steps. These reports are crucial for developers to improve their code.
*   **Persistence**: Stores analysis results and reports in the database, providing a historical record for trend analysis and compliance auditing.

## Integration

The Static Analysis Agent integrates seamlessly with other components of the platform:

*   **`base_agent.py`**: Inherits fundamental functionalities, including NATS communication, logging, and database interaction, ensuring consistent operation and adherence to platform standards.
*   **`config_manager.py`**: Retrieves configuration parameters, such as the list of analysis tools to use, severity thresholds for reporting, and paths to custom rule sets.
*   **`api_gateway.py`**: Exposes endpoints that allow external systems or development pipelines to trigger static code analysis tasks and retrieve their results.
*   **`orchestrator_agent.py`**: Can invoke the Static Analysis Agent as part of a continuous integration/continuous deployment (CI/CD) pipeline or a code review workflow, ensuring code quality gates are met.
*   **`metrics_agent.py`**: Reports key metrics related to static analysis, such as the number of issues found, average analysis time, and the distribution of issue severities, contributing to overall platform observability.

## Configuration

The Static Analysis Agent's behavior is highly configurable through the `ConfigManager`. Key parameters include:

| Parameter Name               | Description                                                                                             | Example Value                                | Default Value     |
| :--------------------------- | :------------------------------------------------------------------------------------------------------ | :------------------------------------------- | :---------------- |
| `analysis_tools`             | A list of static analysis tools to be used (e.g., `pylint`, `flake8`, `bandit`).                      | `["pylint", "flake8"]`                     | `[]`              |
| `default_severity_threshold` | The minimum severity level for issues to be included in reports (e.g., `low`, `medium`, `high`, `critical`). | `"medium"`                                   | `"low"`           |
| `custom_rules_path`          | Path to a directory containing custom static analysis rules.                                            | `"/app/rules/custom_analysis_rules/"`      | `None`            |
| `exclude_paths`              | A list of file paths or patterns to exclude from analysis.                                              | `["tests/", "docs/"]`                      | `[]`              |
| `report_format`              | The desired format for generated analysis reports (e.g., `json`, `xml`, `html`).                        | `"json"`                                     | `"json"`          |

## NATS Communication

The Static Analysis Agent communicates via NATS for task coordination and reporting:

*   **Publishes**: `static_analysis.report`, `static_analysis.alert` (for critical findings)
*   **Subscribes**: `static_analysis.analyze_code`, `config.static_analysis_agent.updated`

## Database Schema

This agent relies on the `static_analysis_reports` (a new table to be created) and `system_metrics` tables in the PostgreSQL database for storing detailed analysis results, historical data, and performance metrics related to its operations.
