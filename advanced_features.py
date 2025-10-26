# advanced_features.py - Enterprise features module
"""
Enterprise features for production agent management system
Includes: WebSocket support, caching, monitoring, security enhancements
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List, Set, Optional
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis.asyncio as aioredis
from prometheus_client import Counter, Histogram, Gauge
import hashlib
import hmac
from functools import wraps

logger = logging.getLogger(__name__)

# Enhanced Prometheus Metrics
WEBSOCKET_CONNECTIONS = Gauge('websocket_connections_active', 'Active WebSocket connections')
WEBSOCKET_MESSAGES = Counter('websocket_messages_total', 'Total WebSocket messages', ['type'])
CACHE_OPERATIONS = Counter('cache_operations_total', 'Cache operations', ['operation', 'result'])
SECURITY_EVENTS = Counter('security_events_total', 'Security events', ['event_type'])

# =============================================================================
# WEBSOCKET CONNECTION MANAGER
# =============================================================================

class ConnectionManager:
    """Manage WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.user_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            self.user_connections[user_id] = set()
        
        self.active_connections[user_id][connection_id] = websocket
        self.user_connections[user_id].add(connection_id)
        
        WEBSOCKET_CONNECTIONS.inc()
        logger.info(f"WebSocket connected: user={user_id}, connection={connection_id}")
    
    def disconnect(self, user_id: str, connection_id: str):
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]
                self.user_connections[user_id].discard(connection_id)
                
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    del self.user_connections[user_id]
                
                WEBSOCKET_CONNECTIONS.dec()
                logger.info(f"WebSocket disconnected: user={user_id}, connection={connection_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a user"""
        if user_id in self.active_connections:
            disconnected = []
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_text(json.dumps(message))
                    WEBSOCKET_MESSAGES.labels(type="sent").inc()
                except:
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected:
                self.disconnect(user_id, connection_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)

# Global connection manager
connection_manager = ConnectionManager()

# =============================================================================
# INTELLIGENT CACHING SYSTEM
# =============================================================================

class CacheManager:
    """Intelligent multi-level caching with TTL and invalidation"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.local_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0}
    
    async def get(self, key: str, default=None):
        """Get from cache with fallback"""
        try:
            # Try local cache first (L1)
            if key in self.local_cache:
                entry = self.local_cache[key]
                if entry["expires"] > datetime.utcnow():
                    self.cache_stats["hits"] += 1
                    CACHE_OPERATIONS.labels(operation="get", result="hit").inc()
                    return entry["value"]
                else:
                    del self.local_cache[key]
            
            # Try Redis cache (L2)
            value = await self.redis.get(key)
            if value:
                self.cache_stats["hits"] += 1
                CACHE_OPERATIONS.labels(operation="get", result="hit").inc()
                return json.loads(value)
            
            self.cache_stats["misses"] += 1
            CACHE_OPERATIONS.labels(operation="get", result="miss").inc()
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    async def set(self, key: str, value, ttl: int = 300):
        """Set cache with TTL"""
        try:
            # Set in local cache (L1)
            self.local_cache[key] = {
                "value": value,
                "expires": datetime.utcnow() + timedelta(seconds=min(ttl, 60))  # Max 1min local
            }
            
            # Set in Redis cache (L2)
            await self.redis.setex(key, ttl, json.dumps(value, default=str))
            
            self.cache_stats["sets"] += 1
            CACHE_OPERATIONS.labels(operation="set", result="success").inc()
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            CACHE_OPERATIONS.labels(operation="set", result="error").inc()
    
    async def delete(self, key: str):
        """Delete from all cache levels"""
        try:
            if key in self.local_cache:
                del self.local_cache[key]
            await self.redis.delete(key)
            CACHE_OPERATIONS.labels(operation="delete", result="success").inc()
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        try:
            # Clear local cache matching pattern
            keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.local_cache[key]
            
            # Clear Redis cache matching pattern
            cursor = '0'
            while cursor != 0:
                cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

# =============================================================================
# ENHANCED SECURITY MIDDLEWARE
# =============================================================================

class SecurityManager:
    """Enhanced security features"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.rate_limits = {}
        self.failed_attempts = {}
    
    async def rate_limit(self, identifier: str, limit: int = 100, window: int = 3600) -> bool:
        """Rate limiting with sliding window"""
        try:
            current_time = datetime.utcnow().timestamp()
            key = f"rate_limit:{identifier}"
            
            # Remove expired entries
            await self.redis.zremrangebyscore(key, 0, current_time - window)
            
            # Count current requests
            count = await self.redis.zcard(key)
            
            if count >= limit:
                SECURITY_EVENTS.labels(event_type="rate_limit_exceeded").inc()
                return False
            
            # Add current request
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, window)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Fail open
    
    async def check_api_key(self, api_key: str, expected_hash: str) -> bool:
        """Secure API key validation"""
        try:
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(
                hashlib.sha256(api_key.encode()).hexdigest(),
                expected_hash
            )
        except Exception:
            return False
    
    async def log_security_event(self, event_type: str, details: dict, user_id: str = None):
        """Log security events for monitoring"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "user_id": user_id
        }
        
        # Log to Redis stream for real-time monitoring
        await self.redis.xadd("security_events", event)
        
        # Update metrics
        SECURITY_EVENTS.labels(event_type=event_type).inc()
        
        logger.warning(f"Security event: {event_type} - {details}")

# =============================================================================
# INTELLIGENT TASK SCHEDULER
# =============================================================================

class TaskScheduler:
    """Intelligent task scheduling with priority and resource management"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.running_tasks = {}
        self.max_concurrent_tasks = 10
    
    async def schedule_task(self, task_data: dict, priority: int = 1, delay: int = 0):
        """Schedule task with priority and optional delay"""
        score = datetime.utcnow().timestamp() + delay + (100 - priority)  # Higher priority = lower score
        
        queue_name = f"task_queue:{task_data.get('task_type', 'default')}"
        await self.redis.zadd(queue_name, {json.dumps(task_data): score})
    
    async def get_next_task(self, task_types: List[str] = None) -> Optional[dict]:
        """Get next task to process based on priority and timing"""
        current_time = datetime.utcnow().timestamp()
        
        # Default to all task types if none specified
        if not task_types:
            task_types = await self._get_all_task_types()
        
        for task_type in task_types:
            queue_name = f"task_queue:{task_type}"
            
            # Get tasks that are due to run
            tasks = await self.redis.zrangebyscore(queue_name, 0, current_time, start=0, num=1)
            
            if tasks:
                # Remove from queue and return
                task_data = json.loads(tasks[0])
                await self.redis.zrem(queue_name, tasks[0])
                return task_data
        
        return None
    
    async def _get_all_task_types(self) -> List[str]:
        """Get all available task types from queue keys"""
        keys = await self.redis.keys("task_queue:*")
        return [key.decode().split(":")[-1] for key in keys]

