#!/bin/bash
# Production Deployment Script for Agent Manager Platform
# Version: 1.0.0

set -e  # Exit on error

echo "================================================"
echo "Agent Manager Platform - Production Deployment"
echo "================================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env.production"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisite() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        exit 1
    fi
    log_info "$1 is installed"
}

# Step 1: Check prerequisites
log_info "Step 1: Checking prerequisites..."
check_prerequisite "python3"
check_prerequisite "docker"
check_prerequisite "docker-compose"
check_prerequisite "psql"  # PostgreSQL client
check_prerequisite "redis-cli"

# Step 2: Validate environment file
log_info "Step 2: Validating environment configuration..."
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file $ENV_FILE not found"
    exit 1
fi

# Check required environment variables
required_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET_KEY"
    "ENCRYPTION_KEY"
    "API_KEY_SECRET"
)

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" "$ENV_FILE"; then
        log_error "Required variable $var not found in $ENV_FILE"
        exit 1
    fi
done
log_info "Environment configuration validated"

# Step 3: Create backup directory
log_info "Step 3: Creating backup directory..."
mkdir -p "$BACKUP_DIR"
log_info "Backup directory created: $BACKUP_DIR"

# Step 4: Backup current database (if exists)
log_info "Step 4: Backing up database..."
if psql "$DATABASE_URL" -c '\l' &> /dev/null; then
    pg_dump "$DATABASE_URL" > "$BACKUP_DIR/database_backup.sql"
    log_info "Database backup created"
else
    log_warn "No existing database to backup"
fi

# Step 5: Install Python dependencies
log_info "Step 5: Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
log_info "Dependencies installed"

# Step 6: Run database migrations
log_info "Step 6: Running database migrations..."
python3 << EOF
import asyncio
from database.secure_database_manager import SecureDatabaseManager
from models.secure_models import Base
from config import settings

async def migrate():
    db_manager = SecureDatabaseManager(
        settings.database.url.get_secret_value()
    )
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database migrations completed")
    await db_manager.engine.dispose()

asyncio.run(migrate())
EOF
log_info "Database migrations completed"

# Step 7: Validate configuration files
log_info "Step 7: Validating configuration files..."
config_files=(
    "config.supreme.yaml"
    "config.ai.yaml"
    "config.monitoring.yaml"
    "config.deployment.yaml"
    "config.performance.yaml"
    "config.security_enhancements.yaml"
    "config.zero_trust_compliance.yaml"
    "config.agent_management.yaml"
)

for config_file in "${config_files[@]}"; do
    if [ ! -f "$config_file" ]; then
        log_error "Configuration file $config_file not found"
        exit 1
    fi
    python3 -c "import yaml; yaml.safe_load(open('$config_file'))" || {
        log_error "Invalid YAML in $config_file"
        exit 1
    }
done
log_info "All configuration files validated"

# Step 8: Run security checks
log_info "Step 8: Running security checks..."

# Check JWT secret length
JWT_SECRET=$(grep "^JWT_SECRET_KEY=" "$ENV_FILE" | cut -d '=' -f2)
if [ ${#JWT_SECRET} -lt 32 ]; then
    log_error "JWT_SECRET_KEY must be at least 32 characters"
    exit 1
fi

# Check encryption key
ENCRYPTION_KEY=$(grep "^ENCRYPTION_KEY=" "$ENV_FILE" | cut -d '=' -f2)
if [ ${#ENCRYPTION_KEY} -lt 32 ]; then
    log_error "ENCRYPTION_KEY must be at least 32 characters"
    exit 1
fi

log_info "Security checks passed"

# Step 9: Run tests
log_info "Step 9: Running tests..."
python3 -m pytest tests/ -v --tb=short || {
    log_error "Tests failed"
    exit 1
}
log_info "All tests passed"

# Step 10: Build Docker images
log_info "Step 10: Building Docker images..."
docker-compose build --no-cache
log_info "Docker images built"

# Step 11: Start services
log_info "Step 11: Starting services..."
docker-compose up -d

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 10

# Check health endpoint
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_info "Services are healthy"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    log_error "Services failed to become healthy"
    docker-compose logs
    exit 1
fi

# Step 12: Run smoke tests
log_info "Step 12: Running smoke tests..."

# Test health endpoint
curl -f http://localhost:8000/health || {
    log_error "Health check failed"
    exit 1
}

# Test metrics endpoint
curl -f http://localhost:8000/metrics || {
    log_error "Metrics endpoint failed"
    exit 1
}

log_info "Smoke tests passed"

# Step 13: Setup monitoring
log_info "Step 13: Setting up monitoring..."
# Start Prometheus
docker-compose up -d prometheus grafana
log_info "Monitoring services started"

# Step 14: Display deployment summary
echo ""
echo "================================================"
log_info "Deployment completed successfully!"
echo "================================================"
echo ""
echo "Services running:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Metrics: http://localhost:8000/metrics"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Review logs: docker-compose logs -f"
echo "  2. Access API docs: http://localhost:8000/docs"
echo "  3. Configure Grafana dashboards"
echo "  4. Set up alerting rules"
echo "  5. Create admin user account"
echo ""
echo "================================================"
