"""
YMERA Enhanced Learning Agent - Collective Knowledge & Multi-Source System
Version: 7.0.0 - Enterprise Enhanced

New Features:
- Collective agent knowledge and capabilities tracking
- Knowledge request routing and permission system
- Multi-source external knowledge acquisition (WebSocket, API, etc.)
- Communication Manager integration
- Agent Manager permission protocol
- Automatic and on-demand log reporting
- Abnormal request detection and escalation
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import hashlib

# Optional dependencies - Structured logging
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    structlog = None
    HAS_STRUCTLOG = False
# Optional dependencies - HTTP client
# Optional dependencies
try:
    import structlog
    HAS_STRUCTLOG = True
    logger = structlog.get_logger(__name__)
except ImportError:
    structlog = None
    HAS_STRUCTLOG = False
    logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    httpx = None
    HAS_HTTPX = False
# Optional dependencies - WebSocket support

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    websockets = None
    HAS_WEBSOCKETS = False

# Optional dependencies - SQL ORM
try:
    from sqlalchemy import text
    HAS_SQLALCHEMY = True
except ImportError:
    text = None
    HAS_SQLALCHEMY = False

# Previous imports from base learning agent
from learning_agent_core import (
    YMERALearningAgent,
    KnowledgeItem,
    KnowledgeType,
    LearningSource,
    AgentRole,
    KnowledgeQuality
)

# Setup logger with fallback
if HAS_STRUCTLOG:
    logger = structlog.get_logger(__name__)
else:
    logger = logging.getLogger(__name__)


# ============================================================================
# ENHANCED DATA MODELS
# ============================================================================

@dataclass
class AgentCapability:
    """Comprehensive agent capability profile"""
    agent_id: str
    role: AgentRole
    
    # Core capabilities
    skills: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    knowledge_domains: List[str] = field(default_factory=list)
    
    # Technical capabilities
    programming_languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    
    # Knowledge owned
    owned_knowledge: List[str] = field(default_factory=list)  # knowledge_ids
    shared_knowledge: List[str] = field(default_factory=list)  # knowledge_ids
    
    # Performance metrics
    expertise_level: Dict[str, float] = field(default_factory=dict)  # domain -> level
    success_rates: Dict[str, float] = field(default_factory=dict)  # task_type -> rate
    response_times: Dict[str, float] = field(default_factory=dict)  # task_type -> avg_time
    
    # Collaboration
    collaboration_history: List[str] = field(default_factory=list)
    preferred_partners: List[str] = field(default_factory=list)
    
    # Status
    current_load: int = 0
    availability: str = "available"  # available, busy, offline
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeRequest:
    """Request for knowledge from an agent"""
    request_id: str
    requesting_agent_id: str
    query: str
    knowledge_type: Optional[str] = None
    urgency: str = "normal"  # low, normal, high, critical
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Routing
    requested_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, approved, rejected, fulfilled
    
    # Permission tracking
    requires_manager_approval: bool = False
    manager_approval_status: Optional[str] = None
    approval_requested_at: Optional[datetime] = None
    
    # Fulfillment
    source: Optional[str] = None  # internal, external_api, external_websocket, peer_agent
    fulfilled_at: Optional[datetime] = None
    response: Optional[Dict[str, Any]] = None


@dataclass
class ExternalKnowledgeSource:
    """External knowledge source configuration"""
    source_id: str
    source_type: str  # api, websocket, database, search_engine
    name: str
    endpoint: str
    
    # Authentication
    auth_type: str = "none"  # none, api_key, oauth, bearer
    credentials: Dict[str, str] = field(default_factory=dict)
    
    # Configuration
    rate_limit: int = 100  # requests per hour
    timeout: int = 30  # seconds
    retry_count: int = 3
    
    # Status
    enabled: bool = True
    last_used: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0.0


@dataclass
class CollectiveKnowledgeLog:
    """Log entry for collective knowledge tracking"""
    log_id: str
    timestamp: datetime
    
    # Snapshot data
    total_agents: int
    active_agents: int
    total_knowledge_items: int
    
    # Agent capabilities summary
    agents_by_role: Dict[str, int]
    knowledge_by_type: Dict[str, int]
    
    # Activity summary
    requests_processed: int
    external_queries: int
    approvals_required: int
    
    # Detailed data
    agent_capabilities: Dict[str, AgentCapability]
    knowledge_catalog: List[Dict[str, Any]]
    recent_requests: List[KnowledgeRequest]
    
    # Anomalies
    abnormal_requests: List[str] = field(default_factory=list)
    security_events: List[str] = field(default_factory=list)


# ============================================================================
# ENHANCED LEARNING AGENT WITH COLLECTIVE KNOWLEDGE
# ============================================================================

class EnhancedLearningAgent(YMERALearningAgent):
    """
    Enhanced Learning Agent with:
    - Collective knowledge and agent capability tracking
    - Multi-source knowledge acquisition
    - Permission-based knowledge sharing
    - Communication Manager integration
    - Automatic reporting to Agent Manager
    """
    
    def __init__(self, config: Dict[str, Any], db_manager):
        super().__init__(config, db_manager)
        
        # Agent capability tracking
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        
        # Knowledge request management
        self.pending_requests: Dict[str, KnowledgeRequest] = {}
        self.request_history: deque = deque(maxlen=1000)
        
        # External knowledge sources
        self.external_sources: Dict[str, ExternalKnowledgeSource] = {}
        
        # Communication Manager connection
        self.communication_manager_url = config.get(
            'communication_manager_url',
            'http://localhost:8002'
        )
        
        # Agent Manager connection
        self.agent_manager_url = config.get(
            'agent_manager_url',
            'http://localhost:8003'
        )
        
        # Collective knowledge logs
        self.knowledge_logs: deque = deque(maxlen=100)
        self.last_log_sent: Optional[datetime] = None
        
        # Anomaly detection
        self.request_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.abnormal_request_threshold = 10  # requests per minute
        
        # Metrics
        self.enhanced_metrics = {
            'total_requests': 0,
            'internal_fulfillments': 0,
            'external_fulfillments': 0,
            'manager_approvals_required': 0,
            'manager_approvals_granted': 0,
            'abnormal_requests_detected': 0,
            'external_sources_used': defaultdict(int)
        }
        
        # WebSocket connections
        self.ws_connections: Dict[str, Any] = {}
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    async def initialize(self) -> bool:
        """Initialize enhanced learning agent"""
        # Call parent initialization
        success = await super().initialize()
        if not success:
            return False
        
        try:
            # Load agent capabilities
            await self._load_agent_capabilities()
            
            # Initialize external sources
            await self._initialize_external_sources()
            
            # Register with Communication Manager
            await self._register_with_communication_manager()
            
            # Start enhanced background tasks
            self._start_enhanced_background_tasks()
            
            self.logger.info(
                "Enhanced Learning Agent initialized",
                agents_tracked=len(self.agent_capabilities),
                external_sources=len(self.external_sources)
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Enhanced initialization failed", error=str(e))
            return False
    
    async def _load_agent_capabilities(self):
        """Load all agent capabilities"""
        agents = await self.db.list_agents(active_only=False)
        
        for agent_data in agents:
            capability = AgentCapability(
                agent_id=agent_data['agent_id'],
                role=AgentRole(agent_data['role']),
                specializations=agent_data.get('specializations', []),
                availability="available" if agent_data.get('active') else "offline"
            )
            
            # Load agent's knowledge contributions
            agent_knowledge = [
                k.knowledge_id for k in self.knowledge_base.values()
                if k.source_agent_id == agent_data['agent_id']
            ]
            capability.owned_knowledge = agent_knowledge
            
            self.agent_capabilities[capability.agent_id] = capability
        
        self.logger.info(f"Loaded {len(self.agent_capabilities)} agent capabilities")
    
    async def _initialize_external_sources(self):
        """Initialize external knowledge sources"""
        # Configure default external sources
        sources = [
            ExternalKnowledgeSource(
                source_id="stackoverflow_api",
                source_type="api",
                name="Stack Overflow API",
                endpoint="https://api.stackexchange.com/2.3/search",
                rate_limit=100
            ),
            ExternalKnowledgeSource(
                source_id="github_api",
                source_type="api",
                name="GitHub API",
                endpoint="https://api.github.com/search/code",
                auth_type="bearer",
                rate_limit=30
            ),
            ExternalKnowledgeSource(
                source_id="documentation_search",
                source_type="api",
                name="Documentation Search",
                endpoint="http://localhost:9000/search",
                rate_limit=200
            ),
            ExternalKnowledgeSource(
                source_id="realtime_learning",
                source_type="websocket",
                name="Real-time Learning Stream",
                endpoint="ws://localhost:9001/learning",
                rate_limit=1000
            )
        ]
        
        for source in sources:
            self.external_sources[source.source_id] = source
        
        self.logger.info(f"Initialized {len(self.external_sources)} external sources")
    
    async def _register_with_communication_manager(self):
        """Register with Communication Manager"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.communication_manager_url}/register",
                    json={
                        'agent_id': self.agent_id,
                        'agent_type': 'learning_coordinator',
                        'capabilities': ['knowledge_management', 'learning_coordination'],
                        'endpoints': {
                            'knowledge_request': '/knowledge/request',
                            'knowledge_query': '/knowledge/query'
                        }
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.logger.info("Registered with Communication Manager")
                else:
                    self.logger.warning(
                        "Communication Manager registration failed",
                        status=response.status_code
                    )
                    
        except Exception as e:
            self.logger.warning(
                "Could not register with Communication Manager",
                error=str(e)
            )
    
    def _start_enhanced_background_tasks(self):
        """Start enhanced background tasks"""
        asyncio.create_task(self._knowledge_request_processing_loop())
        asyncio.create_task(self._capability_tracking_loop())
        asyncio.create_task(self._log_reporting_loop())
        asyncio.create_task(self._external_source_health_check_loop())
        asyncio.create_task(self._anomaly_detection_loop())
    
    # ========================================================================
    # KNOWLEDGE REQUEST HANDLING
    # ========================================================================
    
    async def handle_knowledge_request(
        self,
        requesting_agent_id: str,
        query: str,
        knowledge_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle knowledge request from agent via Communication Manager
        
        Flow:
        1. Check if knowledge exists internally
        2. If found, check if sharing requires permission
        3. If not found or permission needed, request from Agent Manager
        4. If approved and not found, query external sources
        5. Return knowledge to requesting agent
        """
        try:
            # Create request record
            request = KnowledgeRequest(
                request_id=str(uuid.uuid4()),
                requesting_agent_id=requesting_agent_id,
                query=query,
                knowledge_type=knowledge_type,
                context=context or {}
            )
            
            self.pending_requests[request.request_id] = request
            self.enhanced_metrics['total_requests'] += 1
            
            # Detect abnormal request pattern
            is_abnormal = await self._check_abnormal_request(requesting_agent_id)
            if is_abnormal:
                request.urgency = "critical"
                request.requires_manager_approval = True
                self.enhanced_metrics['abnormal_requests_detected'] += 1
                
                # Immediate notification to Agent Manager
                await self._notify_agent_manager_abnormal_request(request)
            
            # Step 1: Search internal knowledge
            internal_results = await self._search_internal_knowledge(request)
            
            if internal_results:
                # Check if permission needed for sensitive knowledge
                needs_permission = self._check_permission_required(
                    internal_results,
                    requesting_agent_id
                )
                
                if not needs_permission:
                    # Direct fulfillment
                    request.status = "fulfilled"
                    request.source = "internal"
                    request.fulfilled_at = datetime.utcnow()
                    request.response = internal_results
                    
                    self.enhanced_metrics['internal_fulfillments'] += 1
                    
                    self.logger.info(
                        "Knowledge request fulfilled internally",
                        request_id=request.request_id,
                        agent=requesting_agent_id
                    )
                    
                    return {
                        'success': True,
                        'request_id': request.request_id,
                        'source': 'internal',
                        'knowledge': internal_results
                    }
                else:
                    # Request permission from Agent Manager
                    request.requires_manager_approval = True
                    approval = await self._request_manager_approval(request, internal_results)
                    
                    if approval['approved']:
                        request.status = "fulfilled"
                        request.fulfilled_at = datetime.utcnow()
                        request.response = internal_results
                        
                        return {
                            'success': True,
                            'request_id': request.request_id,
                            'source': 'internal',
                            'knowledge': internal_results,
                            'approval_required': True
                        }
                    else:
                        request.status = "rejected"
                        return {
                            'success': False,
                            'request_id': request.request_id,
                            'reason': 'Manager approval denied',
                            'message': approval.get('reason')
                        }
            
            # Step 2: Knowledge not found internally, request external access
            request.requires_manager_approval = True
            external_approval = await self._request_external_access_approval(request)
            
            if not external_approval['approved']:
                request.status = "rejected"
                return {
                    'success': False,
                    'request_id': request.request_id,
                    'reason': 'External access denied',
                    'message': external_approval.get('reason')
                }
            
            # Step 3: Query external sources
            external_results = await self._query_external_sources(request)
            
            if external_results:
                request.status = "fulfilled"
                request.source = external_results['source']
                request.fulfilled_at = datetime.utcnow()
                request.response = external_results['knowledge']
                
                self.enhanced_metrics['external_fulfillments'] += 1
                
                # Store externally acquired knowledge
                await self._store_external_knowledge(external_results, request)
                
                return {
                    'success': True,
                    'request_id': request.request_id,
                    'source': 'external',
                    'external_source': external_results['source'],
                    'knowledge': external_results['knowledge']
                }
            else:
                request.status = "not_found"
                return {
                    'success': False,
                    'request_id': request.request_id,
                    'reason': 'Knowledge not found',
                    'message': 'No relevant knowledge found in internal or external sources'
                }
                
        except Exception as e:
            self.logger.error("Knowledge request handling failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _search_internal_knowledge(
        self,
        request: KnowledgeRequest
    ) -> Optional[Dict[str, Any]]:
        """Search internal knowledge base"""
        # Use parent's query_knowledge method
        results = await self.query_knowledge(
            query=request.query,
            requesting_agent_id=request.requesting_agent_id,
            filters={'knowledge_type': request.knowledge_type} if request.knowledge_type else None
        )
        
        if results:
            return {
                'items': [
                    {
                        'knowledge_id': k.knowledge_id,
                        'title': k.title,
                        'description': k.description,
                        'content': k.content,
                        'quality': k.quality_level.value,
                        'confidence': k.confidence_score,
                        'source_agent': k.source_agent_id
                    }
                    for k in results[:5]
                ],
                'count': len(results)
            }
        
        return None
    
    def _check_permission_required(
        self,
        knowledge: Dict[str, Any],
        requesting_agent_id: str
    ) -> bool:
        """Check if permission required to share knowledge"""
        # Check if knowledge is sensitive or proprietary
        for item in knowledge.get('items', []):
            source_agent = item.get('source_agent')
            
            # Check if source agent has restrictions
            capability = self.agent_capabilities.get(source_agent)
            if capability and source_agent != requesting_agent_id:
                # Check if knowledge is in shared list
                if item['knowledge_id'] not in capability.shared_knowledge:
                    return True
            
            # Check if high-value knowledge
            if item.get('quality', 0) >= KnowledgeQuality.PROVEN.value:
                return True
        
        return False
    
    async def _request_manager_approval(
        self,
        request: KnowledgeRequest,
        knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request approval from Agent Manager"""
        try:
            self.enhanced_metrics['manager_approvals_required'] += 1
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_manager_url}/approvals/knowledge-sharing",
                    json={
                        'request_id': request.request_id,
                        'requesting_agent': request.requesting_agent_id,
                        'query': request.query,
                        'knowledge_summary': {
                            'count': knowledge.get('count', 0),
                            'items': [
                                {
                                    'id': item['knowledge_id'],
                                    'title': item['title'],
                                    'source': item['source_agent']
                                }
                                for item in knowledge.get('items', [])[:3]
                            ]
                        },
                        'reason': 'Sensitive or proprietary knowledge sharing',
                        'urgency': request.urgency
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('approved'):
                        self.enhanced_metrics['manager_approvals_granted'] += 1
                        request.manager_approval_status = "approved"
                    else:
                        request.manager_approval_status = "denied"
                    
                    request.approval_requested_at = datetime.utcnow()
                    
                    return result
                else:
                    # Default to approval if manager unavailable (configurable)
                    return {'approved': True, 'reason': 'Manager unavailable, auto-approved'}
                    
        except Exception as e:
            self.logger.error("Manager approval request failed", error=str(e))
            # Default behavior on error
            return {'approved': True, 'reason': 'Error occurred, auto-approved'}
    
    async def _request_external_access_approval(
        self,
        request: KnowledgeRequest
    ) -> Dict[str, Any]:
        """Request approval for external knowledge access"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_manager_url}/approvals/external-access",
                    json={
                        'request_id': request.request_id,
                        'requesting_agent': request.requesting_agent_id,
                        'query': request.query,
                        'reason': 'Knowledge not found internally',
                        'urgency': request.urgency,
                        'context': request.context
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    request.approval_requested_at = datetime.utcnow()
                    
                    if result.get('approved'):
                        self.enhanced_metrics['manager_approvals_granted'] += 1
                        request.manager_approval_status = "approved"
                    else:
                        request.manager_approval_status = "denied"
                    
                    return result
                else:
                    # Deny external access by default if manager unavailable
                    return {
                        'approved': False,
                        'reason': 'Manager unavailable, external access denied by default'
                    }
                    
        except Exception as e:
            self.logger.error("External access approval failed", error=str(e))
            return {'approved': False, 'reason': 'Error occurred'}
    
    async def _query_external_sources(
        self,
        request: KnowledgeRequest
    ) -> Optional[Dict[str, Any]]:
        """Query external knowledge sources"""
        # Try each external source based on query type
        for source_id, source in self.external_sources.items():
            if not source.enabled:
                continue
            
            try:
                if source.source_type == "api":
                    result = await self._query_external_api(source, request)
                elif source.source_type == "websocket":
                    result = await self._query_external_websocket(source, request)
                else:
                    continue
                
                if result:
                    self.enhanced_metrics['external_sources_used'][source_id] += 1
                    source.success_count += 1
                    source.last_used = datetime.utcnow()
                    
                    return {
                        'source': source_id,
                        'knowledge': result
                    }
                    
            except Exception as e:
                self.logger.error(
                    "External source query failed",
                    source=source_id,
                    error=str(e)
                )
                source.failure_count += 1
        
        return None
    
    async def _query_external_api(
        self,
        source: ExternalKnowledgeSource,
        request: KnowledgeRequest
    ) -> Optional[Dict[str, Any]]:
        """Query external API source"""
        try:
            headers = {}
            if source.auth_type == "api_key":
                headers['X-API-Key'] = source.credentials.get('api_key', '')
            elif source.auth_type == "bearer":
                headers['Authorization'] = f"Bearer {source.credentials.get('token', '')}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    source.endpoint,
                    params={'q': request.query},
                    headers=headers,
                    timeout=source.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Process and normalize response
                    return self._normalize_external_response(data, source.source_id)
                    
        except Exception as e:
            self.logger.error(f"API query failed: {e}")
            return None
    
    async def _query_external_websocket(
        self,
        source: ExternalKnowledgeSource,
        request: KnowledgeRequest
    ) -> Optional[Dict[str, Any]]:
        """Query external WebSocket source"""
        try:
            async with websockets.connect(source.endpoint) as websocket:
                # Send query
                await websocket.send(json.dumps({
                    'type': 'query',
                    'query': request.query,
                    'context': request.context
                }))
                
                # Wait for response with timeout
                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=source.timeout
                )
                
                data = json.loads(response)
                return self._normalize_external_response(data, source.source_id)
                
        except Exception as e:
            self.logger.error(f"WebSocket query failed: {e}")
            return None
    
    def _normalize_external_response(
        self,
        data: Dict[str, Any],
        source_id: str
    ) -> Dict[str, Any]:
        """Normalize external response to standard format"""
        # This would be customized based on each source's response format
        return {
            'items': data.get('items', []),
            'source': source_id,
            'metadata': data.get('metadata', {})
        }
    
    async def _store_external_knowledge(
        self,
        external_results: Dict[str, Any],
        request: KnowledgeRequest
    ):
        """Store externally acquired knowledge in internal knowledge base"""
        try:
            for item in external_results['knowledge'].get('items', [])[:3]:
                knowledge = KnowledgeItem(
                    knowledge_id=str(uuid.uuid4()),
                    knowledge_type=KnowledgeType.BEST_PRACTICE,  # Default type
                    source=LearningSource.EXTERNAL_RESOURCE,
                    source_agent_id=self.agent_id,
                    title=item.get('title', 'External Knowledge'),
                    description=item.get('description', ''),
                    content=item,
                    quality_level=KnowledgeQuality.EXPERIMENTAL,
                    confidence_score=0.6,
                    tags=[external_results['source'], 'external']
                )
                
                self.knowledge_base[knowledge.knowledge_id] = knowledge
                await self._persist_knowledge(knowledge)
                
                self.logger.info(
                    "External knowledge stored",
                    knowledge_id=knowledge.knowledge_id,
                    source=external_results['source']
                )
                
        except Exception as e:
            self.logger.error("Failed to store external knowledge", error=str(e))
    
    # ========================================================================
    # AGENT CAPABILITY TRACKING
    # ========================================================================
    
    async def update_agent_capability(
        self,
        agent_id: str,
        updates: Dict[str, Any]
    ):
        """Update agent capability profile"""
        capability = self.agent_capabilities.get(agent_id)
        if not capability:
            self.logger.warning(f"Agent {agent_id} not found in capabilities")
            return
        
        # Update fields
        for key, value in updates.items():
            if hasattr(capability, key):
                setattr(capability, key, value)
        
        capability.last_updated = datetime.utcnow()
        
        self.logger.info(f"Updated capability for agent {agent_id}")
    
    async def track_agent_knowledge_contribution(
        self,
        agent_id: str,
        knowledge_id: str
    ):
        """Track when agent contributes knowledge"""
        capability = self.agent_capabilities.get(agent_id)
        if capability:
            if knowledge_id not in capability.owned_knowledge:
                capability.owned_knowledge.append(knowledge_id)
                capability.last_updated = datetime.utcnow()
    
    async def track_agent_knowledge_usage(
        self,
        agent_id: str,
        knowledge_id: str,
        success: bool
    ):
        """Track when agent uses knowledge"""
        capability = self.agent_capabilities.get(agent_id)
        if not capability:
            return
        
        # Update expertise level for knowledge domain
        knowledge = self.knowledge_base.get(knowledge_id)
        if knowledge:
            domain = knowledge.knowledge_type.value
            
            current_level = capability.expertise_level.get(domain, 0.0)
            if success:
                new_level = min(current_level + 0.1, 1.0)
            else:
                new_level = max(current_level - 0.05, 0.0)
            
            capability.expertise_level[domain] = new_level
            capability.last_updated = datetime.utcnow()
    
    def get_agents_with_capability(
        self,
        skill: Optional[str] = None,
        knowledge_domain: Optional[str] = None,
        min_expertise: float = 0.5
    ) -> List[AgentCapability]:
        """Find agents with specific capabilities"""
        matching_agents = []
        
        for capability in self.agent_capabilities.values():
            if capability.availability != "available":
                continue
            
            if skill and skill not in capability.skills:
                continue
            
            if knowledge_domain:
                expertise = capability.expertise_level.get(knowledge_domain, 0.0)
                if expertise < min_expertise:
                    continue
            
            matching_agents.append(capability)
        
        # Sort by expertise level
        if knowledge_domain:
            matching_agents.sort(
                key=lambda c: c.expertise_level.get(knowledge_domain, 0.0),
                reverse=True
            )
        
        return matching_agents
    
    # ========================================================================
    # COLLECTIVE KNOWLEDGE LOGGING
    # ========================================================================
    
    async def generate_collective_knowledge_log(self) -> CollectiveKnowledgeLog:
        """Generate comprehensive collective knowledge log"""
        log = CollectiveKnowledgeLog(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            total_agents=len(self.agent_capabilities),
            active_agents=len([
                c for c in self.agent_capabilities.values()
                if c.availability == "available"
            ]),
            total_knowledge_items=len(self.knowledge_base),
            agents_by_role=self._count_agents_by_role(),
            knowledge_by_type=self._count_knowledge_by_type(),
            requests_processed=self.enhanced_metrics['total_requests'],
            external_queries=self.enhanced_metrics['external_fulfillments'],
            approvals_required=self.enhanced_metrics['manager_approvals_required'],
            agent_capabilities={
                agent_id: capability
                for agent_id, capability in self.agent_capabilities.items()
            },
            knowledge_catalog=self._create_knowledge_catalog(),
            recent_requests=[
                req for req in list(self.request_history)[-50:]
            ]
        )
        
        # Check for abnormal requests
        for request in list(self.pending_requests.values()):
            if request.urgency == "critical":
                log.abnormal_requests.append(request.request_id)
        
        self.knowledge_logs.append(log)
        return log
    
    def _count_agents_by_role(self) -> Dict[str, int]:
        """Count agents by role"""
        counts = defaultdict(int)
        for capability in self.agent_capabilities.values():
            counts[capability.role.value] += 1
        return dict(counts)
    
    def _count_knowledge_by_type(self) -> Dict[str, int]:
        """Count knowledge by type"""
        counts = defaultdict(int)
        for knowledge in self.knowledge_base.values():
            counts[knowledge.knowledge_type.value] += 1
        return dict(counts)
    
    def _create_knowledge_catalog(self) -> List[Dict[str, Any]]:
        """Create catalog of all knowledge items"""
        catalog = []
        
        for knowledge in self.knowledge_base.values():
            catalog.append({
                'knowledge_id': knowledge.knowledge_id,
                'type': knowledge.knowledge_type.value,
                'title': knowledge.title,
                'source_agent': knowledge.source_agent_id,
                'quality': knowledge.quality_level.value,
                'confidence': knowledge.confidence_score,
                'usage_count': knowledge.usage_count,
                'success_rate': knowledge.success_rate,
                'tags': knowledge.tags,
                'created_at': knowledge.created_at.isoformat()
            })
        
        return catalog
    
    async def send_log_to_agent_manager(
        self,
        log: CollectiveKnowledgeLog,
        reason: str = "scheduled"
    ):
        """Send collective knowledge log to Agent Manager"""
        try:
            # Prepare log data for transmission
            log_data = {
                'log_id': log.log_id,
                'timestamp': log.timestamp.isoformat(),
                'reason': reason,
                'summary': {
                    'total_agents': log.total_agents,
                    'active_agents': log.active_agents,
                    'total_knowledge': log.total_knowledge_items,
                    'agents_by_role': log.agents_by_role,
                    'knowledge_by_type': log.knowledge_by_type
                },
                'activity': {
                    'requests_processed': log.requests_processed,
                    'external_queries': log.external_queries,
                    'approvals_required': log.approvals_required
                },
                'agent_capabilities': {
                    agent_id: {
                        'role': cap.role.value,
                        'skills': cap.skills,
                        'specializations': cap.specializations,
                        'knowledge_domains': cap.knowledge_domains,
                        'expertise_level': cap.expertise_level,
                        'owned_knowledge_count': len(cap.owned_knowledge),
                        'availability': cap.availability
                    }
                    for agent_id, cap in log.agent_capabilities.items()
                },
                'knowledge_catalog_summary': {
                    'total_items': len(log.knowledge_catalog),
                    'by_quality': self._summarize_knowledge_quality(log.knowledge_catalog)
                },
                'abnormal_requests': log.abnormal_requests,
                'security_events': log.security_events
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_manager_url}/reports/collective-knowledge",
                    json=log_data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    self.last_log_sent = datetime.utcnow()
                    self.logger.info(
                        "Collective knowledge log sent to Agent Manager",
                        log_id=log.log_id,
                        reason=reason
                    )
                else:
                    self.logger.error(
                        "Failed to send log to Agent Manager",
                        status=response.status_code
                    )
                    
        except Exception as e:
            self.logger.error("Failed to send log to Agent Manager", error=str(e))
    
    def _summarize_knowledge_quality(
        self,
        catalog: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Summarize knowledge quality distribution"""
        quality_counts = defaultdict(int)
        for item in catalog:
            quality_counts[item['quality']] += 1
        return dict(quality_counts)
    
    # ========================================================================
    # ANOMALY DETECTION
    # ========================================================================
    
    async def _check_abnormal_request(self, agent_id: str) -> bool:
        """Check if request pattern is abnormal"""
        current_time = datetime.utcnow()
        
        # Add current request time
        self.request_patterns[agent_id].append(current_time)
        
        # Clean old requests (older than 1 minute)
        cutoff_time = current_time - timedelta(minutes=1)
        self.request_patterns[agent_id] = [
            t for t in self.request_patterns[agent_id]
            if t > cutoff_time
        ]
        
        # Check if exceeds threshold
        request_count = len(self.request_patterns[agent_id])
        
        if request_count > self.abnormal_request_threshold:
            self.logger.warning(
                "Abnormal request pattern detected",
                agent_id=agent_id,
                request_count=request_count,
                threshold=self.abnormal_request_threshold
            )
            return True
        
        return False
    
    async def _notify_agent_manager_abnormal_request(
        self,
        request: KnowledgeRequest
    ):
        """Notify Agent Manager of abnormal request immediately"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.agent_manager_url}/alerts/abnormal-request",
                    json={
                        'request_id': request.request_id,
                        'agent_id': request.requesting_agent_id,
                        'query': request.query,
                        'timestamp': request.requested_at.isoformat(),
                        'request_count': len(self.request_patterns[request.requesting_agent_id]),
                        'alert_level': 'high'
                    },
                    timeout=10
                )
                
                self.logger.info(
                    "Abnormal request alert sent to Agent Manager",
                    request_id=request.request_id
                )
                
        except Exception as e:
            self.logger.error("Failed to send abnormal request alert", error=str(e))
    
    # ========================================================================
    # KNOWLEDGE SHARING BETWEEN AGENTS
    # ========================================================================
    
    async def facilitate_peer_knowledge_sharing(
        self,
        source_agent_id: str,
        target_agent_id: str,
        knowledge_ids: List[str]
    ) -> Dict[str, Any]:
        """Facilitate direct knowledge sharing between agents"""
        try:
            source_capability = self.agent_capabilities.get(source_agent_id)
            target_capability = self.agent_capabilities.get(target_agent_id)
            
            if not source_capability or not target_capability:
                return {
                    'success': False,
                    'error': 'Agent not found'
                }
            
            # Update shared knowledge lists
            shared_count = 0
            for knowledge_id in knowledge_ids:
                if knowledge_id in source_capability.owned_knowledge:
                    if knowledge_id not in source_capability.shared_knowledge:
                        source_capability.shared_knowledge.append(knowledge_id)
                    shared_count += 1
            
            # Update collaboration history
            if target_agent_id not in source_capability.collaboration_history:
                source_capability.collaboration_history.append(target_agent_id)
            
            if source_agent_id not in target_capability.collaboration_history:
                target_capability.collaboration_history.append(source_agent_id)
            
            self.logger.info(
                "Peer knowledge sharing facilitated",
                source=source_agent_id,
                target=target_agent_id,
                knowledge_count=shared_count
            )
            
            return {
                'success': True,
                'shared_count': shared_count,
                'message': f'Shared {shared_count} knowledge items'
            }
            
        except Exception as e:
            self.logger.error("Peer knowledge sharing failed", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def get_shareable_knowledge(
        self,
        agent_id: str,
        target_agent_role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get knowledge that an agent can share"""
        capability = self.agent_capabilities.get(agent_id)
        if not capability:
            return []
        
        shareable = []
        
        for knowledge_id in capability.owned_knowledge:
            knowledge = self.knowledge_base.get(knowledge_id)
            if not knowledge:
                continue
            
            # Check if already shared
            if knowledge_id in capability.shared_knowledge:
                continue
            
            # Check if applicable to target role
            if target_agent_role:
                try:
                    target_role = AgentRole(target_agent_role)
                    if target_role not in knowledge.applicable_roles:
                        continue
                except ValueError:
                    pass
            
            shareable.append({
                'knowledge_id': knowledge_id,
                'title': knowledge.title,
                'type': knowledge.knowledge_type.value,
                'quality': knowledge.quality_level.value,
                'confidence': knowledge.confidence_score
            })
        
        return shareable
    
    # ========================================================================
    # BACKGROUND TASKS
    # ========================================================================
    
    async def _knowledge_request_processing_loop(self):
        """Process pending knowledge requests"""
        while self.running:
            try:
                # Process pending requests with timeout
                current_time = datetime.utcnow()
                timeout_threshold = timedelta(minutes=5)
                
                for request_id, request in list(self.pending_requests.items()):
                    if request.status == "pending":
                        age = current_time - request.requested_at
                        if age > timeout_threshold:
                            request.status = "timeout"
                            self.logger.warning(
                                "Knowledge request timeout",
                                request_id=request_id
                            )
                    
                    # Move to history if completed or timed out
                    if request.status in ["fulfilled", "rejected", "timeout", "not_found"]:
                        self.request_history.append(request)
                        del self.pending_requests[request_id]
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error("Request processing loop error", error=str(e))
                await asyncio.sleep(30)
    
    async def _capability_tracking_loop(self):
        """Update agent capabilities periodically"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Update expertise levels based on recent activity
                for agent_id, capability in self.agent_capabilities.items():
                    # Check recent activity
                    recent_requests = [
                        req for req in self.request_history
                        if req.requesting_agent_id == agent_id
                        and (datetime.utcnow() - req.requested_at).days < 7
                    ]
                    
                    # Update activity metrics
                    capability.current_load = len([
                        req for req in self.pending_requests.values()
                        if req.requesting_agent_id == agent_id
                    ])
                    
                    # Update availability based on load
                    if capability.current_load > 10:
                        capability.availability = "busy"
                    elif capability.current_load == 0:
                        capability.availability = "available"
                
            except Exception as e:
                self.logger.error("Capability tracking error", error=str(e))
    
    async def _log_reporting_loop(self):
        """Send logs to Agent Manager twice daily"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Check if it's time for scheduled report (every 12 hours)
                if self.last_log_sent is None:
                    should_send = True
                else:
                    time_since_last = current_time - self.last_log_sent
                    should_send = time_since_last >= timedelta(hours=12)
                
                if should_send:
                    # Generate and send log
                    log = await self.generate_collective_knowledge_log()
                    await self.send_log_to_agent_manager(log, reason="scheduled")
                
                # Sleep for 1 hour before checking again
                await asyncio.sleep(3600)
                
            except Exception as e:
                self.logger.error("Log reporting error", error=str(e))
                await asyncio.sleep(3600)
    
    async def _external_source_health_check_loop(self):
        """Check health of external sources"""
        while self.running:
            try:
                await asyncio.sleep(600)  # Every 10 minutes
                
                for source_id, source in self.external_sources.items():
                    if not source.enabled:
                        continue
                    
                    # Check failure rate
                    total = source.success_count + source.failure_count
                    if total > 10:
                        failure_rate = source.failure_count / total
                        
                        if failure_rate > 0.5:
                            source.enabled = False
                            self.logger.warning(
                                "External source disabled due to high failure rate",
                                source_id=source_id,
                                failure_rate=failure_rate
                            )
                
            except Exception as e:
                self.logger.error("External source health check error", error=str(e))
    
    async def _anomaly_detection_loop(self):
        """Detect and report anomalies"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Check for unusual patterns
                current_time = datetime.utcnow()
                
                # Check for agents with excessive requests
                for agent_id, times in self.request_patterns.items():
                    recent_requests = [
                        t for t in times
                        if (current_time - t).seconds < 300  # Last 5 minutes
                    ]
                    
                    if len(recent_requests) > 20:
                        # Generate immediate alert log
                        log = await self.generate_collective_knowledge_log()
                        log.security_events.append(
                            f"Excessive requests from {agent_id}: {len(recent_requests)} in 5 minutes"
                        )
                        
                        # Send immediate log
                        await self.send_log_to_agent_manager(log, reason="security_alert")
                
            except Exception as e:
                self.logger.error("Anomaly detection error", error=str(e))
    
    # ========================================================================
    # ENHANCED PUBLIC API
    # ========================================================================
    
    async def get_collective_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of collective knowledge"""
        return {
            'total_agents': len(self.agent_capabilities),
            'active_agents': len([
                c for c in self.agent_capabilities.values()
                if c.availability == "available"
            ]),
            'total_knowledge': len(self.knowledge_base),
            'knowledge_by_type': self._count_knowledge_by_type(),
            'agents_by_role': self._count_agents_by_role(),
            'metrics': {
                **self.metrics,
                **self.enhanced_metrics
            },
            'external_sources': {
                source_id: {
                    'name': source.name,
                    'type': source.source_type,
                    'enabled': source.enabled,
                    'success_count': source.success_count,
                    'failure_count': source.failure_count
                }
                for source_id, source in self.external_sources.items()
            }
        }
    
    async def get_agent_capability_report(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """Get detailed capability report for an agent"""
        capability = self.agent_capabilities.get(agent_id)
        if not capability:
            return {'error': 'Agent not found'}
        
        # Get agent's knowledge
        owned_knowledge_details = []
        for knowledge_id in capability.owned_knowledge[:10]:  # Top 10
            knowledge = self.knowledge_base.get(knowledge_id)
            if knowledge:
                owned_knowledge_details.append({
                    'id': knowledge_id,
                    'title': knowledge.title,
                    'type': knowledge.knowledge_type.value,
                    'quality': knowledge.quality_level.value,
                    'usage_count': knowledge.usage_count
                })
        
        return {
            'agent_id': agent_id,
            'role': capability.role.value,
            'skills': capability.skills,
            'specializations': capability.specializations,
            'knowledge_domains': capability.knowledge_domains,
            'programming_languages': capability.programming_languages,
            'frameworks': capability.frameworks,
            'expertise_levels': capability.expertise_level,
            'owned_knowledge_count': len(capability.owned_knowledge),
            'shared_knowledge_count': len(capability.shared_knowledge),
            'top_owned_knowledge': owned_knowledge_details,
            'collaboration_partners': capability.collaboration_history[-10:],
            'availability': capability.availability,
            'current_load': capability.current_load,
            'last_updated': capability.last_updated.isoformat()
        }
    
    async def search_agents_by_expertise(
        self,
        domain: str,
        min_expertise: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Search for agents with expertise in specific domain"""
        matching = []
        
        for agent_id, capability in self.agent_capabilities.items():
            expertise = capability.expertise_level.get(domain, 0.0)
            
            if expertise >= min_expertise:
                matching.append({
                    'agent_id': agent_id,
                    'role': capability.role.value,
                    'expertise_level': expertise,
                    'specializations': capability.specializations,
                    'availability': capability.availability
                })
        
        # Sort by expertise level
        matching.sort(key=lambda x: x['expertise_level'], reverse=True)
        
        return matching
    
    async def get_knowledge_flow_statistics(self) -> Dict[str, Any]:
        """Get statistics about knowledge flow between agents"""
        # Analyze knowledge flows
        flows_by_agent = defaultdict(lambda: {'sent': 0, 'received': 0})
        flows_by_type = defaultdict(int)
        
        for flow in self.knowledge_flows:
            flows_by_agent[flow.source_agent]['sent'] += 1
            flows_by_agent[flow.target_agent]['received'] += 1
            
            knowledge = self.knowledge_base.get(flow.knowledge_id)
            if knowledge:
                flows_by_type[knowledge.knowledge_type.value] += 1
        
        # Top contributors
        top_contributors = sorted(
            [
                {'agent_id': agent_id, 'sent': data['sent']}
                for agent_id, data in flows_by_agent.items()
            ],
            key=lambda x: x['sent'],
            reverse=True
        )[:10]
        
        # Top consumers
        top_consumers = sorted(
            [
                {'agent_id': agent_id, 'received': data['received']}
                for agent_id, data in flows_by_agent.items()
            ],
            key=lambda x: x['received'],
            reverse=True
        )[:10]
        
        return {
            'total_flows': len(self.knowledge_flows),
            'flows_by_type': dict(flows_by_type),
            'top_contributors': top_contributors,
            'top_consumers': top_consumers,
            'active_agents_in_flow': len(flows_by_agent)
        }
    
    async def get_external_sources_status(self) -> Dict[str, Any]:
        """Get status of all external sources"""
        sources_status = {}
        
        for source_id, source in self.external_sources.items():
            total = source.success_count + source.failure_count
            success_rate = source.success_count / total if total > 0 else 0.0
            
            sources_status[source_id] = {
                'name': source.name,
                'type': source.source_type,
                'endpoint': source.endpoint,
                'enabled': source.enabled,
                'success_count': source.success_count,
                'failure_count': source.failure_count,
                'success_rate': success_rate,
                'last_used': source.last_used.isoformat() if source.last_used else None,
                'rate_limit': source.rate_limit
            }
        
        return {
            'total_sources': len(self.external_sources),
            'enabled_sources': len([s for s in self.external_sources.values() if s.enabled]),
            'sources': sources_status
        }
    
    async def export_full_knowledge_catalog(self) -> Dict[str, Any]:
        """Export complete knowledge catalog for Agent Manager"""
        catalog = []
        
        for knowledge in self.knowledge_base.values():
            # Get owner capability
            owner = self.agent_capabilities.get(knowledge.source_agent_id)
            
            catalog.append({
                'knowledge_id': knowledge.knowledge_id,
                'type': knowledge.knowledge_type.value,
                'source': knowledge.source.value,
                'title': knowledge.title,
                'description': knowledge.description,
                'tags': knowledge.tags,
                'applicable_roles': [r.value for r in knowledge.applicable_roles],
                'quality_level': knowledge.quality_level.value,
                'confidence_score': knowledge.confidence_score,
                'usage_count': knowledge.usage_count,
                'success_count': knowledge.success_count,
                'failure_count': knowledge.failure_count,
                'success_rate': knowledge.success_rate,
                'source_agent': {
                    'agent_id': knowledge.source_agent_id,
                    'role': owner.role.value if owner else 'unknown'
                },
                'created_at': knowledge.created_at.isoformat(),
                'updated_at': knowledge.updated_at.isoformat(),
                'last_used_at': knowledge.last_used_at.isoformat() if knowledge.last_used_at else None
            })
        
        return {
            'total_items': len(catalog),
            'exported_at': datetime.utcnow().isoformat(),
            'catalog': catalog
        }
    
    async def shutdown(self):
        """Enhanced shutdown with final log"""
        self.logger.info("Shutting down Enhanced Learning Agent")
        
        # Generate and send final log
        final_log = await self.generate_collective_knowledge_log()
        await self.send_log_to_agent_manager(final_log, reason="shutdown")
        
        # Call parent shutdown
        await super().shutdown()
        
        self.logger.info("Enhanced Learning Agent shutdown complete")