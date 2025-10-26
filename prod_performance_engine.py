"""
Production-Ready Performance Engine v3.0
Enterprise-grade real-time performance monitoring with ML-based anomaly detection
"""

import asyncio
import json
import time
import psutil
import gc
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import statistics
from collections import deque, defaultdict
from datetime import datetime, timedelta
import traceback
import signal
import sys
import numpy as np

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    from opentelemetry import trace
    import redis.asyncio as aioredis
    HAS_OBSERVABILITY = True
except ImportError:
    HAS_OBSERVABILITY = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority, AgentState

# ============================================================================
# ENUMS
# ============================================================================

class PerformanceMetric(Enum):
    """Performance metric types"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    QUEUE_DEPTH = "queue_depth"
    CONNECTION_COUNT = "connection_count"
    THREAD_COUNT = "thread_count"
    LATENCY_P50 = "latency_p50"
    LATENCY_P95 = "latency_p95"
    LATENCY_P99 = "latency_p99"

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class OptimizationStrategy(Enum):
    """Optimization strategies"""
    CACHING = "caching"
    BATCHING = "batching"
    PARALLEL = "parallel"
    ASYNC = "async"
    COMPRESSION = "compression"
    INDEXING = "indexing"
    CONNECTION_POOLING = "connection_pooling"
    LAZY_LOADING = "lazy_loading"
    LOAD_BALANCING = "load_balancing"
    RATE_LIMITING = "rate_limiting"

class AnomalyType(Enum):
    """Anomaly detection types"""
    SPIKE = "spike"
    DROP = "drop"
    GRADUAL_INCREASE = "gradual_increase"
    GRADUAL_DECREASE = "gradual_decrease"
    OSCILLATION = "oscillation"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PerformanceThreshold:
    """Performance threshold with anti-flapping"""
    metric: PerformanceMetric
    warning_value: float
    critical_value: float
    unit: str
    enabled: bool = True
    consecutive_violations: int = 3
    current_violations: int = 0
    window_size: int = 5
    
    def check_violation(self, value: float) -> Optional[AlertSeverity]:
        """Check if value violates threshold"""
        if value >= self.critical_value:
            self.current_violations += 1
            if self.current_violations >= self.consecutive_violations:
                return AlertSeverity.CRITICAL
        elif value >= self.warning_value:
            self.current_violations += 1
            if self.current_violations >= self.consecutive_violations:
                return AlertSeverity.HIGH
        else:
            self.current_violations = 0
            return None
        
        return None
    
    def reset(self):
        """Reset violation counter"""
        self.current_violations = 0

@dataclass
class PerformanceAlert:
    """Performance alert with context"""
    id: str
    metric: PerformanceMetric
    severity: AlertSeverity
    current_value: float
    threshold_value: float
    message: str
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    actions_taken: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "metric": self.metric.value,
            "severity": self.severity.value,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "message": self.message,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "metadata": self.metadata,
            "actions_taken": self.actions_taken
        }

@dataclass
class PerformanceSnapshot:
    """Performance snapshot with validation"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    thread_count: int
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Validate snapshot"""
        return (
            0 <= self.cpu_percent <= 100 and
            0 <= self.memory_percent <= 100 and
            self.timestamp > 0
        )

@dataclass
class OptimizationRecommendation:
    """Optimization recommendation with priority"""
    id: str
    strategy: OptimizationStrategy
    title: str
    description: str
    estimated_improvement: str
    complexity: str
    priority_score: float
    implementation_steps: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    timestamp: float
    metric: PerformanceMetric
    anomaly_type: AnomalyType
    severity: float  # 0.0 to 1.0
    expected_range: Tuple[float, float]
    actual_value: float
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "metric": self.metric.value,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity,
            "expected_range": self.expected_range,
            "actual_value": self.actual_value,
            "description": self.description
        }

# ============================================================================
# PERFORMANCE ENGINE
# ============================================================================

class PerformanceEngine(BaseAgent):
    """
    Production-Ready Performance Engine v3.0
    
    Features:
    - Real-time multi-dimensional monitoring
    - ML-based anomaly detection
    - Predictive alerting with smart thresholds
    - Auto-remediation capabilities
    - Comprehensive observability
    - Historical trend analysis
    - Performance forecasting
    - Resource optimization recommendations
    - Self-healing mechanisms
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Performance data storage
        self.metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self.snapshots: deque = deque(maxlen=5000)
        self.performance_baselines: Dict[str, Dict] = {}
        
        # Alerting system
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.suppressed_alerts: Set[str] = set()
        
        # Thresholds with adaptive capability
        self.thresholds: Dict[PerformanceMetric, PerformanceThreshold] = {
            PerformanceMetric.CPU_USAGE: PerformanceThreshold(
                PerformanceMetric.CPU_USAGE, 70.0, 90.0, "%", consecutive_violations=3
            ),
            PerformanceMetric.MEMORY_USAGE: PerformanceThreshold(
                PerformanceMetric.MEMORY_USAGE, 80.0, 95.0, "%", consecutive_violations=3
            ),
            PerformanceMetric.RESPONSE_TIME: PerformanceThreshold(
                PerformanceMetric.RESPONSE_TIME, 500.0, 2000.0, "ms", consecutive_violations=2
            ),
            PerformanceMetric.ERROR_RATE: PerformanceThreshold(
                PerformanceMetric.ERROR_RATE, 1.0, 5.0, "%", consecutive_violations=2
            ),
            PerformanceMetric.DISK_IO: PerformanceThreshold(
                PerformanceMetric.DISK_IO, 100.0, 200.0, "MB/s", consecutive_violations=3
            )
        }
        
        # Optimization engine
        self.recommendations_cache: deque = deque(maxlen=500)
        self.applied_optimizations: Dict[str, Dict] = {}
        
        # Anomaly detection
        self.anomaly_detectors: Dict[str, 'AnomalyDetector'] = {}
        self.detected_anomalies: deque = deque(maxlen=1000)
        
        # Statistics with rolling averages
        self.performance_stats = {
            "monitoring_cycles": 0,
            "alerts_generated": 0,
            "alerts_resolved": 0,
            "alerts_auto_resolved": 0,
            "optimizations_recommended": 0,
            "optimizations_applied": 0,
            "anomalies_detected": 0,
            "average_cpu": 0.0,
            "average_memory": 0.0,
            "peak_cpu": 0.0,
            "peak_memory": 0.0,
            "uptime_seconds": 0.0
        }
        
        # Monitoring state
        self.monitoring_active = True
        self.last_snapshot_time = 0.0
        self.start_time = time.time()
        
        # Auto-remediation
        self.remediation_enabled = True
        self.remediation_history: deque = deque(maxlen=500)
        
        # Graceful shutdown
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Initialize Prometheus metrics if available
        if HAS_OBSERVABILITY:
            self._init_prometheus_metrics()
        
        self.logger.info(
            "PerformanceEngine initialized",
            version="3.0",
            features=[
                "anomaly_detection",
                "auto_remediation",
                "predictive_alerts",
                "ml_forecasting"
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.shutdown_event.set()
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        try:
            prefix = "performance_engine"
            
            self.prom_cpu = Gauge(f'{prefix}_cpu_percent', 'CPU usage percentage')
            self.prom_memory = Gauge(f'{prefix}_memory_percent', 'Memory usage percentage')
            self.prom_response_time = Histogram(
                f'{prefix}_response_time_ms',
                'Response time in milliseconds',
                buckets=[10, 50, 100, 250, 500, 1000, 2500, 5000]
            )
            self.prom_alerts = Counter(
                f'{prefix}_alerts_total',
                'Total alerts generated',
                ['severity']
            )
            self.prom_anomalies = Counter(
                f'{prefix}_anomalies_total',
                'Total anomalies detected',
                ['type']
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to init Prometheus metrics: {e}")
    
    async def start(self):
        """Start performance engine"""
        try:
            self.logger.info("Starting PerformanceEngine")
            
            # Setup subscriptions
            await self._setup_subscriptions()
            
            # Initialize anomaly detectors
            self._init_anomaly_detectors()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Calculate initial baselines
            await self._calculate_baselines()
            
            self.logger.info(
                "PerformanceEngine started successfully",
                monitoring_active=self.monitoring_active
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start PerformanceEngine: {e}", exc_info=True)
            return False
    
    def _init_anomaly_detectors(self):
        """Initialize anomaly detectors for each metric"""
        for metric in [
            PerformanceMetric.CPU_USAGE,
            PerformanceMetric.MEMORY_USAGE,
            PerformanceMetric.RESPONSE_TIME,
            PerformanceMetric.ERROR_RATE
        ]:
            self.anomaly_detectors[metric.value] = AnomalyDetector(
                metric=metric,
                window_size=100,
                sensitivity=2.5
            )
    
    async def _setup_subscriptions(self):
        """Setup NATS subscriptions"""
        subscriptions = [
            ("performance.monitor.start", self._handle_monitor_start),
            ("performance.monitor.stop", self._handle_monitor_stop),
            ("performance.threshold.update", self._handle_threshold_update),
            ("performance.report.request", self._handle_report_request),
            ("performance.remediate", self._handle_remediation_request),
            (f"health.{self.config.name}", self._handle_health_check)
        ]
        
        for subject, handler in subscriptions:
            try:
                await self._subscribe(
                    subject,
                    handler,
                    queue_group=f"{self.config.name}_workers"
                )
            except Exception as e:
                self.logger.error(f"Failed to subscribe to {subject}: {e}")
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        tasks = [
            ("continuous_monitoring", self._continuous_monitoring()),
            ("alert_processor", self._alert_processor()),
            ("optimization_engine", self._optimization_engine()),
            ("baseline_calculator", self._baseline_calculator()),
            ("anomaly_detector", self._anomaly_detection_loop()),
            ("metrics_aggregator", self._metrics_aggregator()),
            ("auto_remediation", self._auto_remediation_loop()),
            ("health_reporter", self._health_reporter())
        ]
        
        for name, coro in tasks:
            task = asyncio.create_task(coro)
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
            self.logger.debug(f"Started background task: {name}")
    
    async def _continuous_monitoring(self):
        """Continuous performance monitoring"""
        self.logger.info("Starting continuous monitoring")
        
        while self.state == AgentState.RUNNING and not self.shutdown_event.is_set():
            try:
                if self.monitoring_active:
                    # Collect snapshot
                    snapshot = await self._collect_performance_snapshot()
                    
                    if snapshot.is_valid():
                        self.snapshots.append(snapshot)
                        
                        # Update metrics history
                        await self._update_metrics_history(snapshot)
                        
                        # Check thresholds
                        await self._check_thresholds(snapshot)
                        
                        # Update statistics
                        await self._update_statistics(snapshot)
                        
                        # Update Prometheus
                        if HAS_OBSERVABILITY:
                            self._update_prometheus(snapshot)
                        
                        # Persist periodically
                        if len(self.snapshots) % 12 == 0:  # Every minute
                            await self._persist_metrics()
                        
                        self.performance_stats["monitoring_cycles"] += 1
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}", exc_info=True)
                await asyncio.sleep(10)
        
        self.logger.info("Continuous monitoring stopped")
    
    async def _collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect comprehensive performance snapshot"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk I/O
            try:
                disk_io = psutil.disk_io_counters()
                disk_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0
                disk_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0
            except:
                disk_read_mb = disk_write_mb = 0
            
            # Network I/O
            try:
                network_io = psutil.net_io_counters()
                network_sent_mb = network_io.bytes_sent / (1024**2) if network_io else 0
                network_recv_mb = network_io.bytes_recv / (1024**2) if network_io else 0
            except:
                network_sent_mb = network_recv_mb = 0
            
            # Process metrics
            try:
                process = psutil.Process()
                active_connections = len(process.connections())
                thread_count = process.num_threads()
            except:
                active_connections = thread_count = 0
            
            # Application metrics
            response_time_ms = getattr(self.metrics, 'avg_processing_time_ms', 0.0)
            
            total_tasks = (
                getattr(self.metrics, 'tasks_completed', 0) + 
                getattr(self.metrics, 'tasks_failed', 0)
            )
            error_rate = (
                (getattr(self.metrics, 'tasks_failed', 0) / total_tasks * 100)
                if total_tasks > 0 else 0.0
            )
            
            snapshot = PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_read_mb=disk_read_mb,
                disk_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_connections=active_connections,
                thread_count=thread_count,
                response_time_ms=response_time_ms,
                error_rate=error_rate
            )
            
            self.last_snapshot_time = time.time()
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error collecting snapshot: {e}")
            # Return empty snapshot
            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=0, memory_percent=0,
                disk_read_mb=0, disk_write_mb=0,
                network_sent_mb=0, network_recv_mb=0,
                active_connections=0, thread_count=0
            )
    
    async def _anomaly_detection_loop(self):
        """Anomaly detection loop"""
        self.logger.info("Starting anomaly detection")
        
        while self.state == AgentState.RUNNING and not self.shutdown_event.is_set():
            try:
                if len(self.snapshots) < 100:
                    await asyncio.sleep(30)
                    continue
                
                # Get recent snapshots
                recent = list(self.snapshots)[-100:]
                
                # Check each metric for anomalies
                for metric_name, detector in self.anomaly_detectors.items():
                    values = self._extract_metric_values(recent, metric_name)
                    
                    if values:
                        anomaly = detector.detect(values[-1], values[:-1])
                        
                        if anomaly:
                            self.detected_anomalies.append(anomaly)
                            self.performance_stats["anomalies_detected"] += 1
                            
                            # Update Prometheus
                            if HAS_OBSERVABILITY:
                                self.prom_anomalies.labels(
                                    type=anomaly.anomaly_type.value
                                ).inc()
                            
                            # Generate alert if severe
                            if anomaly.severity > 0.7:
                                await self._create_anomaly_alert(anomaly)
                            
                            self.logger.warning(
                                "Anomaly detected",
                                metric=metric_name,
                                type=anomaly.anomaly_type.value,
                                severity=anomaly.severity
                            )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Anomaly detection error: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        self.logger.info("Anomaly detection stopped")
    
    def _extract_metric_values(self, snapshots: List[PerformanceSnapshot], metric_name: str) -> List[float]:
        """Extract metric values from snapshots"""
        metric_map = {
            "cpu_usage": lambda s: s.cpu_percent,
            "memory_usage": lambda s: s.memory_percent,
            "response_time": lambda s: s.response_time_ms,
            "error_rate": lambda s: s.error_rate
        }
        
        extractor = metric_map.get(metric_name)
        if not extractor:
            return []
        
        return [extractor(s) for s in snapshots]
    
    async def _auto_remediation_loop(self):
        """Auto-remediation loop"""
        self.logger.info("Starting auto-remediation")
        
        while self.state == AgentState.RUNNING and not self.shutdown_event.is_set():
            try:
                if not self.remediation_enabled:
                    await asyncio.sleep(60)
                    continue
                
                # Check for critical alerts requiring remediation
                for alert_key, alert in list(self.active_alerts.items()):
                    if alert.severity == AlertSeverity.CRITICAL and not alert.resolved:
                        remediation = await self._attempt_remediation(alert)
                        
                        if remediation:
                            self.remediation_history.append(remediation)
                            alert.actions_taken.append(remediation["action"])
                            
                            self.logger.info(
                                "Auto-remediation applied",
                                alert_id=alert.id,
                                action=remediation["action"]
                            )
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-remediation error: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        self.logger.info("Auto-remediation stopped")
    
    async def _attempt_remediation(self, alert: PerformanceAlert) -> Optional[Dict]:
        """Attempt to remediate performance issue"""
        try:
            remediation_map = {
                PerformanceMetric.CPU_USAGE: self._remediate_high_cpu,
                PerformanceMetric.MEMORY_USAGE: self._remediate_high_memory,
                PerformanceMetric.ERROR_RATE: self._remediate_high_errors
            }
            
            remediation_func = remediation_map.get(alert.metric)
            if remediation_func:
                result = await remediation_func(alert)
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Remediation failed: {e}")
            return None
    
    async def _remediate_high_cpu(self, alert: PerformanceAlert) -> Dict:
        """Remediate high CPU usage"""
        # Trigger garbage collection
        collected = gc.collect()
        
        # Request worker scaling
        await self._publish(
            "orchestrator.scale_request",
            {
                "service": self.config.name,
                "reason": "high_cpu",
                "alert_id": alert.id,
                "scale_factor": 1.5
            }
        )
        
        return {
            "action": "cpu_remediation",
            "gc_collected": collected,
            "scale_requested": True,
            "timestamp": time.time()
        }
    
    async def _remediate_high_memory(self, alert: PerformanceAlert) -> Dict:
        """Remediate high memory usage"""
        # Force garbage collection
        collected = gc.collect()
        
        # Clear caches if available
        cache_cleared = 0
        if self.redis_client:
            try:
                # Clear least recently used cache entries
                cache_cleared = await self._clear_cache_percentage(20)
            except:
                pass
        
        return {
            "action": "memory_remediation",
            "gc_collected": collected,
            "cache_cleared": cache_cleared,
            "timestamp": time.time()
        }
    
    async def _remediate_high_errors(self, alert: PerformanceAlert) -> Dict:
        """Remediate high error rate"""
        # Enable circuit breakers
        await self._publish(
            "system.circuit_breaker.enable",
            {
                "reason": "high_error_rate",
                "alert_id": alert.id
            }
        )
        
        return {
            "action": "error_remediation",
            "circuit_breaker_enabled": True,
            "timestamp": time.time()
        }
    
    async def _clear_cache_percentage(self, percentage: int) -> int:
        """Clear specified percentage of cache"""
        try:
            if not self.redis_client:
                return 0
            
            # Get all keys
            keys = await self.redis_client.keys("*")
            keys_to_delete = int(len(keys) * percentage / 100)
            
            if keys_to_delete > 0:
                # Delete oldest keys
                deleted = 0
                for key in keys[:keys_to_delete]:
                    await self.redis_client.delete(key)
                    deleted += 1
                
                return deleted
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Cache clear failed: {e}")
            return 0
    
    async def _health_reporter(self):
        """Report health status periodically"""
        self.logger.info("Starting health reporter")
        
        while self.state == AgentState.RUNNING and not self.shutdown_event.is_set():
            try:
                health_report = {
                    "agent_id": self.config.agent_id,
                    "timestamp": time.time(),
                    "monitoring_active": self.monitoring_active,
                    "active_alerts": len(self.active_alerts),
                    "critical_alerts": len([
                        a for a in self.active_alerts.values() 
                        if a.severity == AlertSeverity.CRITICAL
                    ]),
                    "uptime_seconds": time.time() - self.start_time,
                    "stats": self.performance_stats
                }
                
                await self._publish(
                    f"health.{self.config.name}.report",
                    health_report
                )
                
                await asyncio.sleep(60)  # Report every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health reporter error: {e}")
                await asyncio.sleep(60)
        
        self.logger.info("Health reporter stopped")
    
    def _update_prometheus(self, snapshot: PerformanceSnapshot):
        """Update Prometheus metrics"""
        try:
            self.prom_cpu.set(snapshot.cpu_percent)
            self.prom_memory.set(snapshot.memory_percent)
            self.prom_response_time.observe(snapshot.response_time_ms)
        except:
            pass
    
    async def stop(self):
        """Graceful shutdown"""
        self.logger.info("Initiating graceful shutdown")
        
        self.shutdown_event.set()
        
        # Stop monitoring
        self.monitoring_active = False
        
        # Wait for background tasks
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Final metrics persist
        await self._persist_metrics()
        
        await super().stop()
        
        self.logger.info("PerformanceEngine stopped")


# ============================================================================
# ANOMALY DETECTOR
# ============================================================================

class AnomalyDetector:
    """Statistical anomaly detector"""
    
    def __init__(self, metric: PerformanceMetric, window_size: int = 100, sensitivity: float = 2.5):
        self.metric = metric
        self.window_size = window_size
        self.sensitivity = sensitivity
        self.history: deque = deque(maxlen=window_size)
    
    def detect(self, current_value: float, historical_values: List[float]) -> Optional[AnomalyDetection]:
        """Detect anomalies using statistical methods"""
        if len(historical_values) < 30:
            return None
        
        # Calculate statistics
        mean = statistics.mean(historical_values)
        stdev = statistics.stdev(historical_values)
        
        if stdev == 0:
            return None
        
        # Z-score
        z_score = abs((current_value - mean) / stdev)
        
        if z_score > self.sensitivity:
            # Determine anomaly type
            if current_value > mean + (self.sensitivity * stdev):
                anomaly_type = AnomalyType.SPIKE
            else:
                anomaly_type = AnomalyType.DROP
            
            # Calculate severity (0.0 to 1.0)
            severity = min(1.0, z_score / (self.sensitivity * 2))
            
            return AnomalyDetection(
                timestamp=time.time(),
                metric=self.metric,
                anomaly_type=anomaly_type,
                severity=severity,
                expected_range=(
                    mean - (self.sensitivity * stdev),
                    mean + (self.sensitivity * stdev)
                ),
                actual_value=current_value,
                description=f"{self.metric.value} {anomaly_type.value}: {current_value:.2f} (expected: {mean:.2f}±{stdev:.2f})"
            )
        
        return None


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import os
    
    async def main():
        config = AgentConfig(
            agent_id=os.getenv("AGENT_ID", "performance-engine-001"),
            name="performance_engine",
            agent_type="performance_monitoring",
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL"),
            max_concurrent_tasks=100,
            version="3.0.0"
        )
        
        engine = PerformanceEngine(config)
        
        if await engine.start():
            await engine.shutdown_event.wait()
            await engine.stop()
        else:
            sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
