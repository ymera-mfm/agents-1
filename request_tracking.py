"""
Request Tracking Middleware
Adds unique request IDs for distributed tracing
"""

import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Request tracking middleware - adds unique request ID to each request
    
    Features:
    - Generates or extracts request ID
    - Adds to request state and response headers
    - Binds to logger context for correlated logging
    - Tracks request timing
    
    Usage:
        app.add_middleware(RequestTrackingMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Bind to logger context
        logger = structlog.get_logger().bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path
        )
        request.state.logger = logger
        
        # Log request
        logger.info(
            "Request started",
            client=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent", "unknown")[:100]
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - request.state.start_time
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            # Log response
            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=f"{duration * 1000:.2f}",
                duration_seconds=f"{duration:.3f}"
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - request.state.start_time
            logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=f"{duration * 1000:.2f}"
            )
            raise
