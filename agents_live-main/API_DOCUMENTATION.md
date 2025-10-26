# YMERA Platform - API Documentation

## Overview

The YMERA Platform provides a RESTful API built with FastAPI. All endpoints return JSON responses.

**Base URL:** `http://localhost:8000` (or your deployed domain)

**API Version:** v1

**Interactive Documentation:**
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Authentication

Most endpoints require JWT authentication.

### Get Access Token

**Endpoint:** `POST /auth/token`

**Request:**
```json
{
  "username": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Token

Include in Authorization header:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## System Endpoints

### Health Check

**Endpoint:** `GET /health`

**Description:** Check system health status

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-10-20T00:00:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  }
}
```

### Metrics

**Endpoint:** `GET /metrics`

**Description:** Prometheus metrics for monitoring

**Response:** Prometheus text format

### Version Info

**Endpoint:** `GET /version`

**Response:**
```json
{
  "version": "2.0.0",
  "build": "20251020",
  "environment": "production"
}
```

## Agent Endpoints

### List Agents

**Endpoint:** `GET /api/v1/agents`

**Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100)
- `status` (string): Filter by status (active, inactive, all)

**Response:**
```json
{
  "total": 24,
  "skip": 0,
  "limit": 100,
  "agents": [
    {
      "id": "agent-123",
      "name": "Learning Agent",
      "type": "learning",
      "status": "active",
      "created_at": "2025-10-20T00:00:00Z",
      "updated_at": "2025-10-20T00:00:00Z"
    }
  ]
}
```

### Get Agent

**Endpoint:** `GET /api/v1/agents/{agent_id}`

**Response:**
```json
{
  "id": "agent-123",
  "name": "Learning Agent",
  "type": "learning",
  "status": "active",
  "description": "Adaptive learning agent",
  "configuration": {
    "learning_rate": 0.01,
    "max_iterations": 1000
  },
  "metrics": {
    "tasks_completed": 150,
    "success_rate": 0.95,
    "avg_execution_time": 2.5
  },
  "created_at": "2025-10-20T00:00:00Z",
  "updated_at": "2025-10-20T00:00:00Z"
}
```

### Create Agent

**Endpoint:** `POST /api/v1/agents`

**Request:**
```json
{
  "name": "My Custom Agent",
  "type": "custom",
  "description": "Custom agent for specific tasks",
  "configuration": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Response:**
```json
{
  "id": "agent-456",
  "name": "My Custom Agent",
  "status": "created",
  "message": "Agent created successfully"
}
```

### Update Agent

**Endpoint:** `PUT /api/v1/agents/{agent_id}`

**Request:**
```json
{
  "name": "Updated Agent Name",
  "configuration": {
    "param1": "new_value"
  }
}
```

### Delete Agent

**Endpoint:** `DELETE /api/v1/agents/{agent_id}`

**Response:**
```json
{
  "message": "Agent deleted successfully"
}
```

### Execute Agent

**Endpoint:** `POST /api/v1/agents/{agent_id}/execute`

**Request:**
```json
{
  "input_data": {
    "task": "analyze_data",
    "data": {...}
  },
  "options": {
    "async": true,
    "timeout": 300
  }
}
```

**Response:**
```json
{
  "task_id": "task-789",
  "status": "running",
  "message": "Agent execution started"
}
```

## Task Endpoints

### List Tasks

**Endpoint:** `GET /api/v1/tasks`

**Parameters:**
- `skip`, `limit`: Pagination
- `status`: Filter by status (pending, running, completed, failed)
- `agent_id`: Filter by agent

**Response:**
```json
{
  "total": 50,
  "tasks": [
    {
      "id": "task-789",
      "agent_id": "agent-123",
      "status": "completed",
      "created_at": "2025-10-20T00:00:00Z",
      "completed_at": "2025-10-20T00:01:30Z",
      "result": {...}
    }
  ]
}
```

### Get Task

**Endpoint:** `GET /api/v1/tasks/{task_id}`

**Response:**
```json
{
  "id": "task-789",
  "agent_id": "agent-123",
  "status": "completed",
  "input": {...},
  "output": {...},
  "metrics": {
    "execution_time": 90.5,
    "memory_used": 256
  },
  "created_at": "2025-10-20T00:00:00Z",
  "completed_at": "2025-10-20T00:01:30Z"
}
```

### Cancel Task

**Endpoint:** `POST /api/v1/tasks/{task_id}/cancel`

**Response:**
```json
{
  "message": "Task cancelled successfully"
}
```

## Project Endpoints

### List Projects

**Endpoint:** `GET /api/v1/projects`

**Response:**
```json
{
  "total": 10,
  "projects": [
    {
      "id": "proj-001",
      "name": "Project Alpha",
      "status": "active",
      "created_at": "2025-10-20T00:00:00Z"
    }
  ]
}
```

### Create Project

**Endpoint:** `POST /api/v1/projects`

**Request:**
```json
{
  "name": "New Project",
  "description": "Project description",
  "settings": {}
}
```

## File Endpoints

### Upload File

**Endpoint:** `POST /api/v1/files/upload`

**Request:** multipart/form-data
- `file`: File to upload
- `project_id`: Associated project (optional)

**Response:**
```json
{
  "file_id": "file-123",
  "filename": "document.pdf",
  "size": 1048576,
  "url": "/api/v1/files/file-123"
}
```

### Download File

**Endpoint:** `GET /api/v1/files/{file_id}`

**Response:** File stream

### Delete File

**Endpoint:** `DELETE /api/v1/files/{file_id}`

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional error details"
    }
  }
}
```

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Common Error Codes

