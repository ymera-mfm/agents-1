#!/bin/bash
# YMERA Platform - Deployment Script
# Automates the deployment process with safety checks

set -e  # Exit on error

# Configuration
APP_NAME="ymera-agents"
DEPLOY_USER="${DEPLOY_USER:-app}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/ymera}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
LOG_DIR="${LOG_DIR:-/var/log/ymera}"
ENV_FILE="${ENV_FILE:-.env}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run as root or with sudo
check_privileges() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found"
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_info "Pre-deployment checks passed"
}

# Create backup before deployment
create_backup() {
    log_info "Creating pre-deployment backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="pre_deploy_${TIMESTAMP}"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if [ -f "./scripts/backup.sh" ]; then
        ./scripts/backup.sh --tag "$BACKUP_NAME"
    else
        log_warn "Backup script not found, skipping database backup"
    fi
    
    # Backup current deployment
    if [ -d "$DEPLOY_DIR" ]; then
        tar -czf "$BACKUP_DIR/deploy_${BACKUP_NAME}.tar.gz" -C "$DEPLOY_DIR" .
        log_info "Deployment backup created: $BACKUP_DIR/deploy_${BACKUP_NAME}.tar.gz"
    fi
    
    echo "$BACKUP_NAME" > /tmp/ymera_last_backup
}

# Pull latest changes
pull_changes() {
    log_info "Pulling latest changes..."
    
    if [ -d ".git" ]; then
        git pull origin main
    else
        log_warn "Not a git repository, skipping git pull"
    fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    if docker compose version &> /dev/null; then
        docker compose build --no-cache
    else
        docker-compose build --no-cache
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Check if alembic is configured
    if [ -f "alembic.ini" ]; then
        if docker compose version &> /dev/null; then
            docker compose run --rm app alembic upgrade head
        else
            docker-compose run --rm app alembic upgrade head
        fi
    else
        log_warn "Alembic not configured, skipping migrations"
    fi
}

# Start services
start_services() {
    log_info "Starting services..."
    
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    MAX_RETRIES=30
    RETRY_INTERVAL=2
    
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_info "Services are healthy"
            return 0
        fi
        
        log_info "Waiting for services... ($i/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done
    
    log_error "Services failed to become healthy"
    return 1
}

# Run post-deployment verification
post_deployment_verification() {
    log_info "Running post-deployment verification..."
    
    if [ -f "./scripts/health-check.sh" ]; then
        ./scripts/health-check.sh
    else
        # Basic health check
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_info "Health check passed"
        else
            log_error "Health check failed"
            return 1
        fi
    fi
}

# Main deployment flow
main() {
    log_info "Starting deployment of $APP_NAME..."
    
    # Run pre-deployment checks
    pre_deployment_checks
    
    # Create backup
    create_backup
    
    # Pull latest changes
    pull_changes
    
    # Build images
    build_images
    
    # Run migrations
    run_migrations
    
    # Start services
    start_services
    
    # Wait for services to be healthy
    if ! wait_for_health; then
        log_error "Deployment verification failed"
        log_warn "Consider rolling back using ./scripts/rollback.sh"
        exit 1
    fi
    
    # Post-deployment verification
    if ! post_deployment_verification; then
        log_error "Post-deployment verification failed"
        log_warn "Consider rolling back using ./scripts/rollback.sh"
        exit 1
    fi
    
    log_info "Deployment completed successfully!"
    log_info "Application is running at http://localhost:8000"
}

# Run main function
main "$@"
