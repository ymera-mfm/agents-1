"""
YMERA Enterprise Platform - Production Main Application
FastAPI application with comprehensive middleware, security, and monitoring
Version: 2.0.0
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import asyncio
from typing import Dict, Any
import uvicorn

# Core imports
from ymera_core.config import Settings
from ymera_core.database.manager import DatabaseManager
from ymera_core.cache.redis_cache import RedisCacheManager
from ymera_core.logging.structured_logger import StructuredLogger
from ymera_core.security.auth_manager import AuthManager
from ymera_core.monitoring.metrics import MetricsCollector
from ymera_core.exceptions import YMERAException

# Service imports
from ymera_services.ai.multi_llm_manager import MultiLLMManager
from ymera_services.github.repository_analyzer import GitHubRepositoryAnalyzer
from ymera_services.kibana.kibana_service import KibanaService
from ymera_agents.orchestrator import AgentOrchestrator
from ymera_agents.learning.learning_engine import LearningEngine

# Route imports
from routes.analysis_routes import router as analysis_router
from routes.chat_routes import router as chat_router
from routes.ai_routes import get_all_routers

# Initialize settings and logger
settings = Settings()
logger = StructuredLogger(__name__)

# Global state container
class AppState:
    """Application state container"""
    def __init__(self):
        self.db_manager: DatabaseManager = None
        self.cache_manager: RedisCacheManager = None
        self.auth_manager: AuthManager = None
        self.ai_manager: MultiLLMManager = None
        self.github_analyzer: GitHubRepositoryAnalyzer = None
        self.kibana_service: KibanaService = None
        self.orchestrator: AgentOrchestrator = None
        self.learning_engine: LearningEngine = None
        self.metrics: MetricsCollector = None
        self.is_ready: bool = False

app_state = AppState()

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management - startup and shutdown
    """
    # Startup
    logger.info("Starting YMERA Enterprise Platform...")
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        app_state.db_manager = DatabaseManager(settings.database_url)
        await app_state.db_manager.connect()
        await app_state.db_manager.initialize_schema()
        
        # Initialize cache
        logger.info("Initializing Redis cache...")
        app_state.cache_manager = RedisCacheManager(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db
        )
        await app_state.cache_manager.connect()
        
        # Initialize auth manager
        logger.info("Initializing authentication...")
        app_state.auth_manager = AuthManager(
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        # Initialize AI manager
        logger.info("Initializing AI services...")
        app_state.ai_manager = MultiLLMManager(
            openai_api_key=settings.openai_api_key,
            anthropic_api_key=settings.anthropic_api_key,
            google_api_key=settings.google_api_key,
            cohere_api_key=settings.cohere_api_key
        )
        await app_state.ai_manager.initialize()
        
        # Initialize GitHub analyzer
        logger.info("Initializing GitHub analyzer...")
        app_state.github_analyzer = GitHubRepositoryAnalyzer(
            github_token=settings.github_token
        )
        
        # Initialize Kibana service
        logger.info("Initializing Kibana service...")
        app_state.kibana_service = KibanaService(
            kibana_url=settings.kibana_url,
            username=settings.kibana_username,
            password=settings.kibana_password
        )
        
        # Initialize agent orchestrator
        logger.info("Initializing agent orchestrator...")
        app_state.orchestrator = AgentOrchestrator(
            db_manager=app_state.db_manager,
            cache_manager=app_state.cache_manager,
            ai_manager=app_state.ai_manager
        )
        await app_state.orchestrator.start()
        
        # Initialize learning engine
        logger.info("Initializing learning engine...")
        app_state.learning_engine = LearningEngine(
            db_manager=app_state.db_manager,
            cache_manager=app_state.cache_manager
        )
        await app_state.learning_engine.initialize()
        
        # Initialize metrics collector
        logger.info("Initializing metrics collector...")
        app_state.metrics = MetricsCollector(
            db_manager=app_state.db_manager,
            cache_manager=app_state.cache_manager
        )
        
        # Set ready flag
        app_state.is_ready = True
        
        logger.info("✓ YMERA Enterprise Platform started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down YMERA Enterprise Platform...")
        
        try:
            # Stop orchestrator
            if app_state.orchestrator:
                await app_state.orchestrator.stop()
            
            # Close connections
            if app_state.db_manager:
                await app_state.db_manager.disconnect()
            
            if app_state.cache_manager:
                await app_state.cache_manager.disconnect()
            
            if app_state.ai_manager:
                await app_state.ai_manager.cleanup()
            
            logger.info("✓ Shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {str(e)}", exc_info=True)

# Create FastAPI application
app = FastAPI(
    title="YMERA Enterprise Platform",
    description="Production-ready code analysis and AI platform",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"]
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted host
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

# Performance monitoring middleware
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    """Track request processing time"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 5.0:  # 5 seconds
        logger.warning(
            f"Slow request detected: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration": process_time
            }
        )
    
    # Record metrics
    if app_state.metrics and app_state.is_ready:
        await app_state.metrics.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time
        )
    
    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(
        f"Validation error: {request.url.path}",
        extra={"errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(YMERAException)
async def ymera_exception_handler(request: Request, exc: YMERAException):
    """Handle custom YMERA exceptions"""
    logger.error(
        f"YMERA exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code if hasattr(exc, 'status_code') else status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "detail": str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    # Don't expose internal errors in production
    detail = str(exc) if settings.environment != "production" else "Internal server error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    if not app_state.is_ready or not app_state.db_manager:
        raise YMERAException("Database not initialized")
    return app_state.db_manager

def get_cache_manager() -> RedisCacheManager:
    """Get cache manager instance"""
    if not app_state.is_ready or not app_state.cache_manager:
        raise YMERAException("Cache not initialized")
    return app_state.cache_manager

def get_auth_manager() -> AuthManager:
    """Get auth manager instance"""
    if not app_state.is_ready or not app_state.auth_manager:
        raise YMERAException("Auth manager not initialized")
    return app_state.auth_manager

def get_ai_manager() -> MultiLLMManager:
    """Get AI manager instance"""
    if not app_state.is_ready or not app_state.ai_manager:
        raise YMERAException("AI manager not initialized")
    return app_state.ai_manager

def get_orchestrator() -> AgentOrchestrator:
    """Get agent orchestrator instance"""
    if not app_state.is_ready or not app_state.orchestrator:
        raise YMERAException("Orchestrator not initialized")
    return app_state.orchestrator

def get_learning_engine() -> LearningEngine:
    """Get learning engine instance"""
    if not app_state.is_ready or not app_state.learning_engine:
        raise YMERAException("Learning engine not initialized")
    return app_state.learning_engine

def get_github_analyzer() -> GitHubRepositoryAnalyzer:
    """Get GitHub analyzer instance"""
    if not app_state.is_ready or not app_state.github_analyzer:
        raise YMERAException("GitHub analyzer not initialized")
    return app_state.github_analyzer

def get_kibana_service() -> KibanaService:
    """Get Kibana service instance"""
    if not app_state.is_ready or not app_state.kibana_service:
        raise YMERAException("Kibana service not initialized")
    return app_state.kibana_service

def get_metrics() -> MetricsCollector:
    """Get metrics collector instance"""
    if not app_state.is_ready or not app_state.metrics:
        raise YMERAException("Metrics collector not initialized")
    return app_state.metrics

# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

# Register analysis routes
app.include_router(analysis_router)

# Register chat routes
app.include_router(chat_router)

# Register AI and integration routes
for router in get_all_routers():
    app.include_router(router)

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint - API information"""
    return {
        "name": "YMERA Enterprise Platform",
        "version": "2.0.0",
        "status": "operational" if app_state.is_ready else "initializing",
        "documentation": "/api/docs",
        "health": "/health"
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Comprehensive health check endpoint for load balancers and monitoring.
    """
    if not app_state.is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unavailable",
                "message": "System initializing",
                "timestamp": time.time()
            }
        )
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0",
        "components": {}
    }
    
    # Check database
    try:
        await app_state.db_manager.health_check()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check cache
    try:
        await app_state.cache_manager.health_check()
        health_status["components"]["cache"] = "healthy"
    except Exception as e:
        health_status["components"]["cache"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check AI services
    try:
        ai_health = await app_state.ai_manager.health_check()
        health_status["components"]["ai_services"] = ai_health
    except Exception as e:
        health_status["components"]["ai_services"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check orchestrator
    try:
        orchestrator_health = await app_state.orchestrator.health_check()
        health_status["components"]["orchestrator"] = orchestrator_health
    except Exception as e:
        health_status["components"]["orchestrator"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = (
        status.HTTP_200_OK if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    
    return JSONResponse(status_code=status_code, content=health_status)

@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Readiness check for Kubernetes and container orchestration.
    """
    if app_state.is_ready:
        return {
            "ready": True,
            "timestamp": time.time()
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ready": False,
                "message": "System not ready",
                "timestamp": time.time()
            }
        )

@app.get("/metrics", status_code=status.HTTP_200_OK)
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint.
    Returns metrics in Prometheus exposition format.
    """
    if not app_state.is_ready or not app_state.metrics:
        return ""
    
    try:
        metrics_data = await app_state.metrics.get_prometheus_metrics()
        return metrics_data
    except Exception as e:
        logger.error(f"Failed to generate metrics: {str(e)}")
        return ""

# ============================================================================
# CONFIGURATION AND STARTUP
# ============================================================================

def create_app() -> FastAPI:
    """Factory function to create configured app instance"""
    return app

# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True,
        workers=1 if settings.environment == "development" else settings.workers,
        loop="uvloop",
        http="httptools",
        proxy_headers=True,
        forwarded_allow_ips="*"
    )