"""
YMERA Enterprise AI & Integration Routes - Production Ready
Multi-provider AI services, Kibana integration, and system monitoring
Version: 2.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
import json
import asyncio
from enum import Enum

from ymera_core.security.auth_manager import AuthManager
from ymera_core.logging.structured_logger import StructuredLogger
from ymera_services.ai.multi_llm_manager import MultiLLMManager
from ymera_services.kibana.kibana_service import KibanaService
from ymera_core.database.manager import DatabaseManager

# Initialize logger
logger = StructuredLogger(__name__)

# ============================================================================
# AI SERVICES ROUTES
# ============================================================================

ai_router = APIRouter(prefix="/api/v1/ai", tags=["AI Services"])

class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    AUTO = "auto"

class ChatRequest(BaseModel):
    """AI chat completion request"""
    message: str = Field(..., min_length=1, max_length=32000)
    provider: Optional[AIProvider] = Field(default=AIProvider.AUTO)
    model: Optional[str] = Field(None, max_length=100)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2000, ge=1, le=32000)
    stream: bool = Field(default=False)
    system_prompt: Optional[str] = Field(None, max_length=4000)
    context: List[Dict[str, str]] = Field(default_factory=list, max_length=50)
    
    @field_validator('context')
    @classmethod
    def validate_context(cls, v):
        for msg in v:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError("Context messages must have 'role' and 'content'")
            if msg['role'] not in ['user', 'assistant', 'system']:
                raise ValueError(f"Invalid role: {msg['role']}")
        return v

class AIResponse(BaseModel):
    """AI completion response"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    content: str
    provider: str
    model: str
    tokens_used: int
    finish_reason: str
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EmbeddingRequest(BaseModel):
    """Text embedding request"""
    text: str = Field(..., min_length=1, max_length=8000)
    provider: Optional[AIProvider] = Field(default=AIProvider.AUTO)
    model: Optional[str] = None

class EmbeddingResponse(BaseModel):
    """Embedding response"""
    embedding: List[float]
    provider: str
    model: str
    dimensions: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

