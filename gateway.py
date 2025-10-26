# api/gateway.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.routing import APIRoute
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import json
import yaml
import uuid
from cachetools import TTLCache
import httpx
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

class EnterpriseAPIGateway:
    """Enterprise API Gateway with advanced management features"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.version_manager = APIVersionManager()
        self.rate_limiter = RateLimiter()
        self.transformer = RequestResponseTransformer()
        self.monetization = APIMonetization()
        self.developer_portal = DeveloperPortal()
        self.cache = TTLCache(maxsize=1000, ttl=300)
        self._setup_gateway()
    
    def _setup_gateway(self):
        """Setup API gateway middleware and routes"""
        # Add gateway middleware
        self.app.middleware("http")(self._gateway_middleware)
        
        # Add custom routes for gateway functionality
        self._add_gateway_routes()
        
        # Custom OpenAPI documentation
        self._customize_openapi()
    
    async def _gateway_middleware(self, request: Request, call_next):
        """Main gateway middleware"""
        # Start timing for performance metrics
        start_time = datetime.utcnow()
        
        # Extract API version from request
        api_version = self._extract_api_version(request)
        
        # Check rate limits
        if not await self.rate_limiter.check_rate_limit(request, api_version):
            return Response(
                content=json.dumps({"error": "Rate limit exceeded"}),
                status_code=429,
                headers={"Retry-After": "60"}
            )
        
        # Apply API version transformations
        transformed_request = await self.transformer.transform_request(request, api_version)
        
        # Check monetization (for paid APIs)
        if await self.monetization.requires_payment(request):
            if not await self.monetization.validate_payment(request):
                return Response(
                    content=json.dumps({"error": "Payment required"}),
                    status_code=402
                )
        
        # Process request through chain
        response = await call_next(transformed_request)
        
        # Apply response transformations
        transformed_response = await self.transformer.transform_response(response, api_version)
        
        # Log analytics
        await self._log_api_analytics(request, transformed_response, start_time, api_version)
        
        return transformed_response
    
    def _extract_api_version(self, request: Request) -> str:
        """Extract API version from request"""
        # Check URL path first
        path_parts = request.url.path.split('/')
        if len(path_parts) > 2 and path_parts[1].startswith('v'):
            return path_parts[1]
        
        # Check headers
        version_header = request.headers.get('X-API-Version')
        if version_header and version_header.startswith('v'):
            return version_header
        
        # Check query parameter
        version_param = request.query_params.get('api_version')
        if version_param and version_param.startswith('v'):
            return version_param
        
        # Default to latest stable version
        return self.version_manager.get_latest_stable_version()
    
    def _add_gateway_routes(self):
        """Add gateway-specific routes"""
        
        @self.app.get("/api/versions", tags=["API Gateway"])
        async def get_api_versions():
            """Get available API versions"""
            return self.version_manager.get_available_versions()
        
        @self.app.get("/api/docs", include_in_schema=False)
        async def custom_swagger_ui_html():
            """Custom Swagger UI with versioning"""
            return get_swagger_ui_html(
                openapi_url=f"/api/openapi.json",
                title="YMERA Enterprise API - Developer Portal",
                swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
                swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            )
        
        @self.app.get("/api/openapi.json", include_in_schema=False)
        async def get_openapi_schema():
            """Custom OpenAPI schema with versioning"""
            return self._generate_openapi_schema()
        
        @self.app.get("/api/health/gateway", tags=["API Gateway"])
        async def gateway_health():
            """Gateway health check"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "rate_limiter": await self.rate_limiter.health_check(),
                    "version_manager": await self.version_manager.health_check(),
                    "transformer": await self.transformer.health_check()
                }
            }
    
    def _generate_openapi_schema(self):
        """Generate customized OpenAPI schema"""
        openapi_schema = get_openapi(
            title="YMERA Enterprise API",
            version="2.0.0",
            description="Enterprise-grade project management and analytics API",
            routes=self.app.routes,
        )
        
        # Add customizations
        openapi_schema["info"]["x-logo"] = {
            "url": "https://ymera.example.com/logo.png",
            "backgroundColor": "#FFFFFF"
        }
        
        openapi_schema["servers"] = [
            {
                "url": "https://api.ymera.example.com/v2",
                "description": "Production API v2"
            },
            {
                "url": "https://api.ymera.example.com/v1",
                "description": "Production API v1 (deprecated)"
            }
        ]
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
        
        return openapi_schema
    
    async def _log_api_analytics(self, request: Request, response: Response, 
                               start_time: datetime, api_version: str):
        """Log API analytics for monitoring and billing"""
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms
        
        analytics_data = {
            "request_id": str(uuid.uuid4()),
            "timestamp": start_time.isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "api_version": api_version,
            "status_code": response.status_code,
            "duration_ms": duration,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_length": response.headers.get("content-length", 0),
            "rate_limit_info": await self.rate_limiter.get_rate_limit_info(request),
            "monetization_data": await self.monetization.get_billing_data(request)
        }
        
        # Send to analytics pipeline
        await self._send_to_analytics(analytics_data)

