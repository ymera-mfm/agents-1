
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
import redis.asyncio as redis
import time

from core.config import Settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.redis = redis.Redis.from_url(settings.redis_url)
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/auth") or request.url.path.startswith("/api/admin"):
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}"
            
            current_requests = await self.redis.lrange(key, 0, -1)
            current_time = time.time()
            
            # Remove expired requests
            pipeline = self.redis.pipeline()
            for req_time_str in current_requests:
                req_time = float(req_time_str)
                if current_time - req_time > self.settings.rate_limit_window:
                    pipeline.lrem(key, 1, req_time_str)
            await pipeline.execute()
            
            # Re-fetch after cleanup
            current_requests = await self.redis.lrange(key, 0, -1)
            
            if len(current_requests) >= self.settings.rate_limit_requests:
                return JSONResponse(
                    {"detail": "Rate limit exceeded"},
                    status_code=429
                )
            
            await self.redis.rpush(key, current_time)
            await self.redis.expire(key, self.settings.rate_limit_window)
        
        response = await call_next(request)
        return response