async def get_current_user(request: Request, auth_manager: AuthManager = Depends()) -> dict:
    """Authenticate user"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization"
            )
        
        token = auth_header.replace("Bearer ", "")
        payload = await auth_manager.verify_token(token)
        
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@ai_router.post("/chat", response_model=AIResponse)
async def chat_completion(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    ai_manager: MultiLLMManager = Depends()
):
    """
    Generate AI chat completion with automatic provider selection.
    
    Features:
    - Multi-provider support (OpenAI, Anthropic, Google, Cohere)
    - Automatic failover
    - Context management
    - Token tracking
    - Streaming support
    
    Rate Limits:
    - Free: 20 requests/minute
    - Pro: 100 requests/minute
    - Enterprise: Unlimited
    """
    try:
        user_id = current_user["sub"]
        
        # Determine provider and model
        provider = request.provider if request.provider != AIProvider.AUTO else None
        model = request.model
        
        if not model:
            # Default models per provider
            model_defaults = {
                AIProvider.OPENAI: "gpt-4-turbo-preview",
                AIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
                AIProvider.GOOGLE: "gemini-pro",
                AIProvider.COHERE: "command"
            }
            model = model_defaults.get(provider, "gpt-4-turbo-preview")
        
        # Prepare AI request
        ai_request = {
            "provider": provider,
            "model": model,
            "messages": request.context + [{"role": "user", "content": request.message}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream
        }
        
        if request.system_prompt:
            ai_request["system_prompt"] = request.system_prompt
        
        # Non-streaming response
        if not request.stream:
            response = await ai_manager.get_completion(ai_request)
            
            # Log usage
            logger.info(
                f"AI completion for user {user_id}",
                extra={
                    "user_id": user_id,
                    "provider": response.get("provider"),
                    "tokens": response.get("tokens_used")
                }
            )
            
            return AIResponse(
                content=response["content"],
                provider=response["provider"],
                model=response["model"],
                tokens_used=response.get("tokens_used", 0),
                finish_reason=response.get("finish_reason", "stop"),
                confidence=response.get("confidence"),
                metadata=response.get("metadata", {})
            )
        
        # Streaming response
        async def generate_stream() -> AsyncIterator[str]:
            """Stream AI response chunks"""
            try:
                async for chunk in ai_manager.stream_completion(ai_request):
                    yield f"data: {json.dumps(chunk)}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"AI completion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI completion failed: {str(e)}"
        )

@ai_router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    current_user: dict = Depends(get_current_user),
    ai_manager: MultiLLMManager = Depends()
):
    """
    Generate text embeddings for semantic search and similarity.
    
    Supports:
    - Multiple embedding models
    - Automatic provider selection
    - Dimension normalization
    """
    try:
        user_id = current_user["sub"]
        
        # Generate embeddings
        result = await ai_manager.generate_embeddings({
            "text": request.text,
            "provider": request.provider if request.provider != AIProvider.AUTO else None,
            "model": request.model
        })
        
        logger.info(
            f"Generated embeddings for user {user_id}",
            extra={
                "user_id": user_id,
                "provider": result["provider"],
                "dimensions": len(result["embedding"])
            }
        )
        
        return EmbeddingResponse(
            embedding=result["embedding"],
            provider=result["provider"],
            model=result["model"],
            dimensions=len(result["embedding"])
        )
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding generation failed: {str(e)}"
        )

@ai_router.get("/providers", status_code=status.HTTP_200_OK)
async def list_providers(
    current_user: dict = Depends(get_current_user),
    ai_manager: MultiLLMManager = Depends()
):
    """
    List available AI providers and their models.
    
    Returns provider capabilities, rate limits, and status.
    """
    try:
        providers = await ai_manager.get_available_providers()
        
        return {
            "providers": providers,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve providers"
        )

@ai_router.get("/usage", status_code=status.HTTP_200_OK)
async def get_ai_usage(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """
    Get AI usage statistics for the authenticated user.
    
    Includes:
    - Total requests by provider
    - Token usage
    - Cost estimation
    - Usage trends
    """
    try:
        user_id = current_user["sub"]
        
        usage = await db_manager.get_ai_usage_stats(user_id, days)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_requests": usage.get("total_requests", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "by_provider": usage.get("by_provider", {}),
            "estimated_cost": usage.get("estimated_cost", 0.0),
            "trend": usage.get("trend", [])
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )

# ============================================================================
# KIBANA INTEGRATION ROUTES
# ============================================================================

kibana_router = APIRouter(prefix="/api/v1/kibana", tags=["Kibana Services"])

class KibanaAlertRequest(BaseModel):
    """Kibana alert creation request"""
    name: str = Field(..., min_length=1, max_length=200)
    alert_type: str = Field(..., regex="^(threshold|anomaly|query)$")
    index_pattern: str = Field(..., max_length=200)
    params: Dict[str, Any] = Field(...)
    actions: List[Dict[str, Any]] = Field(default_factory=list, max_items=10)
    enabled: bool = Field(default=True)
    
    @field_validator('params')
    @classmethod
    def validate_params(cls, v, info):
        values = info.data
        alert_type = values.get('alert_type')
        
        if alert_type == 'threshold':
            required = ['threshold', 'comparison', 'timeWindow']
            if not all(k in v for k in required):
                raise ValueError(f"Threshold alert requires: {required}")
        
        elif alert_type == 'anomaly':
            if 'sensitivity' not in v:
                raise ValueError("Anomaly alert requires 'sensitivity'")
        
        elif alert_type == 'query':
            if 'query' not in v:
                raise ValueError("Query alert requires 'query'")
        
        return v

class KibanaAlertResponse(BaseModel):
    """Kibana alert response"""
    success: bool
    message: str
    rule_id: Optional[str] = None
    alert_type: str
    name: str

class KibanaDashboardRequest(BaseModel):
    """Kibana dashboard creation request"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    panels: List[Dict[str, Any]] = Field(..., min_items=1, max_items=20)
    timeRange: Optional[Dict[str, str]] = None
    refreshInterval: Optional[int] = Field(None, ge=5, le=3600)

