# YMERA Platform - Running Guide

This guide provides comprehensive instructions for starting and running the YMERA Multi-Agent AI System in various configurations.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Setup Methods](#setup-methods)
  - [Method 1: Automated Startup Script (Recommended)](#method-1-automated-startup-script-recommended)
  - [Method 2: Docker Compose Full Stack](#method-2-docker-compose-full-stack)
  - [Method 3: Manual Setup](#method-3-manual-setup)
- [Configuration](#configuration)
- [Accessing the System](#accessing-the-system)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)
- [Stopping the System](#stopping-the-system)

---

## Quick Start

For the fastest setup, use the automated startup script:

**Linux/Mac:**
```bash
chmod +x start_system.sh
./start_system.sh
```

**Windows:**
```cmd
start_system.bat
```

Then select option `1` for full local development or option `3` for Docker Compose.

---

## Prerequisites

### Required Software

1. **Python 3.11 or higher**
   - Download: https://www.python.org/downloads/
   - Verify: `python3 --version` (Linux/Mac) or `python --version` (Windows)

2. **PostgreSQL 14 or higher** (if not using Docker)
   - Download: https://www.postgresql.org/download/
   - Or use Docker: see Docker Compose method

3. **Redis 6 or higher** (if not using Docker)
   - Download: https://redis.io/download
   - Or use Docker: see Docker Compose method

### Optional Software

4. **Docker & Docker Compose** (for containerized deployment)
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version` and `docker-compose --version`

5. **Git** (for version control)
   - Download: https://git-scm.com/downloads

---

## Setup Methods

### Method 1: Automated Startup Script (Recommended)

The automated startup script handles all setup steps for you.

#### Linux/Mac

```bash
# Make the script executable
chmod +x start_system.sh

# Run the script
./start_system.sh
```

#### Windows

```cmd
# Run the script
start_system.bat
```

#### Startup Options

The script will present you with the following options:

1. **Full Local Development** - Starts infrastructure and application locally
   - Creates virtual environment
   - Installs dependencies
   - Starts PostgreSQL and Redis in Docker
   - Initializes database
   - Starts the application

2. **Application Only** - Runs only the application (requires external database)
   - Use this if you have PostgreSQL and Redis already running
   - Configure database connections in `.env` file

3. **Docker Compose Full Stack** - Starts everything in containers
   - Easiest option if you have Docker installed
   - All services run in isolated containers
   - No local Python setup needed

4. **Infrastructure Only** - Starts only PostgreSQL and Redis
   - Use this to run infrastructure services separately
   - Application must be started manually

---

### Method 2: Docker Compose Full Stack

This method runs everything in Docker containers.

#### Step 1: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional - defaults work for Docker)
nano .env  # or use your preferred editor
```

#### Step 2: Start All Services

```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

#### Services Included

- **PostgreSQL** - Main database (port 5432)
- **Redis** - Cache and message queue (port 6379)
- **MongoDB** - NoSQL database (port 27017)
- **Kafka** - Event streaming (port 9092)
- **Prometheus** - Metrics collection (port 9090)
- **Grafana** - Metrics visualization (port 3000)
- **Jaeger** - Distributed tracing (port 16686)
- **MinIO** - Object storage (port 9000, console: 9001)

#### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: This deletes all data)
docker-compose down -v
```

---

### Method 3: Manual Setup

For more control over the setup process, follow these manual steps.

#### Step 1: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate.bat

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required settings:
#   - DATABASE_URL: PostgreSQL connection string
#   - REDIS_URL: Redis connection string
#   - JWT_SECRET_KEY: Secure random string (min 32 chars)
```

Example `.env` configuration:

```env
# Database
DATABASE_URL=postgresql://ymera_user:ymera_password@localhost:5432/ymera

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-characters-long
SECRET_KEY=your-super-secret-key-at-least-32-characters-long

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

#### Step 3: Start Infrastructure Services

**Option A: Using Docker Compose (Recommended)**

```bash
# Start only infrastructure services
docker-compose up -d postgres redis
```

**Option B: Using Local Installations**

Start PostgreSQL and Redis according to your installation:

```bash
# PostgreSQL (example for Linux)
sudo service postgresql start

# Redis (example for Linux)
sudo service redis-server start

# macOS with Homebrew
brew services start postgresql
brew services start redis

# Windows - start services from Services panel
```

#### Step 4: Initialize Database

```bash
# Using Alembic migrations
python -m alembic upgrade head

# Or using SQL schema (if alembic not configured)
psql -h localhost -U ymera_user -d ymera < database_schema.sql

# Or using initialization script
python 001_initial_schema.py
```

#### Step 5: Start the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

# Start the application
python main.py

# Alternative: Run with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuration

### Environment Variables

Key environment variables you may need to configure:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | No |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | - | Yes |
| `SECRET_KEY` | General secret key | - | Yes |
| `API_HOST` | API server host | `0.0.0.0` | No |
| `API_PORT` | API server port | `8000` | No |
| `DEBUG` | Enable debug mode | `false` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `CORS_ORIGINS` | Allowed CORS origins | - | No |

### Database Configuration

For PostgreSQL connection, use this format:

```
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database

# Examples:
# Local: postgresql+asyncpg://ymera_user:ymera_password@localhost:5432/ymera
# Docker: postgresql+asyncpg://ymera_user:ymera_password@postgres:5432/ymera
```

For SQLite (development only):

```
DATABASE_URL=sqlite+aiosqlite:///./ymera.db
```

### Security Configuration

Generate secure secret keys:

```bash
# Python method
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL method
openssl rand -base64 32
```

---

## Accessing the System

Once the system is running, you can access:

### Main Application

- **API Base URL**: http://localhost:8000
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Liveness Probe**: http://localhost:8000/health/live
- **Readiness Probe**: http://localhost:8000/health/ready
- **Metrics (Prometheus)**: http://localhost:8000/metrics

### Infrastructure Services (Docker Compose)

- **Grafana Dashboard**: http://localhost:3000
  - Default credentials: admin / ymera_admin
- **Prometheus**: http://localhost:9090
- **Jaeger Tracing**: http://localhost:16686
- **MinIO Console**: http://localhost:9001
  - Default credentials: ymera_admin / ymera_password

### API Authentication

To use the API, you need to register and authenticate:

```bash
# Register a new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Login to get access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePassword123!"
  }'

# Use the token for authenticated requests
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Monitoring and Health Checks

### Health Checks

```bash
# Comprehensive health check
curl http://localhost:8000/health

# Liveness probe (Kubernetes)
curl http://localhost:8000/health/live

# Readiness probe (Kubernetes)
curl http://localhost:8000/health/ready
```

### Viewing Logs

**Application Logs:**

```bash
# If running directly
# Logs appear in console output

# If running with Docker Compose
docker-compose logs -f app

# View specific service logs
docker-compose logs -f postgres
docker-compose logs -f redis
```

**System Metrics:**

- View Prometheus metrics: http://localhost:8000/metrics
- Visualize in Grafana: http://localhost:3000

### Performance Monitoring

Access Grafana dashboards to monitor:
- Request rates and latencies
- Database performance
- Redis cache hit rates
- System resource usage

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Address already in use` or `Port 8000 is already allocated`

**Solution**:
```bash
# Find process using the port (Linux/Mac)
lsof -i :8000
kill -9 <PID>

# Find process using the port (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change the port in .env
API_PORT=8001
```

#### 2. Database Connection Failed

**Error**: `could not connect to server` or `connection refused`

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Verify connection string in .env
# Make sure host, port, username, and password are correct
```

#### 3. Redis Connection Failed

**Error**: `Error connecting to Redis`

**Solution**:
```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis
```

#### 4. Import Errors

**Error**: `ModuleNotFoundError` or `No module named 'xyz'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate.bat  # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Clear pip cache if issues persist
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

#### 5. Alembic Migration Errors

**Error**: `Target database is not up to date`

**Solution**:
```bash
# Check current migration status
alembic current

# Upgrade to latest
alembic upgrade head

# If migrations are out of sync
alembic stamp head
alembic upgrade head

# As a last resort, recreate database
# CAUTION: This will delete all data
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

#### 6. Permission Denied

**Error**: `Permission denied` when running scripts

**Solution**:
```bash
# Make script executable (Linux/Mac)
chmod +x start_system.sh

# Run with explicit interpreter
bash start_system.sh

# Windows: Run as Administrator
# Right-click start_system.bat -> Run as Administrator
```

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/ymera-mfm/Agents-00/issues)
2. Review application logs for error details
3. Consult the [README.md](./README.md) for additional documentation
4. Check [START_HERE.md](./START_HERE.md) for quick reference

---

## Stopping the System

### Stopping Application Only

If running directly:
```bash
# Press Ctrl+C in the terminal where the application is running
```

### Stopping Docker Compose Services

```bash
# Stop all services (containers remain)
docker-compose stop

# Stop and remove containers (data persists)
docker-compose down

# Stop, remove containers, and delete volumes (CAUTION: deletes all data)
docker-compose down -v
```

### Stopping Infrastructure Services

```bash
# Stop only infrastructure
docker-compose stop postgres redis

# Or stop specific service
docker-compose stop postgres
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images and volumes
docker system prune -a --volumes

# Deactivate Python virtual environment
deactivate
```

---

## Development Tips

### Hot Reload

For development, enable hot reload:

```bash
# Edit .env
DEBUG=true
AUTO_RELOAD=true

# Or run with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run tests in parallel
pytest -n auto
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

---

## Production Deployment

For production deployment, see:
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Complete deployment guide
- [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md) - Operations procedures
- [k8s/](./k8s/) - Kubernetes manifests

---

## Quick Reference Commands

```bash
# Start full system (interactive)
./start_system.sh                    # Linux/Mac
start_system.bat                     # Windows

# Docker Compose
docker-compose up -d                 # Start all services
docker-compose down                  # Stop all services
docker-compose ps                    # Check status
docker-compose logs -f               # View logs

# Python virtual environment
python3 -m venv venv                 # Create venv
source venv/bin/activate             # Activate (Linux/Mac)
venv\Scripts\activate.bat            # Activate (Windows)
deactivate                           # Deactivate

# Database
alembic upgrade head                 # Run migrations
alembic current                      # Check migration status

# Application
python main.py                       # Start application
uvicorn main:app --reload            # Start with hot reload

# Testing
pytest                               # Run tests
pytest --cov                         # Run with coverage

# Health checks
curl http://localhost:8000/health    # Health check
curl http://localhost:8000/docs      # API documentation
```

---

## Additional Resources

- [README.md](./README.md) - Project overview
- [START_HERE.md](./START_HERE.md) - Quick start guide
- [AGENT_SYSTEM_COMPLETION_README.md](./AGENT_SYSTEM_COMPLETION_README.md) - Agent system documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

---

**Last Updated**: 2025-10-26  
**Version**: 1.0.0
