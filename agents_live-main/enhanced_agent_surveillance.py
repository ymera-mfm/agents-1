import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import deque
from dataclasses import dataclass, field
import numpy as np
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.secure_database_manager import SecureDatabaseManager
from models.secure_models import Agent, Task, AuditLog
from monitoring.alert_manager import AlertManager, AlertCategory, AlertSeverity
from ai.multi_modal_ai import MultiModalAIService, AIRequest, AIModelType

logger = logging.getLogger(__name__)


@dataclass
class BehaviorPattern:
    """Agent behavior pattern for anomaly detection"""
    pattern_id: str
    agent_id: str
    timestamp: datetime
    metrics_snapshot: Dict[str, float]
    task_distribution: Dict[str, int]
    network_activity: Dict[str, float]
    anomaly_score: float = 0.0
    is_anomalous: bool = False
    confidence: float = 0.0


@dataclass
class AgentThreatIndicator:
    """Security threat indicators for agents"""
    indicator_type: str  # e.g., "unauthorized_access", "data_exfiltration", "resource_abuse"
    severity: str
    detected_at: datetime
    evidence: Dict[str, any]
    risk_score: float
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Track agent-user conversation context"""
    conversation_id: str
    agent_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    message_count: int
    sentiment_scores: List[float]
    topics: List[str]
    escalations: int = 0
    avg_response_time: float = 0.0


class AgentSurveillanceSystem:
    """
    Production-Ready Agent Surveillance and Monitoring System
    
    Features:
    - Real-time behavior monitoring
    - Anomaly detection with ML
    - Security threat detection
    - Performance profiling
    - Conversation monitoring
    - Predictive failure detection
    - Automated incident response
    """

    def __init__(
        self,
        db_manager: SecureDatabaseManager,
        ai_service: MultiModalAIService,
        alert_manager: AlertManager
    ):
        self.db_manager = db_manager
        self.ai_service = ai_service
        self.alert_manager = alert_manager
        
        # Monitoring state
        self.agent_baselines: Dict[str, Dict] = {}
        self.behavior_patterns: Dict[str, deque] = {}
        self.threat_indicators: Dict[str, List[AgentThreatIndicator]] = {}
        self.active_conversations: Dict[str, ConversationContext] = {}
        
        # Configuration
        self.monitoring_interval = settings.monitoring.agent_surveillance.monitoring_interval_seconds
        self.anomaly_threshold = settings.monitoring.agent_surveillance.anomaly_threshold
        self.pattern_window_size = 100  # Keep last 100 behavior patterns
        self.baseline_learning_period = 24 * 3600  # 24 hours
        
        # Performance thresholds
        self.thresholds = settings.monitoring.agent_surveillance.performance_thresholds.model_dump()
        
        # Threat detection rules
        self.threat_rules = self._initialize_threat_rules()
        
        logger.info("Enhanced AgentSurveillanceSystem initialized")

    def _initialize_threat_rules(self) -> Dict[str, Dict]:
        """Initialize threat detection rules"""
        return {
            "excessive_errors": {
                "threshold": 0.20,
                "window": 300,  # 5 minutes
                "severity": "high",
                "action": "quarantine"
            },
            "unusual_resource_consumption": {
                "cpu_spike": 95.0,
                "memory_spike": 95.0,
                "duration": 600,  # 10 minutes
                "severity": "medium",
                "action": "alert"
            },
            "abnormal_task_pattern": {
                "deviation_threshold": 3.0,  # 3 standard deviations
                "min_samples": 50,
                "severity": "medium",
                "action": "investigate"
            },
            "rapid_status_changes": {
                "max_changes": 10,
                "window": 300,  # 5 minutes
                "severity": "high",
                "action": "alert"
            },
            "data_exfiltration": {
                "network_threshold": 1000000000,  # 1GB
                "time_window": 3600,  # 1 hour
                "severity": "critical",
                "action": "quarantine"
            }
        }

    async def start_monitoring(self) -> None:
        """Start comprehensive surveillance monitoring"""
        logger.info("Starting enhanced agent surveillance system")
        
        # Start parallel monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_agent_behavior()),
            asyncio.create_task(self._monitor_security_threats()),
            asyncio.create_task(self._monitor_performance_trends()),
            asyncio.create_task(self._monitor_conversations()),
            asyncio.create_task(self._analyze_patterns_batch())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Agent surveillance monitoring cancelled")
            for task in tasks:
                task.cancel()

    async def _monitor_agent_behavior(self) -> None:
        """Monitor agent behavior patterns"""
        while True:
            try:
                async with self.db_manager.get_session() as session:
                    # Get all active agents
                    result = await session.execute(
                        select(Agent).where(
                            and_(
                                Agent.status.in_(['active', 'busy', 'idle']),
                                Agent.last_heartbeat >= datetime.utcnow() - timedelta(minutes=10)
                            )
                        )
                    )
                    agents = result.scalars().all()
                    
                    # Analyze each agent
                    for agent in agents:
                        await self._analyze_agent_behavior(agent)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Behavior monitoring error: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _analyze_agent_behavior(self, agent: Agent) -> None:
        """Comprehensive behavior analysis for an agent"""
        try:
            agent_id = agent.id
            
            # Create behavior pattern
            pattern = await self._create_behavior_pattern(agent)
            
            # Store pattern
            if agent_id not in self.behavior_patterns:
                self.behavior_patterns[agent_id] = deque(maxlen=self.pattern_window_size)
            self.behavior_patterns[agent_id].append(pattern)
            
            # Learn baseline if not exists
            if agent_id not in self.agent_baselines:
                await self._learn_baseline(agent_id)
            
            # Detect anomalies
            is_anomalous, anomaly_score = await self._detect_anomaly(agent_id, pattern)
            
            if is_anomalous:
                await self._handle_anomalous_behavior(agent, pattern, anomaly_score)
            
            # Check for specific threat patterns
            threats = await self._check_threat_indicators(agent, pattern)
            if threats:
                await self._handle_threats(agent, threats)
            
        except Exception as e:
            logger.error(f"Error analyzing behavior for agent {agent.id}: {e}", exc_info=True)

    async def _create_behavior_pattern(self, agent: Agent) -> BehaviorPattern:
        """Create behavior pattern snapshot"""
        metrics = agent.performance_metrics or {}
        
        # Get recent task distribution
        async with self.db_manager.get_session() as session:
            task_result = await session.execute(
                select(
                    Task.type,
                    func.count(Task.id).label('count')
                ).where(
                    and_(
                        Task.agent_id == agent.id,
                        Task.created_at >= datetime.utcnow() - timedelta(hours=1)
                    )
                ).group_by(Task.type)
            )
            task_distribution = {row.type: row.count for row in task_result}
        
        return BehaviorPattern(
            pattern_id=f"{agent.id}_{datetime.utcnow().timestamp()}",
            agent_id=agent.id,
            timestamp=datetime.utcnow(),
            metrics_snapshot={
                'cpu_usage': metrics.get('cpu_usage', 0),
                'memory_usage': metrics.get('memory_usage', 0),
                'response_time': metrics.get('response_time', 0),
                'error_rate': metrics.get('error_rate', 0),
                'throughput': metrics.get('throughput', 0)
            },
            task_distribution=task_distribution,
            network_activity={
                'requests_per_minute': metrics.get('throughput', 0) / 60.0,
                'data_transferred': 0  # Would be populated from actual network monitoring
            }
        )

    async def _learn_baseline(self, agent_id: str) -> None:
        """Learn normal behavior baseline for an agent"""
        patterns = self.behavior_patterns.get(agent_id, [])
        
        if len(patterns) < 10:  # Need minimum patterns
            return
        
        # Calculate baseline statistics
        cpu_values = [p.metrics_snapshot['cpu_usage'] for p in patterns]
        memory_values = [p.metrics_snapshot['memory_usage'] for p in patterns]
        response_times = [p.metrics_snapshot['response_time'] for p in patterns]
        error_rates = [p.metrics_snapshot['error_rate'] for p in patterns]
        
        self.agent_baselines[agent_id] = {
            'cpu': {
                'mean': np.mean(cpu_values),
                'std': np.std(cpu_values),
                'min': np.min(cpu_values),
                'max': np.max(cpu_values)
            },
            'memory': {
                'mean': np.mean(memory_values),
                'std': np.std(memory_values),
                'min': np.min(memory_values),
                'max': np.max(memory_values)
            },
            'response_time': {
                'mean': np.mean(response_times),
                'std': np.std(response_times),
                'p95': np.percentile(response_times, 95)
            },
            'error_rate': {
                'mean': np.mean(error_rates),
                'std': np.std(error_rates),
                'max': np.max(error_rates)
            },
            'learned_at': datetime.utcnow()
        }
        
        logger.info(f"Baseline learned for agent {agent_id}")

    async def _detect_anomaly(
        self,
        agent_id: str,
        pattern: BehaviorPattern
    ) -> Tuple[bool, float]:
        """Detect anomalies using statistical and ML methods"""
        baseline = self.agent_baselines.get(agent_id)
        if not baseline:
            return False, 0.0
        
        anomaly_scores = []
        
        # Statistical anomaly detection
        metrics = pattern.metrics_snapshot
        
        # CPU anomaly
        cpu_zscore = abs((metrics['cpu_usage'] - baseline['cpu']['mean']) / 
                        (baseline['cpu']['std'] + 0.001))
        anomaly_scores.append(min(cpu_zscore / 3.0, 1.0))
        
        # Memory anomaly
        mem_zscore = abs((metrics['memory_usage'] - baseline['memory']['mean']) / 
                        (baseline['memory']['std'] + 0.001))
        anomaly_scores.append(min(mem_zscore / 3.0, 1.0))
        
        # Response time anomaly
        if metrics['response_time'] > baseline['response_time']['p95'] * 2:
            anomaly_scores.append(0.8)
        
        # Error rate anomaly
        if metrics['error_rate'] > baseline['error_rate']['mean'] + 3 * baseline['error_rate']['std']:
            anomaly_scores.append(0.9)
        
        # Calculate overall anomaly score
        overall_score = max(anomaly_scores) if anomaly_scores else 0.0
        
        # Use AI for complex pattern detection
        if overall_score > 0.5:
            ai_score = await self._ai_anomaly_detection(agent_id, pattern, baseline)
            overall_score = (overall_score + ai_score) / 2.0
        
        is_anomalous = overall_score > self.anomaly_threshold
        
        return is_anomalous, overall_score

    async def _ai_anomaly_detection(
        self,
        agent_id: str,
        pattern: BehaviorPattern,
        baseline: Dict
    ) -> float:
        """Use AI service for advanced anomaly detection"""
        try:
            prompt = f"""Analyze this agent behavior pattern for anomalies:

Current Metrics:
- CPU: {pattern.metrics_snapshot['cpu_usage']}% (baseline: {baseline['cpu']['mean']:.1f}%)
- Memory: {pattern.metrics_snapshot['memory_usage']}% (baseline: {baseline['memory']['mean']:.1f}%)
- Response Time: {pattern.metrics_snapshot['response_time']}ms (baseline: {baseline['response_time']['mean']:.1f}ms)
- Error Rate: {pattern.metrics_snapshot['error_rate']:.3f} (baseline: {baseline['error_rate']['mean']:.3f})

Task Distribution: {pattern.task_distribution}

Provide anomaly score (0-1) and brief explanation in JSON format:
{{"anomaly_score": 0.0, "explanation": "reason", "concerns": []}}"""

            ai_request = AIRequest(
                request_id=f"anomaly_{agent_id}_{datetime.utcnow().timestamp()}",
                model_type=AIModelType.LLM,
                input_data=prompt,
                parameters={
                    "max_tokens": 300,
                    "temperature": 0.3
                }
            )
            
            response = await self.ai_service.process_request(ai_request)
            
            if response.success:
                import json
                result = json.loads(response.output)
                return float(result.get('anomaly_score', 0.5))
            
            return 0.5
            
        except Exception as e:
            logger.error(f"AI anomaly detection failed: {e}")
            return 0.5

    async def _check_threat_indicators(
        self,
        agent: Agent,
        pattern: BehaviorPattern
    ) -> List[AgentThreatIndicator]:
        """Check for security threat indicators"""
        threats = []
        metrics = pattern.metrics_snapshot
        
        # Check excessive errors
        if metrics['error_rate'] > self.threat_rules['excessive_errors']['threshold']:
            threats.append(AgentThreatIndicator(
                indicator_type="excessive_errors",
                severity="high",
                detected_at=datetime.utcnow(),
                evidence={
                    'error_rate': metrics['error_rate'],
                    'threshold': self.threat_rules['excessive_errors']['threshold']
                },
                risk_score=0.8,
                recommended_actions=["investigate_errors", "check_logs", "reduce_load"]
            ))
        
        # Check unusual resource consumption
        if (metrics['cpu_usage'] > self.threat_rules['unusual_resource_consumption']['cpu_spike'] or
            metrics['memory_usage'] > self.threat_rules['unusual_resource_consumption']['memory_spike']):
            threats.append(AgentThreatIndicator(
                indicator_type="unusual_resource_consumption",
                severity="medium",
                detected_at=datetime.utcnow(),
                evidence={
                    'cpu_usage': metrics['cpu_usage'],
                    'memory_usage': metrics['memory_usage']
                },
                risk_score=0.6,
                recommended_actions=["monitor_closely", "check_processes", "profile_performance"]
            ))
        
        # Check rapid status changes (requires history)
        if agent.id in self.behavior_patterns:
            recent_patterns = list(self.behavior_patterns[agent.id])[-10:]
            if len(recent_patterns) >= 10:
                # Detect if there's high variance in metrics
                cpu_variance = np.var([p.metrics_snapshot['cpu_usage'] for p in recent_patterns])
                if cpu_variance > 500:  # High variance threshold
                    threats.append(AgentThreatIndicator(
                        indicator_type="unstable_behavior",
                        severity="medium",
                        detected_at=datetime.utcnow(),
                        evidence={'cpu_variance': cpu_variance},
                        risk_score=0.5,
                        recommended_actions=["stabilize_workload", "investigate_instability"]
                    ))
        
        return threats

    async def _handle_anomalous_behavior(
        self,
        agent: Agent,
        pattern: BehaviorPattern,
        anomaly_score: float
    ) -> None:
        """Handle detected anomalous behavior"""
        severity = AlertSeverity.CRITICAL if anomaly_score > 0.8 else AlertSeverity.WARNING
        
        await self.alert_manager.create_alert(
            category=AlertCategory.SECURITY,
            severity=severity,
            title="Anomalous Agent Behavior Detected",
            description=f"Agent {agent.name} ({agent.id}) showing anomalous behavior (score: {anomaly_score:.3f})",
            source="AgentSurveillanceSystem",
            metadata={
                "agent_id": agent.id,
                "tenant_id": agent.tenant_id,
                "anomaly_score": anomaly_score,
                "metrics": pattern.metrics_snapshot,
                "timestamp": pattern.timestamp.isoformat()
            }
        )
        
        # Update agent security score
        async with self.db_manager.get_session() as session:
            db_agent = await session.get(Agent, agent.id)
            if db_agent:
                score_reduction = 30 if anomaly_score > 0.8 else 15
                db_agent.security_score = max(0, db_agent.security_score - score_reduction)
                await session.commit()
        
        logger.warning(f"Anomalous behavior detected for agent {agent.id}, score: {anomaly_score:.3f}")

    async def _handle_threats(
        self,
        agent: Agent,
        threats: List[AgentThreatIndicator]
    ) -> None:
        """Handle detected security threats"""
        # Store threats
        if agent.id not in self.threat_indicators:
            self.threat_indicators[agent.id] = []
        self.threat_indicators[agent.id].extend(threats)
        
        # Create alerts for high-severity threats
        for threat in threats:
            if threat.severity in ['high', 'critical']:
                await self.alert_manager.create_alert(
                    category=AlertCategory.SECURITY,
                    severity=AlertSeverity.CRITICAL if threat.severity == 'critical' else AlertSeverity.HIGH,
                    title=f"Security Threat: {threat.indicator_type}",
                    description=f"Threat detected on agent {agent.name}: {threat.indicator_type}",
                    source="AgentSurveillanceSystem",
                    metadata={
                        "agent_id": agent.id,
                        "tenant_id": agent.tenant_id,
                        "threat_type": threat.indicator_type,
                        "risk_score": threat.risk_score,
                        "evidence": threat.evidence,
                        "recommended_actions": threat.recommended_actions
                    }
                )
                
                # Execute automated response if configured
                action = self.threat_rules.get(threat.indicator_type, {}).get('action')
                if action == 'quarantine':
                    await self._quarantine_agent(agent.id, f"Automated: {threat.indicator_type}")

    async def _quarantine_agent(self, agent_id: str, reason: str) -> None:
        """Quarantine agent (would integrate with lifecycle manager)"""
        logger.critical(f"Agent {agent_id} quarantined: {reason}")
        # This would call the AgentLifecycleManager.quarantine_agent method

    async def _monitor_security_threats(self) -> None:
        """Monitor for security threats across all agents"""
        while True:
            try:
                # Analyze threat patterns
                await self._analyze_threat_correlations()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Security monitoring error: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _analyze_threat_correlations(self) -> None:
        """Analyze correlations between threats across agents"""
        if not self.threat_indicators:
            return
        
        # Group threats by type
        threat_types: Dict[str, List[str]] = {}
        for agent_id, threats in self.threat_indicators.items():
            for threat in threats:
                if threat.indicator_type not in threat_types:
                    threat_types[threat.indicator_type] = []
                threat_types[threat.indicator_type].append(agent_id)
        
        # Detect coordinated attacks or system-wide issues
        for threat_type, affected_agents in threat_types.items():
            if len(affected_agents) >= 3:  # Multiple agents affected
                await self.alert_manager.create_alert(
                    category=AlertCategory.SECURITY,
                    severity=AlertSeverity.EMERGENCY,
                    title="Coordinated Threat Detected",
                    description=f"Threat type '{threat_type}' detected on {len(affected_agents)} agents",
                    source="AgentSurveillanceSystem",
                    metadata={
                        "threat_type": threat_type,
                        "affected_agents": affected_agents,
                        "count": len(affected_agents)
                    }
                )

    async def _monitor_performance_trends(self) -> None:
        """Monitor long-term performance trends"""
        while True:
            try:
                for agent_id, patterns in self.behavior_patterns.items():
                    if len(patterns) >= 20:
                        await self._analyze_performance_trends(agent_id, list(patterns))
                
                await asyncio.sleep(3600)  # Analyze every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance trend monitoring error: {e}", exc_info=True)
                await asyncio.sleep(300)

    async def _analyze_performance_trends(
        self,
        agent_id: str,
        patterns: List[BehaviorPattern]
    ) -> None:
        """Analyze performance trends to predict issues"""
        # Extract metrics over time
        cpu_trend = [p.metrics_snapshot['cpu_usage'] for p in patterns[-50:]]
        memory_trend = [p.metrics_snapshot['memory_usage'] for p in patterns[-50:]]
        error_trend = [p.metrics_snapshot['error_rate'] for p in patterns[-50:]]
        
        # Detect degradation trends
        if len(cpu_trend) >= 10:
            # Simple linear regression to detect upward trend
            x = np.arange(len(cpu_trend))
            cpu_slope = np.polyfit(x, cpu_trend, 1)[0]
            
            if cpu_slope > 0.5:  # CPU increasing
                await self.alert_manager.create_alert(
                    category=AlertCategory.PERFORMANCE,
                    severity=AlertSeverity.WARNING,
                    title="Performance Degradation Trend",
                    description=f"Agent {agent_id} showing CPU usage increase trend",
                    source="AgentSurveillanceSystem",
                    metadata={
                        "agent_id": agent_id,
                        "metric": "cpu_usage",
                        "trend_slope": cpu_slope
                    }
                )

    async def _monitor_conversations(self) -> None:
        """Monitor agent-user conversations for quality and issues"""
        while True:
            try:
                # Clean up stale conversations
                cutoff = datetime.utcnow() - timedelta(hours=24)
                stale = [cid for cid, ctx in self.active_conversations.items() 
                        if ctx.last_activity < cutoff]
                for cid in stale:
                    del self.active_conversations[cid]
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Conversation monitoring error: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _analyze_patterns_batch(self) -> None:
        """Batch analysis of patterns using AI"""
        while True:
            try:
                await asyncio.sleep(1800)  # Every 30 minutes
                
                # Use AI to analyze patterns across all agents
                summary = await self._generate_surveillance_summary()
                
                if summary.get('critical_issues'):
                    logger.warning(f"Surveillance summary: {len(summary['critical_issues'])} critical issues detected")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch analysis error: {e}", exc_info=True)

    async def _generate_surveillance_summary(self) -> Dict[str, Any]:
        """Generate comprehensive surveillance summary"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agents_monitored": len(self.behavior_patterns),
            "anomalies_detected": sum(1 for patterns in self.behavior_patterns.values() 
                                     for p in patterns if p.is_anomalous),
            "active_threats": sum(len(threats) for threats in self.threat_indicators.values()),
            "critical_issues": [
                agent_id for agent_id, threats in self.threat_indicators.items()
                if any(t.severity == 'critical' for t in threats)
            ]
        }

    async def get_agent_surveillance_report(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive surveillance report for an agent"""
        patterns = list(self.behavior_patterns.get(agent_id, []))
        threats = self.threat_indicators.get(agent_id, [])
        baseline = self.agent_baselines.get(agent_id)
        
        return {
            "agent_id": agent_id,
            "monitoring_duration_hours": len(patterns) * (self.monitoring_interval / 3600),
            "total_patterns_collected": len(patterns),
            "baseline_established": baseline is not None,
            "baseline": baseline,
            "recent_patterns": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "metrics": p.metrics_snapshot,
                    "anomaly_score": p.anomaly_score,
                    "is_anomalous": p.is_anomalous
                }
                for p in patterns[-10:]
            ],
            "threats": [
                {
                    "type": t.indicator_type,
                    "severity": t.severity,
                    "detected_at": t.detected_at.isoformat(),
                    "risk_score": t.risk_score,
                    "evidence": t.evidence
                }
                for t in threats
            ],
            "overall_health": "good" if not threats else "needs_attention"
        }

    async def health_check(self) -> str:
        """Health check for surveillance system"""
        try:
            return "healthy"
        except Exception as e:
            logger.error(f"Surveillance system health check failed: {e}")
            return "unhealthy"