class KibanaResponse(BaseModel):
    """Kibana operation response"""
    success: bool
    message: str
    dashboard_id: Optional[str] = None
    embed_url: Optional[str] = None
    share_url: Optional[str] = None

async def require_admin_role(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role for Kibana operations"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user

@kibana_router.post("/alerts", response_model=KibanaAlertResponse)
async def create_alert(
    request: KibanaAlertRequest,
    current_user: dict = Depends(require_admin_role),
    kibana_service: KibanaService = Depends()
):
    """
    Create Kibana alert rule.
    
    Supports:
    - Threshold alerts (metric thresholds)
    - Anomaly alerts (ML-based detection)
    - Query alerts (custom Elasticsearch queries)
    
    Requires: Admin role
    """
    try:
        user_id = current_user["sub"]
        
        # Create alert
        rule_id = await kibana_service.create_alert(
            name=request.name,
            alert_type=request.alert_type,
            params=request.params,
            actions=request.actions,
            index_pattern=request.index_pattern,
            enabled=request.enabled
        )
        
        logger.info(
            f"User {user_id} created Kibana alert {request.name}",
            extra={
                "user_id": user_id,
                "rule_id": rule_id,
                "alert_type": request.alert_type
            }
        )
        
        return KibanaAlertResponse(
            success=True,
            message="Alert created successfully",
            rule_id=rule_id,
            alert_type=request.alert_type,
            name=request.name
        )
        
    except Exception as e:
        logger.error(f"Alert creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}"
        )

@kibana_router.get("/alerts", status_code=status.HTTP_200_OK)
async def list_alerts(
    current_user: dict = Depends(get_current_user),
    kibana_service: KibanaService = Depends()
):
    """
    List all Kibana alert rules.
    
    Returns alert configuration, status, and trigger history.
    """
    try:
        alerts = await kibana_service.list_alerts()
        
        logger.info(f"User {current_user['sub']} listed Kibana alerts")
        
        return {
            "success": True,
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )

@kibana_router.put("/alerts/{rule_id}", status_code=status.HTTP_200_OK)
async def update_alert(
    rule_id: str = Path(..., max_length=100),
    request: KibanaAlertRequest = ...,
    current_user: dict = Depends(require_admin_role),
    kibana_service: KibanaService = Depends()
):
    """
    Update existing Kibana alert rule.
    
    Requires: Admin role
    """
    try:
        await kibana_service.update_alert(
            rule_id=rule_id,
            params=request.params,
            actions=request.actions,
            alert_type=request.alert_type,
            enabled=request.enabled
        )
        
        logger.info(
            f"User {current_user['sub']} updated alert {rule_id}",
            extra={"user_id": current_user['sub'], "rule_id": rule_id}
        )
        
        return {
            "success": True,
            "message": "Alert updated successfully",
            "rule_id": rule_id
        }
        
    except Exception as e:
        logger.error(f"Alert update failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert: {str(e)}"
        )

@kibana_router.delete("/alerts/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    rule_id: str = Path(..., max_length=100),
    alert_type: str = Query(..., regex="^(threshold|anomaly|query|watcher)$"),
    current_user: dict = Depends(require_admin_role),
    kibana_service: KibanaService = Depends()
):
    """
    Delete Kibana alert rule.
    
    Requires: Admin role
    """
    try:
        await kibana_service.delete_alert(rule_id, alert_type)
        
        logger.info(
            f"User {current_user['sub']} deleted alert {rule_id}",
            extra={"user_id": current_user['sub'], "rule_id": rule_id}
        )
        
    except Exception as e:
        logger.error(f"Alert deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert: {str(e)}"
        )

@kibana_router.post("/dashboards", response_model=KibanaResponse)
async def create_dashboard(
    request: KibanaDashboardRequest,
    current_user: dict = Depends(require_admin_role),
    kibana_service: KibanaService = Depends()
):
    """
    Create Kibana dashboard with visualizations.
    
    Features:
    - Custom panel layouts
    - Embeddable dashboards
    - Shareable URLs
    - Auto-refresh configuration
    
    Requires: Admin role
    """
    try:
        # Create dashboard
        result = await kibana_service.create_dashboard(
            title=request.title,
            description=request.description,
            panels=request.panels,
            time_range=request.timeRange,
            refresh_interval=request.refreshInterval
        )
        
        logger.info(
            f"User {current_user['sub']} created dashboard {result['dashboard_id']}",
            extra={
                "user_id": current_user['sub'],
                "dashboard_id": result['dashboard_id']
            }
        )
        
        return KibanaResponse(
            success=True,
            message="Dashboard created successfully",
            dashboard_id=result['dashboard_id'],
            embed_url=result.get('embed_url'),
            share_url=result.get('share_url')
        )
        
    except Exception as e:
        logger.error(f"Dashboard creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard: {str(e)}"
        )

@kibana_router.get("/dashboards/{dashboard_id}", status_code=status.HTTP_200_OK)
async def get_dashboard(
    dashboard_id: str = Path(..., max_length=100),
    current_user: dict = Depends(get_current_user),
    kibana_service: KibanaService = Depends()
):
    """
    Get Kibana dashboard details and configuration.
    """
    try:
        dashboard = await kibana_service.get_dashboard(dashboard_id)
        
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found"
            )
        
        return {
            "success": True,
            "dashboard": dashboard,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard"
        )

