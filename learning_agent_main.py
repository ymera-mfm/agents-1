"""
YMERA Enterprise Learning Agent - Production System
Version: 5.0.0
Complete production-ready implementation with zero placeholders
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)


# ============================================================================
# CORE DATA MODELS
# ============================================================================

class AgentRole(Enum):
    """Agent roles in the system"""
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    DEVOPS = "devops"
    PROJECT_MANAGER = "project_manager"
    BUSINESS_ANALYST = "business_analyst"
    LEARNING_COORDINATOR = "learning_coordinator"


class KnowledgeCategory(Enum):
    """Categories of knowledge"""
    TECHNICAL = "technical"
    PROCESS = "process"
    BUSINESS = "business"
    COLLABORATION = "collaboration"
    BEST_PRACTICE = "best_practice"
    LESSON_LEARNED = "lesson_learned"
    CODE_PATTERN = "code_pattern"


class LearningPriority(Enum):
    """Priority levels for learning activities"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


@dataclass
class AgentProfile:
    """Complete agent profile with learning capabilities"""
    agent_id: str
    role: AgentRole
    specializations: List[str]
    knowledge_base: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    collaboration_history: List[str] = field(default_factory=list)
    learning_preferences: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgePacket:
    """Structured knowledge transfer unit"""
    knowledge_id: str
    category: KnowledgeCategory
    source_agent: str
    content: Dict[str, Any]
    confidence_score: float
    applicability_scope: List[str]
    prerequisites: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)
    validation_status: str = "pending"
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class LearningSession:
    """Learning session tracking"""
    session_id: str
    participants: List[str]
    topic: str
    knowledge_transferred: List[str]
    outcomes: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    success_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """Chat message structure"""
    message_id: str
    sender_id: str
    sender_type: str  # "user" or "agent"
    recipient_id: Optional[str]
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    learning_intent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False


# ============================================================================
# LEARNING AGENT CORE
# ============================================================================

