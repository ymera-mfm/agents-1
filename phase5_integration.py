"""
Phase 5 Integration Example
Demonstrates how to use all Phase 5 features together
"""

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
import asyncio

# Import Phase 5 components
from core.integration_config import integration_settings
from core.feature_flags import feature_flags, is_enabled
from core.api_standards import (
    success_response,
    error_response,
    paginated_response,
    ErrorCode,
    QueryParams
)
from core.structured_logging import setup_logging, get_logger
from core.metrics import MetricsCollector, initialize_metrics, metrics_router
from core.service_discovery import router as discovery_router
from middleware.request_tracking import RequestTrackingMiddleware, get_request_id
from core.distributed_tracing import tracing, trace_span

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=integration_settings.service_name,
    version=integration_settings.service_version,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

# Add request tracking middleware
app.add_middleware(RequestTrackingMiddleware)

# Initialize metrics
initialize_metrics()

# Include routers
app.include_router(metrics_router)
app.include_router(discovery_router)

# Instrument app for tracing (if enabled)
tracing.instrument_app(app)


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info(
        "Application starting",
        service_name=integration_settings.service_name,
        version=integration_settings.service_version,
        environment="production"
    )


@app.get("/api/v1/example")
async def example_endpoint(
    request: Request,
    params: QueryParams = Depends()
):
    """Example endpoint using Phase 5 features"""
    request_id = get_request_id(request)
    
    logger.info(
        "Processing example request",
        request_id=request_id,
        page=params.page
    )
    
    if not is_enabled("enable_chat_interface"):
        return JSONResponse(
            status_code=503,
            content=error_response(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message="Feature temporarily disabled",
                request_id=request_id
            )
        )
    
    items = [{"id": i, "name": f"Item {i}"} for i in range(1, 11)]
    
    return paginated_response(
        items=items,
        page=params.page,
        page_size=params.page_size,
        total_items=100,
        request_id=request_id
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
