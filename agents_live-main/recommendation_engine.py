"""
Recommendation Engine
Provides intelligent recommendations based on learning and context
"""

import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from models import (
        KnowledgeItem as KnowledgeEntryModel,
        Experience as FeedbackModel
    )
    AgentLearningProfileModel = None
    InteractionLogModel = None
    KnowledgeCategory = None
except ImportError:
    KnowledgeEntryModel = None
    AgentLearningProfileModel = None
    FeedbackModel = None
    InteractionLogModel = None
    KnowledgeCategory = None


logger = structlog.get_logger(__name__)


class RecommendationEngine:
    """
    Intelligent recommendation system for agents
    """
    
    def __init__(self, db_session: AsyncSession, knowledge_store):
        self.db = db_session
        self.knowledge_store = knowledge_store
        self.recommendation_cache = {}
    
    async def get_recommendations(
        self,
        agent_id: str,
        task_type: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations for an agent
        
        Args:
            agent_id: Agent requesting recommendations
            task_type: Type of task
            context: Task context
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []
            
            # Get agent profile
            profile = await self._get_agent_profile(agent_id)
            
            # Get task-specific recommendations
            task_recs = await self._get_task_recommendations(
                agent_id, task_type, context, profile
            )
            recommendations.extend(task_recs)
            
            # Get learning-based recommendations
            learning_recs = await self._get_learning_recommendations(
                agent_id, profile
            )
            recommendations.extend(learning_recs)
            
            # Get collaborative recommendations
            collab_recs = await self._get_collaborative_recommendations(
                agent_id, task_type
            )
            recommendations.extend(collab_recs)
            
            # Rank recommendations
            ranked_recs = self._rank_recommendations(
                recommendations, agent_id, task_type, context
            )
            
            logger.info(f"Generated {len(ranked_recs)} recommendations",
                       agent_id=agent_id,
                       task_type=task_type)
            
            return ranked_recs[:10]  # Top 10
            
        except Exception as e:
            logger.error("Failed to get recommendations", error=str(e))
            return []
    
    async def recommend_knowledge(
        self,
        agent_id: str,
        query: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Recommend specific knowledge for a query"""
        try:
            # Get agent profile for personalization
            profile = await self._get_agent_profile(agent_id)
            
            # Search knowledge base
            knowledge = await self.knowledge_store.search(
                query=query,
                limit=20
            )
            
            # Personalize results based on agent profile
            if profile:
                knowledge = self._personalize_knowledge(knowledge, profile)
            
            # Consider context
            if context:
                knowledge = self._contextualize_knowledge(knowledge, context)
            
            # Add recommendation scores
            for entry in knowledge:
                entry['recommendation_score'] = self._calculate_recommendation_score(
                    entry, agent_id, query, context
                )
            
            # Sort by recommendation score
            knowledge.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            return knowledge[:15]
            
        except Exception as e:
            logger.error("Failed to recommend knowledge", error=str(e))
            return []
    
    async def recommend_collaborators(
        self,
        agent_id: str,
        task_type: str
    ) -> List[Dict[str, Any]]:
        """Recommend other agents to collaborate with"""
        try:
            # Find agents with complementary skills
            stmt = select(AgentLearningProfileModel).where(
                AgentLearningProfileModel.agent_id != agent_id
            )
            result = await self.db.execute(stmt)
            profiles = result.scalars().all()
            
            recommendations = []
            
            for profile in profiles:
                # Calculate collaboration score
                score = await self._calculate_collaboration_score(
                    agent_id, profile.agent_id, task_type
                )
                
                if score > 0.5:
                    recommendations.append({
                        "agent_id": profile.agent_id,
                        "collaboration_score": score,
                        "strengths": profile.strengths,
                        "expertise": profile.knowledge_interests,
                        "past_collaborations": await self._count_past_collaborations(
                            agent_id, profile.agent_id
                        )
                    })
            
            # Sort by score
            recommendations.sort(key=lambda x: x['collaboration_score'], reverse=True)
            
            return recommendations[:5]
            
        except Exception as e:
            logger.error("Failed to recommend collaborators", error=str(e))
            return []
    
    async def recommend_learning_path(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Recommend learning path for agent improvement"""
        try:
            profile = await self._get_agent_profile(agent_id)
            
            if not profile:
                return {"learning_path": [], "message": "No profile data available"}
            
            # Identify improvement areas
            improvement_areas = profile.improvement_areas or []
            
            # Find relevant knowledge for each area
            learning_path = []
            
            for area in improvement_areas[:5]:  # Top 5 areas
                # Search for knowledge in this area
                knowledge = await self.knowledge_store.search(
                    query=area,
                    limit=5
                )
                
                if knowledge:
                    learning_path.append({
                        "area": area,
                        "priority": "high" if area == improvement_areas[0] else "medium",
                        "recommended_knowledge": [
                            {
                                "entry_id": k['entry_id'],
                                "title": k['title'],
                                "category": k['category']
                            }
                            for k in knowledge[:3]
                        ]
                    })
            
            return {
                "agent_id": agent_id,
                "learning_path": learning_path,
                "estimated_duration": len(learning_path) * 2,  # 2 hours per area
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to recommend learning path", error=str(e))
            return {"learning_path": [], "error": str(e)}
    
    async def update_from_feedback(
        self,
        agent_id: str,
        task_id: str,
        rating: int,
        feedback: Dict[str, Any]
    ):
        """Update recommendations based on feedback"""
        try:
            # Store feedback
            feedback_entry = FeedbackModel(
                feedback_id=str(uuid.uuid4()),
                source_type="user",
                source_id=agent_id,
                target_type="task",
                target_id=task_id,
                rating=rating,
                feedback_data=feedback,
                positive_aspects=feedback.get('positives', []),
                improvement_areas=feedback.get('improvements', []),
                processed=False,
                created_at=datetime.utcnow()
            )
            
            self.db.add(feedback_entry)
            await self.db.commit()
            
            # Update agent profile
            await self._update_agent_profile_from_feedback(
                agent_id, rating, feedback
            )
            
            # Clear recommendation cache for this agent
            cache_key = f"rec:{agent_id}"
            if cache_key in self.recommendation_cache:
                del self.recommendation_cache[cache_key]
            
            logger.info("Recommendations updated from feedback",
                       agent_id=agent_id,
                       rating=rating)
            
        except Exception as e:
            logger.error("Failed to update from feedback", error=str(e))
    
    # Helper Methods
    
    async def _get_agent_profile(self, agent_id: str) -> Optional[AgentLearningProfileModel]:
        """Get agent learning profile"""
        try:
            stmt = select(AgentLearningProfileModel).where(
                AgentLearningProfileModel.agent_id == agent_id
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get agent profile", error=str(e))
            return None
    
    async def _get_task_recommendations(
        self,
        agent_id: str,
        task_type: str,
        context: Dict[str, Any],
        profile: Optional[AgentLearningProfileModel]
    ) -> List[Dict[str, Any]]:
        """Get task-specific recommendations"""
        recommendations = []
        
        try:
            # Find successful approaches for this task type
            stmt = select(KnowledgeEntryModel).where(
                and_(
                    KnowledgeEntryModel.metadata['task_type'].astext == task_type,
                    KnowledgeEntryModel.success_rate >= 0.7,
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            ).order_by(
                desc(KnowledgeEntryModel.success_rate),
                desc(KnowledgeEntryModel.usage_count)
            ).limit(5)
            
            result = await self.db.execute(stmt)
            successful_approaches = result.scalars().all()
            
            for entry in successful_approaches:
                recommendations.append({
                    "type": "task_approach",
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "category": entry.category,
                    "success_rate": entry.success_rate,
                    "usage_count": entry.usage_count,
                    "recommendation": f"Use this approach - {entry.success_rate*100:.0f}% success rate",
                    "confidence": 0.85
                })
            
        except Exception as e:
            logger.error("Failed to get task recommendations", error=str(e))
        
        return recommendations
    
    async def _get_learning_recommendations(
        self,
        agent_id: str,
        profile: Optional[AgentLearningProfileModel]
    ) -> List[Dict[str, Any]]:
        """Get learning-based recommendations"""
        recommendations = []
        
        if not profile:
            return recommendations
        
        try:
            # Recommend knowledge in areas of interest
            for category in profile.knowledge_interests[:3]:
                stmt = select(KnowledgeEntryModel).where(
                    and_(
                        KnowledgeEntryModel.category == category,
                        KnowledgeEntryModel.confidence_score >= 0.7,
                        KnowledgeEntryModel.deleted_at.is_(None)
                    )
                ).order_by(
                    desc(KnowledgeEntryModel.confidence_score)
                ).limit(2)
                
                result = await self.db.execute(stmt)
                entries = result.scalars().all()
                
                for entry in entries:
                    recommendations.append({
                        "type": "learning_interest",
                        "entry_id": entry.entry_id,
                        "title": entry.title,
                        "category": entry.category,
                        "recommendation": f"Expand your knowledge in {category}",
                        "confidence": 0.75
                    })
            
        except Exception as e:
            logger.error("Failed to get learning recommendations", error=str(e))
        
        return recommendations
    
    async def _get_collaborative_recommendations(
        self,
        agent_id: str,
        task_type: str
    ) -> List[Dict[str, Any]]:
        """Get collaboration-based recommendations"""
        recommendations = []
        
        try:
            # Find what other agents did for similar tasks
            time_window = timedelta(days=30)
            cutoff = datetime.utcnow() - time_window
            
            stmt = select(
                InteractionLogModel.source_agent_id,
                InteractionLogModel.interaction_data
            ).where(
                and_(
                    InteractionLogModel.interaction_type == task_type,
                    InteractionLogModel.success == True,
                    InteractionLogModel.timestamp >= cutoff,
                    InteractionLogModel.source_agent_id != agent_id
                )
            ).limit(10)
            
            result = await self.db.execute(stmt)
            successful_interactions = result.fetchall()
            
            if successful_interactions:
                # Extract common approaches
                approaches = defaultdict(int)
                for _, data in successful_interactions:
                    if 'approach' in data:
                        approaches[data['approach']] += 1
                
                for approach, count in approaches.items():
                    if count >= 2:  # Used by at least 2 agents
                        recommendations.append({
                            "type": "collaborative",
                            "approach": approach,
                            "used_by": count,
                            "recommendation": f"Other agents successfully used: {approach}",
                            "confidence": min(count / 5, 0.9)
                        })
            
        except Exception as e:
            logger.error("Failed to get collaborative recommendations", error=str(e))
        
        return recommendations
    
    def _rank_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        agent_id: str,
        task_type: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank recommendations by relevance"""
        for rec in recommendations:
            # Calculate overall score
            confidence = rec.get('confidence', 0.5)
            type_weight = self._get_type_weight(rec.get('type'))
            context_match = self._match_context(rec, context)
            
            rec['rank_score'] = (confidence * 0.4) + (type_weight * 0.3) + (context_match * 0.3)
        
        # Sort by rank score
        recommendations.sort(key=lambda x: x['rank_score'], reverse=True)
        
        return recommendations
    
    def _get_type_weight(self, rec_type: str) -> float:
        """Get weight for recommendation type"""
        weights = {
            "task_approach": 0.9,
            "learning_interest": 0.7,
            "collaborative": 0.8,
            "knowledge": 0.75
        }
        return weights.get(rec_type, 0.5)
    
    def _match_context(self, recommendation: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate how well recommendation matches context"""
        if not context:
            return 0.5
        
        match_score = 0.5
        
        # Check for matching tags
        if 'tags' in context and 'tags' in recommendation:
            common_tags = set(context['tags']) & set(recommendation['tags'])
            if common_tags:
                match_score += len(common_tags) * 0.1
        
        # Check for matching category
        if 'category' in context and 'category' in recommendation:
            if context['category'] == recommendation['category']:
                match_score += 0.2
        
        return min(match_score, 1.0)
    
    def _personalize_knowledge(
        self,
        knowledge: List[Dict[str, Any]],
        profile: AgentLearningProfileModel
    ) -> List[Dict[str, Any]]:
        """Personalize knowledge based on agent profile"""
        for entry in knowledge:
            # Boost entries in areas of interest
            if entry.get('category') in profile.knowledge_interests:
                entry['relevance_score'] = entry.get('relevance_score', 0.5) * 1.2
            
            # Reduce entries in known strengths
            if entry.get('category') in profile.strengths:
                entry['relevance_score'] = entry.get('relevance_score', 0.5) * 0.8
        
        return knowledge
    
    def _contextualize_knowledge(
        self,
        knowledge: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Adjust knowledge based on context"""
        urgency = context.get('urgency', 'normal')
        
        for entry in knowledge:
            # Boost high-confidence entries for urgent requests
            if urgency == 'high' and entry.get('confidence_score', 0) > 0.8:
                entry['relevance_score'] = entry.get('relevance_score', 0.5) * 1.3
        
        return knowledge
    
    def _calculate_recommendation_score(
        self,
        entry: Dict[str, Any],
        agent_id: str,
        query: str,
        context: Dict[str, Any]
    ) -> float:
        """Calculate recommendation score for knowledge entry"""
        score = 0.0
        
        # Base score from relevance
        score += entry.get('relevance_score', 0.5) * 0.4
        
        # Confidence score
        score += entry.get('confidence_score', 0.5) * 0.3
        
        # Success rate
        score += entry.get('success_rate', 0.5) * 0.2
        
        # Popularity (usage count)
        usage_score = min(entry.get('usage_count', 0) / 50, 0.1)
        score += usage_score
        
        return min(score, 1.0)
    
    async def _calculate_collaboration_score(
        self,
        agent_id: str,
        potential_collaborator: str,
        task_type: str
    ) -> float:
        """Calculate collaboration score between agents"""
        score = 0.5  # Base score
        
        try:
            # Check past successful collaborations
            past_collabs = await self._count_past_collaborations(
                agent_id, potential_collaborator
            )
            
            if past_collabs > 0:
                score += min(past_collabs * 0.1, 0.3)
            
            # Check complementary skills
            # (would need access to agent capabilities)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error("Failed to calculate collaboration score", error=str(e))
            return 0.5
    
    async def _count_past_collaborations(
        self,
        agent1_id: str,
        agent2_id: str
    ) -> int:
        """Count past collaborations between two agents"""
        try:
            stmt = select(func.count(InteractionLogModel.log_id)).where(
                or_(
                    and_(
                        InteractionLogModel.source_agent_id == agent1_id,
                        InteractionLogModel.target_agent_id == agent2_id
                    ),
                    and_(
                        InteractionLogModel.source_agent_id == agent2_id,
                        InteractionLogModel.target_agent_id == agent1_id
                    )
                )
            )
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error("Failed to count collaborations", error=str(e))
            return 0
    
    async def _update_agent_profile_from_feedback(
        self,
        agent_id: str,
        rating: int,
        feedback: Dict[str, Any]
    ):
        """Update agent profile based on feedback"""
        try:
            profile = await self._get_agent_profile(agent_id)
            
            if not profile:
                return
            
            # Update improvement areas
            if 'improvements' in feedback:
                current_areas = set(profile.improvement_areas or [])
                new_areas = set(feedback['improvements'])
                profile.improvement_areas = list(current_areas | new_areas)
            
            # Update strengths if high rating
            if rating >= 4 and 'positives' in feedback:
                current_strengths = set(profile.strengths or [])
                new_strengths = set(feedback['positives'])
                profile.strengths = list(current_strengths | new_strengths)
            
            await self.db.commit()
            
        except Exception as e:
            logger.error("Failed to update profile from feedback", error=str(e))
