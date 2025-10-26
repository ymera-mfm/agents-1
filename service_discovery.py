"""
Service Discovery and Health Check Module
Provides endpoints for health checks, readiness, liveness, and metrics
"""

from fastapi import APIRouter, status, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime
import asyncio
import psutil
import os

from core.config import settings
from core.integration_config import integration_settings
from core.feature_flags import feature_flags

router = APIRouter()


class HealthStatus(BaseModel):
    """Health status response model"""
    status: str
    timestamp: datetime
    version: str
    service: str
    uptime: float
    checks: Dict[str, dict]


class ReadinessStatus(BaseModel):
    """Readiness status response model"""
    ready: bool
    checks: Dict[str, bool]
    timestamp: datetime


class LivenessStatus(BaseModel):
    """Liveness status response model"""
    alive: bool
    timestamp: datetime


class VersionInfo(BaseModel):
    """Version information response model"""
    service: str
    version: str
    build_date: Optional[str] = None
    commit_hash: Optional[str] = None
    environment: str


# Track startup time
_startup_time = datetime.utcnow()


async def check_database_health() -> dict:
    """Check database connectivity"""
    try:
        from core.database import Database
        db = Database()
        await db.initialize()
        await db.cleanup()
        return {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }


async def check_redis_health() -> dict:
    """Check Redis connectivity"""
    try:
        import redis.asyncio as aioredis
        redis_client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()
        return {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }


async def check_disk_space() -> dict:
    """Check available disk space"""
    try:
        disk_usage = psutil.disk_usage('/')
        percent_used = disk_usage.percent
        
        if percent_used > 90:
            status = "unhealthy"
            message = f"Disk space critical: {percent_used}% used"
        elif percent_used > 80:
            status = "degraded"
            message = f"Disk space warning: {percent_used}% used"
        else:
            status = "healthy"
            message = f"Disk space adequate: {percent_used}% used"
        
        return {
            "status": status,
            "message": message,
            "percent_used": percent_used,
            "free_gb": round(disk_usage.free / (1024**3), 2)
        }
    except Exception as e:
        return {
            "status": "unknown",
            "message": f"Could not check disk space: {str(e)}"
        }


async def check_memory() -> dict:
    """Check memory usage"""
    try:
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        if percent_used > 90:
            status = "unhealthy"
            message = f"Memory critical: {percent_used}% used"
        elif percent_used > 80:
            status = "degraded"
            message = f"Memory warning: {percent_used}% used"
        else:
            status = "healthy"
            message = f"Memory adequate: {percent_used}% used"
        
        return {
            "status": status,
            "message": message,
            "percent_used": percent_used,
            "available_gb": round(memory.available / (1024**3), 2)
        }
    except Exception as e:
        return {
            "status": "unknown",
            "message": f"Could not check memory: {str(e)}"
        }


@router.get(
    "/health",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    tags=["Service Discovery"]
)
async def health_check():
    """
    Comprehensive health check endpoint
    Returns detailed health status of all system components
    """
    checks = {}
    
    # Run all health checks in parallel
    if integration_settings.enable_health_checks:
        results = await asyncio.gather(
            check_database_health(),
            check_redis_health(),
            check_disk_space(),
            check_memory(),
            return_exceptions=True
        )
        
        checks = {
            "database": results[0] if not isinstance(results[0], Exception) else {"status": "error", "message": str(results[0])},
            "redis": results[1] if not isinstance(results[1], Exception) else {"status": "error", "message": str(results[1])},
            "disk": results[2] if not isinstance(results[2], Exception) else {"status": "error", "message": str(results[2])},
            "memory": results[3] if not isinstance(results[3], Exception) else {"status": "error", "message": str(results[3])},
        }
    
    # Determine overall health status
    overall_status = "healthy"
    for check_name, check_result in checks.items():
        if check_result.get("status") == "unhealthy":
            overall_status = "unhealthy"
            break
        elif check_result.get("status") == "degraded" and overall_status != "unhealthy":
            overall_status = "degraded"
    
    # Calculate uptime
    uptime = (datetime.utcnow() - _startup_time).total_seconds()
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=integration_settings.service_version,
        service=integration_settings.service_name,
        uptime=uptime,
        checks=checks
    )


@router.get(
    "/ready",
    response_model=ReadinessStatus,
    status_code=status.HTTP_200_OK,
    tags=["Service Discovery"]
)
async def readiness_check():
    """
    Readiness probe endpoint
    Indicates if the service is ready to accept traffic
    """
    checks = {}
    
    # Check critical dependencies
    if integration_settings.enable_health_checks:
        db_check = await check_database_health()
        checks["database"] = db_check.get("status") == "healthy"
        
        # Application is ready if database is healthy
        ready = checks["database"]
    else:
        ready = True
    
    response_status = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=response_status,
        content=ReadinessStatus(
            ready=ready,
            checks=checks,
            timestamp=datetime.utcnow()
        ).dict()
    )


@router.get(
    "/live",
    response_model=LivenessStatus,
    status_code=status.HTTP_200_OK,
    tags=["Service Discovery"]
)
async def liveness_check():
    """
    Liveness probe endpoint
    Indicates if the service is alive and running
    """
    # Simple liveness check - if we can respond, we're alive
    return LivenessStatus(
        alive=True,
        timestamp=datetime.utcnow()
    )


@router.get(
    "/version",
    response_model=VersionInfo,
    status_code=status.HTTP_200_OK,
    tags=["Service Discovery"]
)
async def version_info():
    """
    Version information endpoint
    Returns service version and build information
    """
    return VersionInfo(
        service=integration_settings.service_name,
        version=integration_settings.service_version,
        build_date=os.environ.get("BUILD_DATE"),
        commit_hash=os.environ.get("COMMIT_HASH"),
        environment=settings.environment
    )


@router.get(
    "/info",
    status_code=status.HTTP_200_OK,
    tags=["Service Discovery"]
)
async def service_info():
    """
    Comprehensive service information endpoint
    Returns service metadata, features, and configuration
    """
    return {
        "service": {
            "name": integration_settings.service_name,
            "version": integration_settings.service_version,
            "id": integration_settings.service_id,
            "environment": settings.environment
        },
        "features": feature_flags.get_enabled_features(),
        "endpoints": {
            "health": integration_settings.health_check_endpoint,
            "readiness": integration_settings.readiness_endpoint,
            "liveness": integration_settings.liveness_endpoint,
            "metrics": integration_settings.metrics_endpoint,
            "version": "/version"
        },
        "integrations": {
            "distributed_tracing": integration_settings.enable_distributed_tracing,
            "metrics_export": integration_settings.enable_metrics_export,
            "service_discovery": integration_settings.enable_service_discovery
        },
        "uptime": (datetime.utcnow() - _startup_time).total_seconds()
    }
