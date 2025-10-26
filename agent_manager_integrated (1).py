"""
Integrated Agent Manager with Code of Conduct Enforcement

This is the SUPREME AGENT MANAGER that:
1. Manages all agent lifecycles
2. Enforces mandatory code of conduct
3. Monitors and surveils all activities
4. Orchestrates intelligent task allocation
5. Reports to admin with recommendations
6. Freezes agents/modules/system on high-risk activities
7. Maintains complete audit trail
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from agent_lifecycle_manager import (
    AgentLifecycleManager, AgentStatus, AgentMetricsSnapshot,
    AgentRegistrationRequest
)
from agent_surveillance import AgentSurveillanceSystem
from agent_orchestrator import (
    IntelligentAgentOrchestrator, TaskRequirement, TaskAssignment,
    AgentProfile, AgentCapability, AgentPerformanceLevel, TaskPriority
)
from agent_code_of_conduct import (
    AgentCodeOfConduct, ActivityLogEntry, ActivityType, RiskLevel
)
from database.secure_database_manager import SecureDatabaseManager
from security.rbac_manager import RBACManager
from monitoring.telemetry_manager import TelemetryManager
from monitoring.alert_manager import AlertManager, AlertCategory, AlertSeverity
from ai.multi_modal_ai import MultiModalAIService
from config import settings

logger = logging.getLogger(__name__)


class SupremeAgentManager:
    """
    SUPREME AGENT MANAGER
    
    This is the central authority for all agent management with:
    - MANDATORY code of conduct enforcement
    - Complete activity logging
    - Real-time surveillance
    - Intelligent orchestration
    - Admin reporting with recommendations
    - Automatic freeze capabilities
    - Full audit trail
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
        
        # MANDATORY: Code of Conduct Protocol
        self.code_of_conduct = AgentCodeOfConduct(
            db_manager, alert_manager
        )
        
        # Core dependencies
        self.db_manager = db_manager
        self.telemetry_manager = telemetry_manager
        self.alert_manager = alert_manager
        self.ai_service = ai_service
        
        # State management
        self.active_agents: Dict[str, Dict] = {}
        self.agent_conversations: Dict[str, List[Dict]] = {}
        
        logger.critical("=" * 80)
        logger.critical("🎯 SUPREME AGENT MANAGER INITIALIZED")
        logger.critical("📋 Code of Conduct: ENFORCED")
        logger.critical("👁️  Surveillance: ACTIVE")
        logger.critical("🤖 Orchestration: ENABLED")
        logger.critical("=" * 80)

    async def start(self):
        """Start all agent management sub-systems"""
        logger.info("Starting Supreme Agent Management System...")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self.surveillance_system.start_monitoring(), name="surveillance"),
            asyncio.create_task(self.orchestrator.start_performance_monitoring(), name="orchestration"),
            asyncio.create_task(self.code_of_conduct.start_background_tasks(), name="code_of_conduct"),
            asyncio.create_task(self._sync_agents_periodically(), name="sync"),
            asyncio.create_task(self._monitor_frozen_entities(), name="freeze_monitor")
        ]
        
        logger.critical("✅ Supreme Agent Management System STARTED")
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Supreme Agent Management System shutdown requested")
            for task in tasks:
                task.cancel()

    async def register_agent(
        self,
        tenant_id: str,
        registration_data: Dict[str, Any],
        requester_id: str
    ) -> Dict[str, Any]:
        """
        Register a new agent with MANDATORY logging
        """
        try:
            # LOG: Agent registration attempt
            await self.code_of_conduct.log_activity(
                ActivityLogEntry(
                    agent_id="system",
                    tenant_id=tenant_id,
                    activity_type=ActivityType.SYSTEM_MODIFICATION,
                    description=f"Agent registration requested by {requester_id}",
                    context={
                        'operation': 'register_agent',
                        'requester': requester_id,
                        'agent_name': registration_data.get('name'),
                        'agent_type': registration_data.get('agent_type')
                    }
                ),
                force_immediate=True
            )
            
            # Validate registration
            registration = AgentRegistrationRequest(**registration_data)
            
            # Register agent
            agent = await self.lifecycle_manager.register_agent(
                tenant_id, registration, requester_id
            )
            
            # Initialize orchestrator profile
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
                'registered_at': datetime.utcnow(),
                'conversation_count': 0,
                'total_tasks': 0
            }
            
            # LOG: Successful registration
            await self.code_of_conduct.log_activity(
                ActivityLogEntry(
                    agent_id=agent.id,
                    tenant_id=tenant_id,
                    activity_type=ActivityType.SYSTEM_MODIFICATION,
                    description=f"Agent {agent.name} successfully registered",
                    context={
                        'operation': 'register_agent_success',
                        'agent_id': agent.id,
                        'agent_name': agent.name,
                        'agent_type': agent.type,
                        'capabilities': registration.capabilities
                    }
                ),
                force_immediate=True
            )
            
            logger.info(f"✅ Agent {agent.id} registered successfully")
            
            return {
                'status': 'success',
                'agent_id': agent.id,
                'message': 'Agent registered and monitoring activated',
                'agent': {
                    'id': agent.id,
                    'name': agent.name,
                    'type': agent.type,
                    'status': agent.status,
                    'capabilities': agent.capabilities,
                    'security_score': agent.security_score
                }
            }
            
        except Exception as e:
            logger.error(f"Agent registration failed: {e}", exc_info=True)
            
            # LOG: Failed registration
            await self.code_of_conduct.log_activity(
                ActivityLogEntry(
                    agent_id="system",
                    tenant_id=tenant_id,
                    activity_type=ActivityType.ERROR_OCCURRENCE,
                    description=f"Agent registration failed: {str(e)}",
                    context={
                        'operation': 'register_agent_failed',
                        'error': str(e),
                        'requester': requester_id
                    }
                ),
                force_immediate=True
            )
            
            return {
                'status': 'failure',
                'error': str(e)
            }

    async def update_agent_metrics(
        self,
        agent_id: str,
        metrics_data: Dict[str, Any],
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Update agent metrics with MANDATORY logging
        """
        try:
            # Check if agent is frozen
            if self.code_of_conduct.check_agent_frozen(agent_id):
                raise PermissionError(f"Agent {agent_id} is frozen and cannot send metrics")
            
            # LOG: Metrics update
            await self.code_of_conduct.log_activity(
                ActivityLogEntry(
                    agent_id=agent_id,
                    tenant_id=tenant_id,
                    activity_type=ActivityType.INTERACTION,
                    description="Agent metrics heartbeat",
                    context={
                        'operation': 'metrics_update',
                        'cpu_usage': metrics_data.get('cpu_usage'),
                        'memory_usage': metrics_data.get('memory_usage'),
                        'error_rate': metrics_data.get('error_rate')
                    }
                )
            )
            
            return {"status": "success", "agent_id": agent_id}
        except Exception as e:
            logger.error(f"Failed to update agent metrics: {e}")
            raise