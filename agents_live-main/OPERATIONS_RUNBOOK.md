# YMERA Database - Operations Runbook

## 🎯 Quick Reference Guide for Database Operations

**Version:** 5.0.0  
**Last Updated:** 2024-10-17

---

## 📚 Table of Contents

1. [Quick Commands](#quick-commands)
2. [Daily Operations](#daily-operations)
3. [Common Tasks](#common-tasks)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance Windows](#maintenance-windows)
6. [Emergency Procedures](#emergency-procedures)

---

## ⚡ Quick Commands

### Health & Status
```bash
# Quick health check
python scripts/database_monitor.py health

# Get database statistics
python -c "import asyncio; from database_core_integrated import get_database_manager; print(asyncio.run((await get_database_manager()).get_statistics()))"

# Check migration status
python database/migration_manager.py status

# Monitor continuously (60s intervals)
python scripts/database_monitor.py monitor --interval 60
```

### Backups
```bash
# Create backup
python scripts/backup_manager.py backup

# List all backups
python scripts/backup_manager.py list

# Verify latest backup
python scripts/backup_manager.py verify $(ls -t database/backups/*.gz | head -1)

# Restore from backup
python scripts/backup_manager.py restore <backup_file>
```

### Migrations
```bash
# Run pending migrations
python database/migration_manager.py migrate

# Check migration status
python database/migration_manager.py status

# Rollback last migration
python database/migration_manager.py rollback --steps 1

# Create new migration
python database/migration_manager.py create <migration_name>
```

### Testing & Development
```bash
# Run all tests
python test_database.py

# Generate test data
python database/fixtures/test_fixtures.py generate --users 100 --tasks 500

# Cleanup test data
python database/fixtures/test_fixtures.py cleanup
```

---

## 📅 Daily Operations

### Morning Routine (09:00)

#### 1. Health Check
```bash
python scripts/database_monitor.py health
```

**Expected Output:**
```
Status: HEALTHY
Database type: postgresql
Response time: <100ms
```

**If unhealthy:** Follow troubleshooting guide below

---

#### 2. Review Overnight Activity
```bash
# Generate 24-hour report
python scripts/database_monitor.py report --hours 24
```

**Check for:**
- Any alerts or warnings
- Performance degradation
- Unusual activity patterns
- Failed operations

---

#### 3. Verify Backups
```bash
# List recent backups
python scripts/backup_manager.py list | head -5

# Verify latest backup
python scripts/backup_manager.py verify $(ls -t database/backups/*.gz | head -1)
```

**Expected:** Backup created within last 24 hours, verification passes

---

#### 4. Check Disk Space
```bash
python scripts/database_monitor.py health | grep -A5 "disk_space"
```

**Action if >80%:** Run cleanup procedures

---

### End of Day Routine (17:00)

#### 1. Performance Review
```bash
python scripts/database_monitor.py metrics
```

---

#### 2. Cleanup Operations
```bash
# Optimize database
python -c "import asyncio; from database_core_integrated import get_database_manager; asyncio.run((await get_database_manager()).optimize_database())"
```

---

#### 3. Export Daily Metrics
```bash
python scripts/database_monitor.py export metrics_$(date +%Y%m%d).json
```

---

## 🔧 Common Tasks

### Task 1: Add New User

#### Via Python
```python
import asyncio
from database_core_integrated import get_db_session, User, BaseRepository

async def create_user():
    async with get_db_session() as session:
        repo = BaseRepository(session, User)
        user = await repo.create(
            username="newuser",
            email="newuser@example.com",
            password_hash="<bcrypt_hash>",
            role="user",
            is_active=True
        )
        print(f"Created user: {user.id}")

asyncio.run(create_user())
```

#### Via SQL (Emergency)
```sql
INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
VALUES (
    uuid_generate_v4(),
    'newuser',
    'newuser@example.com',
    '<bcrypt_hash>',
    'user',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

---

### Task 2: Reset User Password

```python
import asyncio
import bcrypt
from database_core_integrated import get_db_session, User, BaseRepository

async def reset_password(user_id: str, new_password: str):
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    async with get_db_session() as session:
        repo = BaseRepository(session, User)
        user = await repo.update(user_id, password_hash=password_hash)
        print(f"Password reset for user: {user.username}")

asyncio.run(reset_password("user_id_here", "new_password"))
```

---

### Task 3: Archive Old Data

```python
import asyncio
from database_core_integrated import get_database_manager

async def archive_data():
    db_manager = await get_database_manager()
    result = await db_manager.cleanup_old_data(days_to_keep=90)
    print(f"Archived: {result['cleaned']}")

asyncio.run(archive_data())
```

---

### Task 4: Optimize Slow Query

#### 1. Identify Slow Query
```bash
python scripts/database_monitor.py health | grep -A5 "query_performance"
```

#### 2. Add Index (if missing)
```python
from sqlalchemy import text
from database_core_integrated import get_db_session

async def add_index():
    async with get_db_session() as session:
        await session.execute(text("""
            CREATE INDEX idx_custom_name ON table_name(column_name)
        """))
        await session.commit()
```

#### 3. Analyze Query Plan
```sql
EXPLAIN ANALYZE
SELECT ... FROM ... WHERE ...;
```

---

### Task 5: Grant User Permissions

```python
import asyncio
from database_core_integrated import get_db_session, User, BaseRepository

async def grant_permissions(user_id: str, permissions: list):
    async with get_db_session() as session:
        repo = BaseRepository(session, User)
        user = await repo.update(user_id, permissions=permissions)
        print(f"Updated permissions for: {user.username}")

asyncio.run(grant_permissions("user_id", ["read", "write", "admin"]))
```

---

### Task 6: Soft Delete vs Hard Delete

#### Soft Delete (Recommended)
```python
import asyncio
from database_core_integrated import get_db_session, User, BaseRepository

async def soft_delete_user(user_id: str):
    async with get_db_session() as session:
        repo = BaseRepository(session, User)
        success = await repo.soft_delete(user_id)
        print(f"Soft deleted: {success}")

asyncio.run(soft_delete_user("user_id"))
```

#### Hard Delete (Caution!)
```python
async def hard_delete_user(user_id: str):
    async with get_db_session() as session:
        repo = BaseRepository(session, User)
        success = await repo.delete(user_id)
        print(f"Hard deleted: {success}")
```

---

## 🔍 Troubleshooting

### Issue 1: Cannot Connect to Database

#### Symptoms
- Connection timeout errors
- "Connection refused" messages
- Health check failures

#### Diagnosis
```bash
# 1. Check database service status
systemctl status postgresql  # or mysql

# 2. Check network connectivity
ping <database_host>
telnet <database_host> <port>

# 3. Verify credentials
echo $DATABASE_URL
```

#### Solutions
```bash
# Restart database service
sudo systemctl restart postgresql

# Check firewall
sudo ufw status
sudo ufw allow 5432/tcp  # PostgreSQL

# Verify configuration
cat /etc/postgresql/*/main/postgresql.conf | grep listen_addresses
```

---

### Issue 2: Slow Performance

#### Symptoms
- Query timeouts
- High response times
- Connection pool exhaustion

#### Diagnosis
```bash
# Check performance metrics
python scripts/database_monitor.py metrics

# Identify slow queries
python scripts/database_monitor.py health | grep slow_queries

# Check connection pool
python scripts/database_monitor.py health | grep -A10 "connection_pool"
```

#### Solutions
```bash
# 1. Increase connection pool
export DB_POOL_SIZE=30
export DB_MAX_OVERFLOW=60

# 2. Optimize database
python -c "import asyncio; from database_core_integrated import get_database_manager; asyncio.run((await get_database_manager()).optimize_database())"

# 3. Add missing indexes (see Task 4)

# 4. Kill long-running queries (PostgreSQL)
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '10 minutes';
```

---

### Issue 3: Disk Space Full

#### Symptoms
- Write failures
- Backup failures
- "No space left on device"

#### Diagnosis
```bash
# Check disk usage
df -h
du -sh /var/lib/postgresql/  # or database directory

# Find large files
find /var/lib/postgresql/ -type f -size +100M
```

#### Solutions
```bash
# 1. Clean old audit logs
python -c "import asyncio; from database_core_integrated import get_database_manager; asyncio.run((await get_database_manager()).cleanup_old_data(days_to_keep=30))"

# 2. Remove old backups
python scripts/backup_manager.py cleanup --days 30

# 3. Vacuum database (PostgreSQL)
VACUUM FULL;

# 4. Archive old data
# Export and delete old records
```

---

### Issue 4: Migration Failure

#### Symptoms
- Migration errors
- Schema inconsistencies
- Rollback needed

#### Diagnosis
```bash
# Check migration status
python database/migration_manager.py status

# Review migration logs
tail -f /var/log/database/migrations.log
```

#### Solutions
```bash
# 1. Rollback failed migration
python database/migration_manager.py rollback --steps 1

# 2. Fix migration script
# Edit migration file

# 3. Re-run migration
python database/migration_manager.py migrate

# 4. If all else fails, restore backup
python scripts/backup_manager.py restore <backup_before_migration>
```

---

### Issue 5: Data Inconsistency

#### Symptoms
- Unexpected data values
- Foreign key violations
- Checksum mismatches

#### Diagnosis
```bash
# Check data integrity
python test_database.py

# Verify constraints
SELECT * FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY';
```

#### Solutions
```bash
# 1. Identify scope of issue
# Run data validation queries

# 2. Restore from backup if needed
python scripts/backup_manager.py restore <verified_backup>

# 3. Re-run data migrations
python database/migration_manager.py migrate

# 4. Update statistics
python -c "import asyncio; from database_core_integrated import get_database_manager; asyncio.run((await get_database_manager()).optimize_database())"
```

---

## 🕐 Maintenance Windows

### Weekly Maintenance (Sunday 02:00-04:00)

#### Pre-Maintenance Checklist
- [ ] Notify users 24 hours in advance
- [ ] Create full backup
- [ ] Verify backup integrity
- [ ] Prepare rollback plan

#### Maintenance Tasks
```bash
# 1. Full backup
python scripts/backup_manager.py backup

# 2. Run pending migrations
python database/migration_manager.py migrate

# 3. Optimize database
python -c "import asyncio; from database_core_integrated import get_database_manager; asyncio.run((await get_database_manager()).optimize_database())"

# 4. Cleanup old data
python -c "import asyncio; from database_core_integrated import get_database_manager; asyncio.run((await get_database_manager()).cleanup_old_data(days_to_keep=90))"

# 5. Update statistics (PostgreSQL)
ANALYZE;

# 6. Vacuum (PostgreSQL)
VACUUM ANALYZE;
```

#### Post-Maintenance Validation
```bash
# 1. Health check
python scripts/database_monitor.py health

# 2. Run tests
python test_database.py

# 3. Performance check
python scripts/database_monitor.py metrics

# 4. Notify users of completion
```

---

### Monthly Maintenance (First Sunday 02:00-05:00)

#### Additional Tasks
```bash
# 1. Full vacuum (PostgreSQL)
VACUUM FULL;

# 2. Reindex (PostgreSQL)
REINDEX DATABASE <database_name>;

# 3. Archive old backups
python scripts/backup_manager.py cleanup --days 90

# 4. Security audit
# Review user permissions
# Check for inactive accounts
# Update credentials if needed

# 5. Capacity planning review
# Analyze growth trends
# Plan for scaling
```

---

## 🚨 Emergency Procedures

### Emergency Contact
**On-Call Engineer:** [Phone/Pager]  
**Escalation:** See DISASTER_RECOVERY.md

### Critical Issues (Immediate Response)

#### Database Down
```bash
# 1. Check service
systemctl status postgresql

# 2. Restart if needed
sudo systemctl restart postgresql

# 3. If fails, restore from backup
python scripts/backup_manager.py restore <latest_backup>

# 4. Notify team
```

#### Data Breach Suspected
```bash
# 1. ISOLATE IMMEDIATELY
sudo ufw deny from any to any port 5432

# 2. Preserve logs
cp /var/log/postgresql/* /secure/incident/logs/

# 3. Notify security team
# 4. Follow incident response plan
```

#### Mass Data Deletion
```bash
# 1. Stop all write operations
# Kill active connections

# 2. Check soft deletes
SELECT COUNT(*) FROM users WHERE is_deleted = true AND deleted_at > NOW() - INTERVAL '1 hour';

# 3. Restore if needed
python scripts/backup_manager.py restore <backup_before_deletion>
```

---

## 📊 Monitoring Dashboards

### Key Metrics to Watch

#### Health Metrics
- Database uptime: Target >99.9%
- Connection success rate: Target >99%
- Query success rate: Target >99.5%

#### Performance Metrics
- Average query time: Target <100ms
- Connection pool usage: Target <80%
- Disk I/O: Monitor trends

#### Capacity Metrics
- Disk usage: Alert at 80%
- Table sizes: Track growth
- Connection count: Track peak usage

---

## 📝 Logging & Auditing

### Log Locations
```bash
# Application logs
tail -f /var/log/database/application.log

# PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log

# Monitoring logs
tail -f /var/log/database/monitoring.log

# Audit logs (in database)
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100;
```

### Important Audit Queries
```sql
-- Failed login attempts
SELECT * FROM audit_logs 
WHERE action = 'user.login' AND success = false 
ORDER BY created_at DESC LIMIT 50;

-- Recent admin actions
SELECT * FROM audit_logs 
WHERE action LIKE 'admin.%' 
ORDER BY created_at DESC LIMIT 100;

-- Data modifications
SELECT * FROM audit_logs 
WHERE action IN ('create', 'update', 'delete') 
ORDER BY created_at DESC LIMIT 100;
```

---

## 🔗 Related Documentation

- **Disaster Recovery:** `docs/DISASTER_RECOVERY.md`
- **Architecture:** `DATABASE_ARCHITECTURE.md`
- **Implementation:** `IMPLEMENTATION_SUMMARY.md`
- **README:** `README.md`

---

## ✅ Operations Checklist

### Daily
- [ ] Morning health check
- [ ] Review overnight activity
- [ ] Verify backups
- [ ] Check disk space
- [ ] Export metrics

### Weekly
- [ ] Run maintenance window
- [ ] Optimize database
- [ ] Cleanup old data
- [ ] Review slow queries
- [ ] Update documentation

### Monthly
- [ ] Full maintenance window
- [ ] Security audit
- [ ] Capacity review
- [ ] DR drill
- [ ] Team training

---

**Document Owner:** Database Operations Team  
**Review Frequency:** Monthly  
**Last Review:** 2024-10-17  
**Next Review:** 2024-11-17

---

**💡 TIP: Bookmark this page for quick access during operations!**
