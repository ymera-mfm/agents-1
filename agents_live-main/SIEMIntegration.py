# Enhanced SIEM integration
class SIEMIntegration:
    def __init__(self):
        self.siem_enabled = os.getenv("SIEM_ENABLED", "false").lower() == "true"
        self.siem_client = None
        
        if self.siem_enabled:
            self._init_siem_client()
    
    def _init_siem_client(self):
        """Initialize SIEM client"""
        try:
            # This would be actual SIEM client initialization
            # For Splunk: import splunklib.client as client
            # For Elastic: from elasticsearch import Elasticsearch
            logger.info("SIEM client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SIEM: {e}")
            self.siem_enabled = False
    
    async def send_event(self, event: Dict[str, Any]):
        """Send security event to SIEM"""
        if not self.siem_enabled:
            return
        
        try:
            # Standardize event format
            standardized_event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "security",
                "source": "ymera_enterprise",
                "severity": event.get("severity", "medium"),
                "details": event
            }
            
            # This would be actual SIEM integration code
            # For example, with Splunk:
            # self.siem_client.indexes["security"].submit(
            #     json.dumps(standardized_event),
            #     sourcetype="ymera:security"
            # )
            
            logger.info(f"SIEM event sent: {standardized_event}")
            
        except Exception as e:
            logger.error(f"Failed to send SIEM event: {e}")

# Enhanced audit logging with compliance features
class ComplianceAuditLogger:
    @staticmethod
    async def log_gdpr_event(request: Request, user_id: str, action: str, data: Dict[str, Any] = None):
        """Log GDPR-specific audit events"""
        event = {
            "event_type": "gdpr_compliance",
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "data": data or {}
        }
        
        # Send to SIEM
        siem = SIEMIntegration()
        await siem.send_event(event)
        
        # Store in database
        async with DatabaseUtils.get_session() as session:
            audit_log = AuditLogRecord(
                user_id=user_id,
                action=action,
                resource_type="gdpr",
                resource_id=user_id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                details=event
            )
            session.add(audit_log)
            await session.commit()
    
    @staticmethod
    async def log_hipaa_event(request: Request, user_id: str, action: str, phi_data: Dict[str, Any] = None):
        """Log HIPAA-specific audit events"""
        event = {
            "event_type": "hipaa_compliance",
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "phi_access": phi_data or {}
        }
        
        # Send to SIEM
        siem = SIEMIntegration()
        await siem.send_event({**event, "severity": "high"})
        
        # Store in database
        async with DatabaseUtils.get_session() as session:
            audit_log = AuditLogRecord(
                user_id=user_id,
                action=action,
                resource_type="phi",
                resource_id=user_id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                details=event
            )
            session.add(audit_log)
            await session.commit()

# Compliance endpoints
@app.get("/compliance/gdpr/export/{user_id}")
async def gdpr_export_data(
    user_id: str,
    current_user: UserRecord = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """GDPR data export endpoint"""
    async with DatabaseUtils.get_session() as session:
        # Get all user data
        user = await session.execute(
            select(UserRecord).where(UserRecord.id == user_id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Get user's activity logs
        logs = await session.execute(
            select(AuditLogRecord).where(AuditLogRecord.user_id == user_id)
        )
        logs = logs.scalars().all()
        
        # Format for GDPR export
        export_data = {
            "user_data": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "activity_logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent
                }
                for log in logs
            ]
        }
        
        # Log the export event for compliance
        await ComplianceAuditLogger.log_gdpr_event(
            request, 
            current_user.id, 
            "data_export", 
            {"exported_user_id": user_id}
        )
        
        return export_data

@app.delete("/compliance/gdpr/delete/{user_id}")
async def gdpr_delete_data(
    user_id: str,
    current_user: UserRecord = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """GDPR data deletion endpoint"""
    async with DatabaseUtils.get_session() as session:
        # Get user
        user = await session.execute(
            select(UserRecord).where(UserRecord.id == user_id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Anonymize user data instead of actual deletion (GDPR right to be forgotten)
        user.email = f"deleted_{user.id}@example.com"
        user.username = f"deleted_user_{user.id}"
        user.full_name = "Deleted User"
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        
        # Anonymize audit logs
        await session.execute(
            update(AuditLogRecord)
            .where(AuditLogRecord.user_id == user_id)
            .values(ip_address="0.0.0.0", user_agent="deleted")
        )
        
        await session.commit()
        
        # Log the deletion event for compliance
        await ComplianceAuditLogger.log_gdpr_event(
            request, 
            current_user.id, 
            "data_deletion", 
            {"deleted_user_id": user_id}
        )
        
        return {"message": "User data anonymized successfully"}

# Health check endpoint with security headers
@app.get("/health")
async def health_check():
    """Health check endpoint with security headers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response