# security/security_monitor.py
"""
Enhanced security monitoring with threat detection, anomaly detection,
and automated security response.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import json
import re

from models import SecurityEvent, Agent, AuditLog

logger = logging.getLogger(__name__)

class EnhancedSecurityMonitor:
    """Enhanced security monitoring and threat detection"""
    
    def __init__(self, manager):
        """Initialize with reference to the manager"""
        self.manager = manager
        self.threat_patterns = self._load_threat_patterns()
        self.suspicious_activities = set()
        self.active_threats = {}
    
    def _load_threat_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load threat detection patterns"""
        return {
            "suspicious_behavior": {
                "pattern": lambda report: report.get("operations_per_minute", 0) > 1000,
                "severity": "medium",
                "description": "Unusually high operations per minute detected"
            },
            "unauthorized_access_attempt": {
                "pattern": lambda report: report.get("failed_auth_attempts", 0) > 5,
                "severity": "high",
                "description": "Multiple failed authentication attempts detected"
            },
            "data_exfiltration": {
                "pattern": lambda report: report.get("outbound_data_mb", 0) > 100,
                "severity": "critical",
                "description": "Potential data exfiltration detected (large outbound data transfer)"
            },
            "resource_abuse": {
                "pattern": lambda report: (
                    report.get("cpu_usage", 0) > 90 and 
                    report.get("memory_usage", 0) > 90
                ),
                "severity": "medium",
                "description": "Resource abuse detected (high CPU/memory usage)"
            },
            "api_abuse": {
                "pattern": lambda report: report.get("api_requests_per_minute", 0) > 500,
                "severity": "high",
                "description": "API abuse detected (excessive API requests)"
            }
        }
    
    async def start_monitoring(self):
        """Start background security monitoring"""
        logger.info("Starting enhanced security monitoring")
        
        while self.manager.running:
            try:
                await self._check_active_threats()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def analyze_agent_report(self, agent_id: str, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze agent report for security threats and anomalies
        """
        detected_threats = []
        
        try:
            # Check for known threat patterns
            for threat_name, threat_info in self.threat_patterns.items():
                if threat_info["pattern"](report):
                    threat = {
                        "id": f"THREAT-{datetime.utcnow().timestamp()}",
                        "type": threat_name,
                        "severity": threat_info["severity"],
                        "description": threat_info["description"],
                        "agent_id": agent_id,
                        "detection_time": datetime.utcnow().isoformat()
                    }
                    detected_threats.append(threat)
                    
                    # Record the threat
                    await self._record_security_threat(threat)
            
            # Check for anomalies in reported metrics
            anomalies = await self._detect_anomalies(agent_id, report)
            for anomaly in anomalies:
                detected_threats.append({
                    "id": f"ANOMALY-{datetime.utcnow().timestamp()}",
                    "type": "anomaly_detected",
                    "severity": "medium",
                    "description": f"Anomaly detected: {anomaly['metric']} ({anomaly['value']})",
                    "agent_id": agent_id,
                    "detection_time": datetime.utcnow().isoformat()
                })
            
            # Update suspicious activity tracking
            await self._update_suspicious_activity(agent_id, report, detected_threats)
            
            return detected_threats
            
        except Exception as e:
            logger.error(f"Agent report analysis failed: {e}")
            return []
    
    async def _detect_anomalies(self, agent_id: str, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in agent metrics"""
        anomalies = []
        
        try:
            # Get agent history to calculate baseline
            async with self.manager.get_db_session() as session:
                from sqlalchemy import select
                from models import AgentReport
                
                # Get last 10 reports
                result = await session.execute(
                    select(AgentReport)
                    .where(AgentReport.agent_id == agent_id)
                    .order_by(AgentReport.timestamp.desc())
                    .limit(10)
                )
                
                reports = result.scalars().all()
                
                if len(reports) < 5:  # Need enough data for baseline
                    return []
                
                # Calculate baseline for key metrics
                for metric in ["cpu_usage", "memory_usage", "api_requests_per_minute", 
                             "error_rate", "response_time_ms"]:
                    if metric not in report:
                        continue
                        
                    # Calculate baseline from history
                    baseline = sum(r.metrics.get(metric, 0) for r in reports) / len(reports)
                    current_value = report.get(metric, 0)
                    
                    # Check for significant deviation (50%+)
                    deviation_pct = abs(current_value - baseline) / (baseline or 1)
                    if deviation_pct > 0.5:  # 50% deviation
                        anomalies.append({
                            "metric": metric,
                            "baseline": baseline,
                            "value": current_value,
                            "deviation_pct": deviation_pct * 100
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []
    
    async def _record_security_threat(self, threat: Dict[str, Any]) -> None:
        """Record security threat in database and update tracking"""
        try:
            # Add to active threats
            threat_id = threat["id"]
            self.active_threats[threat_id] = threat
            
            # Record in database
            async with self.manager.get_db_session() as session:
                security_event = SecurityEvent(
                    event_type=threat["type"],
                    severity=threat["severity"],
                    source="security_monitor",
                    description=threat["description"],
                    details=threat,
                    agent_id=threat["agent_id"]
                )
                session.add(security_event)
                
                # Create audit log
                audit_log = AuditLog(
                    event_type="security_threat",
                    resource_type="agent",
                    resource_id=threat["agent_id"],
                    action="detect_threat",
                    performed_by="system",
                    severity="high",
                    details=threat
                )
                session.add(audit_log)
                
                await session.commit()
                
            # Update metrics
            self.manager.SECURITY_EVENTS.labels(
                event_type=threat["type"], 
                severity=threat["severity"]
            ).inc()
            
            # Notify admins of critical threats
            if threat["severity"] == "critical":
                await self._notify_admins_of_threat(threat)
                
            # Trigger automatic response for certain threats
            await self._trigger_automated_response(threat)
            
        except Exception as e:
            logger.error(f"Failed to record security threat: {e}")
    
    async def _check_active_threats(self) -> None:
        """Review active threats and update status"""
        current_time = datetime.utcnow()
        resolved_threats = []
        
        for threat_id, threat in self.active_threats.items():
            # Check if threat is still active
            detection_time = datetime.fromisoformat(threat["detection_time"])
            if (current_time - detection_time).total_seconds() > 3600:  # 1 hour
                # Auto-resolve threat after 1 hour without recurrence
                resolved_threats.append(threat_id)
        
        # Remove resolved threats
        for threat_id in resolved_threats:
            del self.active_threats[threat_id]
    
    async def _update_suspicious_activity(self, agent_id: str, 
                                        report: Dict[str, Any], 
                                        threats: List[Dict[str, Any]]) -> None:
        """Update suspicious activity tracking"""
        if threats:
            self.suspicious_activities.add(agent_id)
            
            # If this is a previously unsuspicious agent, log it
            if agent_id not in self.suspicious_activities:
                logger.warning(f"Agent {agent_id} marked as suspicious due to detected threats")
        
        # Remove from suspicious list if no threats for a while and good behavior
        elif agent_id in self.suspicious_activities:
            # Check if report shows normal behavior
            has_abnormal_behavior = any([
                report.get("failed_auth_attempts", 0) > 0,
                report.get("cpu_usage", 0) > 80,
                report.get("memory_usage", 0) > 80,
                report.get("api_requests_per_minute", 0) > 300
            ])
            
            if not has_abnormal_behavior:
                self.suspicious_activities.remove(agent_id)
                logger.info(f"Agent {agent_id} removed from suspicious activities list")
    
    async def _notify_admins_of_threat(self, threat: Dict[str, Any]) -> None:
        """Notify admins of critical security threats"""
        notification = {
            "type": "security_threat",
            "title": f"SECURITY ALERT: {threat['type']}",
            "message": threat["description"],
            "severity": "critical",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "threat_id": threat["id"],
                "agent_id": threat["agent_id"],
                "severity": threat["severity"]
            }
        }
        
        await self.manager.notification_manager.send_notification("admin", notification)
    
    async def _trigger_automated_response(self, threat: Dict[str, Any]) -> None:
        """Trigger automated security response based on threat severity"""
        agent_id = threat["agent_id"]
        severity = threat["severity"]
        
        # For critical threats, isolate the agent immediately
        if severity == "critical":
            logger.warning(f"Auto-isolating agent {agent_id} due to critical security threat")
            
            await self.manager.request_agent_action(
                agent_id=agent_id,
                action=AgentAction.ISOLATE.value,
                reason=f"Automatic isolation due to critical security threat: {threat['type']}",
                requested_by="system"
            )
        
        # For high severity threats, request an audit
        elif severity == "high":
            logger.info(f"Requesting security audit for agent {agent_id} due to high severity threat")
            
            await self.manager.request_agent_action(
                agent_id=agent_id,
                action=AgentAction.AUDIT.value,
                reason=f"Automatic audit due to high severity security threat: {threat['type']}",
                requested_by="system"
            )
    
    async def scan_for_threats(self):
        """Proactive threat scanning"""
        logger.info("Running proactive threat scan")
        
        while self.manager.running:
            try:
                # Sleep at beginning to avoid running immediately after startup
                await asyncio.sleep(3600)  # Run every hour
                
                async with self.manager.get_db_session() as session:
                    # Check for suspicious patterns across all agents
                    await self._scan_for_brute_force_patterns()
                    await self._scan_for_data_exfiltration_patterns()
                    await self._scan_for_dormant_agents()
                    
            except Exception as e:
                logger.error(f"Proactive threat scan failed: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error
    
    async def _scan_for_brute_force_patterns(self):
        """Scan for brute force attack patterns"""
        async with self.manager.get_db_session() as session:
            from sqlalchemy import select, func
            from models import AgentReport
            
            # Look for agents with repeated authentication failures
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            # This query would find agents with high failed auth attempts
            # Note: Specific implementation depends on your schema
            query = (
                select(
                    AgentReport.agent_id,
                    func.sum(AgentReport.metrics['failed_auth_attempts'].as_integer())
                )
                .where(AgentReport.timestamp > one_hour_ago)
                .group_by(AgentReport.agent_id)
                .having(func.sum(AgentReport.metrics['failed_auth_attempts'].as_integer()) > 10)
            )
            
            result = await session.execute(query)
            suspicious_agents = result.all()
            
            for agent_id, failed_attempts in suspicious_agents:
                # Create security event
                security_event = SecurityEvent(
                    event_type="brute_force_detected",
                    severity="high",
                    source="security_scan",
                    description=f"Potential brute force attack detected",
                    agent_id=agent_id,
                    details={
                        "failed_attempts": failed_attempts,
                        "timeframe": "1 hour"
                    }
                )
                session.add(security_event)
                
                # Update metrics and notify admins
                self.manager.SECURITY_EVENTS.labels(
                    event_type="brute_force_detected",
                    severity="high"
                ).inc()
                
            await session.commit()