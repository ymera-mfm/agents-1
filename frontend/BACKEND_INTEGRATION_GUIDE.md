# 🔌 Backend Integration Guide
**AgentFlow Frontend - Backend Integration Manual**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [API Endpoints](#api-endpoints)
5. [WebSocket Integration](#websocket-integration)
6. [Authentication](#authentication)
7. [Data Models](#data-models)
8. [Error Handling](#error-handling)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This guide provides complete instructions for integrating the AgentFlow frontend with your backend services. The frontend is **fully prepared** and waiting for backend connection.

### What's Ready
- ✅ Complete API client with interceptors
- ✅ WebSocket service with reconnection
- ✅ Authentication flow (JWT ready)
- ✅ Error handling and retry logic
- ✅ Loading and error states
- ✅ Backend integration utilities
- ✅ Environment configuration

### What's Needed from Backend
- [ ] RESTful API endpoints (see list below)
- [ ] WebSocket server for real-time features
- [ ] Authentication service (JWT/OAuth)
- [ ] File storage service
- [ ] Database with required models

---

## 🔧 Prerequisites

### Backend Requirements
- **API Server:** RESTful API with JSON responses
- **WebSocket Server:** For real-time updates
- **Authentication:** JWT or OAuth 2.0
- **Database:** PostgreSQL, MongoDB, or similar
- **File Storage:** S3, local storage, or cloud storage
- **CORS:** Properly configured for frontend domain

### Recommended Stack
```
Backend: Node.js/Python/Go/Java
API Framework: Express/FastAPI/Gin/Spring
Database: PostgreSQL/MongoDB
Cache: Redis
WebSocket: Socket.io/ws
File Storage: AWS S3/MinIO
```

---

## 🚀 Quick Start

### Step 1: Configure Environment

Create `.env.production` file:

```env
# API Configuration
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_WS_URL=wss://ws.yourdomain.com
REACT_APP_API_TIMEOUT=10000

# Feature Flags
REACT_APP_ENABLE_3D_VISUALIZATION=true
REACT_APP_ENABLE_REAL_TIME_COLLABORATION=true
REACT_APP_ENABLE_ADVANCED_ANALYTICS=true
REACT_APP_ENABLE_AI_ASSISTANCE=true
REACT_APP_ENABLE_PERFORMANCE_MONITORING=true

# Performance
REACT_APP_MAX_AGENTS=50
REACT_APP_MAX_PROJECTS=100
REACT_APP_CACHE_TIMEOUT=300000

# Analytics
REACT_APP_ANALYTICS_ENABLED=true
REACT_APP_ANALYTICS_SAMPLE_RATE=0.1
REACT_APP_ERROR_REPORTING_ENABLED=true

# Security
REACT_APP_ENABLE_CSP=true
REACT_APP_ENABLE_HTTPS_ONLY=true
REACT_APP_SESSION_TIMEOUT=3600000

# Build
GENERATE_SOURCEMAP=false
INLINE_RUNTIME_CHUNK=false
```

### Step 2: Test Backend Connection

```javascript
import backendIntegration from './utils/backendIntegration';

// Test connection
const testBackend = async () => {
  const result = await backendIntegration.testConnection();
  
  if (result.success) {
    console.log('✅ Backend connected successfully');
  } else {
    console.error('❌ Backend connection failed:', result.error);
  }
};

testBackend();
```

### Step 3: Validate Environment

```bash
# Validate production environment
npm run validate:env:prod

# Run health check
npm run health:check
```

### Step 4: Build and Deploy

```bash
# Build for production
npm run build:prod

# Deploy
npm run deploy:vercel # or your platform
```

---

## 🌐 API Endpoints

The frontend expects the following API endpoints. All responses should be JSON.

### Base URL
```
Production: https://api.yourdomain.com/api/v1
Development: http://localhost:8000/api/v1
```

### 1. Authentication Endpoints

#### POST `/auth/login`
Login user and return JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user123",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "permissions": ["view_dashboard", "view_agents"]
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "refresh_token_here"
  }
}
```

#### POST `/auth/logout`
Logout current user.

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### POST `/auth/refresh`
Refresh expired token.

**Request:**
```json
{
  "refreshToken": "refresh_token_here"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "new_jwt_token",
    "refreshToken": "new_refresh_token"
  }
}
```

### 2. User Endpoints

#### GET `/users/me`
Get current user profile.

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "avatar": "https://cdn.example.com/avatar.jpg",
    "createdAt": "2025-01-01T00:00:00Z"
  }
}
```

#### PUT `/users/:id`
Update user profile.

**Request:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user123",
    "name": "Jane Doe",
    "email": "jane@example.com"
  }
}
```

### 3. Agent Endpoints

#### GET `/agents`
List all agents with pagination.

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `limit` (number): Items per page (default: 20)
- `status` (string): Filter by status (optional)
- `type` (string): Filter by type (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "id": "agent123",
        "name": "Code Generator Agent",
        "type": "coder",
        "status": "active",
        "description": "Generates code based on requirements",
        "capabilities": ["code_generation", "debugging"],
        "metrics": {
          "tasksCompleted": 150,
          "successRate": 0.95,
          "avgExecutionTime": 45
        },
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-15T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

#### POST `/agents`
Create new agent.

**Request:**
```json
{
  "name": "New Agent",
  "type": "coder",
  "description": "Agent description",
  "config": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "agent124",
    "name": "New Agent",
    "type": "coder",
    "status": "idle",
    "createdAt": "2025-01-20T00:00:00Z"
  }
}
```

#### GET `/agents/:id`
Get specific agent details.

#### PUT `/agents/:id`
Update agent configuration.

#### DELETE `/agents/:id`
Delete agent.

#### POST `/agents/:id/execute`
Execute agent task.

**Request:**
```json
{
  "task": "Generate a React component",
  "parameters": {
    "componentName": "UserCard",
    "props": ["name", "email", "avatar"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "executionId": "exec123",
    "status": "started",
    "estimatedTime": 30
  }
}
```

#### POST `/agents/:id/stop`
Stop running agent.

#### GET `/agents/:id/status`
Get agent current status.

#### GET `/agents/:id/logs`
Get agent execution logs.

#### GET `/agents/:id/metrics`
Get agent performance metrics.

### 4. Project Endpoints

#### GET `/projects`
List all projects.

**Response:**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "proj123",
        "name": "E-commerce Platform",
        "description": "Online shopping platform",
        "status": "active",
        "progress": 75,
        "agents": ["agent123", "agent124"],
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-20T00:00:00Z",
        "builds": {
          "total": 45,
          "successful": 42,
          "failed": 3
        }
      }
    ]
  }
}
```

#### POST `/projects`
Create new project.

#### GET `/projects/:id`
Get project details.

#### PUT `/projects/:id`
Update project.

#### DELETE `/projects/:id`
Delete project.

#### POST `/projects/:id/build`
Trigger project build.

**Request:**
```json
{
  "branch": "main",
  "environment": "production"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "buildId": "build123",
    "status": "queued",
    "estimatedTime": 120
  }
}
```

#### POST `/projects/:id/deploy`
Deploy project.

#### GET `/projects/:id/history`
Get project history/timeline.

#### GET `/projects/:id/files`
List project files.

### 5. Chat Endpoints

#### GET `/chat/conversations`
List user conversations.

#### POST `/chat/conversations/:id/send`
Send message.

**Request:**
```json
{
  "message": "Hello, can you help with this code?",
  "type": "text",
  "attachments": []
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "messageId": "msg123",
    "timestamp": "2025-01-20T10:00:00Z",
    "status": "sent"
  }
}
```

#### GET `/chat/conversations/:id/messages`
Get conversation messages.

#### GET `/chat/conversations/:id/history`
Get conversation history.

### 6. File Endpoints

#### POST `/files/upload`
Upload file.

**Request:** multipart/form-data
```
file: [binary data]
projectId: "proj123"
category: "source_code"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "fileId": "file123",
    "filename": "component.jsx",
    "size": 1024,
    "url": "https://cdn.example.com/files/file123",
    "uploadedAt": "2025-01-20T10:00:00Z"
  }
}
```

#### GET `/files/:id/download`
Download file.

#### DELETE `/files/:id`
Delete file.

#### GET `/files`
List files.

#### GET `/files/:id/metadata`
Get file metadata.

### 7. Analytics Endpoints

#### GET `/analytics/dashboard`
Get dashboard analytics.

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "totalAgents": 45,
      "activeAgents": 32,
      "totalProjects": 18,
      "activeProjects": 12
    },
    "metrics": {
      "agentSuccessRate": 0.94,
      "avgTaskTime": 42,
      "projectCompletionRate": 0.89
    },
    "trends": {
      "daily": [...],
      "weekly": [...],
      "monthly": [...]
    }
  }
}
```

#### GET `/analytics/agents`
Get agent analytics.

#### GET `/analytics/projects`
Get project analytics.

#### GET `/analytics/performance`
Get performance metrics.

### 8. Monitoring Endpoints

#### GET `/monitoring/health`
System health check.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-01-20T10:00:00Z",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "storage": "healthy"
  },
  "metrics": {
    "uptime": 99.99,
    "responseTime": 45
  }
}
```

