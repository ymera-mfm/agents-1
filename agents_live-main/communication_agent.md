# Communication Agent Documentation

## Overview

The `CommunicationAgent` is responsible for managing all forms of external and inter-agent communication within the multi-agent platform. It acts as a central hub for sending and receiving messages, integrating with various communication channels, and facilitating AI-driven conversational responses. This agent ensures that information flows smoothly and securely across the platform and to external users or systems.

## Features

*   **NATS Messaging**: Facilitates robust inter-agent communication using NATS publish-subscribe and request-reply patterns.
*   **External Messaging Integration**: Can integrate with external communication platforms (e.g., email, SMS, chat platforms, social media) to send and receive messages.
*   **AI Response Generation**: Coordinates with the `LLMAgent` to generate intelligent and context-aware responses for conversational interactions.
*   **Message Routing**: Intelligently routes incoming messages to the appropriate agents or services for processing.
*   **Notification Management**: Handles sending notifications and alerts based on platform events.
*   **Context Management**: Maintains conversational context for ongoing interactions to ensure coherent responses.

## Task Types

The `CommunicationAgent` processes `TaskRequest` messages with the following `task_type` values:

*   **`send_message`**: Sends a message through a specified channel.
    *   **Payload**: `{"channel": "<channel_type>", "recipient": "<recipient_id>", "content": "<message_content>", "metadata": { ... }}`
    *   **Result**: `{"status": "sent", "message_id": "<message_id>"}`

*   **`receive_message`**: Processes an incoming message from an external channel.
    *   **Payload**: `{"channel": "<channel_type>", "sender": "<sender_id>", "content": "<message_content>", "metadata": { ... }}`
    *   **Result**: `{"status": "processed", "action_taken": "<action>"}`

*   **`generate_chat_response`**: Generates an AI-powered response for a chat session.
    *   **Payload**: `{"session_id": "<session_id>", "user_id": "<user_id>", "message_content": "<user_message>", "conversation_history": [ ... ], "context": { ... }}`
    *   **Result**: `{"response_content": "<ai_generated_response>"}`

*   **`send_notification`**: Sends a notification to a user or group.
    *   **Payload**: `{"user_ids": ["<user_id_1>"], "type": "<notification_type>", "message": "<notification_message>", "priority": "<priority>"}`
    *   **Result**: `{"status": "sent"}`

## NATS Communication

*   **Subject**: `agent.communication_agent.task` (for receiving task requests)
*   **Subject**: `agent.communication_agent.response` (for sending task responses)
*   **Subject**: `chat.ai.response` (publishes AI-generated chat responses, subscribed by `LiveChattingManager`)

Refer to `nats_messaging.md` and `base_agent.md` for detailed message formats.

## Configuration

The `CommunicationAgent` uses the `AgentConfig` for its base configuration. Specific communication channel API keys, templates, or integration settings can be managed via the `ConfigManager`.

**Example `ConfigManager` settings for `communication_agent`:**

| `config_key`      | `config_value`                                                              |
|-------------------|-----------------------------------------------------------------------------|
| `email_api_key`   | `sg.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`                               |
| `sms_gateway_url` | `https://api.sms-provider.com/send`                                         |
| `default_llm_model` | `gpt-4.1-mini`                                                              |

## Deployment

The `CommunicationAgent` should be deployed as a standalone service. Its configuration is primarily driven by environment variables for NATS, PostgreSQL, Redis, and Consul connections, and can be dynamically updated via the `ConfigManager`.

```bash
python communication_agent.py
```

Refer to `README.md` for Docker Compose deployment examples.

