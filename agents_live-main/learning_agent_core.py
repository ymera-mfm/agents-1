"""
YMERA Learning Agent - Production Core Engine
Version: 6.0.0 - Enterprise Ready

Responsibilities:
- Knowledge capture and storage from all agent interactions
- Learning pattern recognition and synthesis
- Inter-agent knowledge distribution and synchronization
- Continuous learning from code analysis, user feedback, and agent outcomes
- Knowledge graph maintenance and relationship mapping
- Learning velocity optimization
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import hashlib
import re

# Optional dependencies - Structured logging
try:
    import structlog
# Optional dependencies
try:
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
    HAS_STRUCTLOG = True
except ImportError:
    structlog = None
    HAS_STRUCTLOG = False

# Optional dependencies - SQL ORM
try:
    from sqlalchemy import text, select, and_, or_, func
    from sqlalchemy.ext.asyncio import AsyncSession
    HAS_SQLALCHEMY = True
except ImportError:
    text = None
    select = None
    and_ = None
    or_ = None
    func = None
    AsyncSession = None
    HAS_SQLALCHEMY = False

# Configure structured logging if available
if HAS_STRUCTLOG:
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
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

# Setup logger based on availability
def get_logger():
    if HAS_STRUCTLOG:
        return structlog.get_logger(__name__)
    else:
        return logging.getLogger(__name__)

# Use get_logger() directly wherever logging is needed.

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class AgentRole(Enum):
    """Agent roles in the YMERA platform"""
    MANAGER = "manager"  # Orchestrates and dispatches tasks
    DEVELOPER = "developer"  # Code generation and modification
    TESTER = "tester"  # Quality assurance and testing
    REVIEWER = "reviewer"  # Code review and standards
    VALIDATOR = "validator"  # Validation and verification
    PROJECT_BUILDER = "project_builder"  # Project assembly
    DEBUGGER = "debugger"  # Bug fixing specialist
    OPTIMIZER = "optimizer"  # Performance optimization
    SECURITY_ANALYST = "security_analyst"  # Security review
    DOCUMENTATION = "documentation"  # Documentation specialist
    LEARNING_COORDINATOR = "learning_coordinator"  # This agent


class KnowledgeType(Enum):
    """Types of knowledge in the system"""
    CODE_PATTERN = "code_pattern"
    BUG_SOLUTION = "bug_solution"
    OPTIMIZATION_TECHNIQUE = "optimization_technique"
    TESTING_STRATEGY = "testing_strategy"
    ARCHITECTURE_DECISION = "architecture_decision"
    USER_PREFERENCE = "user_preference"
    ERROR_RESOLUTION = "error_resolution"
    BEST_PRACTICE = "best_practice"
    TOOL_USAGE = "tool_usage"
    COMMUNICATION_PATTERN = "communication_pattern"
    VALIDATION_RULE = "validation_rule"
    PROJECT_STRUCTURE = "project_structure"


class LearningSource(Enum):
    """Sources of learning"""
    USER_FEEDBACK = "user_feedback"
    CODE_ANALYSIS = "code_analysis"
    TEST_RESULTS = "test_results"
    AGENT_INTERACTION = "agent_interaction"
    ERROR_OCCURRENCE = "error_occurrence"
    SUCCESS_PATTERN = "success_pattern"
    PEER_AGENT = "peer_agent"
    EXTERNAL_RESOURCE = "external_resource"


class KnowledgeQuality(Enum):
    """Knowledge quality levels"""
    EXPERIMENTAL = 1  # Newly captured, unproven
    PROMISING = 2  # Some positive outcomes
    VALIDATED = 3  # Multiple successful applications
    PROVEN = 4  # Consistently successful
    GOLD_STANDARD = 5  # Best practice, highly reliable


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class KnowledgeItem:
    """Comprehensive knowledge item"""
    knowledge_id: str
    knowledge_type: KnowledgeType
    source: LearningSource
    source_agent_id: str
    
    # Content
    title: str
    description: str
    content: Dict[str, Any]
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    applicable_roles: List[AgentRole] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    related_knowledge: List[str] = field(default_factory=list)
    
    # Quality metrics
    quality_level: KnowledgeQuality = KnowledgeQuality.EXPERIMENTAL
    confidence_score: float = 0.5
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    code_examples: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Validation
    validated_by: List[str] = field(default_factory=list)
    validation_notes: List[str] = field(default_factory=list)


@dataclass
class LearningEvent:
    """Event that triggers learning"""
    event_id: str
    event_type: str
    source: LearningSource
    source_agent_id: str
    
    # Event data
    data: Dict[str, Any]
    outcome: str  # success, failure, neutral
    
    # Context
    task_context: Dict[str, Any] = field(default_factory=dict)
    code_context: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None
    
    # Extracted insights
    insights: List[str] = field(default_factory=list)
    patterns_detected: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentLearningProfile:
    """Learning profile for each agent"""
    agent_id: str
    role: AgentRole
    
    # Learning statistics
    knowledge_contributed: int = 0
    knowledge_consumed: int = 0
    learning_velocity: float = 0.0  # Knowledge acquired per day
    teaching_score: float = 0.0  # Quality of knowledge shared
    
    # Specializations learned
    specializations: List[str] = field(default_factory=list)
    strength_areas: List[str] = field(default_factory=list)
    improvement_areas: List[str] = field(default_factory=list)
    
    # Knowledge preferences
    preferred_knowledge_types: List[KnowledgeType] = field(default_factory=list)
    learning_style: str = "balanced"  # fast, balanced, thorough
    
    # Interaction patterns
    collaboration_partners: List[str] = field(default_factory=list)
    knowledge_requests: int = 0
    knowledge_shares: int = 0
    
    # Performance
    task_success_rate: float = 0.0
    improvement_rate: float = 0.0
    
    last_active: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeFlow:
    """Tracks knowledge flow between agents"""
    flow_id: str
    source_agent: str
    target_agent: str
    knowledge_id: str
    
    # Flow details
    transmission_method: str  # direct, broadcast, query_response
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Outcome
    received: bool = False
    applied: bool = False
    application_success: Optional[bool] = None
    feedback: Optional[str] = None
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# YMERA LEARNING AGENT
# ============================================================================

class YMERALearningAgent:
    """
    Production-ready Learning Agent for YMERA platform
    
    Core Responsibilities:
    1. Capture knowledge from all agent activities
    2. Analyze and synthesize learning patterns
    3. Distribute knowledge to relevant agents
    4. Maintain knowledge graph and relationships
    5. Optimize inter-agent learning flow
    6. Track learning velocity and effectiveness
    """
    
    def __init__(self, config: Dict[str, Any], db_manager):
        self.config = config
        self.db = db_manager
        self.agent_id = config.get('agent_id', 'learning_coordinator_001')
        self.logger = logger.bind(agent_id=self.agent_id)
        
        # Knowledge storage
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.knowledge_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Agent profiles
        self.agent_profiles: Dict[str, AgentLearningProfile] = {}
        
        # Learning queues
        self.learning_queue = deque(maxlen=10000)
        self.knowledge_distribution_queue = deque(maxlen=5000)
        
        # Flow tracking
        self.knowledge_flows: List[KnowledgeFlow] = []
        self.flow_analytics: Dict[str, Any] = {}
        
        # Pattern recognition
        self.pattern_cache: Dict[str, Any] = {}
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        
        # Real-time learning
        self.active_learning_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Metrics
        self.metrics = {
            'total_knowledge_items': 0,
            'knowledge_flows': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'agents_learning': 0,
            'average_learning_velocity': 0.0,
            'knowledge_quality_distribution': {},
            'pattern_recognition_accuracy': 0.0
        }
        
        # State
        self.initialized = False
        self.running = False
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    async def initialize(self) -> bool:
        """Initialize the learning agent"""
        try:
            self.logger.info("Initializing YMERA Learning Agent")
            
            # Load existing knowledge from database
            await self._load_knowledge_base()
            
            # Load agent profiles
            await self._load_agent_profiles()
            
            # Build knowledge graph
            await self._build_knowledge_graph()
            
            # Initialize pattern recognition
            await self._initialize_pattern_recognition()
            
            # Start background tasks
            self._start_background_tasks()
            
            self.initialized = True
            self.running = True
            
            self.logger.info(
                "Learning Agent initialized",
                knowledge_items=len(self.knowledge_base),
                agents=len(self.agent_profiles)
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Initialization failed", error=str(e))
            return False
    
    async def _load_knowledge_base(self):
        """Load existing knowledge from database"""
        try:
            knowledge_items = await self.db.search_knowledge({}, limit=10000)
            
            for item in knowledge_items:
                knowledge = KnowledgeItem(
                    knowledge_id=item['knowledge_id'],
                    knowledge_type=KnowledgeType(item['category']),
                    source=LearningSource.AGENT_INTERACTION,
                    source_agent_id=item['source_agent_id'],
                    title=item['content'].get('title', 'Untitled'),
                    description=item['content'].get('description', ''),
                    content=item['content'],
                    confidence_score=item['confidence_score'],
                    usage_count=item['usage_count'],
                    success_rate=item['success_rate'],
                    created_at=item['created_at']
                )
                
                self.knowledge_base[knowledge.knowledge_id] = knowledge
            
            self.metrics['total_knowledge_items'] = len(self.knowledge_base)
            
        except Exception as e:
            self.logger.error("Failed to load knowledge base", error=str(e))
    
    async def _load_agent_profiles(self):
        """Load agent learning profiles"""
        try:
            agents = await self.db.list_agents(active_only=False)
            
            for agent_data in agents:
                profile = AgentLearningProfile(
                    agent_id=agent_data['agent_id'],
                    role=AgentRole(agent_data['role']),
                    last_active=agent_data.get('last_active', datetime.utcnow())
                )
                
                self.agent_profiles[profile.agent_id] = profile
            
            self.metrics['agents_learning'] = len(self.agent_profiles)
            
        except Exception as e:
            self.logger.error("Failed to load agent profiles", error=str(e))
    
    async def _build_knowledge_graph(self):
        """Build knowledge relationship graph"""
        for knowledge_id, knowledge in self.knowledge_base.items():
            # Add related knowledge connections
            for related_id in knowledge.related_knowledge:
                self.knowledge_graph[knowledge_id].add(related_id)
                self.knowledge_graph[related_id].add(knowledge_id)
            
            # Connect by tags
            for other_id, other_knowledge in self.knowledge_base.items():
                if other_id != knowledge_id:
                    common_tags = set(knowledge.tags) & set(other_knowledge.tags)
                    if len(common_tags) >= 2:
                        self.knowledge_graph[knowledge_id].add(other_id)
    
    async def _initialize_pattern_recognition(self):
        """Initialize pattern recognition system"""
        # Load historical success patterns
        self.success_patterns = await self._extract_success_patterns()
        self.failure_patterns = await self._extract_failure_patterns()
    
    def _start_background_tasks(self):
        """Start background processing tasks"""
        asyncio.create_task(self._learning_processing_loop())
        asyncio.create_task(self._knowledge_distribution_loop())
        asyncio.create_task(self._pattern_analysis_loop())
        asyncio.create_task(self._quality_assessment_loop())
        asyncio.create_task(self._metrics_update_loop())
    
    # ========================================================================
    # KNOWLEDGE CAPTURE
    # ========================================================================
    
    async def capture_knowledge_from_event(
        self, 
        event: LearningEvent
    ) -> Optional[str]:
        """
        Capture knowledge from a learning event
        
        This is called when:
        - An agent completes a task
        - A user provides feedback
        - Code is analyzed
        - Tests are executed
        - Errors occur and are resolved
        """
        try:
            # Extract knowledge from event
            knowledge_items = await self._extract_knowledge(event)
            
            captured_ids = []
            for knowledge_data in knowledge_items:
                knowledge = KnowledgeItem(
                    knowledge_id=str(uuid.uuid4()),
                    knowledge_type=knowledge_data['type'],
                    source=event.source,
                    source_agent_id=event.source_agent_id,
                    title=knowledge_data['title'],
                    description=knowledge_data['description'],
                    content=knowledge_data['content'],
                    tags=knowledge_data.get('tags', []),
                    applicable_roles=knowledge_data.get('applicable_roles', []),
                    context=event.task_context
                )
                
                # Determine quality based on outcome
                if event.outcome == 'success':
                    knowledge.quality_level = KnowledgeQuality.PROMISING
                    knowledge.confidence_score = 0.7
                    knowledge.success_count = 1
                else:
                    knowledge.quality_level = KnowledgeQuality.EXPERIMENTAL
                    knowledge.confidence_score = 0.3
                
                # Store knowledge
                self.knowledge_base[knowledge.knowledge_id] = knowledge
                
                # Persist to database
                await self._persist_knowledge(knowledge)
                
                # Update knowledge graph
                await self._update_knowledge_graph(knowledge)
                
                # Update agent profile
                await self._update_agent_contribution(event.source_agent_id)
                
                captured_ids.append(knowledge.knowledge_id)
                
                self.logger.info(
                    "Knowledge captured",
                    knowledge_id=knowledge.knowledge_id,
                    type=knowledge.knowledge_type.value,
                    source=event.source.value
                )
            
            # Queue for distribution
            if captured_ids:
                await self._queue_for_distribution(captured_ids, event)
            
            return captured_ids[0] if captured_ids else None
            
        except Exception as e:
            self.logger.error("Knowledge capture failed", error=str(e))
            return None
    
    async def _extract_knowledge(
        self, 
        event: LearningEvent
    ) -> List[Dict[str, Any]]:
        """Extract structured knowledge from learning event"""
        knowledge_items = []
        
        # Analyze event type and extract relevant knowledge
        if event.source == LearningSource.CODE_ANALYSIS:
            knowledge_items.extend(await self._extract_code_knowledge(event))
        
        elif event.source == LearningSource.USER_FEEDBACK:
            knowledge_items.extend(await self._extract_feedback_knowledge(event))
        
        elif event.source == LearningSource.TEST_RESULTS:
            knowledge_items.extend(await self._extract_test_knowledge(event))
        
        elif event.source == LearningSource.ERROR_OCCURRENCE:
            knowledge_items.extend(await self._extract_error_knowledge(event))
        
        elif event.source == LearningSource.AGENT_INTERACTION:
            knowledge_items.extend(await self._extract_interaction_knowledge(event))
        
        return knowledge_items
    
    async def _extract_code_knowledge(
        self, 
        event: LearningEvent
    ) -> List[Dict[str, Any]]:
        """Extract knowledge from code analysis"""
        knowledge_items = []
        
        code = event.code_context
        if not code:
            return knowledge_items
        
        # Detect patterns
        patterns = await self._detect_code_patterns(code)
        
        for pattern in patterns:
            knowledge_items.append({
                'type': KnowledgeType.CODE_PATTERN,
                'title': f"Code Pattern: {pattern['name']}",
                'description': pattern['description'],
                'content': {
                    'pattern': pattern,
                    'code_example': code,
                    'language': event.data.get('language', 'python'),
                    'context': event.task_context
                },
                'tags': [pattern['name'], event.data.get('language', 'python')],
                'applicable_roles': [AgentRole.DEVELOPER, AgentRole.REVIEWER]
            })
        
        return knowledge_items
    
    async def _extract_feedback_knowledge(
        self, 
        event: LearningEvent
    ) -> List[Dict[str, Any]]:
        """Extract knowledge from user feedback"""
        knowledge_items = []
        
        feedback = event.data.get('feedback', '')
        rating = event.data.get('rating', 0)
        
        if rating >= 4:  # Positive feedback
            knowledge_items.append({
                'type': KnowledgeType.USER_PREFERENCE,
                'title': f"User Preference: {event.data.get('aspect', 'General')}",
                'description': feedback,
                'content': {
                    'feedback': feedback,
                    'rating': rating,
                    'aspect': event.data.get('aspect'),
                    'context': event.user_context
                },
                'tags': ['user_preference', 'positive_feedback'],
                'applicable_roles': [AgentRole.MANAGER, AgentRole.DEVELOPER]
            })
        
        return knowledge_items
    
    async def _extract_test_knowledge(
        self, 
        event: LearningEvent
    ) -> List[Dict[str, Any]]:
        """Extract knowledge from test results"""
        knowledge_items = []
        
        test_results = event.data.get('test_results', {})
        
        if test_results.get('passed'):
            knowledge_items.append({
                'type': KnowledgeType.TESTING_STRATEGY,
                'title': f"Effective Test Strategy: {test_results.get('test_type')}",
                'description': "Successful testing approach",
                'content': {
                    'test_type': test_results.get('test_type'),
                    'coverage': test_results.get('coverage'),
                    'approach': test_results.get('approach'),
                    'results': test_results
                },
                'tags': ['testing', 'qa', test_results.get('test_type', 'general')],
                'applicable_roles': [AgentRole.TESTER, AgentRole.DEVELOPER]
            })
        
        return knowledge_items
    
    async def _extract_error_knowledge(
        self, 
        event: LearningEvent
    ) -> List[Dict[str, Any]]:
        """Extract knowledge from errors and resolutions"""
        knowledge_items = []
        
        error_data = event.data
        
        if event.outcome == 'success':  # Error was resolved
            knowledge_items.append({
                'type': KnowledgeType.ERROR_RESOLUTION,
                'title': f"Error Resolution: {error_data.get('error_type')}",
                'description': f"Solution for {error_data.get('error_message')}",
                'content': {
                    'error_type': error_data.get('error_type'),
                    'error_message': error_data.get('error_message'),
                    'resolution': error_data.get('resolution'),
                    'code_fix': error_data.get('code_fix'),
                    'prevention': error_data.get('prevention_tips')
                },
                'tags': ['error_resolution', 'debugging', error_data.get('error_type', 'general')],
                'applicable_roles': [AgentRole.DEBUGGER, AgentRole.DEVELOPER]
            })
        
        return knowledge_items
    
    async def _extract_interaction_knowledge(
        self, 
        event: LearningEvent
    ) -> List[Dict[str, Any]]:
        """Extract knowledge from agent interactions"""
        knowledge_items = []
        
        interaction = event.data
        
        if interaction.get('collaboration_success'):
            knowledge_items.append({
                'type': KnowledgeType.COMMUNICATION_PATTERN,
                'title': f"Effective Collaboration Pattern",
                'description': interaction.get('description', ''),
                'content': {
                    'participants': interaction.get('participants', []),
                    'pattern': interaction.get('pattern'),
                    'outcome': interaction.get('outcome'),
                    'efficiency_gain': interaction.get('efficiency_gain')
                },
                'tags': ['collaboration', 'communication', 'teamwork'],
                'applicable_roles': [AgentRole.MANAGER]
            })
        
        return knowledge_items
    
    async def _detect_code_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Detect patterns in code"""
        patterns = []
        
        # Design patterns
        if 'class' in code and '__init__' in code:
            patterns.append({
                'name': 'class_structure',
                'description': 'Object-oriented class structure',
                'confidence': 0.9
            })
        
        # Async patterns
        if 'async def' in code and 'await' in code:
            patterns.append({
                'name': 'async_pattern',
                'description': 'Asynchronous programming pattern',
                'confidence': 0.95
            })
        
        # Error handling
        if 'try:' in code and 'except' in code:
            patterns.append({
                'name': 'error_handling',
                'description': 'Exception handling pattern',
                'confidence': 0.9
            })
        
        # Context managers
        if 'with ' in code and 'as ' in code:
            patterns.append({
                'name': 'context_manager',
                'description': 'Context manager usage',
                'confidence': 0.85
            })
        
        return patterns
    
    # ========================================================================
    # KNOWLEDGE DISTRIBUTION
    # ========================================================================
    
    async def distribute_knowledge(
        self, 
        knowledge_id: str,
        target_agents: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Distribute knowledge to relevant agents
        
        If target_agents not specified, automatically determines
        which agents would benefit from this knowledge
        """
        try:
            knowledge = self.knowledge_base.get(knowledge_id)
            if not knowledge:
                return {'success': False, 'error': 'Knowledge not found'}
            
            # Determine targets if not specified
            if not target_agents:
                target_agents = await self._identify_relevant_agents(knowledge)
            
            results = {
                'knowledge_id': knowledge_id,
                'targets': len(target_agents),
                'successful': 0,
                'failed': 0,
                'flows': []
            }
            
            for agent_id in target_agents:
                flow = KnowledgeFlow(
                    flow_id=str(uuid.uuid4()),
                    source_agent=knowledge.source_agent_id,
                    target_agent=agent_id,
                    knowledge_id=knowledge_id,
                    transmission_method='automatic_distribution',
                    context=context or {}
                )
                
                success = await self._transfer_knowledge_to_agent(
                    agent_id,
                    knowledge,
                    flow
                )
                
                if success:
                    results['successful'] += 1
                    flow.received = True
                else:
                    results['failed'] += 1
                
                self.knowledge_flows.append(flow)
                results['flows'].append({
                    'agent_id': agent_id,
                    'success': success,
                    'flow_id': flow.flow_id
                })
            
            # Update metrics
            self.metrics['knowledge_flows'] += len(target_agents)
            knowledge.usage_count += len(target_agents)
            
            self.logger.info(
                "Knowledge distributed",
                knowledge_id=knowledge_id,
                successful=results['successful'],
                failed=results['failed']
            )
            
            return results
            
        except Exception as e:
            self.logger.error("Knowledge distribution failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _identify_relevant_agents(
        self, 
        knowledge: KnowledgeItem
    ) -> List[str]:
        """Identify agents that would benefit from knowledge"""
        relevant_agents = []
        
        for agent_id, profile in self.agent_profiles.items():
            # Skip source agent
            if agent_id == knowledge.source_agent_id:
                continue
            
            # Check role applicability
            if profile.role in knowledge.applicable_roles:
                relevant_agents.append(agent_id)
                continue
            
            # Check specializations
            if any(spec in knowledge.tags for spec in profile.specializations):
                relevant_agents.append(agent_id)
                continue
            
            # Check improvement areas
            if knowledge.knowledge_type.value in profile.improvement_areas:
                relevant_agents.append(agent_id)
        
        return relevant_agents
    
    async def _transfer_knowledge_to_agent(
        self,
        agent_id: str,
        knowledge: KnowledgeItem,
        flow: KnowledgeFlow
    ) -> bool:
        """Transfer knowledge to specific agent"""
        try:
            profile = self.agent_profiles.get(agent_id)
            if not profile:
                return False
            
            # Store in agent's knowledge access log
            await self.db.redis_client.lpush(
                f"agent:{agent_id}:knowledge_access",
                json.dumps({
                    'knowledge_id': knowledge.knowledge_id,
                    'flow_id': flow.flow_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'type': knowledge.knowledge_type.value
                })
            )
            
            # Update agent profile
            profile.knowledge_consumed += 1
            profile.last_active = datetime.utcnow()
            
            # Publish event for agent to consume
            await self.db.publish_event(
                f"agent:{agent_id}:knowledge",
                {
                    'type': 'new_knowledge',
                    'knowledge_id': knowledge.knowledge_id,
                    'flow_id': flow.flow_id,
                    'priority': self._calculate_knowledge_priority(knowledge, profile)
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Knowledge transfer failed",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    def _calculate_knowledge_priority(
        self,
        knowledge: KnowledgeItem,
        profile: AgentLearningProfile
    ) -> int:
        """Calculate priority for knowledge transfer"""
        priority = 3  # Medium priority
        
        # High priority if matches improvement areas
        if knowledge.knowledge_type.value in profile.improvement_areas:
            priority = 5
        
        # High priority if high quality
        elif knowledge.quality_level.value >= KnowledgeQuality.VALIDATED.value:
            priority = 4
        
        # Lower priority if experimental
        elif knowledge.quality_level == KnowledgeQuality.EXPERIMENTAL:
            priority = 2
        
        return priority
    
    # ========================================================================
    # KNOWLEDGE QUERY AND SEARCH
    # ========================================================================
    
    async def query_knowledge(
        self,
        query: str,
        requesting_agent_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[KnowledgeItem]:
        """
        Query knowledge base on behalf of an agent
        
        Considers agent's role, specializations, and current context
        to provide most relevant knowledge
        """
        try:
            profile = self.agent_profiles.get(requesting_agent_id)
            
            # Extract query terms
            query_terms = self._extract_query_terms(query)
            
            # Search knowledge base
            results = []
            for knowledge in self.knowledge_base.values():
                score = await self._calculate_relevance_score(
                    knowledge,
                    query_terms,
                    profile,
                    filters
                )
                
                if score > 0.5:
                    results.append((knowledge, score))
            
            # Sort by relevance
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Update profile
            if profile:
                profile.knowledge_requests += 1
            
            # Track query
            await self._track_knowledge_query(
                requesting_agent_id,
                query,
                [k.knowledge_id for k, _ in results[:10]]
            )
            
            return [k for k, _ in results[:20]]
            
        except Exception as e:
            self.logger.error("Knowledge query failed", error=str(e))
            return []
    
    def _extract_query_terms(self, query: str) -> List[str]:
        """Extract meaningful terms from query"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        
        # Tokenize and clean
        terms = re.findall(r'\b\w+\b', query.lower())
        return [t for t in terms if t not in stop_words and len(t) > 2]
    
    async def _calculate_relevance_score(
        self,
        knowledge: KnowledgeItem,
        query_terms: List[str],
        profile: Optional[AgentLearningProfile],
        filters: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate relevance score for knowledge item"""
        score = 0.0
        
        # Text matching
        searchable_text = f"{knowledge.title} {knowledge.description} {' '.join(knowledge.tags)}"
        for term in query_terms:
            if term in searchable_text.lower():
                score += 0.2
        
        # Role matching
        if profile and profile.role in knowledge.applicable_roles:
            score += 0.3
        
        # Quality boost
        score += knowledge.quality_level.value * 0.1
        
        # Confidence boost
        score += knowledge.confidence_score * 0.2
        
        # Success rate boost
        if knowledge.usage_count > 0:
            score += knowledge.success_rate * 0.3
        
        # Apply filters
        if filters:
            if 'knowledge_type' in filters:
                if knowledge.knowledge_type.value == filters['knowledge_type']:
                    score += 0.2
            
            if 'min_quality' in filters:
                if knowledge.quality_level.value < filters['min_quality']:
                    return 0.0
        
        return min(score, 1.0)
    
    async def _track_knowledge_query(
        self,
        agent_id: str,
        query: str,
        result_ids: List[str]
    ):
        """Track knowledge queries for analytics"""
        await self.db.redis_client.lpush(
            f"agent:{agent_id}:queries",
            json.dumps({
                'query': query,
                'results': result_ids,
                'timestamp': datetime.utcnow().isoformat()
            })
        )
    
    # ========================================================================
    # KNOWLEDGE FEEDBACK AND QUALITY
    # ========================================================================
    
    async def record_knowledge_application(
        self,
        knowledge_id: str,
        agent_id: str,
        success: bool,
        feedback: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Record the application of knowledge by an agent
        This helps track effectiveness and improve quality scores
        """
        try:
            knowledge = self.knowledge_base.get(knowledge_id)
            if not knowledge:
                return
            
            # Update knowledge statistics
            knowledge.usage_count += 1
            if success:
                knowledge.success_count += 1
                self.metrics['successful_applications'] += 1
            else:
                knowledge.failure_count += 1
                self.metrics['failed_applications'] += 1
            
            # Recalculate success rate
            knowledge.success_rate = (
                knowledge.success_count / knowledge.usage_count
                if knowledge.usage_count > 0 else 0.0
            )
            
            # Update quality level based on performance
            await self._update_knowledge_quality(knowledge)
            
            # Update confidence score
            knowledge.confidence_score = await self._calculate_confidence_score(knowledge)
            
            # Update knowledge flow
            flow = next(
                (f for f in reversed(self.knowledge_flows) 
                 if f.knowledge_id == knowledge_id and f.target_agent == agent_id),
                None
            )
            if flow:
                flow.applied = True
                flow.application_success = success
                flow.feedback = feedback
            
            # Update agent profile
            profile = self.agent_profiles.get(agent_id)
            if profile and success:
                await self._update_agent_learning_progress(profile, knowledge)
            
            # Persist updates
            await self._persist_knowledge(knowledge)
            
            self.logger.info(
                "Knowledge application recorded",
                knowledge_id=knowledge_id,
                agent_id=agent_id,
                success=success,
                new_quality=knowledge.quality_level.value
            )
            
        except Exception as e:
            self.logger.error("Failed to record knowledge application", error=str(e))
    
    async def _update_knowledge_quality(self, knowledge: KnowledgeItem):
        """Update knowledge quality level based on performance"""
        usage = knowledge.usage_count
        success_rate = knowledge.success_rate
        
        if usage >= 20 and success_rate >= 0.9:
            knowledge.quality_level = KnowledgeQuality.GOLD_STANDARD
        elif usage >= 10 and success_rate >= 0.8:
            knowledge.quality_level = KnowledgeQuality.PROVEN
        elif usage >= 5 and success_rate >= 0.7:
            knowledge.quality_level = KnowledgeQuality.VALIDATED
        elif usage >= 2 and success_rate >= 0.6:
            knowledge.quality_level = KnowledgeQuality.PROMISING
        else:
            knowledge.quality_level = KnowledgeQuality.EXPERIMENTAL
    
    async def _calculate_confidence_score(self, knowledge: KnowledgeItem) -> float:
        """Calculate confidence score based on multiple factors"""
        # Base score from success rate
        score = knowledge.success_rate * 0.5
        
        # Usage volume factor
        usage_factor = min(knowledge.usage_count / 20.0, 1.0) * 0.2
        score += usage_factor
        
        # Validation factor
        validation_factor = len(knowledge.validated_by) * 0.05
        score += min(validation_factor, 0.2)
        
        # Age factor (newer knowledge gets slight boost)
        age_days = (datetime.utcnow() - knowledge.created_at).days
        age_factor = max(0, (30 - age_days) / 30.0) * 0.1
        score += age_factor
        
        return min(score, 1.0)
    
    async def _update_agent_learning_progress(
        self,
        profile: AgentLearningProfile,
        knowledge: KnowledgeItem
    ):
        """Update agent's learning progress"""
        # Update specializations
        for tag in knowledge.tags:
            if tag not in profile.specializations:
                profile.specializations.append(tag)
        
        # Update strength areas if successful application
        knowledge_area = knowledge.knowledge_type.value
        if knowledge_area not in profile.strength_areas:
            profile.strength_areas.append(knowledge_area)
        
        # Remove from improvement areas if now strong
        if knowledge_area in profile.improvement_areas:
            profile.improvement_areas.remove(knowledge_area)
        
        # Update learning velocity
        days_since_creation = (datetime.utcnow() - knowledge.created_at).days
        if days_since_creation > 0:
            profile.learning_velocity = profile.knowledge_consumed / days_since_creation
    
    # ========================================================================
    # INTER-AGENT KNOWLEDGE SHARING
    # ========================================================================
    
    async def facilitate_knowledge_exchange(
        self,
        agent_a_id: str,
        agent_b_id: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Facilitate knowledge exchange between two agents
        Used when Manager Agent identifies collaboration opportunity
        """
        try:
            profile_a = self.agent_profiles.get(agent_a_id)
            profile_b = self.agent_profiles.get(agent_b_id)
            
            if not profile_a or not profile_b:
                return {'success': False, 'error': 'Agent profiles not found'}
            
            # Find complementary knowledge
            knowledge_a_has = await self._get_agent_knowledge(agent_a_id)
            knowledge_b_has = await self._get_agent_knowledge(agent_b_id)
            
            # Find what A can teach B
            a_to_b = await self._find_teaching_opportunities(
                knowledge_a_has,
                profile_b,
                topic
            )
            
            # Find what B can teach A
            b_to_a = await self._find_teaching_opportunities(
                knowledge_b_has,
                profile_a,
                topic
            )
            
            # Create exchange session
            session_id = str(uuid.uuid4())
            exchange = {
                'session_id': session_id,
                'participants': [agent_a_id, agent_b_id],
                'a_to_b': a_to_b,
                'b_to_a': b_to_a,
                'topic': topic,
                'started_at': datetime.utcnow().isoformat()
            }
            
            self.active_learning_sessions[session_id] = exchange
            
            # Update collaboration history
            profile_a.collaboration_partners.append(agent_b_id)
            profile_b.collaboration_partners.append(agent_a_id)
            
            self.logger.info(
                "Knowledge exchange facilitated",
                session_id=session_id,
                agent_a=agent_a_id,
                agent_b=agent_b_id
            )
            
            return {
                'success': True,
                'session_id': session_id,
                'exchange': exchange
            }
            
        except Exception as e:
            self.logger.error("Knowledge exchange failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _get_agent_knowledge(self, agent_id: str) -> List[KnowledgeItem]:
        """Get knowledge items an agent has contributed or mastered"""
        knowledge = []
        
        # Knowledge contributed
        for k in self.knowledge_base.values():
            if k.source_agent_id == agent_id:
                knowledge.append(k)
        
        # Knowledge successfully applied
        for flow in self.knowledge_flows:
            if (flow.target_agent == agent_id and 
                flow.applied and 
                flow.application_success):
                k = self.knowledge_base.get(flow.knowledge_id)
                if k and k not in knowledge:
                    knowledge.append(k)
        
        return knowledge
    
    async def _find_teaching_opportunities(
        self,
        teacher_knowledge: List[KnowledgeItem],
        learner_profile: AgentLearningProfile,
        topic: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Find knowledge that would benefit the learner"""
        opportunities = []
        
        for knowledge in teacher_knowledge:
            # Skip low quality knowledge
            if knowledge.quality_level.value < KnowledgeQuality.PROMISING.value:
                continue
            
            # Check topic match
            if topic and topic.lower() not in knowledge.title.lower():
                continue
            
            # Check if learner would benefit
            relevance = 0.0
            
            # High relevance if matches improvement areas
            if knowledge.knowledge_type.value in learner_profile.improvement_areas:
                relevance += 0.5
            
            # Medium relevance if matches role
            if learner_profile.role in knowledge.applicable_roles:
                relevance += 0.3
            
            # Lower relevance if matches preferred types
            if knowledge.knowledge_type in learner_profile.preferred_knowledge_types:
                relevance += 0.2
            
            if relevance > 0.3:
                opportunities.append({
                    'knowledge_id': knowledge.knowledge_id,
                    'title': knowledge.title,
                    'relevance': relevance,
                    'quality': knowledge.quality_level.value
                })
        
        # Sort by relevance
        opportunities.sort(key=lambda x: x['relevance'], reverse=True)
        
        return opportunities[:5]
    
    # ========================================================================
    # PATTERN RECOGNITION AND SYNTHESIS
    # ========================================================================
    
    async def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns across all agent activities
        Synthesize higher-level insights from individual knowledge items
        """
        try:
            patterns = {
                'success_patterns': [],
                'failure_patterns': [],
                'efficiency_patterns': [],
                'collaboration_patterns': [],
                'code_patterns': [],
                'insights': []
            }
            
            # Analyze success patterns
            patterns['success_patterns'] = await self._analyze_success_patterns()
            
            # Analyze failure patterns
            patterns['failure_patterns'] = await self._analyze_failure_patterns()
            
            # Analyze collaboration effectiveness
            patterns['collaboration_patterns'] = await self._analyze_collaboration_patterns()
            
            # Analyze code patterns
            patterns['code_patterns'] = await self._analyze_code_patterns()
            
            # Generate insights
            patterns['insights'] = await self._synthesize_insights(patterns)
            
            # Cache patterns
            self.pattern_cache = patterns
            
            return patterns
            
        except Exception as e:
            self.logger.error("Pattern analysis failed", error=str(e))
            return {}
    
    async def _analyze_success_patterns(self) -> List[Dict[str, Any]]:
        """Analyze patterns in successful outcomes"""
        success_knowledge = [
            k for k in self.knowledge_base.values()
            if k.success_rate > 0.8 and k.usage_count >= 3
        ]
        
        patterns = []
        
        # Group by type
        by_type = defaultdict(list)
        for k in success_knowledge:
            by_type[k.knowledge_type].append(k)
        
        for knowledge_type, items in by_type.items():
            if len(items) >= 3:
                patterns.append({
                    'type': 'consistent_success',
                    'knowledge_type': knowledge_type.value,
                    'count': len(items),
                    'avg_success_rate': sum(k.success_rate for k in items) / len(items),
                    'description': f"Consistent success in {knowledge_type.value} knowledge"
                })
        
        return patterns
    
    async def _analyze_failure_patterns(self) -> List[Dict[str, Any]]:
        """Analyze patterns in failures to prevent recurrence"""
        failure_knowledge = [
            k for k in self.knowledge_base.values()
            if k.failure_count > k.success_count and k.usage_count >= 2
        ]
        
        patterns = []
        
        # Group by tags
        tag_failures = defaultdict(int)
        for k in failure_knowledge:
            for tag in k.tags:
                tag_failures[tag] += 1
        
        for tag, count in tag_failures.items():
            if count >= 2:
                patterns.append({
                    'type': 'recurring_failure',
                    'tag': tag,
                    'count': count,
                    'description': f"Multiple failures related to {tag}"
                })
        
        return patterns
    
    async def _analyze_collaboration_patterns(self) -> List[Dict[str, Any]]:
        """Analyze collaboration effectiveness patterns"""
        patterns = []
        
        # Analyze knowledge flows between agents
        flow_pairs = defaultdict(list)
        for flow in self.knowledge_flows:
            if flow.applied and flow.application_success is not None:
                pair = tuple(sorted([flow.source_agent, flow.target_agent]))
                flow_pairs[pair].append(flow)
        
        for (agent_a, agent_b), flows in flow_pairs.items():
            success_rate = sum(1 for f in flows if f.application_success) / len(flows)
            
            if success_rate > 0.8 and len(flows) >= 3:
                patterns.append({
                    'type': 'effective_collaboration',
                    'agents': [agent_a, agent_b],
                    'exchanges': len(flows),
                    'success_rate': success_rate,
                    'description': f"Highly effective knowledge sharing"
                })
        
        return patterns
    
    async def _analyze_code_patterns(self) -> List[Dict[str, Any]]:
        """Analyze code-related patterns"""
        code_knowledge = [
            k for k in self.knowledge_base.values()
            if k.knowledge_type == KnowledgeType.CODE_PATTERN
        ]
        
        patterns = []
        
        # Find frequently used patterns
        pattern_usage = defaultdict(int)
        for k in code_knowledge:
            if 'pattern' in k.content:
                pattern_name = k.content['pattern'].get('name')
                if pattern_name:
                    pattern_usage[pattern_name] += k.usage_count
        
        for pattern_name, usage in sorted(pattern_usage.items(), 
                                         key=lambda x: x[1], 
                                         reverse=True)[:5]:
            patterns.append({
                'type': 'popular_code_pattern',
                'pattern': pattern_name,
                'usage_count': usage,
                'description': f"Frequently used: {pattern_name}"
            })
        
        return patterns
    
    async def _synthesize_insights(
        self, 
        patterns: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """Synthesize high-level insights from patterns"""
        insights = []
        
        # Success insights
        if patterns['success_patterns']:
            best_type = max(
                patterns['success_patterns'],
                key=lambda x: x['avg_success_rate']
            )
            insights.append(
                f"Highest success rate in {best_type['knowledge_type']} "
                f"with {best_type['avg_success_rate']:.1%} success"
            )
        
        # Collaboration insights
        if patterns['collaboration_patterns']:
            insights.append(
                f"Identified {len(patterns['collaboration_patterns'])} "
                f"highly effective agent collaborations"
            )
        
        # Failure insights
        if patterns['failure_patterns']:
            insights.append(
                f"Found {len(patterns['failure_patterns'])} areas "
                f"requiring attention to reduce failures"
            )
        
        # Code insights
        if patterns['code_patterns']:
            insights.append(
                f"Team consistently uses {len(patterns['code_patterns'])} "
                f"proven code patterns"
            )
        
        return insights
    
    async def _extract_success_patterns(self) -> List[Dict[str, Any]]:
        """Extract historical success patterns"""
        # Simplified version - in production would analyze historical data
        return []
    
    async def _extract_failure_patterns(self) -> List[Dict[str, Any]]:
        """Extract historical failure patterns"""
        # Simplified version - in production would analyze historical data
        return []
    
    # ========================================================================
    # KNOWLEDGE GRAPH OPERATIONS
    # ========================================================================
    
    async def _update_knowledge_graph(self, knowledge: KnowledgeItem):
        """Update knowledge graph with new relationships"""
        knowledge_id = knowledge.knowledge_id
        
        # Connect to related knowledge
        for related_id in knowledge.related_knowledge:
            self.knowledge_graph[knowledge_id].add(related_id)
            self.knowledge_graph[related_id].add(knowledge_id)
        
        # Connect by similar tags
        for other_id, other in self.knowledge_base.items():
            if other_id == knowledge_id:
                continue
            
            common_tags = set(knowledge.tags) & set(other.tags)
            if len(common_tags) >= 2:
                self.knowledge_graph[knowledge_id].add(other_id)
                self.knowledge_graph[other_id].add(knowledge_id)
        
        # Connect by type
        for other_id, other in self.knowledge_base.items():
            if (other_id != knowledge_id and 
                other.knowledge_type == knowledge.knowledge_type):
                # Weak connection by type
                if len(self.knowledge_graph[knowledge_id]) < 5:
                    self.knowledge_graph[knowledge_id].add(other_id)
    
    async def get_related_knowledge(
        self,
        knowledge_id: str,
        depth: int = 2
    ) -> List[KnowledgeItem]:
        """Get related knowledge items using graph traversal"""
        if knowledge_id not in self.knowledge_graph:
            return []
        
        visited = set()
        related = []
        queue = deque([(knowledge_id, 0)])
        
        while queue:
            current_id, current_depth = queue.popleft()
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            if current_id != knowledge_id:
                knowledge = self.knowledge_base.get(current_id)
                if knowledge:
                    related.append(knowledge)
            
            if current_depth < depth:
                for neighbor_id in self.knowledge_graph[current_id]:
                    if neighbor_id not in visited:
                        queue.append((neighbor_id, current_depth + 1))
        
        return related
    
    # ========================================================================
    # PERSISTENCE
    # ========================================================================
    
    async def _persist_knowledge(self, knowledge: KnowledgeItem):
        """Persist knowledge to database"""
        try:
            knowledge_data = {
                'knowledge_id': knowledge.knowledge_id,
                'category': knowledge.knowledge_type.value,
                'source_agent_id': knowledge.source_agent_id,
                'content': {
                    'title': knowledge.title,
                    'description': knowledge.description,
                    **knowledge.content
                },
                'confidence_score': knowledge.confidence_score,
                'applicability_scope': [r.value for r in knowledge.applicable_roles],
                'prerequisites': knowledge.prerequisites,
                'related_knowledge': knowledge.related_knowledge,
                'validation_status': knowledge.quality_level.value,
                'usage_count': knowledge.usage_count,
                'success_rate': knowledge.success_rate,
                'created_at': knowledge.created_at,
                'updated_at': knowledge.updated_at
            }
            
            await self.db.save_knowledge(knowledge_data)
            
        except Exception as e:
            self.logger.error("Failed to persist knowledge", error=str(e))
    
    async def _update_agent_contribution(self, agent_id: str):
        """Update agent's contribution statistics"""
        profile = self.agent_profiles.get(agent_id)
        if profile:
            profile.knowledge_contributed += 1
            profile.last_active = datetime.utcnow()
    
    async def _queue_for_distribution(
        self,
        knowledge_ids: List[str],
        event: LearningEvent
    ):
        """Queue knowledge for distribution"""
        for knowledge_id in knowledge_ids:
            self.knowledge_distribution_queue.append({
                'knowledge_id': knowledge_id,
                'event': event,
                'queued_at': datetime.utcnow()
            })
    
    # ========================================================================
    # BACKGROUND TASKS
    # ========================================================================
    
    async def _learning_processing_loop(self):
        """Process learning events from queue"""
        while self.running:
            try:
                if self.learning_queue:
                    event = self.learning_queue.popleft()
                    await self.capture_knowledge_from_event(event)
                else:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                self.logger.error("Learning processing error", error=str(e))
                await asyncio.sleep(5)
    
    async def _knowledge_distribution_loop(self):
        """Distribute queued knowledge"""
        while self.running:
            try:
                if self.knowledge_distribution_queue:
                    item = self.knowledge_distribution_queue.popleft()
                    await self.distribute_knowledge(item['knowledge_id'])
                else:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.error("Distribution error", error=str(e))
                await asyncio.sleep(5)
    
    async def _pattern_analysis_loop(self):
        """Periodically analyze patterns"""
        while self.running:
            try:
                await asyncio.sleep(1800)  # Every 30 minutes
                patterns = await self.analyze_patterns()
                
                # Store patterns in Redis for quick access
                await self.db.redis_client.setex(
                    "learning:patterns",
                    3600,
                    json.dumps(patterns, default=str)
                )
                
            except Exception as e:
                self.logger.error("Pattern analysis error", error=str(e))
    
    async def _quality_assessment_loop(self):
        """Periodically assess knowledge quality"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                for knowledge in self.knowledge_base.values():
                    await self._update_knowledge_quality(knowledge)
                    knowledge.confidence_score = await self._calculate_confidence_score(knowledge)
                    
            except Exception as e:
                self.logger.error("Quality assessment error", error=str(e))
    
    async def _metrics_update_loop(self):
        """Update metrics periodically"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Update metrics
                self.metrics['total_knowledge_items'] = len(self.knowledge_base)
                self.metrics['agents_learning'] = len(self.agent_profiles)
                
                # Calculate average learning velocity
                velocities = [p.learning_velocity for p in self.agent_profiles.values()]
                self.metrics['average_learning_velocity'] = (
                    sum(velocities) / len(velocities) if velocities else 0.0
                )
                
                # Knowledge quality distribution
                quality_dist = defaultdict(int)
                for k in self.knowledge_base.values():
                    quality_dist[k.quality_level.value] += 1
                self.metrics['knowledge_quality_distribution'] = dict(quality_dist)
                
                # Store metrics
                await self.db.redis_client.setex(
                    "learning:metrics",
                    120,
                    json.dumps(self.metrics)
                )
                
            except Exception as e:
                self.logger.error("Metrics update error", error=str(e))
    
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
                'total_knowledge': len(self.knowledge_base),
                'active_agents': len([p for p in self.agent_profiles.values() 
                                     if (datetime.utcnow() - p.last_active).days < 1]),
                'knowledge_flows': len(self.knowledge_flows),
                'active_sessions': len(self.active_learning_sessions),
                'learning_queue_size': len(self.learning_queue)
            },
            'metrics': self.metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_agent_learning_report(
        self, 
        agent_id: str
    ) -> Dict[str, Any]:
        """Generate comprehensive learning report for an agent"""
        profile = self.agent_profiles.get(agent_id)
        if not profile:
            return {'error': 'Agent not found'}
        
        # Get agent's knowledge
        contributed = [k for k in self.knowledge_base.values() 
                      if k.source_agent_id == agent_id]
        
        # Get flows
        incoming = [f for f in self.knowledge_flows 
                   if f.target_agent == agent_id]
        outgoing = [f for f in self.knowledge_flows 
                   if f.source_agent == agent_id]
        
        return {
            'agent_id': agent_id,
            'role': profile.role.value,
            'learning_velocity': profile.learning_velocity,
            'knowledge_contributed': len(contributed),
            'knowledge_consumed': len(incoming),
            'knowledge_shared': len(outgoing),
            'specializations': profile.specializations,
            'strength_areas': profile.strength_areas,
            'improvement_areas': profile.improvement_areas,
            'collaboration_partners': profile.collaboration_partners,
            'task_success_rate': profile.task_success_rate,
            'teaching_score': profile.teaching_score,
            'last_active': profile.last_active.isoformat()
        }
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down Learning Agent")
        self.running = False
        
        # Save state
        await self._save_state()
        
        self.logger.info("Learning Agent shutdown complete")
    
    async def _save_state(self):
        """Save agent state"""
        state = {
            'agent_id': self.agent_id,
            'knowledge_count': len(self.knowledge_base),
            'agent_count': len(self.agent_profiles),
            'flows_count': len(self.knowledge_flows),
            'metrics': self.metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.db.redis_client.setex(
            f"learning:state:{self.agent_id}",
            86400,
            json.dumps(state)
        )