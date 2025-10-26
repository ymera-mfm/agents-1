"""
Insight Generator
Generates actionable insights from accumulated knowledge and patterns
"""

import uuid
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from models import (
        KnowledgeEntryModel, PatternModel, InteractionLogModel,
        InsightType, KnowledgeCategory, PatternStatus
    )
except ImportError:
    # Define stub models if not available
    KnowledgeEntryModel = None
    PatternModel = None
    InteractionLogModel = None
    InsightType = None
    KnowledgeCategory = None
    PatternStatus = None


logger = structlog.get_logger(__name__)


class InsightGenerator:
    """
    Generates insights from patterns, trends, and knowledge analysis
    """
    
    def __init__(self, db_session: AsyncSession, knowledge_store):
        self.db = db_session
        self.knowledge_store = knowledge_store
    
    async def generate(
        self,
        context: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate insights from accumulated data
        
        Args:
            context: Optional context for insight generation
            agent_id: Optional specific agent
            
        Returns:
            List of generated insights
        """
        try:
            insights = []
            
            # Generate different types of insights
            insights.extend(await self._generate_trend_insights())
            insights.extend(await self._generate_anomaly_insights())
            insights.extend(await self._generate_opportunity_insights())
            insights.extend(await self._generate_risk_insights())
            insights.extend(await self._generate_optimization_insights())
            
            # Filter by context if provided
            if context:
                insights = [i for i in insights if self._matches_context(i, context)]
            
            # Filter by agent if provided
            if agent_id:
                insights = [i for i in insights if self._relevant_to_agent(i, agent_id)]
            
            # Sort by importance
            insights.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
            
            logger.info(f"Generated {len(insights)} insights", context=context)
            
            return insights[:20]  # Top 20 insights
            
        except Exception as e:
            logger.error("Insight generation failed", error=str(e))
            return []
    
    async def _generate_trend_insights(self) -> List[Dict[str, Any]]:
        """Generate insights about trends"""
        insights = []
        
        try:
            # Analyze knowledge category trends
            time_window = timedelta(days=30)
            cutoff = datetime.utcnow() - time_window
            
            stmt = select(
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
            )
            
            result = await self.db.execute(stmt)
            category_trends = result.fetchall()
            
            if category_trends:
                top_category, top_count = category_trends[0]
                
                insights.append({
                    "insight_id": str(uuid.uuid4()),
                    "type": InsightType.TREND,
                    "title": f"Growing Interest in {top_category}",
                    "description": f"There has been a significant increase in {top_category} knowledge entries over the past 30 days ({top_count} entries).",
                    "recommendations": [
                        f"Focus on expanding {top_category} knowledge base",
                        "Consider creating specialized agents for this area",
                        "Develop training materials for this category"
                    ],
                    "confidence": 0.8,
                    "importance_score": 0.75,
                    "category": top_category,
                    "data": {
                        "category": top_category,
                        "count": top_count,
                        "time_period": "30_days"
                    }
                })
            
            # Analyze pattern trends
            pattern_stmt = select(
                PatternModel.pattern_type,
                func.count(PatternModel.pattern_id).label('count')
            ).where(
                PatternModel.detected_at >= cutoff
            ).group_by(
                PatternModel.pattern_type
            ).order_by(
                desc('count')
            )
            
            pattern_result = await self.db.execute(pattern_stmt)
            pattern_trends = pattern_result.fetchall()
            
            if pattern_trends and len(pattern_trends) > 1:
                insights.append({
                    "insight_id": str(uuid.uuid4()),
                    "type": InsightType.TREND,
                    "title": "Pattern Detection Trends",
                    "description": f"Most common patterns: {', '.join([pt for pt, _ in pattern_trends[:3]])}",
                    "recommendations": [
                        "Document frequently occurring patterns",
                        "Create pattern recognition templates",
                        "Share pattern insights with agents"
                    ],
                    "confidence": 0.75,
                    "importance_score": 0.7,
                    "data": {
                        "patterns": [
                            {"type": pt, "count": count}
                            for pt, count in pattern_trends
                        ]
                    }
                })
            
        except Exception as e:
            logger.error("Failed to generate trend insights", error=str(e))
        
        return insights
    
    async def _generate_anomaly_insights(self) -> List[Dict[str, Any]]:
        """Generate insights about anomalies"""
        insights = []
        
        try:
            # Detect knowledge gaps
            stmt = select(
                KnowledgeEntryModel.category,
                func.count(KnowledgeEntryModel.entry_id).label('count')
            ).where(
                KnowledgeEntryModel.deleted_at.is_(None)
            ).group_by(
                KnowledgeEntryModel.category
            )
            
            result = await self.db.execute(stmt)
            category_counts = dict(result.fetchall())
            
            # Find underrepresented categories
            if category_counts:
                avg_count = sum(category_counts.values()) / len(category_counts)
                
                for category, count in category_counts.items():
                    if count < avg_count * 0.3:  # Less than 30% of average
                        insights.append({
                            "insight_id": str(uuid.uuid4()),
                            "type": InsightType.ANOMALY,
                            "title": f"Knowledge Gap in {category}",
                            "description": f"The {category} category is significantly underrepresented with only {count} entries compared to average of {int(avg_count)}.",
                            "recommendations": [
                                f"Prioritize {category} knowledge acquisition",
                                f"Assign agents to research {category} topics",
                                "Review if this category is still relevant"
                            ],
                            "confidence": 0.85,
                            "importance_score": 0.8,
                            "category": category,
                            "data": {
                                "category": category,
                                "current_count": count,
                                "average_count": int(avg_count),
                                "gap_percentage": ((avg_count - count) / avg_count) * 100
                            }
                        })
            
            # Detect unusual interaction patterns
            time_window = timedelta(days=7)
            cutoff = datetime.utcnow() - time_window
            
            interaction_stmt = select(
                InteractionLogModel.interaction_type,
                func.count(InteractionLogModel.log_id).label('count'),
                func.avg(InteractionLogModel.duration_ms).label('avg_duration')
            ).where(
                InteractionLogModel.timestamp >= cutoff
            ).group_by(
                InteractionLogModel.interaction_type
            )
            
            interaction_result = await self.db.execute(interaction_stmt)
            interactions = interaction_result.fetchall()
            
            for itype, count, avg_duration in interactions:
                if avg_duration and avg_duration > 5000:  # > 5 seconds
                    insights.append({
                        "insight_id": str(uuid.uuid4()),
                        "type": InsightType.ANOMALY,
                        "title": f"Slow {itype} Interactions",
                        "description": f"{itype} interactions are taking longer than expected (avg: {int(avg_duration)}ms).",
                        "recommendations": [
                            f"Investigate {itype} performance bottlenecks",
                            "Consider caching frequently accessed data",
                            "Optimize {itype} implementation"
                        ],
                        "confidence": 0.8,
                        "importance_score": 0.75,
                        "data": {
                            "interaction_type": itype,
                            "average_duration_ms": int(avg_duration),
                            "sample_size": count
                        }
                    })
            
        except Exception as e:
            logger.error("Failed to generate anomaly insights", error=str(e))
        
        return insights
    
    async def _generate_opportunity_insights(self) -> List[Dict[str, Any]]:
        """Generate insights about opportunities"""
        insights = []
        
        try:
            # Find highly successful patterns
            pattern_stmt = select(PatternModel).where(
                and_(
                    PatternModel.confidence >= 0.8,
                    PatternModel.status == PatternStatus.VALIDATED
                )
            ).order_by(
                desc(PatternModel.confidence)
            ).limit(5)
            
            result = await self.db.execute(pattern_stmt)
            successful_patterns = result.scalars().all()
            
            if successful_patterns:
                insights.append({
                    "insight_id": str(uuid.uuid4()),
                    "type": InsightType.OPPORTUNITY,
                    "title": "High-Value Patterns Identified",
                    "description": f"Found {len(successful_patterns)} validated patterns with high confidence that can be leveraged.",
                    "recommendations": [
                        "Document these patterns as best practices",
                        "Train agents to recognize and apply these patterns",
                        "Create automated pattern detection tools",
                        "Share these patterns across the platform"
                    ],
                    "confidence": 0.85,
                    "importance_score": 0.9,
                    "data": {
                        "pattern_count": len(successful_patterns),
                        "patterns": [
                            {
                                "type": p.pattern_type,
                                "confidence": p.confidence
                            }
                            for p in successful_patterns
                        ]
                    }
                })
            
            # Find knowledge with high success rates
            knowledge_stmt = select(KnowledgeEntryModel).where(
                and_(
                    KnowledgeEntryModel.success_rate >= 0.9,
                    KnowledgeEntryModel.usage_count >= 5,
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            ).order_by(
                desc(KnowledgeEntryModel.success_rate),
                desc(KnowledgeEntryModel.usage_count)
            ).limit(10)
            
            knowledge_result = await self.db.execute(knowledge_stmt)
            high_value_knowledge = knowledge_result.scalars().all()
            
            if high_value_knowledge:
                insights.append({
                    "insight_id": str(uuid.uuid4()),
                    "type": InsightType.OPPORTUNITY,
                    "title": "High-Value Knowledge Identified",
                    "description": f"Identified {len(high_value_knowledge)} knowledge entries with exceptional success rates (>90%).",
                    "recommendations": [
                        "Promote these knowledge entries to all agents",
                        "Create training materials based on this knowledge",
                        "Expand on these successful approaches",
                        "Feature these in agent onboarding"
                    ],
                    "confidence": 0.9,
                    "importance_score": 0.85,
                    "data": {
                        "knowledge_count": len(high_value_knowledge),
                        "categories": list(set(k.category for k in high_value_knowledge)),
                        "average_success_rate": sum(k.success_rate for k in high_value_knowledge) / len(high_value_knowledge)
                    }
                })
            
            # Identify collaboration opportunities
            collab_insight = await self._identify_collaboration_opportunities()
            if collab_insight:
                insights.append(collab_insight)
            
        except Exception as e:
            logger.error("Failed to generate opportunity insights", error=str(e))
        
        return insights
    
    async def _generate_risk_insights(self) -> List[Dict[str, Any]]:
        """Generate insights about risks"""
        insights = []
        
        try:
            # Find low success rate knowledge
            risky_knowledge_stmt = select(KnowledgeEntryModel).where(
                and_(
                    KnowledgeEntryModel.success_rate < 0.5,
                    KnowledgeEntryModel.usage_count >= 3,
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            ).order_by(
                KnowledgeEntryModel.success_rate
            ).limit(10)
            
            risky_result = await self.db.execute(risky_knowledge_stmt)
            risky_knowledge = risky_result.scalars().all()
            
            if risky_knowledge:
                insights.append({
                    "insight_id": str(uuid.uuid4()),
                    "type": InsightType.RISK,
                    "title": "Low Success Rate Knowledge Detected",
                    "description": f"Found {len(risky_knowledge)} knowledge entries with success rates below 50%.",
                    "recommendations": [
                        "Review and update these knowledge entries",
                        "Consider deprecating ineffective approaches",
                        "Investigate why these approaches are failing",
                        "Add warnings or caveats to this knowledge"
                    ],
                    "confidence": 0.8,
                    "importance_score": 0.85,
                    "data": {
                        "risky_count": len(risky_knowledge),
                        "average_success_rate": sum(k.success_rate for k in risky_knowledge) / len(risky_knowledge),
                        "categories": list(set(k.category for k in risky_knowledge))
                    }
                })
            
            # Detect outdated knowledge
            outdated_cutoff = datetime.utcnow() - timedelta(days=180)
            outdated_stmt = select(func.count(KnowledgeEntryModel.entry_id)).where(
                and_(
                    KnowledgeEntryModel.created_at < outdated_cutoff,
                    KnowledgeEntryModel.updated_at.is_(None),
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            )
            
            outdated_result = await self.db.execute(outdated_stmt)
            outdated_count = outdated_result.scalar() or 0
            
            if outdated_count > 10:
                insights.append({
                    "insight_id": str(uuid.uuid4()),
                    "type": InsightType.RISK,
                    "title": "Outdated Knowledge Accumulation",
                    "description": f"{outdated_count} knowledge entries haven't been updated in over 6 months.",
                    "recommendations": [
                        "Review and update outdated knowledge",
                        "Verify current relevance and accuracy",
                        "Archive obsolete entries",
                        "Establish knowledge refresh schedule"
                    ],
                    "confidence": 0.75,
                    "importance_score": 0.7,
                    "data": {
                        "outdated_count": outdated_count,
                        "age_threshold_days": 180
                    }
                })
            
        except Exception as e:
            logger.error("Failed to generate risk insights", error=str(e))
        
        return insights
    
    async def _generate_optimization_insights(self) -> List[Dict[str, Any]]:
        """Generate insights about optimization opportunities"""
        insights = []
        
        try:
            # Find frequently accessed but slow knowledge
            stmt = select(KnowledgeEntryModel).where(
                and_(
                    KnowledgeEntryModel.usage_count >= 10,
                    KnowledgeEntryModel.deleted_at.is_(None)
                )
            ).order_by(
                desc(KnowledgeEntryModel.usage_count)
            ).limit(20)
            
            result = await self.db.execute(stmt)
            popular_knowledge = result.scalars().all()
            
            if popular_knowledge:
                # Check if these should be cached more aggressively
                very_popular = [k for k in popular_knowledge if k.usage_count > 50]
                
                if very_popular:
                    insights.append({
                        "insight_id": str(uuid.uuid4()),
                        "type": InsightType.OPTIMIZATION,
                        "title": "High-Traffic Knowledge Optimization",
                        "description": f"{len(very_popular)} knowledge entries are accessed very frequently (>50 times).",
                        "recommendations": [
                            "Implement aggressive caching for these entries",
                            "Create quick-access shortcuts",
                            "Pre-load these entries for active agents",
                            "Consider creating summaries for faster access"
                        ],
                        "confidence": 0.85,
                        "importance_score": 0.75,
                        "data": {
                            "high_traffic_count": len(very_popular),
                            "total_accesses": sum(k.usage_count for k in very_popular),
                            "top_entries": [
                                {
                                    "entry_id": k.entry_id,
                                    "title": k.title,
                                    "usage_count": k.usage_count
                                }
                                for k in very_popular[:5]
                            ]
                        }
                    })
            
            # Identify duplicate or similar knowledge
            duplicate_insight = await self._identify_duplicate_knowledge()
            if duplicate_insight:
                insights.append(duplicate_insight)
            
            # Suggest knowledge graph optimization
            graph_insight = await self._suggest_graph_optimization()
            if graph_insight:
                insights.append(graph_insight)
            
        except Exception as e:
            logger.error("Failed to generate optimization insights", error=str(e))
        
        return insights
    
    async def _identify_collaboration_opportunities(self) -> Optional[Dict[str, Any]]:
        """Identify opportunities for agent collaboration"""
        try:
            # Analyze interaction patterns
            time_window = timedelta(days=14)
            cutoff = datetime.utcnow() - time_window
            
            stmt = select(
                InteractionLogModel.source_agent_id,
                InteractionLogModel.target_agent_id,
                func.count(InteractionLogModel.log_id).label('count')
            ).where(
                and_(
                    InteractionLogModel.timestamp >= cutoff,
                    InteractionLogModel.target_agent_id.isnot(None)
                )
            ).group_by(
                InteractionLogModel.source_agent_id,
                InteractionLogModel.target_agent_id
            ).order_by(
                desc('count')
            ).limit(10)
            
            result = await self.db.execute(stmt)
            collaborations = result.fetchall()
            
            if collaborations:
                return {
                    "insight_id": str(uuid.uuid4()),
                    "type": InsightType.OPPORTUNITY,
                    "title": "Agent Collaboration Patterns",
                    "description": f"Identified {len(collaborations)} strong collaboration patterns between agents.",
                    "recommendations": [
                        "Create formal collaboration workflows",
                        "Share knowledge between collaborating agents",
                        "Optimize communication protocols",
                        "Document successful collaboration patterns"
                    ],
                    "confidence": 0.8,
                    "importance_score": 0.75,
                    "data": {
                        "collaboration_count": len(collaborations),
                        "top_collaborations": [
                            {
                                "source": source,
                                "target": target,
                                "interaction_count": count
                            }
                            for source, target, count in collaborations[:5]
                        ]
                    }
                }
            
        except Exception as e:
            logger.error("Failed to identify collaboration opportunities", error=str(e))
        
        return None
    
    async def _identify_duplicate_knowledge(self) -> Optional[Dict[str, Any]]:
        """Identify potential duplicate knowledge entries"""
        try:
            # This is simplified - in production, use similarity metrics
            stmt = select(
                KnowledgeEntryModel.category,
                func.count(KnowledgeEntryModel.entry_id).label('count')
            ).where(
                KnowledgeEntryModel.deleted_at.is_(None)
            ).group_by(
                KnowledgeEntryModel.category
            ).having(
                func.count(KnowledgeEntryModel.entry_id) > 20
            )
            
            result = await self.db.execute(stmt)
            crowded_categories = result.fetchall()
            
            if crowded_categories:
                return {
                    "insight_id": str(uuid.uuid4()),
                    "type": InsightType.OPTIMIZATION,
                    "title": "Knowledge Consolidation Opportunity",
                    "description": f"{len(crowded_categories)} categories have many entries that could be consolidated.",
                    "recommendations": [
                        "Review for duplicate or overlapping knowledge",
                        "Merge similar entries",
                        "Create summary entries for related knowledge",
                        "Improve knowledge organization"
                    ],
                    "confidence": 0.7,
                    "importance_score": 0.65,
                    "data": {
                        "categories": [
                            {"category": cat, "count": count}
                            for cat, count in crowded_categories
                        ]
                    }
                }
            
        except Exception as e:
            logger.error("Failed to identify duplicates", error=str(e))
        
        return None
    
    async def _suggest_graph_optimization(self) -> Optional[Dict[str, Any]]:
        """Suggest knowledge graph optimizations"""
        try:
            # Check for orphaned nodes (no connections)
            # This would require querying the graph
            
            return {
                "insight_id": str(uuid.uuid4()),
                "type": InsightType.OPTIMIZATION,
                "title": "Knowledge Graph Optimization",
                "description": "Regular optimization of the knowledge graph can improve query performance.",
                "recommendations": [
                    "Remove weak connections (strength < 0.2)",
                    "Strengthen frequently used paths",
                    "Identify and connect isolated knowledge clusters",
                    "Update relationship strengths based on usage"
                ],
                "confidence": 0.75,
                "importance_score": 0.7,
                "data": {}
            }
            
        except Exception as e:
            logger.error("Failed to suggest graph optimization", error=str(e))
        
        return None
    
    # Utility Methods
    
    def _matches_context(self, insight: Dict[str, Any], context: str) -> bool:
        """Check if insight matches the given context"""
        context_lower = context.lower()
        
        # Check title and description
        if context_lower in insight.get('title', '').lower():
            return True
        if context_lower in insight.get('description', '').lower():
            return True
        
        # Check data fields
        if 'category' in insight.get('data', {}):
            if context_lower in str(insight['data']['category']).lower():
                return True
        
        return False
    
    def _relevant_to_agent(self, insight: Dict[str, Any], agent_id: str) -> bool:
        """Check if insight is relevant to specific agent"""
        # Check if agent is mentioned in the data
        data = insight.get('data', {})
        
        if 'agent_id' in data and data['agent_id'] == agent_id:
            return True
        
        if 'agents' in data and agent_id in data['agents']:
            return True
        
        # By default, all insights are relevant to all agents
        return True
