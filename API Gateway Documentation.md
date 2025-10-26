# API Gateway Documentation

## Overview

The API Gateway is the central entry point for all external interactions with the multi-agent platform. It provides a unified and secure interface for clients to access the various agent services. The gateway is responsible for:

*   **Authentication**: Validating API keys and user credentials.
*   **Request Routing**: Directing incoming requests to the appropriate agent based on the endpoint.
*   **Load Balancing**: Distributing requests across multiple instances of agents (if applicable).
*   **Rate Limiting**: Protecting the platform from excessive requests.
*   **Request/Response Transformation**: Formatting data between the client and the agents.

## Endpoints

The API Gateway exposes the following RESTful endpoints:

### Agent Task Management

*   **`POST /api/tasks`**: Submit a new task to a specific agent.

    **Request Body:**

    ```json
    {
        "agent_name": "<agent_name>",
        "task_type": "<task_type>",
        "payload": { ... },
        "priority": "<priority>"
    }
    ```

    **Response:**

    ```json
    {
        "task_id": "<task_id>",
        "status": "queued"
    }
    ```

*   **`GET /api/tasks/{task_id}`**: Get the status and result of a task.

    **Response:**

    ```json
    {
        "task_id": "<task_id>",
        "status": "<status>",
        "result": { ... },
        "error": "<error_message>"
    }
    ```

### Live Chat Management

The API Gateway also proxies requests to the Live Chatting Manager. Refer to the `live_chatting_manager.md` documentation for detailed specifications of the chat API endpoints.

## Authentication

All requests to the API Gateway must be authenticated using an API key. The API key must be included in the `Authorization` header of the request:

```
Authorization: Bearer <your_api_key>
```

API keys are managed in the `api_keys` table of the PostgreSQL database.

## Error Handling

The API Gateway returns standard HTTP status codes to indicate the success or failure of a request. The response body will contain a JSON object with an `error` field providing more details about the error.

| Status Code | Description                               |
|-------------|-------------------------------------------|
| `200 OK`      | The request was successful.               |
| `201 Created` | The resource was successfully created.    |
| `400 Bad Request` | The request was malformed or invalid.     |
| `401 Unauthorized` | The API key is missing or invalid.        |
| `404 Not Found`    | The requested resource was not found.     |
| `500 Internal Server Error` | An unexpected error occurred on the server. |

