# security/audit_system.py
"""
Enhanced audit system with comprehensive logging, search capabilities,
retention policies, and compliance reporting
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import uuid

from models import AuditLog

logger = logging.getLogger(__name__)

class EnhancedAuditSystem:
    """Enhanced audit logging and compliance reporting"""
    
    def __init__(self, manager):
        """Initialize with reference to manager"""
        self.manager = manager
        self.retention_period = timedelta(days=self.manager.config.get("audit_retention_days", 365))
    
    async def log_event(self, event_type: str, resource_type: str, 
                      resource_id: str, action: str, performed_by: str, 
                      details: Dict[str, Any] = None, severity: str = "info",
                      ip_address: str = None) -> str:
        """Log comprehensive audit event"""
        try:
            correlation_id = str(uuid.uuid4())
            
            async with self.manager.get_db_session() as session:
                audit_log = AuditLog(
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                    performed_by=performed_by,
                    details=details or {},
                    ip_address=ip_address,
                    severity=severity,
                    correlation_id=correlation_id
                )
                
                session.add(audit_log)
                await session.commit()
                
                # Update metrics
                # self.manager.AUDIT_EVENTS.labels(event_type=event_type, severity=severity).inc()
                
                return audit_log.id
                
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Fall back to regular logging if database fails
            logger.warning(f"AUDIT: {event_type} {resource_type}:{resource_id} {action} by {performed_by}")
            return None
    
    async def search_audit_logs(self, filters: Dict[str, Any] = None, 
                              limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Search audit logs with filtering"""
        try:
            async with self.manager.get_db_session() as session:
                from sqlalchemy import select, and_, or_, not_
                
                # Start with base query
                query = select(AuditLog).order_by(AuditLog.timestamp.desc())
                
                # Apply filters if provided
                if filters:
                    conditions = []
                    
                    if "event_type" in filters:
                        conditions.append(AuditLog.event_type == filters["event_type"])
                    
                    if "resource_type" in filters:
                        conditions.append(AuditLog.resource_type == filters["resource_type"])
                    
                    if "resource_id" in filters:
                        conditions.append(AuditLog.resource_id == filters["resource_id"])
                    
                    if "performed_by" in filters:
                        conditions.append(AuditLog.performed_by == filters["performed_by"])
                    
                    if "severity" in filters:
                        conditions.append(AuditLog.severity == filters["severity"])
                    
                    if "start_time" in filters:
                        conditions.append(AuditLog.timestamp >= filters["start_time"])
                    
                    if "end_time" in filters:
                        conditions.append(AuditLog.timestamp <= filters["end_time"])
                    
                    if conditions:
                        query = query.where(and_(*conditions))
                
                # Apply pagination
                query = query.limit(limit).offset(offset)
                
                # Execute query
                result = await session.execute(query)
                logs = result.scalars().all()
                
                # Format results
                return [
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat(),
                        "event_type": log.event_type,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "action": log.action,
                        "performed_by": log.performed_by,
                        "severity": log.severity,
                        "details": log.details,
                        "ip_address": log.ip_address,
                        "correlation_id": log.correlation_id
                    }
                    for log in logs
                ]
                
        except Exception as e:
            logger.error(f"Audit log search failed: {e}")
            return []
    
    async def generate_compliance_report(self, start_time: datetime, 
                                      end_time: datetime, report_type: str = "summary") -> Dict[str, Any]:
        """Generate compliance report from audit logs"""
        try:
            # Get relevant audit logs
            audit_logs = await self.search_audit_logs(
                filters={
                    "start_time": start_time,
                    "end_time": end_time
                },
                limit=10000  # Higher limit for comprehensive reports
            )
            
            if report_type == "summary":
                return self._generate_summary_report(audit_logs, start_time, end_time)
            elif report_type == "detailed":
                return self._generate_detailed_report(audit_logs, start_time, end_time)
            else:
                return {
                    "error": "Invalid report type",
                    "valid_types": ["summary", "detailed"]
                }
                
        except Exception as e:
            logger.error(f"Compliance report generation failed: {e}")
            return {"error": str(e)}
    
    def _generate_summary_report(self, audit_logs: List[Dict[str, Any]], 
                              start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate summary compliance report"""
        # Count events by type
        event_counts = {}
        severity_counts = {}
        user_actions = {}
        resource_counts = {}
        
        for log in audit_logs:
            # Count by event type
            event_counts[log["event_type"]] = event_counts.get(log["event_type"], 0) + 1
            
            # Count by severity
            severity_counts[log["severity"]] = severity_counts.get(log["severity"], 0) + 1
            
            # Count by user
            user = log["performed_by"]
            if user not in user_actions:
                user_actions[user] = {}
            
            action = log["action"]
            user_actions[user][action] = user_actions[user].get(action, 0) + 1
            
            # Count by resource type
            res_type = log["resource_type"]
            resource_counts[res_type] = resource_counts.get(res_type, 0) + 1
        
        # Generate report
        return {
            "report_type": "summary",
            "generated_at": datetime.utcnow().isoformat(),
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "total_events": len(audit_logs),
            "event_type_distribution": event_counts,
            "severity_distribution": severity_counts,
            "user_activity": user_actions,
            "resource_distribution": resource_counts,
            "high_severity_count": severity_counts.get("high", 0) + severity_counts.get("critical", 0)
        }
    
    async def clean_old_logs(self):
        """Clean up old audit logs based on retention policy"""
        try:
            cutoff_date = datetime.utcnow() - self.retention_period
            
            async with self.manager.get_db_session() as session:
                from sqlalchemy import delete
                
                # Delete logs older than retention period
                result = await session.execute(
                    delete(AuditLog).where(AuditLog.timestamp < cutoff_date)
                )
                
                deleted_count = result.rowcount
                await session.commit()
                
                logger.info(f"Cleaned {deleted_count} audit logs older than {cutoff_date}")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Audit log cleanup failed: {e}")
            return 0