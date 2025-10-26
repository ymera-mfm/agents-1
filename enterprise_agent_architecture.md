# YMERA Enterprise Agent System
## Production-Ready Architecture with Genius Simplicity

### Core Philosophy
- **Progressive Enhancement**: Start with solid fundamentals, add complexity only when needed
- **Single Responsibility**: Each component has one clear purpose
- **Fail-Safe Design**: Graceful degradation when components fail
- **Observable by Default**: Built-in monitoring and debugging capabilities

---

## System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│  Agent Core     │────│  Data Layer     │
│   (FastAPI)     │    │  (AsyncIO)      │    │  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Auth Service   │    │  ML Pipeline    │    │  Cache Layer    │
│  (JWT + RBAC)   │    │  (Async Queue)  │    │  (Redis)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Phase 1: Core Foundation (Week 1-2)

### Database Schema
```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessions for JWT management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent experiences (core learning data)
CREATE TABLE agent_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    conversation_id UUID,
    input_data JSONB NOT NULL,
    output_data JSONB,
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
    metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge base
CREATE TABLE knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    tags VARCHAR(255)[],
    category VARCHAR(100),
    confidence_score FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- System metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_experiences_user_id ON agent_experiences(user_id);
CREATE INDEX idx_experiences_conversation_id ON agent_experiences(conversation_id);
CREATE INDEX idx_experiences_created_at ON agent_experiences(created_at);
CREATE INDEX idx_knowledge_category ON knowledge_items(category);
CREATE INDEX idx_knowledge_tags ON knowledge_items USING GIN(tags);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
```

### Core Agent Implementation
```python
# main.py - Main application entry point
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime

from core.agent import YmeraAgent
from core.database import Database
from core.auth import AuthService
from core.config import Settings
from api.routes import router
from middleware.monitoring import MetricsMiddleware
from middleware.rate_limiting import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global instances
settings = Settings()
agent = None
database = None
auth_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global agent, database, auth_service
    
    try:
        # Initialize core components
        database = Database(settings.database_url)
        await database.initialize()
        
        auth_service = AuthService(database, settings)
        await auth_service.initialize()
        
        agent = YmeraAgent(database, settings)
        await agent.initialize()
        
        logger.info("YMERA Agent System initialized successfully")
        yield
        
    finally:
        # Cleanup
        if agent:
            await agent.shutdown()
        if database:
            await database.close()
        logger.info("YMERA Agent System shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="YMERA Enterprise Agent System",
    version="1.0.0",
    description="Production-ready AI agent with enterprise features",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware, redis_url=settings.redis_url)

# Include routes
app.include_router(router, prefix="/api/v1")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "components": {
            "database": await database.health_check(),
            "agent": await agent.health_check(),
            "auth": await auth_service.health_check()
        }
    }
    
    # Check if any component is unhealthy
    if any(not status for status in health_status["components"].values()):
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=1 if settings.debug else 4
    )
```

