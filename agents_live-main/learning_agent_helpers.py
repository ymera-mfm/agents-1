"""
Learning Agent Helper Modules
Additional utility classes and functions
"""

import uuid
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


# ============================================================================
# Agent Communicator
# ============================================================================

class AgentCommunicator:
    """Handles communication between learning agent and other agents"""
    
    def __init__(self, message_broker, learning_agent):
        self.broker = message_broker
        self.learning_agent = learning_agent
    
    async def send_knowledge(
        self,
        target_agent_id: str,
        knowledge_data: Dict[str, Any],
        source_agent_id: str
    ):
        """Send knowledge to a specific agent"""
        try:
            await self.broker.publish(
                f"agent.{target_agent_id}.knowledge",
                {
                    "type": "knowledge_delivery",
                    "source": source_agent_id,
                    "knowledge": knowledge_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info("Knowledge sent to agent",
                       target=target_agent_id,
                       source=source_agent_id)
            
        except Exception as e:
            logger.error("Failed to send knowledge", error=str(e))
    
    async def send_knowledge_response(
        self,
        agent_id: str,
        knowledge_data: List[Dict[str, Any]],
        query: str
    ):
        """Send knowledge in response to request"""
        try:
            await self.broker.publish(
                f"agent.{agent_id}.knowledge_response",
                {
                    "type": "knowledge_response",
                    "query": query,
                    "results": knowledge_data,
                    "count": len(knowledge_data),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error("Failed to send response", error=str(e))
    
    async def notify_new_knowledge(
        self,
        agent_id: str,
        knowledge_id: str,
        category: str,
        preview: str
    ):
        """Notify agent about new knowledge"""
        try:
            await self.broker.publish(
                f"agent.{agent_id}.notifications",
                {
                    "type": "new_knowledge",
                    "knowledge_id": knowledge_id,
                    "category": category,
                    "preview": preview,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error("Failed to notify agent", error=str(e))
    
    async def broadcast_insight(
        self,
        insight: Dict[str, Any],
        target_agents: Optional[List[str]] = None
    ):
        """Broadcast insight to agents"""
        try:
            channel = "agent.broadcast.insights"
            
            await self.broker.publish(
                channel,
                {
                    "type": "insight",
                    "insight": insight,
                    "target_agents": target_agents,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error("Failed to broadcast insight", error=str(e))


# ============================================================================
# Model Trainer
# ============================================================================

class ModelTrainer:
    """Trains and manages ML models for learning"""
    
    def __init__(self, db_session: AsyncSession, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.models = {}
    
    async def start(self):
        """Start model trainer"""
        logger.info("Model Trainer started")
    
    async def stop(self):
        """Stop model trainer"""
        logger.info("Model Trainer stopped")
    
    async def train_models(self):
        """Train all models"""
        try:
            # Train agent performance models
            await self._train_agent_models()
            
            # Train pattern recognition models
            await self._train_pattern_models()
            
            # Train recommendation models
            await self._train_recommendation_models()
            
            logger.info("Models trained successfully")
            
        except Exception as e:
            logger.error("Model training failed", error=str(e))
    
    async def update_agent_model(
        self,
        agent_id: str,
        task_type: str,
        outcome: str,
        success: bool
    ):
        """Update agent-specific model with new data"""
        try:
            # Store training data
            model_key = f"agent_model:{agent_id}:{task_type}"
            
            if model_key not in self.models:
                self.models[model_key] = {
                    "successes": 0,
                    "failures": 0,
                    "total": 0
                }
            
            model = self.models[model_key]
            model['total'] += 1
            
            if success:
                model['successes'] += 1
            else:
                model['failures'] += 1
            
            # Retrain if enough new data
            if model['total'] % 10 == 0:
                await self._retrain_agent_model(agent_id, task_type)
            
        except Exception as e:
            logger.error("Failed to update agent model", error=str(e))
    
    async def _train_agent_models(self):
        """Train agent performance prediction models"""
        # Simplified - in production, use actual ML libraries
        logger.debug("Training agent models")
    
    async def _train_pattern_models(self):
        """Train pattern recognition models"""
        logger.debug("Training pattern models")
    
    async def _train_recommendation_models(self):
        """Train recommendation models"""
        logger.debug("Training recommendation models")
    
    async def _retrain_agent_model(self, agent_id: str, task_type: str):
        """Retrain specific agent model"""
        logger.debug("Retraining agent model",
                    agent_id=agent_id,
                    task_type=task_type)


# ============================================================================
# Learning Analytics
# ============================================================================

class LearningAnalytics:
    """Analytics for learning activities"""
    
    def __init__(self, db_session: AsyncSession, cache_manager):
        self.db = db_session
        self.cache = cache_manager
    
    async def generate_report(
        self,
        time_period: timedelta
    ) -> Dict[str, Any]:
        """Generate comprehensive learning report"""
        try:
            cutoff = datetime.utcnow() - time_period
            
            from ..models import (
                KnowledgeEntryModel, LearningSessionModel,
                PatternModel, InsightModel
            )
            
            # Knowledge statistics
            knowledge_stmt = select(func.count(KnowledgeEntryModel.entry_id)).where(
                and_(
                    KnowledgeEntryModel.created_at >= cutoff,
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            )
            knowledge_result = await self.db.execute(knowledge_stmt)
            new_knowledge = knowledge_result.scalar() or 0
            
            # Learning sessions
            session_stmt = select(func.count(LearningSessionModel.session_id)).where(
                LearningSessionModel.started_at >= cutoff
            )
            session_result = await self.db.execute(session_stmt)
            total_sessions = session_result.scalar() or 0
            
            # Patterns detected
            pattern_stmt = select(func.count(PatternModel.pattern_id)).where(
                PatternModel.detected_at >= cutoff
            )
            pattern_result = await self.db.execute(pattern_stmt)
            patterns_detected = pattern_result.scalar() or 0
            
            # Insights generated
            insight_stmt = select(func.count(InsightModel.insight_id)).where(
                InsightModel.generated_at >= cutoff
            )
            insight_result = await self.db.execute(insight_stmt)
            insights_generated = insight_result.scalar() or 0
            
            # Top categories
            category_stmt = select(
                KnowledgeEntryModel.category,
                func.count(KnowledgeEntryModel.entry_id).label('count')
            ).where(
                and_(
                    KnowledgeEntryModel.created_at >= cutoff,
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            ).group_by(
                KnowledgeEntryModel.category
            ).order_by(
                desc('count')
            ).limit(5)
            
            category_result = await self.db.execute(category_stmt)
            top_categories = [
                {"category": cat, "count": count}
                for cat, count in category_result.fetchall()
            ]
            
            return {
                "period_days": time_period.days,
                "knowledge_created": new_knowledge,
                "learning_sessions": total_sessions,
                "patterns_detected": patterns_detected,
                "insights_generated": insights_generated,
                "top_categories": top_categories,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to generate report", error=str(e))
            return {}
    
    async def get_agent_profile(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed agent learning profile"""
        try:
            from ..models import (
                AgentLearningProfileModel, LearningSessionModel,
                KnowledgeEntryModel
            )
            
            # Get profile
            profile_stmt = select(AgentLearningProfileModel).where(
                AgentLearningProfileModel.agent_id == agent_id
            )
            profile_result = await self.db.execute(profile_stmt)
            profile = profile_result.scalar_one_or_none()
            
            if not profile:
                return {
                    "agent_id": agent_id,
                    "message": "No learning profile found"
                }
            
            # Recent sessions
            session_stmt = select(LearningSessionModel).where(
                LearningSessionModel.agent_id == agent_id
            ).order_by(
                desc(LearningSessionModel.started_at)
            ).limit(10)
            
            session_result = await self.db.execute(session_stmt)
            recent_sessions = session_result.scalars().all()
            
            # Knowledge contributions
            contrib_stmt = select(func.count(KnowledgeEntryModel.entry_id)).where(
                and_(
                    KnowledgeEntryModel.source_agent_id == agent_id,
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            )
            contrib_result = await self.db.execute(contrib_stmt)
            contributions = contrib_result.scalar() or 0
            
            return {
                "agent_id": agent_id,
                "total_learning_sessions": profile.total_learning_sessions,
                "knowledge_contributions": contributions,
                "patterns_discovered": profile.patterns_discovered,
                "average_learning_score": profile.average_learning_score,
                "knowledge_retention_rate": profile.knowledge_retention_rate,
                "application_success_rate": profile.application_success_rate,
                "strengths": profile.strengths,
                "improvement_areas": profile.improvement_areas,
                "preferred_learning_types": profile.preferred_learning_types,
                "knowledge_interests": profile.knowledge_interests,
                "recent_sessions": [
                    {
                        "session_id": s.session_id,
                        "type": s.learning_type,
                        "started_at": s.started_at.isoformat(),
                        "success_score": s.success_score
                    }
                    for s in recent_sessions
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to get agent profile", error=str(e))
            return {}


# ============================================================================
# Lifecycle Manager
# ============================================================================

class AgentLifecycleManager:
    """Manages agent lifecycle in context of learning"""
    
    def __init__(self, db_session: AsyncSession, learning_agent):
        self.db = db_session
        self.learning_agent = learning_agent
    
    async def activate_agent(self, agent_id: str) -> Dict[str, Any]:
        """Activate agent for learning"""
        try:
            # Create learning profile if doesn't exist
            from ..models import AgentLearningProfileModel
            
            stmt = select(AgentLearningProfileModel).where(
                AgentLearningProfileModel.agent_id == agent_id
            )
            result = await self.db.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if not profile:
                profile = AgentLearningProfileModel(
                    profile_id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    total_learning_sessions=0,
                    knowledge_contributions=0,
                    patterns_discovered=0,
                    average_learning_score=0.0,
                    knowledge_retention_rate=0.0,
                    application_success_rate=0.0,
                    preferred_learning_types=[],
                    knowledge_interests=[],
                    strengths=[],
                    improvement_areas=[],
                    learning_history=[],
                    created_at=datetime.utcnow()
                )
                
                self.db.add(profile)
                await self.db.commit()
            
            logger.info("Agent activated for learning", agent_id=agent_id)
            
            return {
                "status": "activated",
                "agent_id": agent_id,
                "profile_created": profile is None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to activate agent", error=str(e))
            raise


# ============================================================================
# Knowledge Validator
# ============================================================================

class KnowledgeValidator:
    """Validates knowledge quality and accuracy"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def validate_knowledge(
        self,
        entry_id: str,
        content: str,
        category: str
    ) -> Dict[str, Any]:
        """Validate knowledge entry"""
        try:
            validation_result = {
                "valid": True,
                "confidence": 0.7,
                "issues": [],
                "recommendations": []
            }
            
            # Check content length
            if len(content) < 50:
                validation_result["issues"].append("Content too short")
                validation_result["confidence"] -= 0.2
            
            # Check for code patterns in non-code categories
            if "```" in content and category != "code_patterns":
                validation_result["recommendations"].append(
                    "Consider categorizing as code_patterns"
                )
            
            # Check for proper formatting
            if not content.strip():
                validation_result["valid"] = False
                validation_result["issues"].append("Empty content")
            
            return validation_result
            
        except Exception as e:
            logger.error("Validation failed", error=str(e))
            return {"valid": False, "error": str(e)}


# ============================================================================
# Performance Tracker
# ============================================================================

class PerformanceTracker:
    """Tracks learning system performance"""
    
    def __init__(self):
        self.metrics = {
            "operations": 0,
            "avg_latency": 0.0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def record_operation(self, latency: float, success: bool):
        """Record operation metrics"""
        self.metrics["operations"] += 1
        
        # Update average latency
        current_avg = self.metrics["avg_latency"]
        n = self.metrics["operations"]
        self.metrics["avg_latency"] = ((current_avg * (n - 1)) + latency) / n
        
        if not success:
            self.metrics["errors"] += 1
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics["cache_misses"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        total_cache = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        hit_rate = (
            self.metrics["cache_hits"] / total_cache 
            if total_cache > 0 else 0
        )
        
        return {
            **self.metrics,
            "cache_hit_rate": hit_rate,
            "error_rate": (
                self.metrics["errors"] / self.metrics["operations"]
                if self.metrics["operations"] > 0 else 0
            )
        }
    
    def reset(self):
        """Reset metrics"""
        self.metrics = {
            "operations": 0,
            "avg_latency": 0.0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }


# ============================================================================
# Utility Functions
# ============================================================================

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity (simplified)"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text"""
    # Simplified keyword extraction
    words = text.lower().split()
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
        'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were'
    }
    
    keywords = [w for w in words if len(w) > 3 and w not in stop_words]
    
    # Return most frequent keywords
    from collections import Counter
    keyword_freq = Counter(keywords)
    return [kw for kw, _ in keyword_freq.most_common(max_keywords)]


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    import re
    # Convert to lowercase
    text = text.lower()
    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text


def calculate_confidence_score(
    usage_count: int,
    success_rate: float,
    age_days: int
) -> float:
    """Calculate confidence score for knowledge"""
    # Base score from success rate
    score = success_rate * 0.5
    
    # Popularity component
    popularity = min(usage_count / 20, 0.3)
    score += popularity
    
    # Freshness component (decay over time)
    if age_days > 180:
        freshness = 0.2 * (1 - min((age_days - 180) / 365, 0.5))
    else:
        freshness = 0.2
    score += freshness
    
    return min(score, 1.0)


def format_insight(insight: Dict[str, Any]) -> str:
    """Format insight for display"""
    return f"""
Insight: {insight.get('title', 'Untitled')}
Type: {insight.get('type', 'Unknown')}
Confidence: {insight.get('confidence', 0):.0%}
Importance: {insight.get('importance_score', 0):.0%}

{insight.get('description', 'No description available')}

Recommendations:
{chr(10).join(f"- {rec}" for rec in insight.get('recommendations', []))}
"""


def calculate_learning_velocity(
    sessions: List[Dict[str, Any]],
    time_period_days: int
) -> float:
    """Calculate learning velocity (sessions per day)"""
    if not sessions or time_period_days == 0:
        return 0.0
    
    return len(sessions) / time_period_days


def identify_learning_trends(
    history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Identify trends in learning history"""
    if not history:
        return {"trend": "insufficient_data"}
    
    # Sort by timestamp
    sorted_history = sorted(history, key=lambda x: x.get('timestamp', ''))
    
    # Calculate trend
    recent = sorted_history[-10:]  # Last 10 sessions
    older = sorted_history[-20:-10] if len(sorted_history) > 10 else []
    
    if older:
        recent_avg = sum(s.get('score', 0) for s in recent) / len(recent)
        older_avg = sum(s.get('score', 0) for s in older) / len(older)
        
        if recent_avg > older_avg * 1.1:
            trend = "improving"
        elif recent_avg < older_avg * 0.9:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "new_learner"
    
    return {
        "trend": trend,
        "recent_sessions": len(recent),
        "average_score": sum(s.get('score', 0) for s in recent) / len(recent) if recent else 0
    }


# ============================================================================
# Knowledge Quality Scorer
# ============================================================================

class KnowledgeQualityScorer:
    """Scores knowledge quality based on multiple factors"""
    
    @staticmethod
    def score_knowledge(
        content: str,
        metadata: Dict[str, Any],
        usage_count: int,
        success_rate: float,
        age_days: int
    ) -> float:
        """Calculate overall quality score"""
        scores = {
            "completeness": KnowledgeQualityScorer._score_completeness(content, metadata),
            "clarity": KnowledgeQualityScorer._score_clarity(content),
            "usefulness": KnowledgeQualityScorer._score_usefulness(usage_count, success_rate),
            "freshness": KnowledgeQualityScorer._score_freshness(age_days)
        }
        
        # Weighted average
        weights = {
            "completeness": 0.3,
            "clarity": 0.2,
            "usefulness": 0.3,
            "freshness": 0.2
        }
        
        total_score = sum(scores[k] * weights[k] for k in scores)
        
        return round(total_score, 2)
    
    @staticmethod
    def _score_completeness(content: str, metadata: Dict[str, Any]) -> float:
        """Score completeness of knowledge"""
        score = 0.5  # Base score
        
        # Check content length
        if len(content) > 200:
            score += 0.2
        if len(content) > 500:
            score += 0.1
        
        # Check metadata
        if metadata.get('tags'):
            score += 0.1
        if metadata.get('examples'):
            score += 0.1
        
        return min(score, 1.0)
    
    @staticmethod
    def _score_clarity(content: str) -> float:
        """Score clarity of knowledge"""
        score = 0.5
        
        # Check for structure (headings, lists, code blocks)
        if '\n' in content:
            score += 0.2
        if any(marker in content for marker in ['1.', '2.', '-', '*']):
            score += 0.2
        if '```' in content:
            score += 0.1
        
        return min(score, 1.0)
    
    @staticmethod
    def _score_usefulness(usage_count: int, success_rate: float) -> float:
        """Score usefulness based on usage and success"""
        # Usage component
        usage_score = min(usage_count / 50, 0.5)
        
        # Success component
        success_score = success_rate * 0.5
        
        return usage_score + success_score
    
    @staticmethod
    def _score_freshness(age_days: int) -> float:
        """Score freshness of knowledge"""
        if age_days < 30:
            return 1.0
        elif age_days < 90:
            return 0.8
        elif age_days < 180:
            return 0.6
        elif age_days < 365:
            return 0.4
        else:
            return max(0.2, 1.0 - (age_days / 730))


# ============================================================================
# Pattern Analyzer
# ============================================================================

class PatternAnalyzer:
    """Advanced pattern analysis utilities"""
    
    @staticmethod
    def analyze_frequency_pattern(
        data: List[Dict[str, Any]],
        key: str
    ) -> Dict[str, Any]:
        """Analyze frequency patterns in data"""
        from collections import Counter
        
        values = [item.get(key) for item in data if key in item]
        freq = Counter(values)
        
        if not freq:
            return {"pattern": "no_data"}
        
        total = len(values)
        most_common = freq.most_common(1)[0]
        
        return {
            "pattern": "frequency",
            "most_common": most_common[0],
            "frequency": most_common[1],
            "percentage": (most_common[1] / total) * 100,
            "unique_values": len(freq),
            "distribution": dict(freq.most_common(5))
        }
    
    @staticmethod
    def analyze_temporal_pattern(
        timestamps: List[datetime]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns"""
        if not timestamps:
            return {"pattern": "no_data"}
        
        # Sort timestamps
        sorted_times = sorted(timestamps)
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(sorted_times)):
            interval = (sorted_times[i] - sorted_times[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return {"pattern": "single_event"}
        
        avg_interval = sum(intervals) / len(intervals)
        
        # Determine pattern type
        if avg_interval < 300:  # < 5 minutes
            pattern_type = "burst"
        elif avg_interval < 3600:  # < 1 hour
            pattern_type = "frequent"
        elif avg_interval < 86400:  # < 1 day
            pattern_type = "regular"
        else:
            pattern_type = "sporadic"
        
        return {
            "pattern": "temporal",
            "type": pattern_type,
            "average_interval_seconds": avg_interval,
            "total_events": len(timestamps),
            "time_span_days": (sorted_times[-1] - sorted_times[0]).days
        }
    
    @staticmethod
    def detect_correlation(
        data1: List[float],
        data2: List[float]
    ) -> float:
        """Detect correlation between two data series"""
        if len(data1) != len(data2) or len(data1) < 2:
            return 0.0
        
        # Calculate Pearson correlation coefficient (simplified)
        n = len(data1)
        
        mean1 = sum(data1) / n
        mean2 = sum(data2) / n
        
        numerator = sum((data1[i] - mean1) * (data2[i] - mean2) for i in range(n))
        
        denom1 = sum((x - mean1) ** 2 for x in data1) ** 0.5
        denom2 = sum((x - mean2) ** 2 for x in data2) ** 0.5
        
        if denom1 == 0 or denom2 == 0:
            return 0.0
        
        correlation = numerator / (denom1 * denom2)
        
        return round(correlation, 3)


# ============================================================================
# Knowledge Merger
# ============================================================================

class KnowledgeMerger:
    """Merges similar or duplicate knowledge entries"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def find_duplicates(
        self,
        similarity_threshold: float = 0.8
    ) -> List[List[str]]:
        """Find potential duplicate knowledge entries"""
        from ..models import KnowledgeEntryModel
        
        try:
            # Get all active knowledge
            stmt = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.deleted_at.is_(None)
            )
            result = await self.db.execute(stmt)
            entries = result.scalars().all()
            
            # Find similar pairs
            duplicates = []
            checked = set()
            
            for i, entry1 in enumerate(entries):
                for entry2 in entries[i+1:]:
                    pair_key = tuple(sorted([entry1.entry_id, entry2.entry_id]))
                    
                    if pair_key in checked:
                        continue
                    
                    checked.add(pair_key)
                    
                    # Check similarity
                    similarity = calculate_similarity(
                        entry1.content,
                        entry2.content
                    )
                    
                    if similarity >= similarity_threshold:
                        duplicates.append([entry1.entry_id, entry2.entry_id])
            
            return duplicates
            
        except Exception as e:
            logger.error("Failed to find duplicates", error=str(e))
            return []
    
    async def merge_entries(
        self,
        entry_ids: List[str],
        merged_by: str
    ) -> str:
        """Merge multiple entries into one"""
        from ..models import KnowledgeEntryModel
        
        try:
            if len(entry_ids) < 2:
                raise ValueError("At least 2 entries required for merge")
            
            # Get all entries
            stmt = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.entry_id.in_(entry_ids)
            )
            result = await self.db.execute(stmt)
            entries = result.scalars().all()
            
            if len(entries) != len(entry_ids):
                raise ValueError("Some entries not found")
            
            # Create merged entry
            merged_content = self._merge_content([e.content for e in entries])
            merged_tags = list(set(tag for e in entries for tag in e.tags))
            merged_metadata = self._merge_metadata([e.metadata for e in entries])
            
            # Use best quality entry as base
            best_entry = max(entries, key=lambda e: e.confidence_score)
            
            merged_entry = KnowledgeEntryModel(
                entry_id=str(uuid.uuid4()),
                category=best_entry.category,
                title=best_entry.title + " (Merged)",
                content=merged_content,
                summary=best_entry.summary,
                source_agent_id=merged_by,
                tags=merged_tags,
                metadata={
                    **merged_metadata,
                    "merged_from": entry_ids,
                    "merged_at": datetime.utcnow().isoformat()
                },
                confidence_score=max(e.confidence_score for e in entries),
                usage_count=sum(e.usage_count for e in entries),
                success_rate=sum(e.success_rate for e in entries) / len(entries),
                created_at=datetime.utcnow()
            )
            
            self.db.add(merged_entry)
            
            # Mark old entries as deleted
            for entry in entries:
                entry.deleted_at = datetime.utcnow()
                entry.deleted_by = merged_by
                entry.deletion_reason = f"Merged into {merged_entry.entry_id}"
            
            await self.db.commit()
            
            logger.info("Entries merged",
                       merged_id=merged_entry.entry_id,
                       source_count=len(entry_ids))
            
            return merged_entry.entry_id
            
        except Exception as e:
            logger.error("Failed to merge entries", error=str(e))
            raise
    
    def _merge_content(self, contents: List[str]) -> str:
        """Merge content from multiple entries"""
        # Simple merge - combine unique content
        merged = "\n\n---\n\n".join(contents)
        return merged
    
    def _merge_metadata(self, metadatas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge metadata from multiple entries"""
        merged = {}
        for meta in metadatas:
            merged.update(meta)
        return merged


# ============================================================================
# Export Utilities
# ============================================================================

class KnowledgeExporter:
    """Export knowledge in various formats"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def export_to_json(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Export knowledge to JSON format"""
        from ..models import KnowledgeEntryModel
        
        try:
            stmt = select(KnowledgeEntryModel).where(
                KnowledgeEntryModel.deleted_at.is_(None)
            )
            
            if category:
                stmt = stmt.where(KnowledgeEntryModel.category == category)
            
            result = await self.db.execute(stmt)
            entries = result.scalars().all()
            
            export_data = {
                "export_date": datetime.utcnow().isoformat(),
                "total_entries": len(entries),
                "category": category,
                "tags": tags,
                "entries": [
                    {
                        "entry_id": e.entry_id,
                        "category": e.category,
                        "title": e.title,
                        "content": e.content,
                        "summary": e.summary,
                        "tags": e.tags,
                        "metadata": e.metadata,
                        "confidence_score": e.confidence_score,
                        "created_at": e.created_at.isoformat()
                    }
                    for e in entries
                ]
            }
            
            return export_data
            
        except Exception as e:
            logger.error("Export failed", error=str(e))
            return {"error": str(e)}
    
    async def export_to_markdown(
        self,
        category: Optional[str] = None
    ) -> str:
        """Export knowledge to Markdown format"""
        json_data = await self.export_to_json(category=category)
        
        if "error" in json_data:
            return f"# Export Error\n\n{json_data['error']}"
        
        markdown = f"# Knowledge Base Export\n\n"
        markdown += f"**Export Date:** {json_data['export_date']}\n\n"
        markdown += f"**Total Entries:** {json_data['total_entries']}\n\n"
        
        if category:
            markdown += f"**Category:** {category}\n\n"
        
        markdown += "---\n\n"
        
        for entry in json_data['entries']:
            markdown += f"## {entry['title']}\n\n"
            markdown += f"**Category:** {entry['category']}\n\n"
            markdown += f"**Tags:** {', '.join(entry['tags'])}\n\n"
            markdown += f"{entry['content']}\n\n"
            markdown += "---\n\n"
        
        return markdown


# Export all helper classes
__all__ = [
    'AgentCommunicator',
    'ModelTrainer',
    'LearningAnalytics',
    'AgentLifecycleManager',
    'KnowledgeValidator',
    'PerformanceTracker',
    'KnowledgeQualityScorer',
    'PatternAnalyzer',
    'KnowledgeMerger',
    'KnowledgeExporter',
    'calculate_similarity',
    'extract_keywords',
    'normalize_text',
    'calculate_confidence_score',
    'format_insight',
    'calculate_learning_velocity',
    'identify_learning_trends'
]