class APIVersionManager:
    """API version management with deprecation support"""
    
    def __init__(self):
        self.versions = {
            "v2": {
                "status": "current",
                "release_date": "2024-01-15",
                "end_of_life": "2025-01-15",
                "docs_url": "https://docs.ymera.example.com/v2"
            },
            "v1": {
                "status": "deprecated",
                "release_date": "2023-06-10",
                "end_of_life": "2024-06-10",
                "docs_url": "https://docs.ymera.example.com/v1",
                "deprecation_notice": "Migrate to v2 by June 10, 2024"
            }
        }
    
    def get_available_versions(self) -> Dict[str, Any]:
        """Get available API versions"""
        return self.versions
    
    def get_latest_stable_version(self) -> str:
        """Get latest stable version"""
        for version, info in self.versions.items():
            if info["status"] == "current":
                return version
        return "v2"  # Fallback
    
    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported"""
        return version in self.versions
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if version is deprecated"""
        return self.versions.get(version, {}).get("status") == "deprecated"
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for version manager"""
        return {
            "status": "healthy",
            "supported_versions": list(self.versions.keys()),
            "latest_version": self.get_latest_stable_version()
        }

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.redis = None  # Will be initialized in async init
        self.rate_limits = {
            "free": {"requests": 100, "period": 3600},  # 100 req/hour
            "basic": {"requests": 1000, "period": 3600},  # 1000 req/hour
            "professional": {"requests": 10000, "period": 3600},  # 10k req/hour
            "enterprise": {"requests": 100000, "period": 3600},  # 100k req/hour
            "unlimited": {"requests": 0, "period": 0}  # Unlimited
        }
    
    async def check_rate_limit(self, request: Request, api_version: str) -> bool:
        """Check rate limit for request"""
        client_id = self._get_client_id(request)
        plan = await self._get_client_plan(client_id)
        
        rate_limit = self.rate_limits.get(plan, self.rate_limits["free"])
        
        if rate_limit["requests"] == 0:  # Unlimited
            return True
        
        key = f"rate_limit:{client_id}:{api_version}"
        current = await self.redis.get(key)
        
        if current and int(current) >= rate_limit["requests"]:
            return False
        
        # Increment counter
        await self.redis.incr(key)
        if not current:
            await self.redis.expire(key, rate_limit["period"])
        
        return True
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # API key takes precedence
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Then JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = SecurityUtils.verify_jwt(token)
                return f"user:{payload.get('sub')}"
            except:
                pass
        
        # Fallback to IP address (least preferred)
        return f"ip:{request.client.host}" if request.client else "anonymous"
    
    async def _get_client_plan(self, client_id: str) -> str:
        """Get client's rate limit plan"""
        # Implementation would check database or cache
        # For now, return based on client type
        if client_id.startswith("api_key:"):
            return "professional"
        elif client_id.startswith("user:"):
            return "basic"
        else:
            return "free"
    
    async def get_rate_limit_info(self, request: Request) -> Dict[str, Any]:
        """Get rate limit information for client"""
        client_id = self._get_client_id(request)
        plan = await self._get_client_plan(client_id)
        rate_limit = self.rate_limits[plan]
        
        key = f"rate_limit:{client_id}:v2"  # Using latest version
        current = int(await self.redis.get(key) or 0)
        
        return {
            "plan": plan,
            "limit": rate_limit["requests"],
            "remaining": max(0, rate_limit["requests"] - current),
            "reset_in": await self.redis.ttl(key),
            "period": rate_limit["period"]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for rate limiter"""
        try:
            await self.redis.ping()
            return {"status": "healthy", "redis": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}

class RequestResponseTransformer:
    """Request/response transformation for API versioning"""
    
    async def transform_request(self, request: Request, api_version: str) -> Request:
        """Transform request based on API version"""
        # Store original request for reference
        request.state.original_url = str(request.url)
        request.state.api_version = api_version
        
        # Apply version-specific transformations
        if api_version == "v1":
            request = await self._transform_v1_request(request)
        elif api_version == "v2":
            request = await self._transform_v2_request(request)
        
        return request
    
    async def transform_response(self, response: Response, api_version: str) -> Response:
        """Transform response based on API version"""
        # Apply version-specific response transformations
        if api_version == "v1":
            response = await self._transform_v1_response(response)
        elif api_version == "v2":
            response = await self._transform_v2_response(response)
        
        # Add API version headers
        response.headers["X-API-Version"] = api_version
        response.headers["X-API-Deprecated"] = "true" if self._is_deprecated(api_version) else "false"
        
        return response
    
    async def _transform_v1_request(self, request: Request) -> Request:
        """Transform requests for v1 API"""
        # Example: Convert old field names to new ones
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.json()
            transformed_body = self._transform_v1_body(body)
            
            # Create new request with transformed body
            request._body = json.dumps(transformed_body).encode()
            request.headers.__dict__["_list"] = [
                (b"content-length", str(len(request._body)).encode()),
                *[(k, v) for k, v in request.headers.items() if k.lower() != b"content-length"]
            ]
        
        return request
    
    async def _transform_v2_request(self, request: Request) -> Request:
        """Transform requests for v2 API"""
        # v2 is current, so minimal transformations
        return request
    
    def _transform_v1_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Transform v1 request body to current format"""
        transformations = {
            "project_name": "name",
            "project_desc": "description",
            "task_assignee": "assigned_to",
            "task_priority_level": "priority"
        }
        
        transformed = {}
        for key, value in body.items():
            new_key = transformations.get(key, key)
            transformed[new_key] = value
        
        return transformed
    
    async def _transform_v1_response(self, response: Response) -> Response:
        """Transform responses for v1 API"""
        # Convert modern response format to v1 format
        if response.headers.get("content-type") == "application/json":
            body = json.loads(response.body)
            transformed_body = self._transform_v1_response_body(body)
            
            response.body = json.dumps(transformed_body).encode()
            response.headers["content-length"] = str(len(response.body))
        
        return response
    
    def _transform_v1_response_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Transform response body to v1 format"""
        transformations = {
            "name": "project_name",
            "description": "project_desc",
            "assigned_to": "task_assignee",
            "priority": "task_priority_level"
        }
        
        transformed = {}
        for key, value in body.items():
            new_key = transformations.get(key, key)
            transformed[new_key] = value
        
        return transformed
    
    def _is_deprecated(self, api_version: str) -> bool:
        """Check if API version is deprecated"""
        return api_version == "v1"  # Example
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for transformer"""
        return {"status": "healthy", "transformations_available": ["v1", "v2"]}

class APIMonetization:
    """API monetization and billing management"""
    
    def __init__(self):
        self.plans = {
            "free": {
                "price": 0,
                "features": ["100 requests/hour", "Basic analytics", "Community support"],
                "rate_limit": "free"
            },
            "basic": {
                "price": 49,
                "features": ["1,000 requests/hour", "Advanced analytics", "Email support"],
                "rate_limit": "basic"
            },
            "professional": {
                "price": 199,
                "features": ["10,000 requests/hour", "Premium analytics", "Priority support", "API keys"],
                "rate_limit": "professional"
            },
            "enterprise": {
                "price": 999,
                "features": ["100,000 requests/hour", "Custom analytics", "24/7 support", "SLA guarantee"],
                "rate_limit": "enterprise"
            }
        }
    
    async def requires_payment(self, request: Request) -> bool:
        """Check if request requires payment"""
        # Free endpoints don't require payment
        if self._is_free_endpoint(request):
            return False
        
        # Check if client has a paid plan
        client_id = self._get_client_id(request)
        plan = await self._get_client_plan(client_id)
        
        return plan != "free"
    
    async def validate_payment(self, request: Request) -> bool:
        """Validate payment for request"""
        client_id = self._get_client_id(request)
        
        # Check if client has active subscription
        has_active_sub = await self._check_active_subscription(client_id)
        
        # Check credit balance for pay-as-you-go
        has_sufficient_credit = await self._check_credit_balance(client_id)
        
        return has_active_sub or has_sufficient_credit
    
    def _is_free_endpoint(self, request: Request) -> bool:
        """Check if endpoint is free"""
        free_endpoints = [
            ("GET", "/api/health"),
            ("GET", "/api/versions"),
            ("GET", "/api/docs"),
            ("GET", "/api/openapi.json")
        ]
        
        return (request.method, request.url.path) in free_endpoints
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier"""
        # Similar to rate limiter implementation
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = SecurityUtils.verify_jwt(token)
                return f"user:{payload.get('sub')}"
            except:
                pass
        
        return f"ip:{request.client.host}" if request.client else "anonymous"
    
    async def _get_client_plan(self, client_id: str) -> str:
        """Get client's plan"""
        # Implementation would check database
        if client_id.startswith("api_key:"):
            return "professional"
        elif client_id.startswith("user:"):
            return "basic"
        else:
            return "free"
    
    async def _check_active_subscription(self, client_id: str) -> bool:
        """Check if client has active subscription"""
        # Implementation would check subscription database
        return True  # Placeholder
    
    async def _check_credit_balance(self, client_id: str) -> bool:
        """Check if client has sufficient credit"""
        # Implementation would check credit balance
        return True  # Placeholder
    
    async def get_billing_data(self, request: Request) -> Dict[str, Any]:
        """Get billing data for analytics"""
        client_id = self._get_client_id(request)
        plan = await self._get_client_plan(client_id)
        
        return {
            "client_id": client_id,
            "plan": plan,
            "price": self.plans[plan]["price"],
            "endpoint": request.url.path,
            "method": request.method
        }

class DeveloperPortal:
    """Developer portal for API consumers"""
    
    def __init__(self):
        self.documentation = self._load_documentation()
        self.sdk_repositories = {
            "python": "https://github.com/ymera/ymera-python-sdk",
            "javascript": "https://github.com/ymera/ymera-js-sdk",
            "java": "https://github.com/ymera/ymera-java-sdk",
            "go": "https://github.com/ymera/ymera-go-sdk",
            "csharp": "https://github.com/ymera/ymera-csharp-sdk"
        }
    
    def _load_documentation(self) -> Dict[str, Any]:
        """Load API documentation"""
        return {
            "quickstart": {
                "title": "Getting Started",
                "content": self._load_markdown_file("docs/quickstart.md")
            },
            "authentication": {
                "title": "Authentication",
                "content": self._load_markdown_file("docs/authentication.md")
            },
            "examples": {
                "title": "Code Examples",
                "content": self._load_markdown_file("docs/examples.md")
            },
            "best_practices": {
                "title": "Best Practices",
                "content": self._load_markdown_file("docs/best_practices.md")
            }
        }
    
    def _load_markdown_file(self, path: str) -> str:
        """Load markdown file content"""
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return f"Documentation not found: {path}"
    
    async def get_portal_data(self) -> Dict[str, Any]:
        """Get developer portal data"""
        return {
            "documentation": self.documentation,
            "sdks": self.sdk_repositories,
            "api_reference": "/api/docs",
            "support": {
                "email": "api-support@ymera.example.com",
                "slack": "https://ymera.slack.com/archives/api-support",
                "forum": "https://community.ymera.example.com"
            },
            "status": {
                "api_status": "https://status.ymera.example.com",
                "uptime": "99.99%",
                "incidents": []
            }
        }