# YMERA Platform - Configuration Guide

## Overview

This guide covers all configuration options for the YMERA platform.

## Environment Variables

### Application Settings

```env
# Application name and environment
APP_NAME=YMERA
APP_ENV=production  # development, staging, production
APP_VERSION=2.0.0

# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json, text
LOG_FILE=/var/log/ymera/app.log
```

### Database Configuration

```env
# Primary database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ymera
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=false  # Log SQL queries (development only)

# Read replica (optional)
DATABASE_READ_URL=postgresql+asyncpg://user:password@replica:5432/ymera
```

### Cache Configuration

```env
# Redis configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=optional-password
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_KEEPALIVE=true

# Cache settings
CACHE_ENABLED=true
CACHE_TTL=3600  # Default TTL in seconds
CACHE_KEY_PREFIX=ymera:
```

### Security Configuration

```env
# JWT settings
JWT_SECRET_KEY=your-secret-key-here-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
JWT_REFRESH_EXPIRATION_DAYS=7

# CORS settings
CORS_ORIGINS=https://example.com,https://www.example.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_BURST=10
```

### Worker Configuration

```env
# Worker processes
MAX_WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
WORKER_TIMEOUT=60
WORKER_KEEPALIVE=5
WORKER_MAX_REQUESTS=10000
WORKER_MAX_REQUESTS_JITTER=1000
```

### Storage Configuration

```env
# File storage
STORAGE_TYPE=local  # local, s3, azure
STORAGE_PATH=/app/data
MAX_UPLOAD_SIZE_MB=100
ALLOWED_EXTENSIONS=pdf,doc,docx,txt,jpg,png

# S3 configuration (if using S3)
S3_BUCKET=ymera-files
S3_REGION=us-east-1
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key

# Azure Blob Storage (if using Azure)
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_CONTAINER_NAME=ymera-files
```

### Email Configuration

```env
# Email settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_TLS=true
EMAIL_FROM=noreply@ymera.com
```

### Monitoring Configuration

```env
# Metrics
METRICS_ENABLED=true
METRICS_PORT=8000
METRICS_PATH=/metrics

# Health checks
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_PATH=/health

# Sentry (error tracking)
SENTRY_DSN=https://your-sentry-dsn
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Agent Configuration

```env
# Agent settings
AGENT_MAX_CONCURRENT=10
AGENT_TIMEOUT=300
AGENT_RETRY_COUNT=3
AGENT_RETRY_DELAY=5
```

## Configuration Files

### gunicorn.conf.py

Located at: `configs/gunicorn.conf.py`

Key settings:
- `workers`: Number of worker processes
- `worker_class`: Worker type (uvicorn for async)
- `bind`: Host and port
- `timeout`: Request timeout
- `accesslog`, `errorlog`: Log configuration

### nginx.conf

Located at: `configs/nginx.conf`

Key settings:
- Reverse proxy configuration
- SSL/TLS settings
- Security headers
- Compression
- Timeouts

### supervisord.conf

Located at: `configs/supervisord.conf`

Manages multiple processes:
- Application server
- Background workers
- Scheduled tasks

## Docker Configuration

### docker-compose.yml

Services:
- `app`: Application server
- `db`: PostgreSQL database
- `redis`: Redis cache
- `nginx`: Reverse proxy
- `prometheus`: Metrics collection
- `grafana`: Monitoring dashboards

Environment variables can be set in `.env` file or directly in docker-compose.yml.

## Database Configuration

### Connection Pool

Optimize connection pool size based on:
- Number of workers: `DB_POOL_SIZE = workers * 2`
- Expected concurrent requests
- Database server capacity

Example for 4 workers:
```env
MAX_WORKERS=4
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

### PostgreSQL Tuning

Edit `postgresql.conf`:

```conf
# Connection settings
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB
```

## Performance Tuning

### Application Performance

```env
# Worker optimization
MAX_WORKERS=4  # 2-4 x CPU cores

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Caching
CACHE_ENABLED=true
CACHE_TTL=3600

# Async processing
ASYNC_ENABLED=true
ASYNC_POOL_SIZE=50
```

### Resource Limits

Docker Compose:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

## Environment-Specific Configuration

### Development

```env
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
DB_ECHO=true
CACHE_ENABLED=false
```

### Staging

```env
APP_ENV=staging
DEBUG=false
LOG_LEVEL=INFO
DB_ECHO=false
CACHE_ENABLED=true
```

### Production

```env
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
DB_ECHO=false
CACHE_ENABLED=true
RATE_LIMIT_ENABLED=true
```

## Security Best Practices

1. **Never commit .env files** - Use .env.example as template
2. **Use strong secrets** - Generate with: `openssl rand -hex 32`
3. **Rotate credentials regularly**
4. **Use environment-specific configurations**
5. **Enable rate limiting in production**
6. **Use HTTPS in production**
7. **Restrict CORS origins**
8. **Keep dependencies updated**

## Configuration Validation

The application validates configuration on startup. Check logs for validation errors.

Example validation checks:
- Required variables are set
- Database connectivity
- Redis connectivity
- Storage path exists and is writable

## Troubleshooting

### Configuration Not Loading

1. Check .env file location
2. Verify file permissions
3. Check for syntax errors
4. Review startup logs

### Database Connection Issues

1. Verify DATABASE_URL format
2. Check database server is running
3. Verify credentials
4. Check network connectivity
5. Review firewall rules

### Cache Issues

1. Verify Redis is running
2. Check REDIS_URL
3. Test connection: `redis-cli ping`
4. Review Redis logs

---

**Last Updated:** 2025-10-20
