# monitoring/health.py
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import httpx
import redis
import asyncpg
from kafka import KafkaProducer, KafkaConsumer
import logging

logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    component: str
    status: str  # healthy, degraded, unhealthy
    response_time: float
    error: Optional[str] = None
    timestamp: datetime = None

@dataclass
class SLAStatus:
    component: str
    uptime_percentage: float
    response_time_avg: float
    error_rate: float
    last_incident: Optional[datetime] = None
    status: str = "operational"  # operational, degraded, outage

class HealthCheckManager:
    """Advanced health check management with SLA monitoring"""
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'redis': self.check_redis,
            'kafka': self.check_kafka,
            'external_apis': self.check_external_apis,
            'storage': self.check_storage,
            'network': self.check_network
        }
        
        self.sla_targets = {
            'database': {'uptime': 99.99, 'response_time': 50, 'error_rate': 0.1},
            'redis': {'uptime': 99.99, 'response_time': 5, 'error_rate': 0.1},
            'kafka': {'uptime': 99.95, 'response_time': 10, 'error_rate': 0.5},
            'api': {'uptime': 99.9, 'response_time': 200, 'error_rate': 0.1}
        }
        
        self.health_history = {}
        self.sla_status = {}
    
    async def perform_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Perform all health checks"""
        results = {}
        
        for component, check_func in self.checks.items():
            try:
                start_time = time.time()
                status = await check_func()
                response_time = (time.time() - start_time) * 1000  # ms
                
                results[component] = HealthCheckResult(
                    component=component,
                    status=status,
                    response_time=response_time,
                    timestamp=datetime.utcnow()
                )
                
            except Exception as e:
                results[component] = HealthCheckResult(
                    component=component,
                    status="unhealthy",
                    response_time=-1,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
        
        self._update_health_history(results)
        self._calculate_sla_status()
        
        return results
    
    async def check_database(self) -> str:
        """Check database connection and performance"""
        try:
            # Test connection
            conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
            await conn.close()
            
            # Test query performance
            start_time = time.time()
            conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
            await conn.execute('SELECT 1')
            await conn.close()
            query_time = (time.time() - start_time) * 1000
            
            if query_time > 100:  # 100ms threshold
                return "degraded"
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return "unhealthy"
    
    async def check_redis(self) -> str:
        """Check Redis connection and performance"""
        try:
            client = redis.Redis.from_url(os.getenv('REDIS_URL'))
            
            # Test connection and latency
            start_time = time.time()
            client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            if ping_time > 10:  # 10ms threshold
                return "degraded"
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return "unhealthy"
    
    async def check_kafka(self) -> str:
        """Check Kafka connectivity"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS').split(','),
                value_serializer=lambda v: str(v).encode('utf-8')
            )
            
            # Test message production
            start_time = time.time()
            future = producer.send('health-check', 'test')
            future.get(timeout=10)
            produce_time = (time.time() - start_time) * 1000
            
            if produce_time > 100:  # 100ms threshold
                return "degraded"
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return "unhealthy"
    
    async def check_external_apis(self) -> str:
        """Check external API dependencies"""
        apis_to_check = [
            'https://api.stripe.com/v1',
            'https://api.twilio.com/2010-04-01',
            'https://slack.com/api/api.test'
        ]
        
        unhealthy_count = 0
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for api_url in apis_to_check:
                try:
                    response = await client.get(api_url)
                    if response.status_code >= 400:
                        unhealthy_count += 1
                except Exception:
                    unhealthy_count += 1
        
        if unhealthy_count == len(apis_to_check):
            return "unhealthy"
        elif unhealthy_count > 0:
            return "degraded"
        else:
            return "healthy"
    
    async def check_storage(self) -> str:
        """Check storage systems"""
        # Check S3/cloud storage accessibility
        try:
            import boto3
            s3 = boto3.client('s3')
            s3.list_buckets()
            return "healthy"
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return "unhealthy"
    
    async def check_network(self) -> str:
        """Check network connectivity"""
        try:
            # Test DNS resolution
            import socket
            socket.gethostbyname('google.com')
            
            # Test network latency
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                await client.get('https://www.google.com')
                latency = (time.time() - start_time) * 1000
                
                if latency > 1000:  # 1 second threshold
                    return "degraded"
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"Network health check failed: {e}")
            return "unhealthy"
    
    def _update_health_history(self, results: Dict[str, HealthCheckResult]):
        """Update health check history"""
        timestamp = datetime.utcnow()
        
        for component, result in results.items():
            if component not in self.health_history:
                self.health_history[component] = []
            
            self.health_history[component].append({
                'timestamp': timestamp,
                'status': result.status,
                'response_time': result.response_time,
                'error': result.error
            })
            
            # Keep only last 24 hours of data
            cutoff = timestamp - timedelta(hours=24)
            self.health_history[component] = [
                entry for entry in self.health_history[component]
                if entry['timestamp'] > cutoff
            ]
    
    def _calculate_sla_status(self):
        """Calculate SLA compliance status"""
        for component in self.health_history.keys():
            if component not in self.sla_targets:
                continue
                
            history = self.health_history[component]
            if not history:
                continue
            
            total_checks = len(history)
            healthy_checks = len([h for h in history if h['status'] == 'healthy'])
            degraded_checks = len([h for h in history if h['status'] == 'degraded'])
            unhealthy_checks = len([h for h in history if h['status'] == 'unhealthy'])
            
            uptime_percentage = (healthy_checks + degraded_checks * 0.5) / total_checks * 100
            
            response_times = [h['response_time'] for h in history if h['response_time'] > 0]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            error_rate = unhealthy_checks / total_checks * 100
            
            # Determine overall status
            if uptime_percentage < self.sla_targets[component]['uptime']:
                status = "outage"
            elif error_rate > self.sla_targets[component]['error_rate']:
                status = "degraded"
            elif avg_response_time > self.sla_targets[component]['response_time']:
                status = "degraded"
            else:
                status = "operational"
            
            self.sla_status[component] = SLAStatus(
                component=component,
                uptime_percentage=uptime_percentage,
                response_time_avg=avg_response_time,
                error_rate=error_rate,
                status=status
            )
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': self._get_overall_status(),
            'component_status': {comp: status.__dict__ for comp, status in self.sla_status.items()},
            'sla_compliance': self._calculate_sla_compliance(),
            'incidents_last_24h': self._get_recent_incidents(),
            'recommendations': self._generate_recommendations()
        }
    
    def _get_overall_status(self) -> str:
        """Get overall system status"""
        if not self.sla_status:
            return "unknown"
        
        statuses = [status.status for status in self.sla_status.values()]
        
        if any(status == "outage" for status in statuses):
            return "outage"
        elif any(status == "degraded" for status in statuses):
            return "degraded"
        else:
            return "operational"
    
    def _calculate_sla_compliance(self) -> Dict[str, bool]:
        """Calculate SLA compliance for each component"""
        compliance = {}
        
        for component, status in self.sla_status.items():
            if component not in self.sla_targets:
                continue
                
            target = self.sla_targets[component]
            compliance[component] = (
                status.uptime_percentage >= target['uptime'] and
                status.response_time_avg <= target['response_time'] and
                status.error_rate <= target['error_rate']
            )
        
        return compliance
    
    def _get_recent_incidents(self) -> List[Dict[str, Any]]:
        """Get recent incidents from health history"""
        incidents = []
        
        for component, history in self.health_history.items():
            for entry in history:
                if entry['status'] != 'healthy' and entry['error']:
                    incidents.append({
                        'component': component,
                        'timestamp': entry['timestamp'].isoformat(),
                        'status': entry['status'],
                        'error': entry['error']
                    })
        
        # Sort by timestamp and return last 10 incidents
        incidents.sort(key=lambda x: x['timestamp'], reverse=True)
        return incidents[:10]
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health data"""
        recommendations = []
        
        for component, status in self.sla_status.items():
            if status.status == "degraded":
                if status.response_time_avg > self.sla_targets[component]['response_time']:
                    recommendations.append(f"Optimize {component} performance - current avg: {status.response_time_avg:.2f}ms")
                if status.error_rate > self.sla_targets[component]['error_rate']:
                    recommendations.append(f"Investigate {component} errors - current rate: {status.error_rate:.2f}%")
            
            if status.uptime_percentage < self.sla_targets[component]['uptime']:
                recommendations.append(f"Improve {component} reliability - current uptime: {status.uptime_percentage:.2f}%")
        
        return recommendations

# Health check endpoints
@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Comprehensive health check endpoint"""
    health_manager = HealthCheckManager()
    results = await health_manager.perform_health_checks()
    
    overall_status = "healthy"
    for result in results.values():
        if result.status != "healthy":
            overall_status = "unhealthy"
            break
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {comp: result.__dict__ for comp, result in results.items()}
    }

