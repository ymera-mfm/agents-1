# YMERA Platform - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deployment Methods](#deployment-methods)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Service Management](#service-management)
6. [Monitoring](#monitoring)
7. [Scaling](#scaling)
8. [Security](#security)

## Prerequisites

### System Requirements
- **OS:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
- **RAM:** 4GB minimum, 8GB recommended
- **CPU:** 2 cores minimum, 4 cores recommended
- **Disk:** 20GB minimum, 50GB recommended
- **Network:** Internet access for initial setup

### Software Requirements
- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **Python:** 3.9+ (if deploying without Docker)
- **PostgreSQL:** 13+ (if deploying without Docker)
- **Redis:** 6.0+ (if deploying without Docker)

### Installation Commands

**Ubuntu/Debian:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**CentOS/RHEL:**
```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Deployment Methods

### Method 1: Docker Compose (Recommended)

**Advantages:**
- All dependencies included
- Easy to manage
- Consistent across environments
- Simple scaling

**Steps:**

1. **Extract deployment package:**
   ```bash
   tar -xzf ymera-deployment.tar.gz
   cd deployment_package
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   nano .env  # Edit configuration
   ```

3. **Deploy:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **Verify:**
   ```bash
   ./health-check.sh
   ```

### Method 2: Manual Deployment

**Steps:**

1. **Install Python and dependencies:**
   ```bash
   sudo apt install python3.9 python3.9-venv python3.9-dev
   python3.9 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL:**
   ```bash
   sudo apt install postgresql postgresql-contrib
   sudo -u postgres psql
   CREATE DATABASE ymera;
   CREATE USER ymera_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE ymera TO ymera_user;
   \q
   ```

3. **Setup Redis:**
   ```bash
   sudo apt install redis-server
   sudo systemctl start redis
   sudo systemctl enable redis
   ```

4. **Configure application:**
   ```bash
   cp .env.example .env
   # Edit .env with database and Redis URLs
   ```

5. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start application:**
   ```bash
   gunicorn -c gunicorn.conf.py main:app
   ```

### Method 3: Kubernetes

**Prerequisites:**
- Kubernetes cluster (1.19+)
- kubectl configured
- Helm 3+ (optional)

**Steps:**

1. **Create namespace:**
   ```bash
   kubectl create namespace ymera
   ```

2. **Create secrets:**
   ```bash
   kubectl create secret generic ymera-secrets \
     --from-literal=jwt-secret=your-secret \
     --from-literal=db-password=your-password \
     -n ymera
   ```

3. **Apply configurations:**
   ```bash
   kubectl apply -f k8s/ -n ymera
   ```

4. **Verify deployment:**
   ```bash
   kubectl get pods -n ymera
   kubectl logs -f deployment/ymera-app -n ymera
   ```

## Configuration

### Environment Variables

**Critical Settings:**

```env
# Application
APP_ENV=production
APP_NAME=YMERA
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/ymera
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=optional-password

# Security
JWT_SECRET_KEY=change-this-to-a-secure-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# API
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
RATE_LIMIT_PER_MINUTE=60

# Workers
MAX_WORKERS=4

# Storage
STORAGE_PATH=/app/data
MAX_UPLOAD_SIZE_MB=100
```

### Advanced Configuration

**Database Connection Pool:**
```env
DB_POOL_SIZE=20              # Initial pool size
DB_MAX_OVERFLOW=10           # Max additional connections
DB_POOL_TIMEOUT=30           # Connection timeout
DB_POOL_RECYCLE=3600         # Recycle connections after 1 hour
```

**Redis Configuration:**
```env
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_KEEPALIVE=True
CACHE_TTL=3600              # Default cache TTL in seconds
```

**Performance Tuning:**
```env
MAX_WORKERS=4               # Number of worker processes
WORKER_CLASS=uvicorn.workers.UvicornWorker
TIMEOUT=60                  # Request timeout
KEEPALIVE=5                 # Keep-alive timeout
```

## Database Setup

### PostgreSQL Setup

**Create Database:**
```sql
-- Connect as postgres user
CREATE DATABASE ymera;
CREATE USER ymera_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ymera TO ymera_user;

-- Grant schema permissions
\c ymera
GRANT ALL ON SCHEMA public TO ymera_user;
```

**Run Migrations:**
```bash
# Using Alembic
alembic upgrade head

# Check current version
alembic current

# Rollback one version
alembic downgrade -1
```

**Backup Database:**
```bash
# Backup
pg_dump -U ymera_user ymera > backup_$(date +%Y%m%d).sql

# Restore
psql -U ymera_user ymera < backup_20251020.sql
```

### Database Maintenance

**Vacuum and Analyze:**
```sql
VACUUM ANALYZE;
```

**Check Database Size:**
```sql
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) 
FROM pg_database;
```

**Monitor Connections:**
```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'ymera';
```

## Service Management

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f app

# Check status
docker-compose ps

# Scale services
docker-compose up -d --scale app=3

# Remove everything
docker-compose down -v
```

### Systemd Service (Manual Deployment)

Create `/etc/systemd/system/ymera.service`:

```ini
[Unit]
Description=YMERA Platform
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=ymera
Group=ymera
WorkingDirectory=/opt/ymera
Environment="PATH=/opt/ymera/venv/bin"
ExecStart=/opt/ymera/venv/bin/gunicorn -c gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Manage Service:**
```bash
# Start service
sudo systemctl start ymera

# Enable auto-start
sudo systemctl enable ymera

# Check status
sudo systemctl status ymera

# View logs
sudo journalctl -u ymera -f

# Restart
sudo systemctl restart ymera
```

## Monitoring

### Built-in Monitoring

**Health Checks:**
```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Cache health
curl http://localhost:8000/health/redis
```

**Metrics:**
```bash
# Prometheus metrics
curl http://localhost:8000/metrics
```

### Prometheus Setup

Access Prometheus at: http://localhost:9090

**Useful Queries:**
- Request rate: `rate(http_requests_total[5m])`
- Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
- P95 latency: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`

### Grafana Setup

Access Grafana at: http://localhost:3000

**Default Credentials:**
- Username: admin
- Password: admin (change on first login)

**Import Dashboard:**
1. Go to Dashboards → Import
2. Upload `monitoring/grafana-dashboard.json`
3. Select Prometheus data source

### Logging

**View Logs:**
```bash
# Docker logs
docker-compose logs -f app

# File logs (manual deployment)
tail -f /var/log/ymera/app.log
```

**Log Format:**
```json
{
  "timestamp": "2025-10-20T00:00:00Z",
  "level": "INFO",
  "message": "Request processed",
  "request_id": "abc123",
  "method": "GET",
  "path": "/api/v1/agents",
  "status": 200,
  "duration_ms": 45
}
```

## Scaling

### Horizontal Scaling

**Docker Compose:**
```bash
# Scale application servers
docker-compose up -d --scale app=3

# Verify
docker-compose ps
```

**Load Balancer:**
Add Nginx or HAProxy in front of multiple instances.

### Vertical Scaling

**Increase Resources:**
```env
# .env file
MAX_WORKERS=8
DB_POOL_SIZE=50
```

**Docker Resources:**
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Database Scaling

**Read Replicas:**
```env
DATABASE_READ_URL=postgresql+asyncpg://user:pass@replica:5432/ymera
```

**Connection Pooling:**
```env
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
```

## Security

### SSL/TLS Setup

**Let's Encrypt with Nginx:**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Firewall Configuration

**UFW (Ubuntu):**
```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### Security Checklist

- [ ] Change all default passwords
- [ ] Set strong JWT_SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall
- [ ] Enable rate limiting
- [ ] Setup backup procedures
- [ ] Configure log retention
- [ ] Review CORS settings
- [ ] Enable security headers
- [ ] Setup monitoring and alerts

### Backup Strategy

**Automated Backups:**
```bash
#!/bin/bash
# /etc/cron.daily/ymera-backup

# Backup database
pg_dump -U ymera_user ymera | gzip > /backups/db_$(date +%Y%m%d).sql.gz

# Backup application data
tar -czf /backups/data_$(date +%Y%m%d).tar.gz /app/data

# Backup configuration
cp .env /backups/env_$(date +%Y%m%d)

# Keep only last 7 days
find /backups -mtime +7 -delete
```

---

**Last Updated:** 2025-10-20
**Version:** 2.0.0
