import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.secure_database_manager import SecureDatabaseManager
from models.secure_models import Agent
from monitoring.alert_manager import AlertManager, AlertCategory, AlertSeverity
from ai.multi_modal_ai import MultiModalAIService, AIRequest, AIModelType

logger = logging.getLogger(__name__)

class SurveillanceConfig:
    """Configuration for agent surveillance with safe defaults"""
    def __init__(self):
        self.anomaly_threshold = getattr(
            settings.monitoring.agent_surveillance if hasattr(settings.monitoring, 'agent_surveillance') else type('obj', (), {}),
            'anomaly_threshold',
            0.7
        )
        self.monitoring_interval_seconds = getattr(
            settings.monitoring.agent_surveillance if hasattr(settings.monitoring, 'agent_surveillance') else type('obj', (), {}),
            'monitoring_interval_seconds',
            60
        )
        self.stale_agent_timeout_minutes = getattr(
            settings.monitoring.agent_surveillance if hasattr(settings.monitoring, 'agent_surveillance') else type('obj', (), {}),
            'stale_agent_timeout_minutes',
            10
        )
        self.security_score_reduction_critical = getattr(
            settings.monitoring.agent_surveillance if hasattr(settings.monitoring, 'agent_surveillance') else type('obj', (), {}),
            'security_score_reduction_critical',
            30
        )
        self.security_score_reduction_warning = getattr(
            settings.monitoring.agent_surveillance if hasattr(settings.monitoring, 'agent_surveillance') else type('obj', (), {}),
            'security_score_reduction_warning',
            15
        )
        
        # Performance thresholds
        thresholds_obj = getattr(
            settings.monitoring.agent_surveillance if hasattr(settings.monitoring, 'agent_surveillance') else type('obj', (), {}),
            'performance_thresholds',
            type('obj', (), {
                'cpu_usage': 85.0,
                'memory_usage': 85.0,
                'response_time': 1000,  # ms
                'error_rate': 0.05  # 5%
            })()
        )
        
        self.performance_thresholds = {
            'cpu_usage': getattr(thresholds_obj, 'cpu_usage', 85.0),
            'memory_usage': getattr(thresholds_obj, 'memory_usage', 85.0),
            'response_time': getattr(thresholds_obj, 'response_time', 1000),
            'error_rate': getattr(thresholds_obj, 'error_rate', 0.05)
        }
        
        # Behavioral analysis settings
        self.enable_ai_behavior_analysis = getattr(
            settings.monitoring.agent_surveillance if hasattr(settings.monitoring, 'agent_surveillance') else type('obj', (), {}),
            'enable_ai_behavior_analysis',
            True
        )
        self.max_concurrent_analyses = getattr(
            settings.monitoring.agent_surveillance if hasattr(settings.monitoring, 'agent_surveillance') else type('obj', (), {}),
            'max_concurrent_analyses',
            10
        )

