# YMERA Platform - Phase 1: Core Integration

## Overview

Phase 1 implements the core integration of the YMERA Platform, combining:
- **Agent Management API** - Complete CRUD operations for AI agents
- **Task Management** - Task creation, assignment, and tracking
- **Chat System** - Real-time WebSocket-based communication
- **File Management** - File upload, download, and storage

## Features Implemented

### 1. Agent Management
- ✅ Create agents with custom capabilities
- ✅ List and filter agents
- ✅ Update agent status and metadata
- ✅ Delete agents
- ✅ Track agent performance metrics

### 2. Task Management
- ✅ Create tasks with priorities
- ✅ Assign tasks to agents
- ✅ Update task status (pending, in_progress, completed, failed)
- ✅ Track task results and errors
- ✅ List tasks by agent or globally

### 3. Chat System
- ✅ Send chat messages via REST API
- ✅ Real-time WebSocket communication
- ✅ Session-based message organization
- ✅ Chat history retrieval
- ✅ Multi-user session support

### 4. File Management
- ✅ Upload files (temporary or permanent)
- ✅ Download files
- ✅ File metadata tracking
- ✅ Session-based file organization
- ✅ File deletion

### 5. System Monitoring
- ✅ Health check endpoint
- ✅ Platform statistics
- ✅ Real-time metrics

## API Endpoints

### Root & Health
- `GET /` - API information and available endpoints
- `GET /health` - Health check with system statistics

### Agent Management
- `POST /api/v1/agents` - Create a new agent
- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{agent_id}` - Get specific agent
- `PUT /api/v1/agents/{agent_id}` - Update agent
- `DELETE /api/v1/agents/{agent_id}` - Delete agent

### Task Management
- `POST /api/v1/tasks` - Create a new task
- `GET /api/v1/tasks` - List tasks (optional: filter by agent_id)
- `GET /api/v1/tasks/{task_id}` - Get specific task
- `PUT /api/v1/tasks/{task_id}/status` - Update task status

### Chat System
- `POST /api/v1/chat/message` - Send a chat message
- `GET /api/v1/chat/{session_id}/history` - Get chat history
- `WS /ws/{session_id}` - WebSocket connection for real-time chat

### File Management
- `POST /api/v1/files/upload` - Upload a file
- `GET /api/v1/files/{file_id}` - Download a file
- `GET /api/v1/files/{file_id}/metadata` - Get file metadata
- `DELETE /api/v1/files/{file_id}` - Delete a file

### Statistics
- `GET /api/v1/stats` - Get platform statistics

## Quick Start

### Installation

1. **Install dependencies:**
```bash
pip install fastapi uvicorn pydantic sqlalchemy asyncpg redis aiofiles httpx websockets
```

2. **Create uploads directory:**
```bash
mkdir -p uploads/temp uploads/permanent uploads/processed
```

### Running the Server

**Option 1: Using the deployment script**
```bash
./deploy_phase1.sh
```

**Option 2: Direct Python execution**
```bash
python3 phase1_integrated_agent_manager.py
```

The server will start on `http://localhost:8000`

### Accessing the API

- **API Documentation (Swagger UI):** http://localhost:8000/docs
- **Alternative API Documentation (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Usage Examples

### 1. Create an Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Developer Agent",
    "agent_type": "developer",
    "capabilities": [
      {
        "name": "python",
        "level": 9,
        "description": "Python development"
      },
      {
        "name": "fastapi",
        "level": 8,
        "description": "FastAPI framework"
      }
    ],
    "metadata": {
      "department": "engineering"
    }
  }'
```

### 2. Create a Task

```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Implement REST API",
    "description": "Create REST API for user management",
    "task_type": "development",
    "parameters": {
      "framework": "FastAPI",
      "database": "PostgreSQL"
    },
    "priority": "high",
    "agent_id": "YOUR_AGENT_ID_HERE"
  }'
```

### 3. Send a Chat Message

```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "content": "Hello, how can you help me?",
    "message_type": "user"
  }'
```

### 4. Upload a File

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload?session_id=session-123" \
  -F "file=@/path/to/your/file.txt"
```

### 5. Get Platform Statistics

```bash
curl "http://localhost:8000/api/v1/stats"
```

## Testing

Run the comprehensive test suite:

```bash
# Make sure the server is running first
python3 test_phase1.py
```

The test suite includes:
- Health check tests
- Agent lifecycle tests (CRUD operations)
- Task management tests
- Chat system tests
- File upload/download tests
- Statistics endpoint tests

## Architecture