# =============================================================================
# HEALTH MONITORING SYSTEM
# =============================================================================

class HealthMonitor:
    """Comprehensive health monitoring"""
    
    def __init__(self, db_session_factory, redis_client: aioredis.Redis):
        self.db_session_factory = db_session_factory
        self.redis = redis_client
        self.health_status = {"status": "healthy", "last_check": datetime.utcnow()}
    
    async def check_system_health(self) -> dict:
        """Perform comprehensive health check"""
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {},
            "metrics": {}
        }
        
        # Database health
        try:
            async with self.db_session_factory() as session:
                await session.execute("SELECT 1")
            health_data["components"]["database"] = "healthy"
        except Exception as e:
            health_data["components"]["database"] = f"unhealthy: {str(e)}"
            health_data["status"] = "unhealthy"
        
        # Redis health
        try:
            await self.redis.ping()
            health_data["components"]["redis"] = "healthy"
        except Exception as e:
            health_data["components"]["redis"] = f"unhealthy: {str(e)}"
            health_data["status"] = "unhealthy"
        
        # Memory usage
        import psutil
        memory = psutil.virtual_memory()
        health_data["metrics"]["memory_usage_percent"] = memory.percent
        health_data["metrics"]["memory_available_gb"] = memory.available / (1024**3)
        
        # CPU usage
        health_data["metrics"]["cpu_usage_percent"] = psutil.cpu_percent(interval=1)
        
        # Active connections
        health_data["metrics"]["websocket_connections"] = len(connection_manager.active_connections)
        
        self.health_status = health_data
        return health_data

