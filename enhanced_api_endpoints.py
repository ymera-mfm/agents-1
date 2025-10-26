"""
Enhanced Learning Agent API - Complete REST Interface
Integrates with Communication Manager and Agent Manager
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json

from enhanced_learning_agent import (
    EnhancedLearningAgent,
    AgentCapability,
    KnowledgeRequest,
    ExternalKnowledgeSource,
    CollectiveKnowledgeLog
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class KnowledgeRequestModel(BaseModel):
    """Model for knowledge request"""
    requesting_agent_id: str
    query: str
    knowledge_type: Optional[str] = None
    urgency: str = Field(default="normal", pattern="^(low|normal|high|critical)$")
    context: Dict[str, Any] = {}


class AgentCapabilityUpdate(BaseModel):
    """Model for updating agent capability"""
    agent_id: str
    skills: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    knowledge_domains: Optional[List[str]] = None
    programming_languages: Optional[List[str]] = None
    frameworks: Optional[List[str]] = None
    availability: Optional[str] = None


class ExternalSourceConfig(BaseModel):
    """Model for configuring external source"""
    source_id: str
    source_type: str
    name: str
    endpoint: str
    auth_type: str = "none"
    credentials: Dict[str, str] = {}
    rate_limit: int = 100
    enabled: bool = True


class PeerSharingRequest(BaseModel):
    """Model for peer-to-peer knowledge sharing"""
    source_agent_id: str
    target_agent_id: str
    knowledge_ids: List[str]


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Enhanced YMERA Learning Agent API",
    description="Collective knowledge management with multi-source acquisition",
    version="7.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instance
enhanced_learning_agent: Optional[EnhancedLearningAgent] = None


@app.on_event("startup")
async def startup():
    """Initialize enhanced learning agent"""
    global enhanced_learning_agent
    
    from learning_agent_database import DatabaseManager
    
    db_manager = DatabaseManager(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/ymera",
        redis_url="redis://localhost:6379/0"
    )
    await db_manager.initialize()
    
    config = {
        'agent_id': 'learning_coordinator_001',
        'knowledge_retention_days': 365,
        'communication_manager_url': 'http://localhost:8002',
        'agent_manager_url': 'http://localhost:8003'
    }
    
    enhanced_learning_agent = EnhancedLearningAgent(config, db_manager)
    await enhanced_learning_agent.initialize()
    
    print("✓ Enhanced Learning Agent API started")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown with final reporting"""
    if enhanced_learning_agent:
        await enhanced_learning_agent.shutdown()


# ============================================================================
# CORE KNOWLEDGE REQUEST ENDPOINTS
# ============================================================================

@app.post("/knowledge/request")
async def request_knowledge(request: KnowledgeRequestModel):
    """
    Primary endpoint for agents to request knowledge
    
    Flow:
    1. Search internal knowledge
    2. Check permission if needed
    3. Query external sources if approved
    4. Return knowledge to requesting agent
    """
    result = await enhanced_learning_agent.handle_knowledge_request(
        requesting_agent_id=request.requesting_agent_id,
        query=request.query,
        knowledge_type=request.knowledge_type,
        context=request.context
    )
    
    return result


@app.get("/knowledge/request/{request_id}/status")
async def get_request_status(request_id: str):
    """Get status of a knowledge request"""
    request = enhanced_learning_agent.pending_requests.get(request_id)
    
    if not request:
        # Check history
        for historical_request in enhanced_learning_agent.request_history:
            if historical_request.request_id == request_id:
                request = historical_request
                break
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {
        'request_id': request.request_id,
        'status': request.status,
        'requesting_agent': request.requesting_agent_id,
        'query': request.query,
        'requested_at': request.requested_at.isoformat(),
        'fulfilled_at': request.fulfilled_at.isoformat() if request.fulfilled_at else None,
        'source': request.source,
        'requires_approval': request.requires_manager_approval,
        'approval_status': request.manager_approval_status
    }


# ============================================================================
# AGENT CAPABILITY ENDPOINTS
# ============================================================================