### Technology Stack
- **Framework:** FastAPI
- **Language:** Python 3.12+
- **Async:** asyncio, aiofiles
- **WebSocket:** Native FastAPI WebSocket support
- **Storage:** In-memory (Phase 1), Database (future phases)

### Components

1. **InMemoryStorage**
   - Temporary storage for agents, tasks, files, and chat messages
   - Will be replaced with PostgreSQL database in Phase 3

2. **FileManager**
   - Handles file upload, download, and deletion
   - Supports temporary and permanent storage
   - File metadata tracking

3. **ConnectionManager**
   - Manages WebSocket connections
   - Session-based message broadcasting
   - Automatic cleanup of disconnected clients

4. **API Routes**
   - RESTful endpoints for all operations
   - WebSocket endpoint for real-time chat
   - Comprehensive error handling

## Data Models

### Agent
- `id`: Unique identifier
- `name`: Agent name
- `agent_type`: developer, analyst, tester, reviewer, coordinator, specialist
- `status`: idle, active, busy, error, maintenance, terminated
- `capabilities`: List of capabilities with skill levels
- `metadata`: Custom metadata
- `created_at`, `updated_at`: Timestamps
- Performance metrics (active_tasks, completed_tasks, success_rate)

### Task
- `id`: Unique identifier
- `name`: Task name
- `description`: Task description
- `task_type`: Type of task
- `parameters`: Task-specific parameters
- `priority`: low, normal, high, urgent
- `status`: pending, in_progress, completed, failed, cancelled
- `agent_id`: Assigned agent
- `result`: Task result
- `error_message`: Error details if failed
- `created_at`, `updated_at`, `completed_at`: Timestamps

### Chat Message
- `message_id`: Unique identifier
- `session_id`: Chat session
- `content`: Message content
- `message_type`: user, agent, system
- `attachments`: List of file IDs
- `timestamp`: Message timestamp

### File
- `file_id`: Unique identifier
- `original_filename`: Original file name
- `size`: File size in bytes
- `content_type`: MIME type
- `session_id`: Associated session
- `file_path`: Storage location
- `upload_timestamp`: Upload time
- `temporary`: Temporary or permanent storage

## Performance Considerations

### Current Implementation
- In-memory storage for fast access
- Async operations throughout
- WebSocket for real-time communication
- Efficient file handling with streaming

### Scalability Notes
- In-memory storage is suitable for Phase 1 testing
- For production (Phase 3+):
  - Replace with PostgreSQL database
  - Add Redis for caching
  - Implement connection pooling
  - Add load balancing

## Security Considerations

### Phase 1 Security
- CORS enabled (configured for development)
- File size limits enforced
- Input validation via Pydantic models
- Error handling to prevent information leakage

### Future Enhancements (Phase 3)
- JWT authentication
- Role-based access control (RBAC)
- API key management
- Rate limiting
- File virus scanning
- Encryption at rest

## Known Limitations

1. **Storage:** Uses in-memory storage (data lost on restart)
2. **Authentication:** No authentication implemented yet
3. **Rate Limiting:** No rate limiting in Phase 1
4. **Persistence:** Files and data not persisted across restarts
5. **Scalability:** Single instance only

These limitations will be addressed in subsequent phases.

## Next Steps

### Phase 2: Advanced Features (Coming Next)
- [ ] Learning engine integration
- [ ] Adaptive routing system
- [ ] Enhanced session management
- [ ] Advanced WebSocket features
- [ ] Agent collaboration features

### Phase 3: Enhancement
- [ ] PostgreSQL database integration
- [ ] JWT authentication
- [ ] Rate limiting middleware
- [ ] Enhanced monitoring with Prometheus
- [ ] API documentation improvements

### Phase 4: Production Readiness
- [ ] Comprehensive testing suite
- [ ] Performance optimization
- [ ] Production deployment configuration
- [ ] Docker containerization
- [ ] Kubernetes manifests

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify Python version (3.12+ required)
- Ensure all dependencies are installed

### File upload fails
- Check uploads directory exists and is writable
- Verify file size is under limit (100MB default)
- Check available disk space

### WebSocket connection fails
- Verify server is running
- Check WebSocket URL format: `ws://localhost:8000/ws/{session_id}`
- Ensure firewall allows WebSocket connections

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review the test suite for usage examples
3. Check logs for error details

## License

Part of the YMERA Platform project.

---

**Phase 1 Status:** ✅ COMPLETE AND READY FOR TESTING

**Last Updated:** October 25, 2025

**Version:** 1.0.0