#### GET `/monitoring/metrics`
Get system metrics.

#### GET `/monitoring/alerts`
Get active alerts.

#### GET `/monitoring/logs`
Get system logs.

#### GET `/monitoring/status`
Get component statuses.

### 9. System Endpoints

#### GET `/system/info`
Get system information.

#### GET `/system/config`
Get system configuration.

#### GET `/system/health`
Health check endpoint.

#### GET `/system/version`
Get API version.

---

## 🔌 WebSocket Integration

### Connection Setup

The frontend expects a WebSocket server at the configured URL.

**WebSocket URL:**
```
Production: wss://ws.yourdomain.com
Development: ws://localhost:8000/ws
```

### Connection Protocol

```javascript
// Frontend automatically connects using:
import { useWebSocket } from './hooks/useWebSocket';

function MyComponent() {
  const { socket, isConnected } = useWebSocket();
  
  useEffect(() => {
    if (isConnected) {
      // Subscribe to channels
      socket.emit('subscribe', { channel: 'agents' });
    }
  }, [isConnected]);
}
```

### Event Types

#### Agent Events
```javascript
// Agent created
{
  event: 'agent:created',
  data: {
    id: 'agent123',
    name: 'New Agent',
    type: 'coder'
  }
}

// Agent status changed
{
  event: 'agent:status:changed',
  data: {
    id: 'agent123',
    status: 'active',
    previousStatus: 'idle'
  }
}

// Agent execution started
{
  event: 'agent:execution:started',
  data: {
    agentId: 'agent123',
    executionId: 'exec123',
    task: 'Generate component'
  }
}

// Agent execution completed
{
  event: 'agent:execution:completed',
  data: {
    agentId: 'agent123',
    executionId: 'exec123',
    result: {...},
    duration: 45
  }
}
```

