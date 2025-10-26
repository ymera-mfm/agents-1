"""
Performance Monitoring System
Tracks system metrics, performance, and health indicators
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import json


class PerformanceMonitor:
    """Monitor system performance and health"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.metrics_history = deque(maxlen=1000)
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'response_time_ms': 5000,
            'error_rate': 0.05
        }
        self.monitoring_active = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
    def _monitor_loop(self, interval: int):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                self._check_alerts(metrics)
                time.sleep(interval)
            except Exception as e:
                print(f"Monitoring error: {e}")
                
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            disk_usage = psutil.disk_usage('/')
        except:
            disk_usage = psutil.disk_usage('C:\\')
            
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'per_cpu': psutil.cpu_percent(interval=1, percpu=True)
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used
            },
            'disk': {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': disk_usage.percent
            },
            'network': self._get_network_stats(),
            'process': self._get_process_stats()
        }
        
    def _get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'errin': net_io.errin,
            'errout': net_io.errout
        }
        
    def _get_process_stats(self) -> Dict[str, Any]:
        """Get current process statistics"""
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            'cpu_percent': process.cpu_percent(interval=1),
            'memory_percent': process.memory_percent(),
            'memory_info': {
                'rss': mem_info.rss,
                'vms': mem_info.vms
            },
            'num_threads': process.num_threads()
        }
        
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check metrics against alert thresholds"""
        alerts = []
        
        if metrics['cpu']['percent'] > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'value': metrics['cpu']['percent'],
                'threshold': self.alert_thresholds['cpu_percent']
            })
            
        if metrics['memory']['percent'] > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'value': metrics['memory']['percent'],
                'threshold': self.alert_thresholds['memory_percent']
            })
            
        if alerts:
            self._handle_alerts(alerts)
            
    def _handle_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle performance alerts"""
        for alert in alerts:
            print(f"ALERT: {alert['type']} - {alert['value']:.2f}% exceeds threshold {alert['threshold']}%")
            
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        if not self.metrics_history:
            return {'error': 'No metrics collected yet'}
            
        recent_metrics = list(self.metrics_history)[-100:]
        
        cpu_values = [m['cpu']['percent'] for m in recent_metrics]
        memory_values = [m['memory']['percent'] for m in recent_metrics]
        
        return {
            'summary': {
                'metrics_collected': len(self.metrics_history),
                'time_range': {
                    'start': recent_metrics[0]['timestamp'],
                    'end': recent_metrics[-1]['timestamp']
                }
            },
            'cpu': {
                'current': cpu_values[-1],
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory': {
                'current': memory_values[-1],
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'latest_metrics': recent_metrics[-1]
        }


class RequestTracker:
    """Track API request metrics"""
    
    def __init__(self):
        self.requests = deque(maxlen=10000)
        self.error_count = 0
        self.total_count = 0
        
    def track_request(self, endpoint: str, duration_ms: float, success: bool, status_code: int):
        """Track a single request"""
        self.total_count += 1
        if not success:
            self.error_count += 1
            
        self.requests.append({
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'duration_ms': duration_ms,
            'success': success,
            'status_code': status_code
        })
        
    def get_stats(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get request statistics for time window"""
        cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_requests = [
            r for r in self.requests 
            if datetime.fromisoformat(r['timestamp']) > cutoff
        ]
        
        if not recent_requests:
            return {'error': 'No requests in time window'}
            
        durations = [r['duration_ms'] for r in recent_requests]
        successes = sum(1 for r in recent_requests if r['success'])
        
        return {
            'time_window_minutes': time_window_minutes,
            'total_requests': len(recent_requests),
            'successful_requests': successes,
            'failed_requests': len(recent_requests) - successes,
            'success_rate': successes / len(recent_requests),
            'error_rate': (len(recent_requests) - successes) / len(recent_requests),
            'response_times': {
                'average_ms': sum(durations) / len(durations),
                'median_ms': sorted(durations)[len(durations) // 2],
                'p95_ms': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations),
                'p99_ms': sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 100 else max(durations),
                'max_ms': max(durations),
                'min_ms': min(durations)
            }
        }


class HealthChecker:
    """System health checker"""
    
    def __init__(self):
        self.health_checks = {}
        
    def register_check(self, name: str, check_func):
        """Register a health check function"""
        self.health_checks[name] = check_func
        
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.health_checks.items():
            try:
                result = await check_func()
                results[name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'details': result
                }
                if not result:
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e)
                }
                overall_healthy = False
                
        return {
            'overall_status': 'healthy' if overall_healthy else 'unhealthy',
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }
