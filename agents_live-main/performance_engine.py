
"""
Upgraded Performance Engine Agent
Advanced performance monitoring, bottleneck detection, and optimization recommendation with predictive capabilities.
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import asyncpg
import statistics

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority
from opentelemetry import trace

class PerformanceMetricType(Enum):
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE_UTILIZATION = "resource_utilization"
    CONCURRENCY = "concurrency"
    SATURATION = "saturation"

class PerformanceIssueSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    name: str
    value: Union[int, float]
    metric_type: PerformanceMetricType
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceIssue:
    id: str
    name: str
    severity: PerformanceIssueSeverity
    description: str
    detected_at: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServicePerformanceSummary:
    service_name: str
    avg_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    throughput_rps: float = 0.0
    error_rate: float = 0.0
    cpu_utilization_percent: float = 0.0
    memory_utilization_percent: float = 0.0
    timestamp: float = field(default_factory=time.time)

class PerformanceEngineAgent(BaseAgent):
    """
    Upgraded Performance Engine Agent for proactive performance analysis and optimization.
    
    Key features include:
    - Real-time collection and analysis of performance metrics (latency, throughput, error rates, resource utilization).
    - Advanced algorithms for bottleneck detection and root cause analysis.
    - Predictive performance modeling to anticipate future issues.
    - Integration with the Optimizing Engine for automated performance adjustments.
    - Dynamic baselining and anomaly detection for performance deviations.
    - Comprehensive performance reporting and visualization capabilities.
    - Extensible architecture for custom performance tests and benchmarks.
    - Persistence of performance data and issues for historical analysis and auditing.
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.db_pool = None
        self.performance_metrics_history = defaultdict(lambda: deque(maxlen=10000)) # Stores raw metrics
        self.service_performance_summaries: Dict[str, ServicePerformanceSummary] = {}
        self.active_performance_issues: Dict[str, PerformanceIssue] = {}
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        self.anomaly_thresholds: Dict[str, float] = {
            "latency_std_dev": 3.0, # Standard deviations for latency anomaly
            "error_rate_threshold": 0.01, # 1% error rate
            "throughput_drop_percent": 0.2 # 20% drop from baseline
        }
        self.prediction_models = {}
        self.ml_model_metadata = {"predictor": {"last_trained": 0, "version": "1.0"}}

    async def start(self):
        """Start performance engine services"""
        if self.config.postgres_url:
            self.db_pool = await asyncpg.create_pool(self.config.postgres_url)
        
        await self._load_performance_baselines()
        await self._train_prediction_models()

        await self._subscribe(
            f"agent.{self.config.name}.task",
            self._handle_performance_task,
            queue_group=f"{self.config.name}_workers"
        )
        
        await self._subscribe(
            "performance.metrics.collect",
            self._handle_performance_metric_collection
        )
        
        await self._subscribe(
            "system.metrics.update", # From Monitoring Agent
            self._handle_system_metrics_update
        )
        
        await self._subscribe(
            "resource.utilization.update", # From Monitoring Agent
            self._handle_resource_utilization_update
        )

        # Start background performance analysis tasks
        asyncio.create_task(self._performance_aggregator_loop())
        asyncio.create_task(self._bottleneck_detector_loop())
        asyncio.create_task(self._predictive_analysis_loop())
        asyncio.create_task(self._performance_issue_manager_loop())
        asyncio.create_task(self._cleanup_old_data())
        
        self.logger.info("Performance Engine Agent started.")

    async def stop(self):
        """Stop performance engine services"""
        await super().stop()
        if self.db_pool:
            await self.db_pool.close()
        self.logger.info("Performance Engine Agent stopped.")

    async def _load_performance_baselines(self):
        """Load performance baselines from DB or compute defaults."""
        if not self.db_pool:
            self.logger.warning("No PostgreSQL connection, using default in-memory baselines.")
            self._set_default_baselines()
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                baselines_data = await conn.fetch("SELECT * FROM performance_baselines")
                for baseline_data in baselines_data:
                    self.performance_baselines[baseline_data["metric_name"]] = {
                        "mean": baseline_data["mean_value"],
                        "std_dev": baseline_data["std_dev_value"],
                        "p99": baseline_data["p99_value"],
                        "last_updated": baseline_data["last_updated"]
                    }
            self.logger.info("Loaded %d performance baselines from database.", len(self.performance_baselines))
        except Exception as e:
            self.logger.error(f"Failed to load performance baselines from DB: {e}")
            self._set_default_baselines()


    async def initialize(self):
            """Initialize performance engine"""
            await self.start()

    async def analyze_performance(self, target: dict) -> dict:
            """Analyze performance"""
            return await self.process(target)


    def _set_default_baselines(self):
        """Set some default baselines if none are loaded."""
        self.performance_baselines = {
            "service.latency.api_gateway": {"mean": 50.0, "std_dev": 10.0, "p99": 150.0, "last_updated": time.time()},
            "service.throughput.api_gateway": {"mean": 1000.0, "std_dev": 100.0, "p99": 1200.0, "last_updated": time.time()},
            "service.error_rate.api_gateway": {"mean": 0.001, "std_dev": 0.0005, "p99": 0.005, "last_updated": time.time()},
        }

    async def _train_prediction_models(self):
        """Train or load pre-trained ML models for performance prediction."""
        self.logger.info("Starting performance prediction model training/loading...")
        try:
            # Simulate a simple prediction model
            self.prediction_models["latency_predictor"] = {"model_type": "ARIMA", "trained": True}
            self.ml_model_metadata["predictor"]["last_trained"] = time.time()
            self.ml_model_metadata["predictor"]["version"] = "1.1"
            self.logger.info("Performance prediction models trained/loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to train/load performance prediction models: {e}")

    async def _handle_performance_task(self, msg):
        """Handle performance-specific tasks."""
        try:
            data = json.loads(msg.data.decode())
            task_type = data.get("task_type")
            payload = data.get("payload", {})

            if task_type == "get_performance_summary":
                return await self._get_performance_summary(payload)
            elif task_type == "get_performance_report":
                return await self._generate_performance_report(payload)
            elif task_type == "run_benchmark":
                return await self._run_benchmark(payload)
            elif task_type == "get_active_issues":
                return {"issues": [issue.__dict__ for issue in self.active_performance_issues.values() if not issue.resolved]}
            elif task_type == "get_historical_metrics":
                return await self._get_historical_metrics(payload)
            else:
                raise ValueError(f"Unknown performance task type: {task_type}")

        except Exception as e:
            self.logger.error(f"Failed to handle performance task: {e}")
            return {"status": "error", "message": str(e)}

    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute performance engine specific tasks."""
        return await self._handle_performance_task(self._create_mock_msg(request.__dict__))

    async def _handle_performance_metric_collection(self, msg):
        """Collect performance metrics from various sources."""
        try:
            data = json.loads(msg.data.decode())
            metric_name = data["name"]
            value = data["value"]
            metric_type = PerformanceMetricType[data["metric_type"].upper()]
            tags = data.get("tags", {})
            timestamp = data.get("timestamp", time.time())
            metadata = data.get("metadata", {})

            metric = PerformanceMetric(
                name=metric_name,
                value=value,
                metric_type=metric_type,
                tags=tags,
                timestamp=timestamp,
                metadata=metadata
            )
            metric_key = self._get_metric_key(metric)
            self.performance_metrics_history[metric_key].append(metric)
            
            # Store in DB for long-term analysis (async)
            asyncio.create_task(self._persist_performance_metric(metric))

            self.logger.debug(f"Collected performance metric: {metric_key}={value}")
        except Exception as e:
            self.logger.error(f"Failed to collect performance metric: {e}")

    async def _handle_system_metrics_update(self, msg):
        """Update internal system metrics from monitoring agent."""
        try:
            data = json.loads(msg.data.decode())
            metrics = data.get("metrics", {})
            # Extract relevant system metrics and store them as performance metrics
            if "cpu_percent" in metrics:
                await self._handle_performance_metric_collection(self._create_mock_msg({
                    "name": "system.cpu.percent",
                    "value": metrics["cpu_percent"],
                    "metric_type": "resource_utilization",
                    "tags": {"host": "system"}
                }))
            if "memory_percent" in metrics:
                await self._handle_performance_metric_collection(self._create_mock_msg({
                    "name": "system.memory.percent",
                    "value": metrics["memory_percent"],
                    "metric_type": "resource_utilization",
                    "tags": {"host": "system"}
                }))
            # Add other system metrics as needed
        except Exception as e:
            self.logger.error(f"Failed to process system metrics update: {e}")

    async def _handle_resource_utilization_update(self, msg):
        """Update internal resource utilization data from monitoring agent."""
        try:
            data = json.loads(msg.data.decode())
            resource_type = data["resource_type"]
            service_name = data["service_name"]
            value = data["value"]
            unit = data["unit"]
            timestamp = data.get("timestamp", time.time())

            # Convert to a generic performance metric
            await self._handle_performance_metric_collection(self._create_mock_msg({
                "name": f"service.{resource_type}.utilization",
                "value": value,
                "metric_type": "resource_utilization",
                "tags": {"service": service_name, "unit": unit},
                "timestamp": timestamp
            }))
        except Exception as e:
            self.logger.error(f"Failed to process resource utilization update: {e}")

    def _get_metric_key(self, metric: PerformanceMetric) -> str:
        """Generate a unique key for a metric based on its name and tags."""
        tags_str = ",".join(f"{k}={v}" for k, v in sorted(metric.tags.items()))
        return f"{metric.name}|{tags_str}"

    async def _persist_performance_metric(self, metric: PerformanceMetric):
        """Persist a performance metric to the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO performance_metrics (name, value, metric_type, tags, timestamp, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, metric.name, metric.value, metric.metric_type.value, json.dumps(metric.tags), metric.timestamp, json.dumps(metric.metadata))
            self.logger.debug(f"Metric {metric.name} persisted to DB.")
        except Exception as e:
            self.logger.error(f"Error persisting metric {metric.name} to DB: {e}")

    async def _performance_aggregator_loop(self):
        """Aggregates raw metrics into service performance summaries periodically."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60) # Aggregate every minute
                self.logger.debug("Running performance aggregation...")
                
                # Group metrics by service
                metrics_by_service = defaultdict(lambda: defaultdict(list))
                for metric_key, metrics_deque in self.performance_metrics_history.items():
                    # Only consider metrics from the last aggregation interval (e.g., 1 minute)
                    recent_metrics = [m for m in metrics_deque if m.timestamp > (time.time() - 60)]
                    if not recent_metrics: continue

                    service_name = metrics_deque[0].tags.get("service") or metrics_deque[0].tags.get("host")
                    if not service_name: continue

                    metrics_by_service[service_name][metrics_deque[0].metric_type].extend(recent_metrics)
                
                for service_name, service_metrics in metrics_by_service.items():
                    summary = ServicePerformanceSummary(service_name=service_name)
                    
                    # Latency
                    latency_values = [m.value for m in service_metrics[PerformanceMetricType.LATENCY]]
                    if latency_values:
                        summary.avg_latency_ms = statistics.mean(latency_values)
                        summary.p99_latency_ms = np.percentile(latency_values, 99)
                    
                    # Throughput
                    throughput_values = [m.value for m in service_metrics[PerformanceMetricType.THROUGHPUT]]
                    if throughput_values:
                        summary.throughput_rps = sum(throughput_values) # Assuming throughput is RPS
                    
                    # Error Rate
                    error_values = [m.value for m in service_metrics[PerformanceMetricType.ERROR_RATE]]
                    if error_values:
                        summary.error_rate = sum(error_values) / len(error_values) # Assuming 0 for success, 1 for error

                    # Resource Utilization (CPU, Memory)
                    cpu_values = [m.value for m in service_metrics[PerformanceMetricType.RESOURCE_UTILIZATION] if "cpu" in m.name]
                    if cpu_values: summary.cpu_utilization_percent = statistics.mean(cpu_values)
                    mem_values = [m.value for m in service_metrics[PerformanceMetricType.RESOURCE_UTILIZATION] if "memory" in m.name]
                    if mem_values: summary.memory_utilization_percent = statistics.mean(mem_values)

                    self.service_performance_summaries[service_name] = summary
                    asyncio.create_task(self._check_for_performance_issues(summary))
                    asyncio.create_task(self._persist_service_summary(summary))

            except Exception as e:
                self.logger.error(f"Performance aggregation failed: {e}")
                await asyncio.sleep(120)

    async def _persist_service_summary(self, summary: ServicePerformanceSummary):
        """Persist service performance summary to the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO service_performance_summaries (service_name, avg_latency_ms, p99_latency_ms, throughput_rps, error_rate, cpu_utilization_percent, memory_utilization_percent, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (service_name, timestamp) DO UPDATE SET
                        avg_latency_ms = EXCLUDED.avg_latency_ms,
                        p99_latency_ms = EXCLUDED.p99_latency_ms,
                        throughput_rps = EXCLUDED.throughput_rps,
                        error_rate = EXCLUDED.error_rate,
                        cpu_utilization_percent = EXCLUDED.cpu_utilization_percent,
                        memory_utilization_percent = EXCLUDED.memory_utilization_percent
                """, summary.service_name, summary.avg_latency_ms, summary.p99_latency_ms, summary.throughput_rps,
                    summary.error_rate, summary.cpu_utilization_percent, summary.memory_utilization_percent, summary.timestamp)
            self.logger.debug(f"Service performance summary for {summary.service_name} persisted to DB.")
        except Exception as e:
            self.logger.error(f"Error persisting service performance summary for {summary.service_name} to DB: {e}")

    async def _check_for_performance_issues(self, summary: ServicePerformanceSummary):
        """Check aggregated performance metrics against baselines and thresholds for issues."""
        issue_detected = False
        issue_description = []
        recommendations = []
        severity = PerformanceIssueSeverity.INFO

        # Latency check
        latency_baseline = self.performance_baselines.get(f"service.latency.{summary.service_name}")
        if latency_baseline and summary.avg_latency_ms > latency_baseline["mean"] + self.anomaly_thresholds["latency_std_dev"] * latency_baseline["std_dev"]:
            issue_detected = True
            issue_description.append(f"High average latency ({summary.avg_latency_ms:.2f}ms) exceeding baseline.")
            recommendations.append("Investigate service load and dependencies.")
            severity = max(severity, PerformanceIssueSeverity.WARNING)
        
        # Error rate check
        error_rate_baseline = self.performance_baselines.get(f"service.error_rate.{summary.service_name}")
        if error_rate_baseline and summary.error_rate > error_rate_baseline["mean"] + self.anomaly_thresholds["error_rate_threshold"]:
            issue_detected = True
            issue_description.append(f"Elevated error rate ({summary.error_rate:.2%}) exceeding baseline.")
            recommendations.append("Check service logs for errors and recent deployments.")
            severity = max(severity, PerformanceIssueSeverity.ERROR)

        # Throughput drop check
        throughput_baseline = self.performance_baselines.get(f"service.throughput.{summary.service_name}")
        if throughput_baseline and summary.throughput_rps < throughput_baseline["mean"] * (1 - self.anomaly_thresholds["throughput_drop_percent"]):
            issue_detected = True
            issue_description.append(f"Significant throughput drop ({summary.throughput_rps:.2f}rps) below baseline.")
            recommendations.append("Verify upstream dependencies and traffic patterns.")
            severity = max(severity, PerformanceIssueSeverity.WARNING)

        # Resource utilization check (simple thresholds for now)
        if summary.cpu_utilization_percent > 85:
            issue_detected = True
            issue_description.append(f"High CPU utilization ({summary.cpu_utilization_percent:.2f}%).")
            recommendations.append("Consider scaling up or optimizing CPU-intensive operations.")
            severity = max(severity, PerformanceIssueSeverity.WARNING)
        if summary.memory_utilization_percent > 90:
            issue_detected = True
            issue_description.append(f"High Memory utilization ({summary.memory_utilization_percent:.2f}%).")
            recommendations.append("Investigate memory leaks or increase memory allocation.")
            severity = max(severity, PerformanceIssueSeverity.ERROR)

        if issue_detected:
            issue_id = f"perf_issue_{summary.service_name}_{int(time.time())}"
            issue = PerformanceIssue(
                id=issue_id,
                name=f"Performance Issue for {summary.service_name}",
                severity=severity,
                description="; ".join(issue_description),
                metrics_snapshot=summary.__dict__,
                recommendations=recommendations
            )
            self.active_performance_issues[issue_id] = issue
            self.logger.warning(f"Detected performance issue for {summary.service_name}: {issue.description}")
            await self._publish("performance.issue.detected", issue.__dict__)
            asyncio.create_task(self._persist_performance_issue(issue))
            # Trigger optimization engine for automated action
            await self._trigger_optimization_engine(issue)
        else:
            # Attempt to resolve any existing issues for this service if conditions are now good
            for issue_id, issue in list(self.active_performance_issues.items()):
                if issue.metrics_snapshot.get("service_name") == summary.service_name and not issue.resolved:
                    self.logger.info(f"Performance issue {issue.id} for {summary.service_name} appears resolved.")
                    issue.resolved = True
                    issue.resolved_at = time.time()
                    await self._publish("performance.issue.resolved", issue.__dict__)
                    asyncio.create_task(self._persist_performance_issue(issue))

    async def _persist_performance_issue(self, issue: PerformanceIssue):
        """Persist a performance issue to the database."""
        if not self.db_pool: return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO performance_issues (id, name, severity, description, detected_at, resolved, resolved_at, metrics_snapshot, recommendations, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO UPDATE SET
                        resolved = EXCLUDED.resolved,
                        resolved_at = EXCLUDED.resolved_at,
                        metrics_snapshot = EXCLUDED.metrics_snapshot,
                        recommendations = EXCLUDED.recommendations,
                        metadata = EXCLUDED.metadata
                """, issue.id, issue.name, issue.severity.value, issue.description, issue.detected_at,
                    issue.resolved, issue.resolved_at, json.dumps(issue.metrics_snapshot), json.dumps(issue.recommendations), json.dumps(issue.metadata))
            self.logger.debug(f"Performance issue {issue.id} persisted to DB.")
        except Exception as e:
            self.logger.error(f"Error persisting performance issue {issue.id} to DB: {e}")

    async def _trigger_optimization_engine(self, issue: PerformanceIssue):
        """Send a request to the Optimizing Engine to address a performance issue."""
        self.logger.info(f"Requesting optimization for performance issue {issue.id}: {issue.description}")
        # Map performance issue to optimization task
        optimization_payload = {
            "task_type": "run_optimization_cycle",
            "payload": {
                "reason": f"Performance issue detected: {issue.name}",
                "issue_id": issue.id,
                "metrics_snapshot": issue.metrics_snapshot,
                "recommendations": issue.recommendations
            }
        }
        await self._publish("intelligence.optimize", optimization_payload)

    async def _bottleneck_detector_loop(self):
        """Periodically analyze performance data to identify bottlenecks."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(300) # Run every 5 minutes
                self.logger.debug("Running bottleneck detection...")
                
                # Example: Simple bottleneck detection - identify services with highest latency/error rate
                if not self.service_performance_summaries:
                    continue

                sorted_by_latency = sorted(self.service_performance_summaries.values(), key=lambda s: s.p99_latency_ms, reverse=True)
                sorted_by_error = sorted(self.service_performance_summaries.values(), key=lambda s: s.error_rate, reverse=True)

                if sorted_by_latency and sorted_by_latency[0].p99_latency_ms > 200: # Arbitrary threshold
                    self.logger.warning(f"Potential latency bottleneck: {sorted_by_latency[0].service_name} (P99 Latency: {sorted_by_latency[0].p99_latency_ms:.2f}ms)")
                    # Create a performance issue if not already active
                    issue_id = f"bottleneck_latency_{sorted_by_latency[0].service_name}"
                    if issue_id not in self.active_performance_issues or self.active_performance_issues[issue_id].resolved:
                        issue = PerformanceIssue(
                            id=issue_id,
                            name=f"Latency Bottleneck in {sorted_by_latency[0].service_name}",
                            severity=PerformanceIssueSeverity.ERROR,
                            description=f"Service {sorted_by_latency[0].service_name} shows high P99 latency. Investigate dependencies and resource contention.",
                            metrics_snapshot=sorted_by_latency[0].__dict__,
                            recommendations=["Analyze service dependencies", "Check resource utilization", "Profile application code"]
                        )
                        self.active_performance_issues[issue_id] = issue
                        await self._publish("performance.issue.detected", issue.__dict__)
                        asyncio.create_task(self._persist_performance_issue(issue))

                if sorted_by_error and sorted_by_error[0].error_rate > 0.05: # Arbitrary threshold
                    self.logger.warning(f"Potential error rate bottleneck: {sorted_by_error[0].service_name} (Error Rate: {sorted_by_error[0].error_rate:.2%})")
                    issue_id = f"bottleneck_error_{sorted_by_error[0].service_name}"
                    if issue_id not in self.active_performance_issues or self.active_performance_issues[issue_id].resolved:
                        issue = PerformanceIssue(
                            id=issue_id,
                            name=f"Error Rate Bottleneck in {sorted_by_error[0].service_name}",
                            severity=PerformanceIssueSeverity.CRITICAL,
                            description=f"Service {sorted_by_error[0].service_name} shows high error rate. Immediate investigation required.",
                            metrics_snapshot=sorted_by_error[0].__dict__,
                            recommendations=["Review recent deployments", "Check service logs for exceptions", "Verify external integrations"]
                        )
                        self.active_performance_issues[issue_id] = issue
                        await self._publish("performance.issue.detected", issue.__dict__)
                        asyncio.create_task(self._persist_performance_issue(issue))

            except Exception as e:
                self.logger.error(f"Bottleneck detection failed: {e}")
                await asyncio.sleep(600)

    async def _predictive_analysis_loop(self):
        """Periodically generate performance predictions."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(900) # Run every 15 minutes
                self.logger.debug("Running predictive performance analysis...")

                # Example: Predict future latency for a critical service
                critical_service = "api_gateway"
                latency_history = [m.value for m_key, m_deque in self.performance_metrics_history.items() 
                                   for m in m_deque if critical_service in m_key and "latency" in m_key]
                
                if len(latency_history) > 100 and self.prediction_models.get("latency_predictor", {}).get("trained"):
                    # Simulate prediction based on recent trend
                    predicted_latency = statistics.mean(latency_history[-50:]) * (1 + random.uniform(-0.05, 0.05))
                    self.logger.info(f"Predicted latency for {critical_service} in next hour: {predicted_latency:.2f}ms")
                    await self._publish("system.prediction.performance", {
                        "type": f"service.latency.{critical_service}",
                        "predicted_value": predicted_latency,
                        "horizon": 3600,
                        "service_name": critical_service
                    })
                    # If predicted latency is high, create a proactive issue
                    if predicted_latency > 200: # Proactive threshold
                        issue_id = f"predicted_latency_{critical_service}_{int(time.time())}"
                        if issue_id not in self.active_performance_issues or self.active_performance_issues[issue_id].resolved:
                            issue = PerformanceIssue(
                                id=issue_id,
                                name=f"Predicted High Latency for {critical_service}",
                                severity=PerformanceIssueSeverity.WARNING,
                                description=f"Predicted average latency of {predicted_latency:.2f}ms for {critical_service} in the next hour. Proactive action recommended.",
                                metrics_snapshot={"predicted_latency": predicted_latency},
                                recommendations=["Pre-scale service", "Review upcoming traffic changes"]
                            )
                            self.active_performance_issues[issue_id] = issue
                            await self._publish("performance.issue.detected", issue.__dict__)
                            asyncio.create_task(self._persist_performance_issue(issue))

            except Exception as e:
                self.logger.error(f"Predictive analysis failed: {e}")
                await asyncio.sleep(1800)

    async def _performance_issue_manager_loop(self):
        """Manages the lifecycle of performance issues, including escalation and resolution."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60) # Check issues every minute
                current_time = time.time()

                for issue_id, issue in list(self.active_performance_issues.items()):
                    if issue.resolved:
                        # Clean up resolved issues after a certain period (e.g., 24 hours)
                        if current_time - (issue.resolved_at or issue.detected_at) > 86400:
                            del self.active_performance_issues[issue_id]
                            self.logger.debug(f"Cleaned up resolved performance issue {issue_id}")
                        continue

                    # Example: Escalate critical issues if not resolved within 30 minutes
                    if issue.severity == PerformanceIssueSeverity.CRITICAL and (current_time - issue.detected_at > 1800):
                        if not issue.metadata.get("escalated"): # Only escalate once
                            self.logger.critical(f"ESCALATING PERFORMANCE ISSUE: {issue.name} ({issue.id})")
                            await self._publish("notification.escalate", {
                                "issue_id": issue.id,
                                "original_severity": issue.severity.value,
                                "escalated_at": time.time(),
                                "message": f"ESCALATED: {issue.description}"
                            })
                            issue.metadata["escalated"] = True
                            asyncio.create_task(self._persist_performance_issue(issue))

            except Exception as e:
                self.logger.error(f"Performance issue manager failed: {e}")
                await asyncio.sleep(120)

    async def _cleanup_old_data(self):
        """Clean up old performance metrics and issues to manage memory and DB space."""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                # Keep raw metrics in buffer for 24 hours
                metrics_cutoff_time = current_time - (24 * 3600)
                for metric_key, metrics_deque in list(self.performance_metrics_history.items()):
                    while metrics_deque and metrics_deque[0].timestamp < metrics_cutoff_time:
                        metrics_deque.popleft()
                    if not metrics_deque: # Remove empty deques
                        del self.performance_metrics_history[metric_key]
                
                # Clean up resolved issues older than 7 days
                resolved_issues_to_remove = [
                    issue_id for issue_id, issue in self.active_performance_issues.items()
                    if issue.resolved and (current_time - (issue.resolved_at or issue.detected_at)) > (7 * 24 * 3600)
                ]
                for issue_id in resolved_issues_to_remove:
                    del self.active_performance_issues[issue_id]
                
                self.logger.info("Performance data cleanup completed",
                                 metrics_series_count=len(self.performance_metrics_history),
                                 active_issues=len([i for i in self.active_performance_issues.values() if not i.resolved]),
                                 resolved_issues_cleaned=len(resolved_issues_to_remove))
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                self.logger.error("Performance data cleanup failed", error=str(e))
                await asyncio.sleep(3600)

    async def _get_performance_summary(self, payload: Dict) -> Dict[str, Any]:
        """Get current performance summaries for all services or a specific one."""
        service_name = payload.get("service_name")
        
        if service_name:
            summary = self.service_performance_summaries.get(service_name)
            if summary:
                return {"service_summary": summary.__dict__}
            else:
                return {"error": "Service not found or no performance data available"}
        else:
            return {
                "all_service_summaries": {
                    name: summary.__dict__
                    for name, summary in self.service_performance_summaries.items()
                },
                "timestamp": time.time()
            }

    async def _generate_performance_report(self, payload: Dict) -> Dict[str, Any]:
        """Generate a detailed performance report for a given period."""
        self.logger.info("Generating detailed performance report...")
        # This would query historical data from the database and compile a comprehensive report.
        # For now, it's a placeholder.
        start_time = payload.get("start_time", time.time() - 3600 * 24) # Last 24 hours
        end_time = payload.get("end_time", time.time())
        service_filter = payload.get("service_name")

        report_data = {
            "report_period": f"{time.ctime(start_time)} to {time.ctime(end_time)}",
            "overall_status": "Good",
            "summary_metrics": {},
            "top_issues": [],
            "service_details": {}
        }

        # Aggregate data from DB for the period
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                # Fetch summaries
                summaries = await conn.fetch("""
                    SELECT * FROM service_performance_summaries
                    WHERE timestamp BETWEEN $1 AND $2
                    AND ($3 IS NULL OR service_name = $3)
                    ORDER BY timestamp ASC
                """, start_time, end_time, service_filter)
                
                # Fetch issues
                issues = await conn.fetch("""
                    SELECT * FROM performance_issues
                    WHERE detected_at BETWEEN $1 AND $2
                    AND ($3 IS NULL OR metrics_snapshot->>'service_name' = $3)
                    ORDER BY detected_at DESC
                """, start_time, end_time, service_filter)
                
                report_data["service_details"] = defaultdict(list)
                for s in summaries:
                    report_data["service_details"][s["service_name"]].append(dict(s))
                
                report_data["top_issues"] = [dict(i) for i in issues]

        # Basic overall status based on issues
        if any(issue["severity"] == PerformanceIssueSeverity.CRITICAL.value for issue in report_data["top_issues"]):
            report_data["overall_status"] = "Critical"
        elif any(issue["severity"] == PerformanceIssueSeverity.ERROR.value for issue in report_data["top_issues"]):
            report_data["overall_status"] = "Degraded"

        return {"report_status": "generated", "data": report_data}

    async def _run_benchmark(self, payload: Dict) -> Dict[str, Any]:
        """Simulate running a performance benchmark."""
        self.logger.info(f"Running benchmark: {payload.get("benchmark_name", "unnamed")}")
        # In a real system, this would trigger an external benchmarking tool
        # and collect its results.
        await asyncio.sleep(5) # Simulate benchmark run time
        results = {
            "benchmark_name": payload.get("benchmark_name", "default_benchmark"),
            "duration_seconds": 5,
            "metrics": {
                "avg_latency_ms": random.uniform(50, 150),
                "throughput_rps": random.uniform(500, 2000),
                "error_rate": random.uniform(0.001, 0.01)
            },
            "status": "completed"
        }
        self.logger.info("Benchmark completed.")
        return results

    async def _get_historical_metrics(self, payload: Dict) -> Dict[str, Any]:
        """Retrieve historical raw metrics for a given metric name and time range."""
        metric_name = payload.get("metric_name")
        service_name = payload.get("service_name")
        start_time = payload.get("start_time", time.time() - 3600) # Last hour
        end_time = payload.get("end_time", time.time())

        if not metric_name:
            return {"error": "metric_name is required."}

        filtered_metrics = []
        for m_key, m_deque in self.performance_metrics_history.items():
            if metric_name in m_key and (not service_name or service_name in m_key):
                for metric in m_deque:
                    if start_time <= metric.timestamp <= end_time:
                        filtered_metrics.append(metric.__dict__)
        
        # Also query from DB for older data if needed
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                db_metrics = await conn.fetch("""
                    SELECT name, value, metric_type, tags, timestamp, metadata
                    FROM performance_metrics
                    WHERE name = $1 AND timestamp BETWEEN $2 AND $3
                    AND ($4 IS NULL OR tags->>'service' = $4 OR tags->>'host' = $4)
                    ORDER BY timestamp ASC
                """, metric_name, start_time, end_time, service_name)
                filtered_metrics.extend([dict(m) for m in db_metrics])

        return {"metric_name": metric_name, "metrics": filtered_metrics}

    def _create_mock_msg(self, payload: Dict) -> Any:
        """Helper to create a mock NATS message for internal calls."""
        class MockMsg:
            def __init__(self, data):
                self.data = json.dumps(data).encode("utf-8")
        return MockMsg(payload)


if __name__ == "__main__":
    import os
    import random
    
    config = AgentConfig(
        name="performance_engine",
        agent_type="performance",
        capabilities=[
            "performance_monitoring",
            "bottleneck_detection",
            "predictive_analysis",
            "optimization_recommendation",
            "benchmarking",
            "performance_reporting"
        ],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"), # Not directly used in this agent, but part of config
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500") # Not directly used in this agent, but part of config
    )
    
    agent = PerformanceEngineAgent(config)
    asyncio.run(agent.run())