### Configuration Management
```python
# core/config.py - Centralized configuration
from pydantic import BaseSettings, validator
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    allowed_hosts: List[str] = ["*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Agent Configuration
    max_conversation_history: int = 50
    learning_batch_size: int = 10
    model_update_interval: int = 3600
    
    @validator('database_url')
    def validate_database_url(cls, v):
        if not v:
            raise ValueError('DATABASE_URL is required')
        return v
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if not v:
            raise ValueError('JWT_SECRET_KEY is required')
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

---

## Phase 2: Core Agent Implementation

### Database Layer
```python
# core/database.py - Simple but robust database layer
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
import asyncpg
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'ymera_agent'
                }
            )
            logger.info("Database pool initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_query(self, query: str, *args) -> List[Dict]:
        """Execute query and return results"""
        async with self.get_connection() as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
                raise
    
    async def execute_single(self, query: str, *args) -> Optional[Dict]:
        """Execute query and return single result"""
        results = await self.execute_query(query, *args)
        return results[0] if results else None
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute command (INSERT, UPDATE, DELETE)"""
        async with self.get_connection() as conn:
            try:
                result = await conn.execute(command, *args)
                return result
            except Exception as e:
                logger.error(f"Command execution failed: {command[:100]}... Error: {e}")
                raise
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            await self.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed")

# core/models.py - Data models
from pydantic import BaseModel, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID

class User(BaseModel):
    id: Optional[UUID] = None
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    @validator('email')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v.lower()

class Experience(BaseModel):
    id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    feedback_score: Optional[int] = None
    metadata: Dict[str, Any] = {}
    processed: bool = False
    created_at: Optional[datetime] = None
    
    @validator('feedback_score')
    def validate_feedback(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Feedback score must be between 1 and 5')
        return v

class KnowledgeItem(BaseModel):
    id: Optional[UUID] = None
    title: str
    content: str
    tags: List[str] = []
    category: Optional[str] = None
    confidence_score: float = 0.0
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Core Agent Logic
```python
# core/agent.py - Main agent implementation
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from uuid import UUID, uuid4

from .database import Database
from .models import Experience, KnowledgeItem
from .ml_pipeline import MLPipeline
from .knowledge_manager import KnowledgeManager

logger = logging.getLogger(__name__)

class YmeraAgent:
    def __init__(self, database: Database, settings):
        self.database = database
        self.settings = settings
        self.ml_pipeline = MLPipeline(settings)
        self.knowledge_manager = KnowledgeManager(database)
        self.is_initialized = False
        self.background_tasks = []
    
    async def initialize(self):
        """Initialize agent components"""
        try:
            await self.ml_pipeline.initialize()
            await self.knowledge_manager.initialize()
            
            # Start background tasks
            self.background_tasks.extend([
                asyncio.create_task(self._experience_processing_loop()),
                asyncio.create_task(self._knowledge_update_loop()),
                asyncio.create_task(self._metrics_collection_loop())
            ])
            
            self.is_initialized = True
            logger.info("Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            raise
    
    async def process_message(self, user_id: UUID, message: str, 
                            conversation_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Process incoming message and generate response"""
        if not self.is_initialized:
            raise RuntimeError("Agent not initialized")
        
        conversation_id = conversation_id or uuid4()
        
        try:
            # Create experience record
            experience = Experience(
                user_id=user_id,
                conversation_id=conversation_id,
                input_data={"message": message, "timestamp": datetime.utcnow().isoformat()},
                metadata={"source": "chat"}
            )
            
            # Get relevant knowledge
            relevant_knowledge = await self.knowledge_manager.search_knowledge(
                message, limit=5
            )
            
            # Generate response using ML pipeline
            response_data = await self.ml_pipeline.generate_response(
                message=message,
                context=relevant_knowledge,
                conversation_history=await self._get_conversation_history(conversation_id)
            )
            
            # Update experience with response
            experience.output_data = response_data
            
            # Store experience
            await self._store_experience(experience)
            
            return {
                "response": response_data.get("response", "I understand your message."),
                "conversation_id": str(conversation_id),
                "confidence": response_data.get("confidence", 0.8),
                "suggestions": response_data.get("suggestions", [])
            }
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return {
                "response": "I'm having trouble processing your message right now. Please try again.",
                "conversation_id": str(conversation_id),
                "confidence": 0.0,
                "error": True
            }
    
    async def provide_feedback(self, experience_id: UUID, score: int, 
                              comment: Optional[str] = None) -> bool:
        """Provide feedback on agent response"""
        try:
            query = """
                UPDATE agent_experiences 
                SET feedback_score = $1, 
                    metadata = metadata || $2,
                    updated_at = NOW()
                WHERE id = $3
            """
            
            metadata_update = {"feedback_comment": comment} if comment else {}
            
            await self.database.execute_command(
                query, score, json.dumps(metadata_update), experience_id
            )
            
            # Trigger learning update
            asyncio.create_task(self._trigger_learning_update())
            
            return True
            
        except Exception as e:
            logger.error(f"Feedback storage failed: {e}")
            return False
    
    async def _store_experience(self, experience: Experience):
        """Store experience in database"""
        query = """
            INSERT INTO agent_experiences (user_id, conversation_id, input_data, 
                                         output_data, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        
        result = await self.database.execute_single(
            query,
            experience.user_id,
            experience.conversation_id,
            json.dumps(experience.input_data),
            json.dumps(experience.output_data) if experience.output_data else None,
            json.dumps(experience.metadata)
        )
        
        return result["id"] if result else None
    
    async def _get_conversation_history(self, conversation_id: UUID, 
                                       limit: int = None) -> List[Dict]:
        """Get conversation history"""
        limit = limit or self.settings.max_conversation_history
        
        query = """
            SELECT input_data, output_data, created_at
            FROM agent_experiences
            WHERE conversation_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        
        results = await self.database.execute_query(query, conversation_id, limit)
        return list(reversed(results))  # Return in chronological order
    
    async def _experience_processing_loop(self):
        """Background loop to process unprocessed experiences"""
        while True:
            try:
                # Get unprocessed experiences
                experiences = await self._get_unprocessed_experiences()
                
                if experiences:
                    await self.ml_pipeline.batch_process_experiences(experiences)
                    await self._mark_experiences_processed([exp["id"] for exp in experiences])
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Experience processing loop failed: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _knowledge_update_loop(self):
        """Background loop to update knowledge base"""
        while True:
            try:
                await self.knowledge_manager.update_knowledge_scores()
                await asyncio.sleep(3600)  # Update every hour
                
            except Exception as e:
                logger.error(f"Knowledge update loop failed: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _metrics_collection_loop(self):
        """Background loop to collect and store metrics"""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(300)  # Collect every 5 minutes
                
            except Exception as e:
                logger.error(f"Metrics collection loop failed: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    async def health_check(self) -> bool:
        """Check agent health"""
        try:
            # Basic checks
            if not self.is_initialized:
                return False
            
            # Check components
            ml_healthy = await self.ml_pipeline.health_check()
            knowledge_healthy = await self.knowledge_manager.health_check()
            
            return ml_healthy and knowledge_healthy
            
        except Exception as e:
            logger.error(f"Agent health check failed: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown agent gracefully"""
        logger.info("Shutting down agent...")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Shutdown components
        await self.ml_pipeline.shutdown()
        await self.knowledge_manager.shutdown()
        
        logger.info("Agent shutdown complete")
```

---

## Phase 3: API Layer & Security

### Authentication Service
```python
# core/auth.py - JWT-based authentication
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, status
from passlib.context import CryptContext
import logging
from uuid import UUID
import json

from .database import Database
from .models import User

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, database: Database, settings):
        self.database = database
        self.settings = settings
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize authentication service"""
        self.is_initialized = True
        logger.info("Authentication service initialized")
    
    async def create_user(self, email: str, password: str, 
                         first_name: Optional[str] = None,
                         last_name: Optional[str] = None) -> User:
        """Create new user"""
        # Check if user exists
        existing = await self.database.execute_single(
            "SELECT id FROM users WHERE email = $1", email
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        
        # Hash password
        password_hash = self.pwd_context.hash(password)
        
        # Create user
        query = """
            INSERT INTO users (email, password_hash, first_name, last_name)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, first_name, last_name, role, is_active, created_at
        """
        
        result = await self.database.execute_single(
            query, email, password_hash, first_name, last_name
        )
        
        return User(**result)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        user_data = await self.database.execute_single(
            "SELECT * FROM users WHERE email = $1 AND is_active = true", email
        )
        
        if not user_data:
            return None
        
        if not self.pwd_context.verify(password, user_data["password_hash"]):
            return None
        
        # Remove password hash from response
        user_data.pop("password_hash", None)
        return User(**user_data)
    
    async def create_access_token(self, user: User) -> Dict[str, str]:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.settings.jwt_expire_minutes)
        
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(
            payload, 
            self.settings.jwt_secret_key, 
            algorithm=self.settings.jwt_algorithm
        )
        
        # Store session
        session_id = await self._create_session(user.id, token, expire)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.settings.jwt_expire_minutes * 60,
            "session_id": session_id
        }
    
    async def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Check session
            user_id = UUID(payload["sub"])
            session = await self._verify_session(user_id, token)
            
            if not session:
                return None
            
            # Get user data
            user_data = await self.database.execute_single(
                "SELECT id, email, first_name, last_name, role, is_active FROM users WHERE id = $1 AND is_active = true",
                user_id
            )
            
            return User(**user_data) if user_data else None
            
        except jwt.PyJWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    async def revoke_token(self, user_id: UUID, token: str) -> bool:
        """Revoke user session"""
        try:
            await self.database.execute_command(
                "DELETE FROM user_sessions WHERE user_id = $1 AND session_token = $2",
                user_id, token
            )
            return True
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False
    
    async def _create_session(self, user_id: UUID, token: str, expires_at: datetime) -> str:
        """Create user session"""
        result = await self.database.execute_single(
            """
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            user_id, token, expires_at
        )
        return str(result["id"])
    
    async def _verify_session(self, user_id: UUID, token: str) -> bool:
        """Verify user session"""
        session = await self.database.execute_single(
            """
            SELECT id FROM user_sessions 
            WHERE user_id = $1 AND session_token = $2 AND expires_at > NOW()
            """,
            user_id, token
        )
        return session is not None
    
    async def health_check(self) -> bool:
        """Check auth service health"""
        return self.is_initialized
```

### API Routes
```python
# api/routes.py - All API endpoints
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from core.auth import AuthService
from core.agent import YmeraAgent
from core.models import User, Experience, KnowledgeItem

# Dependencies
security = HTTPBearer()
router = APIRouter()

# Request/Response models
class UserCreate(BaseModel):
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None

class FeedbackRequest(BaseModel):
    experience_id: UUID
    score: int
    comment: Optional[str] = None

class KnowledgeCreate(BaseModel):
    title: str
    content: str
    tags: List[str] = []
    category: Optional[str] = None

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    from main import auth_service
    
    user = await auth_service.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

async def get_agent() -> YmeraAgent:
    """Get agent instance"""
    from main import agent
    return agent

async def get_auth_service() -> AuthService:
    """Get auth service instance"""
    from main import auth_service
    return auth_service

# Authentication endpoints
@router.post("/auth/register", response_model=Dict[str, Any])
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register new user"""
    try:
        user = await auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        # Create access token
        token_data = await auth_service.create_access_token(user)
        
        return {
            "user": user.dict(),
            "token": token_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/auth/login", response_model=Dict[str, Any])
async def login_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """User login"""
    user = await auth_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token_data = await auth_service.create_access_token(user)
    
    return {
        "user": user.dict(),
        "token": token_data
    }

@router.post("/auth/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """User logout"""
    user = await get_current_user(credentials)
    
    success = await auth_service.revoke_token(user.id, credentials.credentials)
    
    return {"success": success}

# Chat endpoints
@router.post("/chat/message", response_model=Dict[str, Any])
async def send_message(
    message_data: ChatMessage,
    user: User = Depends(get_current_user),
    agent: YmeraAgent = Depends(get_agent)
):
    """Send message to agent"""
    try:
        response = await agent.process_message(
            user_id=user.id,
            message=message_data.message,
            conversation_id=message_data.conversation_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Message processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Message processing failed"
        )

@router.get("/chat/conversations", response_model=List[Dict[str, Any]])
async def get_conversations(
    user: User = Depends(get_current_user),
    agent: YmeraAgent = Depends(get_agent),
    limit: int = 20
):
    """Get user's recent conversations"""
    try:
        conversations = await agent.get_user_conversations(user.id, limit)
        return conversations
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )

@router.get("/chat/history/{conversation_id}", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    agent: YmeraAgent = Depends(get_agent)
):
    """Get conversation history"""
    try:
        history = await agent.get_conversation_history(conversation_id, user.id)
        return history
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )

