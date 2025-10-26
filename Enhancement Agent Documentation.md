# Enhancement Agent Documentation

## Overview

The `EnhancementAgent` is designed to elevate the quality and impact of content by applying advanced optimization and intelligent transformation techniques. It takes existing content and improves it based on various criteria, such as SEO, readability, engagement, and target audience alignment. This agent is crucial for maximizing the effectiveness of generated or human-created content.

## Features

*   **SEO Optimization**: Analyzes content for keywords, readability, and structure to improve search engine ranking.
*   **Readability Improvement**: Adjusts sentence structure, vocabulary, and paragraph length to enhance comprehension.
*   **Engagement Boosting**: Suggests improvements to make content more captivating and interactive.
*   **Target Audience Alignment**: Tailors content tone, style, and messaging to resonate with specific demographics.
*   **Content Summarization/Expansion**: Can condense long articles or expand brief outlines into detailed pieces.
*   **Tone and Style Adjustment**: Modifies the emotional tone or stylistic elements of text (e.g., formal to informal, persuasive to informative).
*   **Multimodal Content Suggestions**: Recommends relevant images, videos, or other media to enrich textual content.

## Task Types

The `EnhancementAgent` processes `TaskRequest` messages with the following `task_type` values:

*   **`optimize_content`**: Optimizes content based on specified criteria (e.g., SEO, readability).
    *   **Payload**: `{"content": "<original_content>", "optimization_targets": ["seo", "readability"], "keywords": ["ai", "agents"]}`
    *   **Result**: `{"optimized_content": "<improved_content>", "report": { ... }, "suggestions": [ ... ]}`

*   **`improve_readability`**: Enhances the readability of the given text.
    *   **Payload**: `{"content": "<original_content>", "target_grade_level": <int>}`
    *   **Result**: `{"improved_content": "<more_readable_content>", "readability_score_before": <float>, "readability_score_after": <float>}`

*   **`adjust_tone`**: Changes the tone of the content to a specified style.
    *   **Payload**: `{"content": "<original_content>", "target_tone": "<formal|informal|persuasive|empathetic>"}`
    *   **Result**: `{"adjusted_content": "<content_with_new_tone>"}`

*   **`generate_summary`**: Creates a concise summary of the content.
    *   **Payload**: `{"content": "<long_content>", "summary_length": "<short|medium|long>"}`
    *   **Result**: `{"summary": "<generated_summary>"}`

*   **`expand_content`**: Expands a brief content piece into a more detailed version.
    *   **Payload**: `{"content": "<brief_content>", "target_length_words": <int>, "context": { ... }}`
    *   **Result**: `{"expanded_content": "<detailed_content>"}`

## NATS Communication

*   **Subject**: `agent.enhancement_agent.task` (for receiving task requests)
*   **Subject**: `agent.enhancement_agent.response` (for sending task responses)

Refer to `nats_messaging.md` and `base_agent.md` for detailed message formats.

## Configuration

The `EnhancementAgent` uses the `AgentConfig` for its base configuration. Specific optimization algorithms, external APIs for content analysis, or style guidelines can be managed via the `ConfigManager`.

**Example `ConfigManager` settings for `enhancement_agent`:**

| `config_key`      | `config_value`                                                              |
|-------------------|-----------------------------------------------------------------------------|
| `seo_tool_api_key`| `xyz123abc456`                                                              |
| `default_readability_target` | `8` (grade level)                                                           |

## Deployment

The `EnhancementAgent` should be deployed as a standalone service. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections, and can be dynamically updated via the `ConfigManager`.

```bash
python enhancement_agent.py
```

Refer to `README.md` for Docker Compose deployment examples.