#### Project Events
```javascript
// Project build started
{
  event: 'project:build:started',
  data: {
    projectId: 'proj123',
    buildId: 'build123',
    branch: 'main'
  }
}

// Project build progress
{
  event: 'project:build:progress',
  data: {
    projectId: 'proj123',
    buildId: 'build123',
    progress: 45,
    stage: 'compiling'
  }
}

// Project build completed
{
  event: 'project:build:completed',
  data: {
    projectId: 'proj123',
    buildId: 'build123',
    status: 'success',
    duration: 120
  }
}
```

#### Chat Events
```javascript
// Message received
{
  event: 'chat:message:received',
  data: {
    conversationId: 'conv123',
    messageId: 'msg123',
    from: 'agent123',
    message: 'Hello!',
    timestamp: '2025-01-20T10:00:00Z'
  }
}

// User typing
{
  event: 'chat:user:typing',
  data: {
    conversationId: 'conv123',
    userId: 'user123',
    isTyping: true
  }
}
```

#### System Events
```javascript
// System alert
{
  event: 'system:alert',
  data: {
    level: 'warning',
    message: 'High CPU usage detected',
    timestamp: '2025-01-20T10:00:00Z'
  }
}

// System update
{
  event: 'system:update',
  data: {
    type: 'config_changed',
    changes: {...}
  }
}
```

### Channel Subscriptions

Backend should support these channels:
- `agents` - Agent updates
- `projects` - Project updates
- `chat` - Chat messages
- `notifications` - User notifications
- `monitoring` - System monitoring
- `system` - System events

---

## 🔐 Authentication

### JWT Token Format

**Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Payload (expected):**
```json
{
  "sub": "user123",
  "email": "user@example.com",
  "role": "user",
  "permissions": ["view_dashboard", "view_agents"],
  "iat": 1705744800,
  "exp": 1705831200
}
```

### Token Refresh Flow

1. Frontend detects token expiration
2. Sends refresh request with refresh token
3. Backend validates and returns new tokens
4. Frontend updates stored tokens
5. Retries failed request with new token

### Protected Routes

Frontend implements authentication guards for:
- All pages except Login
- API requests automatically include token
- WebSocket connection includes token

---

## 📦 Data Models

### User Model
```typescript
interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer';
  avatar?: string;
  permissions: string[];
  preferences: {
    theme: 'dark' | 'light';
    notifications: boolean;
    language: string;
  };
  createdAt: string;
  updatedAt: string;
}
```

