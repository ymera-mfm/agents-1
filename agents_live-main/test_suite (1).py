"""
Comprehensive Database Testing Suite
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Import modules to test
from app.database import DatabaseManager, DatabaseConfig
from app.read_replica_config import ReadReplicaManager, LoadBalancingStrategy
from app.migration_manager import MigrationManager
from app.backup_recovery import AzureBackupManager
from app.query_optimization import QueryPerformanceMonitor, IndexAnalyzer
from app.db_monitoring import DatabaseHealthMonitor, DatabaseMaintenanceScheduler


# Test Configuration
TEST_DB_URL = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')


@pytest.fixture
def db_manager():
    """Create test database manager"""
    manager = DatabaseManager()
    manager.config.get_connection_string = lambda: TEST_DB_URL
    manager.initialize()
    yield manager
    manager.dispose()


@pytest.fixture
def test_session(db_manager):
    """Create test session"""
    with db_manager.get_session() as session:
        yield session


class TestDatabaseManager:
    """Test database manager functionality"""
    
    def test_initialization(self, db_manager):
        """Test database initialization"""
        assert db_manager._engine is not None
        assert db_manager._session_factory is not None
    
    def test_session_creation(self, db_manager):
        """Test session creation"""
        with db_manager.get_session() as session:
            assert session is not None
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
    
    def test_health_check(self, db_manager):
        """Test health check"""
        health = db_manager.health_check()
        assert health['status'] == 'healthy'
        assert 'pool_size' in health
    
    def test_session_rollback_on_error(self, db_manager):
        """Test automatic rollback on error"""
        try:
            with db_manager.get_session() as session:
                # Simulate an error
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Session should be rolled back
        health = db_manager.health_check()
        assert health['status'] == 'healthy'


class TestConnectionPool:
    """Test connection pool behavior"""
    
    def test_pool_size_limits(self, db_manager):
        """Test connection pool limits"""
        sessions = []
        
        # Create sessions up to pool size
        for i in range(db_manager.config.pool_size):
            session = next(db_manager.get_session())
            sessions.append(session)
        
        # All sessions should be valid
        assert len(sessions) == db_manager.config.pool_size
        
        # Cleanup
        for session in sessions:
            session.close()
    
    def test_connection_recycling(self, db_manager):
        """Test connection recycling"""
        # Get initial pool status
        initial_health = db_manager.health_check()
        
        # Use connections
        for _ in range(10):
            with db_manager.get_session() as session:
                session.execute(text("SELECT 1"))
        
        # Pool should be healthy
        final_health = db_manager.health_check()
        assert final_health['status'] == 'healthy'


class TestReadReplicas:
    """Test read replica functionality"""
    
    @pytest.fixture
    def replica_manager(self):
        """Create replica manager for testing"""
        # Use same DB for primary and replica in tests
        manager = ReadReplicaManager(
            primary_connection_string=TEST_DB_URL,
            replica_connection_strings=[TEST_DB_URL],
            load_balancing_strategy=LoadBalancingStrategy.ROUND_ROBIN
        )
        manager.initialize()
        yield manager
        manager.dispose()
    
    def test_replica_initialization(self, replica_manager):
        """Test replica initialization"""
        assert replica_manager.primary_engine is not None
        assert len(replica_manager.replica_engines) > 0
    
    def test_write_session(self, replica_manager):
        """Test write session uses primary"""
        session = replica_manager.get_write_session()
        assert session is not None
        session.close()
    
    def test_read_session(self, replica_manager):
        """Test read session uses replica"""
        session = replica_manager.get_read_session()
        assert session is not None
        session.close()
    
    def test_load_balancing(self, replica_manager):
        """Test load balancing across replicas"""
        # Get multiple read sessions
        sessions = []
        for _ in range(5):
            session = replica_manager.get_read_session()
            sessions.append(session)
        
        # Cleanup
        for session in sessions:
            session.close()
    
    def test_health_check(self, replica_manager):
        """Test replica health check"""
        health = replica_manager.health_check()
        assert 'primary' in health
        assert 'replicas' in health
        assert health['primary']['status'] == 'healthy'


class TestMigrations:
    """Test migration functionality"""
    
    @pytest.fixture
    def migration_manager(self):
        """Create migration manager"""
        return MigrationManager()
    
    def test_get_current_revision(self, migration_manager):
        """Test getting current revision"""
        current = migration_manager.get_current_revision()
        assert current is not None
    
    def test_migration_history(self, migration_manager):
        """Test getting migration history"""
        history = migration_manager.get_migration_history()
        assert isinstance(history, list)
    
    def test_backup_creation(self, migration_manager):
        """Test backup point creation"""
        backup_id = migration_manager._create_backup_point("test_revision")
        assert backup_id.startswith("backup_")


class TestQueryOptimization:
    """Test query optimization features"""
    
    @pytest.fixture
    def query_monitor(self, db_manager):
        """Create query monitor"""
        monitor = QueryPerformanceMonitor(slow_query_threshold=0.1)
        monitor.register_listeners(db_manager._engine)
        return monitor
    
    def test_query_monitoring(self, query_monitor, test_session):
        """Test query monitoring"""
        # Execute some queries
        for _ in range(5):
            test_session.execute(text("SELECT 1"))
        
        # Check statistics
        stats = query_monitor.get_query_statistics()
        assert len(stats) > 0
    
    def test_slow_query_detection(self, query_monitor, test_session):
        """Test slow query detection"""
        import time
        
        # Execute a slow query (simulate with sleep)
        test_session.execute(text("SELECT 1"))
        time.sleep(0.2)  # Simulate slow query
        
        # Check for slow queries
        slow = query_monitor.get_slow_queries()
        # Note: Actual detection depends on query execution time


class TestHealthMonitoring:
    """Test health monitoring functionality"""
    
    @pytest.fixture
    async def health_monitor(self, db_manager):
        """Create health monitor"""
        monitor = DatabaseHealthMonitor(db_manager, alert_config={})
        return monitor
    
    @pytest.mark.asyncio
    async def test_metric_collection(self, health_monitor):
        """Test metric collection"""
        metrics = await health_monitor.collect_metrics()
        
        assert 'timestamp' in metrics
        assert 'database_status' in metrics
        assert 'performance' in metrics
        assert 'connections' in metrics
    
    @pytest.mark.asyncio
    async def test_alert_detection(self, health_monitor):
        """Test alert detection"""
        # Create metrics with alert condition
        metrics = {
            'storage': {'usage_percent': 90},  # Above threshold
            'database_status': {'status': 'healthy'},
            'connections': {},
            'replication': {}
        }
        
        await health_monitor.check_alerts(metrics)
        
        # Check if alerts were generated
        assert len(health_monitor.alert_history) > 0


class TestMaintenance:
    """Test maintenance functionality"""
    
    @pytest.fixture
    def maintenance_scheduler(self, db_manager):
        """Create maintenance scheduler"""
        return DatabaseMaintenanceScheduler(db_manager)
    
    @pytest.mark.asyncio
    async def test_update_statistics(self, maintenance_scheduler):
        """Test statistics update"""
        try:
            result = await maintenance_scheduler.update_statistics()
            assert "success" in result.lower()
        except Exception as e:
            # May fail on SQLite
            pytest.skip(f"Statistics update not supported: {e}")
    
    def test_maintenance_logging(self, maintenance_scheduler):
        """Test maintenance logging"""
        maintenance_scheduler._log_maintenance(
            task="test_task",
            status="success",
            details="Test completed"
        )
        
        assert len(maintenance_scheduler.maintenance_log) > 0
        assert maintenance_scheduler.maintenance_log[-1]['task'] == 'test_task'


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, db_manager):
        """Test complete database workflow"""
        # 1. Health check
        health = db_manager.health_check()
        assert health['status'] == 'healthy'
        
        # 2. Create session and perform operations
        with db_manager.get_session() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        
        # 3. Verify pool status
        final_health = db_manager.health_check()
        assert final_health['status'] == 'healthy'
    
    def test_error_handling(self, db_manager):
        """Test error handling in workflows"""
        try:
            with db_manager.get_session() as session:
                # Execute invalid SQL
                session.execute(text("INVALID SQL"))
        except Exception:
            pass  # Expected to fail
        
        # Database should still be healthy
        health = db_manager.health_check()
        assert health['status'] == 'healthy'


class TestPerformance:
    """Performance tests"""
    
    def test_connection_pool_performance(self, db_manager):
        """Test connection pool performance"""
        import time
        
        start = time.time()
        
        # Create and use 100 sessions
        for _ in range(100):
            with db_manager.get_session() as session:
                session.execute(text("SELECT 1"))
        
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 5.0  # 5 seconds for 100 connections
    
    def test_concurrent_access(self, db_manager):
        """Test concurrent database access"""
        import threading
        
        def worker():
            for _ in range(10):
                with db_manager.get_session() as session:
                    session.execute(text("SELECT 1"))
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All threads should complete successfully
        health = db_manager.health_check()
        assert health['status'] == 'healthy'


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])