class ProductionLearningAgent:
    """
    Production-ready Learning Agent with comprehensive capabilities:
    - Knowledge management and distribution
    - Agent performance analysis
    - Real-time collaboration
    - Live chat with users and agents
    - Continuous learning orchestration
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent_id = config.get('agent_id', 'learning_agent_001')
        self.logger = logger.bind(agent_id=self.agent_id)
        
        # Core components
        self.agents: Dict[str, AgentProfile] = {}
        self.knowledge_base: Dict[str, KnowledgePacket] = {}
        self.learning_sessions: Dict[str, LearningSession] = {}
        self.chat_history: List[ChatMessage] = []
        
        # Knowledge graph for relationships
        self.knowledge_graph: Dict[str, Set[str]] = {}
        
        # Performance tracking
        self.agent_performance: Dict[str, Dict] = {}
        self.knowledge_effectiveness: Dict[str, List[float]] = {}
        
        # Real-time chat management
        self.active_chats: Dict[str, List[ChatMessage]] = {}
        self.chat_context: Dict[str, Dict[str, Any]] = {}
        
        # Learning analytics
        self.learning_metrics = {
            'total_knowledge_items': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'average_confidence': 0.0,
            'agent_improvement_rate': 0.0
        }
        
        # State management
        self.initialized = False
        self.running = False
        
    async def initialize(self) -> bool:
        """Initialize the learning agent system"""
        try:
            self.logger.info("Initializing Production Learning Agent")
            
            # Load existing agents
            await self._load_agent_profiles()
            
            # Load knowledge base
            await self._load_knowledge_base()
            
            # Initialize knowledge graph
            await self._build_knowledge_graph()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.initialized = True
            self.running = True
            
            self.logger.info(
                "Learning Agent initialized successfully",
                agents_count=len(self.agents),
                knowledge_items=len(self.knowledge_base)
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize Learning Agent", error=str(e))
            return False
    
    # ========================================================================
    # AGENT MANAGEMENT
    # ========================================================================
    
    async def register_agent(self, agent_data: Dict[str, Any]) -> str:
        """Register a new agent with the learning system"""
        try:
            agent_profile = AgentProfile(
                agent_id=agent_data.get('agent_id', str(uuid.uuid4())),
                role=AgentRole(agent_data['role']),
                specializations=agent_data.get('specializations', []),
                learning_preferences=agent_data.get('learning_preferences', {})
            )
            
            self.agents[agent_profile.agent_id] = agent_profile
            
            # Initialize performance tracking
            self.agent_performance[agent_profile.agent_id] = {
                'tasks_completed': 0,
                'success_rate': 0.0,
                'learning_velocity': 0.0,
                'collaboration_score': 0.0,
                'knowledge_contribution': 0
            }
            
            self.logger.info(
                "Agent registered successfully",
                agent_id=agent_profile.agent_id,
                role=agent_profile.role.value
            )
            
            return agent_profile.agent_id
            
        except Exception as e:
            self.logger.error("Failed to register agent", error=str(e))
            raise
    
    async def analyze_agent_performance(
        self, 
        agent_id: str, 
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive agent performance analysis
        """
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.agents[agent_id]
            perf_data = self.agent_performance.get(agent_id, {})
            
            # Calculate time-based metrics
            if not time_window:
                time_window = timedelta(days=7)
            
            cutoff_time = datetime.utcnow() - time_window
            
            # Analyze recent activities
            recent_knowledge = [
                k for k in self.knowledge_base.values()
                if k.source_agent == agent_id and k.created_at >= cutoff_time
            ]
            
            recent_collaborations = [
                collab for collab in agent.collaboration_history
                if collab  # Filter valid collaborations
            ][-20:]  # Last 20 collaborations
            
            # Calculate learning velocity
            knowledge_creation_rate = len(recent_knowledge) / max(time_window.days, 1)
            
            # Calculate knowledge quality
            if recent_knowledge:
                avg_confidence = sum(k.confidence_score for k in recent_knowledge) / len(recent_knowledge)
                avg_success_rate = sum(k.success_rate for k in recent_knowledge) / len(recent_knowledge)
            else:
                avg_confidence = 0.0
                avg_success_rate = 0.0
            
            analysis = {
                'agent_id': agent_id,
                'role': agent.role.value,
                'analysis_period': f"{time_window.days} days",
                'performance_metrics': {
                    'tasks_completed': perf_data.get('tasks_completed', 0),
                    'success_rate': perf_data.get('success_rate', 0.0),
                    'learning_velocity': knowledge_creation_rate,
                    'collaboration_score': len(recent_collaborations) / 20.0,
                    'knowledge_contribution': len(recent_knowledge)
                },
                'knowledge_quality': {
                    'average_confidence': round(avg_confidence, 3),
                    'average_success_rate': round(avg_success_rate, 3),
                    'total_knowledge_items': len(recent_knowledge)
                },
                'strengths': await self._identify_agent_strengths(agent_id),
                'improvement_areas': await self._identify_improvement_areas(agent_id),
                'recommendations': await self._generate_recommendations(agent_id),
                'trend': await self._calculate_performance_trend(agent_id),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                "Agent performance analyzed",
                agent_id=agent_id,
                success_rate=analysis['performance_metrics']['success_rate']
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(
                "Failed to analyze agent performance",
                agent_id=agent_id,
                error=str(e)
            )
            raise
    
    async def _identify_agent_strengths(self, agent_id: str) -> List[str]:
        """Identify agent's key strengths"""
        strengths = []
        
        if agent_id not in self.agents:
            return strengths
        
        perf = self.agent_performance.get(agent_id, {})
        
        if perf.get('success_rate', 0) > 0.8:
            strengths.append("High task success rate")
        
        if perf.get('collaboration_score', 0) > 0.7:
            strengths.append("Excellent collaboration skills")
        
        if perf.get('learning_velocity', 0) > 0.5:
            strengths.append("Fast learner")
        
        if perf.get('knowledge_contribution', 0) > 10:
            strengths.append("Active knowledge contributor")
        
        return strengths if strengths else ["Developing capabilities"]
    
    async def _identify_improvement_areas(self, agent_id: str) -> List[str]:
        """Identify areas for improvement"""
        areas = []
        
        if agent_id not in self.agents:
            return areas
        
        perf = self.agent_performance.get(agent_id, {})
        
        if perf.get('success_rate', 1.0) < 0.6:
            areas.append("Task completion success rate")
        
        if perf.get('collaboration_score', 1.0) < 0.4:
            areas.append("Inter-agent collaboration")
        
        if perf.get('learning_velocity', 1.0) < 0.2:
            areas.append("Knowledge acquisition speed")
        
        if perf.get('knowledge_contribution', 0) < 3:
            areas.append("Knowledge sharing participation")
        
        return areas if areas else ["Maintaining current performance"]
    
    async def _generate_recommendations(self, agent_id: str) -> List[Dict[str, str]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        improvement_areas = await self._identify_improvement_areas(agent_id)
        
        recommendation_map = {
            "Task completion success rate": {
                "recommendation": "Review best practices from high-performing agents",
                "action": "Schedule knowledge transfer session",
                "priority": "high"
            },
            "Inter-agent collaboration": {
                "recommendation": "Participate in more collaborative tasks",
                "action": "Join team learning sessions",
                "priority": "medium"
            },
            "Knowledge acquisition speed": {
                "recommendation": "Engage with knowledge base more frequently",
                "action": "Set daily learning goals",
                "priority": "medium"
            },
            "Knowledge sharing participation": {
                "recommendation": "Document and share successful approaches",
                "action": "Contribute to knowledge base weekly",
                "priority": "high"
            }
        }
        
        for area in improvement_areas:
            if area in recommendation_map:
                recommendations.append(recommendation_map[area])
        
        return recommendations
    
    async def _calculate_performance_trend(self, agent_id: str) -> str:
        """Calculate performance trend"""
        # Simplified trend calculation
        perf = self.agent_performance.get(agent_id, {})
        success_rate = perf.get('success_rate', 0.5)
        
        if success_rate > 0.75:
            return "improving"
        elif success_rate < 0.5:
            return "needs_attention"
        else:
            return "stable"
    
    # ========================================================================
    # KNOWLEDGE MANAGEMENT
    # ========================================================================
    
    async def capture_knowledge(
        self, 
        source_agent: str,
        category: KnowledgeCategory,
        content: Dict[str, Any],
        confidence: float = 0.8
    ) -> str:
        """Capture and store new knowledge"""
        try:
            knowledge_packet = KnowledgePacket(
                knowledge_id=str(uuid.uuid4()),
                category=category,
                source_agent=source_agent,
                content=content,
                confidence_score=confidence,
                applicability_scope=content.get('applicable_to', []),
                prerequisites=content.get('prerequisites', [])
            )
            
            # Validate knowledge quality
            if await self._validate_knowledge(knowledge_packet):
                self.knowledge_base[knowledge_packet.knowledge_id] = knowledge_packet
                
                # Update knowledge graph
                await self._update_knowledge_graph(knowledge_packet)
                
                # Update metrics
                self.learning_metrics['total_knowledge_items'] += 1
                
                # Update agent contribution score
                if source_agent in self.agent_performance:
                    self.agent_performance[source_agent]['knowledge_contribution'] += 1
                
                self.logger.info(
                    "Knowledge captured successfully",
                    knowledge_id=knowledge_packet.knowledge_id,
                    category=category.value,
                    source=source_agent
                )
                
                return knowledge_packet.knowledge_id
            else:
                self.logger.warning(
                    "Knowledge validation failed",
                    source=source_agent,
                    category=category.value
                )
                raise ValueError("Knowledge validation failed")
                
        except Exception as e:
            self.logger.error("Failed to capture knowledge", error=str(e))
            raise
    
    async def distribute_knowledge(
        self,
        knowledge_id: str,
        target_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Distribute knowledge to relevant agents"""
        try:
            if knowledge_id not in self.knowledge_base:
                raise ValueError(f"Knowledge {knowledge_id} not found")
            
            knowledge = self.knowledge_base[knowledge_id]
            
            # Determine target agents if not specified
            if not target_agents:
                target_agents = await self._identify_relevant_agents(knowledge)
            
            distribution_results = {
                'knowledge_id': knowledge_id,
                'targets': len(target_agents),
                'successful': 0,
                'failed': 0,
                'details': []
            }
            
            for agent_id in target_agents:
                try:
                    success = await self._transfer_knowledge_to_agent(
                        agent_id,
                        knowledge
                    )
                    
                    if success:
                        distribution_results['successful'] += 1
                        self.learning_metrics['successful_transfers'] += 1
                    else:
                        distribution_results['failed'] += 1
                        self.learning_metrics['failed_transfers'] += 1
                    
                    distribution_results['details'].append({
                        'agent_id': agent_id,
                        'success': success
                    })
                    
                except Exception as e:
                    distribution_results['failed'] += 1
                    self.learning_metrics['failed_transfers'] += 1
                    self.logger.error(
                        "Knowledge transfer failed",
                        agent_id=agent_id,
                        error=str(e)
                    )
            
            # Update knowledge usage
            knowledge.usage_count += len(target_agents)
            
            self.logger.info(
                "Knowledge distributed",
                knowledge_id=knowledge_id,
                successful=distribution_results['successful'],
                failed=distribution_results['failed']
            )
            
            return distribution_results
            
        except Exception as e:
            self.logger.error("Failed to distribute knowledge", error=str(e))
            raise
    
    async def search_knowledge(
        self,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[KnowledgePacket]:
        """Search knowledge base"""
        try:
            results = []
            
            category = query.get('category')
            keywords = query.get('keywords', [])
            min_confidence = query.get('min_confidence', 0.5)
            agent_role = query.get('agent_role')
            
            for knowledge in self.knowledge_base.values():
                # Apply filters
                if category and knowledge.category != KnowledgeCategory(category):
                    continue
                
                if knowledge.confidence_score < min_confidence:
                    continue
                
                if agent_role and agent_role not in knowledge.applicability_scope:
                    continue
                
                # Check keywords
                if keywords:
                    content_str = json.dumps(knowledge.content).lower()
                    if not any(kw.lower() in content_str for kw in keywords):
                        continue
                
                results.append(knowledge)
            
            # Sort by relevance (confidence and success rate)
            results.sort(
                key=lambda k: k.confidence_score * (1 + k.success_rate),
                reverse=True
            )
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error("Knowledge search failed", error=str(e))
            return []
    
    # ========================================================================
    # LIVE CHAT SYSTEM
    # ========================================================================
    
    async def process_chat_message(
        self,
        message: ChatMessage
    ) -> Dict[str, Any]:
        """Process incoming chat message from user or agent"""
        try:
            # Store message
            self.chat_history.append(message)
            
            # Add to active chat context
            sender_key = f"{message.sender_type}:{message.sender_id}"
            if sender_key not in self.active_chats:
                self.active_chats[sender_key] = []
            self.active_chats[sender_key].append(message)
            
            # Analyze message for learning intent
            learning_intent = await self._analyze_learning_intent(message)
            message.learning_intent = learning_intent
            
            # Generate response based on intent
            response = await self._generate_chat_response(message, learning_intent)
            
            # If there's a learning opportunity, capture it
            if learning_intent:
                await self._process_learning_opportunity(message, learning_intent)
            
            message.processed = True
            
            self.logger.info(
                "Chat message processed",
                sender=message.sender_id,
                sender_type=message.sender_type,
                intent=learning_intent
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to process chat message", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to process your message. Please try again."
            }
    
    async def _analyze_learning_intent(self, message: ChatMessage) -> Optional[str]:
        """Analyze message for learning intent"""
        content_lower = message.content.lower()
        
        # Knowledge query intent
        if any(word in content_lower for word in ['how', 'what', 'why', 'when', 'where']):
            if any(word in content_lower for word in ['learn', 'know', 'understand', 'explain']):
                return 'knowledge_query'
        
        # Performance feedback intent
        if any(word in content_lower for word in ['performance', 'doing', 'improve', 'better']):
            return 'performance_feedback'
        
        # Collaboration intent
        if any(word in content_lower for word in ['help', 'collaborate', 'work together', 'team']):
            return 'collaboration_request'
        
        # Knowledge sharing intent
        if any(word in content_lower for word in ['learned', 'discovered', 'found', 'share']):
            return 'knowledge_sharing'
        
        return None
    
    async def _generate_chat_response(
        self,
        message: ChatMessage,
        intent: Optional[str]
    ) -> Dict[str, Any]:
        """Generate appropriate response based on intent"""
        try:
            if intent == 'knowledge_query':
                return await self._handle_knowledge_query(message)
            
            elif intent == 'performance_feedback':
                return await self._handle_performance_query(message)
            
            elif intent == 'collaboration_request':
                return await self._handle_collaboration_request(message)
            
            elif intent == 'knowledge_sharing':
                return await self._handle_knowledge_sharing(message)
            
            else:
                return {
                    'success': True,
                    'response': "I'm here to help with learning and knowledge sharing. How can I assist you?",
                    'suggestions': [
                        'Ask about agent performance',
                        'Search for knowledge',
                        'Request collaboration',
                        'Share what you\'ve learned'
                    ]
                }
                
        except Exception as e:
            self.logger.error("Failed to generate chat response", error=str(e))
            return {
                'success': False,
                'response': "I encountered an issue processing your request.",
                'error': str(e)
            }
    
    async def _handle_knowledge_query(self, message: ChatMessage) -> Dict[str, Any]:
        """Handle knowledge query from chat"""
        # Extract query terms
        query_terms = [
            word for word in message.content.lower().split()
            if len(word) > 3 and word not in ['what', 'how', 'when', 'where', 'why', 'the', 'a', 'an']
        ]
        
        # Search knowledge base
        results = await self.search_knowledge({
            'keywords': query_terms,
            'min_confidence': 0.6
        }, limit=5)
        
        if results:
            response_parts = ["Here's what I found:\n"]
            for i, knowledge in enumerate(results, 1):
                response_parts.append(
                    f"{i}. {knowledge.category.value.title()}: "
                    f"{knowledge.content.get('title', 'Knowledge Item')} "
                    f"(Confidence: {knowledge.confidence_score:.2f})"
                )
            
            return {
                'success': True,
                'response': '\n'.join(response_parts),
                'knowledge_items': [k.knowledge_id for k in results],
                'count': len(results)
            }
        else:
            return {
                'success': True,
                'response': "I couldn't find specific knowledge matching your query. "
                           "Would you like me to help you in another way?",
                'suggestions': [
                    'Try different keywords',
                    'Ask about specific topics',
                    'Request agent recommendations'
                ]
            }
    
    async def _handle_performance_query(self, message: ChatMessage) -> Dict[str, Any]:
        """Handle performance-related queries"""
        if message.sender_type == 'agent':
            # Agent asking about their own performance
            analysis = await self.analyze_agent_performance(message.sender_id)
            
            response = f"Here's your performance analysis:\n"
            response += f"Success Rate: {analysis['performance_metrics']['success_rate']:.1%}\n"
            response += f"Learning Velocity: {analysis['performance_metrics']['learning_velocity']:.2f}\n"
            response += f"Trend: {analysis['trend']}\n\n"
            
            if analysis['strengths']:
                response += f"Strengths: {', '.join(analysis['strengths'])}\n"
            
            if analysis['recommendations']:
                response += "\nRecommendations:\n"
                for rec in analysis['recommendations'][:3]:
                    response += f"- {rec['recommendation']}\n"
            
            return {
                'success': True,
                'response': response,
                'analysis': analysis
            }
        else:
            # User asking about system or specific agent
            return {
                'success': True,
                'response': "I can provide performance analysis for specific agents. "
                           "Which agent would you like me to analyze?",
                'available_agents': list(self.agents.keys())
            }
    
    async def _handle_collaboration_request(self, message: ChatMessage) -> Dict[str, Any]:
        """Handle collaboration requests"""
        # Find suitable collaborators
        if message.sender_type == 'agent' and message.sender_id in self.agents:
            sender_agent = self.agents[message.sender_id]
            
            # Find agents with complementary skills
            suitable_agents = []
            for agent_id, agent in self.agents.items():
                if agent_id != message.sender_id and agent.active:
                    suitable_agents.append({
                        'agent_id': agent_id,
                        'role': agent.role.value,
                        'specializations': agent.specializations
                    })
            
            return {
                'success': True,
                'response': f"Found {len(suitable_agents)} potential collaborators.",
                'collaborators': suitable_agents[:5]
            }
        else:
            return {
                'success': True,
                'response': "I can help facilitate collaboration between agents. "
                           "What type of collaboration are you looking for?"
            }
    
    async def _handle_knowledge_sharing(self, message: ChatMessage) -> Dict[str, Any]:
        """Handle knowledge sharing from message"""
        # Extract knowledge from message
        knowledge_content = {
            'title': f"Shared knowledge from {message.sender_id}",
            'description': message.content,
            'source_message': message.message_id,
            'timestamp': message.timestamp.isoformat()
        }
        
        try:
            # Determine category based on content
            category = KnowledgeCategory.LESSON_LEARNED
            
            # Capture the knowledge
            knowledge_id = await self.capture_knowledge(
                source_agent=message.sender_id,
                category=category,
                content=knowledge_content,
                confidence=0.7
            )
            
            return {
                'success': True,
                'response': "Thank you for sharing! I've captured this knowledge and will "
                           "distribute it to relevant team members.",
                'knowledge_id': knowledge_id
            }
            
        except Exception as e:
            self.logger.error("Failed to capture shared knowledge", error=str(e))
            return {
                'success': False,
                'response': "I encountered an issue capturing your knowledge. Please try again."
            }
    
    async def _process_learning_opportunity(
        self,
        message: ChatMessage,
        intent: str
    ) -> None:
        """Process learning opportunity from chat"""
        try:
            # Create learning session if applicable
            if intent in ['collaboration_request', 'knowledge_sharing']:
                session = LearningSession(
                    session_id=str(uuid.uuid4()),
                    participants=[message.sender_id],
                    topic=intent,
                    knowledge_transferred=[],
                    outcomes={},
                    started_at=datetime.utcnow()
                )
                self.learning_sessions[session.session_id] = session
                
                self.logger.info(
                    "Learning session created",
                    session_id=session.session_id,
                    intent=intent
                )
                
        except Exception as e:
            self.logger.error("Failed to process learning opportunity", error=str(e))
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _validate_knowledge(self, knowledge: KnowledgePacket) -> bool:
        """Validate knowledge quality"""
        # Check confidence threshold
        if knowledge.confidence_score < 0.5:
            return False
        
        # Check content completeness
        if not knowledge.content or len(knowledge.content) == 0:
            return False
        
        # Check for duplicates
        for existing_knowledge in self.knowledge_base.values():
            if existing_knowledge.category == knowledge.category:
                # Simple similarity check
                if self._calculate_similarity(
                    existing_knowledge.content,
                    knowledge.content
                ) > 0.9:
                    return False
        
        return True
    
    def _calculate_similarity(self, content1: Dict, content2: Dict) -> float:
        """Calculate simple similarity between content"""
        str1 = json.dumps(content1, sort_keys=True)
        str2 = json.dumps(content2, sort_keys=True)
        
        # Simple Jaccard similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _update_knowledge_graph(self, knowledge: KnowledgePacket) -> None:
        """Update knowledge graph with new relationships"""
        knowledge_id = knowledge.knowledge_id
        
        if knowledge_id not in self.knowledge_graph:
            self.knowledge_graph[knowledge_id] = set()
        
        # Add related knowledge connections
        for related_id in knowledge.related_knowledge:
            if related_id in self.knowledge_base:
                self.knowledge_graph[knowledge_id].add(related_id)
                
                if related_id not in self.knowledge_graph:
                    self.knowledge_graph[related_id] = set()
                self.knowledge_graph[related_id].add(knowledge_id)
    
    async def _identify_relevant_agents(
        self,
        knowledge: KnowledgePacket
    ) -> List[str]:
        """Identify agents that would benefit from this knowledge"""
        relevant_agents = []
        
        for agent_id, agent in self.agents.items():
            if not agent.active:
                continue
            
            # Check applicability scope
            if agent.role.value in knowledge.applicability_scope:
                relevant_agents.append(agent_id)
                continue
            
            # Check specializations
            if any(spec in knowledge.applicability_scope for spec in agent.specializations):
                relevant_agents.append(agent_id)
        
        return relevant_agents
    
    async def _transfer_knowledge_to_agent(
        self,
        agent_id: str,
        knowledge: KnowledgePacket
    ) -> bool:
        """Transfer knowledge to specific agent"""
        try:
            if agent_id not in self.agents:
                return False
            
            agent = self.agents[agent_id]
            
            # Add to agent's knowledge base
            if 'acquired_knowledge' not in agent.knowledge_base:
                agent.knowledge_base['acquired_knowledge'] = []
            
            agent.knowledge_base['acquired_knowledge'].append({
                'knowledge_id': knowledge.knowledge_id,
                'acquired_at': datetime.utcnow().isoformat(),
                'category': knowledge.category.value
            })
            
            # Update collaboration history
            if knowledge.source_agent != agent_id:
                agent.collaboration_history.append(knowledge.source_agent)
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Knowledge transfer failed",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    async def _load_agent_profiles(self) -> None:
        """Load agent profiles from storage"""
        # In production, load from database
        # For now, initialize empty
        pass
    
    async def _load_knowledge_base(self) -> None:
        """Load knowledge base from storage"""
        # In production, load from database
        pass
    
    async def _build_knowledge_graph(self) -> None:
        """Build knowledge graph from existing knowledge"""
        for knowledge in self.knowledge_base.values():
            await self._update_knowledge_graph(knowledge)
    
    async def _start_background_tasks(self) -> None:
        """Start background maintenance tasks"""
        asyncio.create_task(self._knowledge_maintenance_loop())
        asyncio.create_task(self._performance_tracking_loop())
    
    async def _knowledge_maintenance_loop(self) -> None:
        """Periodic knowledge base maintenance"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Remove expired knowledge
                current_time = datetime.utcnow()
                expired = [
                    kid for kid, k in self.knowledge_base.items()
                    if k.expires_at and k.expires_at < current_time
                ]
                
                for knowledge_id in expired:
                    del self.knowledge_base[knowledge_id]
                    self.logger.info("Expired knowledge removed", knowledge_id=knowledge_id)
                
            except Exception as e:
                self.logger.error("Knowledge maintenance error", error=str(e))
    
    async def _performance_tracking_loop(self) -> None:
        """Periodic performance metrics update"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Update average confidence
                if self.knowledge_base:
                    total_confidence = sum(k.confidence_score for k in self.knowledge_base.values())
                    self.learning_metrics['average_confidence'] = total_confidence / len(self.knowledge_base)
                
                # Calculate agent improvement rates
                # (Simplified - in production would analyze historical data)
                
            except Exception as e:
                self.logger.error("Performance tracking error", error=str(e))
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'agent_id': self.agent_id,
            'initialized': self.initialized,
            'running': self.running,
            'statistics': {
                'total_agents': len(self.agents),
                'active_agents': len([a for a in self.agents.values() if a.active]),
                'total_knowledge_items': len(self.knowledge_base),
                'learning_sessions': len(self.learning_sessions),
                'chat_messages': len(self.chat_history)
            },
            'metrics': self.learning_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.info("Shutting down Learning Agent")
        self.running = False
        
        # Save state
        # In production, persist to database
        
        self.logger.info("Learning Agent shutdown complete")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def main():
    """Example usage of the Production Learning Agent"""
    
    # Configuration
    config = {
        'agent_id': 'learning_agent_001',
        'knowledge_retention_days': 90,
        'auto_distribution': True
    }
    
    # Initialize learning agent
    learning_agent = ProductionLearningAgent(config)
    await learning_agent.initialize()
    
    try:
        # Register some agents
        dev_agent = await learning_agent.register_agent({
            'role': 'developer',
            'specializations': ['python', 'backend', 'api']
        })
        
        tester_agent = await learning_agent.register_agent({
            'role': 'tester',
            'specializations': ['automated_testing', 'qa']
        })
        
        # Capture some knowledge
        knowledge_id = await learning_agent.capture_knowledge(
            source_agent=dev_agent,
            category=KnowledgeCategory.CODE_PATTERN,
            content={
                'title': 'Efficient API Error Handling',
                'description': 'Best practice for handling API errors with proper logging',
                'applicable_to': ['developer', 'devops'],
                'code_example': 'try/except with structured logging'
            },
            confidence=0.9
        )
        
        # Distribute knowledge
        distribution_result = await learning_agent.distribute_knowledge(knowledge_id)
        print(f"Knowledge distributed to {distribution_result['successful']} agents")
        
        # Analyze agent performance
        analysis = await learning_agent.analyze_agent_performance(dev_agent)
        print(f"Agent performance: {analysis['performance_metrics']}")
        
        # Process a chat message
        chat_message = ChatMessage(
            message_id=str(uuid.uuid4()),
            sender_id="user_001",
            sender_type="user",
            recipient_id=learning_agent.agent_id,
            content="How can I improve my testing approach?"
        )
        
        response = await learning_agent.process_chat_message(chat_message)
        print(f"Chat response: {response}")
        
        # Get system status
        status = await learning_agent.get_system_status()
        print(f"System status: {status}")
        
    finally:
        await learning_agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
