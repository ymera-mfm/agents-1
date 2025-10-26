"""
Agent Manager Integration Module

This module provides a unified interface for all agent management operations,
integrating lifecycle management, surveillance, and orchestration.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from agent_lifecycle_manager import AgentLifecycleManager, AgentStatus, AgentMetricsSnapshot
from agent_surveillance import AgentSurveillanceSystem
from agent_orchestrator import IntelligentAgentOrchestrator, TaskRequirement, TaskAssignment
from database.secure_database_manager import SecureDatabaseManager
from security.rbac_manager import RBACManager
from monitoring.telemetry_manager import TelemetryManager
from monitoring.alert_manager import AlertManager
from ai.multi_modal_ai import MultiModalAIService
from config import settings

logger = logging.getLogger(__name__)


class AgentManagerOperationResult(Enum):
    """Operation result status"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    PENDING = "pending"


class AgentManager:
    """
    Unified Agent Management System
    
    Provides a single interface for all agent management operations including:
    - Agent lifecycle management
    - Real-time surveillance and monitoring
    - Intelligent task orchestration
    - Performance analytics
    - Security and compliance
    """

    def __init__(
        self,
        db_manager: SecureDatabaseManager,
        rbac_manager: RBACManager,
        telemetry_manager: TelemetryManager,
        alert_manager: AlertManager,
        ai_service: MultiModalAIService
    ):
        # Initialize sub-systems
        self.lifecycle_manager = AgentLifecycleManager(
            db_manager, rbac_manager, telemetry_manager, alert_manager
        )
        
        self.surveillance_system = AgentSurveillanceSystem(
            db_manager, ai_service, alert_manager
        )
        
        self.orchestrator = IntelligentAgentOrchestrator(ai_service)
        
        # Core dependencies
        self.db_manager = db_manager
        self.telemetry_manager = telemetry_manager
        self.alert_manager = alert_manager
        
        # State management
        self.active_agents: Dict[str, Dict] = {}
        self.agent_conversations: Dict[str, List[Dict]] = {}
        
        logger.info("AgentManager initialized successfully")

    async def start(self):
        """Start all agent management sub-systems"""
        logger.info("Starting Agent Management System...")
        
        tasks = [
            asyncio.create_task(self.surveillance_system.start_monitoring(), name="surveillance"),
            asyncio.create_task(self.orchestrator.start_performance_monitoring(), name="orchestration"),
            asyncio.create_task(self._sync_agents_periodically(), name="sync"),
            asyncio.create_task(self._cleanup_stale_data(), name="cleanup")
        ]
        
        logger.info("Agent Management System started successfully")
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Agent Management System shutdown requested")
            for task in tasks:
                task.cancel()

    async def register_agent(
        self,
        tenant_id: str,
        registration_data: Dict[str, Any],
        requester_id: str
    ) -> Dict[str, Any]:
        """
        Register a new agent
        
        This method:
        1. Validates registration data
        2. Creates agent record
        3. Provisions resources
        4. Initializes monitoring
        """
        try:
            from agent_lifecycle_manager import AgentRegistrationRequest
            
            # Validate and create registration request
            registration = AgentRegistrationRequest(**registration_data)
            
            # Register agent
            agent = await self.lifecycle_manager.register_agent(
                tenant_id, registration, requester_id
            )
            
            # Initialize orchestrator profile
            from agent_orchestrator import AgentProfile, AgentCapability, AgentPerformanceLevel
            
            profile = AgentProfile(
                agent_id=agent.id,
                capabilities=[AgentCapability(c) for c in registration.capabilities.get('types', [])],
                performance_metrics={
                    'success_rate': 1.0,
                    'avg_response_time': 100.0,
                    'throughput': 0,
                    'error_rate': 0.0
                },
                current_load=0.0,
                max_capacity=registration.capabilities.get('max_concurrent_tasks', 10),
                performance_level=AgentPerformanceLevel.GOOD,
                last_updated=datetime.utcnow()
            )
            
            self.orchestrator.update_agent_profile(profile)
            
            # Track active agent
            self.active_agents[agent.id] = {
                'agent': agent,
                'profile': profile,
                'registered_at': datetime.utcnow()
            }
            
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'agent_id': agent.id,
                'message': 'Agent registered and provisioning started',
                'agent': {
                    'id': agent.id,
                    'name': agent.name,
                    'type': agent.type,
                    'status': agent.status,
                    'capabilities': agent.capabilities
                }
            }
            
        except Exception as e:
            logger.error(f"Agent registration failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def update_agent_metrics(
        self,
        agent_id: str,
        metrics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update agent metrics from heartbeat
        
        This method:
        1. Updates lifecycle metrics
        2. Feeds surveillance system
        3. Updates orchestrator profile
        """
        try:
            # Create metrics snapshot
            metrics = AgentMetricsSnapshot(**metrics_data)
            
            # Update lifecycle manager
            await self.lifecycle_manager.update_agent_metrics(agent_id, metrics)
            
            # Update orchestrator profile
            if agent_id in self.active_agents:
                profile = self.active_agents[agent_id]['profile']
                profile.performance_metrics.update({
                    'avg_response_time': metrics.response_time_avg,
                    'error_rate': metrics.error_rate,
                    'throughput': metrics.completed_tasks
                })
                profile.last_updated = datetime.utcnow()
                self.orchestrator.update_agent_profile(profile)
            
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'message': 'Metrics updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Metrics update failed for {agent_id}: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def assign_task(
        self,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assign task to optimal agent using intelligent orchestration
        """
        try:
            from agent_orchestrator import TaskRequirement, TaskPriority, AgentCapability
            
            # Create task requirement
            task = TaskRequirement(
                task_id=task_data['task_id'],
                required_capabilities=[AgentCapability(c) for c in task_data.get('required_capabilities', [])],
                priority=TaskPriority(task_data.get('priority', 'normal')),
                deadline=task_data.get('deadline'),
                estimated_duration=task_data.get('estimated_duration', 60.0),
                resource_requirements=task_data.get('resource_requirements', {}),
                tenant_id=task_data.get('tenant_id')
            )
            
            # Assign using orchestrator
            assignment = await self.orchestrator.assign_task(task)
            
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'assignment': {
                    'task_id': assignment.task_id,
                    'agent_id': assignment.agent_id,
                    'confidence': assignment.confidence_score,
                    'estimated_completion': assignment.estimated_completion_time.isoformat(),
                    'alternatives': assignment.alternative_agents,
                    'reason': assignment.assignment_reason
                }
            }
            
        except Exception as e:
            logger.error(f"Task assignment failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def record_task_completion(
        self,
        task_id: str,
        agent_id: str,
        completion_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record task completion for learning and analytics
        """
        try:
            success = completion_data.get('success', False)
            actual_duration = completion_data.get('duration', 0.0)
            metrics = completion_data.get('metrics', {})
            
            # Update orchestrator
            await self.orchestrator.record_task_completion(
                task_id, agent_id, success, actual_duration, metrics
            )
            
            # Record telemetry
            await self.telemetry_manager.record_event(
                "task_completed",
                {
                    'task_id': task_id,
                    'agent_id': agent_id,
                    'success': success,
                    'duration': actual_duration
                }
            )
            
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'message': 'Task completion recorded'
            }
            
        except Exception as e:
            logger.error(f"Failed to record task completion: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        try:
            # Get from lifecycle manager
            agent = await self.lifecycle_manager.get_agent(agent_id)
            if not agent:
                return {'status': 'not_found'}
            
            # Get surveillance report
            surveillance_report = await self.surveillance_system.get_agent_surveillance_report(agent_id)
            
            # Get analytics
            analytics = await self.lifecycle_manager.get_agent_analytics(agent_id, 24)
            
            # Get orchestration info
            orchestration_data = {}
            if agent_id in self.active_agents:
                profile = self.active_agents[agent_id]['profile']
                orchestration_data = {
                    'current_load': profile.current_load,
                    'max_capacity': profile.max_capacity,
                    'utilization': profile.current_load / profile.max_capacity,
                    'performance_level': profile.performance_level.value
                }
            
            return {
                'agent_id': agent_id,
                'basic_info': {
                    'name': agent.name,
                    'type': agent.type,
                    'status': agent.status,
                    'version': agent.version,
                    'security_score': agent.security_score
                },
                'surveillance': surveillance_report,
                'analytics': analytics,
                'orchestration': orchestration_data,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        try:
            lifecycle_health = await self.lifecycle_manager.health_check()
            surveillance_health = await self.surveillance_system.health_check()
            orchestration_health = await self.orchestrator.health_check()
            
            orchestration_analytics = await self.orchestrator.get_orchestration_analytics()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'healthy' if all(h == 'healthy' for h in [lifecycle_health, surveillance_health, orchestration_health]) else 'degraded',
                'components': {
                    'lifecycle_manager': lifecycle_health,
                    'surveillance_system': surveillance_health,
                    'orchestrator': orchestration_health
                },
                'metrics': {
                    'total_agents': len(self.active_agents),
                    'orchestration': orchestration_analytics
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {'overall_status': 'unhealthy', 'error': str(e)}

    async def quarantine_agent(
        self,
        agent_id: str,
        reason: str,
        requester_id: str
    ) -> Dict[str, Any]:
        """Quarantine an agent for security reasons"""
        try:
            success = await self.lifecycle_manager.quarantine_agent(
                agent_id, reason, requester_id
            )
            
            if success:
                # Remove from active orchestration
                if agent_id in self.active_agents:
                    del self.active_agents[agent_id]
                
                return {
                    'status': AgentManagerOperationResult.SUCCESS.value,
                    'message': f'Agent {agent_id} quarantined successfully'
                }
            else:
                return {
                    'status': AgentManagerOperationResult.FAILURE.value,
                    'message': 'Failed to quarantine agent'
                }
                
        except Exception as e:
            logger.error(f"Quarantine failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def decommission_agent(
        self,
        agent_id: str,
        reason: str,
        requester_id: str
    ) -> Dict[str, Any]:
        """Gracefully decommission an agent"""
        try:
            success = await self.lifecycle_manager.decommission_agent(
                agent_id, reason, requester_id
            )
            
            if success:
                # Remove from active tracking
                if agent_id in self.active_agents:
                    del self.active_agents[agent_id]
                
                return {
                    'status': AgentManagerOperationResult.SUCCESS.value,
                    'message': f'Agent {agent_id} decommissioning initiated'
                }
            else:
                return {
                    'status': AgentManagerOperationResult.FAILURE.value,
                    'message': 'Failed to initiate decommissioning'
                }
                
        except Exception as e:
            logger.error(f"Decommission failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def get_capacity_forecast(
        self,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Get capacity planning forecast"""
        try:
            forecast = await self.orchestrator.capacity_planning(forecast_days)
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'forecast': forecast
            }
        except Exception as e:
            logger.error(f"Capacity forecast failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def optimize_load_distribution(self) -> Dict[str, Any]:
        """Optimize load distribution across agents"""
        try:
            result = await self.orchestrator.intelligent_load_balancing()
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'optimization': result
            }
        except Exception as e:
            logger.error(f"Load optimization failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def get_maintenance_schedule(self) -> Dict[str, Any]:
        """Get predictive maintenance schedule"""
        try:
            schedule = await self.orchestrator.predictive_maintenance()
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'schedule': schedule
            }
        except Exception as e:
            logger.error(f"Maintenance schedule failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def track_conversation(
        self,
        conversation_id: str,
        agent_id: str,
        user_id: str,
        message_data: Dict[str, Any]
    ) -> None:
        """Track agent-user conversation for quality monitoring"""
        if agent_id not in self.agent_conversations:
            self.agent_conversations[agent_id] = []
        
        self.agent_conversations[agent_id].append({
            'conversation_id': conversation_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
            'message': message_data
        })
        
        # Keep only recent conversations
        max_conversations = 1000
        if len(self.agent_conversations[agent_id]) > max_conversations:
            self.agent_conversations[agent_id] = self.agent_conversations[agent_id][-max_conversations:]

    async def get_agent_conversations(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get recent conversations for an agent"""
        conversations = self.agent_conversations.get(agent_id, [])
        return conversations[-limit:]

    async def _sync_agents_periodically(self):
        """Periodically sync agent states between subsystems"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Get all active agents from database
                agents = await self.lifecycle_manager.list_agents(
                    tenant_id=None,  # Get all tenants
                    status='active'
                )
                
                # Sync with orchestrator
                for agent in agents:
                    if agent.id in self.active_agents:
                        profile = self.active_agents[agent.id]['profile']
                        
                        # Update from database
                        profile.performance_metrics.update(agent.performance_metrics or {})
                        profile.last_updated = agent.last_heartbeat or datetime.utcnow()
                        
                        # Re-register with orchestrator
                        self.orchestrator.update_agent_profile(profile)
                
                logger.debug(f"Synced {len(agents)} agents")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent sync error: {e}", exc_info=True)

    async def _cleanup_stale_data(self):
        """Clean up stale data periodically"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Clean up old conversations
                cutoff = datetime.utcnow() - timedelta(days=7)
                for agent_id in list(self.agent_conversations.keys()):
                    conversations = self.agent_conversations[agent_id]
                    self.agent_conversations[agent_id] = [
                        c for c in conversations 
                        if c['timestamp'] > cutoff
                    ]
                
                # Clean up inactive agents from active tracking
                inactive_agents = []
                for agent_id, data in self.active_agents.items():
                    if (datetime.utcnow() - data['profile'].last_updated).total_seconds() > 3600:
                        inactive_agents.append(agent_id)
                
                for agent_id in inactive_agents:
                    del self.active_agents[agent_id]
                
                if inactive_agents:
                    logger.info(f"Cleaned up {len(inactive_agents)} inactive agents from tracking")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}", exc_info=True)

    async def generate_comprehensive_report(
        self,
        tenant_id: Optional[str] = None,
        report_type: str = 'full'
    ) -> Dict[str, Any]:
        """
        Generate comprehensive management report
        
        Report types:
        - full: Complete system report
        - performance: Performance metrics only
        - security: Security posture only
        - capacity: Capacity and forecasting only
        """
        try:
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'report_type': report_type,
                'tenant_id': tenant_id
            }
            
            if report_type in ['full', 'performance']:
                # Get orchestration analytics
                orchestration = await self.orchestrator.get_orchestration_analytics()
                report['performance'] = orchestration
            
            if report_type in ['full', 'security']:
                # Get surveillance summary
                surveillance_summary = await self.surveillance_system._generate_surveillance_summary()
                report['security'] = surveillance_summary
            
            if report_type in ['full', 'capacity']:
                # Get capacity forecast
                capacity = await self.orchestrator.capacity_planning()
                report['capacity'] = capacity
            
            if report_type == 'full':
                # Get system health
                health = await self.get_system_health()
                report['system_health'] = health
                
                # Get maintenance schedule
                maintenance = await self.orchestrator.predictive_maintenance()
                report['maintenance_schedule'] = maintenance
            
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'report': report
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def bulk_operations(
        self,
        operation: str,
        agent_ids: List[str],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform bulk operations on multiple agents
        
        Supported operations:
        - update_status
        - restart
        - upgrade
        - maintenance
        """
        results = {
            'total': len(agent_ids),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for agent_id in agent_ids:
            try:
                if operation == 'update_status':
                    # Update status operation
                    from agent_lifecycle_manager import AgentStatus
                    new_status = AgentStatus(parameters['status'])
                    success = await self.lifecycle_manager.update_agent_status(
                        agent_id, new_status
                    )
                    
                    if success:
                        results['successful'] += 1
                        results['details'].append({
                            'agent_id': agent_id,
                            'status': 'success'
                        })
                    else:
                        results['failed'] += 1
                        results['details'].append({
                            'agent_id': agent_id,
                            'status': 'failed',
                            'reason': 'Status update failed'
                        })
                
                elif operation == 'restart':
                    # Trigger restart via remediation
                    success = await self.lifecycle_manager._execute_remediation_step(
                        agent_id, 'restart'
                    )
                    
                    if success:
                        results['successful'] += 1
                        results['details'].append({
                            'agent_id': agent_id,
                            'status': 'success'
                        })
                    else:
                        results['failed'] += 1
                        results['details'].append({
                            'agent_id': agent_id,
                            'status': 'failed',
                            'reason': 'Restart failed'
                        })
                
                # Add more operations as needed
                
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'agent_id': agent_id,
                    'status': 'failed',
                    'reason': str(e)
                })
        
        return {
            'status': AgentManagerOperationResult.SUCCESS.value if results['failed'] == 0 else AgentManagerOperationResult.PARTIAL_SUCCESS.value,
            'results': results
        }

    async def search_agents(
        self,
        query: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Advanced agent search with filtering
        
        Query parameters:
        - status: Agent status
        - capabilities: Required capabilities
        - performance_level: Performance level
        - min_security_score: Minimum security score
        - tags: Agent tags
        """
        try:
            # Get base list
            agents = await self.lifecycle_manager.list_agents(
                tenant_id=tenant_id,
                status=query.get('status'),
                agent_type=query.get('type')
            )
            
            # Apply additional filters
            filtered_agents = []
            
            for agent in agents:
                # Check capabilities
                if 'capabilities' in query:
                    required_caps = set(query['capabilities'])
                    agent_caps = set(agent.capabilities.get('types', []))
                    if not required_caps.issubset(agent_caps):
                        continue
                
                # Check security score
                if 'min_security_score' in query:
                    if agent.security_score < query['min_security_score']:
                        continue
                
                # Check performance level
                if 'performance_level' in query:
                    if agent.id in self.active_agents:
                        profile = self.active_agents[agent.id]['profile']
                        if profile.performance_level.value != query['performance_level']:
                            continue
                
                filtered_agents.append({
                    'id': agent.id,
                    'name': agent.name,
                    'type': agent.type,
                    'status': agent.status,
                    'security_score': agent.security_score,
                    'capabilities': agent.capabilities
                })
            
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'total_results': len(filtered_agents),
                'agents': filtered_agents
            }
            
        except Exception as e:
            logger.error(f"Agent search failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def export_agent_data(
        self,
        agent_id: str,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Export complete agent data for backup or transfer
        
        Formats: json, yaml, csv
        """
        try:
            # Get complete agent data
            agent = await self.lifecycle_manager.get_agent(agent_id)
            if not agent:
                return {
                    'status': AgentManagerOperationResult.FAILURE.value,
                    'error': 'Agent not found'
                }
            
            # Get analytics
            analytics = await self.lifecycle_manager.get_agent_analytics(agent_id)
            
            # Get surveillance report
            surveillance = await self.surveillance_system.get_agent_surveillance_report(agent_id)
            
            # Get conversation history
            conversations = await self.get_agent_conversations(agent_id)
            
            export_data = {
                'agent_id': agent_id,
                'exported_at': datetime.utcnow().isoformat(),
                'basic_info': {
                    'name': agent.name,
                    'type': agent.type,
                    'version': agent.version,
                    'status': agent.status,
                    'created_at': agent.created_at.isoformat(),
                    'capabilities': agent.capabilities
                },
                'analytics': analytics,
                'surveillance': surveillance,
                'conversations': conversations
            }
            
            if format == 'json':
                import json
                formatted_data = json.dumps(export_data, indent=2)
            elif format == 'yaml':
                import yaml
                formatted_data = yaml.dump(export_data, default_flow_style=False)
            else:
                formatted_data = str(export_data)
            
            return {
                'status': AgentManagerOperationResult.SUCCESS.value,
                'format': format,
                'data': formatted_data
            }
            
        except Exception as e:
            logger.error(f"Agent data export failed: {e}", exc_info=True)
            return {
                'status': AgentManagerOperationResult.FAILURE.value,
                'error': str(e)
            }

    async def health_check(self) -> str:
        """Overall health check"""
        try:
            health = await self.get_system_health()
            return health['overall_status']
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return 'unhealthy'


# Factory function for easy initialization
def create_agent_manager(
    db_manager: SecureDatabaseManager,
    rbac_manager: RBACManager,
    telemetry_manager: TelemetryManager,
    alert_manager: AlertManager,
    ai_service: MultiModalAIService
) -> AgentManager:
    """Factory function to create AgentManager instance"""
    return AgentManager(
        db_manager,
        rbac_manager,
        telemetry_manager,
        alert_manager,
        ai_service
    )
