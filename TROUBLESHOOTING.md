# YMERA Platform - Troubleshooting Guide

## Common Issues and Solutions

### Application Won't Start

#### Issue: Port Already in Use

**Symptoms:**
```
Error: Address already in use: ('0.0.0.0', 8000)
```

**Solutions:**
```bash
# Find process using port 8000
sudo lsof -i :8000
# or
sudo netstat -tulpn | grep 8000

# Kill the process
sudo kill -9 <PID>

# Or change port in .env
PORT=8001
```

#### Issue: Module Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

### Database Issues

#### Issue: Connection Refused

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql
# or for Docker
docker-compose ps db

# Start PostgreSQL
sudo systemctl start postgresql
# or for Docker
docker-compose up -d db

# Verify connectivity
psql -h localhost -U ymera_user -d ymera
```

#### Issue: Authentication Failed

**Symptoms:**
```
FATAL: password authentication failed for user "ymera_user"
```

**Solutions:**
1. Verify credentials in .env file
2. Reset password:
```sql
ALTER USER ymera_user WITH PASSWORD 'new_password';
```
3. Check pg_hba.conf for authentication method
4. Reload PostgreSQL: `sudo systemctl reload postgresql`

#### Issue: Too Many Connections

**Symptoms:**
```
FATAL: too many connections for role "ymera_user"
```

**Solutions:**
```bash
# Check active connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE usename='ymera_user';"

# Reduce connection pool size in .env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5

# Increase max_connections in postgresql.conf
max_connections = 200

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Redis Issues

#### Issue: Redis Connection Failed

**Symptoms:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**
```bash
# Check if Redis is running
sudo systemctl status redis
# or
redis-cli ping

# Start Redis
sudo systemctl start redis

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Test connection
redis-cli
> ping
PONG
```

#### Issue: Redis Out of Memory

**Symptoms:**
```
OOM command not allowed when used memory > 'maxmemory'
```

**Solutions:**
```bash
# Check memory usage
redis-cli info memory

# Increase maxmemory in redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis

# Or clear cache
redis-cli FLUSHALL
```

### Docker Issues

#### Issue: Container Won't Start

**Symptoms:**
```
Error response from daemon: container exited immediately
```

**Solutions:**
```bash
# Check container logs
docker-compose logs app

# Remove and recreate
docker-compose down
docker-compose up -d

# Check disk space
df -h

# Clean up Docker
docker system prune -a
```

#### Issue: Permission Denied

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/data'
```

**Solutions:**
```bash
# Fix permissions
sudo chown -R 1000:1000 ./data

# Or in docker-compose.yml
volumes:
  - ./data:/app/data:rw
```

#### Issue: Out of Disk Space

**Symptoms:**
```
no space left on device
```

**Solutions:**
```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove stopped containers
docker container prune
```

### Performance Issues

#### Issue: High Memory Usage

**Solutions:**
```bash
# Check memory usage
docker stats

# Reduce worker count in .env
MAX_WORKERS=2

# Reduce connection pools
DB_POOL_SIZE=10
REDIS_MAX_CONNECTIONS=25

# Add memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
```

#### Issue: Slow Response Times

**Solutions:**
1. Enable caching:
```env
CACHE_ENABLED=true
CACHE_TTL=3600
```

2. Optimize database queries:
```bash
# Check slow queries
docker-compose exec db psql -U ymera_user -d ymera \
  -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

3. Add database indexes
4. Increase worker count:
```env
MAX_WORKERS=4
```

#### Issue: High CPU Usage

**Solutions:**
```bash
# Check CPU usage
top
# or
htop

# Reduce worker count
MAX_WORKERS=2

# Add CPU limits
deploy:
  resources:
    limits:
      cpus: '1'
```

### API Issues

#### Issue: 502 Bad Gateway

**Symptoms:**
Nginx returns 502 error

**Solutions:**
```bash
# Check if app is running
docker-compose ps app

# Check app logs
docker-compose logs app

# Check Nginx logs
docker-compose logs nginx

# Restart services
docker-compose restart app nginx
```

#### Issue: 504 Gateway Timeout

**Solutions:**
```bash
# Increase timeout in nginx.conf
proxy_read_timeout 120s;
proxy_connect_timeout 120s;

# Increase app timeout in .env
WORKER_TIMEOUT=120

# Restart services
docker-compose restart
```

#### Issue: CORS Errors

**Symptoms:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solutions:**
Add allowed origins to .env:
```env
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Authentication Issues

#### Issue: JWT Token Invalid

**Solutions:**
```bash
# Verify JWT_SECRET_KEY is set correctly
grep JWT_SECRET_KEY .env

# Generate new secret
openssl rand -hex 32

# Update .env and restart
docker-compose restart app
```

#### Issue: Session Expired

**Solutions:**
Increase token expiration in .env:
```env
JWT_EXPIRATION_MINUTES=60
JWT_REFRESH_EXPIRATION_DAYS=7
```

### Migration Issues

#### Issue: Migration Failed

**Symptoms:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'xxxxx'
```

**Solutions:**
```bash
# Check current version
docker-compose exec app alembic current

# Check available versions
docker-compose exec app alembic history

# Reset to base
docker-compose exec app alembic downgrade base

# Rerun migrations
docker-compose exec app alembic upgrade head
```

### Health Check Issues

#### Issue: Health Check Failing

**Solutions:**
```bash
# Manual health check
curl -v http://localhost:8000/health

# Check component health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/redis

# Check logs
docker-compose logs app | grep health

# Restart unhealthy services
docker-compose restart
```

## Debugging Tools

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Logs for specific time
docker-compose logs --since 2024-10-20T10:00:00 app
```

### Interactive Shell

```bash
# Access app container
docker-compose exec app bash

# Access database
docker-compose exec db psql -U ymera_user ymera

# Access Redis
docker-compose exec redis redis-cli
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# API docs
curl http://localhost:8000/docs

# Specific endpoint
curl -X GET http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Getting Help

### Information to Collect

When reporting issues, include:
1. Error messages (full stack trace)
2. Relevant logs
3. Configuration (sanitized .env)
4. System information (OS, Docker version)
5. Steps to reproduce
6. Expected vs actual behavior

### Log Collection Script

```bash
#!/bin/bash
# collect-logs.sh

mkdir -p debug_logs
docker-compose logs > debug_logs/all.log
docker-compose ps > debug_logs/status.txt
docker-compose config > debug_logs/config.yml
df -h > debug_logs/disk.txt
free -h > debug_logs/memory.txt
tar -czf debug_logs_$(date +%Y%m%d).tar.gz debug_logs/
echo "Logs collected: debug_logs_$(date +%Y%m%d).tar.gz"
```

---

**Last Updated:** 2025-10-20
