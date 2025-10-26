# Live Chatting Manager Documentation

## Overview

The Live Chatting Manager is a comprehensive agent responsible for managing real-time chat functionality within the platform. It provides a WebSocket-based interface for live communication and a RESTful API for session management and history retrieval.

## Features

*   **Real-time Chat**: WebSocket server for low-latency, bidirectional communication.
*   **Multi-user Sessions**: Supports both individual and group chat sessions.
*   **Message Persistence**: Chat history is stored in the PostgreSQL database.
*   **AI Integration**: Seamlessly integrates with the `CommunicationAgent` and `LLMAgent` to provide AI-powered responses.
*   **User Presence**: Real-time typing indicators and user online status.
*   **Content Moderation**: Filters for profanity, spam, and malicious content.
*   **RESTful API**: HTTP endpoints for managing chat sessions and retrieving history.

## WebSocket API

The WebSocket server provides the primary interface for real-time chat. To connect, a client must establish a WebSocket connection to the following endpoint:

```
ws://<your_host>:<websocket_port>
```

### Initial Connection

Upon connecting, the client must send an initial JSON message to identify the user and the session they wish to join:

```json
{
    "user_id": "<user_id>",
    "session_id": "<session_id>"
}
```

### Incoming Messages

The server sends various types of messages to the client:

*   **`chat_history`**: Sent upon initial connection, contains recent chat history.
*   **`chat_message`**: A new message in the session.
*   **`user_joined`**: A new user has joined the session.
*   **`user_left`**: A user has left the session.
*   **`typing_status`**: Indicates which users are currently typing.
*   **`session_ended`**: The chat session has been terminated.

### Outgoing Messages

The client can send the following messages to the server:

*   **`chat_message`**: Send a new message to the session.

    ```json
    {
        "type": "chat_message",
        "content": "Hello, world!"
    }
    ```

*   **`typing_indicator`**: Notify the server that the user is typing.

    ```json
    {
        "type": "typing_indicator",
        "is_typing": true
    }
    ```

## RESTful API

The Live Chatting Manager also exposes a RESTful API for session management. These endpoints are typically accessed through the main `api_gateway.py`.

### Chat Session Management

*   **`POST /api/chat/sessions`**: Create a new chat session.
*   **`GET /api/chat/sessions/{session_id}`**: Get details about a specific session.
*   **`POST /api/chat/sessions/{session_id}/join`**: Join a user to a session.
*   **`POST /api/chat/sessions/{session_id}/leave`**: Remove a user from a session.

### Message Management

*   **`GET /api/chat/sessions/{session_id}/messages`**: Retrieve chat history for a session.
*   **`POST /api/chat/sessions/{session_id}/messages`**: Send a message to a session via HTTP.

## Database Schema

The Live Chatting Manager relies on the following tables in the `database_schema.sql`:

*   **`chat_sessions`**: Stores information about each chat session.
*   **`chat_messages`**: Stores all messages sent within chat sessions.

Refer to `database_schema.sql` for detailed table definitions.

