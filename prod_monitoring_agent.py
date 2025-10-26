"""
Production-Ready Real-Time Monitoring Agent v3.0
Enterprise-grade monitoring, alerting, and observability with ML-based anomaly detection
"""

import asyncio
import json
import time
# Optional dependencies - System monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False
# Optional dependencies - HTTP client
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    aiohttp = None
    HAS_AIOHTTP = False
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from collections import defaultdict, deque
import statistics
from datetime import datetime, timedelta
import traceback
import signal

# Optional dependencies
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    aiohttp = None
    HAS_AIOHTTP = False

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    import numpy as np
    from sklearn.ensemble import IsolationForest
    HAS_ML = True
except ImportError:
    HAS_ML = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority, AgentStatus
from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Metric:
    name: str
    type: MetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Alert:
    id: str
    rule_id: str
    severity: AlertSeverity
    message: str
    status: AlertStatus = AlertStatus.OPEN
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    escalation_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "labels": self.labels,
            "annotations": self.annotations,
            "escalation_count": self.escalation_count
        }

@dataclass
class AlertRule:
    id: str
    name: str
    query: str
    condition: str
    threshold: float
    severity: AlertSeverity
    duration: int = 60
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    consecutive_violations: int = 3
    current_violations: int = 0
    cooldown_seconds: int = 300
    last_triggered: float = 0.0
    
    def can_trigger(self) -> bool:
        """Check if rule can trigger alert"""
        return (
            self.enabled and
            time.time() - self.last_triggered >= self.cooldown_seconds
        )

@dataclass
class SLADefinition:
    name: str
    service_name: str
    uptime_target: float  # percentage
    response_time_target: float  # milliseconds
    error_rate_target: float  # percentage
    period_seconds: int = 86400  # 24 hours
    enabled: bool = True

# ============================================================================
# MONITORING AGENT
# ============================================================================

