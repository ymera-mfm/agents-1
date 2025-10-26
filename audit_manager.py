# audit_manager.py
"""
Comprehensive auditing system with regular and surprise audits,
compliance verification, and detailed reporting
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta
import json
import uuid
import random
from enum import Enum
from redis import asyncio as aioredis
import hashlib
import hmac
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class AuditType(str, Enum):
    """Types of audits"""
    REGULAR = "regular"          # Scheduled, expected audit
    SURPRISE = "surprise"        # Unannounced surprise audit
    COMPLIANCE = "compliance"    # Compliance-focused audit
    SECURITY = "security"        # Security-focused audit
    PERFORMANCE = "performance"  # Performance-focused audit
    BEHAVIORAL = "behavioral"    # Agent behavior audit

class AuditScope(str, Enum):
    """Scope of audit"""
    SYSTEM = "system"            # Full system audit
    TENANT = "tenant"            # Tenant-level audit
    AGENT = "agent"              # Single agent audit
    WORKFLOW = "workflow"        # Workflow execution audit
    INTERACTION = "interaction"  # Agent interaction audit

class AuditOutcome(str, Enum):
    """Outcome of audit"""
    PASSED = "passed"            # Fully compliant
    PASSED_WITH_FINDINGS = "passed_with_findings"  # Passed with minor issues
    FAILED = "failed"            # Failed audit
    CRITICAL = "critical"        # Critical failures detected
    INCOMPLETE = "incomplete"    # Audit not completed

@dataclass
class AuditFinding:
    """Audit finding with details"""
    id: str
    audit_id: str
    severity: str  # critical, high, medium, low
    title: str
    description: str
    evidence: Dict
    recommendation: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str = "open"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AuditRecord:
    """Complete audit record"""
    id: str
    audit_type: AuditType
    scope: AuditScope
    target_id: str  # System, tenant, agent, workflow ID
    auditor_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    outcome: Optional[AuditOutcome] = None
    findings: List[AuditFinding] = field(default_factory=list)
    findings_count: Dict[str, int] = field(default_factory=dict)
    summary: str = ""
    next_audit_date: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

class AuditManager:
    """
    Comprehensive auditing system for agent governance
    """
    
    def __init__(self, redis_client: aioredis.Redis, config: Dict):
        self.redis = redis_client
        self.config = config
        self.audit_templates = self._load_audit_templates()
        self.surprise_audit_probability = config.get('surprise_audit_probability', 0.2)
        
        # Schedule audit intervals (in days)
        self.audit_intervals = {
            AuditType.REGULAR: config.get('regular_audit_interval', 30),
            AuditType.COMPLIANCE: config.get('compliance_audit_interval', 90),
            AuditType.SECURITY: config.get('security_audit_interval', 60),
            AuditType.PERFORMANCE: config.get('performance_audit_interval', 45),
            AuditType.BEHAVIORAL: config.get('behavioral_audit_interval', 30)
        }
        
        logger.info("AuditManager initialized")
    
    def _load_audit_templates(self) -> Dict:
        """Load audit templates from configuration"""
        templates = {}
        
        # Load from config, or use defaults
        templates[AuditType.REGULAR] = self.config.get('templates', {}).get('regular', [
            {"id": "reg-1", "check": "agent_reporting", "weight": 1.0, "critical": False},
            {"id": "reg-2", "check": "information_flow", "weight": 1.0, "critical": True},
            {"id": "reg-3", "check": "permission_compliance", "weight": 1.0, "critical": True}
        ])
        
        templates[AuditType.SURPRISE] = self.config.get('templates', {}).get('surprise', [
            {"id": "surp-1", "check": "unauthorized_access", "weight": 2.0, "critical": True},
            {"id": "surp-2", "check": "data_retention", "weight": 1.5, "critical": False},
            {"id": "surp-3", "check": "undisclosed_capabilities", "weight": 2.0, "critical": True}
        ])
        
        templates[AuditType.COMPLIANCE] = self.config.get('templates', {}).get('compliance', [
            {"id": "comp-1", "check": "regulatory_compliance", "weight": 1.5, "critical": True},
            {"id": "comp-2", "check": "data_handling", "weight": 1.5, "critical": True},
            {"id": "comp-3", "check": "audit_trail", "weight": 1.0, "critical": False}
        ])
        
        templates[AuditType.SECURITY] = self.config.get('templates', {}).get('security', [
            {"id": "sec-1", "check": "vulnerability_scan", "weight": 2.0, "critical": True},
            {"id": "sec-2", "check": "encryption_verification", "weight": 1.5, "critical": True},
            {"id": "sec-3", "check": "access_control", "weight": 1.5, "critical": True}
        ])
        
        templates[AuditType.PERFORMANCE] = self.config.get('templates', {}).get('performance', [
            {"id": "perf-1", "check": "resource_usage", "weight": 1.0, "critical": False},
            {"id": "perf-2", "check": "response_time", "weight": 1.0, "critical": False},
            {"id": "perf-3", "check": "throughput", "weight": 1.0, "critical": False}
        ])
        
        templates[AuditType.BEHAVIORAL] = self.config.get('templates', {}).get('behavioral', [
            {"id": "behav-1", "check": "decision_validation", "weight": 1.5, "critical": True},
            {"id": "behav-2", "check": "bias_detection", "weight": 1.5, "critical": True},
            {"id": "behav-3", "check": "consistency", "weight": 1.0, "critical": False}
        ])
        
        return templates
    
    async def initiate_audit(self, audit_type: AuditType, 
                           scope: AuditScope, 
                           target_id: str,
                           auditor_id: str,
                           metadata: Optional[Dict] = None) -> str:
        """
        Initiate a new audit
        """
        audit_id = f"audit_{uuid.uuid4().hex}"
        
        # Create audit record
        audit = AuditRecord(
            id=audit_id,
            audit_type=audit_type,
            scope=scope,
            target_id=target_id,
            auditor_id=auditor_id,
            start_time=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store in Redis
        await self.redis.set(
            f"audit:{audit_id}", 
            json.dumps(self._audit_to_dict(audit)),
            ex=86400 * 180  # Store for 180 days
        )
        
        # Add to indexes
        await self.redis.sadd(f"audits:type:{audit_type}", audit_id)
        await self.redis.sadd(f"audits:scope:{scope}:{target_id}", audit_id)
        
        logger.info(f"Initiated {audit_type} audit {audit_id} on {scope}:{target_id}")
        
        # Start audit process in background
        asyncio.create_task(self._conduct_audit(audit_id))
        
        return audit_id
    
    async def _conduct_audit(self, audit_id: str) -> None:
        """
        Conduct the audit process
        """
        # Get audit record
        audit_data = await self.redis.get(f"audit:{audit_id}")
        if not audit_data:
            logger.error(f"Audit {audit_id} not found")
            return
        
        audit = self._dict_to_audit(json.loads(audit_data))
        
        try:
            # Get audit template
            template = self.audit_templates.get(audit.audit_type, [])
            
            # Conduct checks based on template
            findings = []
            for check in template:
                check_result = await self._run_audit_check(
                    check["check"], 
                    audit.scope, 
                    audit.target_id,
                    check["critical"]
                )
                
                if check_result["issues"]:
                    for issue in check_result["issues"]:
                        finding = AuditFinding(
                            id=f"finding_{uuid.uuid4().hex}",
                            audit_id=audit_id,
                            severity=issue["severity"],
                            title=issue["title"],
                            description=issue["description"],
                            evidence=issue["evidence"],
                            recommendation=issue["recommendation"]
                        )
                        findings.append(finding)
            
            # Calculate outcome based on findings
            outcome = self._determine_audit_outcome(findings)
            
            # Complete audit record
            audit.end_time = datetime.utcnow()
            audit.outcome = outcome
            audit.findings = findings
            audit.findings_count = self._count_findings_by_severity(findings)
            audit.summary = self._generate_audit_summary(audit)
            
            # Schedule next audit
            audit.next_audit_date = self._schedule_next_audit(audit)
            
            # Update audit record
            await self.redis.set(
                f"audit:{audit_id}",
                json.dumps(self._audit_to_dict(audit)),
                ex=86400 * 180  # Store for 180 days
            )
            
            # Store findings separately
            for finding in findings:
                await self.redis.set(
                    f"finding:{finding.id}",
                    json.dumps(self._finding_to_dict(finding)),
                    ex=86400 * 180  # Store for 180 days
                )
                await self.redis.sadd(f"audit:{audit_id}:findings", finding.id)
            
            # Notify about audit completion
            await self._send_audit_notifications(audit)
            
            logger.info(f"Completed audit {audit_id} with outcome {outcome}")
            
        except Exception as e:
            logger.error(f"Error conducting audit {audit_id}: {e}")
            
            # Update audit record with error status
            audit.end_time = datetime.utcnow()
            audit.outcome = AuditOutcome.INCOMPLETE
            audit.summary = f"Audit failed to complete: {str(e)}"
            
            await self.redis.set(
                f"audit:{audit_id}",
                json.dumps(self._audit_to_dict(audit)),
                ex=86400 * 180
            )
    
    async def _run_audit_check(self, check_name: str, scope: AuditScope, 
                            target_id: str, is_critical: bool) -> Dict:
        """
        Run a specific audit check
        """
        # This would integrate with specific check implementations
        # For now, simulate check execution with randomized results
        
        # Map check to handler
        check_handler = getattr(self, f"_check_{check_name}", None)
        
        if check_handler and callable(check_handler):
            # Execute the actual check
            return await check_handler(scope, target_id, is_critical)
        else:
            # Simulate a check result if handler not found
            return self._simulate_check_result(check_name, is_critical)
    
    async def _check_agent_reporting(self, scope: AuditScope, target_id: str, is_critical: bool) -> Dict:
        """Check if agent is properly reporting"""
        issues = []
        
        if scope == AuditScope.AGENT:
            # Get agent reporting data
            last_report = await self._get_agent_last_report(target_id)
            reporting_frequency = await self._get_agent_reporting_frequency(target_id)
            
            if not last_report:
                issues.append({
                    "severity": "critical" if is_critical else "high",
                    "title": "Agent not reporting",
                    "description": f"Agent {target_id} has no reporting history",
                    "evidence": {"last_report": None},
                    "recommendation": "Investigate agent communication issues"
                })
            elif datetime.utcnow() - last_report > timedelta(minutes=reporting_frequency * 2):
                issues.append({
                    "severity": "high",
                    "title": "Agent reporting delays",
                    "description": f"Agent {target_id} last reported {(datetime.utcnow() - last_report).total_seconds() / 60} minutes ago",
                    "evidence": {"last_report": last_report.isoformat(), "expected_frequency": reporting_frequency},
                    "recommendation": "Check agent connectivity and status"
                })
        
        return {
            "check": "agent_reporting",
            "status": "completed",
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_information_flow(self, scope: AuditScope, target_id: str, is_critical: bool) -> Dict:
        """Check information flow compliance"""
        # Implementation would check proper information routing and permissions
        issues = []
        
        # Simulate finding issues
        if random.random() < 0.2:  # 20% chance of finding an issue
            issues.append({
                "severity": "medium",
                "title": "Suboptimal information routing",
                "description": "Information is not following optimal routes between components",
                "evidence": {"flow_analysis": {"inefficiencies": ["route_A_to_B"]}},
                "recommendation": "Optimize routing patterns between components"
            })
        
        if random.random() < 0.05:  # 5% chance of finding a critical issue
            issues.append({
                "severity": "critical",
                "title": "Information leakage risk",
                "description": "Potential for sensitive data to be exposed through improper routing",
                "evidence": {"vulnerability_scan": {"risk_points": ["api_endpoint_x"]}},
                "recommendation": "Implement additional encryption and access controls"
            })
        
        return {
            "check": "information_flow",
            "status": "completed",
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _simulate_check_result(self, check_name: str, is_critical: bool) -> Dict:
        """Simulate an audit check result"""
        issues = []
        
        # Simulate a 15% chance of finding an issue
        if random.random() < 0.15:
            severity = random.choice(["low", "medium", "high", "critical" if is_critical else "high"])
            
            issues.append({
                "severity": severity,
                "title": f"Simulated {severity} issue with {check_name}",
                "description": f"This is a simulated issue for the {check_name} check",
                "evidence": {"simulation": True},
                "recommendation": f"Address the {severity} {check_name} issue"
            })
        
        return {
            "check": check_name,
            "status": "completed",
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_agent_last_report(self, agent_id: str) -> Optional[datetime]:
        """Get agent's last report timestamp"""
        # This would fetch from agent reporting data
        # Simulated implementation
        try:
            timestamp = await self.redis.get(f"agent:{agent_id}:last_report")
            if timestamp:
                return datetime.fromisoformat(timestamp.decode('utf-8'))
            return None
        except Exception:
            return datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
    
    async def _get_agent_reporting_frequency(self, agent_id: str) -> int:
        """Get agent's reporting frequency in minutes"""
        # This would fetch from agent configuration
        # Simulated implementation
        return random.choice([5, 10, 15, 30])
    
    def _determine_audit_outcome(self, findings: List[AuditFinding]) -> AuditOutcome:
        """Determine audit outcome based on findings"""
        if not findings:
            return AuditOutcome.PASSED
        
        # Check for critical findings
        critical_findings = [f for f in findings if f.severity == "critical"]
        if critical_findings:
            return AuditOutcome.CRITICAL
        
        # Check for high severity findings
        high_findings = [f for f in findings if f.severity == "high"]
        if len(high_findings) > 2:  # More than 2 high severity findings = fail
            return AuditOutcome.FAILED
        
        # If we have findings but not enough to fail
        return AuditOutcome.PASSED_WITH_FINDINGS
    
    def _count_findings_by_severity(self, findings: List[AuditFinding]) -> Dict[str, int]:
        """Count findings by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for finding in findings:
            if finding.severity in counts:
                counts[finding.severity] += 1
        
        return counts
    
    def _generate_audit_summary(self, audit: AuditRecord) -> str:
        """Generate summary of audit results"""
        if not audit.findings:
            return "No issues were found during this audit."
        
        summary = f"Audit completed with {len(audit.findings)} findings: "
        summary += ", ".join(f"{count} {severity}" for severity, count in audit.findings_count.items() if count > 0)
        
        if audit.outcome == AuditOutcome.CRITICAL:
            summary += "\n\nCRITICAL ISSUES REQUIRE IMMEDIATE ATTENTION!"
        elif audit.outcome == AuditOutcome.FAILED:
            summary += "\n\nAudit failed due to multiple significant issues."
        
        return summary
    
    def _schedule_next_audit(self, audit: AuditRecord) -> datetime:
        """Schedule next audit based on outcome and type"""
        # Base interval from configuration
        base_days = self.audit_intervals.get(audit.audit_type, 30)
        
        # Adjust based on outcome
        if audit.outcome == AuditOutcome.CRITICAL:
            # Critical findings - re-audit quickly
            days = max(1, base_days // 10)
        elif audit.outcome == AuditOutcome.FAILED:
            # Failed - re-audit at 1/4 the normal interval
            days = max(7, base_days // 4)
        elif audit.outcome == AuditOutcome.PASSED_WITH_FINDINGS:
            # Minor issues - re-audit at 1/2 the normal interval
            days = max(15, base_days // 2)
        else:
            # Passed clean - normal interval
            days = base_days
        
        # Add some randomness to prevent predictability
        days = int(days * random.uniform(0.9, 1.1))
        
        return datetime.utcnow() + timedelta(days=days)
    
    async def _send_audit_notifications(self, audit: AuditRecord) -> None:
        """Send notifications about audit results"""
        # This would integrate with notification system
        notification_data = {
            "type": "audit_completed",
            "audit_id": audit.id,
            "audit_type": audit.audit_type,
            "scope": audit.scope,
            "target_id": audit.target_id,
            "outcome": audit.outcome,
            "findings_count": audit.findings_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish to audit events channel
        await self.redis.publish("audit_events", json.dumps(notification_data))
        
        # Store notification
        await self.redis.lpush(
            "audit_notifications", 
            json.dumps(notification_data)
        )
        await self.redis.ltrim("audit_notifications", 0, 999)  # Keep last 1000
    
    def _audit_to_dict(self, audit: AuditRecord) -> Dict:
        """Convert AuditRecord to dictionary for storage"""
        return {
            "id": audit.id,
            "audit_type": audit.audit_type,
            "scope": audit.scope,
            "target_id": audit.target_id,
            "auditor_id": audit.auditor_id,
            "start_time": audit.start_time.isoformat(),
            "end_time": audit.end_time.isoformat() if audit.end_time else None,
            "outcome": audit.outcome,
            "findings": [self._finding_to_dict(finding) for finding in audit.findings],
            "findings_count": audit.findings_count,
            "summary": audit.summary,
            "next_audit_date": audit.next_audit_date.isoformat() if audit.next_audit_date else None,
            "metadata": audit.metadata
        }
    
    def _dict_to_audit(self, data: Dict) -> AuditRecord:
        """Convert dictionary to AuditRecord"""
        return AuditRecord(
            id=data["id"],
            audit_type=data["audit_type"],
            scope=data["scope"],
            target_id=data["target_id"],
            auditor_id=data["auditor_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            outcome=data.get("outcome"),
            findings=[self._dict_to_finding(finding) for finding in data.get("findings", [])],
            findings_count=data.get("findings_count", {}),
            summary=data.get("summary", ""),
            next_audit_date=datetime.fromisoformat(data["next_audit_date"]) if data.get("next_audit_date") else None,
            metadata=data.get("metadata", {})
        )
    
    def _finding_to_dict(self, finding: AuditFinding) -> Dict:
        """Convert AuditFinding to dictionary for storage"""
        return {
            "id": finding.id,
            "audit_id": finding.audit_id,
            "severity": finding.severity,
            "title": finding.title,
            "description": finding.description,
            "evidence": finding.evidence,
            "recommendation": finding.recommendation,
            "assigned_to": finding.assigned_to,
            "due_date": finding.due_date.isoformat() if finding.due_date else None,
            "status": finding.status,
            "created_at": finding.created_at.isoformat(),
            "updated_at": finding.updated_at.isoformat()
        }
    
    def _dict_to_finding(self, data: Dict) -> AuditFinding:
        """Convert dictionary to AuditFinding"""
        return AuditFinding(
            id=data["id"],
            audit_id=data["audit_id"],
            severity=data["severity"],
            title=data["title"],
            description=data["description"],
            evidence=data["evidence"],
            recommendation=data["recommendation"],
            assigned_to=data.get("assigned_to"),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            status=data.get("status", "open"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
    
    async def schedule_regular_audits(self) -> None:
        """Schedule regular audits for all targets"""
        # This would run periodically to maintain audit schedule
        while True:
            try:
                # Get all agents that need auditing
                agents_to_audit = await self._find_agents_needing_audit()
                
                for agent_id in agents_to_audit:
                    # Randomly determine if this should be a surprise audit
                    is_surprise = random.random() < self.surprise_audit_probability
                    
                    audit_type = AuditType.SURPRISE if is_surprise else AuditType.REGULAR
                    
                    # Initiate audit
                    await self.initiate_audit(
                        audit_type=audit_type,
                        scope=AuditScope.AGENT,
                        target_id=agent_id,
                        auditor_id="system",
                        metadata={"scheduled": True, "surprise": is_surprise}
                    )
                
                # Check for systems and workflows needing audits
                # Similar to agent code above
                
                # Sleep for a while before next check
                await asyncio.sleep(3600)  # Check hourly
                
            except Exception as e:
                logger.error(f"Error scheduling regular audits: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _find_agents_needing_audit(self) -> List[str]:
        """Find agents that need to be audited"""
        # This would check when agents were last audited
        # For now, return a simulated list
        return ["agent_123", "agent_456"]
    
    async def get_audit_report(self, audit_id: str) -> Dict:
        """Get audit report by ID"""
        audit