- `AUTH_REQUIRED`: Authentication required
- `INVALID_TOKEN`: Invalid or expired token
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Request validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

API requests are rate-limited:
- **Default:** 60 requests per minute
- **Authenticated:** 1000 requests per hour

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1634567890
```

## Pagination

List endpoints support pagination:

**Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 1000)

**Response:**
```json
{
  "total": 500,
  "skip": 0,
  "limit": 100,
  "data": [...]
}
```

## Filtering and Sorting

**Filtering:**
```
GET /api/v1/agents?status=active&type=learning
```

**Sorting:**
```
GET /api/v1/agents?sort=created_at&order=desc
```

## Webhooks

Configure webhooks for event notifications:

**Endpoint:** `POST /api/v1/webhooks`

**Request:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["task.completed", "agent.failed"],
  "secret": "your-webhook-secret"
}
```

**Webhook Payload:**
```json
{
  "event": "task.completed",
  "timestamp": "2025-10-20T00:00:00Z",
  "data": {
    "task_id": "task-789",
    "status": "completed"
  }
}
```

## Code Examples

### Python

```python
import requests

# Get access token
response = requests.post(
    "http://localhost:8000/auth/token",
    json={"username": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Use token for API calls
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/agents",
    headers=headers
)
agents = response.json()
```

### JavaScript

```javascript
// Get access token
const tokenResponse = await fetch('http://localhost:8000/auth/token', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password'
  })
});
const {access_token} = await tokenResponse.json();

// Use token for API calls
const response = await fetch('http://localhost:8000/api/v1/agents', {
  headers: {'Authorization': `Bearer ${access_token}`}
});
const agents = await response.json();
```

### cURL

```bash
# Get access token
TOKEN=$(curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Use token
curl http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer $TOKEN"
```

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** - Never commit tokens to version control
3. **Implement token refresh** - Refresh tokens before expiration
4. **Handle rate limits** - Implement exponential backoff
5. **Validate responses** - Always check status codes
6. **Use appropriate timeouts** - Don't hang indefinitely
7. **Log API usage** - For debugging and monitoring
8. **Handle errors gracefully** - User-friendly error messages

---

**Last Updated:** 2025-10-20
**API Version:** 1.0
