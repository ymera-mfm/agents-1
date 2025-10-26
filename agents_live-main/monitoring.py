"""
YMERA Monitoring Service
Prometheus metrics and health monitoring
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from datetime import datetime

logger = logging.getLogger(__name__)


class MonitoringService:
    """Monitoring service with Prometheus metrics"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize monitoring service"""
        self.config = config
        self.enabled = config.get("enabled", True)
        self.prometheus_port = config.get("prometheus_port", 9090)
        
        # Define metrics
        self.tasks_submitted = Counter(
            'ymera_tasks_submitted_total',
            'Total number of learning tasks submitted',
            ['task_type']
        )
        
        self.tasks_completed = Counter(
            'ymera_tasks_completed_total',
            'Total number of learning tasks completed',
            ['task_type', 'status']
        )
        
        self.active_tasks = Gauge(
            'ymera_active_tasks',
            'Number of currently active learning tasks'
        )
        
        self.task_duration = Histogram(
            'ymera_task_duration_seconds',
            'Task execution duration in seconds',
            ['task_type']
        )
        
        self.patterns_detected = Counter(
            'ymera_patterns_detected_total',
            'Total number of patterns detected',
            ['pattern_type']
        )
        
        self.knowledge_entries = Gauge(
            'ymera_knowledge_entries_total',
            'Total number of knowledge base entries'
        )
        
        self.drift_detections = Counter(
            'ymera_drift_detections_total',
            'Total number of concept drift detections',
            ['drift_type']
        )
        
        self.system_health = Gauge(
            'ymera_system_health',
            'System health status (1=healthy, 0=unhealthy)'
        )
        
        self.initialized = False
        
        logger.info("Monitoring service initialized")
    
    async def initialize(self):
        """Initialize the monitoring service"""
        if not self.enabled:
            logger.info("Monitoring is disabled")
            return
        
        try:
            # Start Prometheus HTTP server
            start_http_server(self.prometheus_port)
            self.initialized = True
            self.system_health.set(1)
            logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
        except Exception as e:
            logger.error(f"Failed to start monitoring service: {str(e)}")
            raise
    
    async def record_metric(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a custom metric"""
        if not self.enabled or not self.initialized:
            return
        
        try:
            if metric_name == "tasks_submitted":
                self.tasks_submitted.labels(**(labels or {})).inc(value)
            elif metric_name == "tasks_completed":
                self.tasks_completed.labels(**(labels or {})).inc(value)
            elif metric_name == "patterns_detected":
                self.patterns_detected.labels(**(labels or {})).inc(value)
            elif metric_name == "drift_detections":
                self.drift_detections.labels(**(labels or {})).inc(value)
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {str(e)}")
    
    async def update_gauge(self, gauge_name: str, value: float):
        """Update a gauge metric"""
        if not self.enabled or not self.initialized:
            return
        
        try:
            if gauge_name == "active_tasks":
                self.active_tasks.set(value)
            elif gauge_name == "knowledge_entries":
                self.knowledge_entries.set(value)
            elif gauge_name == "system_health":
                self.system_health.set(value)
        except Exception as e:
            logger.error(f"Failed to update gauge {gauge_name}: {str(e)}")
    
    async def close(self):
        """Close monitoring service"""
        if self.initialized:
            self.system_health.set(0)
            self.initialized = False
            logger.info("Monitoring service closed")
