#!/bin/bash
# YMERA Platform - Rollback Script
# Rolls back to previous deployment version

set -e

# Configuration
APP_NAME="ymera-agents"
BACKUP_DIR="${BACKUP_DIR:-/backups}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get last backup
get_last_backup() {
    if [ -f "/tmp/ymera_last_backup" ]; then
        cat /tmp/ymera_last_backup
    else
        log_error "No backup information found"
        exit 1
    fi
}

# Rollback deployment
rollback_deployment() {
    log_info "Starting rollback for $APP_NAME..."
    
    BACKUP_NAME=$(get_last_backup)
    log_info "Rolling back to backup: $BACKUP_NAME"
    
    # Stop current services
    log_info "Stopping current services..."
    if docker compose version &> /dev/null; then
        docker compose down
    else
        docker-compose down
    fi
    
    # Restore deployment backup
    if [ -f "$BACKUP_DIR/deploy_${BACKUP_NAME}.tar.gz" ]; then
        log_info "Restoring deployment files..."
        tar -xzf "$BACKUP_DIR/deploy_${BACKUP_NAME}.tar.gz" -C "$DEPLOY_DIR"
    fi
    
    # Restore database
    if [ -f "./scripts/restore.sh" ]; then
        log_info "Restoring database..."
        ./scripts/restore.sh "$BACKUP_DIR/db_${BACKUP_NAME}.dump"
    fi
    
    # Start services
    log_info "Starting services..."
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
    
    log_info "Rollback completed successfully"
}

rollback_deployment "$@"
