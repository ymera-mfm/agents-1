"""
Enhanced Health Check Endpoints
Production-ready health checks for Kubernetes and monitoring
"""

from fastapi import APIRouter, status, Depends
from typing import Dict, Any
import time
import psutil
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

# Store startup time
START_TIME = time.time()


@router.get("/live")
async def liveness():
    """
    Kubernetes liveness probe
    Returns 200 if process is alive
    """
    return {
        "status": "alive",
        "timestamp": time.time(),
        "uptime_seconds": time.time() - START_TIME
    }


@router.get("/ready")
async def readiness():
    """
    Kubernetes readiness probe
    Returns 200 if system is ready to accept traffic
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - Essential services
    """
    checks = {}
    all_healthy = True
    
    # Check database (import here to avoid circular dependency)
    try:
        from shared.database.connection_pool import get_db_pool
        pool = get_db_pool()
        if pool:
            # Simple query to check connectivity
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            checks["database"] = "healthy"
        else:
            checks["database"] = "not_initialized"
            all_healthy = False
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)[:100]}"
        all_healthy = False
    
    # Check Redis
    try:
        from shared.cache import get_cache_manager
        cache = get_cache_manager()
        if cache and cache.enabled:
            # Try to set and get a test value
            await cache.set("health_check", "ok", ttl=10)
            value = await cache.get("health_check")
            checks["redis"] = "healthy" if value == "ok" else "unhealthy"
        else:
            checks["redis"] = "not_configured"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)[:100]}"
        all_healthy = False
    
    # Check circuit breakers
    try:
        from shared.patterns import circuit_breaker_registry
        open_breakers = circuit_breaker_registry.list_open_breakers()
        if open_breakers:
            checks["circuit_breakers"] = f"warning: {len(open_breakers)} open"
            # Don't fail readiness for open breakers
        else:
            checks["circuit_breakers"] = "healthy"
    except Exception as e:
        checks["circuit_breakers"] = f"error: {str(e)[:100]}"
    
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": time.time()
    }


@router.get("/startup")
async def startup():
    """
    Kubernetes startup probe
    Returns 200 when initialization is complete
    """
    # Check if critical components are initialized
    initialization_status = {}
    
    try:
        from shared.cache import get_cache_manager
        initialization_status["cache"] = get_cache_manager() is not None
    except:
        initialization_status["cache"] = False
    
    try:
        from shared.database.connection_pool import get_db_pool
        initialization_status["database"] = get_db_pool() is not None
    except:
        initialization_status["database"] = False
    
    all_initialized = all(initialization_status.values())
    
    return {
        "status": "started" if all_initialized else "starting",
        "initialization": initialization_status,
        "uptime_seconds": time.time() - START_TIME,
        "timestamp": time.time()
    }


@router.get("/detailed")
async def detailed_health():
    """
    Detailed health check with comprehensive metrics
    
    Includes:
    - System resources
    - Component status
    - Performance metrics
    - Circuit breaker status
    """
    # System resources
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Cache stats
    cache_stats = {}
    try:
        from shared.cache import get_cache_manager
        cache = get_cache_manager()
        if cache:
            cache_stats = cache.get_stats()
    except:
        pass
    
    # Circuit breaker stats
    circuit_breaker_stats = {}
    try:
        from shared.patterns import circuit_breaker_registry
        circuit_breaker_stats = circuit_breaker_registry.get_all_metrics()
    except:
        pass
    
    # Task queue stats
    task_queue_stats = {}
    try:
        from shared.queue import get_task_queue
        queue = get_task_queue()
        if queue:
            task_queue_stats = queue.get_metrics()
    except:
        pass
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime_seconds": time.time() - START_TIME,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024 * 1024 * 1024)
        },
        "cache": cache_stats,
        "circuit_breakers": circuit_breaker_stats,
        "task_queue": task_queue_stats,
        "agents": {
            "total": 13,
            "active": "check_status_endpoint"  # Placeholder
        }
    }


@router.get("/metrics")
async def metrics():
    """
    Prometheus-compatible metrics endpoint
    
    Returns metrics in Prometheus text format
    """
    metrics_lines = []
    
    # Uptime
    uptime = time.time() - START_TIME
    metrics_lines.append(f"# HELP uptime_seconds System uptime in seconds")
    metrics_lines.append(f"# TYPE uptime_seconds gauge")
    metrics_lines.append(f"uptime_seconds {uptime}")
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    metrics_lines.append(f"# HELP cpu_usage_percent CPU usage percentage")
    metrics_lines.append(f"# TYPE cpu_usage_percent gauge")
    metrics_lines.append(f"cpu_usage_percent {cpu_percent}")
    
    metrics_lines.append(f"# HELP memory_usage_percent Memory usage percentage")
    metrics_lines.append(f"# TYPE memory_usage_percent gauge")
    metrics_lines.append(f"memory_usage_percent {memory.percent}")
    
    # Cache metrics
    try:
        from shared.cache import get_cache_manager
        cache = get_cache_manager()
        if cache:
            stats = cache.get_stats()
            
            metrics_lines.append(f"# HELP cache_hit_rate Cache hit rate")
            metrics_lines.append(f"# TYPE cache_hit_rate gauge")
            metrics_lines.append(f"cache_hit_rate {stats.get('overall_hit_rate', 0)}")
            
            metrics_lines.append(f"# HELP cache_size Current cache size")
            metrics_lines.append(f"# TYPE cache_size gauge")
            metrics_lines.append(f"cache_size {stats.get('l1_size', 0)}")
    except:
        pass
    
    # Circuit breaker metrics
    try:
        from shared.patterns import circuit_breaker_registry
        for name, cb_metrics in circuit_breaker_registry.get_all_metrics().items():
            safe_name = name.replace("-", "_").replace(".", "_")
            
            metrics_lines.append(f"# HELP circuit_breaker_state Circuit breaker state (0=closed, 1=half_open, 2=open)")
            metrics_lines.append(f"# TYPE circuit_breaker_state gauge")
            state_value = {"closed": 0, "half_open": 1, "open": 2}.get(cb_metrics["state"], 0)
            metrics_lines.append(f'circuit_breaker_state{{name="{name}"}} {state_value}')
            
            metrics_lines.append(f"# HELP circuit_breaker_total_calls Total calls through circuit breaker")
            metrics_lines.append(f"# TYPE circuit_breaker_total_calls counter")
            metrics_lines.append(f'circuit_breaker_total_calls{{name="{name}"}} {cb_metrics["total_calls"]}')
    except:
        pass
    
    return "\n".join(metrics_lines)
