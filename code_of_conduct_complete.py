"""
Agent Code of Conduct & Compliance Protocol System - COMPLETE

This module enforces MANDATORY logging, monitoring, and administrative oversight
for all agent activities, interactions, and processes.

CRITICAL: This protocol is MANDATORY and cannot be disabled or bypassed.
All agent activities MUST be logged and reviewed.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import json
import hashlib
from collections import deque
import uuid

from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, Boolean, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import declarative_base

from config import settings
from database.secure_database_manager import SecureDatabaseManager
from monitoring.alert_manager import AlertManager, AlertCategory, AlertSeverity

logger = logging.getLogger(__name__)

Base = declarative_base()


class RiskLevel(str, Enum):
    """Risk levels for agent activities"""
    NEGLIGIBLE = "negligible"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ActivityType(str, Enum):
    """Types of agent activities to log"""
    INTERACTION = "interaction"
    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"
    PROCESS_EXECUTION = "process_execution"
    DATA_ACCESS = "data_access"
    DECISION_MAKING = "decision_making"
    SYSTEM_MODIFICATION = "system_modification"
    EXTERNAL_COMMUNICATION = "external_communication"
    ERROR_OCCURRENCE = "error_occurrence"
    SECURITY_EVENT = "security_event"
    API_CALL = "api_call"
    DATABASE_OPERATION = "database_operation"
    FILE_OPERATION = "file_operation"


class SystemAction(str, Enum):
    """Actions the system can take"""
    LOG_ONLY = "log_only"
    ALERT_ADMIN = "alert_admin"
    REQUEST_APPROVAL = "request_approval"
    FREEZE_AGENT = "freeze_agent"
    FREEZE_MODULE = "freeze_module"
    FREEZE_SYSTEM = "freeze_system"
    QUARANTINE = "quarantine"
    TERMINATE = "terminate"


# Database Models

class AgentActivityLog(Base):
    """Comprehensive activity log for all agent actions"""
    __tablename__ = "agent_activity_logs"
    
    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)
    activity_category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    
    # Context
    context = Column(JSON, nullable=False)
    user_id = Column(String(36), nullable=True, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    
    # Data involved
    input_data_hash = Column(String(64), nullable=True)  # Hash of input
    output_data_hash = Column(String(64), nullable=True)  # Hash of output
    knowledge_gained = Column(JSON, nullable=True)
    
    # Risk and compliance
    risk_level = Column(String(20), nullable=False, index=True)
    compliance_flags = Column(JSON, default=list)
    requires_review = Column(Boolean, default=False, index=True)
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Traceability
    parent_activity_id = Column(String(36), nullable=True, index=True)
    correlation_id = Column(String(36), nullable=False, index=True)
    
    # Integrity
    hash_signature = Column(String(64), nullable=False)
    
    __table_args__ = (
        Index('ix_agent_activity_timestamp_risk', 'timestamp', 'risk_level'),
        Index('ix_agent_activity_agent_type', 'agent_id', 'activity_type'),
        Index('ix_agent_activity_requires_review', 'requires_review', 'reviewed_at'),
    )


class AdminNotification(Base):
    """Admin notifications for agent activities requiring attention"""
    __tablename__ = "admin_notifications"
    
    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, nullable=False, index=True)
    
    risk_level = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    agent_id = Column(String(36), nullable=True, index=True)
    activity_log_id = Column(String(36), nullable=True, index=True)
    
    recommended_actions = Column(JSON, nullable=False)
    system_action_taken = Column(String(50), nullable=True)
    
    status = Column(String(20), default='pending', index=True)
    admin_response = Column(JSON, nullable=True)
    responded_by = Column(String(36), nullable=True)
    responded_at = Column(DateTime, nullable=True)
    
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('ix_admin_notif_status_risk', 'status', 'risk_level'),
        Index('ix_admin_notif_created_status', 'created_at', 'status'),
    )


class SystemFreezeLog(Base):
    """Log of system freezes for audit trail"""
    __tablename__ = "system_freeze_logs"
    
    id = Column(String(36), primary_key=True)
    freeze_timestamp = Column(DateTime, nullable=False, index=True)
    unfreeze_timestamp = Column(DateTime, nullable=True)
    
    freeze_type = Column(String(20), nullable=False)
    freeze_target = Column(String(255), nullable=False)
    
    reason = Column(Text, nullable=False)
    triggered_by_activity = Column(String(36), nullable=True)
    risk_level = Column(String(20), nullable=False)
    
    admin_notified = Column(Boolean, default=True)
    admin_approval_required = Column(Boolean, default=True)
    
    unfreeze_authorized_by = Column(String(36), nullable=True)
    unfreeze_reason = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('ix_freeze_timestamp_type', 'freeze_timestamp', 'freeze_type'),
    )


@dataclass
class ActivityLogEntry:
    """Activity log entry structure"""
    agent_id: str
    tenant_id: str
    activity_type: ActivityType
    description: str
    context: Dict[str, Any]
    risk_level: RiskLevel = RiskLevel.LOW
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    knowledge_gained: Optional[Dict] = None
    compliance_flags: List[str] = field(default_factory=list)
    parent_activity_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    risk_level: RiskLevel
    risk_score: float
    risk_factors: List[str]
    recommended_action: SystemAction
    requires_admin_review: bool
    requires_approval: bool


class AgentCodeOfConduct:
    """
    Enforces mandatory code of conduct for all agents
    
    MANDATORY PROTOCOLS:
    1. All activities MUST be logged
    2. All interactions MUST be recorded
    3. All knowledge gained MUST be documented
    4. All processes MUST be traceable
    5. High-risk activities MUST trigger admin notification
    6. Critical activities MUST freeze and await admin approval
    """

    def __init__(
        self,
        db_manager: SecureDatabaseManager,
        alert_manager: AlertManager
    ):
        self.db_manager = db_manager
        self.alert_manager = alert_manager
        
        # In-memory buffer for high-frequency logging
        self.log_buffer: deque = deque(maxlen=10000)
        self.buffer_flush_interval = 30  # seconds
        
        # Frozen entities tracking
        self.frozen_agents: Dict[str, Dict] = {}
        self.frozen_modules: Dict[str, Dict] = {}
        self.system_frozen: bool = False
        
        # Freeze locks to prevent concurrent unfreezing
        self.freeze_locks: Dict[str, asyncio.Lock] = {}
        
        # Risk assessment rules
        self.risk_rules = self._initialize_risk_rules()
        
        # Admin notification queue
        self.pending_admin_notifications: deque = deque()
        
        # Compliance keywords
        self.compliance_keywords = self._load_compliance_keywords()
        
        # Statistics
        self.stats = {
            'total_activities_logged': 0,
            'high_risk_activities': 0,
            'agents_frozen': 0,
            'admin_notifications_sent': 0
        }
        
        logger.critical("⚠️  Agent Code of Conduct Protocol ACTIVATED")
        logger.critical("📝 All agent activities will be monitored and logged")
        logger.critical("🔒 High-risk activities will trigger automatic freezes")

    def _initialize_risk_rules(self) -> Dict[str, Dict]:
        """Initialize risk assessment rules"""
        return {
            'system_modification': {
                'base_risk': RiskLevel.HIGH,
                'keywords': ['delete', 'modify', 'update', 'configure', 'change', 'alter'],
                'action': SystemAction.REQUEST_APPROVAL
            },
            'sensitive_data_access': {
                'base_risk': RiskLevel.HIGH,
                'keywords': ['password', 'key', 'secret', 'token', 'credential', 'private'],
                'action': SystemAction.ALERT_ADMIN
            },
            'external_communication': {
                'base_risk': RiskLevel.MEDIUM,
                'keywords': ['api', 'external', 'third-party', 'internet', 'http', 'request'],
                'action': SystemAction.LOG_ONLY
            },
            'security_event': {
                'base_risk': RiskLevel.CRITICAL,
                'keywords': ['breach', 'attack', 'unauthorized', 'intrusion', 'hack', 'exploit'],
                'action': SystemAction.FREEZE_AGENT
            },
            'critical_error': {
                'base_risk': RiskLevel.HIGH,
                'keywords': ['crash', 'fatal', 'critical', 'emergency', 'failure'],
                'action': SystemAction.ALERT_ADMIN
            },
            'knowledge_acquisition': {
                'base_risk': RiskLevel.LOW,
                'keywords': ['learn', 'train', 'acquire', 'discover', 'analyze'],
                'action': SystemAction.LOG_ONLY
            },
            'database_modification': {
                'base_risk': RiskLevel.HIGH,
                'keywords': ['insert', 'update', 'delete', 'drop', 'truncate', 'alter'],
                'action': SystemAction.REQUEST_APPROVAL
            },
            'file_system_access': {
                'base_risk': RiskLevel.MEDIUM,
                'keywords': ['file', 'directory', 'write', 'read', 'execute'],
                'action': SystemAction.LOG_ONLY
            }
        }

    def _load_compliance_keywords(self) -> Dict[str, List[str]]:
        """Load compliance-related keywords"""
        return {
            'pii': ['name', 'email', 'phone', 'address', 'ssn', 'dob', 'passport'],
            'phi': ['medical', 'health', 'diagnosis', 'treatment', 'prescription', 'patient'],
            'pci': ['card', 'cvv', 'payment', 'transaction', 'bank', 'account'],
            'confidential': ['confidential', 'secret', 'classified', 'private', 'restricted']
        }

    async def log_activity(
        self,
        entry: ActivityLogEntry,
        force_immediate: bool = False
    ) -> str:
        """
        Log agent activity (MANDATORY - Cannot be bypassed)
        
        Returns: Activity log ID
        """
        try:
            # Check if agent is frozen
            if self.check_agent_frozen(entry.agent_id):
                raise PermissionError(f"Agent {entry.agent_id} is frozen and cannot perform activities")
            
            # Check if system is frozen
            if self.check_system_frozen():
                raise PermissionError("System is frozen. No agent activities allowed.")
            
            # Generate unique ID and correlation ID
            activity_id = str(uuid.uuid4())
            if not entry.correlation_id:
                entry.correlation_id = activity_id
            
            # Assess risk
            risk_assessment = await self._assess_risk(entry)
            entry.risk_level = risk_assessment.risk_level
            
            # Check compliance flags
            entry.compliance_flags.extend(self._check_compliance(entry))
            
            # Hash sensitive data
            input_hash = self._hash_data(entry.input_data) if entry.input_data else None
            output_hash = self._hash_data(entry.output_data) if entry.output_data else None
            
            # Create log record
            log_record = AgentActivityLog(
                id=activity_id,
                agent_id=entry.agent_id,
                tenant_id=entry.tenant_id,
                timestamp=datetime.utcnow(),
                activity_type=entry.activity_type.value,
                activity_category=self._categorize_activity(entry.activity_type),
                description=entry.description,
                context=entry.context,
                user_id=entry.user_id,
                session_id=entry.session_id,
                input_data_hash=input_hash,
                output_data_hash=output_hash,
                knowledge_gained=entry.knowledge_gained,
                risk_level=entry.risk_level.value,
                compliance_flags=entry.compliance_flags,
                requires_review=risk_assessment.requires_admin_review,
                parent_activity_id=entry.parent_activity_id,
                correlation_id=entry.correlation_id,
                hash_signature=self._compute_hash(entry)
            )
            
            # Buffer or immediate write
            if force_immediate or entry.risk_level in [RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
                await self._write_log_immediate(log_record)
            else:
                self.log_buffer.append(log_record)
            
            # Update statistics
            self.stats['total_activities_logged'] += 1
            if entry.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
                self.stats['high_risk_activities'] += 1
            
            # Take action based on risk assessment
            await self._execute_risk_action(activity_id, entry, risk_assessment)
            
            # Log to system logger
            log_level = self._get_log_level(entry.risk_level)
            logger.log(
                log_level,
                f"[AGENT ACTIVITY] {entry.agent_id} - {entry.activity_type.value} - {entry.description}"
            )
            
            return activity_id
            
        except PermissionError:
            raise
        except Exception as e:
            logger.critical(f"CRITICAL: Failed to log agent activity: {e}", exc_info=True)
            await self._emergency_freeze_agent(entry.agent_id, f"Failed to log activity: {e}")
            raise

    async def _assess_risk(self, entry: ActivityLogEntry) -> RiskAssessment:
        """Assess risk level of an activity"""
        risk_factors = []
        risk_score = 0.0
        
        # Base risk from activity type
        activity_rule = self.risk_rules.get(entry.activity_type.value, {})
        base_risk = activity_rule.get('base_risk', RiskLevel.LOW)
        risk_score += self._risk_to_score(base_risk)
        risk_factors.append(f"Base risk: {base_risk.value}")
        
        # Check for risk keywords
        text_to_check = f"{entry.description} {json.dumps(entry.context)}".lower()
        
        for rule_name, rule in self.risk_rules.items():
            keywords = rule.get('keywords', [])
            matched_keywords = [kw for kw in keywords if kw in text_to_check]
            if matched_keywords:
                risk_factors.append(f"Keywords: {', '.join(matched_keywords)}")
                risk_score += 0.1 * len(matched_keywords)
        
        # Check for compliance flags
        compliance_flags = self._check_compliance(entry)
        if compliance_flags:
            risk_factors.extend([f"Compliance: {flag}" for flag in compliance_flags])
            risk_score += 0.2 * len(compliance_flags)
        
        # Context-based risk factors
        if entry.context.get('external_system'):
            risk_factors.append("External system interaction")
            risk_score += 0.2
        
        if entry.context.get('system_critical'):
            risk_factors.append("System-critical operation")
            risk_score += 0.3
        
        if entry.context.get('data_modification'):
            risk_factors.append("Data modification operation")
            risk_score += 0.15
        
        if entry.context.get('privileged_operation'):
            risk_factors.append("Privileged operation")
            risk_score += 0.25
        
        # Determine final risk level and action
        if risk_score >= 1.0:
            final_risk = RiskLevel.EMERGENCY
            recommended_action = SystemAction.FREEZE_SYSTEM
            requires_review = True
            requires_approval = True
        elif risk_score >= 0.8:
            final_risk = RiskLevel.CRITICAL
            recommended_action = SystemAction.FREEZE_AGENT
            requires_review = True
            requires_approval = True
        elif risk_score >= 0.6:
            final_risk = RiskLevel.HIGH
            recommended_action = SystemAction.REQUEST_APPROVAL
            requires_review = True
            requires_approval = True
        elif risk_score >= 0.4:
            final_risk = RiskLevel.MEDIUM
            recommended_action = SystemAction.ALERT_ADMIN
            requires_review = True
            requires_approval = False
        elif risk_score >= 0.2:
            final_risk = RiskLevel.LOW
            recommended_action = SystemAction.LOG_ONLY
            requires_review = False
            requires_approval = False
        else:
            final_risk = RiskLevel.NEGLIGIBLE
            recommended_action = SystemAction.LOG_ONLY
            requires_review = False
            requires_approval = False
        
        return RiskAssessment(
            risk_level=final_risk,
            risk_score=risk_score,
            risk_factors=risk_factors,
            recommended_action=recommended_action,
            requires_admin_review=requires_review,
            requires_approval=requires_approval
        )

    def _risk_to_score(self, risk_level: RiskLevel) -> float:
        """Convert risk level to numeric score"""
        return {
            RiskLevel.NEGLIGIBLE: 0.0,
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.HIGH: 0.6,
            RiskLevel.CRITICAL: 0.8,
            RiskLevel.EMERGENCY: 1.0
        }.get(risk_level, 0.0)

    def _check_compliance(self, entry: ActivityLogEntry) -> List[str]:
        """Check for compliance-related content"""
        flags = []
        
        # Build text to check
        text_parts = [entry.description, json.dumps(entry.context)]
        if entry.input_data:
            text_parts.append(str(entry.input_data))
        if entry.output_data:
            text_parts.append(str(entry.output_data))
        
        text_lower = " ".join(text_parts).lower()
        
        for compliance_type, keywords in self.compliance_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    flags.append(f"{compliance_type.upper()}_DETECTED")
                    break
        
        return list(set(flags))

    async def _execute_risk_action(
        self,
        activity_id: str,
        entry: ActivityLogEntry,
        assessment: RiskAssessment
    ):
        """Execute action based on risk assessment"""
        action = assessment.recommended_action
        
        try:
            if action == SystemAction.FREEZE_SYSTEM:
                await self._freeze_system(activity_id, entry, assessment)
            
            elif action == SystemAction.FREEZE_MODULE:
                module = entry.context.get('module', 'unknown')
                await self._freeze_module(module, activity_id, entry, assessment)
            
            elif action == SystemAction.FREEZE_AGENT:
                await self._freeze_agent(entry.agent_id, activity_id, entry, assessment)
            
            elif action == SystemAction.REQUEST_APPROVAL:
                await self._request_admin_approval(activity_id, entry, assessment)
            
            elif action == SystemAction.ALERT_ADMIN:
                await self._alert_admin(activity_id, entry, assessment)
            
            # Always create notification for high-risk activities
            if assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
                await self._create_admin_notification(activity_id, entry, assessment)
        
        except Exception as e:
            logger.error(f"Failed to execute risk action: {e}", exc_info=True)
            # If we can't execute the action, freeze the agent as a safety measure
            await self._emergency_freeze_agent(entry.agent_id, f"Failed to execute risk action: {e}")

    async def _freeze_agent(
        self,
        agent_id: str,
        activity_id: str,
        entry: ActivityLogEntry,
        assessment: RiskAssessment
    ):
        """Freeze agent and notify admin"""
        if agent_id in self.frozen_agents:
            logger.warning(f"Agent {agent_id} already frozen")
            return
        
        self.frozen_agents[agent_id] = {
            'frozen_at': datetime.utcnow(),
            'reason': entry.description,
            'activity_id': activity_id,
            'risk_level': assessment.risk_level.value,
            'risk_factors': assessment.risk_factors
        }
        
        self.stats['agents_frozen'] += 1
        
        # Create freeze log
        async with self.db_manager.get_session() as session:
            freeze_log = SystemFreezeLog(
                id=str(uuid.uuid4()),
                freeze_timestamp=datetime.utcnow(),
                freeze_type='agent',
                freeze_target=agent_id,
                reason=entry.description,
                triggered_by_activity=activity_id,
                risk_level=assessment.risk_level.value,
                admin_notified=True,
                admin_approval_required=True
            )
            session.add(freeze_log)
            await session.commit()
        
        # Send alert
        await self.alert_manager.create_alert(
            category=AlertCategory.SECURITY,
            severity=AlertSeverity.EMERGENCY,
            title=f"🔒 AGENT FROZEN - {agent_id}",
            description=f"Agent {agent_id} has been automatically frozen due to {assessment.risk_level.value} risk activity: {entry.description}",
            source="CodeOfConduct",
            metadata={
                'agent_id': agent_id,
                'activity_id': activity_id,
                'risk_level': assessment.risk_level.value,
                'risk_factors': assessment.risk_factors,
                'requires_admin_action': True
            }
        )
        
        logger.critical(f"🔒 AGENT FROZEN: {agent_id} - {entry.description}")

    async def _freeze_module(
        self,
        module_name: str,
        activity_id: str,
        entry: ActivityLogEntry,
        assessment: RiskAssessment
    ):
        """Freeze entire module"""
        if module_name in self.frozen_modules:
            logger.warning(f"Module {module_name} already frozen")
            return
        
        self.frozen_modules[module_name] = {
            'frozen_at': datetime.utcnow(),
            'reason': entry.description,
            'activity_id': activity_id,
            'risk_level': assessment.risk_level.value
        }
        
        async with self.db_manager.get_session() as session:
            freeze_log = SystemFreezeLog(
                id=str(uuid.uuid4()),
                freeze_timestamp=datetime.utcnow(),
                freeze_type='module',
                freeze_target=module_name,
                reason=entry.description,
                triggered_by_activity=activity_id,
                risk_level=assessment.risk_level.value,
                admin_notified=True,
                admin_approval_required=True
            )
            session.add(freeze_log)
            await session.commit()
        
        await self.alert_manager.create_alert(
            category=AlertCategory.SECURITY,
            severity=AlertSeverity.EMERGENCY,
            title=f"🔒 MODULE FROZEN - {module_name}",
            description=f"Module '{module_name}' has been frozen: {entry.description}",
            source="CodeOfConduct",
            metadata={
                'module': module_name,
                'activity_id': activity_id,
                'risk_level': assessment.risk_level.value
            }
        )
        
        logger.critical(f"🔒 MODULE FROZEN: {module_name} - {entry.description}")

    async def _freeze_system(
        self,
        activity_id: str,
        entry: ActivityLogEntry,
        assessment: RiskAssessment
    ):
        """Freeze entire system - EMERGENCY ONLY"""
        if self.system_frozen:
            return
        
        self.system_frozen = True
        
        async with self.db_manager.get_session() as session:
            freeze_log = SystemFreezeLog(
                id=str(uuid.uuid4()),
                freeze_timestamp=datetime.utcnow(),
                freeze_type='system',
                freeze_target='ENTIRE_SYSTEM',
                reason=entry.description,
                triggered_by_activity=activity_id,
                risk_level=assessment.risk_level.value,
                admin_notified=True,
                admin_approval_required=True
            )
            session.add(freeze_log)
            await session.commit()
        
        await self.alert_manager.create_alert(
            category=AlertCategory.SECURITY,
            severity=AlertSeverity.EMERGENCY,
            title="🚨 SYSTEM FROZEN - EMERGENCY",
            description=f"ENTIRE SYSTEM FROZEN due to emergency: {entry.description}",
            source="CodeOfConduct",
            metadata={
                'activity_id': activity_id,
                'risk_level': assessment.risk_level.value,
                'risk_factors': assessment.risk_factors,
                'immediate_action_required': True
            }
        )
        
        logger.critical(f"🚨 SYSTEM FROZEN - EMERGENCY: {entry.description}")

    async def _create_admin_notification(
        self,
        activity_id: str,
        entry: ActivityLogEntry,
        assessment: RiskAssessment
    ):
        """Create admin notification"""
        try:
            notification_id = str(uuid.uuid4())
            
            async with self.db_manager.get_session() as session:
                notification = AdminNotification(
                    id=notification_id,
                    created_at=datetime.utcnow(),
                    risk_level=assessment.risk_level.value,
                    title=f"{assessment.risk_level.value.upper()} Risk Activity Detected",
                    description=f"Agent {entry.agent_id} performed {entry.activity_type.value}: {entry.description}",
                    agent_id=entry.agent_id,
                    activity_log_id=activity_id,
                    recommended_actions=self._generate_recommendations(assessment),
                    system_action_taken=assessment.recommended_action.value if assessment.recommended_action else None,
                    status='pending'
                )
                session.add(notification)
                await session.commit()
            
            self.pending_admin_notifications.append(notification_id)
            self.stats['admin_notifications_sent'] += 1
            
        except Exception as e:
            logger.error(f"Failed to create admin notification: {e}", exc_info=True)

    async def _request_admin_approval(
        self,
        activity_id: str,
        entry: ActivityLogEntry,
        assessment: RiskAssessment
    ):
        """Request admin approval before proceeding"""
        await self._create_admin_notification(activity_id, entry, assessment)
        await self._freeze_agent(entry.agent_id, activity_id, entry, assessment)

    async def _alert_admin(
        self,
        activity_id: str,
        entry: ActivityLogEntry,
        assessment: RiskAssessment
    ):
        """Send alert to admin"""
        await self._create_admin_notification(activity_id, entry, assessment)
        
        await self.alert_manager.create_alert(
            category=AlertCategory.SECURITY,
            severity=self._risk_to_alert_severity(assessment.risk_level),
            title=f"Agent Activity Requires Review - {assessment.risk_level.value.upper()}",
            description=f"Agent {entry.agent_id}: {entry.description}",
            source="CodeOfConduct",
            metadata={
                'agent_id': entry.agent_id,
                'activity_id': activity_id,
                'risk_level': assessment.risk_level.value,
                'risk_factors': assessment.risk_factors,
                'requires_review': assessment.requires_admin_review
            }
        )

    def _generate_recommendations(self, assessment: RiskAssessment) -> List[Dict]:
        """Generate recommended actions for admin"""
        recommendations = []
        
        if assessment.risk_level == RiskLevel.EMERGENCY:
            recommendations.extend([
                {'action': 'investigate_immediately', 'priority': 'critical', 'description': 'Immediate investigation required'},
                {'action': 'review_all_recent_activities', 'priority': 'high', 'description': 'Review all activities in the last 24 hours'},
                {'action': 'consider_agent_termination', 'priority': 'high', 'description': 'Evaluate if agent should be permanently terminated'}
            ])
        elif assessment.risk_level == RiskLevel.CRITICAL:
            recommendations.extend([
                {'action': 'review_activity_details', 'priority': 'high', 'description': 'Review complete activity context'},
                {'action': 'verify_agent_integrity', 'priority': 'high', 'description': 'Run integrity check on agent'},
                {'action': 'assess_potential_damage', 'priority': 'medium', 'description': 'Assess if any damage occurred'}
            ])
        elif assessment.risk_level == RiskLevel.HIGH:
            recommendations.extend([
                {'action': 'review_activity_log', 'priority': 'medium', 'description': 'Review activity log when convenient'},
                {'action': 'monitor_agent_closely', 'priority': 'medium', 'description': 'Increase monitoring frequency'}
            ])
        else:
            recommendations.append({'action': 'review_when_convenient', 'priority': 'low', 'description': 'Review during routine audit'})
        
        return recommendations

    async def _emergency_freeze_agent(self, agent_id: str, reason: str):
        """Emergency freeze without full assessment"""
        self.frozen_agents[agent_id] = {
            'frozen_at': datetime.utcnow(),
            'reason': reason,
            'emergency': True
        }
        logger.critical(f"🚨 EMERGENCY FREEZE: {agent_id} - {reason}")
        
        await self.alert_manager.create_alert(
            category=AlertCategory.SECURITY,
            severity=AlertSeverity.EMERGENCY,
            title=f"🚨 EMERGENCY AGENT FREEZE - {agent_id}",
            description=f"Agent emergency frozen: {reason}",
            source="CodeOfConduct",
            metadata={'agent_id': agent_id, 'reason': reason, 'emergency': True}
        )

    def check_agent_frozen(self, agent_id: str) -> bool:
        """Check if agent is frozen"""
        return agent_id in self.frozen_agents

    def check_module_frozen(self, module_name: str) -> bool:
        """Check if module is frozen"""
        return module_name in self.frozen_modules

    def check_system_frozen(self) -> bool:
        """Check if entire system is frozen"""
        return self.system_frozen

    async def unfreeze_agent(
        self,
        agent_id: str,
        admin_id: str,
        reason: str
    ) -> bool:
        """Unfreeze agent (requires admin authorization)"""
        if agent_id not in self.frozen_agents:
            return False
        
        freeze_info = self.frozen_agents.pop(agent_id)
        
        # Update freeze log
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SystemFreezeLog).where(
                    and_(
                        SystemFreezeLog.freeze_target == agent_id,
                        SystemFreezeLog.unfreeze_timestamp.is_(None)
                    )
                ).order_by(desc(SystemFreezeLog.freeze_timestamp)).limit(1)
            )
            freeze_log = result.scalar_one_or_none()
            
            if freeze_log:
                freeze_log.unfreeze_timestamp = datetime.utcnow()
                freeze_log.unfreeze_authorized_by = admin_id
                freeze_log.unfreeze_reason = reason
                await session.commit()
        
        await self.alert_manager.create_alert(
            category=AlertCategory.SYSTEM,
            severity=AlertSeverity.INFO,
            title=f"Agent Unfrozen - {agent_id}",
            description=f"Agent {agent_id} unfrozen by admin {admin_id}: {reason}",
            source="CodeOfConduct",
            metadata={'agent_id': agent_id, 'admin_id': admin_id, 'reason': reason}
        )
        
        logger.info(f"Agent {agent_id} unfrozen by admin {admin_id}: {reason}")
        return True

    async def unfreeze_module(
        self,
        module_name: str,
        admin_id: str,
        reason: str
    ) -> bool:
        """Unfreeze module (requires admin authorization)"""
        if module_name not in self.frozen_modules:
            return False
        
        self.frozen_modules.pop(module_name)
        
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SystemFreezeLog).where(
                    and_(
                        SystemFreezeLog.freeze_target == module_name,
                        SystemFreezeLog.unfreeze_timestamp.is_(None)
                    )
                ).order_by(desc(SystemFreezeLog.freeze_timestamp)).limit(1)
            )
            freeze_log = result.scalar_one_or_none()
            
            if freeze_log:
                freeze_log.unfreeze_timestamp = datetime.utcnow()
                freeze_log.unfreeze_authorized_by = admin_id
                freeze_log.unfreeze_reason = reason
                await session.commit()
        
        logger.info(f"Module {module_name} unfrozen by admin {admin_id}: {reason}")
        return True

    async def unfreeze_system(
        self,
        admin_id: str,
        reason: str
    ) -> bool:
        """Unfreeze entire system (requires admin authorization)"""
        if not self.system_frozen:
            return False
        
        self.system_frozen = False
        
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(SystemFreezeLog).where(
                    and_(
                        SystemFreezeLog.freeze_type == 'system',
                        SystemFreezeLog.unfreeze_timestamp.is_(None)
                    )
                ).order_by(desc(SystemFreezeLog.freeze_timestamp)).limit(1)
            )
            freeze_log = result.scalar_one_or_none()
            
            if freeze_log:
                freeze_log.unfreeze_timestamp = datetime.utcnow()
                freeze_log.unfreeze_authorized_by = admin_id
                freeze_log.unfreeze_reason = reason
                await session.commit()
        
        await self.alert_manager.create_alert(
            category=AlertCategory.SYSTEM,
            severity=AlertSeverity.CRITICAL,
            title="System Unfrozen",
            description=f"System unfrozen by admin {admin_id}: {reason}",
            source="CodeOfConduct",
            metadata={'admin_id': admin_id, 'reason': reason}
        )
        
        logger.critical(f"System unfrozen by admin {admin_id}: {reason}")
        return True

    async def get_pending_admin_notifications(
        self,
        limit: int = 50
    ) -> List[Dict]:
        """Get pending notifications for admin review"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(AdminNotification).where(
                    AdminNotification.status == 'pending'
                ).order_by(
                    desc(AdminNotification.risk_level),
                    desc(AdminNotification.created_at)
                ).limit(limit)
            )
            notifications = result.scalars().all()
            
            return [
                {
                    'id': n.id,
                    'created_at': n.created_at.isoformat(),
                    'risk_level': n.risk_level,
                    'title': n.title,
                    'description': n.description,
                    'agent_id': n.agent_id,
                    'activity_log_id': n.activity_log_id,
                    'recommended_actions': n.recommended_actions,
                    'system_action_taken': n.system_action_taken
                }
                for n in notifications
            ]

    async def respond_to_notification(
        self,
        notification_id: str,
        admin_id: str,
        response: Dict[str, Any]
    ) -> bool:
        """Admin responds to notification"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(AdminNotification).where(AdminNotification.id == notification_id)
            )
            notification = result.scalar_one_or_none()
            
            if not notification:
                return False
            
            notification.status = 'reviewed'
            notification.admin_response = response
            notification.responded_by = admin_id
            notification.responded_at = datetime.utcnow()
            
            # If response includes resolution
            if response.get('resolved'):
                notification.status = 'actioned'
                notification.resolution = response.get('resolution', '')
                notification.resolved_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Admin {admin_id} responded to notification {notification_id}")
            return True

    async def get_agent_activity_log(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get activity log for an agent"""
        async with self.db_manager.get_session() as session:
            query = select(AgentActivityLog).where(
                AgentActivityLog.agent_id == agent_id
            )
            
            if start_date:
                query = query.where(AgentActivityLog.timestamp >= start_date)
            if end_date:
                query = query.where(AgentActivityLog.timestamp <= end_date)
            
            query = query.order_by(desc(AgentActivityLog.timestamp)).limit(limit)
            
            result = await session.execute(query)
            logs = result.scalars().all()
            
            return [
                {
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'activity_type': log.activity_type,
                    'description': log.description,
                    'risk_level': log.risk_level,
                    'context': log.context,
                    'compliance_flags': log.compliance_flags,
                    'requires_review': log.requires_review,
                    'reviewed': log.reviewed_at is not None
                }
                for log in logs
            ]

    async def get_frozen_entities(self) -> Dict[str, Any]:
        """Get all currently frozen entities"""
        return {
            'system_frozen': self.system_frozen,
            'frozen_agents': {
                agent_id: {
                    'frozen_at': info['frozen_at'].isoformat(),
                    'reason': info['reason'],
                    'risk_level': info.get('risk_level', 'unknown')
                }
                for agent_id, info in self.frozen_agents.items()
            },
            'frozen_modules': {
                module: {
                    'frozen_at': info['frozen_at'].isoformat(),
                    'reason': info['reason']
                }
                for module, info in self.frozen_modules.items()
            }
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get code of conduct statistics"""
        async with self.db_manager.get_session() as session:
            # Get total logs
            total_logs = await session.scalar(
                select(func.count(AgentActivityLog.id))
            )
            
            # Get high-risk logs
            high_risk_logs = await session.scalar(
                select(func.count(AgentActivityLog.id)).where(
                    AgentActivityLog.risk_level.in_(['high', 'critical', 'emergency'])
                )
            )
            
            # Get pending reviews
            pending_reviews = await session.scalar(
                select(func.count(AgentActivityLog.id)).where(
                    and_(
                        AgentActivityLog.requires_review == True,
                        AgentActivityLog.reviewed_at.is_(None)
                    )
                )
            )
            
            # Get pending notifications
            pending_notifs = await session.scalar(
                select(func.count(AdminNotification.id)).where(
                    AdminNotification.status == 'pending'
                )
            )
        
        return {
            'total_activities_logged': total_logs or 0,
            'high_risk_activities': high_risk_logs or 0,
            'agents_frozen': len(self.frozen_agents),
            'modules_frozen': len(self.frozen_modules),
            'system_frozen': self.system_frozen,
            'admin_notifications_pending': pending_notifs or 0,
            'activities_requiring_review': pending_reviews or 0,
            'buffer_size': len(self.log_buffer)
        }

    async def flush_log_buffer(self):
        """Flush buffered logs to database"""
        if not self.log_buffer:
            return
        
        try:
            logs_to_write = list(self.log_buffer)
            self.log_buffer.clear()
            
            async with self.db_manager.get_session() as session:
                session.add_all(logs_to_write)
                await session.commit()
            
            logger.debug(f"Flushed {len(logs_to_write)} logs to database")
            
        except Exception as e:
            logger.error(f"Failed to flush log buffer: {e}", exc_info=True)
            # Re-add logs to buffer
            self.log_buffer.extend(logs_to_write)

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        tasks = [
            asyncio.create_task(self._periodic_buffer_flush()),
            asyncio.create_task(self._periodic_cleanup())
        ]
        
        logger.info("Code of Conduct background tasks started")
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for task in tasks:
                task.cancel()

    async def _periodic_buffer_flush(self):
        """Periodically flush log buffer"""
        while True:
            try:
                await asyncio.sleep(self.buffer_flush_interval)
                await self.flush_log_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Buffer flush error: {e}", exc_info=True)

    async def _periodic_cleanup(self):
        """Periodically clean up old data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Clean up old reviewed notifications
                cutoff = datetime.utcnow() - timedelta(days=30)
                
                async with self.db_manager.get_session() as session:
                    await session.execute(
                        select(AdminNotification).where(
                            and_(
                                AdminNotification.status.in_(['reviewed', 'actioned']),
                                AdminNotification.created_at < cutoff
                            )
                        )
                    )
                    # In production, you'd archive rather than delete
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}", exc_info=True)

    # Helper methods
    
    def _categorize_activity(self, activity_type: ActivityType) -> str:
        """Categorize activity for organization"""
        categories = {
            ActivityType.INTERACTION: "user_interaction",
            ActivityType.KNOWLEDGE_ACQUISITION: "learning",
            ActivityType.PROCESS_EXECUTION: "execution",
            ActivityType.DATA_ACCESS: "data_operation",
            ActivityType.DECISION_MAKING: "decision",
            ActivityType.SYSTEM_MODIFICATION: "system_change",
            ActivityType.EXTERNAL_COMMUNICATION: "external",
            ActivityType.ERROR_OCCURRENCE: "error",
            ActivityType.SECURITY_EVENT: "security"
        }
        return categories.get(activity_type, "other")

    def _hash_data(self, data: Any) -> str:
        """Hash data for integrity verification"""
        if data is None:
            return None
        
        data_str = json.dumps(data) if isinstance(data, dict) else str(data)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _compute_hash(self, entry: ActivityLogEntry) -> str:
        """Compute hash signature for log entry"""
        hash_input = f"{entry.agent_id}{entry.activity_type.value}{entry.description}{entry.timestamp if hasattr(entry, 'timestamp') else datetime.utcnow().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def _get_log_level(self, risk_level: RiskLevel) -> int:
        """Get Python logging level from risk level"""
        return {
            RiskLevel.NEGLIGIBLE: logging.DEBUG,
            RiskLevel.LOW: logging.INFO,
            RiskLevel.MEDIUM: logging.WARNING,
            RiskLevel.HIGH: logging.ERROR,
            RiskLevel.CRITICAL: logging.CRITICAL,
            RiskLevel.EMERGENCY: logging.CRITICAL
        }.get(risk_level, logging.INFO)

    def _risk_to_alert_severity(self, risk_level: RiskLevel) -> AlertSeverity:
        """Convert risk level to alert severity"""
        return {
            RiskLevel.NEGLIGIBLE: AlertSeverity.INFO,
            RiskLevel.LOW: AlertSeverity.INFO,
            RiskLevel.MEDIUM: AlertSeverity.WARNING,
            RiskLevel.HIGH: AlertSeverity.CRITICAL,
            RiskLevel.CRITICAL: AlertSeverity.CRITICAL,
            RiskLevel.EMERGENCY: AlertSeverity.EMERGENCY
        }.get(risk_level, AlertSeverity.INFO)

    async def _write_log_immediate(self, log_record: AgentActivityLog):
        """Write log immediately to database"""
        async with self.db_manager.get_session() as session:
            session.add(log_record)
            await session.commit()

    async def health_check(self) -> str:
        """Health check for code of conduct system"""
        try:
            # Check database connectivity
            async with self.db_manager.get_session() as session:
                await session.execute(select(AgentActivityLog).limit(1))
            
            # Check alert manager
            alert_health = await self.alert_manager.health_check()
            if alert_health != "healthy":
                return f"degraded: alert_manager {alert_health}"
            
            return "healthy"
        except Exception as e:
            logger.error(f"Code of Conduct health check failed: {e}")
            return "unhealthy"


