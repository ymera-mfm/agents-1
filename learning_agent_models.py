"""
Learning Agent Database Models
Comprehensive data models for knowledge management, learning, and analytics
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from sqlalchemy import Column, String, DateTime, JSON, Integer, Float, Boolean, Text, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship

from shared.database.models import Base


class KnowledgeCategory(str, Enum):
    """Categories of knowledge in the system"""
    CODE_PATTERNS = "code_patterns"
    BEST_PRACTICES = "best_practices"
    ERROR_PATTERNS = "error_patterns"
    ARCHITECTURE = "architecture"
    ALGORITHMS = "algorithms"
    DEBUGGING_TECHNIQUES = "debugging_techniques"
    TESTING_STRATEGIES = "testing_strategies"
    DEPLOYMENT_PROCEDURES = "deployment_procedures"
    SECURITY_PRACTICES = "security_practices"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    USER_FEEDBACK = "user_feedback"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    TOOL_USAGE = "tool_usage"
    INTEGRATION_PATTERNS = "integration_patterns"
    GENERAL = "general"


class LearningType(str, Enum):
    """Types of learning activities"""
    OUTCOME_BASED = "outcome_based"
    FEEDBACK_BASED = "feedback_based"
    INTERACTION_BASED = "interaction_based"
    PATTERN_BASED = "pattern_based"
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"


class InsightType(str, Enum):
    """Types of insights"""
    TREND = "trend"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    OPTIMIZATION = "optimization"
    PREDICTION = "prediction"


class PatternStatus(str, Enum):
    """Status of detected patterns"""
    DETECTED = "detected"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    APPLIED = "applied"


class KnowledgeEntryModel(Base):
    """Knowledge base entries"""
    __tablename__ = "knowledge_entries"
    
    entry_id = Column(String(255), primary_key=True, index=True)
    category = Column(SQLEnum(KnowledgeCategory), nullable=False, index=True)
    
    # Content
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Metadata
    source_agent_id = Column(String(255), nullable=False, index=True)
    tags = Column(JSON, default=[])
    metadata = Column(JSON, default={})
    
    # Quality metrics
    confidence_score = Column(Float, default=0.5)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Versioning
    version = Column(Integer, default=1)
    parent_entry_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(255), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    
    # Relationships
    patterns = relationship("PatternModel", back_populates="knowledge_entry", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_knowledge_category_created', 'category', 'created_at'),
        Index('idx_knowledge_source_category', 'source_agent_id', 'category'),
    )


class LearningSessionModel(Base):
    """Learning sessions tracking"""
    __tablename__ = "learning_sessions"
    
    session_id = Column(String(255), primary_key=True, index=True)
    agent_id = Column(String(255), nullable=False, index=True)
    learning_type = Column(SQLEnum(LearningType), nullable=False)
    
    # Session data
    session_data = Column(JSON, nullable=False)
    learning_objectives = Column(JSON, default=[])
    
    # Results
    knowledge_gained = Column(JSON, default=[])
    patterns_identified = Column(JSON, default=[])
    insights_generated = Column(JSON, default=[])
    
    # Metrics
    duration_seconds = Column(Integer, nullable=True)
    success_score = Column(Float, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_session_agent_started', 'agent_id', 'started_at'),
    )


class PatternModel(Base):
    """Detected patterns in data"""
    __tablename__ = "patterns"
    
    pattern_id = Column(String(255), primary_key=True, index=True)
    knowledge_entry_id = Column(String(255), ForeignKey('knowledge_entries.entry_id'), nullable=True, index=True)
    
    pattern_type = Column(String(100), nullable=False, index=True)
    pattern_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Pattern data
    pattern_data = Column(JSON, nullable=False)
    examples = Column(JSON, default=[])
    
    # Metrics
    confidence = Column(Float, default=0.5)
    frequency = Column(Integer, default=1)
    impact_score = Column(Float, nullable=True)
    
    # Status
    status = Column(SQLEnum(PatternStatus), default=PatternStatus.DETECTED)
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    knowledge_entry = relationship("KnowledgeEntryModel", back_populates="patterns")
    
    __table_args__ = (
        Index('idx_pattern_type_status', 'pattern_type', 'status'),
    )


class InteractionLogModel(Base):
    """Agent interaction logs for learning"""
    __tablename__ = "interaction_logs"
    
    log_id = Column(String(255), primary_key=True, index=True)
    
    source_agent_id = Column(String(255), nullable=False, index=True)
    target_agent_id = Column(String(255), nullable=True, index=True)
    
    interaction_type = Column(String(100), nullable=False, index=True)
    
    # Interaction details
    interaction_data = Column(JSON, nullable=False)
    context = Column(JSON, default={})
    
    # Outcome
    outcome = Column(String(50), nullable=True)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metrics
    duration_ms = Column(Integer, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_interaction_source_timestamp', 'source_agent_id', 'timestamp'),
        Index('idx_interaction_type_timestamp', 'interaction_type', 'timestamp'),
    )


class InsightModel(Base):
    """Generated insights from learning"""
    __tablename__ = "insights"
    
    insight_id = Column(String(255), primary_key=True, index=True)
    insight_type = Column(SQLEnum(InsightType), nullable=False, index=True)
    
    # Insight content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    recommendations = Column(JSON, default=[])
    
    # Insight data
    insight_data = Column(JSON, nullable=False)
    evidence = Column(JSON, default=[])
    
    # Metrics
    confidence = Column(Float, default=0.5)
    importance_score = Column(Float, default=0.5)
    
    # Impact tracking
    viewed_by = Column(JSON, default=[])
    applied_by = Column(JSON, default=[])
    impact_metrics = Column(JSON, default={})
    
    # Status
    status = Column(String(50), default="active")
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_insight_type_generated', 'insight_type', 'generated_at'),
    )


class KnowledgeGraphModel(Base):
    """Knowledge graph relationships"""
    __tablename__ = "knowledge_graph"
    
    edge_id = Column(String(255), primary_key=True, index=True)
    
    source_entry_id = Column(String(255), ForeignKey('knowledge_entries.entry_id'), nullable=False, index=True)
    target_entry_id = Column(String(255), ForeignKey('knowledge_entries.entry_id'), nullable=False, index=True)
    
    relationship_type = Column(String(100), nullable=False)
    
    # Relationship metadata
    strength = Column(Float, default=0.5)
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_reinforced_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_graph_source_target', 'source_entry_id', 'target_entry_id'),
    )


class AgentLearningProfileModel(Base):
    """Learning profile for each agent"""
    __tablename__ = "agent_learning_profiles"
    
    profile_id = Column(String(255), primary_key=True, index=True)
    agent_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Learning statistics
    total_learning_sessions = Column(Integer, default=0)
    knowledge_contributions = Column(Integer, default=0)
    patterns_discovered = Column(Integer, default=0)
    
    # Performance metrics
    average_learning_score = Column(Float, default=0.0)
    knowledge_retention_rate = Column(Float, default=0.0)
    application_success_rate = Column(Float, default=0.0)
    
    # Preferences
    preferred_learning_types = Column(JSON, default=[])
    knowledge_interests = Column(JSON, default=[])
    
    # Profile data
    strengths = Column(JSON, default=[])
    improvement_areas = Column(JSON, default=[])
    learning_history = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeSubscriptionModel(Base):
    """Agent knowledge subscriptions"""
    __tablename__ = "knowledge_subscriptions"
    
    subscription_id = Column(String(255), primary_key=True, index=True)
    agent_id = Column(String(255), nullable=False, index=True)
    
    # Subscription details
    categories = Column(JSON, nullable=False)
    tags = Column(JSON, default=[])
    filters = Column(JSON, default={})
    
    # Delivery settings
    delivery_method = Column(String(50), default="push")
    frequency = Column(String(50), default="immediate")
    
    # Status
    active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_delivery_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_subscription_agent_active', 'agent_id', 'active'),
    )


class FeedbackModel(Base):
    """User and agent feedback for learning"""
    __tablename__ = "feedback"
    
    feedback_id = Column(String(255), primary_key=True, index=True)
    
    # Source
    source_type = Column(String(50), nullable=False)  # user, agent, system
    source_id = Column(String(255), nullable=False, index=True)
    
    # Target
    target_type = Column(String(50), nullable=False)  # agent, task, knowledge
    target_id = Column(String(255), nullable=False, index=True)
    
    # Feedback content
    rating = Column(Integer, nullable=True)  # 1-5
    feedback_text = Column(Text, nullable=True)
    feedback_data = Column(JSON, default={})
    
    # Categories
    positive_aspects = Column(JSON, default=[])
    improvement_areas = Column(JSON, default=[])
    
    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    actions_taken = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_feedback_target_created', 'target_type', 'target_id', 'created_at'),
    )


class ModelVersionModel(Base):
    """ML model versions for learning"""
    __tablename__ = "model_versions"
    
    version_id = Column(String(255), primary_key=True, index=True)
    model_name = Column(String(255), nullable=False, index=True)
    version_number = Column(String(50), nullable=False)
    
    # Model details
    model_type = Column(String(100), nullable=False)
    model_path = Column(String(500), nullable=False)
    
    # Training info
    training_data_size = Column(Integer, default=0)
    training_duration_seconds = Column(Integer, nullable=True)
    training_metrics = Column(JSON, default={})
    
    # Performance
    validation_metrics = Column(JSON, default={})
    test_metrics = Column(JSON, default={})
    
    # Status
    status = Column(String(50), default="training")  # training, deployed, archived
    deployed_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_model_name_version', 'model_name', 'version_number'),
    )


# Dataclasses for API requests/responses

@dataclass
class KnowledgeEntry:
    """Knowledge entry data"""
    entry_id: str
    category: KnowledgeCategory
    content: str
    source_agent_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.5


@dataclass
class LearningSession:
    """Learning session data"""
    session_id: str
    agent_id: str
    learning_type: LearningType
    session_data: Dict[str, Any]
    learning_objectives: List[str] = field(default_factory=list)


@dataclass
class Pattern:
    """Pattern data"""
    pattern_id: str
    pattern_type: str
    pattern_data: Dict[str, Any]
    confidence: float = 0.5
    pattern_name: Optional[str] = None
    description: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Insight:
    """Insight data"""
    insight_id: str
    insight_type: InsightType
    title: str
    description: str
    recommendations: List[str]
    confidence: float = 0.5
    importance_score: float = 0.5
    evidence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class KnowledgeRequest:
    """Knowledge request data"""
    agent_id: str
    query: str
    category: Optional[KnowledgeCategory] = None
    tags: List[str] = field(default_factory=list)
    urgency: str = "normal"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningOutcome:
    """Learning outcome data"""
    task_id: str
    agent_id: str
    task_type: str
    success: bool
    outcome: str
    details: Dict[str, Any]
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeSubscription:
    """Knowledge subscription data"""
    subscription_id: str
    agent_id: str
    categories: List[KnowledgeCategory]
    tags: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentLearningProfile:
    """Agent learning profile data"""
    agent_id: str
    total_learning_sessions: int
    knowledge_contributions: int
    patterns_discovered: int
    average_learning_score: float
    knowledge_retention_rate: float
    application_success_rate: float
    strengths: List[str]
    improvement_areas: List[str]
    preferred_learning_types: List[LearningType]
    knowledge_interests: List[KnowledgeCategory]
