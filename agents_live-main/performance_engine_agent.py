"""
Advanced Performance Engine Agent
Real-time performance monitoring, optimization, bottleneck detection, and auto-scaling
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
import gc
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import statistics
from collections import deque, defaultdict
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import cProfile
import pstats
import tracemalloc
import sys
import resource
from datetime import datetime

# Optional dependencies
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False

# External monitoring libraries (ensure these are installed or mocked if not critical for core logic)
# import prometheus_client
# from prometheus_client import Counter, Histogram, Gauge, Summary
# import py_spy
# import memory_profiler
# import line_profiler
# import pympler.tracker
# import objgraph

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority

# Optional dependencies - OpenTelemetry
try:
    from opentelemetry.trace import Status, StatusCode
    HAS_OPENTELEMETRY = True
except ImportError:
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    Status = None
    StatusCode = None
    HAS_OPENTELEMETRY = False

class PerformanceMetric(Enum):
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

class OptimizationStrategy(Enum):
    CACHING = "caching"
    BATCHING = "batching"
    PARALLEL = "parallel"
    ASYNC = "async"
    COMPRESSION = "compression"
    INDEXING = "indexing"
    CONNECTION_POOLING = "connection_pooling"
    LAZY_LOADING = "lazy_loading"

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class PerformanceThreshold:
    metric: PerformanceMetric
    warning_value: float
    critical_value: float
    unit: str
    enabled: bool = True

@dataclass
class PerformanceAlert:
    id: str
    metric: PerformanceMetric
    severity: AlertSeverity
    current_value: float
    threshold_value: float
    message: str
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationRecommendation:
    id: str
    strategy: OptimizationStrategy
    title: str
    description: str
    estimated_improvement: str
    complexity: str  # LOW, MEDIUM, HIGH
    priority_score: float
    implementation_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceProfile:
    profile_id: str
    target: str  # function, module, or system
    duration_ms: float
    cpu_time_ms: float
    memory_peak_mb: float
    function_calls: int
    hotspots: List[Dict[str, Any]] = field(default_factory=list)
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

class PerformanceEngineAgent(BaseAgent):
    """
    Advanced Performance Engine with:
    - Real-time system monitoring (CPU, Memory, I/O, Network)
    - Application performance profiling (CPU, Memory, I/O)
    - Bottleneck detection and analysis
    - Auto-scaling recommendations
    - Performance optimization suggestions
    - ML-powered anomaly detection
    - Predictive performance modeling
    - Resource optimization
    - Load testing integration
    - Performance regression detection
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Performance monitoring
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.active_profiles = {}
        self.performance_baselines = {}
        
        # Alerting system
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        
        # Performance thresholds
        self.thresholds = {
            PerformanceMetric.CPU_USAGE: PerformanceThreshold(
                PerformanceMetric.CPU_USAGE, 70.0, 90.0, "%"
            ),
            PerformanceMetric.MEMORY_USAGE: PerformanceThreshold(
                PerformanceMetric.MEMORY_USAGE, 80.0, 95.0, "%"
            ),
            PerformanceMetric.RESPONSE_TIME: PerformanceThreshold(
                PerformanceMetric.RESPONSE_TIME, 500.0, 2000.0, "ms"
            ),
            PerformanceMetric.ERROR_RATE: PerformanceThreshold(
                PerformanceMetric.ERROR_RATE, 1.0, 5.0, "%"
            )
        }
        
        # Prometheus metrics (mocked if prometheus_client is not installed)
        self.prometheus_metrics = self._init_prometheus_metrics()
        
        # Optimization engine
        self.optimization_cache = {}
        self.recommendation_engine = self._init_recommendation_engine()
        
        # Profiling tools
        self.profilers = {
            "cpu": cProfile.Profile(),
            "memory": None,  # Will be initialized when needed
            "line": None     # Will be initialized when needed
        }
        
        # Statistics
        self.performance_stats = {
            "total_profiles": 0,
            "active_monitors": 0,
            "alerts_generated": 0,
            "optimizations_applied": 0,
            "average_response_time": 0.0
        }
        
        # Auto-scaling settings
        self.auto_scaling = {
            "enabled": False,
            "min_instances": 1,
            "max_instances": 10,
            "scale_up_threshold": 80.0,
            "scale_down_threshold": 30.0,
            "cooldown_period": 300  # 5 minutes
        }
        
        # Thread pool for monitoring
        self.monitor_executor = ThreadPoolExecutor(max_workers=4)
        
        # Memory tracking
        tracemalloc.start()
        # self.memory_tracker = pympler.tracker.SummaryTracker() # Commented out if pympler is not installed
    
    async def start(self):
        """Start performance engine services"""
        await self._subscribe(
            f"agent.{self.config.name}.task",
            self._handle_performance_task,
            queue_group=f"{self.config.name}_workers"
        )
        
        await self._subscribe(
            "performance.monitor.start",
            self._handle_monitor_start
        )
        
        await self._subscribe(
            "performance.profile.create",
            self._handle_profile_create
        )
        
        await self._subscribe(
            "performance.optimize.request",
            self._handle_optimize_request
        )
        
        await self._subscribe(
            "performance.threshold.update",
            self._handle_threshold_update
        )
        
        # Start background monitoring
        asyncio.create_task(self._system_monitor())
        asyncio.create_task(self._alert_processor())
        asyncio.create_task(self._optimization_engine())
        asyncio.create_task(self._performance_reporter())
        
        self.logger.info("Performance Engine Agent started")
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics (mocked if client not available)"""
        metrics = {
            "request_duration": type("MockHistogram", (object,), {"observe": lambda *args, **kwargs: None})(),
            "request_count": type("MockCounter", (object,), {"inc": lambda *args, **kwargs: None})(),
            "active_connections": type("MockGauge", (object,), {"set": lambda *args, **kwargs: None})(),
            "memory_usage": type("MockGauge", (object,), {"set": lambda *args, **kwargs: None})(),
            "cpu_usage": type("MockGauge", (object,), {"set": lambda *args, **kwargs: None})()
        }
        # try:
        #     from prometheus_client import Counter, Histogram, Gauge, Summary
        #     metrics["request_duration"] = Histogram(
        #         'request_duration_seconds',
        #         'Request duration in seconds',
        #         ['method', 'endpoint', 'status']
        #     )
        #     metrics["request_count"] = Counter(
        #         'requests_total',
        #         'Total number of requests',
        #         ['method', 'endpoint', 'status']
        #     )
        #     metrics["active_connections"] = Gauge(
        #         'active_connections',
        #         'Number of active connections'
        #     )
        #     metrics["memory_usage"] = Gauge(
        #         'memory_usage_bytes',
        #         'Memory usage in bytes'
        #     )
        #     metrics["cpu_usage"] = Gauge(
        #         'cpu_usage_percent',
        #         'CPU usage percentage'
        #     )
        # except ImportError:
        #     self.logger.warning("Prometheus client not found, using mock metrics.")
        return metrics
    
    def _init_recommendation_engine(self):
        """Initialize optimization recommendation engine"""
        return {
            "rules": {
                "high_cpu_usage": {
                    "condition": lambda metrics: metrics.get("cpu_usage", 0) > 80,
                    "recommendations": [
                        OptimizationStrategy.PARALLEL,
                        OptimizationStrategy.CACHING,
                        OptimizationStrategy.ASYNC
                    ]
                },
                "high_memory_usage": {
                    "condition": lambda metrics: metrics.get("memory_usage", 0) > 85,
                    "recommendations": [
                        OptimizationStrategy.LAZY_LOADING,
                        OptimizationStrategy.COMPRESSION,
                        OptimizationStrategy.CACHING
                    ]
                },
                "slow_response_time": {
                    "condition": lambda metrics: metrics.get("response_time", 0) > 1000,
                    "recommendations": [
                        OptimizationStrategy.CACHING,
                        OptimizationStrategy.INDEXING,
                        OptimizationStrategy.CONNECTION_POOLING
                    ]
                },
                "high_io_wait": {
                    "condition": lambda metrics: metrics.get("io_wait", 0) > 30,
                    "recommendations": [
                        OptimizationStrategy.BATCHING,
                        OptimizationStrategy.ASYNC,
                        OptimizationStrategy.CONNECTION_POOLING
                    ]
                }
            }
        }
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute performance-specific tasks"""
        task_type = request.task_type
        payload = request.payload
        
        if task_type == "monitor_system":
            return await self._monitor_system(payload)
        
        elif task_type == "profile_application":
            return await self._profile_application(payload)
        
        elif task_type == "detect_bottlenecks":
            return await self._detect_bottlenecks(payload)
        
        elif task_type == "optimize_performance":
            return await self._optimize_performance(payload)
        
        elif task_type == "analyze_trends":
            return await self._analyze_trends(payload)
        
        elif task_type == "generate_report":
            return await self._generate_performance_report(payload)
        
        elif task_type == "load_test":
            return await self._run_load_test(payload)
        
        elif task_type == "auto_scale":
            return await self._auto_scale(payload)
        
        else:
            raise ValueError(f"Unknown performance task: {task_type}")
    
    async def _monitor_system(self, payload: Dict) -> Dict[str, Any]:
        """Monitor system performance metrics"""
        duration = payload.get("duration", 60)  # seconds
        interval = payload.get("interval", 1)   # seconds
        
        monitor_id = f"monitor_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        metrics_collected = []
        
        with self.tracer.start_as_current_span("system_monitoring") as span:
            span.set_attribute("monitor_id", monitor_id)
            span.set_attribute("duration", duration)
            
            end_time = start_time + duration
            
            while time.time() < end_time and not self._shutdown_event.is_set():
                try:
                    # Collect system metrics
                    current_metrics = await self._collect_system_metrics()
                    metrics_collected.append({
                        "timestamp": time.time(),
                        **current_metrics
                    })
                    
                    # Store in history
                    for metric_name, value in current_metrics.items():
                        self.metrics_history[metric_name].append({
                            "timestamp": time.time(),
                            "value": value
                        })
                    
                    # Update Prometheus metrics
                    self._update_prometheus_metrics(current_metrics)
                    
                    # Check thresholds
                    await self._check_thresholds(current_metrics)

                    # Persist metrics to DB
                    await self._db_query(
                        "INSERT INTO system_metrics (metric_name, value, unit, timestamp, metadata) VALUES ($1, $2, $3, $4, $5)",
                        "system_performance", json.dumps(current_metrics), "json", datetime.fromtimestamp(time.time()), json.dumps({"monitor_id": monitor_id})
                    )
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    self.logger.error("System monitoring error", error=str(e))
            
            # Generate summary
            summary = self._generate_monitoring_summary(metrics_collected)
            
            return {
                "monitor_id": monitor_id,
                "duration_actual": time.time() - start_time,
                "metrics_collected": len(metrics_collected),
                "summary": summary,
                "alerts_generated": len([a for a in self.active_alerts.values() 
                                       if a.timestamp >= start_time])
            }
    
    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        metrics = {}
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg()
            
            metrics.update({
                "cpu_usage": cpu_percent,
                "cpu_count": cpu_count,
                "load_avg_1min": load_avg[0],
                "load_avg_5min": load_avg[1],
                "load_avg_15min": load_avg[2]
            })
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics.update({
                "memory_usage": memory.percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_used_gb": memory.used / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "swap_usage": swap.percent,
                "swap_used_gb": swap.used / (1024**3)
            })
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.update({
                    "disk_read_mb_per_sec": disk_io.read_bytes / (1024**2),
                    "disk_write_mb_per_sec": disk_io.write_bytes / (1024**2),
                    "disk_read_iops": disk_io.read_count,
                    "disk_write_iops": disk_io.write_count
                })
            
            # Network I/O metrics
            network_io = psutil.net_io_counters()
            if network_io:
                metrics.update({
                    "network_sent_mb_per_sec": network_io.bytes_sent / (1024**2),
                    "network_recv_mb_per_sec": network_io.bytes_recv / (1024**2),
                    "network_packets_sent": network_io.packets_sent,
                    "network_packets_recv": network_io.packets_recv
                })
            
            # Process-specific metrics
            process = psutil.Process()
            metrics.update({
                "process_cpu_percent": process.cpu_percent(),
                "process_memory_mb": process.memory_info().rss / (1024**2),
                "process_num_threads": process.num_threads(),
                "process_num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
            })
            
            # Python-specific metrics
            gc_stats = gc.get_stats()
            metrics.update({
                "python_gc_collections": sum(stat['collections'] for stat in gc_stats),
                "python_objects_tracked": len(gc.get_objects())
            })
            
        except Exception as e:
            self.logger.error("Error collecting system metrics", error=str(e))
        
        return metrics
    
    async def _profile_application(self, payload: Dict) -> Dict[str, Any]:
        """Profile application performance"""
        target_function_name = payload.get("target_function")
        profiling_type = payload.get("type", "cpu")  # cpu, memory, line
        duration = payload.get("duration", 30)
        
        profile_id = f"profile_{uuid.uuid4().hex[:8]}"
        
        with self.tracer.start_as_current_span("application_profiling") as span:
            span.set_attribute("profile_id", profile_id)
            span.set_attribute("target_function", target_function_name)
            span.set_attribute("profiling_type", profiling_type)

            start_time = time.time()
            profile_data = {}

            try:
                if profiling_type == "cpu":
                    self.profilers["cpu"].enable()
                    # In a real scenario, you'd execute the target_function here
                    # For now, simulate work
                    await asyncio.sleep(duration)
                    self.profilers["cpu"].disable()
                    s = pstats.Stats(self.profilers["cpu"])
                    s.strip_dirs().sort_stats("cumulative").print_stats(10) # Print top 10
                    profile_data["cpu_profile"] = s.get_stats_as_dict()

                elif profiling_type == "memory":
                    # Requires memory_profiler, which might not be installed
                    # from memory_profiler import profile as mem_profile
                    # profile_data["memory_profile"] = mem_profile(target_function_name)()
                    self.logger.warning("Memory profiling not fully implemented without memory_profiler library.")
                    await asyncio.sleep(duration)

                elif profiling_type == "line":
                    # Requires line_profiler, which might not be installed
                    # from line_profiler import LineProfiler
                    # lp = LineProfiler()
                    # lp_wrapper = lp(target_function_name)
                    # lp_wrapper()
                    # profile_data["line_profile"] = lp.print_stats()
                    self.logger.warning("Line profiling not fully implemented without line_profiler library.")
                    await asyncio.sleep(duration)
                
                else:
                    raise ValueError(f"Unsupported profiling type: {profiling_type}")

            except Exception as e:
                self.logger.error(f"Profiling failed for {target_function_name}: {e}")
                span.set_status(Status(StatusCode.ERROR, str(e)))
                return {"profile_id": profile_id, "status": "failed", "error": str(e)}

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Create PerformanceProfile object
            performance_profile = PerformanceProfile(
                profile_id=profile_id,
                target=target_function_name,
                duration_ms=duration_ms,
                cpu_time_ms=profile_data.get("cpu_profile", {}).get("total_time", 0) * 1000,
                memory_peak_mb=0, # Placeholder, needs actual memory profiling data
                function_calls=profile_data.get("cpu_profile", {}).get("ncalls", 0),
                hotspots=[], # Extract from profile_data
                bottlenecks=[], # Extract from profile_data
                timestamp=start_time
            )

            # Persist profile to DB
            await self._db_query(
                "INSERT INTO performance_profiles (profile_id, target, duration_ms, cpu_time_ms, memory_peak_mb, function_calls, hotspots, bottlenecks, timestamp, metadata) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
                performance_profile.profile_id, performance_profile.target, performance_profile.duration_ms,
                performance_profile.cpu_time_ms, performance_profile.memory_peak_mb, performance_profile.function_calls,
                json.dumps(performance_profile.hotspots), json.dumps(performance_profile.bottlenecks),
                datetime.fromtimestamp(performance_profile.timestamp), json.dumps(profile_data)
            )

            self.performance_stats["total_profiles"] += 1
            return {"profile_id": profile_id, "status": "completed", "profile_data": profile_data}

    async def _detect_bottlenecks(self, payload: Dict) -> Dict[str, Any]:
        """Detect performance bottlenecks based on collected metrics and profiles"""
        analysis_id = f"bottleneck_analysis_{uuid.uuid4().hex[:8]}"
        self.logger.info(f"Starting bottleneck detection: {analysis_id}")

        bottlenecks = []
        # Example: Check for high CPU usage over time
        cpu_history = self.metrics_history.get("cpu_usage", deque())
        if len(cpu_history) > 10 and statistics.mean([m["value"] for m in list(cpu_history)[-10:]]) > 80:
            bottlenecks.append({"type": "cpu_bound", "message": "Sustained high CPU usage detected."})

        # Example: Check for high memory usage
        memory_history = self.metrics_history.get("memory_usage", deque())
        if len(memory_history) > 10 and statistics.mean([m["value"] for m in list(memory_history)[-10:]]) > 90:
            bottlenecks.append({"type": "memory_leak", "message": "Sustained high memory usage, potential leak."})

        # Integrate with profiling data if available
        # For simplicity, we'll just use the in-memory history for now.

        # Persist bottlenecks to DB
        await self._db_query(
            "INSERT INTO bottlenecks (analysis_id, detected_at, bottlenecks_data, metadata) VALUES ($1, $2, $3, $4)",
            analysis_id, datetime.now(), json.dumps(bottlenecks), json.dumps(payload)
        )

        if bottlenecks:
            self.logger.warning(f"Bottlenecks detected: {bottlenecks}")
            await self._publish_to_stream("performance.bottleneck.detected", {"analysis_id": analysis_id, "bottlenecks": bottlenecks})
        else:
            self.logger.info("No significant bottlenecks detected.")

        return {"analysis_id": analysis_id, "bottlenecks": bottlenecks}

    async def _optimize_performance(self, payload: Dict) -> Dict[str, Any]:
        """Suggest and apply performance optimizations"""
        optimization_id = f"optimization_{uuid.uuid4().hex[:8]}"
        target = payload.get("target", "system")
        optimization_type = payload.get("type", "auto")

        recommendations: List[OptimizationRecommendation] = []

        # Generate recommendations based on current metrics or detected bottlenecks
        current_metrics = await self._collect_system_metrics()
        for rule_name, rule in self.recommendation_engine["rules"].items():
            if rule["condition"](current_metrics):
                for strategy in rule["recommendations"]:
                    rec = OptimizationRecommendation(
                        id=str(uuid.uuid4()),
                        strategy=strategy,
                        title=f"Consider {strategy.value} for {target}",
                        description=f"Applying {strategy.value} could improve performance due to {rule_name}.",
                        estimated_improvement="moderate",
                        complexity="medium",
                        priority_score=0.7,
                        implementation_steps=[f"Implement {strategy.value} for {target}"]
                    )
                    recommendations.append(rec)
        
        # Persist recommendations to DB
        for rec in recommendations:
            await self._db_query(
                "INSERT INTO optimization_recommendations (recommendation_id, strategy, title, description, estimated_improvement, complexity, priority_score, implementation_steps, metadata, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
                rec.id, rec.strategy.value, rec.title, rec.description, rec.estimated_improvement, rec.complexity,
                rec.priority_score, json.dumps(rec.implementation_steps), json.dumps(rec.metadata), datetime.now()
            )

        self.logger.info(f"Generated {len(recommendations)} optimization recommendations for {target}")
        await self._publish_to_stream("performance.optimization.recommendations", {"optimization_id": optimization_id, "recommendations": [r.__dict__ for r in recommendations]})

        # For 
