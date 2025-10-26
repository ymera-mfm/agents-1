# LLM Agent Documentation

## Overview

The `LLMAgent` is responsible for abstracting interactions with various Large Language Models (LLMs). It provides a standardized interface for other agents to leverage the power of generative AI for tasks such as text generation, summarization, translation, and more. By centralizing LLM interactions, the platform can easily switch between different LLM providers, manage API keys, and implement rate limiting or cost optimization strategies.

## Features

*   **LLM Abstraction**: Provides a unified API for interacting with different LLM providers (e.g., OpenAI, Google Gemini, custom models).
*   **Text Generation**: Generates human-like text based on prompts and parameters.
*   **Summarization**: Condenses long texts into shorter, coherent summaries.
*   **Translation**: Translates text between different languages.
*   **Sentiment Analysis**: Determines the emotional tone of a given text.
*   **Context Management**: Manages conversational context for multi-turn interactions.
*   **Rate Limiting & Caching**: Implements mechanisms to control LLM API usage and cache responses for efficiency.
*   **Cost Optimization**: Can be configured to use different LLMs based on cost and performance requirements.

## Task Types

The `LLMAgent` processes `TaskRequest` messages with the following `task_type` values:

*   **`generate_text`**: Generates text based on a prompt.
    *   **Payload**: `{"prompt": "<text_prompt>", "max_tokens": <int>, "temperature": <float>, "model": "<model_name>"}`
    *   **Result**: `{"generated_text": "<generated_content>"}`

*   **`summarize_text`**: Summarizes a given text.
    *   **Payload**: `{"text": "<long_text>", "summary_length": "<short|medium|long>", "model": "<model_name>"}`
    *   **Result**: `{"summary": "<summarized_content>"}`

*   **`translate_text`**: Translates text from a source language to a target language.
    *   **Payload**: `{"text": "<text_to_translate>", "source_language": "<lang_code>", "target_language": "<lang_code>", "model": "<model_name>"}`
    *   **Result**: `{"translated_text": "<translated_content>"}`

*   **`analyze_sentiment`**: Performs sentiment analysis on text.
    *   **Payload**: `{"text": "<text_to_analyze>", "model": "<model_name>"}`
    *   **Result**: `{"sentiment": "<positive|negative|neutral>", "score": <float>}`

*   **`chat_completion`**: Handles multi-turn conversational interactions.
    *   **Payload**: `{"messages": [{"role": "user", "content": "Hello"}, ...], "model": "<model_name>"}`
    *   **Result**: `{"response": {"role": "assistant", "content": "Hi there!"}}`

## NATS Communication

*   **Subject**: `agent.llm_agent.task` (for receiving task requests)
*   **Subject**: `agent.llm_agent.response` (for sending task responses)

Refer to `nats_messaging.md` and `base_agent.md` for detailed message formats.

## Configuration

The `LLMAgent` uses the `AgentConfig` for its base configuration. Specific LLM provider API keys and model preferences can be managed via the `ConfigManager`.

**Example `ConfigManager` settings for `llm_agent`:**

| `config_key`      | `config_value`                                                              |
|-------------------|-----------------------------------------------------------------------------|
| `default_model`   | `gpt-4.1-mini`                                                              |
| `openai_api_key`  | `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (sensitive, use environment variables) |
| `google_api_key`  | `AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (sensitive, use environment variables) |
| `rate_limit_per_minute` | `60`                                                                        |

## Deployment

The `LLMAgent` should be deployed as a standalone service. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections, and can be dynamically updated via the `ConfigManager`.

```bash
python llm_agent.py
```

Refer to `README.md` for Docker Compose deployment examples.

