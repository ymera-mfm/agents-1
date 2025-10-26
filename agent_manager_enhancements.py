"""
Enhanced Agent Manager Components for YMERA Enterprise Multi-Agent System
Focuses on mandatory reporting, lifecycle control, security and monitoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
import uuid

# Structured logging setup
logger = logging.getLogger(__name__)

class AgentReportStatus(Enum):
    """Enhanced agent reporting status tracking"""
    COMPLIANT = "compliant"         # Agent is reporting as required
    WARNED = "warned"               # Agent missed reports but within grace period
    SUSPENDED = "suspended"         # Agent missed too many reports, temporarily suspended
    NON_COMPLIANT = "non_compliant" # Agent consistently fails to report
    EXEMPT = "exempt"               # Agent exempt from reporting requirements

class AgentAction(Enum):
    """Agent lifecycle control actions"""
    WARN = "warn"           # Send warning to agent
    FREEZE = "freeze"       # Temporarily freeze agent activities
    UNFREEZE = "unfreeze"   # Resume agent activities
    DELETE = "delete"       # Permanently delete agent
    AUDIT = "audit"         # Trigger security audit of agent
    ISOLATE = "isolate"     # Network isolate the agent

class AdminApproval(Enum):
    """Admin approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"

class MandatoryReportingEnforcer:
    """Enhanced mandatory reporting enforcement with escalating consequences"""
    
    def __init__(self, db_manager, message_bus, notification_manager):
        self.db_manager = db_manager
        self.message_bus = message_bus
        self.notification_manager = notification_manager
        
        # Reporting configuration
        self.reporting_frequency = timedelta(minutes=5)  # Required reporting interval
        self.warning_threshold = 3    # Missed reports before warning
        self.suspend_threshold = 5    # Missed reports before suspension
        self.non_compliant_threshold = 10  # Missed reports before non-compliance
        
        # Track reporting status
        self.agent_reporting_status = {}  # agent_id -> AgentReportStatus
        self.missed_reports = {}          # agent_id -> count
        self.last_reports = {}            # agent_id -> datetime
        
        logger.info("Mandatory reporting enforcer initialized with thresholds: "
                   f"warning={self.warning_threshold}, suspend={self.suspend_threshold}, "
                   f"non_compliant={self.non_compliant_threshold}")
    
    async def start_monitoring(self):
        """Start background monitoring of agent reports"""
        logger.info("Starting mandatory reporting monitoring")
        while True:
            try:
                await self._check_all_agents()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in reporting monitor: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error
    
    async def _check_all_agents(self):
        """Check reporting compliance for all active agents"""
        now = datetime.utcnow()
        
        # Get all active agents
        async with self.db_manager.get_session() as session:
            result = await session.execute("""
                SELECT id, last_heartbeat, status, reporting_exemption 
                FROM agents
                WHERE status != 'deleted'
            """)
            
            agents = result.fetchall()
            
        for agent_id, last_heartbeat, status, exemption in agents:
            # Skip exempt agents
            if exemption:
                self.agent_reporting_status[agent_id] = AgentReportStatus.EXEMPT
                continue
                
            # Calculate time since last report
            if last_heartbeat:
                time_since_report = now - last_heartbeat
                overdue = time_since_report > self.reporting_frequency
            else:
                # No heartbeat recorded yet
                overdue = True
            
            # Update missed reports counter
            if overdue:
                self.missed_reports[agent_id] = self.missed_reports.get(agent_id, 0) + 1
            else:
                # Reset counter if agent reported on time
                self.missed_reports[agent_id] = 0
                self.agent_reporting_status[agent_id] = AgentReportStatus.COMPLIANT
            
            # Apply escalating consequences
            await self._enforce_reporting_compliance(agent_id)
    
    async def _enforce_reporting_compliance(self, agent_id: str):
        """Apply escalating consequences for non-reporting agents"""
        missed = self.missed_reports.get(agent_id, 0)
        
        if missed >= self.non_compliant_threshold:
            # Agent is severely non-compliant
            if self.agent_reporting_status.get(agent_id) != AgentReportStatus.NON_COMPLIANT:
                self.agent_reporting_status[agent_id] = AgentReportStatus.NON_COMPLIANT
                await self._handle_non_compliant_agent(agent_id)
                
        elif missed >= self.suspend_threshold:
            # Agent needs suspension
            if self.agent_reporting_status.get(agent_id) != AgentReportStatus.SUSPENDED:
                self.agent_reporting_status[agent_id] = AgentReportStatus.SUSPENDED
                await self._suspend_agent(agent_id)
                
        elif missed >= self.warning_threshold:
            # Agent needs warning
            if self.agent_reporting_status.get(agent_id) != AgentReportStatus.WARNED:
                self.agent_reporting_status[agent_id] = AgentReportStatus.WARNED
                await self._warn_agent(agent_id)
    
    async def _warn_agent(self, agent_id: str):
        """Send warning to agent about missed reports"""
        logger.warning(f"Agent {agent_id} has missed {self.missed_reports[agent_id]} reports - sending warning")
        
        # Send warning message to agent
        await self.message_bus.publish(
            f"agent.{agent_id}.control",
            {
                "type": "warning",
                "reason": "missed_reports",
                "count": self.missed_reports[agent_id],
                "timestamp": datetime.utcnow().isoformat(),
                "action_required": "resume_reporting"
            }
        )
        
        # Notify admin
        await self.notification_manager.send_notification(
            "admin",
            {
                "type": "agent_warning",
                "title": f"Agent {agent_id} reporting warning",
                "message": f"Agent has missed {self.missed_reports[agent_id]} required reports",
                "severity": "medium"
            }
        )
    
    async def _suspend_agent(self, agent_id: str):
        """Temporarily suspend non-reporting agent"""
        logger.warning(f"Agent {agent_id} has missed {self.missed_reports[agent_id]} reports - suspending")
        
        # Update agent status in database
        async with self.db_manager.get_session() as session:
            await session.execute(
                "UPDATE agents SET status = 'suspended', suspended_reason = 'missed_reports', "
                "suspended_at = :now WHERE id = :agent_id",
                {"now": datetime.utcnow(), "agent_id": agent_id}
            )
            await session.commit()
        
        # Send suspension message to agent
        await self.message_bus.publish(
            f"agent.{agent_id}.control",
            {
                "type": "control",
                "action": "suspend",
                "reason": "missed_reports",
                "count": self.missed_reports[agent_id],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Notify admin
        await self.notification_manager.send_notification(
            "admin",
            {
                "type": "agent_suspended",
                "title": f"Agent {agent_id} suspended",
                "message": f"Agent automatically suspended after missing {self.missed_reports[agent_id]} reports",
                "severity": "high",
                "action_required": True
            }
        )
    
    async def _handle_non_compliant_agent(self, agent_id: str):
        """Handle severely non-compliant agent - requires admin intervention"""
        logger.error(f"Agent {agent_id} is non-compliant with {self.missed_reports[agent_id]} missed reports")
        
        # Create admin approval request for agent deletion
        approval_request_id = str(uuid.uuid4())
        
        async with self.db_manager.get_session() as session:
            await session.execute(
                "INSERT INTO admin_approvals (id, request_type, resource_id, resource_type, "
                "action, reason, requested_at, status) "
                "VALUES (:id, 'agent_action', :agent_id, 'agent', 'delete', "
                "'Non-compliant with reporting requirements', :now, 'pending')",
                {
                    "id": approval_request_id,
                    "agent_id": agent_id,
                    "now": datetime.utcnow()
                }
            )
            await session.commit()
        
        # Notify all admins of required action
        await self.notification_manager.send_notification(
            "admin",
            {
                "type": "approval_required",
                "title": "Agent Deletion Approval Required",
                "message": f"Agent {agent_id} is non-compliant with reporting requirements. "
                          f"Approval required for deletion.",
                "severity": "critical",
                "approval_id": approval_request_id,
                "action_required": True
            }
        )
    
    async def process_agent_report(self, agent_id: str, report: dict):
        """Process incoming agent report"""
        now = datetime.utcnow()
        
        # Update tracking
        self.last_reports[agent_id] = now
        self.missed_reports[agent_id] = 0
        
        # If agent was previously warned or suspended, update status
        if self.agent_reporting_status.get(agent_id) in [
            AgentReportStatus.WARNED, AgentReportStatus.SUSPENDED, AgentReportStatus.NON_COMPLIANT
        ]:
            # Reset status
            self.agent_reporting_status[agent_id] = AgentReportStatus.COMPLIANT
            
            # If suspended, attempt to restore
            if report.get("status") == "suspended":
                await self._request_unsuspend_agent(agent_id)
        
        # Store report in database
        async with self.db_manager.get_session() as session:
            await session.execute(
                "UPDATE agents SET last_heartbeat = :now, last_report = :report, "
                "health_status = :health, resource_usage = :resources WHERE id = :agent_id",
                {
                    "now": now,
                    "report": report,
                    "health": report.get("health_status", "unknown"),
                    "resources": report.get("resource_usage", {}),
                    "agent_id": agent_id
                }
            )
            await session.commit()
    
    async def _request_unsuspend_agent(self, agent_id: str):
        """Request admin approval to unsuspend agent"""
        approval_request_id = str(uuid.uuid4())
        
        async with self.db_manager.get_session() as session:
            await session.execute(
                "INSERT INTO admin_approvals (id, request_type, resource_id, resource_type, "
                "action, reason, requested_at, status) "
                "VALUES (:id, 'agent_action', :agent_id, 'agent', 'unsuspend', "
                "'Agent has resumed reporting', :now, 'pending')",
                {
                    "id": approval_request_id,
                    "agent_id": agent_id,
                    "now": datetime.utcnow()
                }
            )
            await session.commit()
        
        # Notify admin
        await self.notification_manager.send_notification(
            "admin",
            {
                "type": "approval_required",
                "title": "Agent Unsuspend Approval Required",
                "message": f"Agent {agent_id} has resumed reporting. Approve to unsuspend.",
                "severity": "medium",
                "approval_id": approval_request_id,
                "action_required": True
            }
        )


class AgentLifecycleManager:
    """Enhanced agent lifecycle control with admin approval workflow"""
    
    def __init__(self, db_manager, message_bus, notification_manager, security_manager):
        self.db_manager = db_manager
        self.message_bus = message_bus
        self.notification_manager = notification_manager
        self.security_manager = security_manager
        
        # Track pending actions
        self.pending_actions = {}  # agent_id -> List[action_request]
        
        logger.info("Agent lifecycle manager initialized")
    
    async def request_agent_action(self, agent_id: str, action: AgentAction, 
                                  reason: str, requested_by: str) -> str:
        """Request an action on an agent - requires admin approval"""
        
        # Validate action is allowed
        await self._validate_action_request(agent_id, action, requested_by)
        
        # Create admin approval request
        approval_request_id = str(uuid.uuid4())
        
        async with self.db_manager.get_session() as session:
            # Store request in database
            await session.execute(
                "INSERT INTO admin_approvals (id, request_type, resource_id, resource_type, "
                "action, reason, requested_by, requested_at, status) "
                "VALUES (:id, 'agent_action', :agent_id, 'agent', :action, "
                ":reason, :requested_by, :now, 'pending')",
                {
                    "id": approval_request_id,
                    "agent_id": agent_id,
                    "action": action.value,
                    "reason": reason,
                    "requested_by": requested_by,
                    "now": datetime.utcnow()
                }
            )
            await session.commit()
        
        # Track pending action
        if agent_id not in self.pending_actions:
            self.pending_actions[agent_id] = []
        self.pending_actions[agent_id].append(approval_request_id)
        
        # Notify admins
        await self.notification_manager.send_notification(
            "admin",
            {
                "type": "approval_required",
                "title": f"Agent {action.value.title()} Approval Required",
                "message": f"Request to {action.value} agent {agent_id}. Reason: {reason}",
                "severity": "high" if action == AgentAction.DELETE else "medium",
                "approval_id": approval_request_id,
                "action_required": True,
                "requested_by": requested_by
            }
        )
        
        # Log request
        logger.info(f"Agent action requested: {action.value} for agent {agent_id} "
                  f"by {requested_by}. Approval ID: {approval_request_id}")
        
        # Return approval request ID
        return approval_request_id
    
    async def _validate_action_request(self, agent_id: str, action: AgentAction, requested_by: str):
        """Validate that the requested action is allowed"""
        # Check if agent exists
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                "SELECT status, owner_id FROM agents WHERE id = :agent_id",
                {"agent_id": agent_id}
            )
            agent = result.fetchone()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Check if requester has permission (owner or admin)
            if agent[1] != requested_by:
                # Check if user is admin
                is_admin = await self.security_manager.user_has_role(requested_by, "admin")
                if not is_admin:
                    raise PermissionError(f"User {requested_by} does not have permission to {action.value} agent {agent_id}")
            
            # Check if action makes sense for current state
            current_status = agent[0]
            
            # Validate state transitions
            valid = True
            if action == AgentAction.FREEZE and current_status == "frozen":
                valid = False
            elif action == AgentAction.UNFREEZE and current_status != "frozen":
                valid = False
            elif action == AgentAction.DELETE and current_status == "deleted":
                valid = False
                
            if not valid:
                raise ValueError(f"Cannot {action.value} agent with status {current_status}")
    
    async def process_admin_approval(self, approval_id: str, decision: AdminApproval, 
                                   admin_id: str, notes: Optional[str] = None):
        """Process admin decision on agent action request"""
        async with self.db_manager.get_session() as session:
            # Get approval request details
            result = await session.execute(
                "SELECT resource_id, action, requested_by FROM admin_approvals "
                "WHERE id = :approval_id AND status = 'pending'",
                {"approval_id": approval_id}
            )
            approval = result.fetchone()
            
            if not approval:
                raise ValueError(f"Approval request {approval_id} not found or already processed")
            
            agent_id, action, requested_by = approval
            
            # Update approval status
            await session.execute(
                "UPDATE admin_approvals SET status = :status, processed_by = :admin_id, "
                "processed_at = :now, notes = :notes WHERE id = :approval_id",
                {
                    "status": decision.value,
                    "admin_id": admin_id,
                    "now": datetime.utcnow(),
                    "notes": notes,
                    "approval_id": approval_id
                }
            )
            await session.commit()
        
        # Handle decision
        if decision == AdminApproval.APPROVED:
            # Execute the approved action
            await self._execute_agent_action(agent_id, AgentAction(action), admin_id)
            
            # Notify requester
            await self.notification_manager.send_notification(
                requested_by,
                {
                    "type": "approval_decision",
                    "title": f"Agent {action} Request Approved",
                    "message": f"Your request to {action} agent {agent_id} has been approved.",
                    "severity": "medium",
                    "approval_id": approval_id
                }
            )
        
        elif decision == AdminApproval.REJECTED:
            # Notify requester
            await self.notification_manager.send_notification(
                requested_by,
                {
                    "type": "approval_decision",
                    "title": f"Agent {action} Request Rejected",
                    "message": f"Your request to {action} agent {agent_id} has been rejected. "
                            f"Notes: {notes or 'No additional information provided.'}",
                    "severity": "medium",
                    "approval_id": approval_id
                }
            )
        
        # Remove from pending actions
        if agent_id in self.pending_actions and approval_id in self.pending_actions[agent_id]:
            self.pending_actions[agent_id].remove(approval_id)
    
    async def _execute_agent_action(self, agent_id: str, action: AgentAction, approved_by: str):
        """Execute an approved agent action"""
        logger.info(f"Executing approved agent action: {action.value} for agent {agent_id}")
        
        # Update agent status in database
        async with self.db_manager.get_session() as session:
            if action == AgentAction.WARN:
                # No status change, just send warning
                pass
                
            elif action == AgentAction.FREEZE:
                await session.execute(
                    "UPDATE agents SET status = 'frozen', frozen_at = :now, "
                    "frozen_by = :approved_by WHERE id = :agent_id",
                    {"now": datetime.utcnow(), "approved_by": approved_by, "agent_id": agent_id}
                )
                
            elif action == AgentAction.UNFREEZE:
                await session.execute(
                    "UPDATE agents SET status = 'active', unfrozen_at = :now, "
                    "unfrozen_by = :approved_by WHERE id = :agent_id",
                    {"now": datetime.utcnow(), "approved_by": approved_by, "agent_id": agent_id}
                )
                
            elif action == AgentAction.DELETE:
                # Logical delete with audit trail
                await session.execute(
                    "UPDATE agents SET status = 'deleted', deleted_at = :now, "
                    "deleted_by = :approved_by WHERE id = :agent_id",
                    {"now": datetime.utcnow(), "approved_by": approved_by, "agent_id": agent_id}
                )
                
            elif action == AgentAction.AUDIT:
                await session.execute(
                    "UPDATE agents SET last_audit = :now, audited_by = :approved_by, "
                    "audit_in_progress = TRUE WHERE id = :agent_id",
                    {"now": datetime.utcnow(), "approved_by": approved_by, "agent_id": agent_id}
                )
                
            elif action == AgentAction.ISOLATE:
                await session.execute(
                    "UPDATE agents SET status = 'isolated', isolated_at = :now, "
                    "isolated_by = :approved_by WHERE id = :agent_id",
                    {"now": datetime.utcnow(), "approved_by": approved_by, "agent_id": agent_id}
                )
            
            # Create audit log entry
            await session.execute(
                "INSERT INTO audit_logs (event_type, resource_type, resource_id, action, "
                "performed_by, timestamp, details) VALUES ('agent_lifecycle', 'agent', "
                ":agent_id, :action, :performed_by, :now, :details)",
                {
                    "agent_id": agent_id,
                    "action": action.value,
                    "performed_by": approved_by,
                    "now": datetime.utcnow(),
                    "details": {
                        "approved_action": action.value,
                    }
                }
            )
            
            await session.commit()
        
        # Send control message to agent
        await self.message_bus.publish(
            f"agent.{agent_id}.control",
            {
                "type": "control",
                "action": action.value,
                "timestamp": datetime.utcnow().isoformat(),
                "approved_by": approved_by
            }
        )
        
        # For deletion, perform additional cleanup
        if action == AgentAction.DELETE:
            await self._cleanup_deleted_agent(agent_id)
    
    async def _cleanup_deleted_agent(self, agent_id: str):
        """Perform additional cleanup for deleted agent"""
        # Cancel any pending tasks
        async with self.db_manager.get_session() as session:
            await session.execute(
                "UPDATE tasks SET status = 'cancelled', cancelled_reason = 'agent_deleted', "
                "cancelled_at = :now WHERE agent_id = :agent_id AND status IN ('pending', 'running')",
                {"now": datetime.utcnow(), "agent_id": agent_id}
            )
            await session.commit()
        
        # Revoke any API keys
        await self.security_manager.revoke_agent_credentials(agent_id)
        
        # Unsubscribe from all topics
        await self.message_bus.unsubscribe_all(agent_id)


class EnhancedSecurityMonitor:
    """Enhanced security monitoring and enforcement"""
    
    def __init__(self, db_manager, message_bus, notification_manager, telemetry_manager):
        self.db_manager = db_manager
        self.message_bus = message_bus
        self.notification_manager = notification_manager
        self.telemetry_manager = telemetry_manager
        
        # Security thresholds
        self.consecutive_auth_failures_threshold = 5
        self.suspicious_activity_score_threshold = 0.7
        self.data_volume_threshold_mb = 50  # Alert on agents transferring >50MB data
        
        # Track security incidents
        self.auth_failures = {}  # agent_id -> count
        self.suspicious_activities = {}  # agent_id -> List[activity]
        
        logger.info("Enhanced security monitor initialized")
    
    async def start_monitoring(self):
        """Start security monitoring"""
        logger.info("Starting enhanced security monitoring")
        while True:
            try:
                await self._scan_for_security_anomalies()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in security monitoring: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes
    
    async def _scan_for_security_anomalies(self):
        """Scan system for security anomalies"""
        now = datetime.utcnow()
        lookback = now - timedelta(hours=1)
        
        async with self.db_manager.get_session() as session:
            # Check for authentication failures
            result = await session.execute(
                "SELECT agent_id, COUNT(*) as failure_count FROM security_events "
                "WHERE event_type = 'authentication_failure' AND timestamp > :lookback "
                "GROUP BY agent_id HAVING COUNT(*) >= :threshold",
                {"lookback": lookback, "threshold": self.consecutive_auth_failures_threshold}
            )
            
            for agent_id, failure_count in result:
                await self._handle_auth_failures(agent_id, failure_count)
            
            # Check for suspicious data access patterns
            result = await session.execute(
                "SELECT agent_id, operation_type, resource_path, COUNT(*) as access_count "
                "FROM access_logs WHERE timestamp > :lookback "
                "GROUP BY agent_id, operation_type, resource_path "
                "HAVING COUNT(*) > 100", # Unusual number of accesses to same resource
                {"lookback": lookback}
            )
            
            for agent_id, op_type, resource, count in result:
                await self._handle_suspicious_access(agent_id, op_type, resource, count)
            
            # Check for large data transfers
            result = await session.execute(
                "SELECT agent_id, SUM(data_size_bytes)/1048576 as total_mb FROM data_transfer_logs "
                "WHERE timestamp > :lookback GROUP BY agent_id "
                "HAVING SUM(data_size_bytes)/1048576 > :threshold",
                {"lookback": lookback, "threshold": self.data_volume_threshold_mb}
            )
            
            for agent_id, volume_mb in result:
                await self._handle_large_data_transfer(agent_id, volume_mb)
    
    async def _handle_auth_failures(self, agent_id: str, failure_count: int):
        """Handle suspicious authentication failures"""
        # Log security incident
        incident_id = str(uuid.uuid4())
        
        async with self.db_manager.get_session() as session:
            await session.execute(
                "INSERT INTO security_incidents (id, agent_id, incident_type, severity, "
                "detected_at, details, status) VALUES (:id, :agent_id, 'auth_failure', "
                "'high', :now, :details, 'open')",
                {
                    "id": incident_id,
                    "agent_id": agent_id,
                    "now": datetime.utcnow(),
                    "details": {
                        "failure_count": failure_count,
                        "detection": "consecutive_failures"
                    }
                }
            )
            await session.commit()
        
        # Notify security team
        await self.notification_manager.send_notification(
            "security",
            {
                "type": "security_incident",
                "title": f"Multiple Authentication Failures for Agent {agent_id}",
                "message": f"Detected {failure_count} consecutive authentication failures",
                "severity": "high",
                "incident_id": incident_id,
                "action_required": True
            }
        )
        
        # Request automatic agent freeze
        await self.agent_lifecycle_manager.request_agent_action(
            agent_id,
            AgentAction.FREEZE,
            f"Security incident: {failure_count} consecutive auth failures",
            "system"
        )
    
    async def _handle_suspicious_access(self, agent_id: str, op_type: str, 
                                      resource: str, access_count: int):
        """Handle suspicious resource access patterns"""
        incident_id = str(uuid.uuid4())
        
        async with self.db_manager.get_session() as session:
            await session.execute(
                "INSERT INTO security_incidents (id, agent_id, incident_type, severity, "
                "detected_at, details, status) VALUES (:id, :agent_id, 'suspicious_access', "
                "'medium', :now, :details, 'open')",
                {
                    "id": incident_id,
                    "agent_id": agent_id,
                    "now": datetime.utcnow(),
                    "details": {
                        "operation_type": op_type,
                        "resource": resource,
                        "access_count": access_count
                    }
                }
            )
            await session.commit()
        
        # Notify security team
        await self.notification_manager.send_notification(
            "security",
            {
                "type": "security_incident",
                "title": f"Suspicious Access Pattern for Agent {agent_id}",
                "message": f"Detected {access_count} {op_type} operations on {resource}",
                "severity": "medium",
                "incident_id": incident_id,
                "action_required": True
            }
        )
    
    async def _handle_large_data_transfer(self, agent_id: str, volume_mb: float):
        """Handle suspiciously large data transfers"""
        incident_id = str(uuid.uuid4())
        
        async with self.db_manager.get_session() as session:
            await session.execute(
                "INSERT INTO security_incidents (id, agent_id, incident_type, severity, "
                "detected_at, details, status) VALUES (:id, :agent_id, 'data_transfer', "
                "'high', :now, :details, 'open')",
                {
                    "id": incident_id,
                    "agent_id": agent_id,
                    "now": datetime.utcnow(),
                    "details": {
                        "volume_mb": volume_mb,
                        "threshold": self.data_volume_threshold_mb
                    }
                }
            )
            await session.commit()
        
        # Notify security team
        await self.notification_manager.send_notification(
            "security",
            {
                "type": "security_incident",
                "title": f"Large Data Transfer for Agent {agent_id}",
                "message": f"Agent transferred {volume_mb:.2f} MB of data (threshold: {self.data_volume_threshold_mb} MB)",
                "severity": "high",
                "incident_id": incident_id,
                "action_required": True
            }
        )
        
        # Request automatic agent audit
        await self.agent_lifecycle_manager.request_agent_action(
            agent_id,
            AgentAction.AUDIT,
            f"Security incident: Large data transfer ({volume_mb:.2f} MB)",
            "system"
        )

class DataFlowValidator:
    """Enhanced data flow validation and security"""
    
    def __init__(self, db_manager, security_manager):
        self.db_manager = db_manager
        self.security_manager = security_manager
        
        # Data flow rules
        self.allowed_patterns = {}  # endpoint -> allowed patterns
        self.sensitive_data_patterns = {}  # regex patterns for sensitive data
        
        # Load validation rules
        self._load_validation_rules()
        
        logger.info("Data flow validator initialized")
    
    def _load_validation_rules(self):
        """Load validation rules from configuration"""
        # Example validation rules - would load from secure storage in production
        self.allowed_patterns = {
            "agent.register": {
                "name": r"^[a-zA-Z0-9_\-\.]{3,50}$",
                "capabilities": r"^[a-zA-Z0-9_\-\.]{1,20}$"  # List items pattern
            },
            "task.create": {
                "name": r"^[a-zA-Z0-9_\-\.]{3,100}$",
                "parameters": None  # Complex validation in code
            }
        }
        
        # Sensitive data patterns
        self.sensitive_data_patterns = {
            "api_key": r"[a-zA-Z0-9]{20,64}",
            "password": r"password[\"']?\s*[:=]\s*[\"'][^\"']{8,}[\"']",
            "token": r"(bearer|jwt|auth|access)[_\-\s]?token[\"']?\s*[:=]\s*[\"'][a-zA-Z0-9\._\-]{20,}[\"']",
            "ssn": r"\d{3}[-\s]?\d{2}[-\s]?\d{4}",
            "credit_card": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}"
        }
    
    async def validate_data_flow(self, endpoint: str, data: Dict[str, Any], 
                               context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate data flow against rules"""
        # Check for allowed patterns
        if endpoint in self.allowed_patterns:
            patterns = self.allowed_patterns[endpoint]
            for field, pattern in patterns.items():
                if field in data:
                    if pattern and not self._validate_pattern(data[field], pattern):
                        return False, f"Invalid format for field: {field}"
        
        # Check for sensitive data leakage
        sensitive_data = self._detect_sensitive_data(data)
        if sensitive_data and not self._is_sensitive_data_allowed(endpoint, context):
            return False, f"Sensitive data detected: {', '.join(sensitive_data)}"
        
        # Apply custom validations
        result, message = await self._apply_custom_validations(endpoint, data, context)
        if not result:
            return False, message
        
        # Data passed validation
        return True, None
    
    def _validate_pattern(self, value: Any, pattern: str) -> bool:
        """Validate value against regex pattern"""
        import re
        
        if isinstance(value, str):
            return bool(re.match(pattern, value))
        elif isinstance(value, list):
            return all(bool(re.match(pattern, item)) for item in value if isinstance(item, str))
        elif isinstance(value, dict):
            # For dictionaries, patterns would need to be more complex
            return True
        else:
            return True  # Skip validation for other types
    
    def _detect_sensitive_data(self, data: Any) -> List[str]:
        """Detect sensitive data in input"""
        import re
        
        # Convert data to string for regex matching
        data_str = str(data)
        
        detected = []
        for data_type, pattern in self.sensitive_data_patterns.items():
            if re.search(pattern, data_str):
                detected.append(data_type)
        
        return detected
    
    def _is_sensitive_data_allowed(self, endpoint: str, context: Dict[str, Any]) -> bool:
        """Check if sensitive data is allowed for this endpoint"""
        # Allow sensitive data for authentication endpoints
        if endpoint.startswith("auth."):
            return True
        
        # Allow sensitive data for encrypted connections with proper authorization
        if context.get("connection_encrypted", False) and context.get("authenticated", False):
            return True
        
        return False
    
    async def _apply_custom_validations(self, endpoint: str, data: Dict[str, Any], 
                                      context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Apply custom validations for specific endpoints"""
        
        # Task creation validation
        if endpoint == "task.create":
            # Validate task parameters don't contain executable code
            if "parameters" in data:
                has_code = self._contains_executable_code(data["parameters"])
                if has_code:
                    return False, "Task parameters contain executable code"
                    
            # Validate task priority is appropriate for user role
            if "priority" in data and data["priority"] == "critical":
                user_id = context.get("user_id")
                if user_id:
                    has_permission = await self.security_manager.user_has_permission(
                        user_id, "create_critical_tasks"
                    )
                    if not has_permission:
                        return False, "User does not have permission to create critical tasks"
        
        # Agent registration validation
        elif endpoint == "agent.register":
            # Validate capabilities match allowed list
            if "capabilities" in data:
                for capability in data["capabilities"]:
                    if not await self.security_manager.is_capability_allowed(capability):
                        return False, f"Capability not allowed: {capability}"
        
        # All custom validations passed
        return True, None
    
    def _contains_executable_code(self, data: Any) -> bool:
        """Check if data contains patterns that might be executable code"""
        import re
        
        # Convert to string for pattern matching
        data_str = str(data)
        
        # Patterns that might indicate executable code
        code_patterns = [
            r"exec\s*\(", 
            r"eval\s*\(", 
            r"subprocess\.",
            r"os\.(system|popen|exec)",
            r"import\s+[a-zA-Z_][a-zA-Z0-9_]*",
            r"require\s*\(",
            r"<script>",
            r"function\s*\(",
            r"setTimeout\s*\(",
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, data_str):
                return True
        
        return False


class EnhancedAuditSystem:
    """Enhanced audit logging and compliance tracking"""
    
    def __init__(self, db_manager, telemetry_manager):
        self.db_manager = db_manager
        self.telemetry_manager = telemetry_manager
        logger.info("Enhanced audit system initialized")
    
    async def log_audit_event(self, event_type: str, resource_type: str, 
                           resource_id: str, action: str, performed_by: str, 
                           details: Dict[str, Any]) -> str:
        """Log a comprehensive audit event with full context"""
        audit_id = str(uuid.uuid4())
        
        async with self.db_manager.get_session() as session:
            await session.execute(
                "INSERT INTO audit_logs (id, event_type, resource_type, resource_id, "
                "action, performed_by, timestamp, details) "
                "VALUES (:id, :event_type, :resource_type, :resource_id, :action, "
                ":performed_by, :timestamp, :details)",
                {
                    "id": audit_id,
                    "event_type": event_type,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "action": action,
                    "performed_by": performed_by,
                    "timestamp": datetime.utcnow(),
                    "details": details
                }
            )
            await session.commit()
        
        # Send audit event to telemetry for real-time monitoring
        await self.telemetry_manager.record_audit_event({
            "audit_id": audit_id,
            "event_type": event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "performed_by": performed_by,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return audit_id
    
    async def get_audit_trail(self, resource_type: str, resource_id: str) -> List[Dict[str, Any]]:
        """Get complete audit trail for a resource"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                "SELECT id, event_type, action, performed_by, timestamp, details "
                "FROM audit_logs WHERE resource_type = :resource_type AND "
                "resource_id = :resource_id ORDER BY timestamp DESC",
                {"resource_type": resource_type, "resource_id": resource_id}
            )
            
            audit_logs = []
            for log in result:
                audit_logs.append({
                    "id": log[0],
                    "event_type": log[1],
                    "action": log[2],
                    "performed_by": log[3],
                    "timestamp": log[4],
                    "details": log[5]
                })
            
            return audit_logs
    
    async def get_user_activity(self, user_id: str, start_time: datetime, 
                             end_time: datetime) -> List[Dict[str, Any]]:
        """Get all audit logs for a user's activity"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                "SELECT id, event_type, resource_type, resource_id, action, timestamp, "
                "details FROM audit_logs WHERE performed_by = :user_id AND "
                "timestamp BETWEEN :start_time AND :end_time ORDER BY timestamp DESC",
                {"user_id": user_id, "start_time": start_time, "end_time": end_time}
            )
            
            activities = []
            for log in result:
                activities.append({
                    "id": log[0],
                    "event_type": log[1],
                    "resource_type": log[2],
                    "resource_id": log[3],
                    "action": log[4],
                    "timestamp": log[5],
                    "details": log[6]
                })
            
            return activities