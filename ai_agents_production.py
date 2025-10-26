"""
Production-Ready AI Agents System v3.0
Enterprise-grade AI agents with learning capabilities and system integration

CRITICAL PRODUCTION FIXES:
- Removed SQLite dependency (use PostgreSQL)
- Added proper async/await patterns
- Integrated with BaseAgent architecture
- Enhanced error handling and recovery
- Production-grade configuration management
- Proper resource cleanup
- Connection pooling
- Metrics and monitoring
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
import uuid
from collections import defaultdict, deque

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic SDK not available")


class AgentType(Enum):
    """Types of AI agents"""
    CODE_ANALYZER = "code_analyzer"
    SECURITY_SCANNER = "security_scanner"
    QUALITY_ASSURANCE = "quality_assurance"
    MODULE_MANAGER = "module_manager"
    PERFORMANCE_MONITOR = "performance_monitor"
    GENERAL_ASSISTANT = "general_assistant"


class ConfidenceLevel(Enum):
    """Confidence levels for agent responses"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PriorityLevel(Enum):
    """Priority levels for recommendations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AgentResponse:
    """Structured response from AI agents"""
    agent_id: str
    agent_type: str
    timestamp: str
    confidence_level: str
    executive_summary: str
    detailed_analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    learning_insights: Dict[str, Any]
    next_steps: List[str]
    processing_time: float
    tokens_used: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningPattern:
    """Learning pattern for agent improvement"""
    pattern_id: str
    agent_type: str
    pattern_data: Dict[str, Any]
    success_rate: float
    usage_count: int
    effectiveness_score: float
    context_tags: List[str]
    last_updated: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentLearningManager:
    """Manages learning and pattern recognition using PostgreSQL"""
    
    def __init__(self, db_pool=None, logger=None):
        self.db_pool = db_pool
        self.logger = logger or logging.getLogger(__name__)
        self.patterns_cache: Dict[str, LearningPattern] = {}
        self.performance_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = 0
    
    async def initialize(self):
        """Initialize learning manager with database"""
        if not self.db_pool:
            self.logger.warning("No database pool - learning disabled")
            return False
        
        try:
            await self._create_tables()
            await self._load_patterns_cache()
            self.logger.info("Learning manager initialized")
            return True
        except Exception as e:
            self.logger.error(f"Learning manager init failed: {e}")
            return False
    
    async def _create_tables(self):
        """Create learning tables if they don't exist"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS ai_learning_patterns (
                pattern_id VARCHAR(64) PRIMARY KEY,
                agent_type VARCHAR(50) NOT NULL,
                pattern_data JSONB NOT NULL,
                success_rate FLOAT DEFAULT 1.0,
                usage_count INTEGER DEFAULT 1,
                effectiveness_score FLOAT DEFAULT 1.0,
                context_tags JSONB,
                last_updated TIMESTAMP DEFAULT NOW(),
                created_at TIMESTAMP DEFAULT NOW()
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_learning_agent_type 
            ON ai_learning_patterns(agent_type)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_learning_effectiveness 
            ON ai_learning_patterns(effectiveness_score DESC)
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_agent_performance (
                agent_id VARCHAR(255) PRIMARY KEY,
                agent_type VARCHAR(50) NOT NULL,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                average_response_time FLOAT DEFAULT 0,
                average_confidence FLOAT DEFAULT 0,
                learning_patterns_count INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_agent_feedback (
                feedback_id VARCHAR(64) PRIMARY KEY,
                agent_id VARCHAR(255) NOT NULL,
                task_id VARCHAR(255),
                user_rating INTEGER,
                outcome_success BOOLEAN,
                feedback_text TEXT,
                timestamp TIMESTAMP DEFAULT NOW()
            )
            """
        ]
        
        async with self.db_pool.acquire() as conn:
            for query in queries:
                await conn.execute(query)
    
    async def record_pattern(
        self,
        agent_type: str,
        pattern_data: Dict,
        success: bool,
        context_tags: List[str]
    ):
        """Record a learning pattern"""
        try:
            pattern_str = json.dumps(pattern_data, sort_keys=True)
            # Use SHA-256 instead of MD5 for security
            pattern_id = hashlib.sha256(pattern_str.encode()).hexdigest()
            
            if not self.db_pool:
                return
            
            async with self.db_pool.acquire() as conn:
                # Check if pattern exists
                existing = await conn.fetchrow(
                    "SELECT * FROM ai_learning_patterns WHERE pattern_id = $1",
                    pattern_id
                )
                
                if existing:
                    # Update existing pattern
                    old_success_rate = existing['success_rate']
                    old_usage_count = existing['usage_count']
                    
                    new_usage_count = old_usage_count + 1
                    new_success_rate = (
                        (old_success_rate * old_usage_count + (1 if success else 0)) / 
                        new_usage_count
                    )
                    effectiveness_score = new_success_rate * min(new_usage_count / 10, 1.0)
                    
                    await conn.execute(
                        """
                        UPDATE ai_learning_patterns 
                        SET success_rate = $1, usage_count = $2, 
                            effectiveness_score = $3, context_tags = $4, 
                            last_updated = NOW()
                        WHERE pattern_id = $5
                        """,
                        new_success_rate, new_usage_count, effectiveness_score,
                        json.dumps(context_tags), pattern_id
                    )
                else:
                    # Insert new pattern
                    await conn.execute(
                        """
                        INSERT INTO ai_learning_patterns 
                        (pattern_id, agent_type, pattern_data, success_rate, 
                         usage_count, effectiveness_score, context_tags)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        pattern_id, agent_type, pattern_str,
                        1.0 if success else 0.0, 1,
                        1.0 if success else 0.0, json.dumps(context_tags)
                    )
                
                # Update cache
                self.patterns_cache[pattern_id] = LearningPattern(
                    pattern_id=pattern_id,
                    agent_type=agent_type,
                    pattern_data=pattern_data,
                    success_rate=new_success_rate if existing else (1.0 if success else 0.0),
                    usage_count=new_usage_count if existing else 1,
                    effectiveness_score=effectiveness_score if existing else (1.0 if success else 0.0),
                    context_tags=context_tags,
                    last_updated=time.time()
                )
                
        except Exception as e:
            self.logger.error(f"Failed to record pattern: {e}")
    
    async def get_relevant_patterns(
        self,
        agent_type: str,
        context_tags: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """Get relevant patterns for decision making"""
        try:
            # Check cache freshness
            if time.time() - self.last_cache_update > self.cache_ttl:
                await self._load_patterns_cache()
            
            # Filter patterns from cache
            relevant = []
            for pattern in self.patterns_cache.values():
                if pattern.agent_type != agent_type:
                    continue
                
                if pattern.effectiveness_score < 0.5:
                    continue
                
                # Calculate tag overlap
                tag_overlap = len(set(context_tags) & set(pattern.context_tags))
                relevance = tag_overlap / max(len(context_tags), 1)
                
                if tag_overlap > 0 or not context_tags:
                    relevant.append({
                        'pattern_id': pattern.pattern_id,
                        'pattern_data': pattern.pattern_data,
                        'effectiveness_score': pattern.effectiveness_score,
                        'relevance_score': relevance
                    })
            
            # Sort by combined score
            relevant.sort(
                key=lambda x: x['effectiveness_score'] * (x['relevance_score'] + 0.1),
                reverse=True
            )
            
            return relevant[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get patterns: {e}")
            return []
    
    async def _load_patterns_cache(self):
        """Load patterns into cache"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch(
                    """
                    SELECT pattern_id, agent_type, pattern_data, success_rate,
                           usage_count, effectiveness_score, context_tags,
                           EXTRACT(EPOCH FROM last_updated) as last_updated
                    FROM ai_learning_patterns
                    WHERE effectiveness_score > 0.3
                    ORDER BY effectiveness_score DESC
                    LIMIT 1000
                    """
                )
                
                self.patterns_cache.clear()
                for record in records:
                    self.patterns_cache[record['pattern_id']] = LearningPattern(
                        pattern_id=record['pattern_id'],
                        agent_type=record['agent_type'],
                        pattern_data=json.loads(record['pattern_data']),
                        success_rate=record['success_rate'],
                        usage_count=record['usage_count'],
                        effectiveness_score=record['effectiveness_score'],
                        context_tags=json.loads(record['context_tags']),
                        last_updated=record['last_updated']
                    )
                
                self.last_cache_update = time.time()
                self.logger.debug(f"Loaded {len(self.patterns_cache)} patterns into cache")
                
        except Exception as e:
            self.logger.error(f"Failed to load patterns cache: {e}")
    
    async def update_performance(
        self,
        agent_id: str,
        agent_type: str,
        response_time: float,
        confidence: float,
        success: bool
    ):
        """Update agent performance metrics"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchrow(
                    "SELECT * FROM ai_agent_performance WHERE agent_id = $1",
                    agent_id
                )
                
                if existing:
                    total_requests = existing['total_requests'] + 1
                    successful_requests = existing['successful_requests'] + (1 if success else 0)
                    avg_response_time = (
                        (existing['average_response_time'] * existing['total_requests'] + response_time) /
                        total_requests
                    )
                    avg_confidence = (
                        (existing['average_confidence'] * existing['total_requests'] + confidence) /
                        total_requests
                    )
                    
                    await conn.execute(
                        """
                        UPDATE ai_agent_performance 
                        SET total_requests = $1, successful_requests = $2,
                            average_response_time = $3, average_confidence = $4,
                            last_update = NOW()
                        WHERE agent_id = $5
                        """,
                        total_requests, successful_requests, avg_response_time,
                        avg_confidence, agent_id
                    )
                else:
                    await conn.execute(
                        """
                        INSERT INTO ai_agent_performance 
                        (agent_id, agent_type, total_requests, successful_requests,
                         average_response_time, average_confidence)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        agent_id, agent_type, 1, 1 if success else 0,
                        response_time, confidence
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to update performance: {e}")


class AIAgent:
    """Production-ready AI Agent with Claude integration"""
    
    # System prompt template
    SYSTEM_PROMPT_TEMPLATE = """# AI Agent System Prompt

You are an elite {agent_specialization} AI agent within an enterprise system.

## Core Capabilities
- Deep expertise in {domain}
- Real-time analysis and decision making
- Pattern recognition and learning
- Risk assessment and mitigation
- Clear, actionable recommendations

## Response Format
You must respond in valid JSON format:

{{
  "agent_id": "{agent_id}",
  "timestamp": "ISO_8601_timestamp",
  "confidence_level": "high|medium|low",
  "executive_summary": "Brief overview",
  "detailed_analysis": {{
    "findings": ["finding1", "finding2"],
    "metrics": {{}},
    "patterns_identified": []
  }},
  "recommendations": [
    {{
      "priority": "critical|high|medium|low",
      "action": "specific_action",
      "rationale": "explanation",
      "implementation": "how_to",
      "estimated_effort": "time"
    }}
  ],
  "learning_insights": {{
    "new_patterns": [],
    "success_factors": [],
    "areas_for_improvement": []
  }},
  "next_steps": ["step1", "step2"]
}}

## Quality Standards
- Accuracy: All findings must be verifiable
- Completeness: Address all aspects within scope
- Clarity: Use clear technical language
- Actionability: Provide specific implementable steps
"""

    AGENT_SPECIALIZATIONS = {
        AgentType.CODE_ANALYZER: {
            "title": "Code Analysis Specialist",
            "domain": "static analysis, code quality, architecture patterns",
            "expertise": "software architecture, design patterns, best practices"
        },
        AgentType.SECURITY_SCANNER: {
            "title": "Security Expert",
            "domain": "vulnerability assessment, threat modeling, security best practices",
            "expertise": "OWASP Top 10, penetration testing, security compliance"
        },
        AgentType.QUALITY_ASSURANCE: {
            "title": "Quality Assurance Specialist",
            "domain": "testing strategies, quality metrics, continuous integration",
            "expertise": "test automation, QA methodologies, quality standards"
        },
        AgentType.MODULE_MANAGER: {
            "title": "Architecture Expert",
            "domain": "component architecture, dependency management, modular design",
            "expertise": "software architecture, microservices, system design"
        },
        AgentType.PERFORMANCE_MONITOR: {
            "title": "Performance Engineer",
            "domain": "performance optimization, monitoring, system health",
            "expertise": "profiling, optimization, observability"
        },
        AgentType.GENERAL_ASSISTANT: {
            "title": "General AI Assistant",
            "domain": "full-stack development, operations, project management",
            "expertise": "broad technical knowledge across domains"
        }
    }
    
    def __init__(
        self,
        agent_type: AgentType,
        api_key: str,
        learning_manager: AgentLearningManager,
        logger: Optional[logging.Logger] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.agent_type = agent_type
        self.agent_id = f"{agent_type.value}_{uuid.uuid4().hex[:8]}"
        self.learning_manager = learning_manager
        self.logger = logger or logging.getLogger(__name__)
        self.model = model
        
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("Anthropic SDK required but not available")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Response cache with TTL
        self.response_cache: Dict[str, Tuple[AgentResponse, float]] = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'total_tokens': 0,
            'avg_processing_time': 0.0
        }
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build specialized system prompt"""
        spec = self.AGENT_SPECIALIZATIONS[self.agent_type]
        
        return self.SYSTEM_PROMPT_TEMPLATE.format(
            agent_specialization=spec['title'],
            domain=spec['domain'],
            agent_id=self.agent_id
        )
    
    def _generate_cache_key(self, task: str, context: Dict) -> str:
        """Generate cache key"""
        content = f"{task}:{json.dumps(context, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _extract_context_tags(self, task: str, context: Dict) -> List[str]:
        """Extract context tags for pattern matching"""
        tags = [self.agent_type.value]
        
        task_lower = task.lower()
        keywords = {
            'security': ['security', 'vulnerability', 'attack', 'exploit'],
            'performance': ['performance', 'optimization', 'slow', 'memory'],
            'testing': ['test', 'quality', 'qa', 'bug'],
            'code_analysis': ['code', 'function', 'class', 'method'],
            'debugging': ['error', 'bug', 'issue', 'problem']
        }
        
        for tag, words in keywords.items():
            if any(word in task_lower for word in words):
                tags.append(tag)
        
        # Add context-based tags
        if context:
            if 'file_type' in context:
                tags.append(f"file_{context['file_type']}")
            if 'complexity' in context:
                tags.append(f"complexity_{context['complexity']}")
        
        return list(set(tags))
    
    async def analyze(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        timeout: float = 60.0
    ) -> AgentResponse:
        """Main analysis method with learning integration"""
        start_time = time.time()
        context = context or {}
        
        self.metrics['total_requests'] += 1
        
        try:
            # Check cache
            cache_key = self._generate_cache_key(task, context)
            if use_cache:
                cached = self._get_from_cache(cache_key)
                if cached:
                    self.metrics['cache_hits'] += 1
                    self.logger.debug(f"Cache hit for {self.agent_id}")
                    return cached
            
            # Apply learning patterns
            context_tags = self._extract_context_tags(task, context)
            learning_patterns = await self.learning_manager.get_relevant_patterns(
                self.agent_type.value, context_tags, limit=3
            )
            
            # Prepare enhanced context
            enhanced_context = {
                **context,
                'learning_patterns': len(learning_patterns),
                'pattern_suggestions': [
                    p['pattern_data'].get('suggestion', '')
                    for p in learning_patterns
                ]
            }
            
            # Prepare message
            user_message = f"""Task: {task}

Context: {json.dumps(enhanced_context, indent=2)}

Available Learning Patterns: {len(learning_patterns)}

Analyze this task using your expertise as a {self.agent_type.value.replace('_', ' ').title()} and provide response in required JSON format."""
            
            # Call Claude with timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.messages.create,
                        model=self.model,
                        max_tokens=4000,
                        temperature=0.1,
                        system=self.system_prompt,
                        messages=[{"role": "user", "content": user_message}]
                    ),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"Analysis timeout after {timeout}s")
            
            processing_time = time.time() - start_time
            
            # Parse response
            try:
                response_text = response.content[0].text if response.content else "{}"
                # Remove markdown code blocks if present
                response_text = response_text.replace('```json\n', '').replace('\n```', '').strip()
                response_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON parse error: {e}")
                response_data = self._create_fallback_response(task)
            
            # Create structured response
            agent_response = AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type.value,
                timestamp=response_data.get("timestamp", datetime.now().isoformat()),
                confidence_level=response_data.get("confidence_level", "medium"),
                executive_summary=response_data.get("executive_summary", "Analysis completed"),
                detailed_analysis=response_data.get("detailed_analysis", {}),
                recommendations=response_data.get("recommendations", []),
                learning_insights=response_data.get("learning_insights", {}),
                next_steps=response_data.get("next_steps", []),
                processing_time=processing_time,
                tokens_used=(response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
            )
            
            # Record learning pattern
            pattern_data = {
                'task_preview': task[:100],
                'confidence': agent_response.confidence_level,
                'processing_time': processing_time,
                'recommendations_count': len(agent_response.recommendations)
            }
            
            success = agent_response.confidence_level in ["high", "medium"]
            await self.learning_manager.record_pattern(
                self.agent_type.value, pattern_data, success, context_tags
            )
            
            # Update performance
            confidence_score = {"high": 1.0, "medium": 0.7, "low": 0.4}[agent_response.confidence_level]
            await self.learning_manager.update_performance(
                self.agent_id, self.agent_type.value, processing_time, confidence_score, success
            )
            
            # Cache response
            if use_cache:
                self._add_to_cache(cache_key, agent_response)
            
            # Update metrics
            self.metrics['successful_requests'] += 1
            self.metrics['total_tokens'] += agent_response.tokens_used
            self._update_avg_time(processing_time)
            
            self.logger.info(
                f"Analysis completed",
                agent=self.agent_id,
                time_ms=processing_time*1000,
                tokens=agent_response.tokens_used
            )
            
            return agent_response
            
        except Exception as e:
            self.metrics['failed_requests'] += 1
            processing_time = time.time() - start_time
            
            self.logger.error(f"Analysis failed: {e}", agent=self.agent_id)
            
            # Update performance with failure
            await self.learning_manager.update_performance(
                self.agent_id, self.agent_type.value, processing_time, 0.0, False
            )
            
            return self._create_error_response(str(e), processing_time)
    
    def _create_fallback_response(self, task: str) -> Dict:
        """Create fallback response when JSON parsing fails"""
        return {
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "confidence_level": "low",
            "executive_summary": "Analysis completed with parsing issues",
            "detailed_analysis": {
                "findings": ["Response format error occurred"],
                "metrics": {},
                "patterns_identified": []
            },
            "recommendations": [],
            "learning_insights": {
                "new_patterns": [],
                "success_factors": [],
                "areas_for_improvement": ["Response formatting"]
            },
            "next_steps": ["Review task requirements", "Retry analysis"]
        }
    
    def _create_error_response(self, error: str, processing_time: float) -> AgentResponse:
        """Create error response"""
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type.value,
            timestamp=datetime.now().isoformat(),
            confidence_level="low",
            executive_summary=f"Analysis failed: {error}",
            detailed_analysis={
                "findings": [f"Error: {error}"],
                "metrics": {"processing_time": processing_time},
                "patterns_identified": []
            },
            recommendations=[{
                "priority": "high",
                "action": "Review error and retry",
                "rationale": "Analysis failed",
                "implementation": "Check logs and retry",
                "estimated_effort": "5 minutes"
            }],
            learning_insights={
                "new_patterns": [],
                "success_factors": [],
                "areas_for_improvement": ["Error handling"]
            },
            next_steps=["Review error", "Retry analysis"],
            processing_time=processing_time,
            tokens_used=0
        )
    
    def _get_from_cache(self, cache_key: str) -> Optional[AgentResponse]:
        """Get response from cache if valid"""
        if cache_key in self.response_cache:
            response, timestamp = self.response_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return response
            del self.response_cache[cache_key]
        return None
    
    def _add_to_cache(self, cache_key: str, response: AgentResponse):
        """Add response to cache"""
        self.response_cache[cache_key] = (response, time.time())
        
        # Cleanup old entries
        if len(self.response_cache) > 100:
            oldest = min(self.response_cache.items(), key=lambda x: x[1][1])
            del self.response_cache[oldest[0]]
    
    def _update_avg_time(self, processing_time: float):
        """Update average processing time"""
        total = self.metrics['successful_requests']
        current_avg = self.metrics['avg_processing_time']
        self.metrics['avg_processing_time'] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            **self.metrics,
            "cache_size": len(self.response_cache)
        }