# Feedback endpoints
@router.post("/feedback", response_model=Dict[str, bool])
async def provide_feedback(
    feedback_data: FeedbackRequest,
    user: User = Depends(get_current_user),
    agent: YmeraAgent = Depends(get_agent)
):
    """Provide feedback on agent response"""
    try:
        success = await agent.provide_feedback(
            experience_id=feedback_data.experience_id,
            score=feedback_data.score,
            comment=feedback_data.comment
        )
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Feedback processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Feedback processing failed"
        )

# Knowledge management endpoints
@router.post("/knowledge", response_model=Dict[str, Any])
async def create_knowledge_item(
    knowledge_data: KnowledgeCreate,
    user: User = Depends(get_current_user),
    agent: YmeraAgent = Depends(get_agent)
):
    """Create new knowledge item (admin only)"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        knowledge_item = await agent.knowledge_manager.create_knowledge_item(
            title=knowledge_data.title,
            content=knowledge_data.content,
            tags=knowledge_data.tags,
            category=knowledge_data.category
        )
        
        return knowledge_item.dict()
        
    except Exception as e:
        logger.error(f"Knowledge creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Knowledge creation failed"
        )

@router.get("/knowledge/search", response_model=List[Dict[str, Any]])
async def search_knowledge(
    query: str,
    user: User = Depends(get_current_user),
    agent: YmeraAgent = Depends(get_agent),
    limit: int = 10
):
    """Search knowledge base"""
    try:
        results = await agent.knowledge_manager.search_knowledge(query, limit)
        return results
        
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Knowledge search failed"
        )

@router.get("/knowledge/{knowledge_id}", response_model=Dict[str, Any])
async def get_knowledge_item(
    knowledge_id: UUID,
    user: User = Depends(get_current_user),
    agent: YmeraAgent = Depends(get_agent)
):
    """Get specific knowledge item"""
    try:
        item = await agent.knowledge_manager.get_knowledge_item(knowledge_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge item not found"
            )
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Knowledge retrieval failed"
        )

# Analytics endpoints (admin only)
@router.get("/analytics/usage", response_model=Dict[str, Any])
async def get_usage_analytics(
    user: User = Depends(get_current_user),
    days: int = 7
):
    """Get usage analytics (admin only)"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from main import database
    
    try:
        # Get usage statistics
        query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as message_count,
                COUNT(DISTINCT user_id) as unique_users,
                AVG(CASE WHEN feedback_score IS NOT NULL THEN feedback_score ELSE NULL END) as avg_feedback
            FROM agent_experiences
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """ % days
        
        results = await database.execute_query(query)
        
        return {
            "period_days": days,
            "daily_stats": results,
            "total_messages": sum(row["message_count"] for row in results),
            "avg_daily_users": sum(row["unique_users"] for row in results) / len(results) if results else 0
        }
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analytics retrieval failed"
        )

@router.get("/analytics/performance", response_model=Dict[str, Any])
async def get_performance_analytics(
    user: User = Depends(get_current_user)
):
    """Get system performance analytics (admin only)"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from main import database
    
    try:
        # Get recent performance metrics
        query = """
            SELECT 
                metric_name,
                AVG(metric_value) as avg_value,
                MAX(metric_value) as max_value,
                MIN(metric_value) as min_value,
                COUNT(*) as sample_count
            FROM system_metrics
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY metric_name
        """
        
        results = await database.execute_query(query)
        
        return {
            "metrics": {row["metric_name"]: {
                "avg": row["avg_value"],
                "max": row["max_value"],
                "min": row["min_value"],
                "samples": row["sample_count"]
            } for row in results},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance analytics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Performance analytics retrieval failed"
        )

