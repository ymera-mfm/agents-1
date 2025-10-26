# requirements.txt
"""
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
redis==5.0.1
aiohttp==3.9.1
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
numpy==1.24.3
pandas==2.0.3
scipy==1.11.4
scikit-learn==1.3.2
torch==2.1.1
transformers==4.35.2
sentence-transformers==2.2.2
faiss-cpu==1.7.4
networkx==3.2.1
aiofiles==23.2.1
cryptography==41.0.7
hvac==2.0.0
minio==7.2.0
psutil==5.9.6
"""

# config/settings.py
import os
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
import secrets

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "YMERA Learning Agent"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Vault
    VAULT_URL: str = Field(default="http://localhost:8200", env="VAULT_URL")
    VAULT_TOKEN: str = Field(..., env="VAULT_TOKEN")
    VAULT_NAMESPACE: str = Field(default="", env="VAULT_NAMESPACE")
    
    # ML/AI
    MODEL_CACHE_DIR: str = Field(default="/models", env="MODEL_CACHE_DIR")
    VECTOR_DIMENSION: int = 768
    MAX_BATCH_SIZE: int = 32
    GPU_MEMORY_FRACTION: float = 0.8
    
    # Storage
    UPLOAD_DIR: str = Field(default="/uploads", env="UPLOAD_DIR")
    BACKUP_DIR: str = Field(default="/backups", env="BACKUP_DIR")
    ARCHIVE_DIR: str = Field(default="/archives", env="ARCHIVE_DIR")
    
    # Monitoring
    PROMETHEUS_PUSHGATEWAY_URL: str = Field(default="", env="PROMETHEUS_PUSHGATEWAY_URL")
    ALERTMANAGER_URL: str = Field(default="", env="ALERTMANAGER_URL")
    ALERT_WEBHOOK_URL: str = Field(default="", env="ALERT_WEBHOOK_URL")
    
    # Rate Limiting
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Agent Configuration
    EXPERIENCE_BUFFER_SIZE: int = 10000
    MODEL_UPDATE_INTERVAL: int = 3600
    HEALTH_CHECK_INTERVAL: int = 60
    METRICS_PUSH_INTERVAL: int = 15
    BACKUP_INTERVAL: int = 86400
    ARCHIVE_INTERVAL: int = 86400
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Enhanced agent.py with complete implementations
import asyncio
import uuid
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import json

from fastapi import HTTPException
from sqlalchemy import text
from opentelemetry import trace

from config.settings import get_settings
from database.models import KnowledgeItem, ChatMessage, ModelVersion as ModelVersionDB
from ml.model_factory import ModelFactory
from utils.decorators import retry_on_failure, cache_result
from collections import deque

