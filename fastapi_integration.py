"""
Complete FastAPI Integration with Production Database Setup
"""
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List

# Import our modules
from app.database import (
    init_db, close_db, db_manager, get_db
)
from app.read_replica_config import (
    ReadReplicaManager, DatabaseRouter, LoadBalancingStrategy
)
from app.query_optimization import (
    QueryPerformanceMonitor, IndexAnalyzer, QueryOptimizer
)
from app.db_monitoring import (
    DatabaseHealthMonitor, DatabaseMaintenanceScheduler
)
from app.backup_recovery import (
    AzureBackupManager, DisasterRecoveryManager
)
from app.migration_manager import MigrationManager
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
replica_manager: ReadReplicaManager = None
database_router: DatabaseRouter = None
query_monitor: QueryPerformanceMonitor = None
health_monitor: DatabaseHealthMonitor = None
backup_manager: AzureBackupManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting YMERA application...")
    
    try:
        # Initialize database
        init_db()
        logger.info("✓ Database initialized")
        
        # Setup read replicas if configured
        if os.getenv('DATABASE_REPLICA_1_URL'):
            await setup_read_replicas()
            logger.info("✓ Read replicas configured")
        
        # Initialize query monitoring
        setup_query_monitoring()
        logger.info("✓ Query monitoring enabled")
        
        # Initialize health monitoring
        await setup_health_monitoring()
        logger.info("✓ Health monitoring started")
        
        # Initialize backup manager
        setup_backup_manager()
        logger.info("✓ Backup manager initialized")
        
        logger.info("✅ Application startup complete")
        
        yield
        
    finally:
        # Shutdown
        logger.info("🛑 Shutting down application...")
        
        if replica_manager:
            replica_manager.dispose()
        
        close_db()
        logger.info("✅ Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="YMERA API",
    description="Production-ready API with comprehensive database management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Setup functions
async def setup_read_replicas():
    """Setup read replica configuration"""
    global replica_manager, database_router
    
    primary_conn = os.getenv('DATABASE_URL')
    replica_conns = [
        os.getenv('DATABASE_REPLICA_1_URL'),
        os.getenv('DATABASE_REPLICA_2_URL'),
    ]
    
    # Filter out None values
    replica_conns = [r for r in replica_conns if r]
    
    if replica_conns:
        replica_manager = ReadReplicaManager(
            primary_connection_string=primary_conn,
            replica_connection_strings=replica_conns,
            load_balancing_strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
        )
        
        replica_manager.initialize()
        database_router = DatabaseRouter(replica_manager)


def setup_query_monitoring():
    """Setup query performance monitoring"""
    global query_monitor
    
    slow_query_threshold = float(os.getenv('SLOW_QUERY_THRESHOLD', '1.0'))
    query_monitor = QueryPerformanceMonitor(slow_query_threshold=slow_query_threshold)
    query_monitor.register_listeners(db_manager._engine)


async def setup_health_monitoring():
    """Setup health monitoring with alerts"""
    global health_monitor
    
    alert_config = {
        'email_enabled': os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true',
        'smtp': {
            'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD')
        },
        'alert_recipients': os.getenv('ALERT_RECIPIENTS', '').split(','),
        'webhook_url': os.getenv('ALERT_WEBHOOK_URL')
    }
    
    health_monitor = DatabaseHealthMonitor(
        db_manager=db_manager,
        alert_config=alert_config
    )
    
    # Start monitoring in background
    asyncio.create_task(
        health_monitor.monitor_continuously(interval_seconds=60)
    )


def setup_backup_manager():
    """Setup backup manager"""
    global backup_manager
    
    if os.getenv('AZURE_SUBSCRIPTION_ID'):
        backup_manager = AzureBackupManager()


# Dependency for database sessions
def get_database_session(for_write: bool = False):
    """Get database session (with read replica support)"""
    if database_router:
        session = database_router.session(for_write=for_write)
    else:
        session = next(get_db())
    
    try:
        yield session
    finally:
        session.close()


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "YMERA API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Basic health check"""
    try:
        health = db_manager.health_check()
        return {
            "status": "healthy" if health["status"] == "healthy" else "degraded",
            "database": health,
            "timestamp": health_monitor.metrics_history[-1]['timestamp'] if health_monitor.metrics_history else None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/health/database")
async def database_health():
    """Detailed database health metrics"""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitoring not initialized")
    
    try:
        metrics = await health_monitor.collect_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/summary")
async def health_summary(hours: int = 24):
    """Get health metrics summary"""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitoring not initialized")
    
    summary = health_monitor.get_metrics_summary(hours=hours)
    return summary


@app.get("/health/replicas")
async def replica_health():
    """Check health of all replicas"""
    if not replica_manager:
        return {"message": "Read replicas not configured"}
    
    health_status = replica_manager.health_check()
    return health_status


@app.get("/performance/queries")
async def query_performance():
    """Get query performance statistics"""
    if not query_monitor:
        raise HTTPException(status_code=503, detail="Query monitoring not initialized")
    
    stats = query_monitor.get_query_statistics()
    return {
        "total_queries": len(stats),
        "top_10_slowest": stats[:10]
    }


@app.get("/performance/slow-queries")
async def slow_queries(limit: int = 50):
    """Get recent slow queries"""
    if not query_monitor:
        raise HTTPException(status_code=503, detail="Query monitoring not initialized")
    
    slow = query_monitor.get_slow_queries(limit=limit)
    return {
        "count": len(slow),
        "queries": slow
    }


@app.get("/optimization/missing-indexes")
async def missing_indexes(db: Session = Depends(get_db)):
    """Get missing index recommendations"""
    try:
        analyzer = IndexAnalyzer(db)
        missing = analyzer.find_missing_indexes()
        return {
            "count": len(missing),
            "recommendations": missing[:20]  # Top 20
        }
    except Exception as e:
        logger.error(f"Failed to analyze indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/optimization/unused-indexes")
async def unused_indexes(days: int = 30, db: Session = Depends(get_db)):
    """Get unused index recommendations"""
    try:
        analyzer = IndexAnalyzer(db)
        unused = analyzer.find_unused_indexes(days_threshold=days)
        return {
            "count": len(unused),
            "recommendations": unused
        }
    except Exception as e:
        logger.error(f"Failed to analyze indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/optimization/index-usage")
async def index_usage(db: Session = Depends(get_db)):
    """Get index usage statistics"""
    try:
        analyzer = IndexAnalyzer(db)
        usage = analyzer.analyze_index_usage()
        return {
            "count": len(usage),
            "indexes": usage
        }
    except Exception as e:
        logger.error(f"Failed to get index usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/run")
async def run_maintenance(background_tasks: BackgroundTasks):
    """Run database maintenance tasks"""
    scheduler = DatabaseMaintenanceScheduler(db_manager)
    background_tasks.add_task(scheduler.run_maintenance)
    
    return {
        "message": "Maintenance tasks scheduled",
        "tasks": [
            "update_statistics",
            "rebuild_indexes",
            "clean_backups",
            "analyze_queries"
        ]
    }


@app.post("/maintenance/update-statistics")
async def update_statistics(background_tasks: BackgroundTasks):
    """Update database statistics"""
    scheduler = DatabaseMaintenanceScheduler(db_manager)
    background_tasks.add_task(scheduler.update_statistics)
    
    return {"message": "Statistics update scheduled"}


@app.post("/maintenance/rebuild-indexes")
async def rebuild_indexes(background_tasks: BackgroundTasks):
    """Rebuild fragmented indexes"""
    scheduler = DatabaseMaintenanceScheduler(db_manager)
    background_tasks.add_task(scheduler.rebuild_fragmented_indexes)
    
    return {"message": "Index rebuild scheduled"}


@app.get("/backups/list")
async def list_backups():
    """List available backups"""
    if not backup_manager:
        raise HTTPException(status_code=503, detail="Backup manager not initialized")
    
    try:
        backups = backup_manager.list_long_term_backups()
        return {
            "count": len(backups),
            "backups": backups
        }
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backups/retention-policy")
async def get_retention_policy():
    """Get backup retention policy"""
    if not backup_manager:
        raise HTTPException(status_code=503, detail="Backup manager not initialized")
    
    try:
        policy = backup_manager.get_retention_policy()
        return policy
    except Exception as e:
        logger.error(f"Failed to get retention policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/backups/create")
async def create_backup(backup_name: str = None, background_tasks: BackgroundTasks = None):
    """Create manual backup"""
    if not backup_manager:
        raise HTTPException(status_code=503, detail="Backup manager not initialized")
    
    try:
        result = backup_manager.create_manual_backup(backup_name=backup_name)
        return result
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/migrations/upgrade")
async def upgrade_database(revision: str = "head"):
    """Run database migrations"""
    try:
        migration_manager = MigrationManager()
        
        # Test migration first
        test_success = migration_manager.test_migration_upgrade(revision)
        if not test_success:
            raise HTTPException(
                status_code=400, 
                detail="Migration test failed. Check logs for details."
            )
        
        # Run upgrade with backup
        success = migration_manager.upgrade(revision, backup=True)
        
        if success:
            return {
                "message": "Migration completed successfully",
                "revision": migration_manager.get_current_revision()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Migration failed. Database rolled back."
            )
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/migrations/current")
async def current_migration():
    """Get current migration revision"""
    try:
        migration_manager = MigrationManager()
        current = migration_manager.get_current_revision()
        return {
            "current_revision": current
        }
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/migrations/history")
async def migration_history():
    """Get migration history"""
    try:
        migration_manager = MigrationManager()
        history = migration_manager.get_migration_history()
        return {
            "count": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Failed to get migration history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/migrations/rollback")
async def rollback_migration(steps: int = 1):
    """Rollback database migration"""
    try:
        migration_manager = MigrationManager()
        revision = f"-{steps}"
        
        success = migration_manager.downgrade(revision, backup=True)
        
        if success:
            return {
                "message": f"Rolled back {steps} migration(s)",
                "current_revision": migration_manager.get_current_revision()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Rollback failed"
            )
            
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Example CRUD endpoints using read replicas

@app.get("/users")
async def list_users(skip: int = 0, limit: int = 100):
    """List users (uses read replica)"""
    # Use read replica for queries
    session = database_router.session(for_write=False) if database_router else next(get_db())
    
    try:
        # Your actual query here
        # users = session.query(User).offset(skip).limit(limit).all()
        return {
            "message": "Users retrieved from read replica",
            "count": 0,  # Replace with actual count
            "data": []
        }
    finally:
        session.close()


@app.post("/users")
async def create_user(user_data: Dict):
    """Create user (uses primary database)"""
    # Use primary for writes
    session = database_router.session(for_write=True) if database_router else next(get_db())
    
    try:
        # Your actual creation logic here
        # new_user = User(**user_data)
        # session.add(new_user)
        # session.commit()
        
        return {
            "message": "User created",
            "data": user_data
        }
    finally:
        session.close()


# Admin endpoints (require authentication in production)

@app.get("/admin/pool-status")
async def pool_status():
    """Get connection pool status"""
    health = db_manager.health_check()
    return {
        "primary": health,
        "replicas": replica_manager.health_check() if replica_manager else None
    }


@app.post("/admin/clear-query-stats")
async def clear_query_stats():
    """Clear query performance statistics"""
    if query_monitor:
        query_monitor.clear_statistics()
        return {"message": "Query statistics cleared"}
    return {"message": "Query monitoring not enabled"}


@app.get("/admin/alerts")
async def get_alerts(hours: int = 24):
    """Get recent alerts"""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitoring not initialized")
    
    cutoff = health_monitor.metrics_history[0]['timestamp'] if health_monitor.metrics_history else None
    recent_alerts = [
        alert for alert in health_monitor.alert_history[-100:]
    ]
    
    return {
        "count": len(recent_alerts),
        "alerts": recent_alerts
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )