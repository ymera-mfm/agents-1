# Frontend-Backend Integration Guide

## ✅ Integration Complete

The YMERA Multi-Agent AI System now has both frontend and backend fully integrated.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     YMERA AI System                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Frontend   │◄───────►│   Backend    │                 │
│  │  React App   │  HTTP   │  FastAPI     │                 │
│  │  Port: 80    │  WS     │  Port: 8000  │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│                          ┌────────┴────────┐                │
│                          │                 │                 │
│                   ┌──────▼─────┐   ┌──────▼─────┐          │
│                   │ PostgreSQL │   │   Redis    │          │
│                   │ Port: 5432 │   │ Port: 6379 │          │
│                   └────────────┘   └────────────┘          │
│                                                              │
│                   ┌─────────────┐  ┌────────────┐          │
│                   │    NATS     │  │ Prometheus │          │
│                   │ Port: 4222  │  │ Port: 9090 │          │
│                   └─────────────┘  └────────────┘          │
│                                                              │
│                          ┌─────────────┐                    │
│                          │   Grafana   │                    │
│                          │ Port: 3001  │                    │
│                          └─────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

Start the entire system with one command:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Services will be available at:
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs
- **WebSocket**: ws://localhost:8000/ws
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

### Option 2: Manual Setup

#### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start infrastructure services:
```bash
docker-compose up -d postgres redis nats
```

3. Setup environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the backend:
```bash
python main.py
```

Backend will be available at http://localhost:8000

#### Frontend Setup

1. Install Node dependencies:
```bash
cd frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and set:
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

3. Start the frontend:
```bash
npm start
```

Frontend will be available at http://localhost:3000

## 🔌 API Integration

### REST API Endpoints

The backend provides the following key endpoints:

- **GET /api/v1/health** - Health check
- **GET /api/v1/system/info** - System information
- **GET /api/v1/agents** - List all agents
- **POST /api/v1/agents** - Create new agent
- **GET /api/v1/agents/{id}** - Get agent details
- **DELETE /api/v1/agents/{id}** - Delete agent
- **GET /api/v1/projects** - List all projects

Complete API documentation: http://localhost:8000/api/v1/docs

### WebSocket Integration

The WebSocket endpoint is available at `ws://localhost:8000/ws`

**Connection Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to backend');
  
  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'agents'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

**Event Types:**
- `agent:created` - New agent created
- `agent:deleted` - Agent deleted
- `agent:status:changed` - Agent status updated
- `project:build:started` - Project build started
- `project:build:completed` - Project build completed

## 📊 Features Integrated

### ✅ Real-time Communication
- WebSocket connection between frontend and backend
- Live agent status updates
- Real-time project monitoring
- Broadcast messaging to all connected clients

### ✅ API Integration
- RESTful API for CRUD operations
- JSON response format matching frontend expectations
- Error handling and validation
- CORS enabled for cross-origin requests

### ✅ Infrastructure
- PostgreSQL for persistent storage
- Redis for caching
- NATS for message broker
- Prometheus for metrics
- Grafana for visualization

## 🧪 Testing the Integration

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "YMERA Multi-Agent AI System",
  "version": "1.0.0",
  "environment": "development"
}
```

### 2. List Agents

```bash
curl http://localhost:8000/api/v1/agents
```

Expected response:
```json
{
  "success": true,
  "data": {
    "agents": [],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 0,
      "pages": 0
    }
  }
}
```

### 3. WebSocket Test

Use the browser console or a WebSocket client:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => ws.send(JSON.stringify({type: 'ping'}));
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## 🔧 Configuration

### Backend Environment Variables

Key variables in `.env`:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_HOST` - Redis server host
- `NATS_SERVERS` - NATS server URLs
- `API_HOST` - API server host (default: 0.0.0.0)
- `API_PORT` - API server port (default: 8000)
- `DEBUG` - Debug mode (true/false)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Frontend Environment Variables

Key variables in `frontend/.env`:
- `REACT_APP_API_URL` - Backend API URL
- `REACT_APP_WS_URL` - WebSocket URL
- `REACT_APP_ENABLE_3D_VISUALIZATION` - Enable 3D features
- `REACT_APP_ENABLE_REAL_TIME_COLLABORATION` - Enable real-time features

## 📈 Monitoring

### Prometheus Metrics

Access Prometheus at http://localhost:9090

Key metrics:
- API request rates
- Response times
- Error rates
- WebSocket connections
- Database query performance

### Grafana Dashboards

Access Grafana at http://localhost:3001 (admin/admin)

Pre-configured dashboards:
- System overview
- API performance
- Database metrics
- WebSocket connections

### Frontend Performance

Built-in performance monitoring in the frontend:
- Page load times
- Component render times
- API request latency
- WebSocket message latency

## 🐛 Troubleshooting

### Backend Won't Start

1. Check if ports are available:
```bash
lsof -i :8000  # API port
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :4222  # NATS
```

2. Check logs:
```bash
docker-compose logs backend
```

3. Verify database connection:
```bash
docker-compose exec postgres psql -U postgres -d ymera
```

### Frontend Can't Connect to Backend

1. Verify backend is running:
```bash
curl http://localhost:8000/api/v1/health
```

2. Check CORS configuration in `main.py`

3. Verify environment variables in `frontend/.env`:
```bash
cat frontend/.env | grep REACT_APP_API_URL
```

### WebSocket Connection Fails

1. Check WebSocket endpoint:
```bash
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  http://localhost:8000/ws
```

2. Check browser console for errors

3. Verify firewall/proxy settings

## 🚀 Next Steps

### For Development

1. **Add Authentication**
   - Implement JWT authentication in backend
   - Add login/logout in frontend
   - Protect API endpoints

2. **Implement Agent Operations**
   - Create actual agent instances
   - Add agent execution logic
   - Implement task queue

3. **Add Project Management**
   - Create project CRUD operations
   - Implement build pipeline
   - Add deployment logic

4. **Enhance Real-time Features**
   - Add more WebSocket events
   - Implement chat functionality
   - Add collaborative editing

### For Production

1. **Security Hardening**
   - Enable HTTPS
   - Implement rate limiting
   - Add request validation
   - Setup firewall rules

2. **Performance Optimization**
   - Add caching layer
   - Implement connection pooling
   - Optimize database queries
   - Enable CDN for frontend

3. **Monitoring & Alerting**
   - Configure alerting rules
   - Setup log aggregation
   - Add error tracking (Sentry)
   - Implement health checks

4. **Deployment**
   - Setup CI/CD pipeline
   - Configure Kubernetes manifests
   - Implement blue-green deployment
   - Add automated testing

## 📚 Additional Resources

- **Backend API Docs**: http://localhost:8000/api/v1/docs
- **Frontend Guide**: [frontend/README.md](frontend/README.md)
- **Backend Integration**: [frontend/BACKEND_INTEGRATION_GUIDE.md](frontend/BACKEND_INTEGRATION_GUIDE.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## ✅ Integration Checklist

- [x] Backend API running on port 8000
- [x] Frontend application built and configured
- [x] WebSocket endpoint implemented
- [x] CORS enabled for frontend-backend communication
- [x] Docker Compose configuration for full stack
- [x] Database migrations ready
- [x] Monitoring infrastructure setup
- [x] Documentation complete

**Status: 🎉 Integration Complete and Ready for Development!**