# =============================================================================
# NOTIFICATION SYSTEM
# =============================================================================

class NotificationManager:
    """Multi-channel notification system"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.channels = {}
    
    async def send_notification(self, user_id: str, notification: dict):
        """Send notification through multiple channels"""
        notification.update({
            "timestamp": datetime.utcnow().isoformat(),
            "id": str(uuid.uuid4())
        })
        
        # Store notification in database/cache for persistence
        await self.redis.lpush(
            f"notifications:{user_id}",
            json.dumps(notification)
        )
        await self.redis.expire(f"notifications:{user_id}", 86400 * 30)  # 30 days
        
        # Send real-time via WebSocket
        await connection_manager.send_to_user(user_id, {
            "type": "notification",
            "data": notification
        })
        
        # Send via email/SMS if configured (placeholder)
        if notification.get("priority") == "high":
            await self._send_email_notification(user_id, notification)
    
    async def get_user_notifications(self, user_id: str, limit: int = 50) -> List[dict]:
        """Get user notifications"""
        try:
            notifications = await self.redis.lrange(f"notifications:{user_id}", 0, limit - 1)
            return [json.loads(n) for n in notifications]
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    async def _send_email_notification(self, user_id: str, notification: dict):
        """Send email notification (implement with your email service)"""
        # Placeholder for email integration
        logger.info(f"Email notification sent to user {user_id}: {notification['title']}")

# =============================================================================
# ANALYTICS ENGINE
# =============================================================================

class AnalyticsEngine:
    """Real-time analytics and reporting"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
    
    async def record_event(self, event_type: str, user_id: str, data: dict):
        """Record analytics event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "data": data
        }
        
        # Store in Redis streams for real-time analytics
        await self.redis.xadd("analytics_events", event)
        
        # Update counters
        await self.redis.hincrby("analytics_counters", event_type, 1)
        await self.redis.hincrby(f"user_analytics:{user_id}", event_type, 1)
    
    async def get_analytics_summary(self, time_range: int = 3600) -> dict:
        """Get analytics summary for specified time range"""
        try:
            # Get events from the last hour
            end_time = datetime.utcnow().timestamp() * 1000
            start_time = (datetime.utcnow() - timedelta(seconds=time_range)).timestamp() * 1000
            
            events = await self.redis.xrange(
                "analytics_events",
                min=int(start_time),
                max=int(end_time)
            )
            
            # Process events
            summary = {
                "total_events": len(events),
                "event_types": {},
                "unique_users": set(),
                "time_range": time_range
            }
            
            for event_id, fields in events:
                event_type = fields.get(b"event_type", b"unknown").decode()
                user_id = fields.get(b"user_id", b"anonymous").decode()
                
                summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1
                summary["unique_users"].add(user_id)
            
            summary["unique_users"] = len(summary["unique_users"])
            
            return summary
            
        except Exception as e:
            logger.error(f"Analytics summary error: {e}")
            return {"error": str(e)}

# Initialize global instances (these will be initialized in main.py)
cache_manager = None
security_manager = None
task_scheduler = None
health_monitor = None
notification_manager = None
analytics_engine = None
