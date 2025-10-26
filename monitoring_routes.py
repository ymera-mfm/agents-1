# api/monitoring_routes.py
"""
API routes for monitoring, security, and health checks
"""

from fastapi import APIRouter, Depends, Response
from fastapi import Query
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from models import SecurityEventResponse, SecurityEventQuery

from services import (
    auth_service, security_monitor, health_monitor
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health", response_model=Dict)
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed", response_model=Dict)
async def detailed_health_check(
    current_user = Depends(auth_service.get_admin_user)
):
    """Detailed health check with component status"""
    return await health_monitor.check_system_health()

@router.get("/metrics", response_class=Response)
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/security/threats", response_model=List[SecurityEventResponse])
async def get_security_threats(
    severity: Optional[List[str]] = Query(None),
    resolved: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(auth_service.get_admin_user)
):
    """Get detected security threats"""
    query = SecurityEventQuery(
        severity=severity,
        resolved=resolved,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return await security_monitor.get_detected_threats(query)

@router.post("/security/threats/{threat_id}/resolve", response_model=SecurityEventResponse)
async def resolve_security_threat(
    threat_id: str,
    resolution_data: Dict,
    current_user = Depends(auth_service.get_admin_user)
):
    """Resolve a detected security threat"""
    return await security_monitor.resolve_threat(
        threat_id, 
        current_user.id, 
        resolution_data.get("notes", "")
    )

@router.get("/agents/compliance", response_model=Dict)
async def get_reporting_compliance(
    current_user = Depends(auth_service.get_admin_user)
):
    """Get agent reporting compliance statistics"""
    return await security_monitor.get_reporting_compliance()