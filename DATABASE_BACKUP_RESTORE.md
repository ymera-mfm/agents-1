# Database Backup and Restore Procedures

## Overview
This document outlines the backup and restore procedures for the YMERA platform database.

## Backup Strategy

### Automated Backups

#### Daily Full Backups
- **Schedule**: Every day at 2:00 AM UTC
- **Retention**: 7 days
- **Location**: `/backups/daily/`
- **Format**: PostgreSQL custom format (.dump)

#### Weekly Full Backups
- **Schedule**: Every Sunday at 1:00 AM UTC
- **Retention**: 4 weeks
- **Location**: `/backups/weekly/`
- **Format**: PostgreSQL custom format (.dump)

#### Monthly Backups
- **Schedule**: First day of each month at 12:00 AM UTC
- **Retention**: 12 months
- **Location**: `/backups/monthly/`
- **Format**: PostgreSQL custom format (.dump)

### Manual Backup Procedures

#### Create a Manual Backup

```bash
# Full database backup
pg_dump -Fc -h localhost -U ymera_user -d ymera_production -f /backups/manual/backup_$(date +%Y%m%d_%H%M%S).dump

# Backup with compression
pg_dump -Fc -Z 9 -h localhost -U ymera_user -d ymera_production -f /backups/manual/backup_$(date +%Y%m%d_%H%M%S).dump

# Backup specific tables
pg_dump -Fc -h localhost -U ymera_user -d ymera_production -t users -t agents -t tasks -f /backups/manual/core_tables_$(date +%Y%m%d_%H%M%S).dump
```

## Restore Procedures

### Full Database Restore

```bash
# 1. Drop existing database (if needed)
dropdb -h localhost -U ymera_user ymera_production

# 2. Create new database
createdb -h localhost -U ymera_user ymera_production

# 3. Restore from backup
pg_restore -h localhost -U ymera_user -d ymera_production /backups/manual/backup_20251020_120000.dump

# 4. Verify restoration
psql -h localhost -U ymera_user -d ymera_production -c "SELECT COUNT(*) FROM users;"
```

## Retention Policy

| Backup Type | Retention Period | Storage Location |
|-------------|------------------|------------------|
| Daily       | 7 days          | Local + S3       |
| Weekly      | 4 weeks         | Local + S3       |
| Monthly     | 12 months       | S3 + Glacier     |
| Annual      | 7 years         | Glacier          |

## Contact Information

### Emergency Contacts
- **DBA Team**: dba@ymera.com
- **DevOps Team**: devops@ymera.com
- **On-Call**: +1-555-BACKUP (24/7)
