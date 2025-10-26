# YMERA Learning Agent - Complete Integration & Deployment Guide

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [API Documentation](#api-documentation)
7. [Integration Examples](#integration-examples)
8. [Monitoring & Maintenance](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Production Checklist](#production-checklist)

---

## 🎯 System Overview

The YMERA Learning Agent is a production-ready, intelligent coordination system for managing knowledge, performance analysis, and real-time communication across 15+ specialized agents in your project management platform.

### Key Capabilities
- **Multi-Agent Coordination**: Manages 15+ specialized agents (developers, testers, reviewers, architects, etc.)
- **Knowledge Management**: Captures, validates, and distributes knowledge across agents
- **Performance Analytics**: Real-time analysis of agent performance with actionable recommendations
- **Live Chat System**: Real-time communication with users and agents via REST API and WebSockets
- **Continuous Learning**: Automated knowledge extraction from experiences
- **Collaboration Network**: Facilitates inter-agent collaboration and knowledge transfer

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional but recommended)

### 5-Minute Setup

```bash
# 1. Clone and setup
git clone <repository>
cd ymera-learning-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Initialize database
alembic upgrade head

# 6. Start the service
uvicorn learning_agent_api:app --host 0.0.0.0 --port 8000
```

**With Docker (Recommended for Production):**

```bash
# 1. Configure environment
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Check health
curl http://localhost:8000/health
```

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    YMERA Learning Agent                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   REST API  │  │   WebSocket  │  │  Background Tasks│  │
│  │   FastAPI   │  │  Real-time   │  │   AsyncIO Loops  │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │             │
│  ┌──────▼─────────────────▼────────────────────▼─────────┐ │
│  │           Learning Agent Core Engine                   │ │
│  │  • Knowledge Management  • Performance Analysis        │ │
│  │  • Chat Processing       • Agent Coordination          │ │
│  └──────┬─────────────────────────────────────┬──────────┘ │
│         │                                      │             │
└─────────┼──────────────────────────────────────┼────────────┘
          │                                      │
    ┌─────▼──────┐                        ┌─────▼──────┐
    │ PostgreSQL │                        │   Redis    │
    │  Database  │                        │   Cache    │
    └────────────┘                        └────────────┘
```

### Data Flow

```
User/Agent → REST API/WebSocket → Learning Engine → Database/Cache
                                        ↓
                              Knowledge Processing
                                        ↓
                              Performance Analysis
                                        ↓
                          Distribution to Target Agents
```

---

## 💾 Installation

### Method 1: Manual Installation

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    postgresql-15 \
    redis-server \
    gcc \
    g++ \
    libpq-dev

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Setup PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE ymera_learning;"
sudo -u postgres psql -c "CREATE USER ymera WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ymera_learning TO ymera;"

# Run database migrations
alembic upgrade head
```

### Method 2: Docker Installation (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f learning-agent-api

# Scale service
docker-compose up -d --scale learning-agent-api=3
```

### Method 3: Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace ymera

# Apply configurations
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Check deployment
kubectl get pods -n ymera
kubectl logs -f deployment/learning-agent -n ymera
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ymera_learning
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here

# Features
ENABLE_WEBSOCKETS=true
ENABLE_METRICS=true
ENABLE_AUTO_LEARNING=true

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=30
CACHE_TTL=300
```

### Application Configuration

Create `config.yaml`:

```yaml
learning_agent:
  agent_id: learning_agent_001
  knowledge_retention_days: 90
  auto_distribution: true
  
performance:
  analysis_window_days: 7
  metrics_collection_interval: 300
  
knowledge:
  min_confidence_threshold: 0.7
  max_items_per_agent: 10000
  auto_validation: true
  
chat:
  max_history_size: 1000
  enable_learning_extraction: true
  websocket_timeout: 300
```

---

## 📚 API Documentation

### Base URL
```
Production: https://api.ymera.com/learning
Development: http://localhost:8000
```

### Authentication
```bash
# All requests require API key
curl -H "X-API-Key: your-api-key" http://localhost:8000/agents
```

### Core Endpoints

#### 1. Agent Management

**Register Agent**
```bash
POST /agents/register
Content-Type: application/json

{
  "role": "developer",
  "specializations": ["python", "backend", "api"],
  "learning_preferences": {
    "auto_learn": true,
    "share_knowledge": true
  }
}

Response:
{
  "success": true,
  "agent_id": "dev_agent_001",
  "message": "Agent registered successfully as developer"
}
```

**List Agents**
```bash
GET /agents

Response:
{
  "total": 5,
  "agents": [
    {
      "agent_id": "dev_agent_001",
      "role": "developer",
      "specializations": ["python", "backend"],
      "active": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

**Get Agent Details**
```bash
GET /agents/{agent_id}

Response:
{
  "agent_id": "dev_agent_001",
  "role": "developer",
  "specializations": ["python", "backend"],
  "knowledge_base": {...},
  "performance_metrics": {
    "tasks_completed": 150,
    "success_rate": 0.92,
    "learning_velocity": 0.45
  }
}
```

**Analyze Agent Performance**
```bash
POST /agents/{agent_id}/analyze
Content-Type: application/json

{
  "agent_id": "dev_agent_001",
  "time_window_days": 7
}

Response:
{
  "agent_id": "dev_agent_001",
  "role": "developer",
  "analysis_period": "7 days",
  "performance_metrics": {
    "tasks_completed": 42,
    "success_rate": 0.93,
    "learning_velocity": 0.52,
    "collaboration_score": 0.78
  },
  "knowledge_quality": {
    "average_confidence": 0.87,
    "average_success_rate": 0.91,
    "total_knowledge_items": 15
  },
  "strengths": [
    "High task success rate",
    "Excellent collaboration skills"
  ],
  "improvement_areas": [
    "Knowledge sharing participation"
  ],
  "recommendations": [
    {
      "recommendation": "Contribute to knowledge base weekly",
      "action": "Document successful approaches",
      "priority": "high"
    }
  ],
  "trend": "improving"
}
```

#### 2. Knowledge Management

**Capture Knowledge**
```bash
POST /knowledge/capture
Content-Type: application/json

{
  "source_agent": "dev_agent_001",
  "category": "code_pattern",
  "content": {
    "title": "Efficient API Error Handling",
    "description": "Best practice for structured error responses",
    "code_example": "try/except with custom exceptions",
    "applicable_to": ["developer", "backend"]
  },
  "confidence": 0.9
}

Response:
{
  "success": true,
  "knowledge_id": "know_12345",
  "message": "Knowledge captured successfully"
}
```

**Search Knowledge**
```bash
POST /knowledge/search
Content-Type: application/json

{
  "category": "technical",
  "keywords": ["api", "error", "handling"],
  "min_confidence": 0.7,
  "agent_role": "developer",
  "limit": 10
}

Response:
{
  "total": 3,
  "results": [
    {
      "knowledge_id": "know_12345",
      "category": "code_pattern",
      "source_agent": "dev_agent_001",
      "content": {...},
      "confidence_score": 0.9,
      "usage_count": 15,
      "success_rate": 0.88
    }
  ]
}
```

**Distribute Knowledge**
```bash
POST /knowledge/{knowledge_id}/distribute
Content-Type: application/json

{
  "target_agents": ["dev_agent_002", "dev_agent_003"]
}

Response:
{
  "success": true,
  "distribution_results": {
    "knowledge_id": "know_12345",
    "targets": 2,
    "successful": 2,
    "failed": 0
  }
}
```

#### 3. Live Chat

**Send Chat Message**
```bash
POST /chat/message
Content-Type: application/json

{
  "sender_id": "user_001",
  "sender_type": "user",
  "content": "How can I improve my testing approach?",
  "context": {
    "current_project": "mobile_app",
    "role": "tester"
  }
}

Response:
{
  "success": true,
  "response": "Here are some recommendations for improving your testing approach...",
  "suggestions": [
    "Implement automated regression tests",
    "Use behavior-driven development (BDD)",
    "Review testing patterns from high-performing agents"
  ],
  "knowledge_items": ["know_456", "know_789"]
}
```

**WebSocket Connection**
```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws/chat/user_001');

ws.onopen = () => {
  ws.send(JSON.stringify({
    sender_id: 'user_001',
    sender_type: 'user',
    content: 'What's the best way to handle API errors?',
    context: {}
  }));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log('Response:', response.response);
};
```

**Get Chat History**
```bash
GET /chat/history?sender_id=user_001&limit=50

Response:
{
  "total": 12,
  "messages": [
    {
      "message_id": "msg_001",
      "sender_id": "user_001",
      "content": "How can I improve testing?",
      "learning_intent": "performance_feedback",
      "timestamp": "2024-01-15T10:30:00Z",
      "processed": true
    }
  ]
}
```

#### 4. Analytics

**Learning Velocity**
```bash
GET /analytics/learning-velocity

Response:
{
  "average_system_velocity": 0.523,
  "by_agent": {
    "dev_agent_001": {
      "learning_velocity": 0.62,
      "knowledge_contribution": 18
    },
    "test_agent_001": {
      "learning_velocity": 0.45,
      "knowledge_contribution": 12
    }
  }
}
```

**Collaboration Network**
```bash
GET /analytics/collaboration-network

Response:
{
  "network": {
    "dev_agent_001": {
      "total_collaborations": 45,
      "recent_collaborators": ["test_agent_001", "review_agent_001"],
      "collaboration_score": 0.78
    }
  }
}
```

#### 5. System Status

**Health Check**
```bash
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "service": "learning-agent-api",
  "version": "5.0.0"
}
```

**System Status**
```bash
GET /status

Response:
{
  "agent_id": "learning_agent_001",
  "initialized": true,
  "running": true,
  "statistics": {
    "total_agents": 15,
    "active_agents": 14,
    "total_knowledge_items": 342,
    "learning_sessions": 28,
    "chat_messages": 156
  },
  "metrics": {
    "total_knowledge_items": 342,
    "successful_transfers": 89,
    "failed_transfers": 2,
    "average_confidence": 0.84
  }
}
```

---

## 🔌 Integration Examples

### Python Integration

```python
import asyncio
import aiohttp

class LearningAgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_key = "your-api-key"
    
    async def register_agent(self, role, specializations):
        """Register a new agent"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/agents/register",
                json={
                    "role": role,
                    "specializations": specializations
                },
                headers={"X-API-Key": self.api_key}
            ) as response:
                return await response.json()
    
    async def capture_knowledge(self, agent_id, category, content, confidence=0.8):
        """Capture knowledge from agent"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/knowledge/capture",
                json={
                    "source_agent": agent_id,
                    "category": category,
                    "content": content,
                    "confidence": confidence
                },
                headers={"X-API-Key": self.api_key}
            ) as response:
                return await response.json()
    
    async def chat(self, sender_id, message):
        """Send chat message"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/message",
                json={
                    "sender_id": sender_id,
                    "sender_type": "agent",
                    "content": message
                },
                headers={"X-API-Key": self.api_key}
            ) as response:
                return await response.json()

# Usage
async def main():
    client = LearningAgentClient()
    
    # Register agent
    result = await client.register_agent(
        role="developer",
        specializations=["python", "backend"]
    )
    agent_id = result["agent_id"]
    
    # Capture knowledge
    await client.capture_knowledge(
        agent_id=agent_id,
        category="best_practice",
        content={
            "title": "Code Review Best Practices",
            "description": "Always review security implications",
            "applicable_to": ["developer", "reviewer"]
        }
    )
    
    # Chat with learning agent
    response = await client.chat(
        sender_id=agent_id,
        message="What are my performance metrics?"
    )
    print(response["response"])

asyncio.run(main())
```

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');
const WebSocket = require('ws');

class LearningAgentClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.apiKey = 'your-api-key';
    this.headers = { 'X-API-Key': this.apiKey };
  }

  async registerAgent(role, specializations) {
    const response = await axios.post(
      `${this.baseUrl}/agents/register`,
      { role, specializations },
      { headers: this.headers }
    );
    return response.data;
  }

  async searchKnowledge(query) {
    const response = await axios.post(
      `${this.baseUrl}/knowledge/search`,
      query,
      { headers: this.headers }
    );
    return response.data;
  }

  connectWebSocket(clientId, onMessage) {
    const ws = new WebSocket(`ws://localhost:8000/ws/chat/${clientId}`);
    
    ws.on('open', () => console.log('Connected to Learning Agent'));
    ws.on('message', (data) => onMessage(JSON.parse(data)));
    ws.on('error', (error) => console.error('WebSocket error:', error));
    
    return ws;
  }
}

// Usage
(async () => {
  const client = new LearningAgentClient();
  
  // Register agent
  const agent = await client.registerAgent('tester', ['automation', 'qa']);
  console.log('Agent registered:', agent.agent_id);
  
  // Search knowledge
  const knowledge = await client.searchKnowledge({
    keywords: ['testing', 'automation'],
    min_confidence: 0.7,
    limit: 5
  });
  console.log('Found knowledge:', knowledge.results.length);
  
  // Connect WebSocket
  const ws = client.connectWebSocket('agent_001', (message) => {
    console.log('Received:', message.response);
  });
  
  ws.send(JSON.stringify({
    sender_id: 'agent_001',
    content: 'Show my performance analysis'
  }));
})();
```

---

## 📊 Monitoring & Maintenance

### Prometheus Metrics

Access metrics at: `http://localhost:8000/metrics`

Key metrics:
- `learning_agent_active_agents`: Number of active agents
- `learning_agent_knowledge_items_total`: Total knowledge items
- `learning_agent_chat_messages_total`: Total chat messages processed
- `learning_agent_knowledge_transfers_total`: Knowledge transfer count
- `learning_agent_api_requests_total`: API request count by endpoint

### Grafana Dashboards

1. **System Overview Dashboard**
   - Active agents count
   - Knowledge creation rate
   - Chat activity
   - API performance

2. **Agent Performance Dashboard**
   - Success rates by agent
   - Learning velocity trends
   - Collaboration network graph

3. **Knowledge Analytics Dashboard**
   - Knowledge by category
   - Usage patterns
   - Success rates

### Logging

```bash
# View logs
docker-compose logs -f learning-agent-api

# Filter by level
docker-compose logs learning-agent-api | grep ERROR

# Export logs
docker-compose logs --no-color learning-agent-api > logs.txt
```

### Database Maintenance

```bash
# Backup database
docker exec ymera-postgres pg_dump -U postgres ymera_learning > backup.sql

# Restore database
docker exec -i ymera-postgres psql -U postgres ymera_learning < backup.sql

# Vacuum database
docker exec ymera-postgres psql -U postgres ymera_learning -c "VACUUM ANALYZE;"
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection
docker exec ymera-postgres psql -U postgres -c "SELECT 1;"

# Verify credentials in .env
cat .env | grep DATABASE_URL
```

**2. Redis Connection Issues**
```bash
# Check Redis
docker exec ymera-redis redis-cli ping

# Clear Redis cache
docker exec ymera-redis redis-cli FLUSHALL
```

**3. High Memory Usage**
```bash
# Check container stats
docker stats ymera-learning-agent

# Restart service
docker-compose restart learning-agent-api
```

**4. API Timeout**
```bash
# Increase timeout in config
# In docker-compose.yml, add:
environment:
  - REQUEST_TIMEOUT=60
```

### Debug Mode

```bash
# Enable debug logging
docker-compose down
docker-compose up -e DEBUG=true -e LOG_LEVEL=DEBUG
```

---

## ✅ Production Checklist

### Pre-Deployment

- [ ] Set strong passwords for database and Redis
- [ ] Configure SSL/TLS certificates
- [ ] Set up proper firewall rules
- [ ] Configure backup strategy
- [ ] Set resource limits (CPU, memory)
- [ ] Enable monitoring and alerting
- [ ] Review security settings
- [ ] Test disaster recovery procedures

### Security

- [ ] Change default passwords
- [ ] Enable API authentication
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up VPN or private networking
- [ ] Regular security audits

### Performance

- [ ] Enable connection pooling
- [ ] Configure Redis caching
- [ ] Set up CDN for static assets
- [ ] Enable gzip compression
- [ ] Optimize database indexes
- [ ] Configure auto-scaling

### Monitoring

- [ ] Set up Prometheus
- [ ] Configure Grafana dashboards
- [ ] Enable log aggregation
- [ ] Set up alerts for critical metrics
- [ ] Configure uptime monitoring
- [ ] Enable APM (Application Performance Monitoring)

---

## 📞 Support & Contact

For issues, questions, or contributions:
- Documentation: https://docs.ymera.com
- GitHub Issues: https://github.com/ymera/learning-agent
- Email: support@ymera.com

---

**Version**: 5.0.0  
**Last Updated**: January 2024  
**License**: MIT