# User management endpoints
@router.get("/users/me", response_model=Dict[str, Any])
async def get_current_user_profile(
    user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return user.dict()

@router.put("/users/me", response_model=Dict[str, Any])
async def update_user_profile(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Update current user profile"""
    from main import database
    
    try:
        # Build update query
        updates = []
        params = []
        param_count = 1
        
        if first_name is not None:
            updates.append(f"first_name = ${param_count}")
            params.append(first_name)
            param_count += 1
        
        if last_name is not None:
            updates.append(f"last_name = ${param_count}")
            params.append(last_name)
            param_count += 1
        
        if not updates:
            return user.dict()  # No changes
        
        query = f"""
            UPDATE users 
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE id = ${param_count}
            RETURNING id, email, first_name, last_name, role, is_active, created_at
        """
        params.append(user.id)
        
        result = await database.execute_single(query, *params)
        
        return User(**result).dict()
        
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

---

## Phase 4: ML Pipeline & Knowledge Management

### Simple but Effective ML Pipeline
```python
# core/ml_pipeline.py - Lightweight ML processing
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

logger = logging.getLogger(__name__)

class MLPipeline:
    def __init__(self, settings):
        self.settings = settings
        self.vectorizer = None
        self.response_templates = {}
        self.knowledge_vectors = None
        self.is_initialized = False
        
        # Simple response templates for different intents
        self.default_responses = {
            "greeting": [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Welcome! How may I assist you?"
            ],
            "question": [
                "That's an interesting question. Let me help you with that.",
                "Based on what I know, here's what I can tell you:",
                "Great question! Here's my understanding:"
            ],
            "request": [
                "I'll help you with that request.",
                "Let me assist you with this.",
                "I'll do my best to help you."
            ],
            "default": [
                "I understand what you're asking about.",
                "Let me provide you with some information.",
                "I'll help you with that."
            ]
        }
    
    async def initialize(self):
        """Initialize ML components"""
        try:
            # Initialize TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )
            
            # Load or create knowledge vectors
            await self._initialize_knowledge_vectors()
            
            self.is_initialized = True
            logger.info("ML Pipeline initialized")
            
        except Exception as e:
            logger.error(f"ML Pipeline initialization failed: {e}")
            raise
    
    async def generate_response(self, message: str, context: List[Dict] = None,
                               conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Generate response to user message"""
        try:
            # Detect intent (simplified)
            intent = await self._detect_intent(message)
            
            # Find relevant context
            relevant_context = await self._find_relevant_context(message, context or [])
            
            # Generate response based on intent and context
            response = await self._generate_contextual_response(
                message, intent, relevant_context, conversation_history or []
            )
            
            # Calculate confidence score
            confidence = await self._calculate_confidence(message, relevant_context)
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(message, intent)
            
            return {
                "response": response,
                "intent": intent,
                "confidence": confidence,
                "suggestions": suggestions,
                "context_used": len(relevant_context) > 0
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now.",
                "intent": "error",
                "confidence": 0.0,
                "suggestions": [],
                "context_used": False
            }
    
    async def _detect_intent(self, message: str) -> str:
        """Simple intent detection"""
        message_lower = message.lower()
        
        # Greeting patterns
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        if any(greeting in message_lower for greeting in greetings):
            return "greeting"
        
        # Question patterns
        question_words = ["what", "how", "why", "when", "where", "who", "which", "can you"]
        if any(word in message_lower for word in question_words) or message.endswith("?"):
            return "question"
        
        # Request patterns
        request_words = ["please", "could you", "would you", "can you help", "i need", "i want"]
        if any(word in message_lower for word in request_words):
            return "request"
        
        return "default"
    
    async def _find_relevant_context(self, message: str, context: List[Dict]) -> List[Dict]:
        """Find relevant context using simple similarity"""
        if not context or not self.vectorizer:
            return []
        
        try:
            # Vectorize the message
            message_vector = self.vectorizer.transform([message])
            
            # Vectorize context items
            context_texts = [item.get("content", "") for item in context]
            if not context_texts:
                return []
            
            context_vectors = self.vectorizer.transform(context_texts)
            
            # Calculate similarities
            similarities = cosine_similarity(message_vector, context_vectors)[0]
            
            # Get top relevant items (similarity > 0.1)
            relevant_indices = [i for i, sim in enumerate(similarities) if sim > 0.1]
            relevant_indices.sort(key=lambda i: similarities[i], reverse=True)
            
            return [context[i] for i in relevant_indices[:3]]  # Top 3 relevant items
            
        except Exception as e:
            logger.error(f"Context finding failed: {e}")
            return []
    
    async def _generate_contextual_response(self, message: str, intent: str,
                                           relevant_context: List[Dict],
                                           conversation_history: List[Dict]) -> str:
        """Generate response using context"""
        # Get base response template
        templates = self.default_responses.get(intent, self.default_responses["default"])
        base_response = np.random.choice(templates)
        
        # If we have relevant context, incorporate it
        if relevant_context:
            context_info = relevant_context[0]  # Use the most relevant
            context_text = context_info.get("content", "")
            
            if len(context_text) > 200:
                context_text = context_text[:200] + "..."
            
            response = f"{base_response}\n\nBased on what I know: {context_text}"
        else:
            response = base_response
        
        return response
    
    async def _calculate_confidence(self, message: str, relevant_context: List[Dict]) -> float:
        """Calculate response confidence score"""
        base_confidence = 0.7
        
        # Increase confidence if we have relevant context
        if relevant_context:
            base_confidence += 0.2
        
        # Decrease confidence for very long or very short messages
        if len(message) < 5:
            base_confidence -= 0.2
        elif len(message) > 500:
            base_confidence -= 0.1
        
        return max(0.0, min(1.0, base_confidence))
    
    async def _generate_suggestions(self, message: str, intent: str) -> List[str]:
        """Generate helpful suggestions"""
        suggestions = []
        
        if intent == "greeting":
            suggestions = [
                "What would you like to know about?",
                "How can I help you today?",
                "Ask me any questions you have"
            ]
        elif intent == "question":
            suggestions = [
                "Would you like more details about this topic?",
                "Is there anything specific you'd like to know?",
                "Can I help clarify anything else?"
            ]
        elif intent == "request":
            suggestions = [
                "Is there anything else I can help you with?",
                "Would you like me to provide more information?",
                "Do you need help with something else?"
            ]
        
        return suggestions[:2]  # Return top 2 suggestions
    
    async def batch_process_experiences(self, experiences: List[Dict]):
        """Process a batch of experiences for learning"""
        try:
            # Simple learning: update response quality based on feedback
            for experience in experiences:
                feedback_score = experience.get("feedback_score")
                if feedback_score is not None:
                    await self._update_response_quality(experience, feedback_score)
            
            logger.info(f"Processed {len(experiences)} experiences")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
    
    async def _update_response_quality(self, experience: Dict, feedback_score: int):
        """Update response quality based on feedback"""
        # This is where you'd implement more sophisticated learning
        # For now, we'll just log the feedback for analysis
        input_data = experience.get("input_data", {})
        output_data = experience.get("output_data", {})
        
        logger.info(f"Feedback received: {feedback_score}/5 for response to '{input_data.get('message', '')}'")
    
    async def _initialize_knowledge_vectors(self):
        """Initialize knowledge vectors for similarity search"""
        try:
            # This would be populated with actual knowledge base content
            sample_knowledge = [
                "Welcome to our system. I'm here to help you with any questions.",
                "You can ask me about various topics and I'll do my best to help.",
                "If you need assistance, feel free to ask me anything."
            ]
            
            self.knowledge_vectors = self.vectorizer.fit_transform(sample_knowledge)
            logger.info("Knowledge vectors initialized")
            
        except Exception as e:
            logger.error(f"Knowledge vector initialization failed: {e}")
    
    async def health_check(self) -> bool:
        """Check ML pipeline health"""
        return self.is_initialized and self.vectorizer is not None
    
    async def shutdown(self):
        """Shutdown ML pipeline"""
        logger.info("ML Pipeline shutdown complete")

# core/knowledge_manager.py - Knowledge base management
class KnowledgeManager:
    def __init__(self, database):
        self.database = database
        self.is_initialized = False
        self.search_cache = {}
    
    async def initialize(self):
        """Initialize knowledge manager"""
        self.is_initialized = True
        logger.info("Knowledge Manager initialized")
    
    async def create_knowledge_item(self, title: str, content: str,
                                   tags: List[str] = None, category: str = None) -> KnowledgeItem:
        """Create new knowledge item"""
        query = """
            INSERT INTO knowledge_items (title, content, tags, category)
            VALUES ($1, $2, $3, $4)
            RETURNING id, title, content, tags, category, confidence_score, usage_count, created_at, updated_at
        """
        
        result = await self.database.execute_single(
            query, title, content, tags or [], category
        )
        
        return KnowledgeItem(**result)
    
    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
        """Search knowledge base"""
        # Simple text search - in production you'd use full-text search
        search_query = """
            SELECT id, title, content, tags, category, confidence_score, usage_count
            FROM knowledge_items
            WHERE 
                title ILIKE $1 
                OR content ILIKE $1
                OR $2 = ANY(tags)
            ORDER BY confidence_score DESC, usage_count DESC
            LIMIT $3
        """
        
        search_term = f"%{query}%"
        results = await self.database.execute_query(search_query, search_term, query, limit)
        
        # Update usage counts
        if results:
            ids = [result["id"] for result in results]
            await self._update_usage_counts(ids)
        
        return results
    
    async def get_knowledge_item(self, knowledge_id: UUID) -> Optional[Dict]:
        """Get specific knowledge item"""
        query = """
            SELECT id, title, content, tags, category, confidence_score, usage_count, created_at, updated_at
            FROM knowledge_items
            WHERE id = $1
        """
        
        result = await self.database.execute_single(query, knowledge_id)
        
        if result:
            # Update usage count
            await self._update_usage_counts([knowledge_id])
        
        return result
    
    async def update_knowledge_scores(self):
        """Update knowledge confidence scores based on usage and feedback"""
        # Simple scoring algorithm - you'd make this more sophisticated
        query = """
            UPDATE knowledge_items
            SET confidence_score = LEAST(1.0, 
                (usage_count * 0.1) + 
                (EXTRACT(DAYS FROM NOW() - created_at) * -0.01) + 0.5
            )
            WHERE confidence_score != LEAST(1.0, 
                (usage_count * 0.1) + 
                (EXTRACT(DAYS FROM NOW() - created_at) * -0.01) + 0.5
            )
        """
        
        await self.database.execute_command(query)
        logger.info("Knowledge scores updated")
    
    async def _update_usage_counts(self, knowledge_ids: List[UUID]):
        """Update usage counts for knowledge items"""
        if not knowledge_ids:
            return
        
        query = """
            UPDATE knowledge_items
            SET usage_count = usage_count + 1, updated_at = NOW()
            WHERE id = ANY($1)
        """
        
        await self.database.execute_command(query, knowledge_ids)
    
    async def health_check(self) -> bool:
        """Check knowledge manager health"""
        return self.is_initialized
    
    async def shutdown(self):
        """Shutdown knowledge manager"""
        logger.info("Knowledge Manager shutdown complete")

---

## Phase 5: Middleware & Monitoring

### Rate Limiting Middleware
```python
# middleware/rate_limiting.py - Redis-based rate limiting
import time
import json
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis.asyncio as aioredis
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str, default_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.redis_url = redis_url
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.redis = None
    
    async def dispatch(self, request: Request, call_next):
        # Initialize Redis connection if needed
        if not self.redis:
            try:
                self.redis = await aioredis.from_url(self.redis_url)
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                # Continue without rate limiting if Redis is unavailable
                return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        try:
            allowed = await self._check_rate_limit(client_id, request.url.path)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue on rate limiting errors
        
        response = await call_next(request)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user from JWT token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # You'd decode JWT here to get user ID
                # For now, use a hash of the token
                import hashlib
                token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:8]
                return f"user:{token_hash}"
            except:
                pass
        
        # Fall back to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """Check if client is within rate limits"""
        key = f"rate_limit:{client_id}:{endpoint}"
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        try:
            # Use Redis sorted set for sliding window
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
            pipe.zadd(key, {str(current_time): current_time})  # Add current request
            pipe.zcard(key)  # Count current requests
            pipe.expire(key, self.window_seconds)  # Set expiration
            
            results = await pipe.execute()
            request_count = results[2]  # zcard result
            
            return request_count <= self.default_limit
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Fail open

# middleware/monitoring.py - Performance monitoring
class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.response_times = []
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment request counter
        self.request_count += 1
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            # Keep only recent response times
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-500:]
            
            # Add metrics headers
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Request-Count"] = str(self.request_count)
            
            # Log slow requests
            if response_time > 2.0:  # Log requests taking more than 2 seconds
                logger.warning(f"Slow request: {request.method} {request.url.path} took {response_time:.3f}s")
            
            return response
            
        except Exception as e:
            # Log errors
            response_time = time.time() - start_time
            logger.error(f"Request failed: {request.method} {request.url.path} - {e} (took {response_time:.3f}s)")
            raise
    
    def get_metrics(self) -> dict:
        """Get current metrics"""
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            max_response_time = max(self.response_times)
        else:
            avg_response_time = 0
            max_response_time = 0
        
        return {
            "total_requests": self.request_count,
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "recent_requests": len(self.response_times)
        }

---

## Phase 6: Docker & Deployment

### Production Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### Requirements File
```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
asyncpg==0.29.0
redis==5.0.1
PyJWT==2.8.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
scikit-learn==1.3.2
numpy==1.24.4

# Optional monitoring/production
prometheus-client==0.19.0
structlog==23.2.0
```

### Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ymera:password@postgres:5432/ymera_db
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=your-super-secure-secret-key-here-32-chars-min
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ymera
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ymera_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Database Migration Script
```sql
-- init.sql - Database initialization
-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent experiences table
CREATE TABLE IF NOT EXISTS agent_experiences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB,
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
    metadata JSONB DEFAULT '{}',
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge base table
CREATE TABLE IF NOT EXISTS knowledge_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    tags VARCHAR(255)[] DEFAULT '{}',
    category VARCHAR(100),
    confidence_score FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_expires ON user_sessions(user_id, expires_at);

CREATE INDEX IF NOT EXISTS idx_experiences_user_id ON agent_experiences(user_id);
CREATE INDEX IF NOT EXISTS idx_experiences_conversation_id ON agent_experiences(conversation_id);
CREATE INDEX IF NOT EXISTS idx_experiences_created_at ON agent_experiences(created_at);
CREATE INDEX IF NOT EXISTS idx_experiences_processed ON agent_experiences(processed);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_items(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_items USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON knowledge_items(confidence_score);

CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON system_metrics(metric_name, timestamp);

-- Create trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiences_updated_at BEFORE UPDATE ON agent_experiences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_updated_at BEFORE UPDATE ON knowledge_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample admin user (password: admin123)
INSERT INTO users (email, password_hash, first_name, last_name, role) VALUES 
('admin@ymera.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJcwvQhCi', 'Admin', 'User', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Insert sample knowledge items
INSERT INTO knowledge_items (title, content, category, tags) VALUES 
('Welcome Message', 'Welcome to YMERA Agent System! I am an AI assistant designed to help you with various tasks and questions. Feel free to ask me anything.', 'system', ARRAY['welcome', 'introduction']),
('System Capabilities', 'I can help you with answering questions, providing information, having conversations, and learning from our interactions to improve over time.', 'system', ARRAY['capabilities', 'features']),
('Getting Started', 'To get started, simply type your question or message. I will do my best to provide helpful and accurate responses based on my knowledge and training.', 'help', ARRAY['getting-started', 'help'])
ON CONFLICT DO NOTHING;
```

---

## Phase 7: Complete System Integration

### Environment Configuration
```bash
# .env.example
# Copy this to .env and fill in your values

# Database
DATABASE_URL=postgresql://ymera:password@localhost:5432/ymera_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-super-secure-secret-key-here-at-least-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
ALLOWED_HOSTS=["*"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Agent Settings
MAX_CONVERSATION_HISTORY=50
LEARNING_BATCH_SIZE=10
MODEL_UPDATE_INTERVAL=3600
```

### Complete Agent Extensions
```python
# core/agent.py - Additional methods for the complete system
class YmeraAgent:
    # ... (previous methods remain the same)
    
    async def get_user_conversations(self, user_id: UUID, limit: int = 20) -> List[Dict]:
        """Get user's recent conversations"""
        query = """
            SELECT 
                conversation_id,
                COUNT(*) as message_count,
                MAX(created_at) as last_activity,
                MIN(created_at) as started_at
            FROM agent_experiences
            WHERE user_id = $1
            GROUP BY conversation_id
            ORDER BY last_activity DESC
            LIMIT $2
        """
        
        conversations = await self.database.execute_query(query, user_id, limit)
        
        # Get first message for each conversation as preview
        for conv in conversations:
            first_msg = await self.database.execute_single(
                """
                SELECT input_data->>'message' as preview
                FROM agent_experiences
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT 1
                """,
                conv["conversation_id"]
            )
            conv["preview"] = first_msg["preview"] if first_msg else "No preview"
        
        return conversations
    
    async def get_conversation_history(self, conversation_id: UUID, 
                                     user_id: UUID) -> List[Dict]:
        """Get conversation history with user verification"""
        # Verify user has access to this conversation
        access_check = await self.database.execute_single(
            "SELECT 1 FROM agent_experiences WHERE conversation_id = $1 AND user_id = $2 LIMIT 1",
            conversation_id, user_id
        )
        
        if not access_check:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        query = """
            SELECT 
                id,
                input_data,
                output_data,
                feedback_score,
                created_at
            FROM agent_experiences
            WHERE conversation_id = $1
            ORDER BY created_at ASC
        """
        
        return await self.database.execute_query(query, conversation_id)
    
    async def _get_unprocessed_experiences(self, limit: int = 100) -> List[Dict]:
        """Get unprocessed experiences for batch learning"""
        query = """
            SELECT id, user_id, conversation_id, input_data, output_data, feedback_score, metadata
            FROM agent_experiences
            WHERE processed = false
            ORDER BY created_at ASC
            LIMIT $1
        """
        
        return await self.database.execute_query(query, limit)
    
    async def _mark_experiences_processed(self, experience_ids: List[UUID]):
        """Mark experiences as processed"""
        if not experience_ids:
            return
        
        query = """
            UPDATE agent_experiences
            SET processed = true, updated_at = NOW()
            WHERE id = ANY($1)
        """
        
        await self.database.execute_command(query, experience_ids)
    
    async def _trigger_learning_update(self):
        """Trigger asynchronous learning update"""
        # This would trigger more sophisticated learning in production
        logger.info("Learning update triggered")
    
    async def _collect_system_metrics(self):
        """Collect and store system metrics"""
        import psutil
        
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = [
                ("cpu_usage_percent", cpu_percent),
                ("memory_usage_percent", memory.percent),
                ("memory_available_bytes", memory.available),
                ("disk_usage_percent", disk.percent),
                ("disk_free_bytes", disk.free)
            ]
            
            # Database metrics
            db_stats = await self._get_database_stats()
            metrics.extend(db_stats)
            
            # Store metrics
            for metric_name, value in metrics:
                await self.database.execute_command(
                    "INSERT INTO system_metrics (metric_name, metric_value) VALUES ($1, $2)",
                    metric_name, value
                )
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
    
    async def _get_database_stats(self) -> List[tuple]:
        """Get database performance statistics"""
        try:
            # Get table sizes
            stats = []
            
            # Count records in main tables
            for table in ['users', 'agent_experiences', 'knowledge_items', 'user_sessions']:
                result = await self.database.execute_single(f"SELECT COUNT(*) as count FROM {table}")
                stats.append((f"db_{table}_count", result["count"]))
            
            # Get recent activity
            recent_experiences = await self.database.execute_single(
                "SELECT COUNT(*) as count FROM agent_experiences WHERE created_at >= NOW() - INTERVAL '1 hour'"
            )
            stats.append(("db_recent_experiences_1h", recent_experiences["count"]))
            
            return stats
            
        except Exception as e:
            logger.error(f"Database stats collection failed: {e}")
            return []
```

### Production Monitoring & Health Checks
```python
# api/monitoring.py - Enhanced monitoring endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import asyncio
from datetime import datetime, timedelta

monitoring_router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@monitoring_router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """Get system metrics"""
    from main import app
    
    # Get middleware metrics
    metrics_middleware = None
    for middleware in app.user_middleware:
        if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'MetricsMiddleware':
            metrics_middleware = middleware.cls
            break
    
    if metrics_middleware:
        middleware_metrics = metrics_middleware.get_metrics()
    else:
        middleware_metrics = {}
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - app.state.start_time).total_seconds(),
        "middleware_metrics": middleware_metrics,
        "status": "healthy"
    }

@monitoring_router.get("/health/deep", response_model=Dict[str, Any])
async def deep_health_check():
    """Comprehensive health check"""
    from main import database, agent, auth_service
    
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "healthy",
        "components": {}
    }
    
    # Check database
    try:
        db_start = datetime.utcnow()
        db_healthy = await database.health_check()
        db_time = (datetime.utcnow() - db_start).total_seconds()
        
        health_status["components"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "response_time_seconds": db_time
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check agent
    try:
        agent_start = datetime.utcnow()
        agent_healthy = await agent.health_check()
        agent_time = (datetime.utcnow() - agent_start).total_seconds()
        
        health_status["components"]["agent"] = {
            "status": "healthy" if agent_healthy else "unhealthy",
            "response_time_seconds": agent_time
        }
    except Exception as e:
        health_status["components"]["agent"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check auth service
    try:
        auth_healthy = await auth_service.health_check()
        health_status["components"]["auth"] = {
            "status": "healthy" if auth_healthy else "unhealthy"
        }
    except Exception as e:
        health_status["components"]["auth"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Overall status
    if any(comp["status"] == "unhealthy" for comp in health_status["components"].values()):
        health_status["overall_status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

# Include in main router
from api.routes import router
router.include_router(monitoring_router)
```

### Startup and Deployment Scripts
```bash
#!/bin/bash
# scripts/start.sh - Production startup script

set -e

echo "Starting YMERA Agent System..."

# Check required environment variables
required_vars=("DATABASE_URL" "REDIS_URL" "JWT_SECRET_KEY")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

# Wait for database to be ready
echo "Waiting for database..."
python -c "
import asyncio
import asyncpg
import os
import time

async def wait_for_db():
    max_attempts = 30
    attempt = 0
    while attempt < max_attempts:
        try:
            conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
            await conn.close()
            print('Database is ready!')
            return
        except Exception as e:
            print(f'Attempt {attempt + 1}: Database not ready ({e})')
            await asyncio.sleep(2)
            attempt += 1
    
    print('Database failed to become ready')
    exit(1)

asyncio.run(wait_for_db())
"

# Run database migrations if needed
echo "Running database setup..."
psql $DATABASE_URL -f init.sql

# Start the application
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port ${API_PORT:-8000} --workers ${WORKERS:-1}
```

### Production Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ymera-agent
  labels:
    app: ymera-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ymera-agent
  template:
    metadata:
      labels:
        app: ymera-agent
    spec:
      containers:
      - name: ymera-agent
        image: ymera/agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ymera-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: ymera-secrets
              key: redis-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ymera-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: ymera-agent-service
spec:
  selector:
    app: ymera-agent
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

---

## Final Integration & Testing

### Simple Integration Test
```python
# tests/test_integration.py
import pytest
import asyncio
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_user_registration_and_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        register_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        register_response = await client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == 200
        
        # Login user
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["token"]["access_token"]
        
        # Test authenticated endpoint
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = await client.get("/api/v1/users/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_chat_functionality():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First register and login
        # ... (registration code from above)
        
        # Send chat message
        headers = {"Authorization": f"Bearer {token}"}
        chat_data = {"message": "Hello, how are you?"}
        
        chat_response = await client.post("/api/v1/chat/message", json=chat_data, headers=headers)
        assert chat_response.status_code == 200
        
        response_data = chat_response.json()
        assert "response" in response_data
        assert "conversation_id" in response_data
        assert response_data["confidence"] > 0
```

### Quick Start Guide
```bash
# Quick Start - Complete System Setup

# 1. Clone the repository (if applicable)
# git clone <repository-url>
# cd ymera-agent

# 2. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 3. Start with Docker Compose (easiest)
docker-compose up -d

# 4. Verify the system is running
curl http://localhost:8000/health

# 5. Create admin user (if needed)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com",
    "password": "SecurePassword123!",
    "first_name": "Admin",
    "last_name": "User"
  }'

# 6. Test the chat functionality
# First login to get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourcompany.com", "password": "SecurePassword123!"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['token']['access_token'])")

# Send a chat message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "Hello, can you help me?"}'
```

---

## System Summary

This production-ready YMERA Agent System provides:

### ✅ **Core Features Implemented**
- **Secure Authentication**: JWT with session management
- **RESTful API**: Complete CRUD operations for all entities  
- **Real-time Chat**: Conversation management with history
- **ML Pipeline**: Simple but effective response generation
- **Knowledge Base**: Searchable knowledge management
- **Rate Limiting**: Redis-based protection
- **Health Monitoring**: Comprehensive health checks
- **Database Management**: PostgreSQL with proper migrations
- **Docker Support**: Ready for containerized deployment

### ✅ **Enterprise-Ready Components**
- **Security**: Input sanitization, SQL injection prevention
- **Scalability**: Async architecture, connection pooling
- **Monitoring**: Performance metrics, error tracking
- **Deployment**: Docker, Kubernetes configurations
- **Testing**: Integration tests included
- **Documentation**: Complete API documentation

### ✅ **Production Deployment**
- **Environment Management**: Proper config handling
- **Database Migrations**: Automated schema management
- **Health Checks**: Liveness and readiness probes
- **Graceful Shutdown**: Proper cleanup on termination
- **Error Handling**: Comprehensive error management

This system balances **sophisticated enterprise features** with **practical simplicity**. The architecture allows for easy extension while maintaining solid production-ready foundations. Each component is focused and well-defined, making the system maintainable and scalable.

The "genius in simplicity" comes from using proven patterns consistently throughout the system, making it easy to understand, deploy, and maintain while still providing enterprise-grade capabilities.
    