"""
Chat Interface
Natural language interface for user communication
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

try:
    from database import Database as ProjectDatabase
except ImportError:
    ProjectDatabase = None

try:
    from agent_orchestrator import AgentOrchestrator
except ImportError:
    AgentOrchestrator = None

logger = logging.getLogger(__name__)


class ChatInterface:
    """
    Chat Interface with Natural Language Processing
    
    Features:
    - Context-aware responses
    - Command recognition
    - Multi-language support (placeholder)
    - History tracking
    """
    
    def __init__(
        self,
        settings,
        database: ProjectDatabase,
        agent_orchestrator: AgentOrchestrator
    ):
        self.settings = settings
        self.database = database
        self.agent_orchestrator = agent_orchestrator
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize chat interface"""
        self.is_initialized = True
        logger.info("✓ Chat interface initialized")
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Process user message and generate response
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
        
        Returns:
            response: Dict with response and metadata
        """
        logger.info(f"Processing message from user {user_id}: {message[:50]}...")
        
        try:
            # Detect intent
            intent = self._detect_intent(message)
            
            # Generate response based on intent
            if intent == "status_query":
                response = await self._handle_status_query(message, context)
            elif intent == "help":
                response = await self._handle_help_request(message)
            elif intent == "command":
                response = await self._handle_command(message, context)
            else:
                response = await self._handle_general_query(message, context)
            
            # Store message in history
            await self._store_message(user_id, message, response["response"], context)
            
            return response
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return {
                "response": "I apologize, but I'm having trouble understanding your request. Could you rephrase that?",
                "suggestions": ["Try 'help' for available commands"],
                "attachments": [],
                "error": True
            }
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Status queries
        if any(word in message_lower for word in ["status", "progress", "how is"]):
            return "status_query"
        
        # Help requests
        if any(word in message_lower for word in ["help", "how to", "what can"]):
            return "help"
        
        # Commands
        if message.startswith("/"):
            return "command"
        
        return "general"
    
    async def _handle_status_query(self, message: str, context: Optional[Dict]) -> Dict:
        """Handle project status queries"""
        # Extract project info from context
        project_id = context.get("project_id") if context else None
        
        if not project_id:
            return {
                "response": "Which project would you like to check? Please specify the project ID or name.",
                "suggestions": ["Show all projects", "List recent projects"],
                "attachments": []
            }
        
        # Get project status
        project = await self.database.get_project(project_id)
        
        if not project:
            return {
                "response": f"I couldn't find project {project_id}. Please check the ID.",
                "suggestions": ["List all projects"],
                "attachments": []
            }
        
        response_text = f"""
Project: {project['name']}
Status: {project['status']}
Progress: {project.get('progress', 0):.1f}%
Created: {project['created_at'].strftime('%Y-%m-%d')}
        """.strip()
        
        return {
            "response": response_text,
            "suggestions": [
                "Show detailed report",
                "List pending submissions",
                "Check quality metrics"
            ],
            "attachments": []
        }
    
    async def _handle_help_request(self, message: str) -> Dict:
        """Handle help requests"""
        help_text = """
I can help you with:

📊 Project Management:
  - Check project status
  - View progress
  - List submissions

🔍 Quality Verification:
  - Review quality scores
  - Check failed submissions
  - View quality trends

📁 File Management:
  - Upload files
  - Download files
  - List project files

💬 General:
  - Ask questions
  - Get reports
  - View analytics

Try asking: "What's the status of project XYZ?" or "Show quality report"
        """.strip()
        
        return {
            "response": help_text,
            "suggestions": ["Show project status", "List recent submissions"],
            "attachments": []
        }
    
    async def _handle_command(self, message: str, context: Optional[Dict]) -> Dict:
        """Handle slash commands"""
        parts = message.split()
        command = parts[0][1:]  # Remove /
        
        if command == "status":
            project_id = parts[1] if len(parts) > 1 else context.get("project_id")
            return await self._handle_status_query(f"status of {project_id}", {"project_id": project_id})
        
        elif command == "help":
            return await self._handle_help_request("")
        
        else:
            return {
                "response": f"Unknown command: /{command}",
                "suggestions": ["/help", "/status <project_id>"],
                "attachments": []
            }
    
    async def _handle_general_query(self, message: str, context: Optional[Dict]) -> Dict:
        """Handle general queries"""
        # Simplified response generation
        # In production, integrate with NLP models
        
        return {
            "response": f"I understand you're asking about: {message[:100]}...\n\nI'm processing your request. How can I help you specifically?",
            "suggestions": [
                "Show project status",
                "Get help",
                "List commands"
            ],
            "attachments": []
        }
    
    async def _store_message(
        self,
        user_id: str,
        message: str,
        response: str,
        context: Optional[Dict]
    ):
        """Store message in chat history"""
        query = """
            INSERT INTO chat_messages (user_id, message, response, context)
            VALUES ($1, $2, $3, $4)
        """
        
        import json
        await self.database.execute_command(
            query,
            user_id,
            message,
            response,
            json.dumps(context or {})
        )
    
    async def health_check(self) -> bool:
        """Check chat interface health"""
        return self.is_initialized
    
    async def shutdown(self):
        """Shutdown chat interface"""
        logger.info("Chat interface shutdown complete")

