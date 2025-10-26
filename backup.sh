#!/bin/bash
# YMERA Platform - Backup Script
# Creates database and application backups

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-ymera_user}"
DB_NAME="${DB_NAME:-ymera_production}"

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Create backup
create_backup() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    TAG="${1:-$TIMESTAMP}"
    
    log_info "Creating backup with tag: $TAG"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Database backup
    log_info "Backing up database..."
    pg_dump -Fc -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f "$BACKUP_DIR/db_${TAG}.dump"
    
    log_info "Backup created: $BACKUP_DIR/db_${TAG}.dump"
    
    # Compress backup
    gzip "$BACKUP_DIR/db_${TAG}.dump"
    
    log_info "Backup completed successfully"
}

create_backup "$@"
