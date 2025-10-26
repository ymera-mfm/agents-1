"""
Multi-Level Cache Manager
Production-grade caching with L1 (memory) and L2 (Redis) support
"""

import asyncio
import json
import hashlib
from typing import Any, Optional, Callable
from datetime import timedelta
from functools import wraps
from enum import Enum

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

import structlog

logger = structlog.get_logger(__name__)


class CacheStrategy(Enum):
    """Caching strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    WRITE_THROUGH = "write_through"  # Write to all levels
    WRITE_BACK = "write_back"  # Write async to L2


class MultiLevelCache:
    """
    Multi-level caching with L1 (memory), L2 (Redis)
    
    Provides:
    - Automatic cache warming
    - Cache invalidation
    - TTL management
    - Cache-aside pattern
    - Write-through/write-back
    - Graceful degradation
    
    Usage:
        cache = MultiLevelCache(redis_client, default_ttl=3600)
        
        # Get
        value = await cache.get("my_key")
        
        # Set
        await cache.set("my_key", value, ttl=300)
        
        # Decorator
        @cached(ttl=300, key_prefix="user")
        async def get_user(user_id: str):
            return await db.get_user(user_id)
    """
    
    def __init__(self, redis_client: Optional[redis.Redis], default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.enabled = redis_client is not None and REDIS_AVAILABLE
        
        # L1 cache (memory) - fast but limited
        self.l1_cache: dict[str, tuple[Any, float]] = {}
        self.l1_max_size = 1000
        self.l1_access_count: dict[str, int] = {}
        
        # Cache statistics
        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "total_requests": 0,
            "sets": 0,
            "deletes": 0
        }
        
        if not self.enabled:
            logger.warning("Redis not available - using L1 (memory) cache only")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (multi-level)
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        self.stats["total_requests"] += 1
        
        # Try L1 cache (memory) first
        value = self._get_from_l1(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value
        
        self.stats["l1_misses"] += 1
        
        # Try L2 cache (Redis)
        if self.enabled:
            value = await self._get_from_l2(key)
            if value is not None:
                self.stats["l2_hits"] += 1
                # Warm L1 cache
                self._set_to_l1(key, value)
                return value
            
            self.stats["l2_misses"] += 1
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
    ):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            strategy: Caching strategy
        """
        self.stats["sets"] += 1
        ttl = ttl or self.default_ttl
        
        if strategy == CacheStrategy.WRITE_THROUGH:
            # Write to all levels synchronously
            self._set_to_l1(key, value, ttl)
            if self.enabled:
                await self._set_to_l2(key, value, ttl)
        elif strategy == CacheStrategy.WRITE_BACK:
            # Write to L1 immediately, L2 async
            self._set_to_l1(key, value, ttl)
            if self.enabled:
                asyncio.create_task(self._set_to_l2(key, value, ttl))
        else:
            # Default to write-through
            self._set_to_l1(key, value, ttl)
            if self.enabled:
                await self._set_to_l2(key, value, ttl)
    
    async def delete(self, key: str):
        """Delete cache entry"""
        self.stats["deletes"] += 1
        self._delete_from_l1(key)
        if self.enabled:
            await self._delete_from_l2(key)
    
    async def invalidate(self, key: str):
        """Alias for delete"""
        await self.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        # L1 invalidation
        keys_to_delete = [k for k in self.l1_cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.l1_cache[key]
            if key in self.l1_access_count:
                del self.l1_access_count[key]
        
        # L2 invalidation
        if self.enabled and self.redis:
            try:
                keys = await self.redis.keys(f"*{pattern}*")
                if keys:
                    await self.redis.delete(*keys)
            except Exception as e:
                logger.error(f"Pattern invalidation error: {e}")
    
    async def clear(self):
        """Clear all cache"""
        self.l1_cache.clear()
        self.l1_access_count.clear()
        if self.enabled and self.redis:
            try:
                await self.redis.flushdb()
            except Exception as e:
                logger.error(f"Cache clear error: {e}")
    
    def _get_from_l1(self, key: str) -> Optional[Any]:
        """Get from L1 (memory) cache"""
        if key in self.l1_cache:
            value, expiry = self.l1_cache[key]
            current_time = asyncio.get_event_loop().time()
            
            if expiry > current_time:
                # Update access count for LRU
                self.l1_access_count[key] = self.l1_access_count.get(key, 0) + 1
                return value
            else:
                # Expired
                del self.l1_cache[key]
                if key in self.l1_access_count:
                    del self.l1_access_count[key]
        return None
    
    def _set_to_l1(self, key: str, value: Any, ttl: int = None):
        """Set to L1 (memory) cache"""
        # Evict if cache is full (LRU)
        if len(self.l1_cache) >= self.l1_max_size:
            # Find least recently used (lowest access count)
            if self.l1_access_count:
                lru_key = min(self.l1_access_count.keys(), key=lambda k: self.l1_access_count[k])
                del self.l1_cache[lru_key]
                del self.l1_access_count[lru_key]
            else:
                # If no access counts, remove oldest
                if self.l1_cache:
                    oldest_key = next(iter(self.l1_cache))
                    del self.l1_cache[oldest_key]
        
        ttl = ttl or self.default_ttl
        expiry = asyncio.get_event_loop().time() + ttl
        self.l1_cache[key] = (value, expiry)
        self.l1_access_count[key] = 1
    
    def _delete_from_l1(self, key: str):
        """Delete from L1 cache"""
        if key in self.l1_cache:
            del self.l1_cache[key]
        if key in self.l1_access_count:
            del self.l1_access_count[key]
    
    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Get from L2 (Redis) cache"""
        if not self.enabled or not self.redis:
            return None
        
        try:
            data = await self.redis.get(key)
            if data:
                # Use JSON instead of pickle for security
                return json.loads(data)
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
        return None
    
    async def _set_to_l2(self, key: str, value: Any, ttl: int):
        """Set to L2 (Redis) cache"""
        if not self.enabled or not self.redis:
            return
        
        try:
            # Use JSON instead of pickle for security
            data = json.dumps(value)
            await self.redis.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
    
    async def _delete_from_l2(self, key: str):
        """Delete from L2 cache"""
        if not self.enabled or not self.redis:
            return
        
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"L2 cache delete error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.stats["total_requests"]
        if total == 0:
            return {**self.stats, "l1_hit_rate": 0, "l2_hit_rate": 0, "overall_hit_rate": 0}
        
        l1_hit_rate = self.stats["l1_hits"] / total
        l2_requests = total - self.stats["l1_hits"]
        l2_hit_rate = self.stats["l2_hits"] / l2_requests if l2_requests > 0 else 0
        overall_hit_rate = (self.stats["l1_hits"] + self.stats["l2_hits"]) / total
        
        return {
            **self.stats,
            "l1_hit_rate": l1_hit_rate,
            "l2_hit_rate": l2_hit_rate,
            "overall_hit_rate": overall_hit_rate,
            "l1_size": len(self.l1_cache),
            "l1_max_size": self.l1_max_size
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "total_requests": 0,
            "sets": 0,
            "deletes": 0
        }


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl=300, key_prefix="user_data")
        async def get_user(user_id: str):
            return await db.get_user(user_id)
        
        # With different strategies
        @cached(ttl=60, strategy=CacheStrategy.WRITE_BACK)
        async def get_temporary_data():
            return expensive_operation()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cache = get_cache_manager()
            if cache:
                cached_value = await cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if cache:
                await cache.set(cache_key, result, ttl, strategy)
            
            return result
        return wrapper
    return decorator


# Global cache manager instance
_cache_manager: Optional[MultiLevelCache] = None


def initialize_cache(redis_client: Optional[redis.Redis], default_ttl: int = 3600):
    """
    Initialize global cache manager
    
    Usage:
        from shared.cache import initialize_cache
        import redis.asyncio as redis
        
        redis_client = redis.from_url(settings.REDIS_URL)
        initialize_cache(redis_client, default_ttl=3600)
    """
    global _cache_manager
    _cache_manager = MultiLevelCache(redis_client, default_ttl)
    logger.info("Cache manager initialized", redis_enabled=redis_client is not None)


def get_cache_manager() -> Optional[MultiLevelCache]:
    """Get global cache manager"""
    return _cache_manager
