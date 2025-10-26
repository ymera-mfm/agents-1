"""
Real-time Monitoring Agent
Advanced system monitoring, alerting, and observability
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict, deque
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

# Optional dependencies - OpenTelemetry
try:
    from opentelemetry import trace, metrics
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    metrics = None
    HAS_OPENTELEMETRY = False

import logging
import statistics
from datetime import datetime, timedelta

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

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority

try:
    from opentelemetry import trace
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    HAS_OPENTELEMETRY = False

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

@dataclass
class Metric:
    name: str
    type: MetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None

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

@dataclass
class AlertRule:
    id: str
    name: str
    query: str
    condition: str
    threshold: float
    severity: AlertSeverity
    duration: int = 60  # seconds
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)

class RealTimeMonitoringAgent(BaseAgent):
    """
    Real-time Monitoring Agent providing:
    - System metrics collection (CPU, memory, disk, network)
    - Application metrics monitoring
    - Custom metrics ingestion and storage
    - Real-time alerting and notification
    - Performance dashboards and visualizations
    - Log aggregation and analysis
    - Health check orchestration
    - SLA monitoring and reporting
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Metrics storage
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.metric_definitions: Dict[str, Dict] = {}
        
        # Alerting system
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # System monitoring
        self.system_collectors = {}
        self.collection_interval = 10  # seconds
        
        # Performance tracking
        self.performance_baselines = {}
        self.anomaly_detectors = {}
        
        # Health checks
        self.health_checks: Dict[str, Dict] = {}
        self.service_status: Dict[str, Dict] = {}
        
        # SLA tracking
        self.sla_definitions: Dict[str, Dict] = {}
        self.sla_metrics: Dict[str, Dict] = {}
        
        # Initialize default alert rules
        self._setup_default_alert_rules()
        
        # Initialize system collectors
        self._setup_system_collectors()
    
    async def start(self):
        """Start monitoring agent services"""
        
        # Core monitoring endpoints
        await self._subscribe(
            f"agent.{self.config.name}.task",
            self._handle_monitoring_task,
            queue_group=f"{self.config.name}_workers"
        )
        
        # Metrics ingestion
        await self._subscribe(
            "monitoring.metrics.ingest",
            self._handle_metrics_ingestion
        )
        
        # Alert management
        await self._subscribe(
            "monitoring.alerts.manage",
            self._handle_alert_management
        )
        
        # Health check requests
        await self._subscribe(
            "monitoring.health.check",
            self._handle_health_check
        )
        
        # SLA monitoring
        await self._subscribe(
            "monitoring.sla.track",
            self._handle_sla_tracking
        )
        
        # Background tasks
        asyncio.create_task(self._collect_system_metrics())
        asyncio.create_task(self._process_alert_rules())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._sla_monitoring_loop())
        asyncio.create_task(self._metrics_cleanup())
        asyncio.create_task(self._publish_dashboards())
        
        self.logger.info("Real-time Monitoring Agent started")
    
    def _setup_default_alert_rules(self):
        """Setup default system alert rules"""
        
        default_rules = [
            AlertRule(
                id="high_cpu_usage",
                name="High CPU Usage",
                query="system_cpu_percent",
                condition=">",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                duration=300,
                annotations={
                    "description": "CPU usage is above 80% for more than 5 minutes",
                    "runbook_url": "/runbooks/high-cpu"
                }
            ),
            AlertRule(
                id="high_memory_usage",
                name="High Memory Usage",
                query="system_memory_percent",
                condition=">",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                duration=180,
                annotations={
                    "description": "Memory usage is above 85% for more than 3 minutes"
                }
            ),
            AlertRule(
                id="disk_space_low",
                name="Low Disk Space",
                query="system_disk_usage_percent",
                condition=">",
                threshold=90.0,
                severity=AlertSeverity.CRITICAL,
                duration=60,
                annotations={
                    "description": "Disk usage is above 90%"
                }
            ),
            AlertRule(
                id="agent_down",
                name="Agent Down",
                query="agent_health_status",
                condition="==",
                threshold=0.0,
                severity=AlertSeverity.CRITICAL,
                duration=30,
                annotations={
                    "description": "Agent is not responding to health checks"
                }
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
        """Execute monitoring-specific tasks"""
        task_type = request.task_type
        payload = request.payload
        
        if task_type == "ingest_metrics":
            return await self._ingest_metrics(payload)
        
        elif task_type == "query_metrics":
            return await self._query_metrics(payload)
        
        elif task_type == "create_alert_rule":
            return await self._create_alert_rule(payload)
        
        elif task_type == "manage_alert":
            return await self._manage_alert(payload)
        
        elif task_type == "health_check":
            return await self._perform_health_check(payload)
        
        elif task_type == "get_dashboard_data":
            return await self._get_dashboard_data(payload)
        
        elif task_type == "analyze_performance":
            return await self._analyze_performance(payload)
        
        elif task_type == "setup_sla":
            return await self._setup_sla(payload)
        
        else:
            raise ValueError(f"Unknown monitoring task type: {task_type}")
    
    async def _collect_system_metrics(self):
        """Collect system metrics continuously"""
        
        while not self._shutdown_event.is_set():
            try:
                # Collect metrics from all collectors
                for collector_name, collector_func in self.system_collectors.items():
                    try:
                        metrics = await collector_func()
                        
                        # Store metrics
                        for metric in metrics:
                            self._store_metric(metric)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to collect {collector_name} metrics: {e}")
                
                # Publish collected metrics
                await self._publish_metrics_update()
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"System metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_cpu_metrics(self) -> List[Metric]:
        """Collect CPU metrics"""
        
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
        
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
                unit="count",
                labels={"collector": "system"}
            ),
            Metric(
                name="system_load_avg_1m",
                type=MetricType.GAUGE,
                value=load_avg[0],
                labels={"collector": "system"}
            ),
            Metric(
                name="system_load_avg_5m",
                type=MetricType.GAUGE,
                value=load_avg[1],
                labels={"collector": "system"}
            ),
            Metric(
                name="system_load_avg_15m",
                type=MetricType.GAUGE,
                value=load_avg[2],
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
                name="system_memory_available",
                type=MetricType.GAUGE,
                value=memory.available,
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
                name="system_swap_total",
                type=MetricType.GAUGE,
                value=swap.total,
                unit="bytes",
                labels={"collector": "system"}
            ),
            Metric(
                name="system_swap_used",
                type=MetricType.GAUGE,
                value=swap.used,
                unit="bytes",
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
        
        # Disk usage for all mount points
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                labels = {
                    "collector": "system",
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype
                }
                
                metrics.extend([
                    Metric(
                        name="system_disk_total",
                        type=MetricType.GAUGE,
                        value=usage.total,
                        unit="bytes",
                        labels=labels
                    ),
                    Metric(
                        name="system_disk_used",
                        type=MetricType.GAUGE,
                        value=usage.used,
                        unit="bytes",
                        labels=labels
                    ),
                    Metric(
                        name="system_disk_free",
                        type=MetricType.GAUGE,
                        value=usage.free,
                        unit="bytes",
                        labels=labels
                    ),
                    Metric(
                        name="system_disk_usage_percent",
                        type=MetricType.GAUGE,
                        value=usage.used / usage.total * 100,
                        unit="percent",
                        labels=labels
                    )
                ])
                
            except PermissionError:
                continue
        
        # Disk I/O statistics
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.extend([
                    Metric(
                        name="system_disk_read_bytes",
                        type=MetricType.COUNTER,
                        value=disk_io.read_bytes,
                        unit="bytes",
                        labels={"collector": "system"}
                    ),
                    Metric(
                        name="system_disk_write_bytes",
                        type=MetricType.COUNTER,
                        value=disk_io.write_bytes,
                        unit="bytes",
                        labels={"collector": "system"}
                    ),
                    Metric(
                        name="system_disk_read_count",
                        type=MetricType.COUNTER,
                        value=disk_io.read_count,
                        labels={"collector": "system"}
                    ),
                    Metric(
                        name="system_disk_write_count",
                        type=MetricType.COUNTER,
                        value=disk_io.write_count,
                        labels={"collector": "system"}
                    )
                ])
        except Exception:
            pass
        
        return metrics
    
    async def _collect_network_metrics(self) -> List[Metric]:
        """Collect network metrics"""
        
        metrics = []
        
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                metrics.extend([
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
                    ),
                    Metric(
                        name="system_network_packets_sent",
                        type=MetricType.COUNTER,
                        value=net_io.packets_sent,
                        labels={"collector": "system"}
                    ),
                    Metric(
                        name="system_network_packets_recv",
                        type=MetricType.COUNTER,
                        value=net_io.packets_recv,
                        labels={"collector": "system"}
                    )
                ])
        except Exception:
            pass
            
        return metrics

    async def _collect_process_metrics(self) -> List[Metric]:
        """Collect process-level metrics"""
        
        metrics = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                
                labels = {
                    "collector": "system",
                    "process_name": proc_info['name'],
                    "pid": str(proc_info['pid']),
                    "username": proc_info['username']
                }
                
                metrics.extend([
                    Metric(
                        name="process_cpu_percent",
                        type=MetricType.GAUGE,
                        value=proc_info['cpu_percent'],
                        unit="percent",
                        labels=labels
                    ),
                    Metric(
                        name="process_memory_percent",
                        type=MetricType.GAUGE,
                        value=proc_info['memory_percent'],
                        unit="percent",
                        labels=labels
                    )
                ])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return metrics

    def _store_metric(self, metric: Metric):
        """Store metric in buffer"""
        
        # Create a unique key for the metric based on its name and labels
        label_str = ",".join(sorted([f"{k}={v}" for k, v in metric.labels.items()]))
        metric_key = f"{metric.name}{{{label_str}}}"
        
        # Store the metric value and timestamp
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
            "labels": list(set().union(*[
                set(labels.keys()) 
                for labels in [existing.get("labels", {}) for existing in self.metric_definitions.values()]
            ]) | set(metric.labels.keys()))
        }
    
    async def _process_alert_rules(self):
        """Process alert rules and generate alerts"""
        
        while not self._shutdown_event.is_set():
            try:
                for rule_id, rule in self.alert_rules.items():
                    if not rule.enabled:
                        continue
                    
                    try:
                        # Evaluate alert rule
                        should_alert = await self._evaluate_alert_rule(rule)
                        
                        existing_alert = self.active_alerts.get(rule_id)
                        
                        if should_alert and not existing_alert:
                            # Create new alert
                            alert = Alert(
                                id=f"alert_{rule_id}_{int(time.time())}",
                                rule_id=rule_id,
                                severity=rule.severity,
                                message=f"Alert: {rule.name}",
                                labels=rule.labels,
                                annotations=rule.annotations
                            )
                            
                            self.active_alerts[rule_id] = alert
                            self.alert_history.append(alert)
                            
                            # Send alert notification
                            await self._send_alert_notification(alert)
                            
                            self.logger.warning(f"Alert triggered: {rule.name}")
                        
                        elif not should_alert and existing_alert:
                            # Resolve existing alert
                            existing_alert.status = AlertStatus.RESOLVED
                            existing_alert.resolved_at = time.time()
                            existing_alert.updated_at = time.time()
                            
                            del self.active_alerts[rule_id]
                            
                            # Send resolution notification
                            await self._send_alert_resolution_notification(existing_alert)
                            
                            self.logger.info(f"Alert resolved: {rule.name}")
                    
                    except Exception as e:
                        self.logger.error(f"Failed to process alert rule {rule_id}: {e}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(60)
    
    async def _evaluate_alert_rule(self, rule: AlertRule) -> bool:
        """Evaluate if an alert rule should trigger"""
        
        try:
            # Get recent metrics for the rule query
            metric_data = await self._query_metrics_internal(rule.query, duration=rule.duration)
            
            if not metric_data:
                return False
            
            # Get the latest value
            latest_value = metric_data[-1]["value"]
            
            # Evaluate condition
            if rule.condition == ">":
                return latest_value > rule.threshold
            elif rule.condition == "<":
                return latest_value < rule.threshold
            elif rule.condition == ">=":
                return latest_value >= rule.threshold
            elif rule.condition == "<=":
                return latest_value <= rule.threshold
            elif rule.condition == "==":
                return latest_value == rule.threshold
            elif rule.condition == "!=":
                return latest_value != rule.threshold
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate alert rule {rule.id}: {e}")
            return False
    
    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification"""
        
        notification = {
            "alert_id": alert.id,
            "rule_id": alert.rule_id,
            "severity": alert.severity.value,
            "message": alert.message,
            "status": alert.status.value,
            "created_at": alert.created_at,
            "labels": alert.labels,
            "annotations": alert.annotations
        }
        
        # Publish to alert topic
        await self._publish("monitoring.alerts.triggered", notification)
        
        # Send to communication agent for distribution
        await self._publish("communication.send", {
            "sender": self.config.name,
            "recipients": ["orchestrator", "health"],
            "subject": f"alert.{alert.severity.value}",
            "payload": notification,
            "priority": 4 if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.ERROR] else 2
        })
    
    async def _send_alert_resolution_notification(self, alert: Alert):
        """Send alert resolution notification"""
        
        notification = {
            "alert_id": alert.id,
            "rule_id": alert.rule_id,
            "severity": alert.severity.value,
            "message": f"RESOLVED: {alert.message}",
            "status": alert.status.value,
            "resolved_at": alert.resolved_at,
            "duration": alert.resolved_at - alert.created_at
        }
        
        await self._publish("monitoring.alerts.resolved", notification)
    
    async def _health_check_loop(self):
        """Perform health checks on registered services"""
        
        while not self._shutdown_event.is_set():
            try:
                for service_name, check_config in self.health_checks.items():
                    try:
                        status = await self._perform_health_check_internal(service_name, check_config)
                        self.service_status[service_name] = status
                        
                        # Store health metric
                        health_metric = Metric(
                            name="service_health_status",
                            type=MetricType.GAUGE,
                            value=1.0 if status["healthy"] else 0.0,
                            labels={
                                "service": service_name,
                                "collector": "health_check"
                            }
                        )
                        self._store_metric(health_metric)
                        
                    except Exception as e:
                        self.logger.error(f"Health check failed for {service_name}: {e}")
                        
                        # Mark as unhealthy
                        self.service_status[service_name] = {
                            "healthy": False,
                            "error": str(e),
                            "last_check": time.time()
                        }
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)
    
    async def _sla_monitoring_loop(self):
        """Monitor SLA metrics"""
        
        while not self._shutdown_event.is_set():
            try:
                for sla_name, sla_config in self.sla_definitions.items():
                    try:
                        sla_status = await self._calculate_sla_status(sla_name, sla_config)
                        self.sla_metrics[sla_name] = sla_status
                        
                        # Store SLA metrics
                        for metric_name, value in sla_status.items():
                            if isinstance(value, (int, float)):
                                sla_metric = Metric(
                                    name=f"sla_{metric_name}",
                                    type=MetricType.GAUGE,
                                    value=value,
                                    labels={
                                        "sla": sla_name,
                                        "collector": "sla"
                                    }
                                )
                                self._store_metric(sla_metric)
                        
                    except Exception as e:
                        self.logger.error(f"SLA monitoring failed for {sla_name}: {e}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"SLA monitoring loop error: {e}")
                await asyncio.sleep(300)
    
    async def _metrics_cleanup(self):
        """Clean up old metrics to prevent memory issues"""
        
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                retention_period = 24 * 3600  # 24 hours
                
                for metric_key, metric_buffer in self.metrics_buffer.items():
                    # Remove old metrics
                    while (metric_buffer and 
                           current_time - metric_buffer[0]["timestamp"] > retention_period):
                        metric_buffer.popleft()
                
                # Clean up resolved alerts older than 7 days
                resolved_cutoff = current_time - (7 * 24 * 3600)
                self.alert_history = deque([
                    alert for alert in self.alert_history
                    if alert.status != AlertStatus.RESOLVED or alert.resolved_at > resolved_cutoff
                ], maxlen=10000)
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                self.logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _publish_dashboards(self):
        """Publish dashboard data"""
        
        while not self._shutdown_event.is_set():
            try:
                # Create dashboard data
                dashboard_data = {
                    "timestamp": time.time(),
                    "system_overview": await self._get_system_overview(),
                    "active_alerts": [
                        {
                            "id": alert.id,
                            "rule_id": alert.rule_id,
                            "severity": alert.severity.value,
                            "message": alert.message,
                            "created_at": alert.created_at,
                            "duration": time.time() - alert.created_at
                        }
                        for alert in self.active_alerts.values()
                    ],
                    "service_health": self.service_status,
                    "sla_status": self.sla_metrics
                }
                
                # Publish dashboard update
                await self._publish("monitoring.dashboard.update", dashboard_data)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Dashboard publishing error: {e}")
                await asyncio.sleep(60)
    
    async def _get_system_overview(self) -> Dict[str, Any]:
        """Get system overview metrics"""
        
        overview = {}
        
        try:
            # Get latest system metrics
            current_time = time.time()
            time_window = 300  # 5 minutes
            
            system_metrics = [
                "system_cpu_percent",
                "system_memory_percent",
                "system_disk_usage_percent",
                "system_load_avg_1m"
            ]
            
            for metric_name in system_metrics:
                metric_data = []
                
                for key, buffer in self.metrics_buffer.items():
                    if key.startswith(metric_name):
                        recent_data = [
                            entry for entry in buffer
                            if current_time - entry["timestamp"] <= time_window
                        ]
                        if recent_data:
                            metric_data.extend([entry["value"] for entry in recent_data])
                
                if metric_data:
                    overview[metric_name] = {
                        "current": metric_data[-1],
                        "average": statistics.mean(metric_data),
                        "max": max(metric_data),
                        "min": min(metric_data)
                    }
        
        except Exception as e:
            self.logger.error(f"Failed to get system overview: {e}")
        
        return overview
    async def _ingest_metrics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest metrics into the monitoring system and persist them in the database."""
        metrics_data = payload.get("metrics")
        if not metrics_data:
            raise ValueError("Metrics data is missing in payload")

        ingested_count = 0
        for metric_raw in metrics_data:
            try:
                metric = Metric(
                    name=metric_raw["name"],
                    type=MetricType[metric_raw["type"].upper()],
                    value=metric_raw["value"],
                    timestamp=metric_raw.get("timestamp", time.time()),
                    labels=metric_raw.get("labels", {}),
                    unit=metric_raw.get("unit")
                )
                self._store_metric(metric) # Store in buffer for real-time processing

                # Persist metric in database
                await self._db_query(
                    """INSERT INTO metrics (name, type, value, timestamp, labels, unit)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    metric.name, metric.type.value, metric.value, datetime.fromtimestamp(metric.timestamp),
                    json.dumps(metric.labels), metric.unit
                )
                ingested_count += 1
            except Exception as e:
                self.logger.error(f"Failed to ingest or persist metric: {e}", metric=metric_raw)

        return {"status": "success", "ingested_count": ingested_count}

    async def _query_metrics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Query metrics from the monitoring system, prioritizing database for historical data."""
        query_name = payload.get("query_name")
        duration = payload.get("duration", 3600)  # Default to 1 hour
        start_time = payload.get("start_time", time.time() - duration)
        end_time = payload.get("end_time", time.time())
        labels_filter = payload.get("labels_filter", {})

        if not query_name:
            raise ValueError("Query name is missing in payload")

        # First, try to get recent metrics from the in-memory buffer
        buffer_results = await self._query_metrics_from_buffer(query_name, start_time, end_time, labels_filter)

        # Then, query historical metrics from the database
        db_results = await self._query_metrics_from_db(query_name, start_time, end_time, labels_filter)

        # Combine and deduplicate results, prioritizing buffer for freshness
        combined_results = {m["timestamp"]: m for m in db_results}
        for m in buffer_results:
            combined_results[m["timestamp"]] = m

        sorted_results = sorted(combined_results.values(), key=lambda x: x["timestamp"])

        return {"status": "success", "metrics": sorted_results}

    async def _query_metrics_from_buffer(self, query_name: str, start_time: float, end_time: float, labels_filter: Dict[str, str]) -> List[Dict[str, Any]]:
        """Internal method to query metrics from the in-memory buffer."""
        results = []
        for metric_key, buffer in self.metrics_buffer.items():
            if query_name in metric_key:
                for m in buffer:
                    if start_time <= m["timestamp"] <= end_time:
                        # Basic label filtering (can be enhanced for complex queries)
                        metric_labels = dict(item.split("=") for item in metric_key.split("{")[1][:-1].split(",") if item) if "{" in metric_key else {}
                        if all(metric_labels.get(k) == v for k, v in labels_filter.items()):
                            results.append(m)
        return results

    async def _query_metrics_from_db(self, query_name: str, start_time: float, end_time: float, labels_filter: Dict[str, str]) -> List[Dict[str, Any]]:
        """Internal method to query metrics from the database."""
        if not self.db_pool:
            self.logger.warning("DB pool not initialized, cannot query historical metrics.")
            return []

        query = """SELECT name, type, value, EXTRACT(EPOCH FROM timestamp) as timestamp, labels, unit
                   FROM metrics
                   WHERE name = $1 AND timestamp BETWEEN $2 AND $3"""
        args = [query_name, datetime.fromtimestamp(start_time), datetime.fromtimestamp(end_time)]

        # Add label filters dynamically
        filter_clauses = []
        for k, v in labels_filter.items():
            filter_clauses.append(f"labels->>'{k}' = ${len(args) + 1}")
            args.append(v)
        if filter_clauses:
            query += " AND " + " AND ".join(filter_clauses)

        query += " ORDER BY timestamp ASC"

        records = await self._db_query(query, *args)
        if records:
            return [{
                "name": r["name"],
                "type": r["type"],
                "value": r["value"],
                "timestamp": r["timestamp"],
                "labels": json.loads(r["labels"]) if r["labels"] else {},
                "unit": r["unit"]
            } for r in records]
        return []

    async def _create_alert_rule(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert rule and persist it in the database."""
        rule_id = payload.get("id")
        if not rule_id:
            raise ValueError("Alert rule ID is missing")

        rule = AlertRule(
            id=rule_id,
            name=payload["name"],
            query=payload["query"],
            condition=payload["condition"],
            threshold=payload["threshold"],
            severity=AlertSeverity[payload["severity"].upper()],
            duration=payload.get("duration", 60),
            enabled=payload.get("enabled", True),
            labels=payload.get("labels", {}),
            annotations=payload.get("annotations", {})
        )

        self.alert_rules[rule_id] = rule

        # Persist alert rule in database
        await self._db_query(
            """INSERT INTO alert_rules (id, name, query, condition, threshold, severity, duration, enabled, labels, annotations)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
               ON CONFLICT (id) DO UPDATE SET
               name = EXCLUDED.name, query = EXCLUDED.query, condition = EXCLUDED.condition, threshold = EXCLUDED.threshold,
               severity = EXCLUDED.severity, duration = EXCLUDED.duration, enabled = EXCLUDED.enabled,
               labels = EXCLUDED.labels, annotations = EXCLUDED.annotations, updated_at = NOW()""",
            rule.id, rule.name, rule.query, rule.condition, rule.threshold, rule.severity.value, rule.duration,
            rule.enabled, json.dumps(rule.labels), json.dumps(rule.annotations)
        )

        return {"status": "success", "rule_id": rule_id}

    async def _manage_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Manage an existing alert (e.g., acknowledge, resolve, suppress) and persist changes."""
        alert_id = payload.get("alert_id")
        action = payload.get("action")

        if not alert_id or not action:
            raise ValueError("Alert ID or action is missing")

        alert = None
        # Check active alerts first
        for a in self.active_alerts.values():
            if a.id == alert_id:
                alert = a
                break
        # If not active, check history (though usually management is for active alerts)
        if not alert:
            for a in self.alert_history:
                if a.id == alert_id:
                    alert = a
                    break

        if not alert:
            raise ValueError(f"Alert with ID {alert_id} not found")

        old_status = alert.status
        if action == "acknowledge":
            alert.status = AlertStatus.ACKNOWLEDGED
        elif action == "resolve":
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = time.time()
        elif action == "suppress":
            alert.status = AlertStatus.SUPPRESSED
        else:
            raise ValueError(f"Unknown alert action: {action}")

        alert.updated_at = time.time()
        self.logger.info(f"Alert {alert_id} {action}d. New status: {alert.status.value}")

        # Update in active alerts if applicable
        if alert.status == AlertStatus.RESOLVED and alert.rule_id in self.active_alerts:
            del self.active_alerts[alert.rule_id]
        elif alert.status != AlertStatus.RESOLVED:
            # If it's an active alert being acknowledged or suppressed, keep it in active_alerts
            # If it was resolved and then re-opened (unlikely but possible), add it back
            self.active_alerts[alert.rule_id] = alert

        # Persist alert status change in database
        await self._db_query(
            """UPDATE alerts SET status = $1, updated_at = $2, resolved_at = $3 WHERE id = $4""",
            alert.status.value, datetime.fromtimestamp(alert.updated_at), 
            datetime.fromtimestamp(alert.resolved_at) if alert.resolved_at else None, alert.id
        )

        # Store updated alert in history (if not already there or if status changed significantly)
        # For simplicity, we'll just append, assuming history has a maxlen
        if old_status != alert.status:
            self.alert_history.append(alert)

        return {"status": "success", "alert_id": alert_id, "new_status": alert.status.value}

    async def _perform_health_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform an on-demand health check for a service and persist the result."""
        service_name = payload.get("service_name")
        if not service_name:
            raise ValueError("Service name is missing")

        check_config = self.health_checks.get(service_name)
        if not check_config:
            raise ValueError(f"No health check configuration found for service {service_name}")

        status = await self._perform_health_check_internal(service_name, check_config)
        self.service_status[service_name] = status

        # Store health metric
        health_metric = Metric(
            name="service_health_status",
            type=MetricType.GAUGE,
            value=1.0 if status["healthy"] else 0.0,
            labels={
                "service": service_name,
                "collector": "health_check"
            }
        )
        self._store_metric(health_metric)

        # Persist health check result in database
        await self._db_query(
            """INSERT INTO health_checks (service_name, healthy, error, last_check, check_type, target)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            service_name, status["healthy"], status["error"], datetime.fromtimestamp(status["last_check"]),
            check_config["type"], check_config["target"]
        )

        return {"status": "success", "service_name": service_name, "health_status": status}

    async def _perform_health_check_internal(self, service_name: str, check_config: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to perform a health check"""

        check_type = check_config["type"]
        target = check_config["target"]

        healthy = False
        error = None

        if check_type == "http":
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(target, timeout=check_config.get("timeout", 5)) as response:
                        if response.status == 200:
                            healthy = True
                        else:
                            error = f"HTTP status {response.status}"
            except aiohttp.ClientError as e:
                error = str(e)
            except asyncio.TimeoutError:
                error = "Timeout"
        elif check_type == "nats":
            # For NATS, we assume the agent's own NATS connection is a good indicator
            # or we could try to connect to a specific subject
            healthy = self.nc.is_connected if self.nc else False
            if not healthy:
                error = "NATS connection not active"
        elif check_type == "postgres":
            try:
                if self.db_pool:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute("SELECT 1")
                    healthy = True
                else:
                    error = "PostgreSQL pool not initialized"
            except Exception as e:
                error = str(e)
        elif check_type == "redis":
            try:
                if self.redis:
                    await self.redis.ping()
                    healthy = True
                else:
                    error = "Redis client not initialized"
            except Exception as e:
                error = str(e)
        else:
            error = f"Unknown health check type: {check_type}"

        return {"healthy": healthy, "error": error, "last_check": time.time()}

    async def _setup_sla(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Setup a new SLA definition and persist it in the database."""
        sla_name = payload.get("name")
        if not sla_name:
            raise ValueError("SLA name is missing")

        self.sla_definitions[sla_name] = payload

        # Persist SLA definition in database
        await self._db_query(
            """INSERT INTO sla_definitions (name, definition)
               VALUES ($1, $2)
               ON CONFLICT (name) DO UPDATE SET
               definition = EXCLUDED.definition, updated_at = NOW()""",
            sla_name, json.dumps(payload)
        )

        return {"status": "success", "sla_name": sla_name}

    async def _calculate_sla_status(self, sla_name: str, sla_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate SLA status based on defined metrics and thresholds, using historical data from DB."""

        service_name = sla_config.get("service_name")
        uptime_target = sla_config.get("uptime_target", 99.9)  # percentage
        period_seconds = sla_config.get("period", 24 * 3600)  # Default to 24 hours

        if not service_name:
            return {"error": "service_name not defined for SLA"}

        # Get health check history for the service from the database
        health_records = await self._db_query(
            """SELECT healthy, last_check FROM health_checks
               WHERE service_name = $1 AND last_check >= $2
               ORDER BY last_check ASC""",
            service_name, datetime.fromtimestamp(time.time() - period_seconds)
        )

        if not health_records:
            return {"status": "no_data", "uptime_percentage": 0.0, "meets_sla": False}

        total_checks = len(health_records)
        healthy_checks = sum(1 for r in health_records if r["healthy"])

        uptime_percentage = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0.0
        meets_sla = uptime_percentage >= uptime_target

        return {
            "uptime_percentage": uptime_percentage,
            "uptime_target": uptime_target,
            "meets_sla": meets_sla,
            "last_calculated": time.time()
        }

    async def _publish_metrics_update(self):
        """Publish collected metrics to the NATS stream for other agents and for frontend visualization."""

        metrics_to_publish = []
        for metric_key, buffer in self.metrics_buffer.items():
            if buffer:
                latest_metric = buffer[-1]
                # Reconstruct labels from metric_key if present
                labels = {}
                if "{" in metric_key and "}" in metric_key:
                    labels_str = metric_key.split("{")[1][:-1]
                    for item in labels_str.split(","):
                        if "=" in item:
                            k, v = item.split("=")
                            labels[k] = v

                metrics_to_publish.append({
                    "name": metric_key.split("{")[0],
                    "type": latest_metric["type"],
                    "value": latest_metric["value"],
                    "timestamp": latest_metric["timestamp"],
                    "labels": labels,
                    "unit": latest_metric["unit"]
                })

        if metrics_to_publish:
            await self._publish_to_stream("metrics.system.update", {"agent_id": self.id, "metrics": metrics_to_publish})

    async def _handle_monitoring_task(self, msg):
        """Handle incoming monitoring tasks"""
        await self._handle_task_request(msg)

    async def _handle_metrics_ingestion(self, msg):
        """Handle metrics ingestion from other agents/services"""
        payload = json.loads(msg.data.decode())
        # Acknowledge message immediately to prevent redelivery, as persistence is handled internally
        await msg.ack()
        try:
            await self._ingest_metrics(payload)
        except Exception as e:
            self.logger.error(f"Error processing metrics ingestion: {e}", payload=payload)

    async def _handle_alert_management(self, msg):
        """Handle alert management requests"""
        payload = json.loads(msg.data.decode())
        action = payload.get("action")

        try:
            if action == "create_rule":
                await self._create_alert_rule(payload["rule"])
            elif action == "update_rule":
                rule_id = payload["rule"]["id"]
                if rule_id in self.alert_rules:
                    # Update in-memory rule
                    self.alert_rules[rule_id] = AlertRule(**payload["rule"])
                    # Persist update in DB
                    await self._db_query(
                        """UPDATE alert_rules SET name = $1, query = $2, condition = $3, threshold = $4, severity = $5, duration = $6, enabled = $7, labels = $8, annotations = $9, updated_at = NOW() WHERE id = $10""",
                        self.alert_rules[rule_id].name, self.alert_rules[rule_id].query, self.alert_rules[rule_id].condition,
                        self.alert_rules[rule_id].threshold, self.alert_rules[rule_id].severity.value, self.alert_rules[rule_id].duration,
                        self.alert_rules[rule_id].enabled, json.dumps(self.alert_rules[rule_id].labels), json.dumps(self.alert_rules[rule_id].annotations), rule_id
                    )
                else:
                    self.logger.warning(f"Attempted to update non-existent rule: {rule_id}")
            elif action == "delete_rule":
                rule_id = payload["rule_id"]
                if rule_id in self.alert_rules:
                    del self.alert_rules[rule_id]
                    # Delete from DB
                    await self._db_query("DELETE FROM alert_rules WHERE id = $1", rule_id)
                else:
                    self.logger.warning(f"Attempted to delete non-existent rule: {rule_id}")
            elif action in ["acknowledge", "resolve", "suppress"]:
                await self._manage_alert(payload)
            else:
                self.logger.warning(f"Unknown alert management action: {action}")
        except Exception as e:
            self.logger.error(f"Error processing alert management request: {e}", payload=payload)
        finally:
            await msg.ack()

    async def _handle_health_check(self, msg):
        """Handle health check requests"""
        payload = json.loads(msg.data.decode())
        service_name = payload.get("service_name")

        try:
            if service_name:
                status = await self._perform_health_check(payload)
                await self._publish(msg.reply, json.dumps(status).encode())
            else:
                self.logger.warning("Health check request missing service_name")
                await self._publish(msg.reply, json.dumps({"error": "service_name missing"}).encode())
        except Exception as e:
            self.logger.error(f"Failed to perform health check for {service_name}: {e}")
            await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
        finally:
            await msg.ack()

    async def _handle_sla_tracking(self, msg):
        """Handle SLA tracking requests"""
        payload = json.loads(msg.data.decode())
        action = payload.get("action")

        try:
            if action == "setup":
                await self._setup_sla(payload["sla_definition"])
            elif action == "get_status":
                sla_name = payload.get("sla_name")
                if sla_name and sla_name in self.sla_definitions:
                    status = await self._calculate_sla_status(sla_name, self.sla_definitions[sla_name])
                    await self._publish(msg.reply, json.dumps(status).encode())
                else:
                    self.logger.warning(f"SLA definition not found for {sla_name}")
                    await self._publish(msg.reply, json.dumps({"error": f"SLA definition not found for {sla_name}"}).encode())
            else:
                self.logger.warning(f"Unknown SLA tracking action: {action}")
        except Exception as e:
            self.logger.error(f"Error processing SLA tracking request: {e}", payload=payload)
        finally:
            await msg.ack()


if __name__ == "__main__":
    async def main():
        config = AgentConfig(
            name="monitoring-agent",
            agent_type="monitoring",
            capabilities=["metrics_collection", "alerting", "health_checks", "sla_monitoring"]
        )
        agent = RealTimeMonitoringAgent(config)
        await agent.run()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Monitoring Agent stopped.")