@app.get("/health/detailed", tags=["Monitoring"])
async def detailed_health_check():
    """Detailed health check with SLA information"""
    health_manager = HealthCheckManager()
    await health_manager.perform_health_checks()
    report = health_manager.generate_health_report()
    
    return report

@app.get("/health/startup", tags=["Monitoring"])
async def startup_health_check():
    """Startup health check for Kubernetes"""
    # Check critical dependencies only
    critical_checks = ['database', 'redis', 'kafka']
    health_manager = HealthCheckManager()
    
    results = {}
    for check in critical_checks:
        if check in health_manager.checks:
            results[check] = await health_manager.checks[check]()
    
    # All critical services must be healthy
    if all(status == "healthy" for status in results.values()):
        return {"status": "healthy", "components": results}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "components": results}
        )

@app.get("/health/ready", tags=["Monitoring"])
async def readiness_health_check():
    """Readiness health check for Kubernetes"""
    # Check all dependencies
    health_manager = HealthCheckManager()
    results = await health_manager.perform_health_checks()
    
    # Allow degraded but not unhealthy
    if any(result.status == "unhealthy" for result in results.values()):
        return JSONResponse(
            status_code=503,
            content={"status": "unready", "components": {comp: result.__dict__ for comp, result in results.items()}}
        )
    else:
        return {"status": "ready", "components": {comp: result.__dict__ for comp, result in results.items()}}