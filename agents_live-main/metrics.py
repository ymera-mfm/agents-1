"""Metrics Collector for Prometheus"""

from typing import Dict, List, Optional, Any

from prometheus_client import Counter, Gauge, Histogram, Summary
import structlog


class MetricsCollector:
    """Collects and exposes metrics for Prometheus"""
    
    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)
        
        # Counters
        self.counters = {}
        
        # Gauges
        self.gauges = {}
        
        # Histograms
        self.histograms = {}
        
        # Initialize common metrics
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize common metrics"""
        # Project Agent metrics
        self.counters['project_agent_submissions_total'] = Counter(
            'project_agent_submissions_total',
            'Total submissions received',
            ['agent']
        )
        
        self.counters['project_agent_integrations_total'] = Counter(
            'project_agent_integrations_total',
            'Total successful integrations',
            ['agent']
        )
        
        self.counters['project_agent_rejections_total'] = Counter(
            'project_agent_rejections_total',
            'Total rejections',
            ['agent']
        )
        
        self.counters['project_agent_errors_total'] = Counter(
            'project_agent_errors_total',
            'Total errors',
            ['type']
        )
        
        # Learning Agent metrics
        self.counters['learning_agent_knowledge_received'] = Counter(
            'learning_agent_knowledge_received',
            'Knowledge items received',
            ['source']
        )
        
        self.counters['learning_agent_knowledge_provided'] = Counter(
            'learning_agent_knowledge_provided',
            'Knowledge items provided',
            ['agent']
        )
        
        self.counters['learning_agent_feedback_received'] = Counter(
            'learning_agent_feedback_received',
            'Feedback received',
            ['agent']
        )
        
        self.counters['learning_agent_errors'] = Counter(
            'learning_agent_errors',
            'Learning agent errors',
            ['type']
        )
        
        # System metrics
        self.gauges['active_sessions'] = Gauge(
            'active_sessions',
            'Number of active sessions'
        )
        
        self.gauges['queue_size'] = Gauge(
            'queue_size',
            'Size of processing queue'
        )
        
        # Response time histogram
        self.histograms['request_duration_seconds'] = Histogram(
            'request_duration_seconds',
            'Request duration in seconds',
            ['endpoint', 'method']
        )
    
    def increment_counter(self, name: str, labels: dict = None) -> None:
        """Increment a counter metric"""
        try:
            if name in self.counters:
                if labels:
                    self.counters[name].labels(**labels).inc()
                else:
                    self.counters[name].inc()
        except Exception as e:
            self.logger.error(f"Error incrementing counter {name}: {e}")
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric"""
        try:
            if name in self.gauges:
                self.gauges[name].set(value)
        except Exception as e:
            self.logger.error(f"Error setting gauge {name}: {e}")
    
    def observe_histogram(self, name: str, value: float, labels: dict = None) -> None:
        """Observe a histogram metric"""
        try:
            if name in self.histograms:
                if labels:
                    self.histograms[name].labels(**labels).observe(value)
                else:
                    self.histograms[name].observe(value)
        except Exception as e:
            self.logger.error(f"Error observing histogram {name}: {e}")