class AgentSurveillanceSystem:
    """Real-time agent monitoring, anomaly detection, and performance analysis.
    
    This system acts as the Agent Manager's eyes and ears, continuously monitoring:
    - Agent health and performance metrics
    - Behavioral anomalies using AI
    - Security violations and suspicious activities
    - API access patterns and data flow
    - Compliance with security policies
    
    Reports findings to Agent Manager for enforcement actions.
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
        
        # Load configuration with safe defaults
        self.config = SurveillanceConfig()
        
        # Runtime state
        self.agent_metrics: Dict[str, Dict] = {}
        self.monitoring_active = False
        self.analysis_semaphore = asyncio.Semaphore(self.config.max_concurrent_analyses)
        self.monitored_agents: Set[str] = set()
        
        logger.info(
            f"AgentSurveillanceSystem initialized. "
            f"AI analysis: {self.config.enable_ai_behavior_analysis}, "
            f"Monitoring interval: {self.config.monitoring_interval_seconds}s"
        )
    
    async def start_monitoring(self):
        """Start background monitoring of all agents"""
        if self.monitoring_active:
            logger.warning("Monitoring already active, skipping start")
            return
        
        self.monitoring_active = True
        logger.info("Starting agent surveillance system")
        
        while self.monitoring_active:
            try:
                await self._monitor_all_agents()
                await asyncio.sleep(self.config.monitoring_interval_seconds)
            except asyncio.CancelledError:
                logger.info("Agent surveillance monitoring loop cancelled.")
                self.monitoring_active = False
                break
            except Exception as e:
                logger.error(f"Monitoring loop failed: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait longer on error
    
    async def stop_monitoring(self):
        """Gracefully stop monitoring"""
        logger.info("Stopping agent surveillance system")
        self.monitoring_active = False
    
    async def _monitor_all_agents(self):
        """Monitor all active agents for anomalies and performance issues"""
        try:
            async with self.db_manager.get_session() as session:
                stale_cutoff = datetime.utcnow() - timedelta(
                    minutes=self.config.stale_agent_timeout_minutes
                )
                
                result = await session.execute(
                    select(Agent).where(
                        and_(
                            Agent.status == 'active',
                            Agent.last_heartbeat >= stale_cutoff
                        )
                    )
                )
                agents = result.scalars().all()
                
                # Track which agents we're monitoring
                current_agent_ids = {str(agent.id) for agent in agents}
                self.monitored_agents = current_agent_ids
                
                # Process agents with concurrency control
                monitoring_tasks = []
                for agent in agents:
                    monitoring_tasks.append(self._analyze_agent_with_semaphore(agent))
                
                # Gather results, capturing exceptions
                results = await asyncio.gather(*monitoring_tasks, return_exceptions=True)
                
                # Log any exceptions
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Error analyzing agent {agents[i].id}: {result}",
                            exc_info=result
                        )
        
        except Exception as e:
            logger.error(f"Error in _monitor_all_agents: {e}", exc_info=True)
    
    async def _analyze_agent_with_semaphore(self, agent):
        """Wrapper to enforce concurrency limits"""
        async with self.analysis_semaphore:
            return await self._analyze_agent(agent)
    
    async def _analyze_agent(self, agent):
        """Comprehensive agent analysis including performance and security"""
        try:
            analysis_start = datetime.utcnow()
            
            # Check basic health metrics
            health_issues = await self._check_health_metrics(agent)
            if health_issues:
                await self._handle_health_issues(agent, health_issues)
            
            # Perform AI-powered behavior analysis if enabled
            if self.config.enable_ai_behavior_analysis and self.ai_service:
                try:
                    agent_data = self._prepare_agent_data(agent)
                    analysis = await self._analyze_behavior_with_ai(agent_data)
                    
                    # Store metrics for historical analysis
                    self.agent_metrics[str(agent.id)] = {
                        **analysis,
                        'last_analyzed': analysis_start.isoformat(),
                        'analysis_duration': (datetime.utcnow() - analysis_start).total_seconds()
                    }
                    
                    # Handle anomalies
                    if analysis.get('is_anomaly', False):
                        await self._handle_anomaly(agent, analysis)
                
                except Exception as e:
                    logger.error(f"AI behavior analysis failed for agent {agent.id}: {e}")
            
            # Check for stale agents
            if await self._is_agent_stale(agent):
                await self._handle_stale_agent(agent)
            
            # Check for suspicious API access patterns
            await self._check_api_access_patterns(agent)
            
        except Exception as e:
            logger.error(f"Error analyzing agent {agent.id}: {e}", exc_info=True)
    
    async def _analyze_behavior_with_ai(self, agent_data: Dict) -> Dict:
        """Use AI to analyze agent behavior patterns"""
        try:
            # Create AI request for behavior analysis
            ai_request = AIRequest(
                request_id=f"surveillance_{agent_data['id']}_{datetime.utcnow().timestamp()}",
                model_type=AIModelType.LLM,
                input_data={
                    "task": "analyze_agent_behavior",
                    "agent_data": agent_data,
                    "thresholds": self.config.performance_thresholds
                },
                parameters={
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 500,
                    "temperature": 0.3  # Lower temperature for more deterministic analysis
                }
            )
            
            response = await self.ai_service.process_request(ai_request)
            
            if response.success:
                # Parse AI response
                result = response.output if isinstance(response.output, dict) else {
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'confidence': 0.5,
                    'ai_explanation': str(response.output)
                }
                return result
            else:
                logger.warning(f"AI behavior analysis failed: {response.metadata}")
                return {'is_anomaly': False, 'anomaly_score': 0.0, 'confidence': 0.0}
        
        except Exception as e:
            logger.error(f"Error in AI behavior analysis: {e}")
            return {'is_anomaly': False, 'anomaly_score': 0.0, 'confidence': 0.0}
    
    async def _check_health_metrics(self, agent) -> List[Dict]:
        """Check agent health metrics against thresholds"""
        issues = []
        metrics = agent.performance_metrics or {}
        
        # CPU usage check
        cpu_usage = metrics.get('cpu_usage', 0)
        if cpu_usage > self.config.performance_thresholds['cpu_usage']:
            issues.append({
                'type': 'high_cpu',
                'metric': 'cpu_usage',
                'value': cpu_usage,
                'threshold': self.config.performance_thresholds['cpu_usage']
            })
        
        # Memory usage check
        memory_usage = metrics.get('memory_usage', 0)
        if memory_usage > self.config.performance_thresholds['memory_usage']:
            issues.append({
                'type': 'high_memory',
                'metric': 'memory_usage',
                'value': memory_usage,
                'threshold': self.config.performance_thresholds['memory_usage']
            })
        
        # Response time check
        response_time = metrics.get('response_time', 0)
        if response_time > self.config.performance_thresholds['response_time']:
            issues.append({
                'type': 'high_response_time',
                'metric': 'response_time',
                'value': response_time,
                'threshold': self.config.performance_thresholds['response_time']
            })
        
        # Error rate check
        error_rate = metrics.get('error_rate', 0)
        if error_rate > self.config.performance_thresholds['error_rate']:
            issues.append({
                'type': 'high_error_rate',
                'metric': 'error_rate',
                'value': error_rate,
                'threshold': self.config.performance_thresholds['error_rate']
            })
        
        return issues
    
    async def _handle_health_issues(self, agent, issues: List[Dict]):
        """Handle detected health issues"""
        for issue in issues:
            severity = AlertSeverity.WARNING
            if issue['type'] in ['high_cpu', 'high_memory']:
                severity = AlertSeverity.CRITICAL if issue['value'] > 95 else AlertSeverity.WARNING
            elif issue['type'] == 'high_error_rate':
                severity = AlertSeverity.CRITICAL if issue['value'] > 0.1 else AlertSeverity.WARNING
            
            await self.alert_manager.create_alert(
                category=AlertCategory.PERFORMANCE,
                severity=severity,
                title=f"Agent Health Issue: {issue['type'].replace('_', ' ').title()}",
                description=(
                    f"Agent {agent.name} ({agent.id}) has {issue['type'].replace('_', ' ')}: "
                    f"{issue['value']:.2f} (threshold: {issue['threshold']})"
                ),
                source="AgentSurveillanceSystem",
                metadata={
                    "agent_id": str(agent.id),
                    "tenant_id": agent.tenant_id,
                    "metric": issue['metric'],
                    "value": issue['value'],
                    "threshold": issue['threshold']
                }
            )
    
    async def _handle_anomaly(self, agent, analysis: Dict):
        """Handle AI-detected anomalies"""
        anomaly_score = analysis.get('anomaly_score', 0)
        confidence = analysis.get('confidence', 0)
        
        severity = (
            AlertSeverity.CRITICAL 
            if anomaly_score > self.config.anomaly_threshold and confidence > 0.8
            else AlertSeverity.WARNING
        )
        
        await self.alert_manager.create_alert(
            category=AlertCategory.SECURITY,
            severity=severity,
            title="Agent Anomalous Behavior Detected",
            description=(
                f"Agent {agent.name} ({agent.id}) shows anomalous behavior: "
                f"score {anomaly_score:.3f} (confidence: {confidence:.3f}). "
                f"AI Explanation: {analysis.get('ai_explanation', 'N/A')}"
            ),
            source="AgentSurveillanceSystem",
            metadata={
                "agent_id": str(agent.id),
                "tenant_id": agent.tenant_id,
                "anomaly_score": anomaly_score,
                "confidence": confidence,
                "ai_analysis": analysis,
                "requires_manager_action": severity == AlertSeverity.CRITICAL
            }
        )
        
        # Update agent security score based on anomaly
        async with self.db_manager.get_session() as session:
            db_agent = await session.get(Agent, agent.id)
            if db_agent:
                score_reduction = (
                    self.config.security_score_reduction_critical 
                    if severity == AlertSeverity.CRITICAL 
                    else self.config.security_score_reduction_warning
                )
                new_score = max(0, db_agent.security_score - score_reduction)
                db_agent.security_score = new_score
                await session.commit()
                
                logger.warning(
                    f"Agent {agent.id} security score reduced to {new_score} "
                    f"due to anomaly (severity: {severity.value})"
                )
    
    async def _is_agent_stale(self, agent) -> bool:
        """Check if agent hasn't sent heartbeat recently"""
        if not agent.last_heartbeat:
            return True
        
        stale_threshold = datetime.utcnow() - timedelta(
            minutes=self.config.stale_agent_timeout_minutes
        )
        return agent.last_heartbeat < stale_threshold
    
    async def _handle_stale_agent(self, agent):
        """Handle agents that haven't sent recent heartbeats"""
        await self.alert_manager.create_alert(
            category=AlertCategory.SYSTEM,
            severity=AlertSeverity.WARNING,
            title="Agent Stale Heartbeat",
            description=(
                f"Agent {agent.name} ({agent.id}) has not sent a heartbeat in "
                f"{self.config.stale_agent_timeout_minutes} minutes."
            ),
            source="AgentSurveillanceSystem",
            metadata={
                "agent_id": str(agent.id),
                "tenant_id": agent.tenant_id,
                "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else "N/A"
            }
        )
    
    async def _check_api_access_patterns(self, agent):
        """Check for suspicious API access patterns"""
        try:
            metrics = agent.performance_metrics or {}
            
            # Check for unusual API call frequency
            api_calls = metrics.get('api_calls_per_minute', 0)
            if api_calls > 1000:  # Threshold for suspicious activity
                await self.alert_manager.create_alert(
                    category=AlertCategory.SECURITY,
                    severity=AlertSeverity.WARNING,
                    title="Suspicious API Access Pattern",
                    description=(
                        f"Agent {agent.name} ({agent.id}) is making unusually high "
                        f"number of API calls: {api_calls} calls/minute"
                    ),
                    source="AgentSurveillanceSystem",
                    metadata={
                        "agent_id": str(agent.id),
                        "tenant_id": agent.tenant_id,
                        "api_calls_per_minute": api_calls
                    }
                )
            
            # Check for unauthorized endpoint access attempts
            failed_auth_attempts = metrics.get('failed_auth_attempts', 0)
            if failed_auth_attempts > 5:
                await self.alert_manager.create_alert(
                    category=AlertCategory.SECURITY,
                    severity=AlertSeverity.CRITICAL,
                    title="Multiple Failed Authentication Attempts",
                    description=(
                        f"Agent {agent.name} ({agent.id}) has {failed_auth_attempts} "
                        f"failed authentication attempts"
                    ),
                    source="AgentSurveillanceSystem",
                    metadata={
                        "agent_id": str(agent.id),
                        "tenant_id": agent.tenant_id,
                        "failed_auth_attempts": failed_auth_attempts,
                        "requires_immediate_action": True
                    }
                )
        
        except Exception as e:
            logger.error(f"Error checking API access patterns for agent {agent.id}: {e}")
    
    def _prepare_agent_data(self, agent) -> Dict:
        """Prepare agent data for AI analysis"""
        metrics = agent.performance_metrics or {}
        
        return {
            'id': str(agent.id),
            'name': agent.name,
            'type': agent.type,
            'cpu_usage': metrics.get('cpu_usage', 0),
            'memory_usage': metrics.get('memory_usage', 0),
            'response_time': metrics.get('response_time', 0),
            'error_rate': metrics.get('error_rate', 0),
            'api_calls_per_minute': metrics.get('api_calls_per_minute', 0),
            'failed_auth_attempts': metrics.get('failed_auth_attempts', 0),
            'last_heartbeat': agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
            'security_score': agent.security_score,
            'uptime_seconds': (datetime.utcnow() - agent.created_at).total_seconds() if agent.created_at else 0,
            'status': agent.status,
            'capabilities': agent.capabilities,
            'recent_tasks_completed': metrics.get('recent_tasks_completed', 0),
            'recent_tasks_failed': metrics.get('recent_tasks_failed', 0)
        }
    
    async def get_agent_metrics(self, agent_id: str) -> Optional[Dict]:
        """Get historical metrics for an agent"""
        return self.agent_metrics.get(agent_id)
    
    async def get_all_metrics(self) -> Dict:
        """Get metrics for all monitored agents"""
        return self.agent_metrics.copy()
    
    async def get_surveillance_report(self) -> Dict:
        """Generate comprehensive surveillance report"""
        return {
            "monitoring_active": self.monitoring_active,
            "monitored_agents_count": len(self.monitored_agents),
            "agents_with_metrics": len(self.agent_metrics),
            "configuration": {
                "anomaly_threshold": self.config.anomaly_threshold,
                "monitoring_interval_seconds": self.config.monitoring_interval_seconds,
                "ai_analysis_enabled": self.config.enable_ai_behavior_analysis
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    async def health_check(self) -> str:
        """Perform a health check on the AgentSurveillanceSystem."""
        try:
            # Check if DB is accessible
            async with self.db_manager.get_session() as session:
                await session.execute(select(Agent).limit(1))
            
            # Check AI service health
            if self.ai_service:
                ai_health = await self.ai_service.health_check()
                if ai_health != "healthy":
                    return f"degraded: AI service is {ai_health}"
            
            # Check Alert Manager health
            alert_manager_health = await self.alert_manager.health_check()
            if alert_manager_health != "healthy":
                return f"degraded: Alert Manager is {alert_manager_health}"
            
            return "healthy"
        except Exception as e:
            logger.error(f"AgentSurveillanceSystem health check failed: {e}", exc_info=True)
            return "unhealthy"