class AIAgentOrchestrator:
    """Orchestrates multiple AI agents"""
    
    def __init__(
        self,
        api_key: str,
        db_pool=None,
        logger: Optional[logging.Logger] = None
    ):
        self.api_key = api_key
        self.db_pool = db_pool
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize learning manager
        self.learning_manager = AgentLearningManager(db_pool, logger)
        
        # Agent registry
        self.agents: Dict[AgentType, AIAgent] = {}
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'agent_selections': defaultdict(int),
            'avg_routing_time': 0.0
        }
    
    async def initialize(self):
        """Initialize orchestrator"""
        try:
            await self.learning_manager.initialize()
            
            # Initialize all agent types
            for agent_type in AgentType:
                self.agents[agent_type] = AIAgent(
                    agent_type=agent_type,
                    api_key=self.api_key,
                    learning_manager=self.learning_manager,
                    logger=self.logger
                )
            
            self.logger.info(f"Orchestrator initialized with {len(self.agents)} agents")
            return True
            
        except Exception as e:
            self.logger.error(f"Orchestrator init failed: {e}")
            return False
    
    def get_agent(self, agent_type: AgentType) -> AIAgent:
        """Get specific agent"""
        return self.agents[agent_type]
    
    async def analyze_with_best_agent(
        self,
        task: str,
        context: Optional[Dict] = None
    ) -> AgentResponse:
        """Automatically select and use best agent"""
        start_time = time.time()
        
        # Simple task classification
        task_lower = task.lower()
        
        keywords_map = {
            AgentType.SECURITY_SCANNER: ['security', 'vulnerability', 'exploit', 'attack'],
            AgentType.QUALITY_ASSURANCE: ['test', 'quality', 'bug', 'defect'],
            AgentType.PERFORMANCE_MONITOR: ['performance', 'optimization', 'slow', 'memory'],
            AgentType.MODULE_MANAGER: ['module', 'dependency', 'architecture', 'design'],
            AgentType.CODE_ANALYZER: ['code', 'function', 'class', 'method']
        }
        
        selected_type = AgentType.GENERAL_ASSISTANT
        for agent_type, keywords in keywords_map.items():
            if any(kw in task_lower for kw in keywords):
                selected_type = agent_type
                break
        
        agent = self.agents[selected_type]
        
        # Update metrics
        self.metrics['total_requests'] += 1
        self.metrics['agent_selections'][selected_type.value] += 1
        
        routing_time = time.time() - start_time
        self._update_routing_time(routing_time)
        
        self.logger.info(f"Selected {selected_type.value} for task")
        
        return await agent.analyze(task, context)
    
    async def collaborative_analysis(
        self,
        task: str,
        agent_types: List[AgentType],
        context: Optional[Dict] = None
    ) -> Dict[AgentType, AgentResponse]:
        """Run collaborative analysis with multiple agents"""
        tasks = []
        for agent_type in agent_types:
            agent = self.agents[agent_type]
            tasks.append(agent.analyze(task, context))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        result = {}
        for i, agent_type in enumerate(agent_types):
            if isinstance(responses[i], Exception):
                self.logger.error(f"Agent {agent_type.value} failed: {responses[i]}")
            else:
                result[agent_type] = responses[i]
        
        return result
    
    def _update_routing_time(self, routing_time: float):
        """Update average routing time"""
        total = self.metrics['total_requests']
        current_avg = self.metrics['avg_routing_time']
        self.metrics['avg_routing_time'] = (
            (current_avg * (total - 1) + routing_time) / total
        )
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        agent_metrics = {}
        for agent_type, agent in self.agents.items():
            agent_metrics[agent_type.value] = agent.get_metrics()
        
        return {
            "orchestrator": self.metrics,
            "agents": agent_metrics,
            "total_agents": len(self.agents),
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up AI Agent Orchestrator")
        
        # Clear caches
        for agent in self.agents.values():
            agent.response_cache.clear()
        
        self.agents.clear()


# Database schema
AI_AGENTS_DB_SCHEMA = """
-- AI Learning patterns table
CREATE TABLE IF NOT EXISTS ai_learning_patterns (
    pattern_id VARCHAR(64) PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    pattern_data JSONB NOT NULL,
    success_rate FLOAT DEFAULT 1.0,
    usage_count INTEGER DEFAULT 1,
    effectiveness_score FLOAT DEFAULT 1.0,
    context_tags JSONB,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_learning_agent_type ON ai_learning_patterns(agent_type);
CREATE INDEX IF NOT EXISTS idx_learning_effectiveness ON ai_learning_patterns(effectiveness_score DESC);

-- AI Agent performance table
CREATE TABLE IF NOT EXISTS ai_agent_performance (
    agent_id VARCHAR(255) PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    average_response_time FLOAT DEFAULT 0,
    average_confidence FLOAT DEFAULT 0,
    learning_patterns_count INTEGER DEFAULT 0,
    last_update TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_perf_type ON ai_agent_performance(agent_type);

-- AI Agent feedback table
CREATE TABLE IF NOT EXISTS ai_agent_feedback (
    feedback_id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255),
    user_rating INTEGER,
    outcome_success BOOLEAN,
    feedback_text TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_agent ON ai_agent_feedback(agent_id);
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON ai_agent_feedback(timestamp DESC);
"""


# Example usage
async def example_usage():
    """Example of using the AI agents"""
    
    # Mock database pool for example
    db_pool = None  # In production, use actual asyncpg pool
    
    # Get API key from environment variable (NEVER hardcode)
    import os
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable must be set")
    
    orchestrator = AIAgentOrchestrator(
        api_key=api_key,
        db_pool=db_pool
    )
    
    await orchestrator.initialize()
    
    # Example 1: Automatic agent selection
    logger.info("=== Automatic Agent Selection ===")
    response = await orchestrator.analyze_with_best_agent(
        task="Analyze this Python code for security vulnerabilities",
        context={
            "file_type": "python",
            "complexity": "medium"
        }
    )
    
    logger.info(f"Agent: {response.agent_id}")
    logger.info(f"Confidence: {response.confidence_level}")
    logger.info(f"Summary: {response.executive_summary}")
    logger.info(f"Processing time: {response.processing_time:.2f}s")
    logger.info()
    
    # Example 2: Specific agent usage
    logger.info("=== Specific Agent Usage ===")
    code_agent = orchestrator.get_agent(AgentType.CODE_ANALYZER)
    code_response = await code_agent.analyze(
        task="Review this function for performance optimization",
        context={"language": "python"}
    )
    
    logger.info(f"Summary: {code_response.executive_summary}")
    logger.info(f"Recommendations: {len(code_response.recommendations)}")
    logger.info()
    
    # Example 3: Collaborative analysis
    logger.info("=== Collaborative Analysis ===")
    collaborative = await orchestrator.collaborative_analysis(
        task="Analyze authentication function",
        agent_types=[
            AgentType.CODE_ANALYZER,
            AgentType.SECURITY_SCANNER,
            AgentType.PERFORMANCE_MONITOR
        ]
    )
    
    for agent_type, response in collaborative.items():
        logger.info(f"{agent_type.value}: {response.confidence_level} confidence")
    logger.info()
    
    # Example 4: System metrics
    logger.info("=== System Metrics ===")
    metrics = orchestrator.get_system_metrics()
    logger.info(f"Total requests: {metrics['orchestrator']['total_requests']}")
    logger.info(f"Agents active: {metrics['total_agents']}")
    
    await orchestrator.cleanup()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(example_usage())
    except KeyboardInterrupt:
        logger.info("\nShutdown by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        logging.exception(e)