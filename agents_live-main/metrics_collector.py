"""
Metrics Collector
Performance monitoring and analytics for the Project Agent
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Comprehensive Metrics Collection System
    
    Tracks:
    - Request/response times
    - Success/failure rates
    - Resource utilization
    - Agent performance
    - Build statistics
    - Quality scores
    """
    
    def __init__(self):
        # Counters
        self.counters: Dict[str, int] = defaultdict(int)
        
        # Gauges (current values)
        self.gauges: Dict[str, float] = defaultdict(float)
        
        # Histograms (time series)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Response times
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Project-specific metrics
        self.project_metrics: Dict[str, Dict] = defaultdict(lambda: {
            'submissions_total': 0,
            'submissions_approved': 0,
            'submissions_rejected': 0,
            'avg_quality_score': 0.0,
            'builds_total': 0,
            'builds_successful': 0,
            'avg_build_time': 0.0
        })
        
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize metrics collector"""
        self.is_initialized = True
        logger.info("✓ Metrics collector initialized")
    
    # =========================================================================
    # COUNTER OPERATIONS
    # =========================================================================
    
    def increment_counter(self, metric_name: str, labels: Optional[Dict[str, str]] = None, value: int = 1):
        """Increment counter metric"""
        key = self._build_metric_key(metric_name, labels)
        self.counters[key] += value
    
    def get_counter(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get counter value"""
        key = self._build_metric_key(metric_name, labels)
        return self.counters.get(key, 0)
    
    # =========================================================================
    # GAUGE OPERATIONS
    # =========================================================================
    
    def set_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value"""
        key = self._build_metric_key(metric_name, labels)
        self.gauges[key] = value
    
    def get_gauge(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value"""
        key = self._build_metric_key(metric_name, labels)
        return self.gauges.get(key, 0.0)
    
    # =========================================================================
    # HISTOGRAM OPERATIONS
    # =========================================================================
    
    def observe_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Add observation to histogram"""
        key = self._build_metric_key(metric_name, labels)
        self.histograms[key].append({
            'value': value,
            'timestamp': time.time()
        })
    
    def get_histogram_stats(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> Dict:
        """Get histogram statistics"""
        key = self._build_metric_key(metric_name, labels)
        observations = self.histograms.get(key, deque())
        
        if not observations:
            return {'count': 0, 'min': 0, 'max': 0, 'avg': 0, 'p50': 0, 'p95': 0, 'p99': 0}
        
        values = sorted([obs['value'] for obs in observations])
        count = len(values)
        
        return {
            'count': count,
            'min': values[0],
            'max': values[-1],
            'avg': sum(values) / count,
            'p50': values[int(count * 0.5)],
            'p95': values[int(count * 0.95)] if count > 20 else values[-1],
            'p99': values[int(count * 0.99)] if count > 100 else values[-1]
        }
    
    # =========================================================================
    # RESPONSE TIME TRACKING
    # =========================================================================
    
    def record_response_time(self, endpoint: str, duration_ms: float):
        """Record API endpoint response time"""
        self.response_times[endpoint].append(duration_ms)
        self.observe_histogram(f'response_time_{endpoint}', duration_ms)
    
    def get_response_time_stats(self, endpoint: str) -> Dict:
        """Get response time statistics for endpoint"""
        times = list(self.response_times.get(endpoint, deque()))
        
        if not times:
            return {'count': 0, 'avg': 0, 'min': 0, 'max': 0}
        
        return {
            'count': len(times),
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }
    
    # =========================================================================
    # PROJECT-SPECIFIC METRICS
    # =========================================================================
    
    def record_submission(self, project_id: str, status: str, quality_score: Optional[float] = None):
        """Record submission metrics"""
        metrics = self.project_metrics[project_id]
        metrics['submissions_total'] += 1
        
        if status == 'approved':
            metrics['submissions_approved'] += 1
        elif status == 'rejected':
            metrics['submissions_rejected'] += 1
        
        if quality_score is not None:
            # Update running average
            total = metrics['submissions_total']
            current_avg = metrics['avg_quality_score']
            metrics['avg_quality_score'] = (current_avg * (total - 1) + quality_score) / total
    
    def record_build(self, project_id: str, success: bool, build_time_seconds: float):
        """Record build metrics"""
        metrics = self.project_metrics[project_id]
        metrics['builds_total'] += 1
        
        if success:
            metrics['builds_successful'] += 1
        
        # Update running average build time
        total = metrics['builds_total']
        current_avg = metrics['avg_build_time']
        metrics['avg_build_time'] = (current_avg * (total - 1) + build_time_seconds) / total
    
    def get_project_metrics(self, project_id: str) -> Dict:
        """Get metrics for specific project"""
        return dict(self.project_metrics.get(project_id, {}))
    
    # =========================================================================
    # AGGREGATED METRICS
    # =========================================================================
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {
                key: self.get_histogram_stats(key) 
                for key in self.histograms.keys()
            },
            'response_times': {
                endpoint: self.get_response_time_stats(endpoint)
                for endpoint in self.response_times.keys()
            },
            'system': self._get_system_metrics()
        }
    
    def _get_system_metrics(self) -> Dict:
        """Get system-level metrics"""
        return {
            'total_requests': self.get_counter('requests_total'),
            'total_errors': self.get_counter('errors_total'),
            'active_projects': len(self.project_metrics),
            'total_submissions': sum(m['submissions_total'] for m in self.project_metrics.values()),
            'total_builds': sum(m['builds_total'] for m in self.project_metrics.values()),
            'avg_quality_score': self._calculate_global_avg_quality(),
            'success_rate': self._calculate_success_rate()
        }
    
    def _calculate_global_avg_quality(self) -> float:
        """Calculate global average quality score"""
        if not self.project_metrics:
            return 0.0
        
        scores = [m['avg_quality_score'] for m in self.project_metrics.values() 
                 if m['submissions_total'] > 0]
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_submissions = sum(m['submissions_total'] for m in self.project_metrics.values())
        approved_submissions = sum(m['submissions_approved'] for m in self.project_metrics.values())
        
        if total_submissions == 0:
            return 0.0
        
        return (approved_submissions / total_submissions) * 100
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _build_metric_key(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Build metric key with labels"""
        if not labels:
            return metric_name
        
        label_str = ','.join(f'{k}={v}' for k, v in sorted(labels.items()))
        return f'{metric_name}{{{label_str}}}'
    
    async def reset_metrics(self):
        """Reset all metrics (use with caution)"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.response_times.clear()
        self.project_metrics.clear()
        
        logger.warning("All metrics have been reset")
    
    async def export_metrics_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            lines.append(f'{key} {value}')
        
        # Gauges
        for key, value in self.gauges.items():
            lines.append(f'{key} {value}')
        
        # Histograms
        for key, observations in self.histograms.items():
            stats = self.get_histogram_stats(key.split('{')[0])
            lines.append(f'{key}_count {stats["count"]}')
            lines.append(f'{key}_sum {stats["avg"] * stats["count"]}')
            lines.append(f'{key}_avg {stats["avg"]}')
        
        return '\n'.join(lines)
    
    async def health_check(self) -> bool:
        """Check metrics collector health"""
        return self.is_initialized
    
    async def shutdown(self):
        """Shutdown metrics collector"""
        logger.info("Metrics collector shutdown complete")


class MetricsMiddleware:
    """
    FastAPI middleware for automatic metrics collection
    """
    
    def __init__(self, app, metrics_collector: MetricsCollector):
        self.app = app
        self.metrics = metrics_collector
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Increment request counter
        self.metrics.increment_counter('requests_total', {
            'method': scope['method'],
            'path': scope['path']
        })
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration_ms = (time.time() - start_time) * 1000
                
                # Record response time
                self.metrics.record_response_time(scope['path'], duration_ms)
                
                # Increment status code counter
                status_code = message["status"]
                self.metrics.increment_counter('responses_total', {
                    'method': scope['method'],
                    'path': scope['path'],
                    'status': str(status_code)
                })
                
                # Increment error counter if error status
                if status_code >= 400:
                    self.metrics.increment_counter('errors_total', {
                        'method': scope['method'],
                        'path': scope['path'],
                        'status': str(status_code)
                    })
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
