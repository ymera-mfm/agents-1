# Production Deployment Guide - Agent Platform Engines v3.0

## Table of Contents
1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Deployment](#deployment)
7. [Monitoring](#monitoring)
8. [Security](#security)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance](#maintenance)

---

## Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/your-org/agent-platform.git
cd agent-platform

# Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

# Start infrastructure
docker-compose up -d nats postgres redis

# Run engines
python optimizing_engine.py  # Terminal 1
python performance_engine.py  # Terminal 2
python analyzer_engine.py    # Terminal 3
```

### Production Deployment
```bash
# Using Docker Compose
docker-compose up -d

# Using Kubernetes
kubectl apply -f k8s/
```

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer                           │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴──────────────┬────────────────────────┐
    │                           │                        │
┌───▼──────────┐   ┌───────────▼────┐   ┌──────────────▼───┐
│  Optimizing  │   │  Performance   │   │    Analyzer      │
│   Engine     │   │     Engine     │   │     Engine       │
│  (2+ pods)   │   │   (2+ pods)    │   │   (2+ pods)      │
└───┬──────────┘   └────────┬───────┘   └────────┬─────────┘
    │                       │                     │
    └───────────────────────┼─────────────────────┘
                           │
            ┌──────────────┴───────────────┐
            │                              │
    ┌───────▼─────────┐           ┌───────▼────────┐
    │  NATS JetStream │           │   PostgreSQL   │
    │   (Messaging)   │           │   (Database)   │
    └─────────────────┘           └────────────────┘
            │
    ┌───────▼─────────┐
    │      Redis      │
    │     (Cache)     │
    └─────────────────┘
```

### Data Flow
1. **Optimizing Engine**: Monitors system metrics → Identifies optimization opportunities → Applies optimizations → Records results
2. **Performance Engine**: Collects performance data → Detects anomalies → Generates alerts → Triggers auto-remediation
3. **Analyzer Engine**: Receives code → Analyzes quality → Generates reports → Suggests fixes

---

## Prerequisites

### System Requirements
- **CPU**: 4+ cores per engine
- **RAM**: 8GB+ per engine
- **Storage**: 100GB+ for logs and metrics
- **Network**: 1Gbps+ recommended

### Software Requirements
- **Python**: 3.10+ (3.11 recommended)
- **Docker**: 24.0+ with Compose v2
- **Kubernetes**: 1.28+ (for K8s deployment)
- **PostgreSQL**: 15+
- **Redis**: 7+
- **NATS**: 2.10+

### Development Tools
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3.11 python3.11-venv python3.11-dev \
    postgresql-client redis-tools \
    build-essential libpq-dev \
    curl git

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

---

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-org/agent-platform.git
cd agent-platform
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

Required environment variables:
```bash
# Database
POSTGRES_PASSWORD=secure_password_here
POSTGRES_URL=postgresql://agentuser:${POSTGRES_PASSWORD}@postgres:5432/agentdb

# Redis
REDIS_URL=redis://redis:6379

# NATS
NATS_URL=nats://nats:4222

# Security
JWT_SECRET=your_jwt_secret_32_chars_min
ENCRYPTION_KEY=your_encryption_key_here

# Monitoring
GRAFANA_PASSWORD=secure_grafana_password

# Feature Flags
ENABLE_ML_FEATURES=true
ENABLE_AUTO_REMEDIATION=true
LOG_LEVEL=INFO
```

### 3. Initialize Database
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for startup
sleep 10

# Initialize schema
docker-compose exec postgres psql -U agentuser -d agentdb -f /docker-entrypoint-initdb.d/init.sql
```

### 4. Build Images
```bash
# Build all engines
docker-compose build

# Or build individually
docker build -f Dockerfile.optimizing -t optimizing-engine:3.0 .
docker build -f Dockerfile.performance -t performance-engine:3.0 .
docker build -f Dockerfile.analyzer -t analyzer-engine:3.0 .
```

---

## Configuration

### Engine Configuration

#### Optimizing Engine
```yaml
# config/optimizing-engine.yaml
optimization:
  monitoring_interval: 60  # seconds
  auto_apply_threshold: 0.8  # confidence threshold
  max_concurrent_optimizations: 5
  
thresholds:
  cpu_usage_warning: 70.0
  cpu_usage_critical: 90.0
  memory_usage_warning: 80.0
  memory_usage_critical: 95.0

cache:
  default_ttl: 3600  # 1 hour
  max_size_mb: 1024
  strategy: adaptive
```

#### Performance Engine
```yaml
# config/performance-engine.yaml
monitoring:
  interval: 5  # seconds
  retention_days: 30
  aggregation_interval: 60
  
alerts:
  consecutive_violations: 3
  cooldown_seconds: 300
  
anomaly_detection:
  enabled: true
  sensitivity: 2.5
  window_size: 100
  
auto_remediation:
  enabled: true
  max_actions_per_hour: 10
```

#### Analyzer Engine
```yaml
# config/analyzer-engine.yaml
analysis:
  default_depth: deep
  cache_results: true
  cache_ttl: 3600
  
quality_gates:
  maintainability_index: 65.0
  technical_debt_ratio: 5.0
  code_coverage: 80.0
  
ml_features:
  false_positive_detection: true
  auto_fix_suggestions: true
```

---

## Deployment

### Docker Compose (Development/Small Production)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Scale engines
docker-compose up -d --scale optimizing-engine=3 --scale performance-engine=3
```

### Kubernetes (Production)

```bash
# Create namespace
kubectl create namespace agent-platform

# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy infrastructure
kubectl apply -f k8s/nats-deployment.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

# Deploy engines
kubectl apply -f k8s/optimizing-engine-deployment.yaml
kubectl apply -f k8s/performance-engine-deployment.yaml
kubectl apply -f k8s/analyzer-engine-deployment.yaml

# Deploy monitoring
kubectl apply -f k8s/monitoring/

# Check status
kubectl get pods -n agent-platform
kubectl get services -n agent-platform

# View logs
kubectl logs -f deployment/optimizing-engine -n agent-platform
```

### Helm Deployment (Recommended)
```bash
# Add Helm chart repository
helm repo add agent-platform https://charts.agent-platform.io
helm repo update

# Install
helm install agent-platform agent-platform/platform \
  --namespace agent-platform \
  --create-namespace \
  --values values-production.yaml

# Upgrade
helm upgrade agent-platform agent-platform/platform \
  --namespace agent-platform \
  --values values-production.yaml
```

---

## Monitoring

### Prometheus Metrics

Each engine exposes metrics on port 909X:
- Optimizing Engine: `:9091/metrics`
- Performance Engine: `:9092/metrics`
- Analyzer Engine: `:9093/metrics`

Key metrics:
```
# Optimizing Engine
optimizing_engine_optimizations_total{rule_id,status}
optimizing_engine_optimization_duration_seconds{rule_id}
optimizing_engine_system_cpu_percent
optimizing_engine_system_memory_percent

# Performance Engine
performance_engine_cpu_percent
performance_engine_memory_percent
performance_engine_alerts_total{severity}
performance_engine_anomalies_total{type}

# Analyzer Engine
analyzer_engine_analyses_total
analyzer_engine_issues_total{severity,category}
analyzer_engine_analysis_duration_seconds
```

### Grafana Dashboards

Access Grafana at `http://localhost:3000` (default: admin/admin123)

Pre-configured dashboards:
1. **System Overview**: All engines, resource usage, health status
2. **Optimizing Engine**: Optimization metrics, rule performance, improvements
3. **Performance Engine**: Real-time monitoring, alerts, anomalies
4. **Analyzer Engine**: Code quality trends, issue distribution

Import dashboards:
```bash
# Copy dashboards
cp monitoring/grafana/dashboards/*.json /var/lib/grafana/dashboards/

# Or via API
curl -X POST http://admin:admin123@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboards/system-overview.json
```

### Alerting

Configure AlertManager:
```yaml
# monitoring/alertmanager.yml
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'team-notifications'

receivers:
  - name: 'team-notifications'
    email_configs:
      - to: 'team@example.com'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
```

Alert rules:
```yaml
# monitoring/alerts.yml
groups:
  - name: engines
    interval: 30s
    rules:
      - alert: HighCPUUsage
        expr: optimizing_engine_system_cpu_percent > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High CPU usage detected"
      
      - alert: HighErrorRate
        expr: rate(performance_engine_errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: high
```

---

## Security

### Best Practices

1. **Secrets Management**
```bash
# Use Kubernetes secrets
kubectl create secret generic agent-secrets \
  --from-literal=postgres-password='your-password' \
  --from-literal=jwt-secret='your-jwt-secret'

# Or use external secret managers
# - AWS Secrets Manager
# - HashiCorp Vault
# - Azure Key Vault
```

2. **Network Security**
```yaml
# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-network-policy
spec:
  podSelector:
    matchLabels:
      app: optimizing-engine
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nats
```

3. **TLS/SSL**
```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt

# Create secret
kubectl create secret tls agent-tls \
  --cert=tls.crt --key=tls.key
```

4. **RBAC**
```yaml
# Service account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: engine-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: engine-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
```

---

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up -d --scale optimizing-engine=5

# Kubernetes
kubectl scale deployment optimizing-engine --replicas=5 -n agent-platform

# Auto-scaling (HPA)
kubectl autoscale deployment optimizing-engine \
  --min=2 --max=10 \
  --cpu-percent=70 \
  -n agent-platform
```

### Vertical Scaling

Update resource limits:
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2"
  limits:
    memory: "8Gi"
    cpu: "4"
```

### Database Scaling

```bash
# Read replicas
kubectl apply -f k8s/postgres-replica.yaml

# Connection pooling
# Use PgBouncer or built-in pool settings
POSTGRES_POOL_MIN=10
POSTGRES_POOL_MAX=100
```

---

## Troubleshooting

### Common Issues

#### 1. Engine Not Starting
```bash
# Check logs
docker-compose logs optimizing-engine

# Common causes:
# - Database connection failed
# - Redis unavailable
# - NATS not ready

# Solution: Verify infrastructure
docker-compose ps
docker-compose restart postgres redis nats
```

#### 2. High Memory Usage
```bash
# Check metrics
curl localhost:9091/metrics | grep memory

# Analyze
kubectl top pods -n agent-platform

# Solution: Adjust limits or scale
kubectl set resources deployment optimizing-engine \
  --limits=memory=8Gi -n agent-platform
```

#### 3. Slow Performance
```bash
# Check database
psql -h localhost -U agentuser -d agentdb
> SELECT * FROM pg_stat_activity WHERE state = 'active';

# Check Redis
redis-cli INFO stats

# Solution: Add indexes, optimize queries
```

### Debug Mode

Enable debug logging:
```bash
# Environment variable
LOG_LEVEL=DEBUG

# Or via API
curl -X POST localhost:9091/api/v1/config \
  -d '{"log_level": "DEBUG"}'
```

### Health Checks

```bash
# Docker
docker-compose ps

# Kubernetes
kubectl get pods -n agent-platform
kubectl describe pod optimizing-engine-xxx -n agent-platform

# Manual check
curl http://localhost:9091/health
curl http://localhost:9092/health
curl http://localhost:9093/health
```

---

## Maintenance

### Backup

#### Database Backup
```bash
# Backup
docker-compose exec postgres pg_dump -U agentuser agentdb > backup.sql

# Restore
docker-compose exec -T postgres psql -U agentuser agentdb < backup.sql

# Automated backups
0 2 * * * /usr/local/bin/backup-database.sh
```

#### Configuration Backup
```bash
# Backup configs
tar -czf configs-$(date +%Y%m%d).tar.gz config/ k8s/

# Backup secrets (encrypted)
kubectl get secrets -n agent-platform -o yaml > secrets.yaml
gpg -c secrets.yaml
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Update with zero downtime
docker-compose up -d --no-deps --build optimizing-engine

# Kubernetes rolling update
kubectl set image deployment/optimizing-engine \
  optimizing-engine=optimizing-engine:3.1 \
  -n agent-platform
```

### Log Rotation

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Cleanup

```bash
# Remove old containers
docker system prune -a

# Clean old logs
find /var/log/engines -name "*.log" -mtime +30 -delete

# Vacuum database
docker-compose exec postgres vacuumdb -U agentuser -d agentdb --analyze
```

---

## Production Checklist

- [ ] All secrets configured and secured
- [ ] TLS/SSL certificates installed
- [ ] Database initialized and backed up
- [ ] Monitoring and alerting configured
- [ ] Log aggregation set up
- [ ] Resource limits configured
- [ ] Auto-scaling policies defined
- [ ] Disaster recovery plan documented
- [ ] Security scanning completed
- [ ] Performance testing passed
- [ ] Documentation updated
- [ ] Team trained on operations

---

## Support

- **Documentation**: https://docs.agent-platform.io
- **Issues**: https://github.com/your-org/agent-platform/issues
- **Slack**: #agent-platform-support
- **Email**: support@agent-platform.io

---

## License

Copyright © 2025 Your Organization. All rights reserved.