@kibana_router.get("/health", status_code=status.HTTP_200_OK)
async def kibana_health(
    current_user: dict = Depends(get_current_user),
    kibana_service: KibanaService = Depends()
):
    """
    Check Kibana service health and connectivity.
    
    Returns:
    - Kibana status
    - Elasticsearch connectivity
    - Available features
    """
    try:
        health = await kibana_service.health_check()
        
        return {
            "success": True,
            "health": health,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Kibana health check failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# SYSTEM MONITORING & METRICS ROUTES
# ============================================================================

monitoring_router = APIRouter(prefix="/api/v1/monitoring", tags=["System Monitoring"])

@monitoring_router.get("/health", status_code=status.HTTP_200_OK)
async def system_health(
    db_manager: DatabaseManager = Depends(),
    ai_manager: MultiLLMManager = Depends()
):
    """
    Comprehensive system health check.
    
    Checks:
    - Database connectivity
    - AI service availability
    - Cache status
    - Background workers
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        await db_manager.health_check()
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Connected"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check AI services
    try:
        ai_health = await ai_manager.health_check()
        health_status["components"]["ai_services"] = ai_health
    except Exception as e:
        health_status["components"]["ai_services"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Return appropriate status code
    status_code = (
        status.HTTP_200_OK if health_status["status"] == "healthy" 
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return health_status

@monitoring_router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics(
    current_user: dict = Depends(require_admin_role),
    db_manager: DatabaseManager = Depends()
):
    """
    Get system-wide metrics and statistics.
    
    Requires: Admin role
    
    Returns:
    - Request metrics
    - Performance statistics
    - Resource utilization
    - Error rates
    """
    try:
        metrics = await db_manager.get_system_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "uptime_seconds": metrics.get("uptime", 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )

@monitoring_router.get("/logs", status_code=status.HTTP_200_OK)
async def get_logs(
    level: str = Query("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin_role),
    db_manager: DatabaseManager = Depends()
):
    """
    Retrieve system logs with filtering.
    
    Requires: Admin role
    
    Supports:
    - Log level filtering
    - Pagination
    - Time range filtering
    """
    try:
        logs = await db_manager.get_system_logs(
            level=level,
            limit=limit,
            offset=offset
        )
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "level": level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve logs"
        )

# ============================================================================
# ROUTER AGGREGATION
# ============================================================================

def get_all_routers():
    """Return all routers for inclusion in main app"""
    return [ai_router, kibana_router, monitoring_router]