@app.post("/capabilities/update")
async def update_agent_capability(update: AgentCapabilityUpdate):
    """Update agent capability profile"""
    updates = update.dict(exclude_unset=True, exclude={'agent_id'})
    
    await enhanced_learning_agent.update_agent_capability(
        agent_id=update.agent_id,
        updates=updates
    )
    
    return {
        'success': True,
        'agent_id': update.agent_id,
        'message': 'Capability updated successfully'
    }


@app.get("/capabilities/{agent_id}")
async def get_agent_capability(agent_id: str):
    """Get detailed agent capability report"""
    report = await enhanced_learning_agent.get_agent_capability_report(agent_id)
    
    if 'error' in report:
        raise HTTPException(status_code=404, detail=report['error'])
    
    return report


@app.get("/capabilities/search/expertise")
async def search_by_expertise(
    domain: str,
    min_expertise: float = 0.5
):
    """Search for agents with expertise in specific domain"""
    agents = await enhanced_learning_agent.search_agents_by_expertise(
        domain=domain,
        min_expertise=min_expertise
    )
    
    return {
        'domain': domain,
        'min_expertise': min_expertise,
        'found': len(agents),
        'agents': agents
    }


@app.post("/capabilities/track/contribution")
async def track_knowledge_contribution(
    agent_id: str,
    knowledge_id: str
):
    """Track when agent contributes knowledge"""
    await enhanced_learning_agent.track_agent_knowledge_contribution(
        agent_id=agent_id,
        knowledge_id=knowledge_id
    )
    
    return {'success': True}


@app.post("/capabilities/track/usage")
async def track_knowledge_usage(
    agent_id: str,
    knowledge_id: str,
    success: bool
):
    """Track when agent uses knowledge"""
    await enhanced_learning_agent.track_agent_knowledge_usage(
        agent_id=agent_id,
        knowledge_id=knowledge_id,
        success=success
    )
    
    return {'success': True}


# ============================================================================
# PEER KNOWLEDGE SHARING ENDPOINTS
# ============================================================================

@app.post("/peer-sharing/facilitate")
async def facilitate_peer_sharing(request: PeerSharingRequest):
    """Facilitate direct knowledge sharing between agents"""
    result = await enhanced_learning_agent.facilitate_peer_knowledge_sharing(
        source_agent_id=request.source_agent_id,
        target_agent_id=request.target_agent_id,
        knowledge_ids=request.knowledge_ids
    )
    
    return result


@app.get("/peer-sharing/shareable/{agent_id}")
async def get_shareable_knowledge(
    agent_id: str,
    target_role: Optional[str] = None
):
    """Get knowledge that an agent can share"""
    shareable = await enhanced_learning_agent.get_shareable_knowledge(
        agent_id=agent_id,
        target_agent_role=target_role
    )
    
    return {
        'agent_id': agent_id,
        'shareable_count': len(shareable),
        'knowledge': shareable
    }


# ============================================================================
# COLLECTIVE KNOWLEDGE ENDPOINTS
# ============================================================================

@app.get("/collective/summary")
async def get_collective_summary():
    """Get summary of collective knowledge across all agents"""
    summary = await enhanced_learning_agent.get_collective_knowledge_summary()
    return summary


@app.get("/collective/catalog")
async def get_knowledge_catalog(
    export_full: bool = False
):
    """Get knowledge catalog"""
    if export_full:
        catalog = await enhanced_learning_agent.export_full_knowledge_catalog()
    else:
        # Return summary catalog
        catalog = {
            'total_items': len(enhanced_learning_agent.knowledge_base),
            'by_type': enhanced_learning_agent._count_knowledge_by_type(),
            'sample_items': [
                {
                    'id': k.knowledge_id,
                    'title': k.title,
                    'type': k.knowledge_type.value,
                    'quality': k.quality_level.value
                }
                for k in list(enhanced_learning_agent.knowledge_base.values())[:20]
            ]
        }
    
    return catalog


@app.get("/collective/flow-statistics")
async def get_flow_statistics():
    """Get knowledge flow statistics"""
    stats = await enhanced_learning_agent.get_knowledge_flow_statistics()
    return stats


