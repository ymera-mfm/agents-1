"""
Read Replica and Horizontal Scaling Configuration
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import random
import logging
from typing import List, Optional
from enum import Enum
import os

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Database type enumeration"""
    PRIMARY = "primary"
    REPLICA = "replica"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for read replicas"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"


class ReadReplicaManager:
    """Manage read replicas for horizontal scaling"""
    
    def __init__(self, 
                 primary_connection_string: str,
                 replica_connection_strings: List[str],
                 load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        
        self.primary_connection_string = primary_connection_string
        self.replica_connection_strings = replica_connection_strings
        self.strategy = load_balancing_strategy
        
        # Initialize engines
        self.primary_engine = None
        self.replica_engines = []
        self.replica_index = 0
        
        # Track connections for least connections strategy
        self.connection_counts = {}
        
        # Session factories
        self.primary_session_factory = None
        self.replica_session_factories = []
    
    def initialize(self):
        """Initialize primary and replica engines"""
        try:
            # Create primary engine
            self.primary_engine = create_engine(
                self.primary_connection_string,
                pool_size=20,
                max_overflow=40,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False
            )
            
            self.primary_session_factory = sessionmaker(
                bind=self.primary_engine,
                autocommit=False,
                autoflush=False
            )
            
            logger.info("Primary database initialized")
            
            # Create replica engines
            for i, replica_conn_str in enumerate(self.replica_connection_strings):
                replica_engine = create_engine(
                    replica_conn_str,
                    pool_size=30,  # More connections for read replicas
                    max_overflow=60,
                    pool_timeout=30,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    echo=False
                )
                
                replica_session_factory = sessionmaker(
                    bind=replica_engine,
                    autocommit=False,
                    autoflush=False
                )
                
                self.replica_engines.append(replica_engine)
                self.replica_session_factories.append(replica_session_factory)
                self.connection_counts[i] = 0
                
                logger.info(f"Read replica {i+1} initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    def get_write_session(self) -> Session:
        """Get session for write operations (primary only)"""
        if not self.primary_session_factory:
            raise RuntimeError("Database not initialized")
        
        return self.primary_session_factory()
    
    def get_read_session(self) -> Session:
        """Get session for read operations (from replicas)"""
        if not self.replica_session_factories:
            # Fall back to primary if no replicas
            logger.warning("No replicas available, using primary for read")
            return self.get_write_session()
        
        replica_index = self._select_replica()
        session = self.replica_session_factories[replica_index]()
        
        # Track connection for load balancing
        self.connection_counts[replica_index] += 1
        
        # Register cleanup on session close
        @event.listens_for(session, "after_commit")
        @event.listens_for(session, "after_rollback")
        def receive_after_commit_rollback(session):
            self.connection_counts[replica_index] -= 1
        
        return session
    
    def _select_replica(self) -> int:
        """Select replica based on load balancing strategy"""
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select()
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random_select()
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select()
        else:
            return 0
    
    def _round_robin_select(self) -> int:
        """Round-robin replica selection"""
        replica_index = self.replica_index
        self.replica_index = (self.replica_index + 1) % len(self.replica_engines)
        return replica_index
    
    def _random_select(self) -> int:
        """Random replica selection"""
        return random.randint(0, len(self.replica_engines) - 1)
    
    def _least_connections_select(self) -> int:
        """Select replica with least active connections"""
        return min(self.connection_counts.items(), key=lambda x: x[1])[0]
    
    def health_check(self) -> dict:
        """Check health of all database connections"""
        health_status = {
            "primary": self._check_engine_health(self.primary_engine),
            "replicas": []
        }
        
        for i, engine in enumerate(self.replica_engines):
            replica_status = self._check_engine_health(engine)
            replica_status["replica_id"] = i
            replica_status["active_connections"] = self.connection_counts[i]
            health_status["replicas"].append(replica_status)
        
        return health_status
    
    def _check_engine_health(self, engine) -> dict:
        """Check health of a specific engine"""
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            
            pool_status = engine.pool.status()
            
            return {
                "status": "healthy",
                "pool_size": engine.pool.size(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "pool_status": pool_status
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def dispose(self):
        """Dispose all database connections"""
        if self.primary_engine:
            self.primary_engine.dispose()
        
        for engine in self.replica_engines:
            engine.dispose()
        
        logger.info("All database connections disposed")


class DatabaseRouter:
    """Route database operations to primary or replicas"""
    
    def __init__(self, replica_manager: ReadReplicaManager):
        self.replica_manager = replica_manager
    
    def session(self, for_write: bool = False) -> Session:
        """
        Get appropriate database session
        
        Args:
            for_write: If True, returns primary session. If False, returns replica session
        """
        if for_write:
            return self.replica_manager.get_write_session()
        else:
            return self.replica_manager.get_read_session()


class ShardingManager:
    """Manage database sharding for horizontal partitioning"""
    
    def __init__(self, shard_configs: List[dict]):
        """
        Initialize sharding manager
        
        Args:
            shard_configs: List of shard configurations with connection strings
                Example: [
                    {'shard_id': 0, 'connection_string': '...', 'range': (0, 1000)},
                    {'shard_id': 1, 'connection_string': '...', 'range': (1001, 2000)}
                ]
        """
        self.shards = {}
        self.shard_ranges = {}
        
        for config in shard_configs:
            shard_id = config['shard_id']
            engine = create_engine(
                config['connection_string'],
                pool_size=20,
                max_overflow=40,
                pool_pre_ping=True
            )
            
            session_factory = sessionmaker(bind=engine)
            
            self.shards[shard_id] = {
                'engine': engine,
                'session_factory': session_factory,
                'range': config.get('range')
            }
            
            if 'range' in config:
                self.shard_ranges[shard_id] = config['range']
    
    def get_shard_for_key(self, shard_key: int) -> int:
        """Determine which shard a key belongs to"""
        for shard_id, (min_val, max_val) in self.shard_ranges.items():
            if min_val <= shard_key <= max_val:
                return shard_id
        
        # Default to modulo sharding if no range matches
        return shard_key % len(self.shards)
    
    def get_session(self, shard_key: int) -> Session:
        """Get session for a specific shard based on shard key"""
        shard_id = self.get_shard_for_key(shard_key)
        shard = self.shards.get(shard_id)
        
        if not shard:
            raise ValueError(f"No shard found for key {shard_key}")
        
        return shard['session_factory']()
    
    def broadcast_query(self, query_func, *args, **kwargs) -> List:
        """Execute a query across all shards and aggregate results"""
        results = []
        
        for shard_id, shard in self.shards.items():
            session = shard['session_factory']()
            try:
                result = query_func(session, *args, **kwargs)
                results.append({
                    'shard_id': shard_id,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Query failed on shard {shard_id}: {e}")
                results.append({
                    'shard_id': shard_id,
                    'error': str(e)
                })
            finally:
                session.close()
        
        return results
    
    def dispose(self):
        """Dispose all shard connections"""
        for shard in self.shards.values():
            shard['engine'].dispose()


# Example usage configuration
def create_replica_setup():
    """Create read replica setup for production"""
    primary_conn = os.getenv('DATABASE_URL')
    
    # Configure read replicas (these would be actual replica connection strings)
    replica_conns = [
        os.getenv('DATABASE_REPLICA_1_URL', primary_conn),
        os.getenv('DATABASE_REPLICA_2_URL', primary_conn),
    ]
    
    replica_manager = ReadReplicaManager(
        primary_connection_string=primary_conn,
        replica_connection_strings=replica_conns,
        load_balancing_strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
    )
    
    replica_manager.initialize()
    
    return DatabaseRouter(replica_manager)


# Example usage
"""
# Initialize
router = create_replica_setup()

# For read operations (uses replicas)
with router.session(for_write=False) as session:
    users = session.query(User).all()

# For write operations (uses primary)
with router.session(for_write=True) as session:
    new_user = User(name="John")
    session.add(new_user)
    session.commit()
"""