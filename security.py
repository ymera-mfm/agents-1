"""
Security Middleware
Implements security headers, rate limiting, and request validation
"""

import time
import hashlib
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses
    Implements OWASP recommended security headers
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server header (don't expose server version)
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limits request body size to prevent memory exhaustion attacks
    """
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": "Request entity too large",
                        "max_size_bytes": self.max_size,
                        "received_bytes": content_length
                    }
                )
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware
    Limits requests per IP address and per user
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Track requests by IP
        self.ip_requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/live", "/health/ready", "/metrics"]:
            return await call_next(request)
        
        # Current time
        now = datetime.utcnow()
        
        # Clean old requests (older than 1 hour)
        self.ip_requests[client_ip] = [
            req_time for req_time in self.ip_requests[client_ip]
            if now - req_time < timedelta(hours=1)
        ]
        
        # Check rate limits
        recent_requests = self.ip_requests[client_ip]
        
        # Requests in last minute
        last_minute = [
            req_time for req_time in recent_requests
            if now - req_time < timedelta(minutes=1)
        ]
        
        if len(last_minute) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded (per minute) for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "limit": "requests_per_minute",
                    "max_requests": self.requests_per_minute,
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Requests in last hour
        if len(recent_requests) >= self.requests_per_hour:
            logger.warning(f"Rate limit exceeded (per hour) for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "limit": "requests_per_hour",
                    "max_requests": self.requests_per_hour,
                    "retry_after": 3600
                },
                headers={"Retry-After": "3600"}
            )
        
        # Record this request
        self.ip_requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.requests_per_minute - len(last_minute)
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            self.requests_per_hour - len(recent_requests)
        )
        
        return response


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """
    Limits request processing time to prevent resource exhaustion
    """
    
    def __init__(self, app, timeout_seconds: int = 30):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(self, request: Request, call_next):
        import asyncio
        
        try:
            # Process request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            logger.error(f"Request timeout: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Request timeout",
                    "timeout_seconds": self.timeout_seconds,
                    "path": str(request.url.path)
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all requests and responses for audit trail
    """
    
    async def dispatch(self, request: Request, call_next):
        # Start time
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "client_ip": request.client.host if request.client else "unknown",
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params)
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "method": request.method,
                "path": request.url.path
            }
        )
        
        # Add response time header
        response.headers["X-Response-Time"] = f"{round(duration * 1000, 2)}ms"
        
        return response