class RealTimeMonitoringAgent(BaseAgent):
    """
    Production-Ready Real-Time Monitoring Agent v3.0
    
    Features:
    - Multi-dimensional system monitoring (CPU, memory, disk, network)
    - Application performance tracking with custom metrics
    - ML-based anomaly detection
    - Intelligent alerting with escalation
    - SLA monitoring and reporting
    - Health check orchestration
    - Prometheus metrics export
    - Time-series data storage
    - Alert aggregation and deduplication
    - Auto-remediation triggers
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Metrics storage with time-series support
        self.metrics_buffer: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self.metric_definitions: Dict[str, Dict] = {}
        
        # Alerting system
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.alert_aggregation_window = 60  # seconds
        
        # System monitoring
        self.system_collectors = {}
        self.collection_interval = 10  # seconds
        
        # Performance baselines for anomaly detection
        self.performance_baselines: Dict[str, Dict] = {}
        
        # ML-based anomaly detectors
        self.anomaly_detectors: Dict[str, Any] = {}
        if HAS_ML:
            self._init_anomaly_detectors()
        
        # Health checks
        self.health_checks: Dict[str, Dict] = {}
        self.service_status: Dict[str, Dict] = {}
        
        # SLA tracking
        self.sla_definitions: Dict[str, SLADefinition] = {}
        self.sla_metrics: Dict[str, Dict] = {}
        
        # Statistics
        self.monitoring_stats = {
            "metrics_collected": 0,
            "alerts_generated": 0,
            "alerts_resolved": 0,
            "anomalies_detected": 0,
            "health_checks_performed": 0,
            "sla_violations": 0
        }
        
        # Prometheus metrics
        if HAS_ML:
            self._init_prometheus_metrics()
        
        # Graceful shutdown
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Initialize default alert rules
        self._setup_default_alert_rules()
        
        # Initialize system collectors
        self._setup_system_collectors()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown")
        self.shutdown_event.set()
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        try:
            prefix = "monitoring_agent"
            self.prom_metrics_collected = Counter(
                f'{prefix}_metrics_collected_total',
                'Total metrics collected'
            )
            self.prom_alerts_generated = Counter(
                f'{prefix}_alerts_generated_total',
                'Total alerts generated',
                ['severity']
            )
            self.prom_system_cpu = Gauge(
                f'{prefix}_system_cpu_percent',
                'System CPU usage'
            )
            self.prom_system_memory = Gauge(
                f'{prefix}_system_memory_percent',
                'System memory usage'
            )
        except Exception as e:
            self.logger.warning(f"Failed to init Prometheus metrics: {e}")
    
    def _init_anomaly_detectors(self):
        """Initialize ML-based anomaly detectors"""
        try:
            for metric_name in ['cpu_usage', 'memory_usage', 'response_time']:
                self.anomaly_detectors[metric_name] = IsolationForest(
                    contamination=0.1,
                    random_state=42
                )
        except Exception as e:
            self.logger.error(f"Failed to init anomaly detectors: {e}")
    
    async def start(self):
        """Start monitoring agent"""
        try:
            # Start Prometheus metrics server
            if HAS_ML:
                try:
                    start_http_server(9095)
                    self.logger.info("Prometheus server started on port 9095")
                except Exception as e:
                    self.logger.warning(f"Prometheus server failed: {e}")
            
            # Load alert rules from database
            await self._load_alert_rules_from_db()
            
            # Setup subscriptions
            await self._setup_subscriptions()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.logger.info(
                "Real-Time Monitoring Agent started",
                rules=len(self.alert_rules)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring agent: {e}")
            return False
    
    async def _setup_subscriptions(self):
        """Setup NATS subscriptions"""
        subscriptions = [
            ("monitoring.metrics.ingest", self._handle_metrics_ingestion),
            ("monitoring.alerts.manage", self._handle_alert_management),
            ("monitoring.health.check", self._handle_health_check_request),
            ("monitoring.sla.track", self._handle_sla_tracking),
            ("agent.presence.update", self._handle_presence_update)
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
            ("system_metrics_collector", self._collect_system_metrics()),
            ("alert_processor", self._process_alert_rules()),
            ("health_check_loop", self._health_check_loop()),
            ("sla_monitor", self._sla_monitoring_loop()),
            ("metrics_cleanup", self._metrics_cleanup()),
            ("anomaly_detector", self._anomaly_detection_loop()),
            ("baseline_calculator", self._baseline_calculator()),
            ("alert_escalator", self._alert_escalation_loop())
        ]
        
        for name, coro in tasks:
            task = asyncio.create_task(coro)
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
            self.logger.debug(f"Started background task: {name}")
    
    def _setup_default_alert_rules(self):
        """Setup comprehensive default alert rules"""
        default_rules = [
            AlertRule(
                id="cpu_critical",
                name="Critical CPU Usage",
                query="system_cpu_percent",
                condition=">",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration=120,
                consecutive_violations=2,
                annotations={
                    "description": "CPU usage above 95%",
                    "runbook": "/runbooks/high-cpu"
                }
            ),
            AlertRule(
                id="cpu_warning",
                name="High CPU Usage",
                query="system_cpu_percent",
                condition=">",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                duration=300,
                consecutive_violations=3
            ),
            AlertRule(
                id="memory_critical",
                name="Critical Memory Usage",
                query="system_memory_percent",
                condition=">",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration=120,
                consecutive_violations=2
            ),
            AlertRule(
                id="memory_warning",
                name="High Memory Usage",
                query="system_memory_percent",
                condition=">",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                duration=180,
                consecutive_violations=3
            ),
            AlertRule(
                id="disk_critical",
                name="Critical Disk Space",
                query="system_disk_usage_percent",
                condition=">",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration=60,
                consecutive_violations=2
            ),
            AlertRule(
                id="response_time_high",
                name="High Response Time",
                query="response_time_ms",
                condition=">",
                threshold=2000.0,
                severity=AlertSeverity.WARNING,
                duration=300,
                consecutive_violations=3
            ),
            AlertRule(
                id="error_rate_high",
                name="High Error Rate",
                query="error_rate_percent",
                condition=">",
                threshold=5.0,
                severity=AlertSeverity.ERROR,
                duration=120,
                consecutive_violations=2
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.id] = rule
    
    def _setup_system_collectors(self):
        """Setup system metric collectors"""
        self.system_collectors = {
            "cpu": self._collect_cpu_metrics,
            "memory": self._collect_memory_metrics,
            "disk": self._collect_disk_metrics,
            "network": self._collect_network_metrics,
            "process": self._collect_process_metrics
        }
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute monitoring tasks"""
        task_type = request.task_type
        payload = request.payload
        
        handlers = {
            "ingest_metrics": self._ingest_metrics,
            "query_metrics": self._query_metrics,
            "create_alert_rule": self._create_alert_rule,
            "manage_alert": self._manage_alert,
            "perform_health_check": self._perform_health_check,
            "setup_sla": self._setup_sla,
            "get_monitoring_status": self._get_monitoring_status
        }
        
        handler = handlers.get(task_type)
        if not handler:
            return {
                "status": "error",
                "error": f"Unknown task type: {task_type}"
            }
        
        try:
            result = await handler(payload)
            return {"status": "success", **result}
        except Exception as e:
            self.logger.error(f"Task failed: {task_type}", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _collect_system_metrics(self):
        """Continuously collect system metrics"""
        self.logger.info("Starting system metrics collection")
        
        while self.state == AgentStatus.RUNNING and not self.shutdown_event.is_set():
            try:
                # Collect from all collectors
                for collector_name, collector_func in self.system_collectors.items():
                    try:
                        metrics = await collector_func()
                        
                        for metric in metrics:
                            self._store_metric(metric)
                            self.monitoring_stats["metrics_collected"] += 1
                            
                            # Update Prometheus
                            if HAS_ML:
                                self.prom_metrics_collected.inc()
                                
                                if metric.name == "system_cpu_percent":
                                    self.prom_system_cpu.set(metric.value)
                                elif metric.name == "system_memory_percent":
                                    self.prom_system_memory.set(metric.value)
                        
                    except Exception as e:
                        self.logger.error(
                            f"Collector {collector_name} failed: {e}"
                        )
                
                # Publish metrics update
                await self._publish_metrics_update()
                
                # Persist to database periodically
                if self.monitoring_stats["metrics_collected"] % 100 == 0:
                    await self._persist_metrics_batch()
                
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(10)
        
        self.logger.info("System metrics collection stopped")
    
    async def _collect_cpu_metrics(self) -> List[Metric]:
        """Collect CPU metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count()
        
        try:
            load_avg = psutil.getloadavg()
        except:
            load_avg = (0, 0, 0)
        
        return [
            Metric(
                name="system_cpu_percent",
                type=MetricType.GAUGE,
                value=cpu_percent,
                unit="percent",
                labels={"collector": "system"}
            ),
            Metric(
                name="system_cpu_count",
                type=MetricType.GAUGE,
                value=cpu_count,
                labels={"collector": "system"}
            ),
            Metric(
                name="system_load_avg_1m",
                type=MetricType.GAUGE,
                value=load_avg[0],
                labels={"collector": "system"}
            )
        ]
    
    async def _collect_memory_metrics(self) -> List[Metric]:
        """Collect memory metrics"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return [
            Metric(
                name="system_memory_total",
                type=MetricType.GAUGE,
                value=memory.total,
                unit="bytes",
                labels={"collector": "system"}
            ),
            Metric(
                name="system_memory_used",
                type=MetricType.GAUGE,
                value=memory.used,
                unit="bytes",
                labels={"collector": "system"}
            ),
            Metric(
                name="system_memory_percent",
                type=MetricType.GAUGE,
                value=memory.percent,
                unit="percent",
                labels={"collector": "system"}
            ),
            Metric(
                name="system_swap_percent",
                type=MetricType.GAUGE,
                value=swap.percent,
                unit="percent",
                labels={"collector": "system"}
            )
        ]
    
    async def _collect_disk_metrics(self) -> List[Metric]:
        """Collect disk metrics"""
        metrics = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                labels = {
                    "collector": "system",
                    "device": partition.device,
                    "mountpoint": partition.mountpoint
                }
                
                metrics.append(Metric(
                    name="system_disk_usage_percent",
                    type=MetricType.GAUGE,
                    value=usage.percent,
                    unit="percent",
                    labels=labels
                ))
            except (PermissionError, OSError):
                continue
        
        return metrics
    
    async def _collect_network_metrics(self) -> List[Metric]:
        """Collect network metrics"""
        try:
            net_io = psutil.net_io_counters()
            return [
                Metric(
                    name="system_network_bytes_sent",
                    type=MetricType.COUNTER,
                    value=net_io.bytes_sent,
                    unit="bytes",
                    labels={"collector": "system"}
                ),
                Metric(
                    name="system_network_bytes_recv",
                    type=MetricType.COUNTER,
                    value=net_io.bytes_recv,
                    unit="bytes",
                    labels={"collector": "system"}
                )
            ]
        except:
            return []
    
    async def _collect_process_metrics(self) -> List[Metric]:
        """Collect process-level metrics"""
        # Collect only for current process to avoid overhead
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_percent = process.memory_percent()
            
            return [
                Metric(
                    name="agent_process_cpu_percent",
                    type=MetricType.GAUGE,
                    value=cpu_percent,
                    unit="percent",
                    labels={"agent": self.config.name}
                ),
                Metric(
                    name="agent_process_memory_percent",
                    type=MetricType.GAUGE,
                    value=memory_percent,
                    unit="percent",
                    labels={"agent": self.config.name}
                )
            ]
        except:
            return []
    
    def _store_metric(self, metric: Metric):
        """Store metric in time-series buffer"""
        label_str = ",".join(sorted([f"{k}={v}" for k, v in metric.labels.items()]))
        metric_key = f"{metric.name}{{{label_str}}}"
        
        self.metrics_buffer[metric_key].append({
            "timestamp": metric.timestamp,
            "value": metric.value,
            "type": metric.type.value,
            "unit": metric.unit
        })
        
        # Update metric definition
        self.metric_definitions[metric.name] = {
            "type": metric.type.value,
            "unit": metric.unit,
            "labels": list(metric.labels.keys())
        }
    
    async def _process_alert_rules(self):
        """Process alert rules and generate alerts"""
        self.logger.info("Starting alert processor")
        
        while self.state == AgentStatus.RUNNING and not self.shutdown_event.is_set():
            try:
                for rule_id, rule in list(self.alert_rules.items()):
                    if not rule.enabled:
                        continue
                    
                    try:
                        should_alert = await self._evaluate_alert_rule(rule)
                        
                        if should_alert:
                            rule.current_violations += 1
                            
                            if rule.current_violations >= rule.consecutive_violations:
                                if rule.can_trigger():
                                    await self._create_alert(rule)
                                    rule.last_triggered = time.time()
                                    rule.current_violations = 0
                        else:
                            # Reset violations if condition no longer met
                            if rule.current_violations > 0:
                                rule.current_violations = 0
                            
                            # Resolve existing alert
                            if rule_id in self.active_alerts:
                                await self._resolve_alert(rule_id)
                    
                    except Exception as e:
                        self.logger.error(f"Rule {rule_id} eval failed: {e}")
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Alert processor error: {e}")
                await asyncio.sleep(60)
        
        self.logger.info("Alert processor stopped")
    
    async def _evaluate_alert_rule(self, rule: AlertRule) -> bool:
        """Evaluate if alert rule should trigger"""
        try:
            metric_data = await self._query_metrics_internal(
                rule.query,
                duration=rule.duration
            )
            
            if not metric_data:
                return False
            
            latest_value = metric_data[-1]["value"]
            
            conditions = {
                ">": lambda v, t: v > t,
                "<": lambda v, t: v < t,
                ">=": lambda v, t: v >= t,
                "<=": lambda v, t: v <= t,
                "==": lambda v, t: v == t,
                "!=": lambda v, t: v != t
            }
            
            condition_func = conditions.get(rule.condition)
            if condition_func:
                return condition_func(latest_value, rule.threshold)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Rule evaluation failed: {e}")
            return False
    
    async def _create_alert(self, rule: AlertRule):
        """Create and publish alert"""
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        
        alert = Alert(
            id=alert_id,
            rule_id=rule.id,
            severity=rule.severity,
            message=f"{rule.name}: threshold {rule.threshold} exceeded",
            labels=rule.labels,
            annotations=rule.annotations
        )
        
        self.active_alerts[rule.id] = alert
        self.alert_history.append(alert)
        self.monitoring_stats["alerts_generated"] += 1
        
        # Update Prometheus
        if HAS_ML:
            self.prom_alerts_generated.labels(
                severity=alert.severity.value
            ).inc()
        
        # Persist alert
        await self._persist_alert(alert)
        
        # Publish alert
        await self._publish("monitoring.alerts.triggered", alert.to_dict())
        
        # Trigger auto-remediation if configured
        await self._trigger_remediation(alert)
        
        self.logger.warning(
            "Alert created",
            alert_id=alert_id,
            severity=alert.severity.value,
            rule=rule.name
        )
    
    async def _resolve_alert(self, rule_id: str):
        """Resolve active alert"""
        if rule_id in self.active_alerts:
            alert = self.active_alerts[rule_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = time.time()
            alert.updated_at = time.time()
            
            self.monitoring_stats["alerts_resolved"] += 1
            
            # Publish resolution
            await self._publish(
                "monitoring.alerts.resolved",
                alert.to_dict()
            )
            
            # Update in database
            await self._update_alert_status(alert)
            
            del self.active_alerts[rule_id]
            
            self.logger.info(f"Alert resolved: {alert.id}")
    
    async def _query_metrics_internal(
        self,
        query: str,
        duration: int
    ) -> List[Dict]:
        """Internal metrics query"""
        results = []
        current_time = time.time()
        cutoff_time = current_time - duration
        
        for metric_key, buffer in self.metrics_buffer.items():
            if query in metric_key:
                for entry in buffer:
                    if entry["timestamp"] >= cutoff_time:
                        results.append(entry)
        
        return sorted(results, key=lambda x: x["timestamp"])
    
    async def _anomaly_detection_loop(self):
        """ML-based anomaly detection"""
        if not HAS_ML:
            return
        
        self.logger.info("Starting anomaly detection")
        
        while self.state == AgentStatus.RUNNING and not self.shutdown_event.is_set():
            try:
                for metric_name, detector in self.anomaly_detectors.items():
                    metric_data = await self._query_metrics_internal(
                        metric_name,
                        duration=300
                    )
                    
                    if len(metric_data) < 10:
                        continue
                    
                    values = np.array([m["value"] for m in metric_data]).reshape(-1, 1)
                    
                    # Train detector if not trained
                    if not hasattr(detector, 'offset_'):
                        detector.fit(values)
                        continue
                    
                    # Detect anomalies
                    predictions = detector.predict(values[-1:])
                    
                    if predictions[0] == -1:  # Anomaly detected
                        self.monitoring_stats["anomalies_detected"] += 1
                        
                        await self._handle_anomaly(
                            metric_name,
                            metric_data[-1]["value"]
                        )
                
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Anomaly detection error: {e}")
                await asyncio.sleep(60)
    
    async def _handle_anomaly(self, metric_name: str, value: float):
        """Handle detected anomaly"""
        self.logger.warning(
            "Anomaly detected",
            metric=metric_name,
            value=value
        )
        
        # Publish anomaly event
        await self._publish("monitoring.anomaly.detected", {
            "metric_name": metric_name,
            "value": value,
            "timestamp": time.time()
        })
    
    async def stop(self):
        """Graceful shutdown"""
        self.logger.info("Stopping monitoring agent")
        
        self.shutdown_event.set()
        
        # Final metrics persist
        await self._persist_metrics_batch()
        
        await super().stop()
        
        self.logger.info("Monitoring agent stopped")


if __name__ == "__main__":
    import os
    
    async def main():
        config = AgentConfig(
            name="monitoring-agent",
            agent_type="monitoring",
            capabilities=[
                "metrics_collection",
                "alerting",
                "health_checks",
                "sla_monitoring",
                "anomaly_detection"
            ],
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL")
        )
        
        agent = RealTimeMonitoringAgent(config)
        
        if await agent.start():
            await agent.shutdown_event.wait()
            await agent.stop()
        else:
            sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested...")
