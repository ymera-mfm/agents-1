# Examination Agent Documentation

## Overview

The `ExaminationAgent` is dedicated to ensuring the quality, accuracy, and compliance of content within the multi-agent platform. It performs various checks, validations, and analyses to identify potential issues, verify facts, and ensure adherence to predefined standards or guidelines. This agent is crucial for maintaining the integrity and trustworthiness of generated or processed content.

## Features

*   **Content Validation**: Checks content against predefined rules, schemas, or formats.
*   **Fact-Checking**: Verifies factual claims using external knowledge bases or search capabilities.
*   **Compliance Checks**: Ensures content adheres to regulatory, ethical, or brand guidelines.
*   **Quality Assessment**: Evaluates content readability, coherence, and overall quality metrics.
*   **Plagiarism Detection**: Identifies instances of unoriginal content.
*   **Security Scanning**: Scans content for potential vulnerabilities or malicious patterns (e.g., SQL injection, XSS).
*   **Feedback Generation**: Provides detailed reports and actionable feedback on identified issues.

## Task Types

The `ExaminationAgent` processes `TaskRequest` messages with the following `task_type` values:

*   **`examine_content`**: Performs a comprehensive examination of the given content.
    *   **Payload**: `{"content": "<text_content>", "checks": ["fact_check", "compliance", "quality"], "context": { ... }}`
    *   **Result**: `{"status": "<passed|failed|pending_review>", "report": { ... }, "issues": [ ... ]}`

*   **`fact_check`**: Verifies factual claims within the content.
    *   **Payload**: `{"content": "<text_content>", "claims": ["<claim_1>", "<claim_2>"]}`
    *   **Result**: `{"fact_check_results": [{"claim": "<claim>", "status": "<verified|unverified|disputed>", "evidence": "<url>"}]}`

*   **`check_compliance`**: Checks content against specified compliance rules.
    *   **Payload**: `{"content": "<text_content>", "ruleset_id": "<ruleset_identifier>"}`
    *   **Result**: `{"compliance_status": "<compliant|non_compliant>", "violations": [ ... ]}`

*   **`assess_quality`**: Assesses the overall quality of the content.
    *   **Payload**: `{"content": "<text_content>", "metrics": ["readability", "coherence"]}`
    *   **Result**: `{"quality_score": <float>, "readability_score": <float>, "suggestions": [ ... ]}`

## NATS Communication

*   **Subject**: `agent.examination_agent.task` (for receiving task requests)
*   **Subject**: `agent.examination_agent.response` (for sending task responses)

Refer to `nats_messaging.md` and `base_agent.md` for detailed message formats.

## Configuration

The `ExaminationAgent` uses the `AgentConfig` for its base configuration. Specific rulesets, external API endpoints for fact-checking, or quality assessment models can be managed via the `ConfigManager`.

**Example `ConfigManager` settings for `examination_agent`:**

| `config_key`      | `config_value`                                                              |
|-------------------|-----------------------------------------------------------------------------|
| `default_ruleset` | `GDPR_Compliance`                                                           |
| `fact_check_api_endpoint` | `https://api.factchecker.com/verify`                                        |

## Deployment

The `ExaminationAgent` should be deployed as a standalone service. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections, and can be dynamically updated via the `ConfigManager`.

```bash
python examination_agent.py
```

Refer to `README.md` for Docker Compose deployment examples.

