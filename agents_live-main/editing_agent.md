# Editing Agent Documentation

## Overview

The `EditingAgent` specializes in content refinement, revision tracking, and collaborative editing functionalities within the multi-agent platform. It provides capabilities to modify, correct, and improve textual content based on specific instructions or quality standards. This agent is crucial for maintaining high content quality and facilitating iterative content development workflows.

## Features

*   **Content Modification**: Performs various text editing operations, such as grammar correction, spelling checks, stylistic improvements, and factual updates.
*   **Revision Tracking**: Keeps a history of changes made to content, allowing for rollbacks and auditing.
*   **Collaborative Editing Support**: Integrates with other agents or external systems to facilitate multi-user content editing workflows.
*   **Quality Assurance Integration**: Works in conjunction with the `ExaminationAgent` to ensure edited content meets predefined quality metrics.
*   **Version Control**: Manages different versions of content, enabling comparison and merging of changes.

## Task Types

The `EditingAgent` processes `TaskRequest` messages with the following `task_type` values:

*   **`edit_text`**: Edits a given text based on provided instructions.
    *   **Payload**: `{"text": "<original_text>", "instructions": "<editing_instructions>", "revision_id": "<optional_revision_id>"}`
    *   **Result**: `{"edited_text": "<modified_text>", "changes_made": "<description_of_changes>", "new_revision_id": "<new_revision_id>"}`

*   **`proofread_text`**: Proofreads text for grammar, spelling, and punctuation errors.
    *   **Payload**: `{"text": "<text_to_proofread>"}`
    *   **Result**: `{"corrected_text": "<corrected_text>", "corrections": [{"original": "<word>", "suggestion": "<word>"}, ...]}`

*   **`apply_style_guide`**: Applies a specific style guide to the text.
    *   **Payload**: `{"text": "<original_text>", "style_guide_id": "<style_guide_identifier>"}`
    *   **Result**: `{"styled_text": "<formatted_text>"}`

*   **`compare_revisions`**: Compares two versions of a text and highlights differences.
    *   **Payload**: `{"text_a": "<text_version_a>", "text_b": "<text_version_b>"}`
    *   **Result**: `{"differences": "<diff_output_format>"}`

## NATS Communication

*   **Subject**: `agent.editing_agent.task` (for receiving task requests)
*   **Subject**: `agent.editing_agent.response` (for sending task responses)

Refer to `nats_messaging.md` and `base_agent.md` for detailed message formats.

## Configuration

The `EditingAgent` uses the `AgentConfig` for its base configuration. Specific editing rules, style guides, or integration settings can be managed via the `ConfigManager`.

**Example `ConfigManager` settings for `editing_agent`:**

| `config_key`      | `config_value`                                                              |
|-------------------|-----------------------------------------------------------------------------|
| `default_style_guide` | `AP_Style`                                                                  |
| `grammar_check_api_endpoint` | `https://api.grammar.com/check`                                             |

## Deployment

The `EditingAgent` should be deployed as a standalone service. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections, and can be dynamically updated via the `ConfigManager`.

```bash
python editing_agent.py
```

Refer to `README.md` for Docker Compose deployment examples.