@app.post("/collective/generate-log")
async def generate_knowledge_log():
    """Generate collective knowledge log on demand"""
    log = await enhanced_learning_agent.generate_collective_knowledge_log()
    
    return {
        'log_id': log.log_id,
        'timestamp': log.timestamp.isoformat(),
        'summary': {
            'total_agents': log.total_agents,
            'active_agents': log.active_agents,
            'total_knowledge': log.total_knowledge_items,
            'requests_processed': log.requests_processed
        },
        'message': 'Log generated successfully'
    }


@app.post("/collective/send-log-to-manager")
async def send_log_to_manager(reason: str = "on_demand"):
    """Send collective knowledge log to Agent Manager"""
    log = await enhanced_learning_agent.generate_collective_knowledge_log()
    await enhanced_learning_agent.send_log_to_agent_manager(log, reason=reason)
    
    return {
        'success': True,
        'log_id': log.log_id,
        'sent_at': datetime.utcnow().isoformat(),
        'reason': reason
    }


# ============================================================================
# EXTERNAL SOURCES ENDPOINTS
# ============================================================================

@app.post("/external-sources/configure")
async def configure_external_source(config: ExternalSourceConfig):
    """Configure a new external knowledge source"""
    from enhanced_learning_agent import ExternalKnowledgeSource
    
    source = ExternalKnowledgeSource(
        source_id=config.source_id,
        source_type=config.source_type,
        name=config.name,
        endpoint=config.endpoint,
        auth_type=config.auth_type,
        credentials=config.credentials,
        rate_limit=config.rate_limit,
        enabled=config.enabled
    )
    
    enhanced_learning_agent.external_sources[config.source_id] = source
    
    return {
        'success': True,
        'source_id': config.source_id,
        'message': 'External source configured'
    }


@app.get("/external-sources/status")
async def get_external_sources_status():
    """Get status of all external sources"""
    status = await enhanced_learning_agent.get_external_sources_status()
    return status


@app.post("/external-sources/{source_id}/enable")
async def enable_external_source(source_id: str):
    """Enable an external source"""
    if source_id not in enhanced_learning_agent.external_sources:
        raise HTTPException(status_code=404, detail="Source not found")
    
    enhanced_learning_agent.external_sources[source_id].enabled = True
    
    return {
        'success': True,
        'source_id': source_id,
        'enabled': True
    }


@app.post("/external-sources/{source_id}/disable")
async def disable_external_source(source_id: str):
    """Disable an external source"""
    if source_id not in enhanced_learning_agent.external_sources:
        raise HTTPException(status_code=404, detail="Source not found")
    
    enhanced_learning_agent.external_sources[source_id].enabled = False
    
    return {
        'success': True,
        'source_id': source_id,
        'enabled': False
    }


# ============================================================================
# COMMUNICATION MANAGER INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/comm/route-request")
async def route_knowledge_request_from_comm_manager(
    request_id: str,
    from_agent: str,
    to_agent: str,
    message_type: str,
    payload: Dict[str, Any]
):
    """
    Receive knowledge request routed through Communication Manager
    
    This is called by Communication Manager when an agent sends
    a knowledge request message
    """
    if message_type == "knowledge_request":
        result = await enhanced_learning_agent.handle_knowledge_request(
            requesting_agent_id=from_agent,
            query=payload.get('query', ''),
            knowledge_type=payload.get('knowledge_type'),
            context=payload.get('context', {})
        )
        
        # Send response back through Communication Manager
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{enhanced_learning_agent.communication_manager_url}/send",
                json={
                    'from': enhanced_learning_agent.agent_id,
                    'to': from_agent,
                    'message_type': 'knowledge_response',
                    'payload': result,
                    'in_response_to': request_id
                }
            )
        
        return {'success': True, 'routed': True}
    
    return {'success': False, 'error': 'Unknown message type'}


@app.post("/comm/notify")
async def receive_notification_from_comm_manager(
    notification_type: str,
    data: Dict[str, Any]
):
    """Receive notifications from Communication Manager"""
    enhanced_learning_agent.logger.info(
        "Notification received from Communication Manager",
        type=notification_type,
        data=data
    )
    
    return {'success': True, 'acknowledged': True}


