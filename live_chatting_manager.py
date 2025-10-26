"""
Complete Live Chatting Manager Agent
Real-time conversational AI with multi-user support, context management, and integration
"""

import asyncio
import json
import time
import traceback # Added for detailed error logging
import os # Added for environment variables
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field, asdict # Added asdict for easier serialization
from enum import Enum
import uuid
from collections import defaultdict, deque
import websockets
import aiohttp
from aiohttp import web, WSMsgType
import logging
import hashlib
from datetime import datetime, timedelta

from base_agent import BaseAgent, AgentConfig, TaskRequest, TaskResponse, Priority, AgentStatus, TaskStatus # Updated import
from opentelemetry import trace

class ChatSessionStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    ENDED = "ended"
    PAUSED = "paused"

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    NOTIFICATION = "notification"
    TYPING = "typing"
    ERROR = "error"

class SessionType(Enum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    SUPPORT = "support"
    CONSULTATION = "consultation"

@dataclass
class ChatMessage:
    id: str
    session_id: str
    user_id: str
    message_type: MessageType
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    replied_to: Optional[str] = None
    edited_at: Optional[float] = None
    attachments: List[str] = field(default_factory=list)

@dataclass
class ChatSession:
    id: str
    session_type: SessionType
    status: ChatSessionStatus
    participants: Set[str]
    title: str = "Chat Session"
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    conversation_summary: str = ""
    
@dataclass
class UserConnection:
    user_id: str
    session_id: str
    websocket: Any
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    user_agent: str = ""
    ip_address: str = ""

class LiveChattingManager(BaseAgent):
    """
    Live Chatting Manager providing:
    - Real-time WebSocket-based chat functionality
    - Multi-user chat rooms and private messaging
    - Context-aware conversational AI integration
    - Message persistence and history management
    - User presence and typing indicators
    - File sharing and media attachments
    - Chat moderation and content filtering
    - Integration with LLM agents for AI responses
    - Analytics and conversation insights
    - Chat session management and archiving
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Chat session management
        self.chat_sessions: Dict[str, ChatSession] = {}
        self.user_connections: Dict[str, UserConnection] = {}
        self.session_participants: Dict[str, Set[str]] = defaultdict(set)
        
        # Message storage and routing
        self.message_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.typing_indicators: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # AI Integration
        self.ai_enabled_sessions: Set[str] = set()
        self.conversation_contexts: Dict[str, List[Dict]] = defaultdict(list)
        
        # WebSocket server configuration from config or environment
        self.websocket_host = self.config.get_setting("websocket_host", "0.0.0.0")
        self.websocket_port = int(self.config.get_setting("websocket_port", 8765))
        
        # HTTP server for REST API configuration from config or environment
        self.http_app = None
        self.http_server = None
        self.http_port = int(self.config.get_setting("http_port", 8080))
        
        # Content filtering and moderation
        self.content_filters: List[callable] = []
        self.moderation_enabled = self.config.get_setting("moderation_enabled", True)
        
        # Analytics and metrics (BaseAgent now handles publishing, but we keep raw data)
        self.chat_metrics = {
            "total_messages": 0,
            "active_sessions": 0,
            "total_users": 0,
            "ai_responses_generated": 0,
            "average_response_time": 0.0
        }
        
        # Rate limiting
        self.rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        self._setup_content_filters()
    
    async def start(self):
        """Start the live chatting manager"""
        
        # The BaseAgent already subscribes to agent.{self.config.name}.task
        
        # Subscribe to AI responses (these would come from the CommunicationAgent)
        await self._subscribe(
            "chat.ai.response",
            self._handle_ai_response
        )
        
        # Start WebSocket server
        asyncio.create_task(self._start_websocket_server())
        
        # Start HTTP REST API server
        asyncio.create_task(self._start_http_server())
        
        # Start background tasks
        asyncio.create_task(self._session_cleanup_loop())
        asyncio.create_task(self._typing_indicator_cleanup())
        
        self.logger.info("Live Chatting Manager started")
    
    def _setup_content_filters(self):
        """Setup content filtering and moderation"""
        self.content_filters = [
            self._filter_profanity,
            self._filter_spam,
            self._filter_malicious_content,
            self._filter_personal_information
        ]
    
    async def _start_websocket_server(self):
        """Start the WebSocket server for real-time chat"""
        
        async def handle_websocket(websocket, path):
            try:
                await self._handle_websocket_connection(websocket, path)
            except websockets.exceptions.ConnectionClosed:
                self.logger.info(f"WebSocket connection closed for {websocket.remote_address}")
            except Exception as e:
                self.logger.error(f"WebSocket connection error: {e}", traceback=traceback.format_exc())
        
        self.websocket_server = await websockets.serve(
            handle_websocket,
            self.websocket_host,
            self.websocket_port
        )
        
        self.logger.info(f"WebSocket server started on {self.websocket_host}:{self.websocket_port}")
    
    async def _start_http_server(self):
        """Start HTTP server for REST API"""
        
        self.http_app = web.Application()
        
        # REST API routes
        self.http_app.router.add_post("/api/chat/sessions", self._create_session_handler)
        self.http_app.router.add_get("/api/chat/sessions/{session_id}", self._get_session_handler)
        self.http_app.router.add_post("/api/chat/sessions/{session_id}/join", self._join_session_handler)
        self.http_app.router.add_post("/api/chat/sessions/{session_id}/leave", self._leave_session_handler)
        self.http_app.router.add_get("/api/chat/sessions/{session_id}/messages", self._get_messages_handler)
        self.http_app.router.add_post("/api/chat/sessions/{session_id}/messages", self._send_message_handler)
        self.http_app.router.add_get("/api/chat/user/{user_id}/sessions", self._get_user_sessions_handler)
        self.http_app.router.add_get("/api/chat/metrics", self._get_chat_metrics_handler)
        
        # Health check
        self.http_app.router.add_get("/health", self._health_check_handler)
        
        runner = web.AppRunner(self.http_app)
        await runner.setup()
        
        site = web.TCPSite(runner, "0.0.0.0", self.http_port)
        await site.start()
        
        self.logger.info(f"HTTP server started on port {self.http_port}")
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Implement the actual task logic for the LiveChattingManager agent"""
        task_type = request.task_type
        payload = request.payload

        try:
            result: Dict[str, Any] = {}
            if task_type == "create_chat_session":
                result = await self._create_chat_session_task(payload)
            elif task_type == "send_chat_message":
                result = await self._send_chat_message_task(payload)
            elif task_type == "get_chat_history":
                result = await self._get_chat_history_task(payload)
            elif task_type == "end_chat_session":
                result = await self._end_chat_session_task(payload)
            elif task_type == "join_chat_session":
                result = await self._join_chat_session_task(payload)
            elif task_type == "leave_chat_session":
                result = await self._leave_chat_session_task(payload)
            elif task_type == "enable_ai_for_session":
                result = await self._enable_ai_for_session_task(payload)
            else:
                raise ValueError(f"Unknown live chatting task type: {task_type}")
            
            return TaskResponse(task_id=request.task_id, status=TaskStatus.COMPLETED, result=result).dict()

        except Exception as e:
            self.logger.error(f"Error executing live chatting task {task_type}", error=str(e), traceback=traceback.format_exc())
            return TaskResponse(task_id=request.task_id, status=TaskStatus.FAILED, error=str(e)).dict()

    async def _create_chat_session_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to create a new chat session"""
        session_id = payload.get("session_id", str(uuid.uuid4()))
        session_type = SessionType(payload.get("session_type", "individual"))
        participants = set(payload.get("participants", []))
        title = payload.get("title", f"Chat Session {session_id[:8]}")
        settings = payload.get("settings", {})

        if session_id in self.chat_sessions:
            raise ValueError(f"Session {session_id} already exists.")

        session = ChatSession(
            id=session_id,
            session_type=session_type,
            status=ChatSessionStatus.ACTIVE,
            participants=participants,
            title=title,
            settings=settings
        )
        self.chat_sessions[session_id] = session
        for participant in participants:
            self.session_participants[session_id].add(participant)
        self.chat_metrics["active_sessions"] = len(self.chat_sessions)
        self.logger.info(f"Chat session {session_id} created.")
        
        # Persist to database
        if self.db_pool:
            await self._persist_chat_session(session)

        return asdict(session)

    async def _send_chat_message_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to send a chat message from an agent or system"""
        session_id = payload["session_id"]
        user_id = payload.get("user_id", "system_agent") # Sender of the message
        content = payload["content"]
        message_type = MessageType(payload.get("message_type", "system"))
        metadata = payload.get("metadata", {})
        replied_to = payload.get("replied_to")
        attachments = payload.get("attachments", [])

        if session_id not in self.chat_sessions:
            raise ValueError(f"Session {session_id} not found.")

        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            message_type=message_type,
            content=content,
            metadata=metadata,
            replied_to=replied_to,
            attachments=attachments
        )

        self.message_buffer[session_id].append(chat_message)
        self.chat_metrics["total_messages"] += 1
        self.chat_sessions[session_id].last_activity = time.time()

        # Broadcast to all connected WebSocket clients for this session
        await self._broadcast_to_session(session_id, {
            "type": "chat_message",
            "message": {
                "id": chat_message.id,
                "user_id": chat_message.user_id,
                "content": chat_message.content,
                "timestamp": chat_message.timestamp,
                "message_type": chat_message.message_type.value,
                "metadata": chat_message.metadata,
                "replied_to": chat_message.replied_to,
                "attachments": chat_message.attachments
            }
        })
        self.logger.info(f"Message sent to session {session_id} by {user_id}.")
        
        # Store message in database if available
        if self.db_pool:
            await self._store_message_in_db(chat_message)

        return asdict(chat_message)

    async def _get_chat_history_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to retrieve chat history for a session"""
        session_id = payload["session_id"]
        limit = payload.get("limit", 100)
        offset = payload.get("offset", 0)

        if session_id not in self.chat_sessions:
            raise ValueError(f"Session {session_id} not found.")
        
        # Retrieve from buffer first, then potentially from DB for older messages
        messages = list(self.message_buffer[session_id])
        # For a real system, this would query the database for historical messages
        if self.db_pool:
            db_messages = await self._fetch_messages_from_db(session_id, limit, offset)
            # Combine and deduplicate if necessary, for simplicity, assuming DB is primary source for history
            messages = db_messages + messages # Simple concatenation, real logic would be more complex
        
        return {"messages": [asdict(msg) for msg in messages[offset:offset+limit]]}

    async def _end_chat_session_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to end a chat session"""
        session_id = payload["session_id"]

        if session_id not in self.chat_sessions:
            raise ValueError(f"Session {session_id} not found.")

        session = self.chat_sessions[session_id]
        session.status = ChatSessionStatus.ENDED
        session.ended_at = time.time()
        self.chat_metrics["active_sessions"] = len(self.chat_sessions)

        # Notify participants
        await self._broadcast_to_session(session_id, {
            "type": "session_ended",
            "session_id": session_id,
            "timestamp": time.time()
        })

        # Clean up connections for this session
        connections_to_close = [k for k, v in self.user_connections.items() if v.session_id == session_id]
        for key in connections_to_close:
            await self._cleanup_connection(key)
        
        # Update session in database
        if self.db_pool:
            await self._update_persisted_chat_session(session)

        self.logger.info(f"Chat session {session_id} ended.")
        return {"session_id": session_id, "status": "ended"}

    async def _join_chat_session_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method for an agent to join a chat session"""
        session_id = payload["session_id"]
        user_id = payload["user_id"]

        if session_id not in self.chat_sessions:
            raise ValueError(f"Session {session_id} not found.")
        
        self.chat_sessions[session_id].participants.add(user_id)
        self.session_participants[session_id].add(user_id)
        self.chat_sessions[session_id].last_activity = time.time()

        await self._broadcast_to_session(session_id, {
            "type": "user_joined",
            "user_id": user_id,
            "timestamp": time.time()
        })
        self.logger.info(f"User/Agent {user_id} joined session {session_id}.")
        
        # Update session in database
        if self.db_pool:
            await self._update_persisted_chat_session(self.chat_sessions[session_id])

        return {"session_id": session_id, "user_id": user_id, "status": "joined"}

    async def _leave_chat_session_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method for an agent to leave a chat session"""
        session_id = payload["session_id"]
        user_id = payload["user_id"]

        if session_id not in self.chat_sessions:
            raise ValueError(f"Session {session_id} not found.")
        
        if user_id in self.chat_sessions[session_id].participants:
            self.chat_sessions[session_id].participants.remove(user_id)
            self.session_participants[session_id].remove(user_id)
            self.chat_sessions[session_id].last_activity = time.time()

            await self._broadcast_to_session(session_id, {
                "type": "user_left",
                "user_id": user_id,
                "timestamp": time.time()
            })
            self.logger.info(f"User/Agent {user_id} left session {session_id}.")
            
            # Update session in database
            if self.db_pool:
                await self._update_persisted_chat_session(self.chat_sessions[session_id])

            return {"session_id": session_id, "user_id": user_id, "status": "left"}
        else:
            raise ValueError(f"User/Agent {user_id} not found in session {session_id}.")

    async def _enable_ai_for_session_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to enable AI responses for a specific chat session"""
        session_id = payload["session_id"]
        enable = payload.get("enable", True)

        if session_id not in self.chat_sessions:
            raise ValueError(f"Session {session_id} not found.")
        
        if enable:
            self.ai_enabled_sessions.add(session_id)
            self.logger.info(f"AI enabled for session {session_id}.")
        else:
            self.ai_enabled_sessions.discard(session_id)
            self.logger.info(f"AI disabled for session {session_id}.")
        
        # Update session in database
        if self.db_pool:
            await self._update_persisted_chat_session(self.chat_sessions[session_id])

        return {"session_id": session_id, "ai_enabled": enable}

    async def _handle_websocket_connection(self, websocket, path):
        """Handle a new WebSocket connection"""
        user_id = str(uuid.uuid4()) # Generate a unique ID for the connected user
        session_id = ""
        self.logger.info(f"New WebSocket connection from {websocket.remote_address}, assigned user_id: {user_id}")

        try:
            # Wait for initial message to identify user and session
            initial_message = await websocket.recv()
            data = json.loads(initial_message)
            
            user_id = data.get("user_id", user_id) # Allow client to provide user_id
            session_id = data.get("session_id")
            
            if not session_id:
                # If no session_id, maybe create a new one or reject
                self.logger.warning(f"WebSocket connection from {user_id} without session_id. Closing.")
                await websocket.close()
                return
            
            if session_id not in self.chat_sessions:
                self.logger.warning(f"WebSocket connection from {user_id} for non-existent session {session_id}. Closing.")
                await websocket.close()
                return
            
            # Check if user is a participant or can join
            if user_id not in self.chat_sessions[session_id].participants:
                # Auto-join if allowed, or reject
                self.chat_sessions[session_id].participants.add(user_id)
                self.session_participants[session_id].add(user_id)
                self.logger.info(f"User {user_id} auto-joined session {session_id} via WebSocket.")
                
                # Notify others of new participant
                await self._broadcast_to_session(session_id, {
                    "type": "user_joined",
                    "user_id": user_id,
                    "timestamp": time.time()
                })

            self.user_connections[user_id] = UserConnection(
                user_id=user_id,
                session_id=session_id,
                websocket=websocket,
                user_agent=data.get("user_agent", ""),
                ip_address=websocket.remote_address[0]
            )
            self.chat_metrics["total_users"] = len(self.user_connections)
            self.logger.info(f"User {user_id} connected to session {session_id}.")

            # Send initial history to the new client
            history = await self._get_chat_history_task({"session_id": session_id})
            await websocket.send(json.dumps({"type": "chat_history", "messages": history["messages"]}))

            # Keep connection alive and process incoming messages
            async for message in websocket:
                await self._handle_websocket_message(user_id, session_id, message)

        except websockets.exceptions.ConnectionClosedOK:
            self.logger.info(f"WebSocket connection closed gracefully for {user_id} in session {session_id}")
        except Exception as e:
            self.logger.error(f"Error in WebSocket connection for {user_id} in session {session_id}: {e}", traceback=traceback.format_exc())
        finally:
            await self._cleanup_connection(user_id)

    async def _handle_websocket_message(self, user_id: str, session_id: str, message: str):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "chat_message":
                content = data.get("content")
                if not content:
                    raise ValueError("Message content cannot be empty.")
                
                # Apply content filters
                if self.moderation_enabled:
                    filtered_content, is_flagged = self._apply_content_filters(content)
                    if is_flagged:
                        self.logger.warning(f"Message from {user_id} in {session_id} flagged by moderator: {content}")
                        # Optionally, send a notification to the user or moderator
                        await self._send_system_message(session_id, f"Your message was flagged for review: {content}", user_id)
                        return # Do not process flagged message further
                    content = filtered_content

                chat_message = ChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    user_id=user_id,
                    message_type=MessageType.USER,
                    content=content,
                    metadata=data.get("metadata", {})
                )
                self.message_buffer[session_id].append(chat_message)
                self.chat_metrics["total_messages"] += 1
                self.chat_sessions[session_id].last_activity = time.time()

                # Broadcast to all participants in the session
                await self._broadcast_to_session(session_id, {
                    "type": "chat_message",
                    "message": asdict(chat_message)
                })
                
                # Store message in database
                if self.db_pool:
                    await self._store_message_in_db(chat_message)

                # If AI is enabled for this session, send to CommunicationAgent
                if session_id in self.ai_enabled_sessions:
                    await self._request_ai_response(session_id, chat_message)

            elif message_type == "typing_indicator":
                is_typing = data.get("is_typing", False)
                if is_typing:
                    self.typing_indicators[session_id][user_id] = time.time()
                else:
                    self.typing_indicators[session_id].pop(user_id, None)
                await self._broadcast_typing_status(session_id)
            
            elif message_type == "edit_message":
                message_id = data.get("message_id")
                new_content = data.get("new_content")
                await self._edit_message(session_id, user_id, message_id, new_content)

            elif message_type == "delete_message":
                message_id = data.get("message_id")
                await self._delete_message(session_id, user_id, message_id)

            elif message_type == "read_receipt":
                message_id = data.get("message_id")
                await self._handle_read_receipt(session_id, user_id, message_id)

            else:
                self.logger.warning(f"Unknown WebSocket message type: {message_type}")
                await self._send_system_message(session_id, f"Unknown message type: {message_type}", user_id)

        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON received from {user_id} in session {session_id}: {message}")
            await self._send_system_message(session_id, "Invalid message format. Please send valid JSON.", user_id)
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message from {user_id} in session {session_id}: {e}", traceback=traceback.format_exc())
            await self._send_system_message(session_id, f"An error occurred while processing your message: {e}", user_id)

    async def _edit_message(self, session_id: str, user_id: str, message_id: str, new_content: str):
        """Edit an existing message"""
        for i, msg in enumerate(self.message_buffer[session_id]):
            if msg.id == message_id and msg.user_id == user_id: # Only allow author to edit
                original_content = msg.content
                msg.content = new_content
                msg.edited_at = time.time()
                
                # Update in DB
                if self.db_pool:
                    await self._update_message_in_db(msg)

                await self._broadcast_to_session(session_id, {
                    "type": "message_edited",
                    "message_id": message_id,
                    "new_content": new_content,
                    "edited_at": msg.edited_at,
                    "editor_id": user_id
                })
                self.logger.info(f"Message {message_id} in session {session_id} edited by {user_id}.")
                return
        self.logger.warning(f"Message {message_id} not found or not authorized to edit by {user_id} in session {session_id}.")
        await self._send_system_message(session_id, "Could not edit message. Message not found or you are not the author.", user_id)

    async def _delete_message(self, session_id: str, user_id: str, message_id: str):
        """Delete an existing message"""
        original_message = None
        for i, msg in enumerate(self.message_buffer[session_id]):
            if msg.id == message_id and msg.user_id == user_id: # Only allow author to delete
                original_message = self.message_buffer[session_id].pop(i) # Remove from deque
                break
        
        if original_message:
            # Delete from DB
            if self.db_pool:
                await self._delete_message_from_db(message_id)

            await self._broadcast_to_session(session_id, {
                "type": "message_deleted",
                "message_id": message_id,
                "deleter_id": user_id
            })
            self.logger.info(f"Message {message_id} in session {session_id} deleted by {user_id}.")
        else:
            self.logger.warning(f"Message {message_id} not found or not authorized to delete by {user_id} in session {session_id}.")
            await self._send_system_message(session_id, "Could not delete message. Message not found or you are not the author.", user_id)

    async def _handle_read_receipt(self, session_id: str, user_id: str, message_id: str):
        """Handle read receipts"""
        # This would typically update a 'read_by' field in the message in the DB
        # and broadcast a 'read_receipt' event to other participants.
        self.logger.debug(f"Read receipt for message {message_id} by {user_id} in session {session_id} (placeholder).")
        if self.db_pool:
            await self._update_message_read_status_in_db(message_id, user_id)
        await self._broadcast_to_session(session_id, {
            "type": "read_receipt",
            "message_id": message_id,
            "user_id": user_id,
            "timestamp": time.time()
        })

    async def _broadcast_to_session(self, session_id: str, message: Dict):
        """Broadcast a message to all connected clients in a session"""
        if session_id not in self.chat_sessions:
            return
        
        disconnected_users = []
        for user_id in list(self.session_participants[session_id]): # Iterate over a copy
            if user_id in self.user_connections:
                conn = self.user_connections[user_id]
                if conn.session_id == session_id:
                    try:
                        await conn.websocket.send(json.dumps(message))
                        conn.last_activity = time.time()
                    except websockets.exceptions.ConnectionClosed:
                        disconnected_users.append(user_id)
                    except Exception as e:
                        self.logger.error(f"Error broadcasting to {user_id} in session {session_id}: {e}", traceback=traceback.format_exc())
            else:
                disconnected_users.append(user_id)
        
        for user_id in disconnected_users:
            await self._cleanup_connection(user_id)

    async def _broadcast_typing_status(self, session_id: str):
        """Broadcast typing indicators to all participants in a session"""
        typing_users = [uid for uid, ts in self.typing_indicators[session_id].items() if time.time() - ts < 5] # Typing for last 5 seconds
        await self._broadcast_to_session(session_id, {
            "type": "typing_status",
            "session_id": session_id,
            "typing_users": typing_users
        })

    async def _send_system_message(self, session_id: str, content: str, target_user_id: Optional[str] = None):
        """Send a system message to a session or a specific user in a session"""
        system_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id="system",
            message_type=MessageType.SYSTEM,
            content=content
        )
        self.message_buffer[session_id].append(system_message)
        if self.db_pool:
            await self._store_message_in_db(system_message)

        if target_user_id and target_user_id in self.user_connections:
            conn = self.user_connections[target_user_id]
            if conn.session_id == session_id:
                try:
                    await conn.websocket.send(json.dumps({"type": "chat_message", "message": asdict(system_message)}))
                except Exception as e:
                    self.logger.error(f"Error sending system message to {target_user_id}: {e}", traceback=traceback.format_exc())
        else:
            await self._broadcast_to_session(session_id, {"type": "chat_message", "message": asdict(system_message)})

    async def _request_ai_response(self, session_id: str, last_message: ChatMessage):
        """Request an AI response from the CommunicationAgent"""
        # This sends a task to the CommunicationAgent to generate a response
        # The CommunicationAgent will then publish back to "chat.ai.response"
        self.logger.info(f"Requesting AI response for session {session_id} from CommunicationAgent.")
        
        # Fetch recent conversation history for context
        recent_messages = list(self.message_buffer[session_id])[-10:] # Last 10 messages
        conversation_history = [
            {"role": "user" if msg.message_type == MessageType.USER else "assistant", "content": msg.content}
            for msg in recent_messages
        ]

        task_payload = {
            "session_id": session_id,
            "user_id": last_message.user_id,
            "message_content": last_message.content,
            "conversation_history": conversation_history,
            "context": self.chat_sessions[session_id].context # Pass session context
        }
        
        # Publish a task for the CommunicationAgent
        await self._publish_task(
            agent_name="communication_agent", # Assuming CommunicationAgent handles AI responses
            task_type="generate_chat_response",
            payload=task_payload,
            priority=Priority.HIGH
        )

    async def _handle_ai_response(self, msg):
        """Handle incoming AI responses from the CommunicationAgent"""
        try:
            data = json.loads(msg.data.decode())
            session_id = data["session_id"]
            ai_response_content = data["response_content"]
            
            if session_id not in self.chat_sessions:
                self.logger.warning(f"Received AI response for non-existent session {session_id}.")
                return
            
            # Send the AI response as an assistant message
            await self._send_chat_message_task({
                "session_id": session_id,
                "user_id": "ai_assistant",
                "content": ai_response_content,
                "message_type": MessageType.ASSISTANT
            })
            self.chat_metrics["ai_responses_generated"] += 1
            self.logger.info(f"AI response sent to session {session_id}.")
            
        except Exception as e:
            self.logger.error(f"Error handling AI response: {e}", traceback=traceback.format_exc())

    async def _cleanup_connection(self, user_id: str):
        """Clean up a disconnected user's WebSocket connection"""
        if user_id in self.user_connections:
            conn = self.user_connections.pop(user_id)
            session_id = conn.session_id
            
            # Remove from session participants if they were the last connection for that user_id
            # This logic might need refinement for multiple connections per user
            if session_id in self.session_participants and user_id in self.session_participants[session_id]:
                # Check if this user_id has other active connections before removing from participants
                if not any(uc.user_id == user_id and uc.session_id == session_id for uc in self.user_connections.values()):
                    self.session_participants[session_id].discard(user_id)
                    await self._broadcast_to_session(session_id, {
                        "type": "user_left",
                        "user_id": user_id,
                        "timestamp": time.time()
                    })

            self.chat_metrics["total_users"] = len(self.user_connections)
            self.logger.info(f"Cleaned up connection for user {user_id} from session {session_id}.")

    async def _session_cleanup_loop(self):
        """Background task to clean up idle or ended sessions"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                idle_timeout = self.config.get_setting("session_idle_timeout_seconds", 3600) # 1 hour
                
                sessions_to_end = []
                for session_id, session in self.chat_sessions.items():
                    if session.status == ChatSessionStatus.ACTIVE and \
                       (current_time - session.last_activity > idle_timeout or not session.participants):
                        sessions_to_end.append(session_id)
                
                for session_id in sessions_to_end:
                    self.logger.info(f"Ending idle chat session {session_id}.")
                    await self._end_chat_session_task({"session_id": session_id})
                
                # Remove ended sessions from memory after a grace period
                ended_sessions_to_remove = []
                session_retention_period = self.config.get_setting("session_retention_seconds", 86400) # 24 hours
                for session_id, session in self.chat_sessions.items():
                    if session.status == ChatSessionStatus.ENDED and \
                       session.ended_at and (current_time - session.ended_at > session_retention_period):
                        ended_sessions_to_remove.append(session_id)
                
                for session_id in ended_sessions_to_remove:
                    del self.chat_sessions[session_id]
                    self.session_participants.pop(session_id, None)
                    self.message_buffer.pop(session_id, None)
                    self.ai_enabled_sessions.discard(session_id)
                    self.conversation_contexts.pop(session_id, None)
                    self.logger.info(f"Removed ended chat session {session_id} from memory.")

                await asyncio.sleep(self.config.get_setting("session_cleanup_interval_seconds", 300)) # Check every 5 minutes
            except Exception as e:
                self.logger.error(f"Error in session cleanup loop: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(60)

    async def _typing_indicator_cleanup(self):
        """Background task to clean up old typing indicators"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                for session_id, users_typing in list(self.typing_indicators.items()):
                    users_to_remove = []
                    for user_id, timestamp in users_typing.items():
                        if current_time - timestamp > 5: # If no activity for 5 seconds, stop typing
                            users_to_remove.append(user_id)
                    for user_id in users_to_remove:
                        self.typing_indicators[session_id].pop(user_id)
                    if not self.typing_indicators[session_id]:
                        self.typing_indicators.pop(session_id)
                    await self._broadcast_typing_status(session_id)
                await asyncio.sleep(1) # Check every second
            except Exception as e:
                self.logger.error(f"Error in typing indicator cleanup loop: {e}", traceback=traceback.format_exc())
                await asyncio.sleep(5)

    def _apply_content_filters(self, content: str) -> Tuple[str, bool]:
        """Apply a series of content filters"""
        is_flagged = False
        processed_content = content
        for filter_func in self.content_filters:
            processed_content, flagged_by_filter = filter_func(processed_content)
            if flagged_by_filter:
                is_flagged = True
        return processed_content, is_flagged

    def _filter_profanity(self, content: str) -> Tuple[str, bool]:
        """Simple profanity filter (placeholder)"""
        profane_words = ["badword1", "badword2"]
        flagged = False
        for word in profane_words:
            if word in content.lower():
                content = content.replace(word, "*" * len(word))
                flagged = True
        return content, flagged

    def _filter_spam(self, content: str) -> Tuple[str, bool]:
        """Simple spam filter (placeholder)"""
        spam_patterns = [r"http[s]?://[^\]+\.com", r"buy now", r"free money"]
        flagged = False
        for pattern in spam_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flagged = True
                break
        return content, flagged

    def _filter_malicious_content(self, content: str) -> Tuple[str, bool]:
        """Simple malicious content filter (placeholder)"""
        malicious_patterns = [r"<script>", r"eval\(", r"system\("]
        flagged = False
        for pattern in malicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flagged = True
                break
        return content, flagged

    def _filter_personal_information(self, content: str) -> Tuple[str, bool]:
        """Simple personal information filter (placeholder)"""
        # Regex for common patterns like email, phone numbers, etc.
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        flagged = False
        if re.search(email_pattern, content) or re.search(phone_pattern, content):
            flagged = True
            # Replace with [REDACTED] or similar
            content = re.sub(email_pattern, "[EMAIL_REDACTED]", content)
            content = re.sub(phone_pattern, "[PHONE_REDACTED]", content)
        return content, flagged

    # HTTP Request Handlers
    async def _create_session_handler(self, request):
        """HTTP handler to create a new chat session"""
        try:
            data = await request.json()
            session = await self._create_chat_session_task(data)
            return web.json_response(session, status=201)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            self.logger.error(f"Error in _create_session_handler: {e}", traceback=traceback.format_exc())
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _get_session_handler(self, request):
        """HTTP handler to get chat session details"""
        session_id = request.match_info.get("session_id")
        if session_id not in self.chat_sessions:
            return web.json_response({"error": "Session not found"}, status=404)
        return web.json_response(asdict(self.chat_sessions[session_id]))

    async def _join_session_handler(self, request):
        """HTTP handler for a user/agent to join a session"""
        try:
            session_id = request.match_info.get("session_id")
            data = await request.json()
            user_id = data.get("user_id")
            if not user_id:
                return web.json_response({"error": "user_id is required"}, status=400)
            result = await self._join_chat_session_task({"session_id": session_id, "user_id": user_id})
            return web.json_response(result)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            self.logger.error(f"Error in _join_session_handler: {e}", traceback=traceback.format_exc())
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _leave_session_handler(self, request):
        """HTTP handler for a user/agent to leave a session"""
        try:
            session_id = request.match_info.get("session_id")
            data = await request.json()
            user_id = data.get("user_id")
            if not user_id:
                return web.json_response({"error": "user_id is required"}, status=400)
            result = await self._leave_chat_session_task({"session_id": session_id, "user_id": user_id})
            return web.json_response(result)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            self.logger.error(f"Error in _leave_session_handler: {e}", traceback=traceback.format_exc())
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _get_messages_handler(self, request):
        """HTTP handler to get chat messages for a session"""
        try:
            session_id = request.match_info.get("session_id")
            limit = int(request.query.get("limit", 100))
            offset = int(request.query.get("offset", 0))
            messages = await self._get_chat_history_task({"session_id": session_id, "limit": limit, "offset": offset})
            return web.json_response(messages)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            self.logger.error(f"Error in _get_messages_handler: {e}", traceback=traceback.format_exc())
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _send_message_handler(self, request):
        """HTTP handler to send a message to a session"""
        try:
            session_id = request.match_info.get("session_id")
            data = await request.json()
            user_id = data.get("user_id", "rest_api_user")
            content = data.get("content")
            message_type = data.get("message_type", "user")
            
            if not content:
                return web.json_response({"error": "Message content is required"}, status=400)
            
            message = await self._send_chat_message_task({
                "session_id": session_id,
                "user_id": user_id,
                "content": content,
                "message_type": message_type
            })
            return web.json_response(message, status=201)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            self.logger.error(f"Error in _send_message_handler: {e}", traceback=traceback.format_exc())
            return web.json_response({"error": "Internal server error"}, status=500)

    async def _get_user_sessions_handler(self, request):
        """HTTP handler to get all sessions a user is part of"""
        user_id = request.match_info.get("user_id")
        user_sessions = []
        for session_id, session in self.chat_sessions.items():
            if user_id in session.participants:
                user_sessions.append(asdict(session))
        return web.json_response({"sessions": user_sessions})

    async def _get_chat_metrics_handler(self, request):
        """HTTP handler to get chat metrics"""
        # Update dynamic metrics before returning
        self.chat_metrics["active_sessions"] = len([s for s in self.chat_sessions.values() if s.status == ChatSessionStatus.ACTIVE])
        self.chat_metrics["total_users"] = len(self.user_connections)
        return web.json_response(self._get_agent_metrics())

    async def _health_check_handler(self, request):
        """Health check endpoint"""
        return web.json_response({"status": "ok", "agent": self.config.name, "uptime": time.time() - self._start_time})

    # Database Persistence Methods
    async def _persist_chat_session(self, session: ChatSession):
        """Persist a new chat session to the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        INSERT INTO chat_sessions (id, session_type, status, title, context, created_at, last_activity, ended_at, settings, conversation_summary, participants)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (id) DO UPDATE SET
                            session_type = EXCLUDED.session_type,
                            status = EXCLUDED.status,
                            title = EXCLUDED.title,
                            context = EXCLUDED.context,
                            last_activity = EXCLUDED.last_activity,
                            ended_at = EXCLUDED.ended_at,
                            settings = EXCLUDED.settings,
                            conversation_summary = EXCLUDED.conversation_summary,
                            participants = EXCLUDED.participants;
                        """,
                        session.id,
                        session.session_type.value,
                        session.status.value,
                        session.title,
                        json.dumps(session.context),
                        datetime.fromtimestamp(session.created_at),
                        datetime.fromtimestamp(session.last_activity),
                        datetime.fromtimestamp(session.ended_at) if session.ended_at else None,
                        json.dumps(session.settings),
                        session.conversation_summary,
                        list(session.participants) # Store as array of text
                    )
            self.logger.debug(f"Chat session {session.id} persisted to DB.")
        except Exception as e:
            self.logger.error(f"Error persisting chat session {session.id} to DB: {e}", traceback=traceback.format_exc())

    async def _update_persisted_chat_session(self, session: ChatSession):
        """Update an existing chat session in the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        UPDATE chat_sessions
                        SET session_type = $2, status = $3, title = $4, context = $5, last_activity = $6, ended_at = $7, settings = $8, conversation_summary = $9, participants = $10
                        WHERE id = $1;
                        """,
                        session.id,
                        session.session_type.value,
                        session.status.value,
                        session.title,
                        json.dumps(session.context),
                        datetime.fromtimestamp(session.last_activity),
                        datetime.fromtimestamp(session.ended_at) if session.ended_at else None,
                        json.dumps(session.settings),
                        session.conversation_summary,
                        list(session.participants)
                    )
            self.logger.debug(f"Chat session {session.id} updated in DB.")
        except Exception as e:
            self.logger.error(f"Error updating chat session {session.id} in DB: {e}", traceback=traceback.format_exc())

    async def _store_message_in_db(self, message: ChatMessage):
        """Store a chat message in the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        INSERT INTO chat_messages (id, session_id, user_id, message_type, content, timestamp, metadata, replied_to, edited_at, attachments)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);
                        """,
                        message.id,
                        message.session_id,
                        message.user_id,
                        message.message_type.value,
                        message.content,
                        datetime.fromtimestamp(message.timestamp),
                        json.dumps(message.metadata),
                        message.replied_to,
                        datetime.fromtimestamp(message.edited_at) if message.edited_at else None,
                        message.attachments # Store as array of text
                    )
            self.logger.debug(f"Message {message.id} stored in DB for session {message.session_id}.")
        except Exception as e:
            self.logger.error(f"Error storing message {message.id} to DB: {e}", traceback=traceback.format_exc())

    async def _fetch_messages_from_db(self, session_id: str, limit: int, offset: int) -> List[ChatMessage]:
        """Fetch chat messages from the database for a given session."""
        if not self.db_pool: return []
        messages = []
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, session_id, user_id, message_type, content, timestamp, metadata, replied_to, edited_at, attachments
                    FROM chat_messages
                    WHERE session_id = $1
                    ORDER BY timestamp ASC
                    LIMIT $2 OFFSET $3;
                    """,
                    session_id, limit, offset
                )
                for row in rows:
                    messages.append(ChatMessage(
                        id=row["id"],
                        session_id=row["session_id"],
                        user_id=row["user_id"],
                        message_type=MessageType(row["message_type"]),
                        content=row["content"],
                        timestamp=row["timestamp"].timestamp(),
                        metadata=row["metadata"],
                        replied_to=row["replied_to"],
                        edited_at=row["edited_at"].timestamp() if row["edited_at"] else None,
                        attachments=row["attachments"]
                    ))
            self.logger.debug(f"Fetched {len(messages)} messages from DB for session {session_id}.")
        except Exception as e:
            self.logger.error(f"Error fetching messages from DB for session {session_id}: {e}", traceback=traceback.format_exc())
        return messages

    async def _update_message_in_db(self, message: ChatMessage):
        """Update an existing message in the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        UPDATE chat_messages
                        SET content = $2, edited_at = $3, metadata = $4, attachments = $5
                        WHERE id = $1;
                        """,
                        message.id,
                        message.content,
                        datetime.fromtimestamp(message.edited_at) if message.edited_at else None,
                        json.dumps(message.metadata),
                        message.attachments
                    )
            self.logger.debug(f"Message {message.id} updated in DB.")
        except Exception as e:
            self.logger.error(f"Error updating message {message.id} in DB: {e}", traceback=traceback.format_exc())

    async def _delete_message_from_db(self, message_id: str):
        """Delete a message from the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        """
                        DELETE FROM chat_messages
                        WHERE id = $1;
                        """,
                        message_id
                    )
            self.logger.debug(f"Message {message_id} deleted from DB.")
        except Exception as e:
            self.logger.error(f"Error deleting message {message_id} from DB: {e}", traceback=traceback.format_exc())

    async def _update_message_read_status_in_db(self, message_id: str, user_id: str):
        """Update the read status of a message in the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # This assumes a 'read_by' JSONB field or a separate 'message_reads' table
                    # For simplicity, let's assume a JSONB 'metadata' field that can store read_by users
                    await conn.execute(
                        """
                        UPDATE chat_messages
                        SET metadata = jsonb_set(metadata, 
                                                 ARRAY["read_by"], 
                                                 (metadata->>
                                                 ARRAY["read_by"] || $2)::jsonb, 
                                                 true)
                        WHERE id = $1;
                        """,
                        message_id,
                        json.dumps([user_id]) # Append user_id to a JSON array
                    )
            self.logger.debug(f"Message {message_id} read status updated for {user_id} in DB.")
        except Exception as e:
            self.logger.error(f"Error updating read status for message {message_id} by {user_id} in DB: {e}", traceback=traceback.format_exc())

    def _get_agent_metrics(self) -> Dict[str, Any]:
        """Provide LiveChattingManager specific metrics."""
        base_metrics = super()._get_agent_metrics()
        base_metrics.update({
            "total_messages": self.chat_metrics["total_messages"],
            "active_sessions": len([s for s in self.chat_sessions.values() if s.status == ChatSessionStatus.ACTIVE]),
            "total_users_connected": len(self.user_connections),
            "ai_responses_generated": self.chat_metrics["ai_responses_generated"],
            "average_response_time": self.chat_metrics["average_response_time"],
            "websocket_host": self.websocket_host,
            "websocket_port": self.websocket_port,
            "http_port": self.http_port,
            "moderation_enabled": self.moderation_enabled
        })
        return base_metrics


if __name__ == "__main__":
    config = AgentConfig(
        name="live_chatting_manager",
        agent_type="communication",
        capabilities=[
            "create_chat_session", "send_chat_message", "get_chat_history",
            "end_chat_session", "join_chat_session", "leave_chat_session",
            "enable_ai_for_session", "websocket_interface", "rest_api_interface"
        ],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL", "postgresql://agent:secure_password@postgres:5432/ymera"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        # Specific settings for LiveChattingManager
        settings={
            "websocket_host": os.getenv("WEBSOCKET_HOST", "0.0.0.0"),
            "websocket_port": int(os.getenv("WEBSOCKET_PORT", 8765)),
            "http_port": int(os.getenv("HTTP_PORT", 8080)),
            "moderation_enabled": os.getenv("MODERATION_ENABLED", "true").lower() == "true",
            "session_idle_timeout_seconds": int(os.getenv("SESSION_IDLE_TIMEOUT_SECONDS", 3600)),
            "session_retention_seconds": int(os.getenv("SESSION_RETENTION_SECONDS", 86400))
        }
    )
    
    agent = LiveChattingManager(config)
    asyncio.run(agent.run())

