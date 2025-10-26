# Multi-Level Caching Strategy
class MultiLevelCache:
    def __init__(self):
        self.l1_cache = {}  # In-memory cache (thread-safe)
        self.l1_lock = asyncio.Lock()
        self.redis_client = None
        self.init_redis()
    
    def init_redis(self):
        """Initialize Redis client"""
        try:
            import redis
            self.redis_client = redis.Redis.from_url(
                os.getenv('REDIS_URL', 'redis://localhost:6379'),
                decode_responses=True
            )
            self.redis_client.ping()  # Test connection
        except (ImportError, redis.ConnectionError):
            logger.warning("Redis not available, using in-memory cache only")
            self.redis_client = None
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from multi-level cache"""
        # L1: In-memory cache
        async with self.l1_lock:
            if key in self.l1_cache:
                item = self.l1_cache[key]
                if item["expires_at"] > datetime.utcnow():
                    MetricsCollector.record_cache_hit('l1')
                    return item["value"]
                else:
                    # Remove expired item
                    del self.l1_cache[key]
        
        # L2: Redis cache
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    # Deserialize if needed
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass  # Keep as string
                    
                    # Store in L1 cache
                    async with self.l1_lock:
                        self.l1_cache[key] = {
                            "value": value,
                            "expires_at": datetime.utcnow() + timedelta(seconds=60)  # Short TTL for L1
                        }
                    
                    MetricsCollector.record_cache_hit('l2')
                    return value
            except Exception as e:
                logger.error(f"Redis cache error: {e}")
        
        # L3: Database (caller should handle this)
        MetricsCollector.record_cache_miss('all')
        return default
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in multi-level cache"""
        # Serialize if needed
        if not isinstance(value, (str, bytes)):
            try:
                value = json.dumps(value)
            except (TypeError, ValueError):
                pass  # Keep as is if not serializable
        
        # L1: In-memory cache
        async with self.l1_lock:
            self.l1_cache[key] = {
                "value": value,
                "expires_at": datetime.utcnow() + timedelta(seconds=min(60, ttl))  # Cap L1 TTL
            }
        
        # L2: Redis cache
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, value)
            except Exception as e:
                logger.error(f"Failed to set Redis cache: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete key from all cache levels"""
        # L1: In-memory cache
        async with self.l1_lock:
            if key in self.l1_cache:
                del self.l1_cache[key]
        
        # L2: Redis cache
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Failed to delete from Redis: {e}")
    
    async def clear(self) -> None:
        """Clear all cache levels"""
        # L1: In-memory cache
        async with self.l1_lock:
            self.l1_cache.clear()
        
        # L2: Redis cache
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.error(f"Failed to clear Redis: {e}")

# Database Optimization with Read Replicas and Sharding
class OptimizedDatabaseUtils:
    def __init__(self):
        self.primary_engine = None
        self.replica_engines = []
        self.session_factories = {}
        self.init_engines()
    
    def init_engines(self):
        """Initialize database engines with read replicas"""
        # Primary database (writes)
        self.primary_engine = create_async_engine(
            os.getenv('DATABASE_PRIMARY_URL', os.getenv('DATABASE_URL')),
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        
        # Read replicas
        replica_urls = os.getenv('DATABASE_REPLICA_URLS', '').split(',')
        for i, replica_url in enumerate(replica_urls):
            if replica_url.strip():
                engine = create_async_engine(
                    replica_url.strip(),
                    pool_size=15,
                    max_overflow=5,
                    pool_timeout=30,
                    pool_recycle=1800,
                    pool_pre_ping=True
                )
                self.replica_engines.append(engine)
        
        # Session factories
        self.session_factories['primary'] = async_sessionmaker(
            self.primary_engine, expire_on_commit=False
        )
        
        for i, engine in enumerate(self.replica_engines):
            self.session_factories[f'replica_{i}'] = async_sessionmaker(
                engine, expire_on_commit=False
            )
    
    def get_session_factory(self, for_write: bool = False) -> async_sessionmaker:
        """Get appropriate session factory"""
        if for_write or not self.replica_engines:
            return self.session_factories['primary']
        else:
            # Round-robin load balancing for reads
            replica_id = hash(str(asyncio.current_task())) % len(self.replica_engines)
            return self.session_factories[f'replica_{replica_id}']
    
    @asynccontextmanager
    async def get_session(self, for_write: bool = False):
        """Get database session with read/write routing"""
        session_factory = self.get_session_factory(for_write)
        session = session_factory()
        
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    # Sharding implementation
    def get_shard_for_entity(self, entity_id: UUID, total_shards: int = 4) -> int:
        """Determine which shard an entity belongs to"""
        return hash(str(entity_id)) % total_shards
    
    async def get_sharded_session(self, entity_id: UUID, for_write: bool = False):
        """Get session for specific shard"""
        shard_id = self.get_shard_for_entity(entity_id)
        shard_url = os.getenv(f'DATABASE_SHARD_{shard_id}_URL')
        
        if not shard_url:
            # Fallback to primary if shard not configured
            return self.get_session(for_write)
        
        # Create engine for shard if not exists
        if f'shard_{shard_id}' not in self.session_factories:
            engine = create_async_engine(
                shard_url,
                pool_size=10,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True
            )
            self.session_factories[f'shard_{shard_id}'] = async_sessionmaker(
                engine, expire_on_commit=False
            )
        
        session = self.session_factories[f'shard_{shard_id}']()
        return session

# Materialized Views for Analytics
class MaterializedViewManager:
    def __init__(self):
        self.db = DatabaseUtils()
        self.refresh_intervals = {
            'project_stats_hourly': 3600,
            'user_activity_daily': 86400,
            'system_metrics_5min': 300
        }
        self.refresh_tasks = {}
    
    async def create_materialized_views(self):
        """Create materialized views for analytics"""
        views = {
            'project_stats_hourly': """
                CREATE MATERIALIZED VIEW IF NOT EXISTS project_stats_hourly AS
                SELECT 
                    project_id,
                    COUNT(*) as total_tasks,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
                    AVG(execution_time) as avg_execution_time,
                    date_trunc('hour', created_at) as time_bucket
                FROM tasks
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY project_id, time_bucket
            """,
            'user_activity_daily': """
                CREATE MATERIALIZED VIEW IF NOT EXISTS user_activity_daily AS
                SELECT 
                    user_id,
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT action) as unique_actions,
                    date_trunc('day', timestamp) as date
                FROM audit_logs
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY user_id, date
            """
        }
        
        async with self.db.get_session() as session:
            for view_name, view_sql in views.items():
                await session.execute(text(view_sql))
            await session.commit()
    
    async def refresh_materialized_views(self):
        """Refresh materialized views on schedule"""
        for view_name, interval in self.refresh_intervals.items():
            self.refresh_tasks[view_name] = asyncio.create_task(
                self._refresh_view_periodically(view_name, interval)
            )
    
    async def _refresh_view_periodically(self, view_name: str, interval: int):
        """Refresh a materialized view periodically"""
        while True:
            try:
                async with self.db.get_session() as session:
                    await session.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                    await session.commit()
                    logger.info(f"Refreshed materialized view: {view_name}")
            except Exception as e:
                logger.error(f"Failed to refresh view {view_name}: {e}")
            
            await asyncio.sleep(interval)
    
    async def get_view_data(self, view_name: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get data from materialized view"""
        async with self.db.get_session() as session:
            # Validate view_name against allowed list to prevent SQL injection
            allowed_views = ['task_summary', 'agent_summary', 'performance_metrics']  # Add all valid view names
            if view_name not in allowed_views:
                raise ValueError(f"Invalid view name: {view_name}")
            
            query = f"SELECT * FROM {view_name}"  # Safe now after validation
            params = {}
            
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    where_clauses.append(f"{key} = :{key}")
                    params[key] = value
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            return [dict(row) for row in rows]

# Connection Pooling with Failover
class ConnectionPoolManager:
    def __init__(self):
        self.primary_pool = None
        self.replica_pools = []
        self.health_check_task = None
        self.init_pools()
    
    def init_pools(self):
        """Initialize connection pools"""
        # Primary pool
        self.primary_pool = self._create_pool(
            os.getenv('DATABASE_PRIMARY_URL', os.getenv('DATABASE_URL'))
        )
        
        # Replica pools
        replica_urls = os.getenv('DATABASE_REPLICA_URLS', '').split(',')
        for replica_url in replica_urls:
            if replica_url.strip():
                pool = self._create_pool(replica_url.strip())
                self.replica_pools.append({
                    'pool': pool,
                    'healthy': True,
                    'last_check': datetime.utcnow()
                })
        
        # Start health checks
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    def _create_pool(self, database_url: str):
        """Create a database connection pool"""
        return asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            max_queries=10000,
            max_inactive_connection_lifetime=300,
            timeout=30
        )
    
    async def get_connection(self, for_write: bool = False):
        """Get database connection with failover"""
        if for_write or not self.replica_pools:
            return await self.primary_pool.acquire()
        
        # Try healthy replicas in round-robin
        healthy_replicas = [r for r in self.replica_pools if r['healthy']]
        if not healthy_replicas:
            # Fallback to primary if no replicas are healthy
            return await self.primary_pool.acquire()
        
        replica = healthy_replicas[hash(str(asyncio.current_task())) % len(healthy_replicas)]
        return await replica['pool'].acquire()
    
    async def _health_check_loop(self):
        """Periodically check database health"""
        while True:
            try:
                for replica in self.replica_pools:
                    try:
                        async with replica['pool'].acquire() as conn:
                            await conn.execute("SELECT 1")
                        replica['healthy'] = True
                    except Exception as e:
                        replica['healthy'] = False
                        logger.warning(f"Replica database unhealthy: {e}")
                
                # Check primary
                try:
                    async with self.primary_pool.acquire() as conn:
                        await conn.execute("SELECT 1")
                except Exception as e:
                    logger.error(f"Primary database unhealthy: {e}")
                    # Implement failover logic here
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def close(self):
        """Close all connection pools"""
        if self.health_check_task:
            self.health_check_task.cancel()
        
        await self.primary_pool.close()
        for replica in self.replica_pools:
            await replica['pool'].close()