# ============================================================================
# AGENT MANAGER INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/manager/approval-response")
async def receive_approval_response(
    request_id: str,
    approved: bool,
    reason: Optional[str] = None
):
    """
    Receive approval response from Agent Manager
    
    This is called by Agent Manager in response to approval requests
    """
    request = enhanced_learning_agent.pending_requests.get(request_id)
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if approved:
        request.manager_approval_status = "approved"
        enhanced_learning_agent.logger.info(
            "Manager approval received",
            request_id=request_id
        )
    else:
        request.manager_approval_status = "denied"
        request.status = "rejected"
        enhanced_learning_agent.logger.info(
            "Manager approval denied",
            request_id=request_id,
            reason=reason
        )
    
    return {
        'success': True,
        'request_id': request_id,
        'acknowledged': True
    }


@app.post("/manager/command")
async def receive_manager_command(
    command: str,
    parameters: Dict[str, Any]
):
    """
    Receive commands from Agent Manager
    
    Commands can include:
    - generate_report
    - disable_external_source
    - reset_metrics
    - etc.
    """
    if command == "generate_report":
        log = await enhanced_learning_agent.generate_collective_knowledge_log()
        await enhanced_learning_agent.send_log_to_agent_manager(log, reason="manager_command")
        return {'success': True, 'log_id': log.log_id}
    
    elif command == "disable_external_source":
        source_id = parameters.get('source_id')
        if source_id in enhanced_learning_agent.external_sources:
            enhanced_learning_agent.external_sources[source_id].enabled = False
            return {'success': True, 'source_id': source_id, 'disabled': True}
        return {'success': False, 'error': 'Source not found'}
    
    elif command == "reset_metrics":
        enhanced_learning_agent.enhanced_metrics = {
            'total_requests': 0,
            'internal_fulfillments': 0,
            'external_fulfillments': 0,
            'manager_approvals_required': 0,
            'manager_approvals_granted': 0,
            'abnormal_requests_detected': 0,
            'external_sources_used': defaultdict(int)
        }
        return {'success': True, 'metrics_reset': True}
    
    return {'success': False, 'error': 'Unknown command'}


# ============================================================================
# WEBSOCKET ENDPOINTS FOR REAL-TIME UPDATES
# ============================================================================