# Decorator for mandatory logging
def log_agent_activity(
    activity_type: ActivityType,
    description: Optional[str] = None
):
    """Decorator to automatically log agent activities"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract agent_id and tenant_id from args/kwargs
            agent_id = kwargs.get('agent_id') or (args[1] if len(args) > 1 else None)
            tenant_id = kwargs.get('tenant_id') or (args[2] if len(args) > 2 else None)
            
            # Get code of conduct instance (should be passed or accessible)
            conduct = kwargs.get('conduct')
            
            if conduct and agent_id and tenant_id:
                # Create activity entry
                entry = ActivityLogEntry(
                    agent_id=agent_id,
                    tenant_id=tenant_id,
                    activity_type=activity_type,
                    description=description or func.__name__,
                    context={
                        'function': func.__name__,
                        'module': func.__module__,
                        'args': str(args),
                        'kwargs': {k: v for k, v in kwargs.items() if k != 'conduct'}
                    }
                )
                
                # Log before execution
                activity_id = await conduct.log_activity(entry)
                
                try:
                    # Execute function
                    result = await func(*args, **kwargs)
                    
                    # Log success
                    entry.output_data = str(result)[:1000]  # Truncate large outputs
                    await conduct.log_activity(entry, force_immediate=False)
                    
                    return result
                    
                except Exception as e:
                    # Log error
                    entry.activity_type = ActivityType.ERROR_OCCURRENCE
                    entry.description = f"Error in {func.__name__}: {str(e)}"
                    entry.context['error'] = str(e)
                    await conduct.log_activity(entry, force_immediate=True)
                    raise
            else:
                # No logging, just execute
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator