
"""
Advanced API Gateway for Multi-Agent Platform
Centralized entry point for external services, routing requests to appropriate agents,
and handling authentication, authorization, and rate limiting.
"""

import asyncio
import json
import time
import os
import logging
import uuid
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque

from aiohttp import web
from nats.aio.client import Client as NATSClient
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

# Assuming these are defined in a common utility or base agent
# For now, defining them here for self-containment
class AgentStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    OFFLINE = "offline"
    ERROR = "error"

@dataclass
class AgentConfig:
    name: str
    agent_type: str
    capabilities: List[str]
    nats_url: str
    postgres_url: Optional[str] = None
    redis_url: Optional[str] = None
    consul_url: Optional[str] = None
    log_level: str = "INFO"

@dataclass
class TaskRequest:
    task_id: str
    task_type: str
    sender_id: str
    payload: Dict[str, Any]
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskResponse:
    task_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: float = field(default_factory=time.time)

class APIGateway:
    """
    The Advanced API Gateway acts as the primary entry point for external clients
    to interact with the multi-agent platform. It handles:
    - Request routing to appropriate agents via NATS.
    - Authentication and Authorization (JWT-based).
    - Rate Limiting to protect backend agents.
    - Request validation and transformation.
    - Centralized error handling and logging.
    - Service discovery integration (via NATS/Consul).
    - Health checks and monitoring.
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.nats_client = NATSClient()
        self.http_app = web.Application()
        self.http_server = None
        self.http_port = int(os.getenv("HTTP_PORT", 8000))
        self.jwt_secret = os.getenv("JWT_SECRET", "super-secret-jwt-key")
        self.agent_routes: Dict[str, str] = {}
        self.rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.agent_presence: Dict[str, Dict] = {}
        self.db_pool = None # Added for database connection pool

        self._setup_routes()

    def _setup_logging(self):
        logger = logging.getLogger(self.config.name)
        logger.setLevel(self.config.log_level.upper())
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def _init_db_pool(self):
        if self.config.postgres_url:
            try:
                import asyncpg
                self.db_pool = await asyncpg.create_pool(self.config.postgres_url)
                self.logger.info("Database connection pool initialized.")
            except Exception as e:
                self.logger.error(f"Failed to connect to PostgreSQL: {e}")
        else:
            self.logger.warning("No PostgreSQL URL provided in config. Database features will be disabled.")

    def _setup_routes(self):
        self.http_app.router.add_post("/api/v1/auth/login", self._handle_login)
        self.http_app.router.add_post("/api/v1/agent/{agent_name}/{task_type}", self._handle_agent_task)
        self.http_app.router.add_get("/health", self._handle_health_check)
        self.http_app.router.add_get("/api/v1/agents/status", self._handle_agent_status)
        # Add more generic routes or dynamic routing based on configuration

        # Middleware for authentication and rate limiting
        self.http_app.middlewares.append(self._auth_middleware)
        self.http_app.middlewares.append(self._rate_limit_middleware)

    async def start(self):
        await self._connect_to_nats()
        await self._init_db_pool() # Initialize DB pool
        await self._subscribe_to_agent_presence()
        asyncio.create_task(self._start_http_server())
        self.logger.info(f"API Gateway started on port {self.http_port}")

    async def _connect_to_nats(self):
        try:
            await self.nats_client.connect(servers=[self.config.nats_url])
            self.logger.info(f"Connected to NATS at {self.config.nats_url}")
        except NoServersError as e:
            self.logger.error(f"Could not connect to NATS: {e}")
            # Exit or implement retry logic
            exit(1)
        except Exception as e:
            self.logger.error(f"NATS connection error: {e}")
            exit(1)

    async def _subscribe_to_agent_presence(self):
        # Subscribe to agent presence updates from the CommunicationAgent
        await self.nats_client.subscribe("agent.presence.update", cb=self._agent_presence_callback)
        self.logger.info("Subscribed to agent.presence.update")

    async def _agent_presence_callback(self, msg):
        try:
            data = json.loads(msg.data.decode())
            agent_id = data["agent_id"]
            status = data["status"]
            last_seen = data.get("timestamp", time.time())
            self.agent_presence[agent_id] = {"status": status, "last_seen": last_seen}
            self.logger.debug(f"Agent presence update: {agent_id} is {status}")
        except Exception as e:
            self.logger.error(f"Error processing agent presence update: {e}")

    async def _start_http_server(self):
        runner = web.AppRunner(self.http_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.http_port)
        await site.start()
        self.logger.info(f"HTTP server running on http://0.0.0.0:{self.http_port}")

    async def _auth_middleware(self, app, handler):
        async def middleware_handler(request):
            # Skip authentication for login and health check endpoints
            if request.path in ["/api/v1/auth/login", "/health"] or request.path.startswith("/static/"):
                return await handler(request)

            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise web.HTTPUnauthorized(reason="Authorization header missing")

            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    decoded_token = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                    request["user"] = decoded_token # Attach user info to request
                except jwt.ExpiredSignatureError:
                    raise web.HTTPUnauthorized(reason="Token has expired")
                except jwt.InvalidTokenError:
                    raise web.HTTPUnauthorized(reason="Invalid token")
            elif auth_header.startswith("ApiKey "):
                api_key = auth_header.split(" ")[1]
                if not self.db_pool:
                    raise web.HTTPServiceUnavailable(reason="API Key authentication is currently unavailable.")
                try:
                    async with self.db_pool.acquire() as conn:
                        # A more secure implementation would hash the API key
                        api_key_record = await conn.fetchrow("SELECT * FROM api_keys WHERE api_key_hash = $1 AND is_active = TRUE", api_key)
                        if not api_key_record:
                            raise web.HTTPUnauthorized(reason="Invalid API Key")
                        # Attach user info from API key
                        user_record = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", api_key_record['user_id'])
                        request["user"] = {'user_id': str(user_record['user_id']), 'username': user_record['username']}
                        # Update last_used_at
                        await conn.execute("UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE api_key_id = $1", api_key_record['api_key_id'])
                except Exception as e:
                    self.logger.error(f"API Key validation error: {e}")
                    raise web.HTTPInternalServerError(reason="Error during API Key validation")
            else:
                raise web.HTTPUnauthorized(reason="Authorization header malformed")
            
            return await handler(request)
        return middleware_handler

    async def _rate_limit_middleware(self, app, handler):
        async def middleware_handler(request):
            # Apply rate limiting based on user ID or IP address
            client_id = request["user"]["user_id"] if "user" in request else request.remote
            current_time = time.time()

            # Clean up old timestamps
            while self.rate_limits[client_id] and self.rate_limits[client_id][0] < current_time - 60:
                self.rate_limits[client_id].popleft()
            
            # Max 100 requests per minute per client
            if len(self.rate_limits[client_id]) >= 100:
                raise web.HTTPTooManyRequests(reason="Rate limit exceeded")
                
            self.rate_limits[client_id].append(current_time)
            return await handler(request)
        return middleware_handler

    async def _handle_login(self, request):
        if not self.db_pool:
            return web.json_response({"error": "Authentication service is currently unavailable."}, status=503)
        try:
            data = await request.json()
            username = data.get("username")
            password = data.get("password")

            async with self.db_pool.acquire() as conn:
                user_record = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
                if user_record and user_record['password_hash'] == password: # In production, use a secure password hashing library like bcrypt
                    user_id = str(user_record['user_id'])
                    # Generate JWT token
                    payload = {
                        "user_id": user_id,
                        "username": username,
                        "exp": datetime.utcnow() + timedelta(hours=1)
                    }
                    token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
                    return web.json_response({"token": token})
                else:
                    raise web.HTTPUnauthorized(reason="Invalid credentials")
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return web.json_response({"error": str(e)}, status=400)

    async def _handle_agent_task(self, request):
        agent_name = request.match_info["agent_name"]
        task_type = request.match_info["task_type"]
        
        try:
            payload = await request.json()
            sender_id = request["user"]["user_id"] # Get user_id from authenticated token

            # Check if agent is active
            if agent_name not in self.agent_presence or self.agent_presence[agent_name]["status"] != AgentStatus.ACTIVE.value:
                raise web.HTTPServiceUnavailable(reason=f"Agent {agent_name} is not active or available.")

            # Create a TaskRequest object
            task_request = TaskRequest(
                task_id=str(uuid.uuid4()),
                task_type=task_type,
                sender_id=sender_id,
                payload=payload,
                metadata={
                    "source_ip": request.remote,
                    "request_path": request.path
                }
            )

            # Publish the task to the agent's NATS subject and wait for a response
            subject = f"agent.{agent_name}.task"
            self.logger.info(f"Sending task {task_request.task_id} to {subject}")
            
            try:
                # NATS request-reply pattern
                response_msg = await self.nats_client.request(
                    subject,
                    json.dumps(asdict(task_request)).encode(),
                    timeout=30 # Wait up to 30 seconds for agent response
                )
                response_data = json.loads(response_msg.data.decode())
                task_response = TaskResponse(**response_data)

                if task_response.success:
                    return web.json_response(task_response.result)
                else:
                    return web.json_response({"error": task_response.error}, status=500)
            except TimeoutError:
                self.logger.warning(f"Agent {agent_name} timed out responding to task {task_request.task_id}")
                raise web.HTTPGatewayTimeout(reason=f"Agent {agent_name} did not respond in time.")
            except ConnectionClosedError:
                self.logger.error(f"NATS connection closed while sending task to {agent_name}")
                raise web.HTTPServiceUnavailable(reason="Internal communication error.")

        except web.HTTPException:
            raise # Re-raise aiohttp HTTP exceptions
        except Exception as e:
            self.logger.error(f"Error handling agent task: {e}", exc_info=True)
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_health_check(self, request):
        # Check NATS connection status
        nats_status = "connected" if self.nats_client.is_connected else "disconnected"
        db_status = "connected" if self.db_pool else "disconnected"
        
        # Check agent statuses
        active_agents = {aid: info["status"] for aid, info in self.agent_presence.items() if info["status"] == AgentStatus.ACTIVE.value}

        return web.json_response({
            "status": "healthy",
            "nats_connection": nats_status,
            "database_connection": db_status,
            "active_agents": active_agents,
            "timestamp": time.time()
        })

    async def _handle_agent_status(self, request):
        return web.json_response({"agent_presence": self.agent_presence})

    async def stop(self):
        if self.nats_client.is_connected:
            await self.nats_client.close()
        if self.db_pool:
            await self.db_pool.close()
        if self.http_server:
            await self.http_app.shutdown()
            await self.http_app.cleanup()
        self.logger.info("API Gateway stopped.")


if __name__ == "__main__":
    # Example usage
    config = AgentConfig(
        name="api_gateway",
        agent_type="gateway",
        capabilities=["http_api", "nats_proxy", "auth", "rate_limiting"],
        nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"), # Added for DB connection
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )

    gateway = APIGateway(config)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(gateway.start())
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(gateway.stop())
    finally:
        loop.close()