@app.websocket("/ws/knowledge-stream")
async def websocket_knowledge_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time knowledge updates
    
    Agents can connect to receive real-time notifications about:
    - New knowledge added
    - Knowledge quality updates
    - Relevant knowledge for their role
    """
    await websocket.accept()
    client_id = str(uuid.uuid4())
    
    try:
        # Wait for agent identification
        agent_data = await websocket.receive_json()
        agent_id = agent_data.get('agent_id')
        
        if not agent_id:
            await websocket.close(code=1008, reason="Agent ID required")
            return
        
        enhanced_learning_agent.logger.info(
            "WebSocket connection established",
            agent_id=agent_id,
            client_id=client_id
        )
        
        # Send initial knowledge summary
        summary = await enhanced_learning_agent.get_collective_knowledge_summary()
        await websocket.send_json({
            'type': 'initial_summary',
            'data': summary
        })
        
        # Keep connection alive and send updates
        while True:
            # Check for new relevant knowledge every 5 seconds
            await asyncio.sleep(5)
            
            # Get agent capability
            capability = enhanced_learning_agent.agent_capabilities.get(agent_id)
            if not capability:
                continue
            
            # Check for new knowledge relevant to this agent
            recent_knowledge = [
                k for k in enhanced_learning_agent.knowledge_base.values()
                if (datetime.utcnow() - k.created_at).seconds < 300  # Last 5 minutes
                and capability.role in k.applicable_roles
            ]
            
            if recent_knowledge:
                await websocket.send_json({
                    'type': 'new_knowledge',
                    'count': len(recent_knowledge),
                    'items': [
                        {
                            'id': k.knowledge_id,
                            'title': k.title,
                            'type': k.knowledge_type.value,
                            'quality': k.quality_level.value
                        }
                        for k in recent_knowledge[:5]
                    ]
                })
            
    except WebSocketDisconnect:
        enhanced_learning_agent.logger.info(
            "WebSocket disconnected",
            agent_id=agent_id,
            client_id=client_id
        )
    except Exception as e:
        enhanced_learning_agent.logger.error(
            "WebSocket error",
            error=str(e)
        )
        await websocket.close()


# ============================================================================
# ANALYTICS & MONITORING ENDPOINTS
# ============================================================================

@app.get("/analytics/request-patterns")
async def get_request_patterns():
    """Get request patterns for anomaly detection"""
    patterns = {}
    
    for agent_id, times in enhanced_learning_agent.request_patterns.items():
        patterns[agent_id] = {
            'total_requests': len(times),
            'requests_last_minute': len([
                t for t in times
                if (datetime.utcnow() - t).seconds < 60
            ]),
            'requests_last_hour': len([
                t for t in times
                if (datetime.utcnow() - t).seconds < 3600
            ])
        }
    
    return {
        'patterns': patterns,
        'abnormal_threshold': enhanced_learning_agent.abnormal_request_threshold
    }


@app.get("/analytics/metrics")
async def get_enhanced_metrics():
    """Get enhanced metrics"""
    return {
        'base_metrics': enhanced_learning_agent.metrics,
        'enhanced_metrics': dict(enhanced_learning_agent.enhanced_metrics),
        'timestamp': datetime.utcnow().isoformat()
    }


@app.get("/analytics/pending-requests")
async def get_pending_requests():
    """Get all pending knowledge requests"""
    pending = []
    
    for request in enhanced_learning_agent.pending_requests.values():
        pending.append({
            'request_id': request.request_id,
            'agent': request.requesting_agent_id,
            'query': request.query[:100],  # Truncate
            'status': request.status,
            'urgency': request.urgency,
            'requested_at': request.requested_at.isoformat(),
            'requires_approval': request.requires_manager_approval
        })
    
    return {
        'count': len(pending),
        'requests': pending
    }


@app.get("/analytics/knowledge-gaps")
async def identify_knowledge_gaps():
    """Identify knowledge gaps in the system"""
    gaps = []
    
    # Analyze failed requests
    failed_requests = [
        req for req in enhanced_learning_agent.request_history
        if req.status == "not_found"
    ]
    
    # Group by query similarity
    query_groups = defaultdict(list)
    for req in failed_requests[-100:]:  # Last 100 failed
        # Simple grouping by first few words
        query_key = ' '.join(req.query.split()[:3])
        query_groups[query_key].append(req)
    
    for query_key, requests in query_groups.items():
        if len(requests) >= 3:  # Multiple requests for similar knowledge
            gaps.append({
                'query_pattern': query_key,
                'request_count': len(requests),
                'requesting_agents': list(set([r.requesting_agent_id for r in requests])),
                'sample_query': requests[0].query
            })
    
    return {
        'identified_gaps': len(gaps),
        'gaps': gaps
    }


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        'status': 'healthy',
        'service': 'enhanced-learning-agent',
        'version': '7.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }


@app.get("/status")
async def get_status():
    """Get comprehensive system status"""
    status = await enhanced_learning_agent.get_system_status()
    
    # Add enhanced status
    status['enhanced'] = {
        'total_capabilities_tracked': len(enhanced_learning_agent.agent_capabilities),
        'external_sources': len(enhanced_learning_agent.external_sources),
        'enabled_sources': len([
            s for s in enhanced_learning_agent.external_sources.values()
            if s.enabled
        ]),
        'pending_requests': len(enhanced_learning_agent.pending_requests),
        'last_log_sent': (
            enhanced_learning_agent.last_log_sent.isoformat()
            if enhanced_learning_agent.last_log_sent
            else None
        )
    }
    
    return status


# ============================================================================
# UTILITY IMPORTS
# ============================================================================

import uuid
import httpx
from collections import defaultdict


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)