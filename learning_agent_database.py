"""
YMERA Learning Agent - Production Database Layer
Complete database integration with PostgreSQL and Redis
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, Text, ForeignKey, Index
from datetime import datetime
import asyncio
import json
from typing import Dict, List, Any, Optional
import redis.asyncio as aioredis

Base = declarative_base()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Agent(Base):
    """Agent database model"""
    __tablename__ = 'agents'
    
    agent_id = Column(String(50), primary_key=True)
    role = Column(String(50), nullable=False)
    specializations = Column(JSON, default=list)
    knowledge_base = Column(JSON, default=dict)
    performance_metrics = Column(JSON, default=dict)
    collaboration_history = Column(JSON, default=list)
    learning_preferences = Column(JSON, default=dict)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    knowledge_items = relationship("Knowledge", back_populates="source_agent_rel")
    chat_messages = relationship("ChatMessageDB", back_populates="sender")
    
    __table_args__ = (
        Index('ix_agents_role', 'role'),
        Index('ix_agents_active', 'active'),
    )


class Knowledge(Base):
    """Knowledge database model"""
    __tablename__ = 'knowledge'
    
    knowledge_id = Column(String(50), primary_key=True)
    category = Column(String(50), nullable=False)
    source_agent_id = Column(String(50), ForeignKey('agents.agent_id'))
    content = Column(JSON, nullable=False)
    confidence_score = Column(Float, default=0.8)
    applicability_scope = Column(JSON, default=list)
    prerequisites = Column(JSON, default=list)
    related_knowledge = Column(JSON, default=list)
    validation_status = Column(String(20), default='pending')
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    source_agent_rel = relationship("Agent", back_populates="knowledge_items")
    
    __table_args__ = (
        Index('ix_knowledge_category', 'category'),
        Index('ix_knowledge_source', 'source_agent_id'),
        Index('ix_knowledge_validation', 'validation_status'),
    )


class LearningSessionDB(Base):
    """Learning session database model"""
    __tablename__ = 'learning_sessions'
    
    session_id = Column(String(50), primary_key=True)
    participants = Column(JSON, nullable=False)
    topic = Column(String(200))
    knowledge_transferred = Column(JSON, default=list)
    outcomes = Column(JSON, default=dict)
    success_metrics = Column(JSON, default=dict)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('ix_sessions_started', 'started_at'),
    )


class ChatMessageDB(Base):
    """Chat message database model"""
    __tablename__ = 'chat_messages'
    
    message_id = Column(String(50), primary_key=True)
    sender_id = Column(String(50), ForeignKey('agents.agent_id'))
    sender_type = Column(String(10), nullable=False)  # user or agent
    recipient_id = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    context = Column(JSON, default=dict)
    learning_intent = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    # Relationships
    sender = relationship("Agent", back_populates="chat_messages")
    
    __table_args__ = (
        Index('ix_chat_sender', 'sender_id'),
        Index('ix_chat_timestamp', 'timestamp'),
    )


class PerformanceMetric(Base):
    """Performance metrics time series"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), ForeignKey('agents.agent_id'))
    metric_type = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    context = Column(JSON, default=dict)
    
    __table_args__ = (
        Index('ix_metrics_agent_type', 'agent_id', 'metric_type'),
        Index('ix_metrics_recorded', 'recorded_at'),
    )


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Production database manager with connection pooling"""
    
    def __init__(self, database_url: str, redis_url: str):
        self.database_url = database_url
        self.redis_url = redis_url
        self.engine = None
        self.async_session_factory = None
        self.redis_client = None
        
    async def initialize(self):
        """Initialize database connections"""
        # PostgreSQL
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Redis
        self.redis_client = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )
        
        print("✓ Database connections initialized")
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
        
        if self.redis_client:
            await self.redis_client.close()
    
    # ========================================================================
    # AGENT OPERATIONS
    # ========================================================================
    
    async def save_agent(self, agent_data: Dict[str, Any]) -> str:
        """Save agent to database"""
        async with self.async_session_factory() as session:
            agent = Agent(**agent_data)
            session.add(agent)
            await session.commit()
            return agent.agent_id
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        async with self.async_session_factory() as session:
            result = await session.get(Agent, agent_id)
            if result:
                return {
                    'agent_id': result.agent_id,
                    'role': result.role,
                    'specializations': result.specializations,
                    'knowledge_base': result.knowledge_base,
                    'performance_metrics': result.performance_metrics,
                    'active': result.active,
                    'created_at': result.created_at,
                    'last_active': result.last_active
                }
            return None
    
    async def update_agent(self, agent_id: str, updates: Dict[str, Any]):
        """Update agent data"""
        async with self.async_session_factory() as session:
            agent = await session.get(Agent, agent_id)
            if agent:
                for key, value in updates.items():
                    setattr(agent, key, value)
                await session.commit()
    
    async def list_agents(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all agents"""
        async with self.async_session_factory() as session:
            from sqlalchemy import select
            
            query = select(Agent)
            if active_only:
                query = query.where(Agent.active == True)
            
            result = await session.execute(query)
            agents = result.scalars().all()
            
            return [{
                'agent_id': a.agent_id,
                'role': a.role,
                'active': a.active,
                'created_at': a.created_at
            } for a in agents]
    
    # ========================================================================
    # KNOWLEDGE OPERATIONS
    # ========================================================================
    
    async def save_knowledge(self, knowledge_data: Dict[str, Any]) -> str:
        """Save knowledge to database"""
        async with self.async_session_factory() as session:
            knowledge = Knowledge(**knowledge_data)
            session.add(knowledge)
            await session.commit()
            return knowledge.knowledge_id
    
    async def get_knowledge(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """Get knowledge by ID"""
        async with self.async_session_factory() as session:
            result = await session.get(Knowledge, knowledge_id)
            if result:
                return {
                    'knowledge_id': result.knowledge_id,
                    'category': result.category,
                    'source_agent_id': result.source_agent_id,
                    'content': result.content,
                    'confidence_score': result.confidence_score,
                    'usage_count': result.usage_count,
                    'success_rate': result.success_rate,
                    'created_at': result.created_at
                }
            return None
    
    async def search_knowledge(self, filters: Dict[str, Any], limit: int = 10) -> List[Dict]:
        """Search knowledge with filters"""
        async with self.async_session_factory() as session:
            from sqlalchemy import select
            
            query = select(Knowledge)
            
            if 'category' in filters:
                query = query.where(Knowledge.category == filters['category'])
            
            if 'min_confidence' in filters:
                query = query.where(Knowledge.confidence_score >= filters['min_confidence'])
            
            if 'source_agent' in filters:
                query = query.where(Knowledge.source_agent_id == filters['source_agent'])
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            knowledge_items = result.scalars().all()
            
            return [{
                'knowledge_id': k.knowledge_id,
                'category': k.category,
                'content': k.content,
                'confidence_score': k.confidence_score
            } for k in knowledge_items]
    
    async def increment_knowledge_usage(self, knowledge_id: str):
        """Increment knowledge usage count"""
        async with self.async_session_factory() as session:
            knowledge = await session.get(Knowledge, knowledge_id)
            if knowledge:
                knowledge.usage_count += 1
                knowledge.updated_at = datetime.utcnow()
                await session.commit()
    
    # ========================================================================
    # CHAT OPERATIONS
    # ========================================================================
    
    async def save_chat_message(self, message_data: Dict[str, Any]) -> str:
        """Save chat message"""
        async with self.async_session_factory() as session:
            message = ChatMessageDB(**message_data)
            session.add(message)
            await session.commit()
            return message.message_id
    
    async def get_chat_history(
        self, 
        sender_id: Optional[str] = None, 
        limit: int = 50
    ) -> List[Dict]:
        """Get chat history"""
        async with self.async_session_factory() as session:
            from sqlalchemy import select
            
            query = select(ChatMessageDB).order_by(ChatMessageDB.timestamp.desc())
            
            if sender_id:
                query = query.where(ChatMessageDB.sender_id == sender_id)
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            messages = result.scalars().all()
            
            return [{
                'message_id': m.message_id,
                'sender_id': m.sender_id,
                'content': m.content,
                'timestamp': m.timestamp
            } for m in messages]
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    async def save_performance_metric(self, metric_data: Dict[str, Any]):
        """Save performance metric"""
        async with self.async_session_factory() as session:
            metric = PerformanceMetric(**metric_data)
            session.add(metric)
            await session.commit()
    
    async def get_agent_metrics(
        self, 
        agent_id: str, 
        metric_type: Optional[str] = None,
        days: int = 7
    ) -> List[Dict]:
        """Get agent performance metrics"""
        async with self.async_session_factory() as session:
            from sqlalchemy import select
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(PerformanceMetric).where(
                PerformanceMetric.agent_id == agent_id,
                PerformanceMetric.recorded_at >= cutoff_date
            )
            
            if metric_type:
                query = query.where(PerformanceMetric.metric_type == metric_type)
            
            result = await session.execute(query)
            metrics = result.scalars().all()
            
            return [{
                'metric_type': m.metric_type,
                'metric_value': m.metric_value,
                'recorded_at': m.recorded_at
            } for m in metrics]
    
    # ========================================================================
    # REDIS CACHE OPERATIONS
    # ========================================================================
    
    async def cache_agent_performance(self, agent_id: str, data: Dict[str, Any], ttl: int = 300):
        """Cache agent performance data in Redis"""
        key = f"agent:performance:{agent_id}"
        await self.redis_client.setex(key, ttl, json.dumps(data))
    
    async def get_cached_performance(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get cached performance data"""
        key = f"agent:performance:{agent_id}"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else None
    
    async def cache_knowledge_search(self, query_hash: str, results: List[Dict], ttl: int = 600):
        """Cache knowledge search results"""
        key = f"knowledge:search:{query_hash}"
        await self.redis_client.setex(key, ttl, json.dumps(results))
    
    async def get_cached_search(self, query_hash: str) -> Optional[List[Dict]]:
        """Get cached search results"""
        key = f"knowledge:search:{query_hash}"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else None
    
    async def publish_event(self, channel: str, event: Dict[str, Any]):
        """Publish event to Redis pub/sub"""
        await self.redis_client.publish(channel, json.dumps(event))
    
    async def subscribe_to_events(self, channel: str, callback):
        """Subscribe to events"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(channel)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                event = json.loads(message['data'])
                await callback(event)


# ============================================================================
# DATABASE INTEGRATION FOR LEARNING AGENT
# ============================================================================

class DatabaseIntegratedLearningAgent:
    """Learning Agent with full database integration"""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        self.config = config
        self.db = db_manager
        self.agent_id = config.get('agent_id', 'learning_agent_001')
    
    async def initialize(self):
        """Initialize with database"""
        await self.db.initialize()
        
        # Load agents from database
        agents = await self.db.list_agents()
        print(f"✓ Loaded {len(agents)} agents from database")
        
        # Load knowledge from database
        knowledge_items = await self.db.search_knowledge({}, limit=1000)
        print(f"✓ Loaded {len(knowledge_items)} knowledge items from database")
    
    async def register_agent(self, agent_data: Dict[str, Any]) -> str:
        """Register agent with database persistence"""
        agent_id = await self.db.save_agent(agent_data)
        
        # Initialize performance tracking
        await self.db.save_performance_metric({
            'agent_id': agent_id,
            'metric_type': 'registration',
            'metric_value': 1.0,
            'context': {'role': agent_data['role']}
        })
        
        return agent_id
    
    async def capture_knowledge(
        self, 
        source_agent: str,
        category: str,
        content: Dict[str, Any],
        confidence: float = 0.8
    ) -> str:
        """Capture knowledge with database persistence"""
        knowledge_data = {
            'knowledge_id': str(uuid.uuid4()),
            'category': category,
            'source_agent_id': source_agent,
            'content': content,
            'confidence_score': confidence,
            'applicability_scope': content.get('applicable_to', []),
            'validation_status': 'validated' if confidence > 0.8 else 'pending'
        }
        
        knowledge_id = await self.db.save_knowledge(knowledge_data)
        
        # Cache for quick access
        await self.db.redis_client.setex(
            f"knowledge:{knowledge_id}",
            3600,
            json.dumps(knowledge_data)
        )
        
        # Publish event
        await self.db.publish_event('knowledge:created', {
            'knowledge_id': knowledge_id,
            'source_agent': source_agent,
            'category': category
        })
        
        return knowledge_id
    
    async def search_knowledge_cached(
        self, 
        query: Dict[str, Any], 
        limit: int = 10
    ) -> List[Dict]:
        """Search knowledge with caching"""
        import hashlib
        
        # Create query hash for caching
        query_str = json.dumps(query, sort_keys=True)
        query_hash = hashlib.md5(query_str.encode()).hexdigest()
        
        # Check cache
        cached = await self.db.get_cached_search(query_hash)
        if cached:
            return cached
        
        # Query database
        results = await self.db.search_knowledge(query, limit)
        
        # Cache results
        await self.db.cache_knowledge_search(query_hash, results)
        
        return results


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """Example usage of database-integrated learning agent"""
    
    # Configuration
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/ymera_learning"
    REDIS_URL = "redis://localhost:6379/0"
    
    # Initialize database manager
    db_manager = DatabaseManager(DATABASE_URL, REDIS_URL)
    
    # Create database-integrated learning agent
    config = {
        'agent_id': 'learning_agent_001',
        'knowledge_retention_days': 90
    }
    
    agent = DatabaseIntegratedLearningAgent(config, db_manager)
    
    try:
        await agent.initialize()
        
        # Register an agent
        agent_id = await agent.register_agent({
            'agent_id': 'dev_agent_001',
            'role': 'developer',
            'specializations': ['python', 'backend'],
            'active': True
        })
        print(f"Agent registered: {agent_id}")
        
        # Capture knowledge
        knowledge_id = await agent.capture_knowledge(
            source_agent=agent_id,
            category='technical',
            content={
                'title': 'Best practice for API error handling',
                'description': 'Use structured error responses with proper HTTP codes',
                'applicable_to': ['developer', 'backend']
            },
            confidence=0.9
        )
        print(f"Knowledge captured: {knowledge_id}")
        
        # Search knowledge
        results = await agent.search_knowledge_cached({
            'category': 'technical',
            'min_confidence': 0.7
        })
        print(f"Found {len(results)} knowledge items")
        
    finally:
        await db_manager.close()


if __name__ == "__main__":
    import uuid
    asyncio.run(main())
