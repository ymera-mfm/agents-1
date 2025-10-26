# Drafting Agent Documentation

## Overview

The `DraftingAgent` is specialized in content creation, document generation, and template management within the multi-agent platform. It takes high-level instructions or data and produces structured textual content, reports, or documents. This agent is essential for automating content generation workflows, ensuring consistency, and accelerating content production.

## Features

*   **Content Generation**: Creates new textual content based on prompts, data, and templates.
*   **Document Assembly**: Combines various content blocks, data points, and media into coherent documents.
*   **Template Management**: Utilizes predefined templates for consistent document formatting and structure.
*   **Data Integration**: Can pull data from various sources (e.g., databases, APIs) to populate dynamic content.
*   **Output Formatting**: Generates content in various formats (e.g., Markdown, HTML, PDF, plain text).
*   **Version Control Integration**: Can integrate with version control systems for managing generated documents.

## Task Types

The `DraftingAgent` processes `TaskRequest` messages with the following `task_type` values:

*   **`generate_document`**: Generates a complete document based on a template and provided data.
    *   **Payload**: `{"template_id": "<template_identifier>", "data": { ... }, "output_format": "<markdown|html|pdf>"}`
    *   **Result**: `{"document_content": "<generated_document_string>", "format": "<output_format>", "document_id": "<optional_id>"}`

*   **`create_content_block`**: Creates a smaller block of content (e.g., a paragraph, a section) based on instructions.
    *   **Payload**: `{"instructions": "<content_instructions>", "context": { ... }}`
    *   **Result**: `{"content_block": "<generated_text>"}`

*   **`populate_template`**: Fills a given template with provided data.
    *   **Payload**: `{"template_string": "<template_content>", "data": { ... }, "template_type": "<markdown|html>"}`
    *   **Result**: `{"filled_content": "<populated_template>"}`

*   **`export_document`**: Converts content into a specified output format.
    *   **Payload**: `{"content": "<text_content>", "source_format": "<markdown|html>", "target_format": "<pdf|html|txt>"}`
    *   **Result**: `{"exported_content": "<content_in_target_format>", "format": "<target_format>"}`

## NATS Communication

*   **Subject**: `agent.drafting_agent.task` (for receiving task requests)
*   **Subject**: `agent.drafting_agent.response` (for sending task responses)

Refer to `nats_messaging.md` and `base_agent.md` for detailed message formats.

## Configuration

The `DraftingAgent` uses the `AgentConfig` for its base configuration. Specific template locations, default output formats, or integration settings can be managed via the `ConfigManager`.

**Example `ConfigManager` settings for `drafting_agent`:**

| `config_key`      | `config_value`                                                              |
|-------------------|-----------------------------------------------------------------------------|
| `template_storage_path` | `/app/templates`                                                            |
| `default_output_format` | `markdown`                                                                  |

## Deployment

The `DraftingAgent` should be deployed as a standalone service. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections, and can be dynamically updated via the `ConfigManager`.

```bash
python drafting_agent.py
```

Refer to `README.md` for Docker Compose deployment examples.

