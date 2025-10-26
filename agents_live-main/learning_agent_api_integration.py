"""
YMERA Learning Agent - Manager Agent Integration
Complete API for interaction between Manager Agent and Learning Agent
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json

from learning_agent_core import (
    YMERALearningAgent,
    LearningEvent,
    KnowledgeType,
    LearningSource,
    AgentRole
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CodeAnalysisRequest(BaseModel):
    """Request for code analysis and learning"""
    agent_id: str
    code: str
    language: str = "python"
    context: Dict[str, Any] = {}
    file_path: Optional[str] = None
    operation: str  # "create", "modify", "debug", "optimize"


class TaskOutcomeRequest(BaseModel):
    """Report task outcome for learning"""
    agent_id: str
    task_id: str
    task_type: str
    outcome: str  # "success", "failure", "partial"
    duration_seconds: float
    code_produced: Optional[str] = None
    errors_encountered: List[str] = []
    solutions_applied: List[str] = []
    context: Dict[str, Any] = {}


class UserFeedbackRequest(BaseModel):
    """User feedback for learning"""
    session_id: str
    rating: int = Field(ge=1, le=5)
    feedback_text: str
    aspect: str  # "code_quality", "speed", "accuracy", "communication"
    agent_involved: Optional[str] = None
    context: Dict[str, Any] = {}


class KnowledgeQueryRequest(BaseModel):
    """Query knowledge base"""
    agent_id: str
    query: str
    knowledge_types: Optional[List[str]] = None
    min_quality: Optional[int] = None
    limit: int = Field(default=10, ge=1, le=50)


class CollaborationRequest(BaseModel):
    """Request collaboration setup"""
    initiating_agent: str
    target_agent: str
    topic: Optional[str] = None
    objective: str


class KnowledgeApplicationFeedback(BaseModel):
    """Feedback on knowledge application"""
    knowledge_id: str
    agent_id: str
    success: bool
    feedback: Optional[str] = None
    context: Dict[str, Any] = {}


class AgentRegistrationRequest(BaseModel):
    """Register new agent for learning"""
    agent_id: str
    role: str
    specializations: List[str] = []
    learning_preferences: Dict[str, Any] = {}


# ============================================================================
# MANAGER AGENT INTERFACE
# ============================================================================

class ManagerAgentInterface:
    """
    Interface for Manager Agent to interact with Learning Agent
    
    Manager Agent responsibilities:
    1. Report all agent activities and outcomes
    2. Query knowledge for decision making
    3. Request collaboration recommendations
    4. Submit user feedback
    5. Request learning reports
    """
    
    def __init__(self, learning_agent: YMERALearningAgent):
        self.learning_agent = learning_agent
    
    async def report_file_received(
        self,
        manager_agent_id: str,
        file_info: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Report when Manager receives files from user
        Learning Agent extracts patterns and requirements
        """
        event = LearningEvent(
            event_id=str(uuid.uuid4()),
            event_type="file_received",
            source=LearningSource.USER_FEEDBACK,
            source_agent_id=manager_agent_id,
            data={
                'file_type': file_info.get('type'),
                'file_size': file_info.get('size'),
                'language': file_info.get('language'),
                'analysis': analysis_results
            },
            outcome="success",
            task_context={
                'operation': 'file_analysis',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        knowledge_id = await self.learning_agent.capture_knowledge_from_event(event)
        
        return {
            'success': True,
            'knowledge_captured': knowledge_id is not None,
            'knowledge_id': knowledge_id
        }
    
    async def report_task_dispatch(
        self,
        manager_agent_id: str,
        task: Dict[str, Any],
        assigned_agents: List[str],
        reasoning: str
    ) -> Dict[str, Any]:
        """
        Report task dispatch decision
        Helps learning agent understand delegation patterns
        """
        event = LearningEvent(
            event_id=str(uuid.uuid4()),
            event_type="task_dispatch",
            source=LearningSource.AGENT_INTERACTION,
            source_agent_id=manager_agent_id,
            data={
                'task_type': task.get('type'),
                'complexity': task.get('complexity'),
                'assigned_agents': assigned_agents,
                'reasoning': reasoning
            },
            outcome="success",
            task_context=task
        )
        
        await self.learning_agent.capture_knowledge_from_event(event)
        
        return {'success': True}
    
    async def get_agent_recommendations(
        self,
        task_type: str,
        task_description: str,
        available_agents: List[str]
    ) -> Dict[str, Any]:
        """
        Get recommendations for which agents to assign to task
        Based on historical performance and learning
        """
        recommendations = []
        
        for agent_id in available_agents:
            report = await self.learning_agent.get_agent_learning_report(agent_id)
            
            if report.get('error'):
                continue
            
            # Calculate suitability score
            score = 0.0
            
            # Check specializations
            if task_type in report.get('specializations', []):
                score += 0.4
            
            # Check strength areas
            if task_type in report.get('strength_areas', []):
                score += 0.3
            
            # Factor in success rate
            score += report.get('task_success_rate', 0) * 0.3
            
            if score > 0.3:
                recommendations.append({
                    'agent_id': agent_id,
                    'score': score,
                    'role': report['role'],
                    'specializations': report['specializations'],
                    'success_rate': report['task_success_rate']
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'recommendations': recommendations,
            'top_choice': recommendations[0] if recommendations else None
        }
    
    async def query_similar_solutions(
        self,
        problem_description: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Query for similar problems and their solutions
        Helps Manager Agent make better decisions
        """
        # Search for error resolutions and solutions
        results = await self.learning_agent.query_knowledge(
            query=problem_description,
            requesting_agent_id="manager",
            filters={
                'knowledge_type': KnowledgeType.ERROR_RESOLUTION.value,
                'min_quality': 2
            }
        )
        
        solutions = []
        for knowledge in results:
            solutions.append({
                'knowledge_id': knowledge.knowledge_id,
                'title': knowledge.title,
                'description': knowledge.description,
                'solution': knowledge.content.get('resolution'),
                'quality': knowledge.quality_level.value,
                'success_rate': knowledge.success_rate,
                'usage_count': knowledge.usage_count
            })
        
        return solutions
    
    async def request_collaboration_setup(
        self,
        agent_a: str,
        agent_b: str,
        objective: str
    ) -> Dict[str, Any]:
        """
        Request Learning Agent to facilitate knowledge exchange
        between two agents for better collaboration
        """
        result = await self.learning_agent.facilitate_knowledge_exchange(
            agent_a_id=agent_a,
            agent_b_id=agent_b,
            topic=objective
        )
        
        return result


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="YMERA Learning Agent API",
    description="Knowledge and learning management for YMERA platform",
    version="6.0.0"
)

# Global instances
learning_agent: Optional[YMERALearningAgent] = None
manager_interface: Optional[ManagerAgentInterface] = None


@app.on_event("startup")
async def startup():
    """Initialize learning agent"""
    global learning_agent, manager_interface
    
    from learning_agent_database import DatabaseManager
    
    # Initialize database
    db_manager = DatabaseManager(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/ymera",
        redis_url="redis://localhost:6379/0"
    )
    await db_manager.initialize()
    
    # Initialize learning agent
    config = {
        'agent_id': 'learning_coordinator_001',
        'knowledge_retention_days': 365
    }
    
    learning_agent = YMERALearningAgent(config, db_manager)
    await learning_agent.initialize()
    
    # Initialize manager interface
    manager_interface = ManagerAgentInterface(learning_agent)
    
    print("✓ Learning Agent API started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown learning agent"""
    if learning_agent:
        await learning_agent.shutdown()


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        'status': 'healthy',
        'service': 'learning-agent',
        'timestamp': datetime.utcnow().isoformat()
    }


@app.get("/status")
async def get_status():
    """Get system status"""
    if not learning_agent:
        raise HTTPException(status_code=503, detail="Learning agent not initialized")
    
    return await learning_agent.get_system_status()


# ============================================================================
# KNOWLEDGE CAPTURE ENDPOINTS
# ============================================================================

@app.post("/capture/code-analysis")
async def capture_code_analysis(
    request: CodeAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Capture learning from code analysis
    Called by Developer, Optimizer, or Debugger agents
    """
    event = LearningEvent(
        event_id=str(uuid.uuid4()),
        event_type="code_analysis",
        source=LearningSource.CODE_ANALYSIS,
        source_agent_id=request.agent_id,
        data={
            'language': request.language,
            'operation': request.operation,
            'file_path': request.file_path
        },
        outcome="success",
        code_context=request.code,
        task_context=request.context
    )
    
    # Process in background
    background_tasks.add_task(
        learning_agent.capture_knowledge_from_event,
        event
    )
    
    return {
        'success': True,
        'message': 'Code analysis queued for learning',
        'event_id': event.event_id
    }


@app.post("/capture/task-outcome")
async def capture_task_outcome(
    request: TaskOutcomeRequest,
    background_tasks: BackgroundTasks
):
    """
    Capture learning from task outcome
    Called by any agent after completing a task
    """
    event = LearningEvent(
        event_id=str(uuid.uuid4()),
        event_type="task_completion",
        source=LearningSource.AGENT_INTERACTION,
        source_agent_id=request.agent_id,
        data={
            'task_id': request.task_id,
            'task_type': request.task_type,
            'duration': request.duration_seconds,
            'errors': request.errors_encountered,
            'solutions': request.solutions_applied
        },
        outcome=request.outcome,
        code_context=request.code_produced,
        task_context=request.context
    )
    
    background_tasks.add_task(
        learning_agent.capture_knowledge_from_event,
        event
    )
    
    return {
        'success': True,
        'message': 'Task outcome recorded',
        'event_id': event.event_id
    }


@app.post("/capture/user-feedback")
async def capture_user_feedback(
    request: UserFeedbackRequest,
    background_tasks: BackgroundTasks
):
    """
    Capture learning from user feedback
    Called by Manager Agent when receiving user input
    """
    event = LearningEvent(
        event_id=str(uuid.uuid4()),
        event_type="user_feedback",
        source=LearningSource.USER_FEEDBACK,
        source_agent_id=request.agent_involved or "manager",
        data={
            'rating': request.rating,
            'feedback': request.feedback_text,
            'aspect': request.aspect,
            'session_id': request.session_id
        },
        outcome="success" if request.rating >= 4 else "neutral",
        user_context=request.context
    )
    
    background_tasks.add_task(
        learning_agent.capture_knowledge_from_event,
        event
    )
    
    return {
        'success': True,
        'message': 'User feedback captured for learning'
    }


@app.post("/capture/error-resolution")
async def capture_error_resolution(
    agent_id: str,
    error_type: str,
    error_message: str,
    resolution: str,
    code_fix: Optional[str] = None
):
    """
    Capture error resolution for future reference
    Called by Debugger or any agent that resolves an error
    """
    event = LearningEvent(
        event_id=str(uuid.uuid4()),
        event_type="error_resolution",
        source=LearningSource.ERROR_OCCURRENCE,
        source_agent_id=agent_id,
        data={
            'error_type': error_type,
            'error_message': error_message,
            'resolution': resolution,
            'code_fix': code_fix
        },
        outcome="success",
        code_context=code_fix
    )
    
    knowledge_id = await learning_agent.capture_knowledge_from_event(event)
    
    return {
        'success': True,
        'knowledge_id': knowledge_id,
        'message': 'Error resolution captured and will be shared with team'
    }


# ============================================================================
# KNOWLEDGE QUERY ENDPOINTS
# ============================================================================

@app.post("/query/knowledge")
async def query_knowledge(request: KnowledgeQueryRequest):
    """
    Query knowledge base
    Used by any agent to find relevant knowledge
    """
    filters = {}
    
    if request.knowledge_types:
        filters['knowledge_types'] = request.knowledge_types
    
    if request.min_quality:
        filters['min_quality'] = request.min_quality
    
    results = await learning_agent.query_knowledge(
        query=request.query,
        requesting_agent_id=request.agent_id,
        filters=filters
    )
    
    # Format results
    knowledge_items = []
    for knowledge in results[:request.limit]:
        knowledge_items.append({
            'knowledge_id': knowledge.knowledge_id,
            'type': knowledge.knowledge_type.value,
            'title': knowledge.title,
            'description': knowledge.description,
            'quality': knowledge.quality_level.value,
            'confidence': knowledge.confidence_score,
            'success_rate': knowledge.success_rate,
            'usage_count': knowledge.usage_count,
            'applicable_roles': [r.value for r in knowledge.applicable_roles],
            'tags': knowledge.tags,
            'created_at': knowledge.created_at.isoformat()
        })
    
    return {
        'success': True,
        'count': len(knowledge_items),
        'results': knowledge_items
    }


@app.get("/query/similar-solutions/{problem_hash}")
async def find_similar_solutions(
    problem_hash: str,
    requesting_agent: str,
    limit: int = 5
):
    """
    Find similar problems and solutions
    Used by agents when encountering new problems
    """
    # Search for error resolutions
    results = await learning_agent.query_knowledge(
        query=problem_hash,
        requesting_agent_id=requesting_agent,
        filters={'knowledge_type': KnowledgeType.ERROR_RESOLUTION.value}
    )
    
    solutions = []
    for knowledge in results[:limit]:
        solutions.append({
            'knowledge_id': knowledge.knowledge_id,
            'title': knowledge.title,
            'solution': knowledge.content.get('resolution'),
            'code_fix': knowledge.content.get('code_fix'),
            'success_rate': knowledge.success_rate,
            'quality': knowledge.quality_level.value
        })
    
    return {
        'found': len(solutions),
        'solutions': solutions
    }


@app.get("/query/best-practices/{domain}")
async def get_best_practices(
    domain: str,
    agent_id: str,
    limit: int = 10
):
    """
    Get best practices for a domain
    Used by agents to learn optimal approaches
    """
    results = await learning_agent.query_knowledge(
        query=domain,
        requesting_agent_id=agent_id,
        filters={
            'knowledge_type': KnowledgeType.BEST_PRACTICE.value,
            'min_quality': KnowledgeQuality.VALIDATED.value
        }
    )
    
    practices = []
    for knowledge in results[:limit]:
        practices.append({
            'title': knowledge.title,
            'description': knowledge.description,
            'content': knowledge.content,
            'quality': knowledge.quality_level.value,
            'success_rate': knowledge.success_rate
        })
    
    return {
        'domain': domain,
        'practices': practices
    }


# ============================================================================
# KNOWLEDGE FEEDBACK ENDPOINTS
# ============================================================================

@app.post("/feedback/application")
async def record_knowledge_application(request: KnowledgeApplicationFeedback):
    """
    Record feedback on knowledge application
    Critical for quality assessment
    """
    await learning_agent.record_knowledge_application(
        knowledge_id=request.knowledge_id,
        agent_id=request.agent_id,
        success=request.success,
        feedback=request.feedback,
        context=request.context
    )
    
    return {
        'success': True,
        'message': 'Application feedback recorded'
    }


@app.post("/feedback/validate/{knowledge_id}")
async def validate_knowledge(
    knowledge_id: str,
    validator_agent_id: str,
    validation_notes: str
):
    """
    Validate knowledge item
    Called by Validator or Reviewer agents
    """
    knowledge = learning_agent.knowledge_base.get(knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    knowledge.validated_by.append(validator_agent_id)
    knowledge.validation_notes.append(validation_notes)
    knowledge.updated_at = datetime.utcnow()
    
    # Increase quality if validated by multiple agents
    if len(knowledge.validated_by) >= 3:
        if knowledge.quality_level.value < KnowledgeQuality.VALIDATED.value:
            knowledge.quality_level = KnowledgeQuality.VALIDATED
    
    await learning_agent._persist_knowledge(knowledge)
    
    return {
        'success': True,
        'new_quality': knowledge.quality_level.value,
        'validators': len(knowledge.validated_by)
    }


# ============================================================================
# COLLABORATION ENDPOINTS
# ============================================================================

@app.post("/collaboration/setup")
async def setup_collaboration(request: CollaborationRequest):
    """
    Setup knowledge exchange between agents
    Called by Manager Agent
    """
    result = await learning_agent.facilitate_knowledge_exchange(
        agent_a_id=request.initiating_agent,
        agent_b_id=request.target_agent,
        topic=request.topic
    )
    
    return result


@app.get("/collaboration/recommendations/{agent_id}")
async def get_collaboration_recommendations(
    agent_id: str,
    objective: Optional[str] = None
):
    """
    Get collaboration recommendations for an agent
    Suggests best partners based on complementary knowledge
    """
    profile = learning_agent.agent_profiles.get(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    recommendations = []
    
    for other_id, other_profile in learning_agent.agent_profiles.items():
        if other_id == agent_id:
            continue
        
        # Calculate compatibility score
        score = 0.0
        
        # Check complementary specializations
        complementary = set(other_profile.specializations) - set(profile.specializations)
        score += len(complementary) * 0.2
        
        # Check if other has what this agent needs
        for improvement_area in profile.improvement_areas:
            if improvement_area in other_profile.strength_areas:
                score += 0.3
        
        # Check past collaboration success
        if other_id in profile.collaboration_partners:
            score += 0.2
        
        if score > 0.3:
            recommendations.append({
                'agent_id': other_id,
                'role': other_profile.role.value,
                'compatibility_score': score,
                'can_teach': list(complementary),
                'specializations': other_profile.specializations
            })
    
    recommendations.sort(key=lambda x: x['compatibility_score'], reverse=True)
    
    return {
        'agent_id': agent_id,
        'recommendations': recommendations[:5]
    }


# ============================================================================
# AGENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/agents/register")
async def register_agent(request: AgentRegistrationRequest):
    """
    Register new agent with learning system
    Called when new agent joins platform
    """
    from learning_agent_core import AgentLearningProfile, AgentRole
    
    profile = AgentLearningProfile(
        agent_id=request.agent_id,
        role=AgentRole(request.role),
        specializations=request.specializations
    )
    
    learning_agent.agent_profiles[request.agent_id] = profile
    
    return {
        'success': True,
        'agent_id': request.agent_id,
        'message': 'Agent registered for learning'
    }


@app.get("/agents/{agent_id}/report")
async def get_agent_report(agent_id: str):
    """
    Get comprehensive learning report for agent
    """
    report = await learning_agent.get_agent_learning_report(agent_id)
    return report


@app.get("/agents/{agent_id}/recommendations")
async def get_agent_recommendations(agent_id: str):
    """
    Get learning recommendations for agent
    Suggests areas for improvement and knowledge to acquire
    """
    profile = learning_agent.agent_profiles.get(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    recommendations = []
    
    # Recommend based on improvement areas
    for area in profile.improvement_areas:
        # Find high-quality knowledge in this area
        relevant_knowledge = [
            k for k in learning_agent.knowledge_base.values()
            if k.knowledge_type.value == area and 
            k.quality_level.value >= KnowledgeQuality.VALIDATED.value
        ]
        
        if relevant_knowledge:
            recommendations.append({
                'area': area,
                'priority': 'high',
                'knowledge_count': len(relevant_knowledge),
                'recommended_knowledge': [
                    {'id': k.knowledge_id, 'title': k.title}
                    for k in relevant_knowledge[:3]
                ]
            })
    
    return {
        'agent_id': agent_id,
        'recommendations': recommendations,
        'improvement_areas': profile.improvement_areas,
        'current_strengths': profile.strength_areas
    }


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/patterns")
async def get_learning_patterns():
    """
    Get analyzed learning patterns
    Useful for Manager Agent decision making
    """
    patterns = await learning_agent.analyze_patterns()
    return patterns


@app.get("/analytics/knowledge-graph/{knowledge_id}")
async def get_knowledge_relationships(
    knowledge_id: str,
    depth: int = 2
):
    """
    Get related knowledge using graph traversal
    """
    related = await learning_agent.get_related_knowledge(knowledge_id, depth)
    
    return {
        'knowledge_id': knowledge_id,
        'related_count': len(related),
        'related_knowledge': [
            {
                'id': k.knowledge_id,
                'title': k.title,
                'type': k.knowledge_type.value,
                'quality': k.quality_level.value
            }
            for k in related
        ]
    }


@app.get("/analytics/team-learning")
async def get_team_learning_analytics():
    """
    Get team-wide learning analytics
    """
    total_agents = len(learning_agent.agent_profiles)
    active_agents = len([
        p for p in learning_agent.agent_profiles.values()
        if (datetime.utcnow() - p.last_active).days < 7
    ])
    
    avg_velocity = sum(
        p.learning_velocity for p in learning_agent.agent_profiles.values()
    ) / total_agents if total_agents > 0 else 0
    
    # Knowledge by quality
    quality_dist = {}
    for k in learning_agent.knowledge_base.values():
        quality_dist[k.quality_level.name] = quality_dist.get(k.quality_level.name, 0) + 1
    
    return {
        'total_agents': total_agents,
        'active_agents': active_agents,
        'average_learning_velocity': avg_velocity,
        'total_knowledge': len(learning_agent.knowledge_base),
        'knowledge_by_quality': quality_dist,
        'total_flows': len(learning_agent.knowledge_flows),
        'successful_applications': learning_agent.metrics['successful_applications'],
        'failed_applications': learning_agent.metrics['failed_applications']
    }


# ============================================================================
# MANAGER AGENT SPECIFIC ENDPOINTS
# ============================================================================

@app.post("/manager/file-received")
async def manager_file_received(
    manager_id: str,
    file_info: Dict[str, Any],
    analysis: Dict[str, Any]
):
    """
    Manager reports file received from user
    """
    result = await manager_interface.report_file_received(
        manager_agent_id=manager_id,
        file_info=file_info,
        analysis_results=analysis
    )
    return result


@app.post("/manager/task-dispatch")
async def manager_task_dispatch(
    manager_id: str,
    task: Dict[str, Any],
    assigned_agents: List[str],
    reasoning: str
):
    """
    Manager reports task dispatch decision
    """
    result = await manager_interface.report_task_dispatch(
        manager_agent_id=manager_id,
        task=task,
        assigned_agents=assigned_agents,
        reasoning=reasoning
    )
    return result


@app.post("/manager/agent-recommendations")
async def get_manager_agent_recommendations(
    task_type: str,
    task_description: str,
    available_agents: List[str]
):
    """
    Get agent assignment recommendations from Learning Agent
    """
    recommendations = await manager_interface.get_agent_recommendations(
        task_type=task_type,
        task_description=task_description,
        available_agents=available_agents
    )
    return recommendations


@app.post("/manager/query-solutions")
async def manager_query_solutions(
    problem_description: str,
    context: Dict[str, Any]
):
    """
    Query for similar problems and solutions
    """
    solutions = await manager_interface.query_similar_solutions(
        problem_description=problem_description,
        context=context
    )
    return {
        'problem': problem_description,
        'solutions_found': len(solutions),
        'solutions': solutions
    }


# ============================================================================
# STREAMING ENDPOINTS
# ============================================================================

@app.get("/stream/learning-events")
async def stream_learning_events(agent_id: Optional[str] = None):
    """
    Stream learning events in real-time
    Useful for monitoring and dashboards
    """
    async def event_generator():
        while True:
            if learning_agent.learning_queue:
                event = learning_agent.learning_queue[-1]  # Peek at latest
                yield f"data: {json.dumps(asdict(event), default=str)}\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# ============================================================================
# UTILITY
# ============================================================================

import uuid

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)