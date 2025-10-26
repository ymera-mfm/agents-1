# Performance monitoring
class PerformanceMonitor:
    @staticmethod
    async def track_response_time(request: Request, call_next):
        """Track API response time"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Record metrics
        await MetricsManager.record_metric(
            "api_response_time",
            process_time,
            tags={
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code
            }
        )
        
        # Add server timing header
        response.headers["Server-Timing"] = f"total;dur={process_time*1000:.2f}"
        
        return response

# Security metrics collection
class SecurityMetrics:
    @staticmethod
    async def record_security_event(event_type: str, severity: str, details: Dict[str, Any]):
        """Record security metrics"""
        await MetricsManager.record_metric(
            "security_events",
            1,
            tags={
                "type": event_type,
                "severity": severity
            }
        )
        
        # Send to SIEM
        siem = SIEMIntegration()
        await siem.send_event({
            "event_type": event_type,
            "severity": severity,
            "details": details
        })

# Business metrics
class BusinessMetrics:
    @staticmethod
    async def record_user_activity(user_id: str, action: str, resource_type: str):
        """Record user activity for business metrics"""
        await MetricsManager.record_metric(
            "user_activity",
            1,
            tags={
                "action": action,
                "resource_type": resource_type
            }
        )
    
    @staticmethod
    async def calculate_user_satisfaction():
        """Calculate user satisfaction score"""
        # This would integrate with actual user feedback systems
        pass

# Health check with detailed metrics
@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check with metrics"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "api_response_time_95p": await MetricsManager.get_metric_percentile("api_response_time", 0.95),
            "error_rate": await MetricsManager.get_metric_rate("api_errors", "api_requests"),
            "database_latency": await DatabaseUtils.get_performance_metrics(),
            "cache_hit_rate": await CacheManager.get_hit_rate(),
            "active_users": await UserManager.get_active_user_count(),
            "security_events": await SecurityMetrics.get_event_counts()
        },
        "system": {
            "memory_usage": psutil.virtual_memory().percent,
            "cpu_usage": psutil.cpu_percent(),
            "disk_usage": psutil.disk_usage('/').percent
        }
    }
    
    return health_data

# Add metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware for collecting metrics"""
    # Record request
    await MetricsManager.record_metric("api_requests", 1, tags={"path": request.url.path, "method": request.method})
    
    try:
        response = await call_next(request)
        
        # Record response status
        await MetricsManager.record_metric(
            "api_responses", 
            1, 
            tags={"path": request.url.path, "method": request.method, "status_code": response.status_code}
        )
        
        return response
        
    except Exception as e:
        # Record error
        await MetricsManager.record_metric(
            "api_errors", 
            1, 
            tags={"path": request.url.path, "method": request.method, "error_type": type(e).__name__}
        )
        raise e