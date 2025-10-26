"""
Monitoring Agent - System health and metrics tracking
"""
from typing import Any, Dict, Optional
import asyncio
from datetime import datetime
import psutil

from base_agent import BaseAgent
from logger import logger


class MonitoringAgent(BaseAgent):
    """
    Agent responsible for monitoring system health and collecting metrics.
    Tracks CPU, memory, agent status, and performance metrics.
    """
    
    def __init__(self, agent_id: str = "monitoring_agent", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.metrics: Dict[str, Any] = {}
        self.alert_threshold = self.config.get("alert_threshold", 80)
        
    async def initialize(self) -> bool:
        """Initialize monitoring agent"""
        try:
            self.logger.info("Initializing Monitoring Agent")
            self.metrics = {
                "start_time": datetime.utcnow(),
                "total_checks": 0,
                "alerts": []
            }
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}", exc_info=True)
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process monitoring requests"""
        try:
            msg_type = message.get("type")
            
            if msg_type == "get_metrics":
                return await self.get_current_metrics()
            elif msg_type == "get_health":
                return await self.check_system_health()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def execute(self) -> Any:
        """Execute monitoring checks"""
        try:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            }
            
            # Check for alerts
            if cpu_percent > self.alert_threshold:
                await self.create_alert("high_cpu", f"CPU usage at {cpu_percent}%")
            
            if memory.percent > self.alert_threshold:
                await self.create_alert("high_memory", f"Memory usage at {memory.percent}%")
            
            self.metrics["latest"] = metrics
            self.metrics["total_checks"] += 1
            
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            self.logger.error(f"Error in monitoring: {e}", exc_info=True)
    
    async def create_alert(self, alert_type: str, message: str) -> None:
        """Create a system alert"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.metrics.setdefault("alerts", []).append(alert)
        self.logger.warning(f"Alert: {alert_type} - {message}")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_usage": disk.percent,
            "disk_free_gb": disk.free / (1024 * 1024 * 1024)
        }
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        latest = self.metrics.get("latest", {})
        
        health_status = "healthy"
        if latest.get("cpu_percent", 0) > self.alert_threshold:
            health_status = "degraded"
        if latest.get("memory_percent", 0) > self.alert_threshold:
            health_status = "degraded"
        
        return {
            "status": health_status,
            "metrics": latest,
            "alerts": self.metrics.get("alerts", [])[-10:]  # Last 10 alerts
        }
