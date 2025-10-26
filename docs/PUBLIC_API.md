# YMERA Multi-Agent AI System - Public REST API v1

## Overview

The YMERA Public REST API provides programmatic access to the multi-agent AI system, enabling external applications and services to create, manage, and interact with AI agents for various automation tasks.

**Base URL**: `https://api.ymera.io/v1`  
**Authentication**: Bearer Token (JWT)  
**Rate Limits**: 1000 requests/hour per API key

## Authentication

All API requests require authentication using a JWT bearer token.

```bash
Authorization: Bearer <your_api_token>
```

### Obtain API Token

```http
POST /auth/token
Content-Type: application/json

{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## Core Resources

### Agents

#### List All Agents

```http
GET /agents
```

**Query Parameters**:
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20, max: 100)
- `type` (string): Filter by agent type
- `status` (string): Filter by status (initialized, running, paused, stopped, error)

**Response**:
```json
{
  "agents": [
    {
      "agent_id": "code_gen_001",
      "type": "code_generation",
      "status": "running",
      "created_at": "2025-10-26T10:00:00Z",
      "config": {
        "supported_languages": ["python", "javascript", "typescript"]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

#### Get Agent Details

```http
GET /agents/{agent_id}
```

**Response**:
```json
{
  "agent_id": "code_gen_001",
  "type": "code_generation",
  "status": "running",
  "created_at": "2025-10-26T10:00:00Z",
  "last_active": "2025-10-26T14:30:00Z",
  "config": {
    "supported_languages": ["python", "javascript", "typescript"]
  },
  "metrics": {
    "total_tasks": 150,
    "successful_tasks": 145,
    "failed_tasks": 5
  }
}
```

#### Create Agent

```http
POST /agents
Content-Type: application/json

{
  "type": "code_generation",
  "config": {
    "supported_languages": ["python", "javascript"],
    "checkpoint_interval": 60
  }
}
```

**Response** (201 Created):
```json
{
  "agent_id": "code_gen_002",
  "type": "code_generation",
  "status": "initialized",
  "created_at": "2025-10-26T15:00:00Z",
  "config": {
    "supported_languages": ["python", "javascript"],
    "checkpoint_interval": 60
  }
}
```

#### Update Agent Configuration

```http
PATCH /agents/{agent_id}
Content-Type: application/json

{
  "config": {
    "checkpoint_interval": 120
  }
}
```

**Response**:
```json
{
  "agent_id": "code_gen_001",
  "config": {
    "checkpoint_interval": 120
  },
  "updated_at": "2025-10-26T15:30:00Z"
}
```

#### Delete Agent

```http
DELETE /agents/{agent_id}
```

**Response** (204 No Content)

### Tasks

#### Submit Task to Agent

```http
POST /agents/{agent_id}/tasks
Content-Type: application/json

{
  "type": "generate_code",
  "parameters": {
    "language": "python",
    "specification": "Create a REST API endpoint for user authentication",
    "options": {
      "framework": "fastapi"
    }
  }
}
```

**Response** (202 Accepted):
```json
{
  "task_id": "task_001",
  "agent_id": "code_gen_001",
  "status": "queued",
  "submitted_at": "2025-10-26T15:00:00Z"
}
```

#### Get Task Status

```http
GET /agents/{agent_id}/tasks/{task_id}
```

**Response**:
```json
{
  "task_id": "task_001",
  "agent_id": "code_gen_001",
  "status": "completed",
  "submitted_at": "2025-10-26T15:00:00Z",
  "completed_at": "2025-10-26T15:00:05Z",
  "result": {
    "status": "success",
    "language": "python",
    "code": "from fastapi import FastAPI, HTTPException...",
    "metadata": {
      "lines_of_code": 45
    }
  }
}
```

**Task Status Values**:
- `queued`: Task submitted but not yet started
- `processing`: Task is being processed
- `completed`: Task completed successfully
- `failed`: Task failed with error

### Projects

#### Create Project

```http
POST /projects
Content-Type: application/json

{
  "name": "E-commerce Platform",
  "description": "Building automated testing and deployment pipeline",
  "agents": ["code_gen_001", "devops_001"]
}
```

**Response** (201 Created):
```json
{
  "project_id": "proj_001",
  "name": "E-commerce Platform",
  "description": "Building automated testing and deployment pipeline",
  "created_at": "2025-10-26T15:00:00Z",
  "agents": ["code_gen_001", "devops_001"]
}
```

#### List Projects

```http
GET /projects
```

**Response**:
```json
{
  "projects": [
    {
      "project_id": "proj_001",
      "name": "E-commerce Platform",
      "status": "active",
      "agents_count": 2,
      "created_at": "2025-10-26T15:00:00Z"
    }
  ]
}
```

## Specialized Agents

### Code Generation Agent

Type: `code_generation`

**Supported Operations**:

1. **Generate Code**
```json
{
  "type": "generate_code",
  "parameters": {
    "language": "python|javascript|typescript|java|go|rust",
    "specification": "Description of what the code should do",
    "options": {
      "style": "pep8|google|airbnb",
      "framework": "fastapi|express|spring"
    }
  }
}
```

2. **Analyze Code**
```json
{
  "type": "analyze_code",
  "parameters": {
    "language": "python",
    "code": "def example(): pass",
    "options": {
      "check_style": true,
      "check_complexity": true
    }
  }
}
```

3. **Refactor Code**
```json
{
  "type": "refactor_code",
  "parameters": {
    "language": "python",
    "code": "Original code here",
    "options": {
      "remove_duplicates": true,
      "optimize": true
    }
  }
}
```

4. **Generate Tests**
```json
{
  "type": "generate_tests",
  "parameters": {
    "language": "python",
    "code": "Code to test",
    "options": {
      "framework": "pytest|jest|junit"
    }
  }
}
```

### DevOps Agent

Type: `devops`

**Supported Operations**:

1. **Deploy Service**
```json
{
  "type": "deploy",
  "parameters": {
    "environment": "development|staging|production",
    "service": "api-service",
    "options": {
      "version": "1.2.0",
      "strategy": "rolling|blue-green|canary"
    }
  }
}
```

2. **Provision Infrastructure**
```json
{
  "type": "provision",
  "parameters": {
    "environment": "production",
    "options": {
      "resources": [
        {"type": "compute", "name": "web-server", "size": "large"},
        {"type": "database", "name": "postgres", "size": "medium"}
      ]
    }
  }
}
```

3. **Monitor Health**
```json
{
  "type": "monitor",
  "parameters": {
    "environment": "production",
    "service": "api-service"
  }
}
```

4. **Analyze Logs**
```json
{
  "type": "analyze_logs",
  "parameters": {
    "environment": "production",
    "service": "api-service",
    "options": {
      "time_range": "1h",
      "severity": "error|warning|info"
    }
  }
}
```

5. **Rollback Deployment**
```json
{
  "type": "rollback",
  "parameters": {
    "environment": "production",
    "service": "api-service",
    "options": {
      "target_version": "1.1.0"
    }
  }
}
```

## Webhooks

Configure webhooks to receive real-time notifications about agent activities.

### Register Webhook

```http
POST /webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/ymera",
  "events": ["task.completed", "task.failed", "agent.error"],
  "secret": "your_webhook_secret"
}
```

### Webhook Events

**task.completed**:
```json
{
  "event": "task.completed",
  "timestamp": "2025-10-26T15:00:00Z",
  "task_id": "task_001",
  "agent_id": "code_gen_001",
  "result": { ... }
}
```

**task.failed**:
```json
{
  "event": "task.failed",
  "timestamp": "2025-10-26T15:00:00Z",
  "task_id": "task_002",
  "agent_id": "devops_001",
  "error": "Deployment failed: Connection timeout"
}
```

## Error Handling

All errors return standard HTTP status codes with detailed error messages.

**Error Response Format**:
```json
{
  "error": {
    "code": "invalid_request",
    "message": "Invalid agent type specified",
    "details": {
      "field": "type",
      "allowed_values": ["code_generation", "devops", "monitoring"]
    }
  }
}
```

**Common Error Codes**:
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

API requests are rate-limited per API key:
- **Standard**: 1,000 requests/hour
- **Professional**: 10,000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1635264000
```

## SDK Libraries

Official SDK libraries are available for:
- Python: `pip install ymera-sdk`
- JavaScript/Node.js: `npm install @ymera/sdk`
- Go: `go get github.com/ymera/sdk-go`
- Java: Maven Central

**Python Example**:
```python
from ymera import YmeraClient

client = YmeraClient(api_key="your_api_key")

# Create code generation agent
agent = client.agents.create(type="code_generation")

# Submit task
task = client.tasks.submit(
    agent_id=agent.id,
    type="generate_code",
    parameters={
        "language": "python",
        "specification": "Create a REST API endpoint"
    }
)

# Wait for completion
result = task.wait()
print(result.code)
```

## Versioning

The API is versioned via the URL path. Current version: **v1**

Breaking changes will result in a new API version. We maintain backward compatibility for at least 12 months after a new version is released.

## Support

- **Documentation**: https://docs.ymera.io
- **API Status**: https://status.ymera.io
- **Support Email**: support@ymera.io
- **Community Forum**: https://community.ymera.io

## Changelog

### v1.0.0 (2025-10-26)
- Initial public API release
- Code Generation Agent support
- DevOps Agent support
- Basic monitoring and health checks
- Webhook support
- Multi-tenancy support
