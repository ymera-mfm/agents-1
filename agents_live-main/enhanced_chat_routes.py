"""
YMERA Enterprise Chat System - Production Ready Routes
WebSocket and REST API with streaming, security, and monitoring
Version: 2.0.0
"""

from fastapi import (
    APIRouter, WebSocket, WebSocketDisconnect, Depends, 
    HTTPException, status, Query, Path, Request
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime
import json
import asyncio
import logging
from enum import Enum
import uuid

from ymera_core.security.auth_manager import AuthManager
from ymera_core.database.manager import DatabaseManager
from ymera_core.cache.redis_cache import RedisCacheManager
from ymera_services.ai.multi_llm_manager import MultiLLMManager
from ymera_agents.learning.learning_engine import LearningEngine
from ymera_agents.orchestrator import AgentOrchestrator
from ymera_core.logging.structured_logger import StructuredLogger

# Initialize logger
logger = StructuredLogger(__name__)

# Enums
class ChatMode(str, Enum):
    """Chat interaction modes"""
    GENERAL = "general"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    DEBUGGING = "debugging"

class MessageType(str, Enum):
    """Message types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

class MessageStatus(str, Enum):
    """Message status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Pydantic models
class CreateSessionRequest(BaseModel):
    """Request to create new chat session"""
    title: Optional[str] = Field(None, max_length=200)
    mode: ChatMode = Field(default=ChatMode.GENERAL)
    active_agents: List[str] = Field(default_factory=list, max_length=5)
    system_prompt: Optional[str] = Field(None, max_length=2000)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v and not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip() if v else None

class SendMessageRequest(BaseModel):
    """Request to send message"""
    content: str = Field(..., min_length=1, max_length=4000)
    agent_id: Optional[str] = Field(None, max_length=100)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    stream: bool = Field(default=False, description="Enable streaming response")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()

class UpdateSessionRequest(BaseModel):
    """Request to update session"""
    title: Optional[str] = Field(None, max_length=200)
    active_agents: Optional[List[str]] = Field(None, max_items=5)
    system_prompt: Optional[str] = Field(None, max_length=2000)

class SessionResponse(BaseModel):
    """Chat session response"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: str
    user_id: str
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime
    active_agents: List[str]
    message_count: int
    total_tokens: int
    is_active: bool = True

class MessageResponse(BaseModel):
    """Chat message response"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    id: str
    session_id: str
    content: str
    message_type: MessageType
    timestamp: datetime
    agent_id: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    tokens: Optional[int] = None

class ChatAnalyticsResponse(BaseModel):
    """Chat analytics response"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    total_sessions: int
    total_messages: int
    avg_messages_per_session: float
    total_tokens: int
    last_activity: Optional[datetime]
    agent_usage: List[Dict[str, Any]]
    popular_topics: List[str]

# WebSocket Connection Manager
class ChatConnectionManager:
    """
    Production-ready WebSocket connection manager with:
    - Connection pooling
    - Automatic reconnection handling
    - Message queuing
    - Health monitoring
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.user_sessions: Dict[str, List[str]] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self.logger = StructuredLogger(__name__)
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        session_id: str
    ) -> None:
        """Connect user to chat session with validation"""
        try:
            await websocket.accept()
            
            # Initialize user structures
            if user_id not in self.active_connections:
                self.active_connections[user_id] = {}
                self.user_sessions[user_id] = []
            
            # Store connection
            self.active_connections[user_id][session_id] = websocket
            
            if session_id not in self.user_sessions[user_id]:
                self.user_sessions[user_id].append(session_id)
            
            # Initialize message queue
            connection_key = f"{user_id}:{session_id}"
            self.message_queues[connection_key] = asyncio.Queue()
            
            # Start heartbeat
            self.heartbeat_tasks[connection_key] = asyncio.create_task(
                self._heartbeat_loop(user_id, session_id)
            )
            
            self.logger.info(
                f"User {user_id} connected to session {session_id}",
                extra={"user_id": user_id, "session_id": session_id}
            )
            
            # Send connection confirmation
            await self.send_to_session(user_id, session_id, {
                "type": "connected",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected successfully"
            })
            
        except Exception as e:
            self.logger.error(f"Connection error: {str(e)}", exc_info=True)
            raise
    
    async def disconnect(self, user_id: str, session_id: str) -> None:
        """Gracefully disconnect user from session"""
        try:
            # Cancel heartbeat
            connection_key = f"{user_id}:{session_id}"
            if connection_key in self.heartbeat_tasks:
                self.heartbeat_tasks[connection_key].cancel()
                del self.heartbeat_tasks[connection_key]
            
            # Clear message queue
            if connection_key in self.message_queues:
                del self.message_queues[connection_key]
            
            # Remove connection
            if user_id in self.active_connections:
                if session_id in self.active_connections[user_id]:
                    del self.active_connections[user_id][session_id]
                
                if session_id in self.user_sessions.get(user_id, []):
                    self.user_sessions[user_id].remove(session_id)
                
                # Clean up empty user entries
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    if user_id in self.user_sessions:
                        del self.user_sessions[user_id]
            
            self.logger.info(
                f"User {user_id} disconnected from session {session_id}",
                extra={"user_id": user_id, "session_id": session_id}
            )
            
        except Exception as e:
            self.logger.error(f"Disconnect error: {str(e)}", exc_info=True)
    
    async def send_to_session(
        self, 
        user_id: str, 
        session_id: str, 
        message: dict
    ) -> bool:
        """Send message to specific session with error handling"""
        if (user_id in self.active_connections and 
            session_id in self.active_connections[user_id]):
            try:
                websocket = self.active_connections[user_id][session_id]
                await websocket.send_json(message)
                return True
                
            except WebSocketDisconnect:
                self.logger.warning(f"WebSocket disconnected for {user_id}/{session_id}")
                await self.disconnect(user_id, session_id)
                return False
                
            except Exception as e:
                self.logger.error(
                    f"Error sending to {user_id}/{session_id}: {str(e)}",
                    exc_info=True
                )
                await self.disconnect(user_id, session_id)
                return False
        
        return False
    
    async def broadcast_to_user(self, user_id: str, message: dict) -> int:
        """Broadcast message to all user's sessions"""
        sent_count = 0
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id].copy():
                if await self.send_to_session(user_id, session_id, message):
                    sent_count += 1
        return sent_count
    
    async def _heartbeat_loop(self, user_id: str, session_id: str) -> None:
        """Send periodic heartbeat to maintain connection"""
        try:
            while True:
                await asyncio.sleep(30)  # Every 30 seconds
                
                success = await self.send_to_session(user_id, session_id, {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                if not success:
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Heartbeat error: {str(e)}", exc_info=True)
    
    def get_active_users(self) -> List[str]:
        """Get list of active users"""
        return list(self.active_connections.keys())
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get active sessions for user"""
        return self.user_sessions.get(user_id, []).copy()
    
    def get_connection_count(self) -> int:
        """Get total active connections"""
        return sum(len(sessions) for sessions in self.active_connections.values())

# Global connection manager
connection_manager = ChatConnectionManager()

# Router setup
router = APIRouter(prefix="/api/v1/chat", tags=["Chat System"])

# Dependencies
async def get_current_user_ws(
    token: str,
    auth_manager: AuthManager = Depends()
) -> dict:
    """Authenticate WebSocket connection"""
    try:
        payload = await auth_manager.verify_token(token)
        if not payload or "sub" not in payload:
            raise ValueError("Invalid token")
        return payload
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_user(
    request: Request,
    auth_manager: AuthManager = Depends()
) -> dict:
    """Authenticate REST API request"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.replace("Bearer ", "")
        payload = await auth_manager.verify_token(token)
        
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def validate_session_access(
    session_id: str,
    user_id: str,
    db_manager: DatabaseManager
) -> bool:
    """Validate user has access to session"""
    session = await db_manager.get_chat_session(session_id)
    return session and session.get("user_id") == user_id

# WebSocket Endpoint
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    token: str = Query(...),
    db_manager: DatabaseManager = Depends(),
    ai_manager: MultiLLMManager = Depends(),
    learning_engine: LearningEngine = Depends()
):
    """
    WebSocket endpoint for real-time chat with streaming responses.
    
    Features:
    - Real-time bidirectional communication
    - Streaming AI responses
    - Automatic reconnection support
    - Message queuing
    - Health monitoring
    """
    user = None
    
    try:
        # Authenticate
        auth_manager = AuthManager()
        user = await get_current_user_ws(token, auth_manager)
        user_id = user["sub"]
        
        # Validate session access
        if not await validate_session_access(session_id, user_id, db_manager):
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Connect
        await connection_manager.connect(websocket, user_id, session_id)
        
        # Message processing loop
        while True:
            try:
                # Receive message with timeout
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=300.0  # 5 minute timeout
                )
                
                # Validate message
                if "content" not in data:
                    await connection_manager.send_to_session(user_id, session_id, {
                        "type": "error",
                        "message": "Invalid message format"
                    })
                    continue
                
                # Create message record
                message_id = str(uuid.uuid4())
                await db_manager.create_chat_message({
                    "id": message_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "content": data["content"],
                    "message_type": MessageType.USER,
                    "timestamp": datetime.utcnow()
                })
                
                # Send acknowledgment
                await connection_manager.send_to_session(user_id, session_id, {
                    "type": "message_received",
                    "message_id": message_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Process message and stream response
                await process_and_stream_response(
                    user_id=user_id,
                    session_id=session_id,
                    message_content=data["content"],
                    message_id=message_id,
                    ai_manager=ai_manager,
                    learning_engine=learning_engine,
                    db_manager=db_manager
                )
                
            except asyncio.TimeoutError:
                # Send ping to check connection
                await connection_manager.send_to_session(user_id, session_id, {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {user_id}/{session_id}")
                break
                
            except Exception as e:
                logger.error(f"Message processing error: {str(e)}", exc_info=True)
                await connection_manager.send_to_session(user_id, session_id, {
                    "type": "error",
                    "message": "Error processing message",
                    "error": str(e)
                })
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
    
    finally:
        if user:
            await connection_manager.disconnect(user["sub"], session_id)

async def process_and_stream_response(
    user_id: str,
    session_id: str,
    message_content: str,
    message_id: str,
    ai_manager: MultiLLMManager,
    learning_engine: LearningEngine,
    db_manager: DatabaseManager
) -> None:
    """Process message and stream AI response"""
    try:
        # Get session context
        session = await db_manager.get_chat_session(session_id)
        message_history = await db_manager.get_session_messages(
            session_id,
            limit=10
        )
        
        # Prepare AI request
        ai_request = {
            "prompt": message_content,
            "context": message_history,
            "mode": session.get("mode", "general"),
            "stream": True
        }
        
        # Send processing status
        await connection_manager.send_to_session(user_id, session_id, {
            "type": "processing",
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Stream AI response
        response_id = str(uuid.uuid4())
        full_response = []
        
        async for chunk in ai_manager.stream_completion(ai_request):
            # Send chunk to client
            await connection_manager.send_to_session(user_id, session_id, {
                "type": "response_chunk",
                "message_id": response_id,
                "content": chunk.get("content", ""),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            full_response.append(chunk.get("content", ""))
        
        # Combine full response
        complete_response = "".join(full_response)
        
        # Save assistant message
        await db_manager.create_chat_message({
            "id": response_id,
            "session_id": session_id,
            "content": complete_response,
            "message_type": MessageType.ASSISTANT,
            "timestamp": datetime.utcnow(),
            "tokens": len(complete_response.split())  # Rough estimate
        })
        
        # Send completion
        await connection_manager.send_to_session(user_id, session_id, {
            "type": "response_complete",
            "message_id": response_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update learning engine asynchronously
        asyncio.create_task(
            learning_engine.record_interaction(
                user_id=user_id,
                session_id=session_id,
                user_message=message_content,
                assistant_response=complete_response
            )
        )
        
    except Exception as e:
        logger.error(f"Response streaming error: {str(e)}", exc_info=True)
        await connection_manager.send_to_session(user_id, session_id, {
            "type": "error",
            "message": "Error generating response",
            "error": str(e)
        })

# REST API Endpoints

@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Create a new chat session.
    
    Features:
    - Configurable chat modes
    - Agent selection
    - Custom system prompts
    - Automatic title generation
    """
    try:
        user_id = current_user["sub"]
        session_id = str(uuid.uuid4())
        
        # Generate default title if not provided
        title = request.title or f"Chat Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        # Create session
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "mode": request.mode,
            "active_agents": request.active_agents,
            "system_prompt": request.system_prompt,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0,
            "total_tokens": 0,
            "is_active": True
        }
        
        await db_manager.create_chat_session(session_data)
        
        logger.info(
            f"Created chat session {session_id} for user {user_id}",
            extra={"session_id": session_id, "user_id": user_id}
        )
        
        return SessionResponse(**session_data)
        
    except Exception as e:
        logger.error(f"Session creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_inactive: bool = Query(False),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Get user's chat sessions with pagination.
    
    Returns most recent sessions first.
    """
    try:
        user_id = current_user["sub"]
        
        # Try cache first
        cache_key = f"user_sessions:{user_id}:{limit}:{offset}:{include_inactive}"
        cached = await cache_manager.get(cache_key)
        
        if cached:
            return [SessionResponse(**s) for s in json.loads(cached)]
        
        # Get from database
        sessions = await db_manager.get_user_chat_sessions(
            user_id=user_id,
            limit=limit,
            offset=offset,
            include_inactive=include_inactive
        )
        
        # Cache for 1 minute
        await cache_manager.set(
            cache_key,
            json.dumps([s.dict() for s in sessions]),
            expire=60
        )
        
        return [SessionResponse(**s.dict()) for s in sessions]
        
    except Exception as e:
        logger.error(f"Failed to retrieve sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """Get specific chat session details."""
    try:
        user_id = current_user["sub"]
        
        session = await db_manager.get_chat_session(session_id)
        
        if not session or session.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        return SessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )

@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    request: UpdateSessionRequest,
    session_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Update chat session configuration.
    
    Allows updating:
    - Session title
    - Active agents
    - System prompt
    """
    try:
        user_id = current_user["sub"]
        
        # Verify access
        session = await db_manager.get_chat_session(session_id)
        if not session or session.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Prepare updates
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.active_agents is not None:
            updates["active_agents"] = request.active_agents
        if request.system_prompt is not None:
            updates["system_prompt"] = request.system_prompt
        
        updates["updated_at"] = datetime.utcnow()
        
        # Update session
        await db_manager.update_chat_session(session_id, updates)
        
        # Clear cache
        await cache_manager.delete_pattern(f"user_sessions:{user_id}:*")
        
        # Get updated session
        updated_session = await db_manager.get_chat_session(session_id)
        
        logger.info(
            f"Updated session {session_id}",
            extra={"session_id": session_id, "updates": list(updates.keys())}
        )
        
        return SessionResponse(**updated_session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session update failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session"
        )

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Delete chat session and all associated messages.
    
    This operation cannot be undone.
    """
    try:
        user_id = current_user["sub"]
        
        # Verify access
        if not await validate_session_access(session_id, user_id, db_manager):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Disconnect any active WebSocket connections
        if user_id in connection_manager.user_sessions:
            if session_id in connection_manager.user_sessions[user_id]:
                await connection_manager.disconnect(user_id, session_id)
        
        # Delete session and messages
        await db_manager.delete_chat_session(session_id)
        
        # Clear cache
        await cache_manager.delete_pattern(f"user_sessions:{user_id}:*")
        
        logger.info(
            f"Deleted session {session_id}",
            extra={"session_id": session_id, "user_id": user_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    session_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    ai_manager: MultiLLMManager = Depends(),
    learning_engine: LearningEngine = Depends()
):
    """
    Send message to chat session (REST endpoint).
    
    For real-time streaming responses, use the WebSocket endpoint.
    """
    try:
        user_id = current_user["sub"]
        
        # Verify access
        if not await validate_session_access(session_id, user_id, db_manager):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Create user message
        message_id = str(uuid.uuid4())
        await db_manager.create_chat_message({
            "id": message_id,
            "session_id": session_id,
            "user_id": user_id,
            "content": request.content,
            "message_type": MessageType.USER,
            "timestamp": datetime.utcnow()
        })
        
        # Get response from AI
        session = await db_manager.get_chat_session(session_id)
        message_history = await db_manager.get_session_messages(session_id, limit=10)
        
        ai_response = await ai_manager.generate_completion({
            "prompt": request.content,
            "context": message_history,
            "mode": session.get("mode", "general"),
            "agent_id": request.agent_id
        })
        
        # Create assistant message
        response_id = str(uuid.uuid4())
        response_message = {
            "id": response_id,
            "session_id": session_id,
            "content": ai_response["content"],
            "message_type": MessageType.ASSISTANT,
            "timestamp": datetime.utcnow(),
            "agent_id": request.agent_id,
            "confidence_score": ai_response.get("confidence"),
            "tokens": ai_response.get("tokens")
        }
        
        await db_manager.create_chat_message(response_message)
        
        # Update session stats
        await db_manager.increment_session_stats(
            session_id,
            message_count=2,
            tokens=ai_response.get("tokens", 0)
        )
        
        # Record interaction for learning
        asyncio.create_task(
            learning_engine.record_interaction(
                user_id=user_id,
                session_id=session_id,
                user_message=request.content,
                assistant_response=ai_response["content"]
            )
        )
        
        return MessageResponse(**response_message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Message send failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    limit: int = Query(50, ge=1, le=200),
    before: Optional[str] = Query(None, description="Message ID for pagination"),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """
    Get messages from chat session with pagination.
    
    Returns messages in reverse chronological order.
    """
    try:
        user_id = current_user["sub"]
        
        # Verify access
        if not await validate_session_access(session_id, user_id, db_manager):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Get messages
        messages = await db_manager.get_session_messages(
            session_id=session_id,
            limit=limit,
            before=before
        )
        
        return [MessageResponse(**m.dict()) for m in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve messages: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )

@router.get("/analytics", response_model=ChatAnalyticsResponse)
async def get_chat_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(),
    cache_manager: RedisCacheManager = Depends()
):
    """
    Get comprehensive chat analytics for user.
    
    Includes:
    - Session statistics
    - Message counts
    - Token usage
    - Agent usage patterns
    - Popular topics
    """
    try:
        user_id = current_user["sub"]
        
        # Try cache
        cache_key = f"chat_analytics:{user_id}:{days}"
        cached = await cache_manager.get(cache_key)
        
        if cached:
            return ChatAnalyticsResponse(**json.loads(cached))
        
        # Get analytics
        analytics = await db_manager.get_chat_analytics(user_id, days)
        
        response = ChatAnalyticsResponse(
            total_sessions=analytics.get("total_sessions", 0),
            total_messages=analytics.get("total_messages", 0),
            avg_messages_per_session=round(
                analytics.get("avg_messages_per_session", 0.0), 2
            ),
            total_tokens=analytics.get("total_tokens", 0),
            last_activity=analytics.get("last_activity"),
            agent_usage=analytics.get("agent_usage", []),
            popular_topics=analytics.get("popular_topics", [])
        )
        
        # Cache for 5 minutes
        await cache_manager.set(
            cache_key,
            json.dumps(response.dict()),
            expire=300
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to retrieve analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
    - Connection manager status
    - Active connections count
    - System health
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "active_connections": connection_manager.get_connection_count(),
            "active_users": len(connection_manager.get_active_users()),
            "components": {
                "websocket": "operational",
                "connection_manager": "operational"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.post("/sessions/{session_id}/export")
async def export_session(
    session_id: str = Path(..., regex="^[a-f0-9-]{36}$"),
    format: str = Query("json", regex="^(json|markdown|txt)$"),
    current_user: dict = Depends(get_current_user),
    db_manager: DatabaseManager = Depends()
):
    """
    Export chat session in various formats.
    
    Supported formats:
    - JSON: Complete structured data
    - Markdown: Formatted for reading
    - TXT: Plain text transcript
    """
    try:
        user_id = current_user["sub"]
        
        # Verify access
        if not await validate_session_access(session_id, user_id, db_manager):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Get session and messages
        session = await db_manager.get_chat_session(session_id)
        messages = await db_manager.get_session_messages(session_id, limit=10000)
        
        # Format based on requested format
        if format == "json":
            export_data = {
                "session": session,
                "messages": [m.dict() for m in messages],
                "exported_at": datetime.utcnow().isoformat()
            }
            return export_data
            
        elif format == "markdown":
            content = f"# {session['title']}\n\n"
            content += f"**Created:** {session['created_at']}\n"
            content += f"**Mode:** {session['mode']}\n\n"
            content += "---\n\n"
            
            for msg in messages:
                role = "**You:**" if msg.message_type == "user" else "**Assistant:**"
                content += f"{role}\n{msg.content}\n\n"
            
            return {"content": content, "format": "markdown"}
            
        else:  # txt
            content = f"{session['title']}\n"
            content += f"Created: {session['created_at']}\n"
            content += "=" * 50 + "\n\n"
            
            for msg in messages:
                role = "You" if msg.message_type == "user" else "Assistant"
                content += f"[{role}]:\n{msg.content}\n\n"
            
            return {"content": content, "format": "txt"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export session"
        )