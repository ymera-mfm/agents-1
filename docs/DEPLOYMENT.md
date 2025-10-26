# YMERA System Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS 12+, or Windows 10/11 with WSL2
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space

### Software Requirements
- Python 3.11 or higher
- Docker 20.10+ and Docker Compose 2.0+
- Git 2.30+
- PostgreSQL 16+ (for non-Docker setup)
- Redis 7+ (for non-Docker setup)
- NATS Server (for non-Docker setup)

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/ymera-mfm/agents-1.git
cd agents-1
```

### 2. Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_HOST`: Redis server hostname
- `NATS_SERVERS`: NATS server URLs
- `SECRET_KEY`: JWT secret (generate with `openssl rand -hex 32`)

### 5. Start Infrastructure Services

#### Option A: Using Docker Compose (Recommended)
```bash
# Start only infrastructure services
docker-compose up -d postgres redis nats

# Check services are running
docker-compose ps
```

#### Option B: Manual Installation
```bash
# Install and start PostgreSQL
sudo apt-get install postgresql-16
sudo systemctl start postgresql

# Install and start Redis
sudo apt-get install redis-server
sudo systemctl start redis

# Install and start NATS
# Download from https://nats.io/download/
./nats-server
```

### 6. Initialize Database
```bash
# Run migrations (when implemented)
# alembic upgrade head

# Or manually create tables
python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
```

### 7. Start Application
```bash
# Using the startup script
./start_system.sh  # Linux/macOS
start_system.bat   # Windows

# Or directly with Python
python main.py
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/v1/docs
- Health: http://localhost:8000/api/v1/health

## Docker Deployment

### Quick Start
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Build
```bash
# Build production image
docker build -t ymera-system:latest .

# Run with production settings
docker run -d \
  --name ymera-api \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql+asyncpg://... \
  ymera-system:latest
```

### Docker Compose Services

The `docker-compose.yml` includes:
- **postgres**: Database service
- **redis**: Cache service
- **nats**: Message broker
- **ymera-api**: Main application
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboard

## Production Deployment

### Kubernetes Deployment

#### 1. Create Namespace
```bash
kubectl create namespace ymera
```

#### 2. Create Secrets
```bash
kubectl create secret generic ymera-secrets \
  --from-literal=database-url='postgresql+asyncpg://...' \
  --from-literal=secret-key='your-secret-key' \
  -n ymera
```

#### 3. Deploy Services
```bash
# Deploy infrastructure
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/nats.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Deploy ingress
kubectl apply -f k8s/ingress.yaml
```

#### 4. Verify Deployment
```bash
# Check pods
kubectl get pods -n ymera

# Check services
kubectl get svc -n ymera

# View logs
kubectl logs -f deployment/ymera-api -n ymera
```

### Cloud Platforms

#### AWS ECS
```bash
# Build and push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t ymera-system .
docker tag ymera-system:latest <account>.dkr.ecr.us-east-1.amazonaws.com/ymera-system:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/ymera-system:latest

# Create ECS task definition and service
aws ecs create-service --cluster ymera-cluster --service-name ymera-api ...
```

#### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/ymera-system
gcloud run deploy ymera-api \
  --image gcr.io/PROJECT-ID/ymera-system \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure Container Apps
```bash
# Create container app
az containerapp create \
  --name ymera-api \
  --resource-group ymera-rg \
  --environment ymera-env \
  --image ymera-system:latest \
  --target-port 8000
```

## Configuration

### Environment Variables

#### Application Settings
- `APP_NAME`: Application name (default: "YMERA Multi-Agent AI System")
- `DEBUG`: Enable debug mode (default: false)
- `ENVIRONMENT`: Deployment environment (development/production)

#### API Settings
- `API_HOST`: API host (default: "0.0.0.0")
- `API_PORT`: API port (default: 8000)
- `API_PREFIX`: API path prefix (default: "/api/v1")

#### Database Settings
- `DATABASE_URL`: Full database connection string
- `DATABASE_POOL_SIZE`: Connection pool size (default: 10)
- `DATABASE_MAX_OVERFLOW`: Max overflow connections (default: 20)

#### Security Settings
- `SECRET_KEY`: JWT signing secret (required)
- `ALGORITHM`: JWT algorithm (default: "HS256")
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiry (default: 30)

#### Agent Settings
- `MAX_AGENTS`: Maximum agent instances (default: 1000)
- `AGENT_TIMEOUT`: Agent timeout in seconds (default: 300)
- `MESSAGE_QUEUE_SIZE`: Message queue size (default: 10000)

### Configuration Files

#### .env (Development)
```env
DEBUG=true
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ymera
```

#### .env.production (Production)
```env
DEBUG=false
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:password@prod-db:5432/ymera
SECRET_KEY=<strong-random-key>
```

## Monitoring

### Prometheus
Access at: http://localhost:9090

Key metrics to monitor:
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request latency
- `agent_status`: Agent health status
- `system_cpu_percent`: CPU usage
- `system_memory_percent`: Memory usage

### Grafana
Access at: http://localhost:3000 (admin/admin)

Import dashboards:
1. YMERA System Overview
2. Agent Performance
3. API Metrics
4. Infrastructure Health

### Health Checks
```bash
# API health
curl http://localhost:8000/api/v1/health

# Prometheus targets
curl http://localhost:9090/api/v1/targets
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check database is running
docker-compose ps postgres

# Test connection
psql -h localhost -U postgres -d ymera

# Check connection string in .env
```

#### 2. Port Already in Use
```bash
# Find process using port
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process or change port in .env
```

#### 3. Module Import Errors
```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt

# Check Python version
python --version  # Should be 3.11+
```

#### 4. Docker Service Not Starting
```bash
# View service logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Rebuild service
docker-compose up -d --build <service-name>
```

### Logs

#### Application Logs
```bash
# View logs
tail -f logs/ymera.log

# Docker logs
docker-compose logs -f ymera-api
```

#### Database Logs
```bash
# PostgreSQL logs
docker-compose logs -f postgres
```

### Performance Issues

#### High CPU Usage
- Check agent configuration
- Review message queue size
- Monitor slow queries
- Scale horizontally

#### High Memory Usage
- Check for memory leaks
- Review connection pooling
- Monitor agent instances
- Increase container resources

#### Slow API Responses
- Enable query caching
- Optimize database queries
- Add database indexes
- Use connection pooling

## Support

For issues and questions:
- GitHub Issues: https://github.com/ymera-mfm/agents-1/issues
- Documentation: See `/docs` directory
- Email: support@ymera.io
