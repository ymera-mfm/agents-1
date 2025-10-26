"""Security Middleware"""

import time
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from shared.config.settings import Settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and rate limiting"""
    
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.logger = structlog.get_logger(__name__)
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks"""
        try:
            # Add request ID
            request_id = f"req_{int(time.time() * 1000)}"
            request.state.request_id = request_id
            
            # Rate limiting (simple implementation)
            if self.settings.RATE_LIMIT_ENABLED:
                client_ip = request.client.host
                if not await self._check_rate_limit(client_ip):
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"error": "Rate limit exceeded"}
                    )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            self.logger.error(f"Security middleware error: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
    
    async def _check_rate_limit(self, client_ip: str) -> bool:
        """Check rate limit for client"""
        current_time = time.time()
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Remove old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if current_time - req_time < 60
        ]
        
        # Check limit
        if len(self.request_counts[client_ip]) >= self.settings.RATE_LIMIT_PER_MINUTE:
            return False
        
        # Add current request
        self.request_counts[client_ip].append(current_time)
        return True
