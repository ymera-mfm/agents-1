# Configuration Documentation

## Overview
This document provides comprehensive documentation for all configuration options in the YMERA Agent Platform.

## Environment Variables

### Server Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PROJECT_AGENT_HOST` | string | `0.0.0.0` | Host to bind the server to |
| `PROJECT_AGENT_PORT` | integer | `8001` | Port to run the server on |
| `ENVIRONMENT` | string | `production` | Environment name (development/staging/production) |
| `DEBUG` | boolean | `false` | Enable debug mode |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `WORKER_COUNT` | integer | `4` | Number of worker processes |

### Database Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | **required** | PostgreSQL connection string |
| `DATABASE_POOL_SIZE` | integer | `20` | Database connection pool size |
| `DATABASE_MAX_OVERFLOW` | integer | `10` | Maximum overflow connections |
| `DATABASE_ECHO` | boolean | `false` | Echo SQL queries to console |

### Redis Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis connection string |
| `REDIS_PASSWORD` | string | `null` | Redis password (if required) |
| `REDIS_MAX_CONNECTIONS` | integer | `50` | Maximum Redis connections |

### Security Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JWT_SECRET_KEY` | string | **required** | JWT signing key (min 32 chars) |
| `JWT_ALGORITHM` | string | `RS256` | JWT algorithm (RS256/HS256) |
| `JWT_EXPIRE_MINUTES` | integer | `60` | JWT token expiration time |
| `JWT_PUBLIC_KEY_PATH` | string | `null` | Path to JWT public key (RS256) |
| `JWT_PRIVATE_KEY_PATH` | string | `null` | Path to JWT private key (RS256) |

### Integration Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SERVICE_NAME` | string | `ymera-agents` | Service name for discovery |
| `SERVICE_VERSION` | string | `2.0.0` | Service version |
| `AUTH_SERVICE_URL` | string | `http://auth-service:8200` | Auth service endpoint |
| `MONITORING_SERVICE_URL` | string | `http://monitoring-service:8300` | Monitoring service endpoint |
| `LOGGING_SERVICE_URL` | string | `http://logging-service:8400` | Logging service endpoint |

### Feature Flags

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FEATURE_CHAT_INTERFACE` | boolean | `true` | Enable chat interface |
| `FEATURE_FILE_VERSIONING` | boolean | `true` | Enable file versioning |
| `FEATURE_AUTO_INTEGRATION` | boolean | `true` | Enable automatic integration |
| `FEATURE_DISTRIBUTED_TRACING` | boolean | `true` | Enable distributed tracing |
| `FEATURE_METRICS_EXPORT` | boolean | `true` | Enable metrics export |
| `FEATURE_TWO_FACTOR_AUTH` | boolean | `false` | Enable 2FA |
| `FEATURE_AI_SUGGESTIONS` | boolean | `false` | Enable AI suggestions (experimental) |

### Monitoring & Observability

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_DISTRIBUTED_TRACING` | boolean | `true` | Enable distributed tracing |
| `ENABLE_METRICS_EXPORT` | boolean | `true` | Enable metrics export |
| `ENABLE_HEALTH_CHECKS` | boolean | `true` | Enable health checks |
| `PROMETHEUS_ENABLED` | boolean | `true` | Enable Prometheus metrics |
| `JAEGER_ENABLED` | boolean | `true` | Enable Jaeger tracing |
| `JAEGER_AGENT_HOST` | string | `localhost` | Jaeger agent host |
| `JAEGER_AGENT_PORT` | integer | `6831` | Jaeger agent port |
| `LOG_FORMAT` | string | `json` | Log format (json/text) |

## Configuration Validation

The system validates configuration at startup:

### Required Variables
- `DATABASE_URL` - Must be a valid PostgreSQL connection string
- `JWT_SECRET_KEY` - Must be at least 32 characters

### Validation Rules
- Port numbers must be between 1 and 65535
- Pool sizes must be positive integers
- Percentages must be between 0 and 100
- URLs must be valid HTTP/HTTPS URLs

## Multi-Environment Setup

### Development
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_ECHO=true
```

### Staging
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
ENABLE_DISTRIBUTED_TRACING=true
```

### Production
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ENABLE_DISTRIBUTED_TRACING=true
ENABLE_METRICS_EXPORT=true
```

## Security Best Practices

1. **JWT Secret Key**
   - Generate using: `openssl rand -base64 32`
   - Never commit to version control
   - Rotate regularly (every 90 days)

2. **Database Credentials**
   - Use strong passwords
   - Rotate credentials regularly
   - Use connection pooling

3. **Redis**
   - Always use password protection
   - Use TLS for production
   - Limit network access

## Performance Tuning

### Database
- Increase `DATABASE_POOL_SIZE` for high traffic
- Adjust `DATABASE_MAX_OVERFLOW` based on peak load
- Enable connection recycling

### Redis
- Increase `REDIS_MAX_CONNECTIONS` for caching-heavy workloads
- Use Redis Cluster for horizontal scaling

### Workers
- Set `WORKER_COUNT` to number of CPU cores
- Increase for I/O-bound applications
- Decrease for memory-constrained environments

## Troubleshooting

### Configuration Not Loading
1. Check `.env` file exists in project root
2. Verify file permissions (should be readable)
3. Check for syntax errors in `.env`

### Invalid Configuration
1. Review validation error messages
2. Check data types match expected types
3. Verify required variables are set

### Performance Issues
1. Check resource limits
2. Review connection pool settings
3. Monitor metrics in Grafana
