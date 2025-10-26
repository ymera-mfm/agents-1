# YMERA Enhanced Learning System - Deployment Guide

This comprehensive guide provides step-by-step instructions for deploying the YMERA Enhanced Learning System in various environments, from local development to production Kubernetes clusters.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Deployment](#local-development-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Provider Specific Instructions](#cloud-provider-specific-instructions)
6. [Configuration Management](#configuration-management)
7. [Security Hardening](#security-hardening)
8. [Monitoring and Observability Setup](#monitoring-and-observability-setup)
9. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
10. [Scaling and Performance Tuning](#scaling-and-performance-tuning)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements (Development):**
- CPU: 4 cores
- RAM: 16 GB
- Storage: 50 GB SSD
- OS: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2

**Recommended Requirements (Production):**
- CPU: 16+ cores
- RAM: 64+ GB
- Storage: 500+ GB SSD (with backup storage)
- GPU: NVIDIA GPU with CUDA support (for deep learning workloads)
- OS: Linux (Ubuntu 22.04 LTS recommended)

### Software Dependencies

- **Docker**: 24.0+ with Docker Compose 2.0+
- **Kubernetes**: 1.28+ (for production deployment)
- **kubectl**: Latest version
- **Helm**: 3.12+ (optional, for Kubernetes package management)
- **Python**: 3.11+
- **Git**: Latest version

### Network Requirements

- Outbound internet access for pulling Docker images and Python packages
- Open ports for services (configurable):
  - 8080: API Gateway
  - 8001-8006: Microservices
  - 5432: PostgreSQL
  - 27017: MongoDB
  - 6379: Redis
  - 9092: Kafka
  - 9090: Prometheus
  - 3000: Grafana
  - 16686: Jaeger

## Local Development Deployment

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd ymera_enhanced

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Create .env file from template
cp .env.example .env

# Edit .env with your local settings
nano .env
```

**Minimal .env configuration for development:**

```env
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DB_PASSWORD=ymera_password
NOSQL_PASSWORD=ymera_password
REDIS_PASSWORD=ymera_password

# Security (generate secure secrets for production)
JWT_SECRET=your-dev-jwt-secret-change-in-production

# Storage
STORAGE_ACCESS_KEY=ymera_admin
STORAGE_SECRET_KEY=ymera_password
```

### Step 3: Start Infrastructure Services

```bash
# Start all infrastructure services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

### Step 4: Initialize Databases

```bash
# Run database migrations (if applicable)
python scripts/init_databases.py

# Verify database connectivity
python scripts/check_connections.py
```

### Step 5: Run Services Locally

```bash
# Terminal 1: Learning Engine
python -m learning_engine.main

# Terminal 2: Multimodal Service
python -m multimodal.main

# Terminal 3: Explainability Service
python -m explainability.main

# ... and so on for other services
```

### Step 6: Verify Deployment

```bash
# Check service health
curl http://localhost:8001/health

# Access API documentation
open http://localhost:8001/docs
```

## Docker Deployment

### Step 1: Build Docker Images

```bash
# Build all service images
docker-compose -f docker-compose.prod.yml build

# Or build individual services
docker build -t ymera-learning-engine:latest -f deployments/docker/learning-engine.Dockerfile .
```

### Step 2: Configure Production Environment

```bash
# Create production .env file
cp .env.example .env.prod

# Edit with production settings
nano .env.prod
```

**Important production settings:**

```env
ENVIRONMENT=production
DEBUG=false

# Use strong, randomly generated secrets
JWT_SECRET=<generate-with-openssl-rand-base64-32>
DB_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>

# Configure cloud storage
STORAGE_PROVIDER=s3
STORAGE_BUCKET=ymera-production-bucket
STORAGE_ACCESS_KEY=<aws-access-key>
STORAGE_SECRET_KEY=<aws-secret-key>

# Enable security features
ENABLE_ENCRYPTION_AT_REST=true
ENABLE_ENCRYPTION_IN_TRANSIT=true
```

### Step 3: Deploy with Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Scale specific services
docker-compose -f docker-compose.prod.yml up -d --scale learning-engine=3

# Monitor deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 4: Configure Reverse Proxy (Nginx)

```bash
# Install Nginx
sudo apt-get update
sudo apt-get install nginx

# Copy Nginx configuration
sudo cp deployments/nginx/ymera.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/ymera.conf /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## Kubernetes Deployment

### Step 1: Prepare Kubernetes Cluster

```bash
# Verify cluster access
kubectl cluster-info
kubectl get nodes

# Create namespace
kubectl create namespace ymera

# Set as default namespace
kubectl config set-context --current --namespace=ymera
```

### Step 2: Configure Secrets and ConfigMaps

```bash
# Create secrets
kubectl create secret generic ymera-secrets \
  --from-literal=db-password=<strong-password> \
  --from-literal=jwt-secret=<jwt-secret> \
  --from-literal=redis-password=<redis-password> \
  --namespace=ymera

# Create ConfigMap
kubectl create configmap ymera-config \
  --from-file=config/settings.py \
  --namespace=ymera
```

### Step 3: Deploy Infrastructure Components

```bash
# Deploy PostgreSQL
kubectl apply -f deployments/kubernetes/postgres.yaml

# Deploy MongoDB
kubectl apply -f deployments/kubernetes/mongodb.yaml

# Deploy Redis
kubectl apply -f deployments/kubernetes/redis.yaml

# Deploy Kafka
kubectl apply -f deployments/kubernetes/kafka.yaml

# Verify infrastructure
kubectl get pods -n ymera
kubectl get pvc -n ymera
```

### Step 4: Deploy Application Services

```bash
# Deploy all services
kubectl apply -f deployments/kubernetes/services/

# Or deploy individually
kubectl apply -f deployments/kubernetes/services/learning-engine.yaml
kubectl apply -f deployments/kubernetes/services/multimodal.yaml
kubectl apply -f deployments/kubernetes/services/explainability.yaml
kubectl apply -f deployments/kubernetes/services/automl.yaml
kubectl apply -f deployments/kubernetes/services/analytics.yaml

# Deploy API Gateway
kubectl apply -f deployments/kubernetes/api-gateway.yaml
```

### Step 5: Configure Ingress

```bash
# Install Ingress Controller (if not already installed)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.4/deploy/static/provider/cloud/deploy.yaml

# Deploy Ingress resource
kubectl apply -f deployments/kubernetes/ingress.yaml

# Get external IP
kubectl get ingress -n ymera
```

### Step 6: Deploy Monitoring Stack

```bash
# Deploy Prometheus
kubectl apply -f deployments/kubernetes/monitoring/prometheus.yaml

# Deploy Grafana
kubectl apply -f deployments/kubernetes/monitoring/grafana.yaml

# Deploy Jaeger
kubectl apply -f deployments/kubernetes/monitoring/jaeger.yaml

# Verify monitoring stack
kubectl get pods -n ymera -l app.kubernetes.io/component=monitoring
```

### Step 7: Configure Horizontal Pod Autoscaling

```bash
# Deploy HPA for services
kubectl apply -f deployments/kubernetes/hpa/

# Verify HPA
kubectl get hpa -n ymera
```

## Cloud Provider Specific Instructions

### AWS (EKS)

```bash
# Create EKS cluster
eksctl create cluster \
  --name ymera-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --managed

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name ymera-cluster

# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=ymera-cluster

# Use AWS RDS for PostgreSQL
# Use AWS DocumentDB for MongoDB
# Use AWS ElastiCache for Redis
# Use AWS MSK for Kafka
# Use AWS S3 for object storage
```

### GCP (GKE)

```bash
# Create GKE cluster
gcloud container clusters create ymera-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10

# Get credentials
gcloud container clusters get-credentials ymera-cluster --zone us-central1-a

# Use Cloud SQL for PostgreSQL
# Use Cloud Firestore/MongoDB Atlas for NoSQL
# Use Cloud Memorystore for Redis
# Use Cloud Pub/Sub (or Kafka on GKE)
# Use Cloud Storage for object storage
```

### Azure (AKS)

```bash
# Create resource group
az group create --name ymera-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group ymera-rg \
  --name ymera-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10 \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group ymera-rg --name ymera-cluster

# Use Azure Database for PostgreSQL
# Use Azure Cosmos DB for NoSQL
# Use Azure Cache for Redis
# Use Azure Event Hubs (or Kafka on AKS)
# Use Azure Blob Storage for object storage
```

## Configuration Management

### Using Kubernetes ConfigMaps

```bash
# Update configuration
kubectl create configmap ymera-config \
  --from-file=config/ \
  --dry-run=client -o yaml | kubectl apply -f -

# Rollout restart to pick up changes
kubectl rollout restart deployment/learning-engine -n ymera
```

### Using External Configuration Services

For production, consider using:
- **Consul**: Distributed configuration and service discovery
- **etcd**: Kubernetes-native key-value store
- **AWS Systems Manager Parameter Store**: For AWS deployments
- **GCP Secret Manager**: For GCP deployments
- **Azure Key Vault**: For Azure deployments

## Security Hardening

### Network Security

```bash
# Apply Network Policies
kubectl apply -f deployments/kubernetes/network-policies/

# Enable Pod Security Standards
kubectl label namespace ymera pod-security.kubernetes.io/enforce=restricted
```

### RBAC Configuration

```bash
# Create service accounts
kubectl apply -f deployments/kubernetes/rbac/service-accounts.yaml

# Apply roles and bindings
kubectl apply -f deployments/kubernetes/rbac/roles.yaml
kubectl apply -f deployments/kubernetes/rbac/role-bindings.yaml
```

### TLS/SSL Configuration

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f deployments/kubernetes/cert-manager/cluster-issuer.yaml

# Update Ingress to use TLS
kubectl apply -f deployments/kubernetes/ingress-tls.yaml
```

## Monitoring and Observability Setup

### Prometheus Configuration

```bash
# Deploy Prometheus Operator
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Create ServiceMonitors
kubectl apply -f deployments/kubernetes/monitoring/service-monitors/
```

### Grafana Dashboards

```bash
# Import dashboards
kubectl create configmap grafana-dashboards \
  --from-file=deployments/grafana/dashboards/ \
  --namespace=ymera

# Access Grafana
kubectl port-forward -n ymera svc/grafana 3000:3000
```

### Distributed Tracing

```bash
# Configure OpenTelemetry Collector
kubectl apply -f deployments/kubernetes/monitoring/otel-collector.yaml

# Verify tracing
kubectl port-forward -n ymera svc/jaeger-query 16686:16686
```

## Backup and Disaster Recovery

### Database Backups

```bash
# PostgreSQL backup
kubectl exec -n ymera postgres-0 -- pg_dump -U ymera_user ymera > backup.sql

# MongoDB backup
kubectl exec -n ymera mongodb-0 -- mongodump --out=/backup

# Automated backups with CronJob
kubectl apply -f deployments/kubernetes/cronjobs/backup.yaml
```

### Velero for Kubernetes Backups

```bash
# Install Velero
velero install \
  --provider aws \
  --bucket ymera-backups \
  --secret-file ./credentials-velero

# Create backup schedule
velero schedule create ymera-daily --schedule="0 2 * * *"

# Test restore
velero restore create --from-backup ymera-daily-20231001
```

## Scaling and Performance Tuning

### Horizontal Scaling

```bash
# Manual scaling
kubectl scale deployment learning-engine --replicas=5 -n ymera

# Auto-scaling based on CPU
kubectl autoscale deployment learning-engine \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n ymera
```

### Vertical Scaling

```bash
# Update resource requests/limits
kubectl set resources deployment learning-engine \
  --requests=cpu=2,memory=4Gi \
  --limits=cpu=4,memory=8Gi \
  -n ymera
```

### Performance Optimization

- Enable connection pooling for databases
- Configure Redis as a distributed cache
- Use CDN for static assets
- Enable gzip compression in Nginx
- Optimize database indices
- Use read replicas for read-heavy workloads

## Troubleshooting

### Common Issues and Solutions

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n ymera
kubectl logs <pod-name> -n ymera
```

**Service connectivity issues:**
```bash
kubectl get svc -n ymera
kubectl get endpoints -n ymera
kubectl exec -it <pod-name> -n ymera -- curl http://service-name:port/health
```

**Resource constraints:**
```bash
kubectl top nodes
kubectl top pods -n ymera
kubectl describe node <node-name>
```

**Database connection errors:**
```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:16 --restart=Never -- psql -h postgres -U ymera_user -d ymera

# Check database logs
kubectl logs -n ymera postgres-0
```

### Health Checks

```bash
# Check all service health endpoints
for service in learning-engine multimodal explainability automl analytics; do
  echo "Checking $service..."
  kubectl exec -n ymera deployment/api-gateway -- curl -s http://$service:8000/health
done
```

### Log Aggregation

```bash
# Stream logs from all services
kubectl logs -f -l app.kubernetes.io/part-of=ymera -n ymera --all-containers=true

# Export logs for analysis
kubectl logs -n ymera --all-containers=true > ymera-logs.txt
```

---

For additional support, consult the main README.md or contact the YMERA development team.