### Agent Model
```typescript
interface Agent {
  id: string;
  name: string;
  type: 'coder' | 'analyst' | 'security' | 'designer' | 'tester' | 'devops';
  status: 'idle' | 'active' | 'busy' | 'error' | 'offline';
  description: string;
  capabilities: string[];
  config: {
    model: string;
    temperature: number;
    maxTokens: number;
  };
  metrics: {
    tasksCompleted: number;
    successRate: number;
    avgExecutionTime: number;
  };
  createdAt: string;
  updatedAt: string;
}
```

### Project Model
```typescript
interface Project {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'completed' | 'archived';
  progress: number; // 0-100
  agents: string[]; // Agent IDs
  builds: {
    total: number;
    successful: number;
    failed: number;
    lastBuild: {
      id: string;
      status: string;
      timestamp: string;
    };
  };
  createdAt: string;
  updatedAt: string;
}
```

### Message Model
```typescript
interface Message {
  id: string;
  conversationId: string;
  from: string; // User or Agent ID
  message: string;
  type: 'text' | 'code' | 'file';
  attachments?: Array<{
    id: string;
    name: string;
    url: string;
  }>;
  timestamp: string;
}
```

---

## ⚠️ Error Handling

### Error Response Format

All errors should follow this format:

```json
{
  "success": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Authentication failed",
    "details": "Invalid credentials provided",
    "statusCode": 401
  }
}
```

### Error Codes

Frontend handles these error codes:
- `AUTH_FAILED` - Authentication failure
- `UNAUTHORIZED` - No permission
- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Input validation failed
- `RATE_LIMIT` - Too many requests
- `SERVER_ERROR` - Internal server error
- `TIMEOUT` - Request timeout
- `NETWORK_ERROR` - Network issue

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Too Many Requests
- `500` - Server Error
- `503` - Service Unavailable

---

## 🧪 Testing

### Test Backend Connection

```bash
# Test API health
curl -X GET https://api.yourdomain.com/api/v1/system/health

# Test authentication
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### Integration Tests

```bash
# Run E2E tests with backend
PLAYWRIGHT_BASE_URL=https://yourdomain.com npm run test:e2e

# Run specific test
npm run test:e2e -- tests/auth.spec.js
```

### Manual Testing Checklist

- [ ] Login/logout flow
- [ ] API endpoint responses
- [ ] WebSocket connection
- [ ] Real-time updates
- [ ] File upload/download
- [ ] Error handling
- [ ] Token refresh
- [ ] CORS configuration

---

## 🚀 Deployment

### CORS Configuration

Backend must allow requests from frontend domain:

```javascript
// Example CORS configuration
{
  origin: [
    'https://yourdomain.com',
    'https://app.yourdomain.com'
  ],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}
```

### SSL/TLS

- Use HTTPS for API (required in production)
- Use WSS for WebSocket (required in production)
- Valid SSL certificate

### Environment Variables

Backend should support these:
```env
API_PORT=8000
WS_PORT=8001
JWT_SECRET=your_secret_key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CORS_ORIGIN=https://yourdomain.com
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. CORS Errors
**Symptom:** Browser console shows CORS policy errors

**Solution:**
- Check backend CORS configuration
- Ensure origin is whitelisted
- Verify credentials are allowed
- Check preflight OPTIONS requests

#### 2. WebSocket Connection Failed
**Symptom:** WebSocket doesn't connect

**Solution:**
- Verify WSS URL is correct
- Check firewall/proxy settings
- Ensure WebSocket server is running
- Test connection manually

#### 3. Authentication Errors
**Symptom:** 401 Unauthorized errors

**Solution:**
- Check token format
- Verify token hasn't expired
- Ensure refresh token works
- Check Authorization header

#### 4. API Timeouts
**Symptom:** Requests timeout

**Solution:**
- Increase timeout in .env
- Optimize backend response time
- Check network connectivity
- Enable request caching

### Debug Mode

Enable debug mode for detailed logs:

```env
REACT_APP_DEBUG_MODE=true
REACT_APP_LOG_LEVEL=debug
```

### Support

For issues:
1. Check browser console for errors
2. Review network tab in DevTools
3. Check backend logs
4. Enable frontend debug mode
5. Contact development team

---

## 📞 Support & Resources

### Documentation
- [System Diagnostics Report](./SYSTEM_DIAGNOSTICS_REPORT.md)
- [README.md](./README.md)
- [API Documentation](./docs/)

### Code Examples
- [Backend Integration Utils](./src/utils/backendIntegration.js)
- [API Service](./src/services/api.js)
- [WebSocket Hook](./src/hooks/useWebSocket.js)

### Contact
- GitHub Issues
- Development Team
- Documentation

---

**Last Updated:** October 25, 2025  
**Version:** 1.0  
**Status:** Production Ready
