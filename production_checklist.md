# YMERA Platform - Production Deployment Checklist

**Version:** 4.0.0  
**Last Updated:** 2025-01-24  
**Status:** Ready for Production ✅

---

## 📋 Pre-Deployment Checklist

### 1. Code Quality & Testing

- [ ] All unit tests passing
- [ ] Integration tests completed
- [ ] Load testing performed
- [ ] Security audit completed
- [ ] Code review approved
- [ ] No critical/high severity issues in code scan
- [ ] All TODOs and FIXMEs resolved

### 2. Dependencies & Environment

- [ ] All dependencies installed from requirements.txt
- [ ] Python version verified (>=3.9)
- [ ] Virtual environment activated
- [ ] Environment variables configured
- [ ] .env file created from .env.example
- [ ] All secrets rotated for production
- [ ] No development dependencies in production

### 3. Database

- [ ] Database server running and accessible
- [ ] Database migrations executed (alembic upgrade head)
- [ ] Database backups configured
- [ ] Connection pooling configured
- [ ] Read replicas configured (if applicable)
- [ ] Database credentials secured
- [ ] Database performance tested

### 4. File Storage

- [ ] Storage directories created
- [ ] Correct permissions set (755 for dirs, 644 for files)
- [ ] Sufficient disk space available
- [ ] Backup strategy implemented
- [ ] File cleanup jobs scheduled
- [ ] Virus scanning configured (if required)

### 5. Security

- [ ] HTTPS/TLS certificates installed
- [ ] JWT secrets generated and secured
- [ ] CORS origins configured correctly
- [ ] Rate limiting enabled
- [ ] SQL injection protection verified
- [ ] XSS protection enabled
- [ ] CSRF protection configured
- [ ] Security headers configured
- [ ] Firewall rules configured
- [ ] DDoS protection enabled

### 6. Monitoring & Logging

- [ ] Application logging configured
- [ ] Log rotation setup
- [ ] Error tracking service integrated (Sentry/etc)
- [ ] Performance monitoring active
- [ ] Health check endpoints tested
- [ ] Alerting rules configured
- [ ] Dashboard created
- [ ] On-call rotation established

---

## 🚀 Deployment Steps

### Step 1: Backup Current System

```bash
# Create comprehensive backup
./deploy_production.py --backup-only

# Or manually
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/
```

### Step 2: Run Deployment Script

```bash
# Run automated deployment
python deploy_production.py

# Follow prompts and review output
```

### Step 3: Configure Environment

```bash
# Copy and edit environment file
cp backend/.env.example backend/.env
nano backend/.env

# Required variables:
# - DATABASE_URL
# - REDIS_URL
# - JWT_SECRET
# - SECRET_KEY
# - ALLOWED_ORIGINS
```

### Step 4: Install Dependencies

```bash
cd backend
pip install -r requirements.txt --no-cache-dir
```

### Step 5: Run Database Migrations

```bash
# Check current migration status
alembic current

# Run migrations
alembic upgrade head

# Verify
alembic current
```

### Step 6: Verify Installation

```bash
# Test imports
python -c "from app.API_GATEWAY_CORE_ROUTES import database; print('✅ OK')"

# Test database connection
python -c "
import asyncio
from app.API_GATEWAY_CORE_ROUTES import database
async def test():
    await database.init_database()
    healthy = await database._db_manager.health_check()
    print(f'Database: {\"✅ Healthy\" if healthy else \"❌ Unhealthy\"}')
    await database.close_database()
asyncio.run(test())
"
```

### Step 7: Start Application

#### Development Mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode:
```bash
# Using Gunicorn with Uvicorn workers
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/ymera/access.log \
    --error-logfile /var/log/ymera/error.log \
    --log-level info \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50
```

### Step 8: Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Test file upload
curl -X POST http://localhost:8000/api/v1/files/upload \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -F "file=@test.txt"

# Test WebSocket
# Use wscat or browser console
```

---

## 🔧 Configuration Guide

### Database Configuration

```env
# PostgreSQL (Recommended)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Connection Pooling
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_PRE_PING=True
DATABASE_POOL_RECYCLE=3600
```

### Redis Configuration

```env
# Redis for caching and rate limiting
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
```

### File Storage Configuration

```env
FILE_STORAGE_PATH=/var/ymera/files
TEMP_STORAGE_PATH=/var/ymera/temp
MAX_FILE_SIZE=104857600  # 100MB
MAX_FILES_PER_USER=1000
ALLOWED_MIME_TYPES=application/pdf,image/jpeg,image/png

# Virus Scanning (optional)
VIRUS_SCAN_ENABLED=False
CLAMAV_SOCKET=/var/run/clamav/clamd.ctl
```

### Security Configuration

```env
# Secrets (CHANGE THESE!)
JWT_SECRET=your-256-bit-secret-key-here
SECRET_KEY=your-secret-key-here

# JWT Settings
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

---

## 📊 Monitoring Setup

### Health Check Endpoints

```bash
# Basic health
GET /health

# Detailed metrics
GET /metrics

# Gateway stats
GET /gateway/stats
```

### Log Locations

```
Application Logs: /var/log/ymera/app.log
Access Logs: /var/log/ymera/access.log
Error Logs: /var/log/ymera/error.log
```

### Monitoring Tools

- **Application**: Prometheus + Grafana
- **Errors**: Sentry / Rollbar
- **Logs**: ELK Stack / Loki
- **APM**: New Relic / Datadog

---

## 🐛 Troubleshooting

### Issue: Import Errors

**Symptoms**: `ModuleNotFoundError` or `ImportError`

**Solutions**:
```bash
# Verify Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check __init__.py files
find backend/app -name "__init__.py" -type f
```

### Issue: Database Connection Failed

**Symptoms**: `sqlalchemy.exc.OperationalError`

**Solutions**:
```bash
# Test connection
psql -h localhost -U postgres -d ymera

# Check DATABASE_URL format
echo $DATABASE_URL

# Verify PostgreSQL is running
systemctl status postgresql

# Check logs
tail -f /var/log/postgresql/postgresql-*.log
```

### Issue: File Upload Fails

**Symptoms**: `413 Payload Too Large` or `Permission Denied`

**Solutions**:
```bash
# Check storage directory
ls -la /var/ymera/files

# Fix permissions
chmod 755 /var/ymera/files
chown www-data:www-data /var/ymera/files

# Check file size limits
grep MAX_FILE_SIZE .env

# Check disk space
df -h /var/ymera
```

### Issue: High Memory Usage

**Symptoms**: Application slow or OOM errors

**Solutions**:
```bash
# Check memory usage
ps aux | grep gunicorn

# Reduce workers
# Edit gunicorn command: --workers 2

# Check for memory leaks
# Profile with memory_profiler

# Increase system memory
# Or implement pagination/streaming
```

### Issue: WebSocket Connection Drops

**Symptoms**: Frequent disconnections

**Solutions**:
```bash
# Check proxy timeout settings (nginx example)
# proxy_read_timeout 3600s;
# proxy_