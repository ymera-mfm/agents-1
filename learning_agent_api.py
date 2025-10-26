"""
Learning Agent API Routes
FastAPI endpoints for learning agent operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/learning-agent", tags=["Learning Agent"])


# Request/Response Models

class KnowledgeStoreRequest(BaseModel):
    content: str
    category: str
    source_agent_id: str
    metadata: Optional[Dict[str, Any]] = None
    tags: List[str] = []
    title: Optional[str] = None
    summary: Optional[str] = None


class KnowledgeSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 10
    min_confidence: float = 0.3


class LearningOutcomeRequest(BaseModel):
    task_id: str
    agent_id: str
    task_type: str
    outcome: str
    success: bool
    details: Dict[str, Any]


class UserFeedbackRequest(BaseModel):
    agent_id: str
    task_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback: Dict[str, Any]


class InteractionLogRequest(BaseModel):
    source_agent_id: str
    target_agent_id: Optional[str] = None
    interaction_type: str
    interaction_data: Dict[str, Any]
    outcome: Optional[str] = None


class KnowledgeSubscriptionRequest(BaseModel):
    agent_id: str
    categories: List[str]
    tags: List[str] = []
    filters: Optional[Dict[str, Any]] = None


class KnowledgeShareRequest(BaseModel):
    source_agent_id: str
    target_agent_ids: List[str]
    knowledge_ids: List[str]


class RecommendationRequest(BaseModel):
    agent_id: str
    task_type: str
    context: Dict[str, Any]


# Placeholder dependency - will be injected by main app
async def get_learning_agent():
    """Dependency to get learning agent instance"""
    raise HTTPException(status_code=500, detail="Learning Agent not initialized")


# Knowledge Management Endpoints

@router.post("/knowledge/store", status_code=status.HTTP_201_CREATED)
async def store_knowledge(
    request: KnowledgeStoreRequest,
    learning_agent=Depends(get_learning_agent)
):
    """Store new knowledge in the knowledge base"""
    try:
        result = await learning_agent.store_knowledge(
            content=request.content,
            category=request.category,
            source_agent_id=request.source_agent_id,
            metadata=request.metadata,
            tags=request.tags
        )
        return result
    except Exception as e:
        logger.error("Failed to store knowledge", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge/search")
async def search_knowledge(
    request: KnowledgeSearchRequest,
    learning_agent=Depends(get_learning_agent)
):
    """Search knowledge base"""
    try:
        results = await learning_agent.retrieve_knowledge(
            query=request.query,
            category=request.category,
            tags=request.tags,
            limit=request.limit
        )
        return {
            "results": results,
            "count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Knowledge search failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge/{entry_id}")
async def get_knowledge(
    entry_id: str,
    learning_agent=Depends(get_learning_agent)
):
    """Get specific knowledge entry"""
    try:
        knowledge = await learning_agent.knowledge_store.get(entry_id)
        if not knowledge:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        return knowledge
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get knowledge", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/knowledge/{entry_id}")
async def update_knowledge(
    entry_id: str,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    learning_agent=Depends(get_learning_agent)
):
    """Update knowledge entry"""
    try:
        result = await learning_agent.update_knowledge(
            entry_id=entry_id,
            content=content,
            metadata=metadata,
            tags=tags
        )
        return result
    except Exception as e:
        logger.error("Failed to update knowledge", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/knowledge/{entry_id}")
async def delete_knowledge(
    entry_id: str,
    reason: str,
    deleted_by: str,
    learning_agent=Depends(get_learning_agent)
):
    """Delete knowledge entry"""
    try:
        result = await learning_agent.delete_knowledge(
            entry_id=entry_id,
            reason=reason,
            deleted_by=deleted_by
        )
        return result
    except Exception as e:
        logger.error("Failed to delete knowledge", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge/category/{category}")
async def get_knowledge_by_category(
    category: str,
    limit: int = Query(50, le=100),
    learning_agent=Depends(get_learning_agent)
):
    """Get knowledge entries by category"""
    try:
        entries = await learning_agent.knowledge_store.get_by_category(
            category=category,
            limit=limit
        )
        return {
            "category": category,
            "entries": entries,
            "count": len(entries)
        }
    except Exception as e:
        logger.error("Failed to get category knowledge", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# Learning Endpoints

@router.post("/learning/outcome")
async def learn_from_outcome(
    request: LearningOutcomeRequest,
    learning_agent=Depends(get_learning_agent)
):
    """Learn from task outcome"""
    try:
        result = await learning_agent.learn_from_outcome(
            task_id=request.task_id,
            agent_id=request.agent_id,
            task_type=request.task_type,
            outcome=request.outcome,
            success=request.success,
            details=request.details
        )
        return result
    except Exception as e:
        logger.error("Failed to learn from outcome", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/learning/feedback")
async def learn_from_feedback(
    request: UserFeedbackRequest,
    learning_agent=Depends(get_learning_agent)
):
    """Learn from user feedback"""
    try:
        result = await learning_agent.learn_from_user_feedback(
            agent_id=request.agent_id,
            task_id=request.task_id,
            feedback=request.feedback,
            rating=request.rating
        )
        return result
    except Exception as e:
        logger.error("Failed to learn from feedback", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/learning/interaction")
async def log_interaction(
    request: InteractionLogRequest,
    learning_agent=Depends(get_learning_agent)
):
    """Log agent interaction for learning"""
    try:
        result = await learning_agent.log_interaction(
            source_agent_id=request.source_agent_id,
            target_agent_id=request.target_agent_id,
            interaction_type=request.interaction_type,
            interaction_data=request.interaction_data,
            outcome=request.outcome
        )
        return result
    except Exception as e:
        logger.error("Failed to log interaction", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# Pattern & Insight Endpoints

@router.post("/patterns/detect")
async def detect_patterns(
    data_source: str,
    time_window_days: int = 7,
    learning_agent=Depends(get_learning_agent)
):
    """Detect patterns in data"""
    try:
        patterns = await learning_agent.detect_patterns(
            data_source=data_source,
            time_window=timedelta(days=time_window_days)
        )
        return {
            "patterns": patterns,
            "count": len(patterns),
            "data_source": data_source,
            "time_window_days": time_window_days
        }
    except Exception as e:
        logger.error("Pattern detection failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/insights/generate")
async def generate_insights(
    context: Optional[str] = None,
    agent_id: Optional[str] = None,
    learning_agent=Depends(get_learning_agent)
):
    """Generate insights from accumulated knowledge"""
    try:
        insights = await learning_agent.generate_insights(
            context=context,
            agent_id=agent_id
        )
        return {
            "insights": insights,
            "count": len(insights),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Insight generation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# Knowledge Flow Endpoints

@router.post("/knowledge-flow/subscribe")
async def subscribe_to_knowledge(
    request: KnowledgeSubscriptionRequest,
    learning_agent=Depends(get_learning_agent)
):
    """Subscribe to knowledge updates"""
    try:
        result = await learning_agent.subscribe_to_knowledge(
            agent_id=request.agent_id,
            categories=request.categories,
            tags=request.tags
        )
        return result
    except Exception as e:
        logger.error("Failed to create subscription", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge-flow/share")
async def share_knowledge(
    request: KnowledgeShareRequest,
    learning_agent=Depends(get_learning_agent)
):
    """Share knowledge with specific agents"""
    try:
        result = await learning_agent.share_knowledge(
            source_agent_id=request.source_agent_id,
            target_agent_ids=request.target_agent_ids,
            knowledge_ids=request.knowledge_ids
        )
        return result
    except Exception as e:
        logger.error("Failed to share knowledge", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge-flow/request")
async def request_knowledge(
    agent_id: str,
    query: str,
    urgency: str = "normal",
    learning_agent=Depends(get_learning_agent)
):
    """Request specific knowledge"""
    try:
        result = await learning_agent.request_knowledge(
            agent_id=agent_id,
            query=query,
            urgency=urgency
        )
        return result
    except Exception as e:
        logger.error("Failed to request knowledge", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge-flow/subscriptions/{agent_id}")
async def get_agent_subscriptions(
    agent_id: str,
    learning_agent=Depends(get_learning_agent)
):
    """Get agent's knowledge subscriptions"""
    try:
        subscriptions = await learning_agent.flow_manager.get_agent_subscriptions(
            agent_id
        )
        return {
            "agent_id": agent_id,
            "subscriptions": subscriptions,
            "count": len(subscriptions)
        }
    except Exception as e:
        logger.error("Failed to get subscriptions", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# Recommendation Endpoints

@router.post("/recommendations/get")
async def get_recommendations(
    request: RecommendationRequest,
    learning_agent=Depends(get_learning_agent)
):
    """Get recommendations for agent"""
    try:
        recommendations = await learning_agent.get_recommendations(
            agent_id=request.agent_id,
            task_type=request.task_type,
            context=request.context
        )
        return {
            "agent_id": request.agent_id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get recommendations", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommendations/collaborators/{agent_id}")
async def recommend_collaborators(
    agent_id: str,
    task_type: str,
    learning_agent=Depends(get_learning_agent)
):
    """Recommend collaborators for agent"""
    try:
        collaborators = await learning_agent.recommendation_engine.recommend_collaborators(
            agent_id=agent_id,
            task_type=task_type
        )
        return {
            "agent_id": agent_id,
            "task_type": task_type,
            "recommended_collaborators": collaborators,
            "count": len(collaborators)
        }
    except Exception as e:
        logger.error("Failed to recommend collaborators", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommendations/learning-path/{agent_id}")
async def get_learning_path(
    agent_id: str,
    learning_agent=Depends(get_learning_agent)
):
    """Get recommended learning path for agent"""
    try:
        learning_path = await learning_agent.recommendation_engine.recommend_learning_path(
            agent_id
        )
        return learning_path
    except Exception as e:
        logger.error("Failed to get learning path", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# Analytics & Reporting Endpoints

@router.get("/analytics/learning-report")
async def get_learning_report(
    days: int = Query(7, ge=1, le=90),
    learning_agent=Depends(get_learning_agent)
):
    """Get learning analytics report"""
    try:
        report = await learning_agent.get_learning_report(
            time_period=timedelta(days=days)
        )
        return report
    except Exception as e:
        logger.error("Failed to get learning report", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/agent-profile/{agent_id}")
async def get_agent_learning_profile(
    agent_id: str,
    learning_agent=Depends(get_learning_agent)
):
    """Get agent's learning profile"""
    try:
        profile = await learning_agent.get_agent_learning_profile(agent_id)
        return profile
    except Exception as e:
        logger.error("Failed to get agent profile", error=str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/analytics/knowledge-statistics")
async def get_knowledge_statistics(
    learning_agent=Depends(get_learning_agent)
):
    """Get knowledge base statistics"""
    try:
        stats = await learning_agent.get_knowledge_statistics()
        return stats
    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/knowledge-graph")
async def get_knowledge_graph_stats(
    learning_agent=Depends(get_learning_agent)
):
    """Get knowledge graph statistics"""
    try:
        stats = await learning_agent.knowledge_graph.get_statistics()
        return stats
    except Exception as e:
        logger.error("Failed to get graph statistics", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/flow-metrics")
async def get_flow_metrics(
    learning_agent=Depends(get_learning_agent)
):
    """Get knowledge flow metrics"""
    try:
        metrics = await learning_agent.flow_manager.get_flow_metrics()
        return metrics
    except Exception as e:
        logger.error("Failed to get flow metrics", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# Knowledge Graph Endpoints

@router.get("/graph/related/{entry_id}")
async def get_related_knowledge(
    entry_id: str,
    max_depth: int = Query(2, ge=1, le=5),
    limit: int = Query(10, le=50),
    learning_agent=Depends(get_learning_agent)
):
    """Get related knowledge entries"""
    try:
        related = await learning_agent.knowledge_graph.get_related_nodes(
            entry_id=entry_id,
            max_depth=max_depth,
            limit=limit
        )
        return {
            "entry_id": entry_id,
            "related": related,
            "count": len(related)
        }
    except Exception as e:
        logger.error("Failed to get related knowledge", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph/path")
async def find_knowledge_path(
    source_id: str,
    target_id: str,
    max_depth: int = Query(5, ge=1, le=10),
    learning_agent=Depends(get_learning_agent)
):
    """Find path between two knowledge entries"""
    try:
        path = await learning_agent.knowledge_graph.find_path(
            source_id=source_id,
            target_id=target_id,
            max_depth=max_depth
        )
        
        if not path:
            raise HTTPException(status_code=404, detail="No path found")
        
        return {
            "source_id": source_id,
            "target_id": target_id,
            "path": path,
            "distance": len(path) - 1
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to find path", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph/clusters")
async def get_knowledge_clusters(
    min_size: int = Query(3, ge=2),
    learning_agent=Depends(get_learning_agent)
):
    """Get knowledge clusters"""
    try:
        clusters = await learning_agent.knowledge_graph.get_clusters(
            min_cluster_size=min_size
        )
        return {
            "clusters": clusters,
            "count": len(clusters)
        }
    except Exception as e:
        logger.error("Failed to get clusters", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph/central-nodes")
async def get_central_nodes(
    limit: int = Query(10, le=50),
    learning_agent=Depends(get_learning_agent)
):
    """Get most central nodes in knowledge graph"""
    try:
        nodes = await learning_agent.knowledge_graph.get_central_nodes(limit=limit)
        return {
            "central_nodes": nodes,
            "count": len(nodes)
        }
    except Exception as e:
        logger.error("Failed to get central nodes", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# System Management Endpoints

@router.post("/system/optimize")
async def optimize_system(
    learning_agent=Depends(get_learning_agent)
):
    """Optimize learning system"""
    try:
        # Optimize knowledge graph
        await learning_agent.knowledge_graph.optimize()
        
        # Rebuild indexes
        await learning_agent.knowledge_store.rebuild_index()
        
        return {
            "status": "optimized",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("System optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "learning_agent",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/system/status")
async def get_system_status(
    learning_agent=Depends(get_learning_agent)
):
    """Get learning system status"""
    try:
        # Get various metrics
        knowledge_stats = await learning_agent.get_knowledge_statistics()
        flow_metrics = await learning_agent.flow_manager.get_flow_metrics()
        
        return {
            "status": "operational",
            "knowledge_base": {
                "total_entries": knowledge_stats.get('total_entries', 0),
                "categories": len(knowledge_stats.get('by_category', {}))
            },
            "knowledge_flow": {
                "active_subscriptions": flow_metrics.get('subscriptions_active', 0),
                "knowledge_shared": flow_metrics.get('knowledge_shared', 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
