# YMERA Platform - Deployment Guide

## Overview
This guide covers the deployment process for the YMERA Agent Platform.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 16+
- Redis 7+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space minimum

## Pre-Deployment Checklist

- [ ] Review and update `.env` file with production values
- [ ] Generate strong JWT secret key (minimum 32 characters)
- [ ] Configure database connection strings
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Review resource limits in docker-compose.yml
- [ ] Test backup and restore procedures
- [ ] Prepare rollback plan

## Deployment Steps

### 1. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env

# Required changes:
# - JWT_SECRET_KEY: Generate secure key
# - DATABASE_URL: Production database connection
# - REDIS_URL: Production Redis connection
# - CORS_ORIGINS: Your domain(s)
```

### 2. Database Setup

```bash
# Initialize database
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
docker-compose exec postgres pg_isready

# Run migrations
docker-compose run --rm app alembic upgrade head

# (Optional) Seed production data
docker-compose run --rm app python -c "
from core.db_seeding import seed_database
from core.database import Database
import asyncio

async def seed():
    db = Database()
    await db.initialize()
    async with db.session_maker() as session:
        await seed_database(session, 'production')
    await db.cleanup()

asyncio.run(seed())
"
```

### 3. Build and Deploy

```bash
# Using deployment script
sudo ./scripts/deploy.sh

# Or manually
docker-compose build
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Run health checks
./scripts/health-check.sh

# Check logs
docker-compose logs -f app

# Verify endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/metrics
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace ymera
```

### 2. Apply Configurations

```bash
# Create secrets (update values first!)
kubectl apply -f k8s/secrets.yaml

# Create ConfigMap
kubectl apply -f k8s/configmap.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml

# Create services
kubectl apply -f k8s/service.yaml

# Configure ingress
kubectl apply -f k8s/ingress.yaml

# Set up autoscaling
kubectl apply -f k8s/hpa.yaml
```

### 3. Verify Deployment

```bash
# Check pods
kubectl get pods -n ymera

# Check services
kubectl get svc -n ymera

# Check logs
kubectl logs -n ymera -l app=ymera-agents --tail=100

# Check HPA
kubectl get hpa -n ymera
```

## Post-Deployment

### 1. Security Hardening

- Change default admin password immediately
- Enable firewall rules
- Configure SSL/TLS
- Set up rate limiting
- Enable audit logging

### 2. Monitoring Setup

```bash
# Access Grafana
open http://localhost:3000

# Import dashboard
# Navigate to: Create > Import
# Upload: grafana-dashboards/ymera-system-overview.json
```

### 3. Backup Configuration

```bash
# Test backup
./scripts/backup.sh --tag "post-deployment"

# Verify backup
ls -lh /backups/

# Schedule automated backups (add to crontab)
0 2 * * * /path/to/scripts/backup.sh
```

## Rollback Procedure

If deployment fails:

```bash
# Stop current deployment
docker-compose down

# Restore from backup
./scripts/rollback.sh

# Verify rollback
./scripts/health-check.sh
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs app

# Common issues:
# - Database connection failed: Check DATABASE_URL
# - Redis connection failed: Check REDIS_URL
# - Permission denied: Check file permissions
```

### Health Checks Failing

```bash
# Check service status
docker-compose ps

# Check database connectivity
docker-compose exec postgres psql -U ymera_user -d ymera -c "SELECT 1"

# Check Redis connectivity
docker-compose exec redis redis-cli ping
```

### High Resource Usage

```bash
# Check resource usage
docker stats

# Scale down if needed
docker-compose up -d --scale app=1
```

## Environment Variables Reference

See `.env.example` for complete list of environment variables.

### Critical Variables

- `JWT_SECRET_KEY`: JWT signing key (required)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `REDIS_URL`: Redis connection string (required)
- `ENVIRONMENT`: Environment name (development/staging/production)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)

## Support

For deployment issues:
- Email: devops@ymera.com
- Slack: #ymera-deployments
- Emergency: +1-555-DEPLOY