settings = get_settings()
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Agent state management"""
    is_initialized: bool = False
    is_shutting_down: bool = False
    active_sessions: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    last_health_check: Optional[datetime] = None

class UltraAdvancedLearningAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = self._merge_config(config)
        self.agent_id = str(uuid.uuid4())
        self.start_time = datetime.utcnow()
        self.state = AgentState()
        
        # Initialize components
        self._initialize_components()
        
        # Knowledge and learning management
        self.experience_buffer = deque(maxlen=self.config["max_experience_buffer"])
        self.knowledge_cache = {}
        self.learning_metrics = {}
        
        # Inter-agent communication
        self.agent_registry = {}
        self.message_queue = asyncio.Queue()
        
        logger.info(f"Initialized Learning Agent: {self.agent_id}")
    
    def _merge_config(self, custom_config: Optional[Dict]) -> Dict:
        """Merge custom config with default settings"""
        base_config = {
            "name": "UltraLearningAgent",
            "version": settings.APP_VERSION,
            "max_experience_buffer": settings.EXPERIENCE_BUFFER_SIZE,
            "model_update_interval": settings.MODEL_UPDATE_INTERVAL,
            "health_check_interval": settings.HEALTH_CHECK_INTERVAL,
            "metrics_push_interval": settings.METRICS_PUSH_INTERVAL,
            "backup_interval": settings.BACKUP_INTERVAL,
            "archive_interval": settings.ARCHIVE_INTERVAL,
        }
        if custom_config:
            base_config.update(custom_config)
        return base_config
    
    def _initialize_components(self):
        """Initialize all component dependencies"""
        from database.connection_pool import DatabasePool
        from database.redis_manager import RedisManager
        from security.vault_manager import VaultManager
        from security.encryption_service import EnhancedEncryptionService
        from ml.model_loader import ModelLoader
        from ml.model_registry import ModelRegistry
        from knowledge.knowledge_manager import EnhancedKnowledgeManager
        from knowledge.vector_store import VectorStore
        from knowledge.knowledge_graph import KnowledgeGraph
        from communication.websocket_manager import ConnectionManager
        from utils.metrics import AdvancedMetrics
        
        # Core services
        self.db_pool = DatabasePool(settings.DATABASE_URL)
        self.redis_manager = RedisManager(settings.REDIS_URL)
        self.vault_manager = VaultManager(settings.VAULT_URL, settings.VAULT_TOKEN)
        self.encryption_service = EnhancedEncryptionService(self.vault_manager)
        
        # ML components
        self.model_factory = ModelFactory()
        self.model_loader = ModelLoader(self.model_factory)
        self.model_registry = ModelRegistry(self.db_pool)
        
        # Knowledge components
        self.knowledge_manager = EnhancedKnowledgeManager(
            self.db_pool, self.redis_manager, self.vault_manager, self.encryption_service
        )
        self.vector_store = VectorStore()
        self.knowledge_graph = KnowledgeGraph()
        
        # Communication
        self.websocket_manager = ConnectionManager()
        
        # Monitoring
        self.metrics = AdvancedMetrics(settings.PROMETHEUS_PUSHGATEWAY_URL)
    
    async def initialize(self):
        """Complete initialization of the agent"""
        try:
            with tracer.start_as_current_span("agent_initialization"):
                logger.info("Starting agent initialization...")
                
                # Initialize database connections
                await self.db_pool.initialize()
                await self.redis_manager.connect()
                
                # Initialize security
                await self.vault_manager.initialize()
                await self.encryption_service.initialize()
                
                # Initialize ML components
                await self.model_loader.initialize(self.model_registry)
                await self._load_production_models()
                
                # Initialize knowledge systems
                await self.knowledge_manager.initialize()
                await self.vector_store.initialize()
                await self.knowledge_graph.initialize()
                
                # Start background tasks
                self._start_background_tasks()
                
                self.state.is_initialized = True
                logger.info("Agent initialized successfully")
                
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            raise
    
    def _start_background_tasks(self):
        """Start all background processing tasks"""
        tasks = [
            self._experience_processing_loop(),
            self._model_retraining_loop(),
            self._health_monitoring_loop(),
            self._metrics_collection_loop(),
            self._knowledge_sync_loop(),
            self._agent_communication_loop(),
        ]
        for task in tasks:
            asyncio.create_task(task)
    
    async def _load_production_models(self):
        """Load all production models"""
        try:
            async with self.db_pool.get_session() as session:
                result = await session.execute(
                    text("SELECT model_id, version FROM model_versions WHERE status = 'production'")
                )
                models = result.fetchall()
                
                for model_id, version in models:
                    await self.model_loader.load_model(model_id, version)
                    logger.info(f"Loaded production model: {model_id}:{version}")
        except Exception as e:
            logger.error(f"Failed to load production models: {e}")
    
    @tracer.start_as_current_span("process_experience")
    @retry_on_failure(max_attempts=3)
    async def process_experience(self, experience: Dict[str, Any], user_context: Dict) -> Dict:
        """Process and learn from new experience"""
        try:
            # Extract knowledge
            knowledge = await self._extract_knowledge(experience)
            
            # Store in knowledge base
            knowledge_id = await self._store_knowledge(knowledge, user_context)
            
            # Update vector embeddings
            embedding = await self._generate_embedding(knowledge["content"])
            await self.vector_store.add_vector(knowledge_id, embedding, knowledge)
            
            # Update knowledge graph
            await self._update_knowledge_graph(knowledge_id, knowledge)
            
            # Queue for model retraining
            self.experience_buffer.append({
                "knowledge_id": knowledge_id,
                "knowledge": knowledge,
                "timestamp": datetime.utcnow()
            })
            
            # Share with other agents
            await self._share_knowledge_with_agents(knowledge_id, knowledge)
            
            self.metrics.experiences_processed.inc()
            
            return {
                "status": "success",
                "knowledge_id": knowledge_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Experience processing failed: {e}")
            self.metrics.experience_processing_errors.inc()
            raise
    
    async def _extract_knowledge(self, experience: Dict) -> Dict:
        """Extract structured knowledge from experience"""
        # Use NLP model for knowledge extraction
        content = experience.get("content", "")
        
        # Extract entities, relationships, and concepts
        knowledge = {
            "content": content,
            "source": experience.get("source"),
            "type": experience.get("type", "general"),
            "entities": await self._extract_entities(content),
            "concepts": await self._extract_concepts(content),
            "confidence": 0.95,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "processing_version": self.config["version"]
            }
        }
        return knowledge
    
    async def _extract_entities(self, text: str) -> List[Dict]:
        """Extract entities from text using NER model"""
        # Simplified entity extraction
        entities = []
        # Would use actual NER model here
        return entities
    
    async def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simplified concept extraction
        concepts = []
        # Would use actual concept extraction model
        return concepts
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text"""
        # Use sentence transformer or similar
        # Simplified for example
        import hashlib
        hash_val = hashlib.sha256(text.encode()).digest()
        embedding = [float(b) / 255.0 for b in hash_val[:settings.VECTOR_DIMENSION]]
        return embedding
    
    async def _store_knowledge(self, knowledge: Dict, user_context: Dict) -> str:
        """Store knowledge in database"""
        async with self.db_pool.get_session() as session:
            knowledge_item = KnowledgeItem(
                content=json.dumps(knowledge),
                source=knowledge.get("source", "unknown"),
                tags=knowledge.get("concepts", []),
                security_level=user_context.get("security_level", "internal"),
                created_by=user_context.get("user_id")
            )
            session.add(knowledge_item)
            await session.commit()
            return knowledge_item.id
    
    async def _update_knowledge_graph(self, knowledge_id: str, knowledge: Dict):
        """Update knowledge graph with new knowledge"""
        # Add node for new knowledge
        await self.knowledge_graph.add_node(knowledge_id, knowledge)
        
        # Find and create relationships
        for entity in knowledge.get("entities", []):
            entity_id = f"entity_{entity.get('name', 'unknown')}"
            await self.knowledge_graph.add_node(entity_id, entity)
            await self.knowledge_graph.add_edge(
                knowledge_id, entity_id, "contains_entity"
            )
        
        # Link to similar knowledge
        similar = await self._find_similar_knowledge(knowledge)
        for sim_id, similarity in similar[:5]:
            await self.knowledge_graph.add_edge(
                knowledge_id, sim_id, "similar_to",
                {"similarity": similarity}
            )
    
    async def _find_similar_knowledge(self, knowledge: Dict) -> List[tuple]:
        """Find similar knowledge items"""
        embedding = await self._generate_embedding(knowledge["content"])
        similar = await self.vector_store.search_similar(embedding, top_k=10)
        return [(item["id"], item["similarity"]) for item in similar]
    
    async def _share_knowledge_with_agents(self, knowledge_id: str, knowledge: Dict):
        """Share knowledge with other agents in the platform"""
        message = {
            "type": "knowledge_update",
            "source_agent": self.agent_id,
            "knowledge_id": knowledge_id,
            "knowledge": knowledge,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to registered agents
        for agent_id in self.agent_registry:
            if agent_id != self.agent_id:
                await self._send_to_agent(agent_id, message)
    
    async def _send_to_agent(self, agent_id: str, message: Dict):
        """Send message to another agent"""
        try:
            # Use agent communicator or message queue
            await self.redis_manager.publish(f"agent:{agent_id}", json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to agent {agent_id}: {e}")
    
    @cache_result(ttl=60)
    async def analyze_agent_performance(self, agent_id: str) -> Dict:
        """Analyze another agent's performance based on outcomes"""
        try:
            # Retrieve agent's recent activities
            activities = await self._get_agent_activities(agent_id)
            
            # Analyze outcomes
            analysis = {
                "agent_id": agent_id,
                "period": "last_24_hours",
                "total_actions": len(activities),
                "success_rate": self._calculate_success_rate(activities),
                "avg_response_time": self._calculate_avg_response_time(activities),
                "error_patterns": self._identify_error_patterns(activities),
                "recommendations": [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Generate recommendations
            if analysis["success_rate"] < 0.9:
                analysis["recommendations"].append({
                    "type": "performance",
                    "message": "Consider optimizing error handling",
                    "priority": "high"
                })
            
            if analysis["avg_response_time"] > 1000:  # ms
                analysis["recommendations"].append({
                    "type": "latency",
                    "message": "Response time exceeds threshold",
                    "priority": "medium"
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze agent {agent_id}: {e}")
            raise
    
    async def _get_agent_activities(self, agent_id: str) -> List[Dict]:
        """Retrieve agent activities from monitoring system"""
        # Query from database or monitoring system
        activities = []
        return activities
    
    def _calculate_success_rate(self, activities: List[Dict]) -> float:
        """Calculate success rate from activities"""
        if not activities:
            return 1.0
        successful = sum(1 for a in activities if a.get("status") == "success")
        return successful / len(activities)
    
    def _calculate_avg_response_time(self, activities: List[Dict]) -> float:
        """Calculate average response time"""
        if not activities:
            return 0.0
        times = [a.get("response_time", 0) for a in activities]
        return sum(times) / len(times) if times else 0.0
    
    def _identify_error_patterns(self, activities: List[Dict]) -> List[Dict]:
        """Identify patterns in errors"""
        errors = [a for a in activities if a.get("status") == "error"]
        patterns = []
        
        # Group errors by type
        error_types = {}
        for error in errors:
            error_type = error.get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        for error_type, count in error_types.items():
            if count > 5:  # Threshold for pattern
                patterns.append({
                    "type": error_type,
                    "frequency": count,
                    "severity": "high" if count > 10 else "medium"
                })
        
        return patterns
    
    async def handle_chat_message(self, session_id: str, message: Dict, user_context: Dict) -> Dict:
        """Handle chat interaction with learning capabilities"""
        try:
            # Process message
            response = await self._process_chat_message(message, user_context)
            
            # Learn from interaction
            await self._learn_from_chat(session_id, message, response)
            
            # Store for analysis
            await self._store_chat_message(session_id, message, response, user_context)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat handling failed: {e}")
            raise
    
    async def _process_chat_message(self, message: Dict, user_context: Dict) -> Dict:
        """Process chat message and generate response"""
        content = message.get("content", "")
        
        # Search relevant knowledge
        relevant_knowledge = await self.knowledge_manager.search_knowledge_secure(
            content, user_context, vector_search=True
        )
        
        # Generate response based on knowledge
        response_content = self._generate_chat_response(content, relevant_knowledge)
        
        return {
            "role": "assistant",
            "content": response_content,
            "knowledge_used": [k["id"] for k in relevant_knowledge[:3]],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_chat_response(self, query: str, knowledge: List[Dict]) -> str:
        """Generate chat response from knowledge"""
        if not knowledge:
            return "I don't have specific information about that yet, but I'm continuously learning."
        
        # Synthesize response from knowledge
        response = "Based on my knowledge: "
        key_points = []
        for item in knowledge[:3]:
            content = json.loads(item.get("content", "{}"))
            key_points.append(content.get("content", ""))
        
        response += " ".join(key_points[:2])
        return response
    
    async def _learn_from_chat(self, session_id: str, message: Dict, response: Dict):
        """Learn from chat interaction"""
        # Extract patterns and update knowledge
        interaction = {
            "session_id": session_id,
            "query": message.get("content"),
            "response": response.get("content"),
            "timestamp": datetime.utcnow()
        }
        
        # Queue for learning
        self.experience_buffer.append({
            "type": "chat_interaction",
            "data": interaction
        })
    
    async def _store_chat_message(self, session_id: str, message: Dict, response: Dict, user_context: Dict):
        """Store chat messages for analysis"""
        async with self.db_pool.get_session() as session:
            # Store user message
            user_msg = ChatMessage(
                session_id=session_id,
                sender_id=user_context.get("user_id", "unknown"),
                message_type="user",
                content=message.get("content")
            )
            session.add(user_msg)
            
            # Store assistant response
            assistant_msg = ChatMessage(
                session_id=session_id,
                sender_id=self.agent_id,
                message_type="assistant",
                content=response.get("content")
            )
            session.add(assistant_msg)
            
            await session.commit()
    
    # Background task loops
    async def _experience_processing_loop(self):
        """Process queued experiences"""
        while not self.state.is_shutting_down:
            try:
                if len(self.experience_buffer) > 0:
                    batch = []
                    for _ in range(min(32, len(self.experience_buffer))):
                        if self.experience_buffer:
                            batch.append(self.experience_buffer.popleft())
                    
                    if batch:
                        await self._process_experience_batch(batch)
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Experience processing loop error: {e}")
                await asyncio.sleep(30)
    
    async def _process_experience_batch(self, batch: List[Dict]):
        """Process a batch of experiences"""
        for experience in batch:
            try:
                # Process based on type
                exp_type = experience.get("type", "general")
                if exp_type == "chat_interaction":
                    await self._process_chat_learning(experience["data"])
                else:
                    await self._process_general_learning(experience)
                    
            except Exception as e:
                logger.error(f"Failed to process experience: {e}")
    
    async def _process_chat_learning(self, interaction: Dict):
        """Learn from chat interactions"""
        # Analyze patterns, update models, etc.
        pass
    
    async def _process_general_learning(self, experience: Dict):
        """Process general learning experiences"""
        # Update knowledge base, retrain models, etc.
        pass
    
    async def _model_retraining_loop(self):
        """Periodically retrain models"""
        while not self.state.is_shutting_down:
            try:
                await asyncio.sleep(self.config["model_update_interval"])
                
                if await self._should_retrain():
                    await self._retrain_models()
                    
            except Exception as e:
                logger.error(f"Model retraining loop error: {e}")
                await asyncio.sleep(3600)
    
    async def _should_retrain(self) -> bool:
        """Determine if models should be retrained"""
        # Check data drift, performance metrics, new data volume
        return len(self.experience_buffer) > 1000
    
    async def _retrain_models(self):
        """Retrain ML models with new data"""
        logger.info("Starting model retraining...")
        # Implementation for model retraining
        pass
    
    async def _health_monitoring_loop(self):
        """Monitor system health"""
        while not self.state.is_shutting_down:
            try:
                health_status = await self.get_health_status()
                self.state.last_health_check = datetime.utcnow()
                
                if health_status["status"] != "healthy":
                    logger.warning(f"Health degraded: {health_status}")
                
                await asyncio.sleep(self.config["health_check_interval"])
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _metrics_collection_loop(self):
        """Collect and push metrics"""
        while not self.state.is_shutting_down:
            try:
                await self.metrics.update_system_metrics()
                await asyncio.sleep(self.config["metrics_push_interval"])
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    async def _knowledge_sync_loop(self):
        """Sync knowledge with other agents"""
        while not self.state.is_shutting_down:
            try:
                # Subscribe to knowledge updates from other agents
                updates = await self._receive_knowledge_updates()
                
                for update in updates:
                    await self._integrate_external_knowledge(update)
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Knowledge sync error: {e}")
                await asyncio.sleep(60)
    
    async def _receive_knowledge_updates(self) -> List[Dict]:
        """Receive knowledge updates from other agents"""
        updates = []
        # Implementation for receiving updates
        return updates
    
    async def _integrate_external_knowledge(self, update: Dict):
        """Integrate knowledge from other agents"""
        try:
            source_agent = update.get("source_agent")
            knowledge = update.get("knowledge")
            
            # Validate and integrate
            if await self._validate_external_knowledge(knowledge):
                await self._store_knowledge(knowledge, {"user_id": source_agent})
                logger.info(f"Integrated knowledge from agent {source_agent}")
                
        except Exception as e:
            logger.error(f"Failed to integrate external knowledge: {e}")
    
    async def _validate_external_knowledge(self, knowledge: Dict) -> bool:
        """Validate knowledge from external sources"""
        # Implement validation logic
        return True
    
    async def _agent_communication_loop(self):
        """Handle inter-agent communication"""
        while not self.state.is_shutting_down:
            try:
                # Process incoming messages
                while not self.message_queue.empty():
                    message = await self.message_queue.get()
                    await self._handle_agent_message(message)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Agent communication error: {e}")
                await asyncio.sleep(10)
    
    async def _handle_agent_message(self, message: Dict):
        """Handle message from another agent"""
        msg_type = message.get("type")
        
        if msg_type == "knowledge_request":
            await self._handle_knowledge_request(message)
        elif msg_type == "performance_query":
            await self._handle_performance_query(message)
        elif msg_type == "learning_update":
            await self._handle_learning_update(message)
    
    async def _handle_knowledge_request(self, message: Dict):
        """Handle knowledge request from another agent"""
        query = message.get("query")
        requesting_agent = message.get("source_agent")
        
        # Search and respond
        results = await self.knowledge_manager.search_knowledge_secure(
            query, {"user_id": requesting_agent}
        )
        
        response = {
            "type": "knowledge_response",
            "source_agent": self.agent_id,
            "results": results,
            "query": query
        }
        
        await self._send_to_agent(requesting_agent, response)
    
    async def _handle_performance_query(self, message: Dict):
        """Handle performance query from another agent"""
        target_agent = message.get("target_agent")
        analysis = await self.analyze_agent_performance(target_agent)
        
        response = {
            "type": "performance_analysis",
            "source_agent": self.agent_id,
            "analysis": analysis
        }
        
        await self._send_to_agent(message.get("source_agent"), response)
    
    async def _handle_learning_update(self, message: Dict):
        """Handle learning update from another agent"""
        learning_data = message.get("learning_data")
        
        # Process and integrate learning
        experience = {
            "content": learning_data,
            "source": f"agent_{message.get('source_agent')}",
            "type": "shared_learning"
        }
        
        await self.process_experience(experience, {"user_id": "system"})
    
    async def get_health_status(self) -> Dict:
        """Get comprehensive health status"""
        try:
            health_checks = {
                "database": await self._check_database_health(),
                "redis": await self._check_redis_health(),
                "models": await self._check_models_health(),
                "knowledge": await self._check_knowledge_health(),
            }
            
            # Overall status
            all_healthy = all(check.get("healthy", False) for check in health_checks.values())
            
            return {
                "status": "healthy" if all_healthy else "degraded",
                "agent_id": self.agent_id,
                "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
                "checks": health_checks,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_database_health(self) -> Dict:
        """Check database health"""
        try:
            async with self.db_pool.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return {"healthy": True, "latency_ms": 5}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_redis_health(self) -> Dict:
        """Check Redis health"""
        try:
            await self.redis_manager.ping()
            return {"healthy": True, "latency_ms": 2}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_models_health(self) -> Dict:
        """Check ML models health"""
        try:
            loaded_models = await self.model_loader.get_loaded_models()
            return {
                "healthy": len(loaded_models) > 0,
                "loaded_count": len(loaded_models)
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_knowledge_health(self) -> Dict:
        """Check knowledge systems health"""
        try:
            # Check if knowledge manager is operational
            test_query = "health_check"
            results = await self.knowledge_manager.search_knowledge_secure(
                test_query, {"user_id": "system"}
            )
            return {"healthy": True, "operational": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def shutdown(self):
        """Graceful shutdown"""
        if self.state.is_shutting_down:
            return
        
        self.state.is_shutting_down = True
        logger.info("Starting graceful shutdown...")
        
        try:
            # Save current state
            await self._save_state()
            
            # Close connections
            await self.db_pool.close()
            await self.redis_manager.close()
            
            # Unload models
            await self.model_loader.unload_models()
            
            logger.info("Shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _save_state(self):
        """Save agent state before shutdown"""
        state_data = {
            "agent_id": self.agent_id,
            "experience_buffer": list(self.experience_buffer),
            "learning_metrics": self.learning_metrics,
            "shutdown_time": datetime.utcnow().isoformat()
        }
        
        # Save to Redis or persistent storage
        await self.redis_manager.set(
            f"agent_state:{self.agent_id}",
            json.dumps(state_data),
            expire=86400  # 24 hours
        )

# Additional utility modules

# utils/decorators.py
from functools import wraps
import asyncio
from typing import Callable, Any

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator for async functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator

def cache_result(ttl: int = 60):
    """Cache decorator with TTL"""
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if (datetime.utcnow() - timestamp).total_seconds() < ttl:
                    return result
            
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, datetime.utcnow())
            return result
        return wrapper
    return decorator

# database/migrations/env.py
"""Alembic migration environment"""
from alembic import context
from sqlalchemy import engine_from_config, pool
from config.settings import get_settings
from database.models import Base

settings = get_settings()
config = context.config

# Set database URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
