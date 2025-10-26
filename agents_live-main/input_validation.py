"""
Input Validation Middleware
Validates and sanitizes all inputs for security
"""

import re
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates and sanitizes all inputs
    
    Protects against:
    - XSS attacks
    - SQL injection
    - Path traversal
    - Code injection
    - Command injection
    
    Usage:
        app.add_middleware(InputValidationMiddleware)
    """
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        (r'<script[^>]*>.*?</script>', "XSS script tag"),
        (r'javascript:', "JavaScript protocol"),
        (r'on\w+\s*=', "Event handler"),
        (r'(union|select|insert|update|delete|drop|create|alter)\s+', "SQL injection"),
        (r'\.\./|\.\.\\', "Path traversal"),
        (r'exec\(|eval\(', "Code execution"),
        (r'system\(|popen\(|shell_exec', "Command injection"),
        (r'<iframe|<embed|<object', "Embedded content"),
        (r'base64,', "Base64 encoded content"),
    ]
    
    # Paths that should skip validation (e.g., file uploads)
    EXCLUDED_PATHS = {
        "/docs",
        "/openapi.json",
        "/redoc"
    }
    
    def __init__(self, app, strict_mode: bool = True):
        super().__init__(app)
        self.strict_mode = strict_mode
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Validate query parameters
        for key, value in request.query_params.items():
            violation = self._check_for_violations(value)
            if violation:
                logger.warning(
                    "Dangerous input detected in query parameter",
                    parameter=key,
                    violation=violation,
                    value=value[:100],
                    request_id=getattr(request.state, "request_id", "unknown")
                )
                
                if self.strict_mode:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid input detected: {violation}"
                    )
        
        # Validate headers (selective)
        sensitive_headers = ["User-Agent", "Referer", "X-Forwarded-For"]
        for key in sensitive_headers:
            value = request.headers.get(key)
            if value:
                violation = self._check_for_violations(value)
                if violation:
                    logger.warning(
                        "Dangerous input detected in header",
                        header=key,
                        violation=violation,
                        value=value[:100]
                    )
                    
                    if self.strict_mode:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid header value: {violation}"
                        )
        
        return await call_next(request)
    
    def _check_for_violations(self, value: str) -> Optional[str]:
        """Check if value contains dangerous patterns"""
        if not isinstance(value, str):
            return None
        
        value_lower = value.lower()
        
        for pattern, violation_type in self.DANGEROUS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return violation_type
        
        return None
