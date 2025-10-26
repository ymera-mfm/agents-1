"""
YMERA Enterprise Metrics Collection System
Production-Ready Performance Monitoring & Analytics
✅ PRODUCTION READY - Syntax error at line 445 fixed
"""

import asyncio
import json
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import logging
from enum import Enum
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor
import gc
import sys
import platform
import socket
import uuid
from statistics import mean, median, stdev

class MetricType(Enum):
    """Enumeration of metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"

class MetricScope(Enum):
    """Enumeration of metric scopes"""
    SYSTEM = "system"
    AGENT = "agent"
    LEARNING = "learning"
    API = "api"
    DATABASE = "database"
    REDIS = "redis"
    AI_SERVICE = "ai_service"
    ORCHESTRATION = "orchestration"

@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: Union[int, float]
    timestamp: datetime
    metric_type: MetricType
    scope: MetricScope
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'metric_type': self.metric_type.value,
            'scope': self.scope.value,
            'tags': self.tags,
            'metadata': self.metadata or {}
        }

@dataclass
class SystemResourceMetrics:
    """System resource utilization metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    load_average: List[float]
    active_connections: int
    thread_count: int
    process_count: int
    file_descriptors: int
    timestamp: datetime

@dataclass
class AgentPerformanceMetrics:
    """Individual agent performance metrics"""
    agent_id: str
    agent_type: str
    status: str
    task_count_total: int
    task_count_active: int
    task_count_completed: int
    task_count_failed: int
    average_task_duration: float
    last_activity: datetime
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float
    success_rate: float
    throughput_per_minute: float
    queue_size: int
    learning_score: float
    adaptation_rate: float

@dataclass
class LearningEngineMetrics:
    """Learning engine performance metrics"""
    total_learning_sessions: int
    active_learning_sessions: int
    knowledge_base_size: int
    vector_embeddings_count: int
    learning_rate: float
    adaptation_score: float
    model_accuracy: float
    training_iterations: int
    last_training_time: datetime
    feedback_count: int
    positive_feedback_ratio: float
    knowledge_retention_score: float
    inference_latency_ms: float
    embedding_generation_time_ms: float

@dataclass
class OrchestrationMetrics:
    """Agent orchestration metrics"""
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    average_workflow_duration: float
    coordination_overhead_ms: float
    message_throughput: float
    agent_coordination_score: float
    resource_allocation_efficiency: float

class MetricsAggregator:
    """Advanced metrics aggregation and analysis"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.data_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.lock = threading.RLock()
    
    def add_metric(self, metric: MetricPoint):
        """Add a metric point to the aggregation window"""
        with self.lock:
            key = f"{metric.scope.value}.{metric.name}"
            self.data_windows[key].append(metric)
    
    def get_statistics(self, metric_key: str) -> Dict[str, float]:
        """Get statistical analysis of a metric"""
        with self.lock:
            window = self.data_windows.get(metric_key, deque())
            if not window:
                return {}
            
            values = [point.value for point in window if isinstance(point.value, (int, float))]
            if not values:
                return {}
            
            try:
                return {
                    'count': len(values),
                    'sum': sum(values),
                    'mean': mean(values),
                    'median': median(values),
                    'min': min(values),
                    'max': max(values),
                    'std_dev': stdev(values) if len(values) > 1 else 0.0,
                    'latest': values[-1],
                    'trend': self._calculate_trend(values)
                }
            except Exception as e:
                logging.error(f"Error calculating statistics for {metric_key}: {e}")
                return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
        
        recent = values[-min(10, len(values)):]
        older = values[-min(20, len(values)):-10] or values[:1]
        
        recent_avg = mean(recent)
        older_avg = mean(older)
        
        if recent_avg > older_avg * 1.05:
            return "increasing"
        elif recent_avg < older_avg * 0.95:
            return "decreasing"
        else:
            return "stable"

class MetricsCollector:
    """
    Enterprise-grade metrics collection system for YMERA multi-agent platform
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        health_monitor=None,
        collection_interval: int = 30,
        retention_hours: int = 24,
        batch_size: int = 100,
        enable_detailed_profiling: bool = True
    ):
        self.redis_client = redis_client
        self.health_monitor = health_monitor
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours
        self.batch_size = batch_size
        self.enable_detailed_profiling = enable_detailed_profiling
        
        self.logger = logging.getLogger(f"{__name__}.MetricsCollector")
        self.aggregator = MetricsAggregator()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="metrics")
        
        self.is_running = False
        self.is_initialized = False
        self.collection_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.last_collection_time: Optional[datetime] = None
        
        self.metrics_buffer: List[MetricPoint] = []
        self.buffer_lock = asyncio.Lock()
        self.collection_count = 0
        self.error_count = 0
        
        self.instance_id = str(uuid.uuid4())[:8]
        self.hostname = socket.gethostname()
        self.platform_info = {
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
        
        self.redis_keys = {
            'metrics': f"ymera:metrics:{self.instance_id}",
            'system_stats': f"ymera:system_stats:{self.instance_id}",
            'agent_stats': f"ymera:agent_stats:{self.instance_id}",
            'learning_stats': f"ymera:learning_stats:{self.instance_id}",
            'orchestration_stats': f"ymera:orchestration_stats:{self.instance_id}",
            'performance_summary': f"ymera:performance_summary:{self.instance_id}"
        }
        
        self._baseline_metrics = {}
    
    async def initialize(self) -> bool:
        """Initialize the metrics collection system"""
        try:
            self.logger.info("Initializing YMERA Metrics Collection System...")
            
            await self.redis_client.ping()
            await self._setup_redis_structures()
            await self._collect_baseline_metrics()
            
            if not self.collection_task:
                self.collection_task = asyncio.create_task(self._collection_loop())
            
            if not self.cleanup_task:
                self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.is_initialized = True
            self.logger.info("✅ Metrics Collection System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics collector: {e}")
            return False
    
    async def _setup_redis_structures(self):
        """Set up Redis data structures for metrics storage"""
        pipeline = self.redis_client.pipeline()
        
        for key in self.redis_keys.values():
            pipeline.expire(key, self.retention_hours * 3600)
        
        await pipeline.execute()
    
    async def _collect_baseline_metrics(self):
        """Collect baseline system metrics for comparison"""
        try:
            process = psutil.Process()
            system_info = {
                'boot_time': psutil.boot_time(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_total': psutil.disk_usage('/').total,
                'process_start_time': process.create_time()
            }
            
            self._baseline_metrics = system_info
            await self.redis_client.hset(
                f"{self.redis_keys['system_stats']}:baseline",
                mapping={k: json.dumps(v) for k, v in system_info.items()}
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting baseline metrics: {e}")
    
    async def start_collection(self):
        """Start metrics collection"""
        if not self.is_initialized:
            await self.initialize()
        
        self.is_running = True
        self.logger.info("🚀 Metrics collection started")
    
    async def stop_collection(self):
        """Stop metrics collection gracefully"""
        self.is_running = False
        
        if self.collection_task and not self.collection_task.done():
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self._flush_metrics_buffer()
        self.executor.shutdown(wait=True)
        self.logger.info("✅ Metrics collection stopped")
    
    async def _collection_loop(self):
        """Main metrics collection loop"""
        while self.is_running:
            try:
                start_time = time.time()
                
                await asyncio.gather(
                    self._collect_system_metrics(),
                    self._collect_agent_metrics(),
                    self._collect_learning_metrics(),
                    self._collect_orchestration_metrics(),
                    self._collect_api_metrics(),
                    return_exceptions=True
                )
                
                await self._flush_metrics_buffer()
                
                collection_duration = time.time() - start_time
                self.collection_count += 1
                self.last_collection_time = datetime.utcnow()
                
                await self._record_metric(
                    name="collection_duration_seconds",
                    value=collection_duration,
                    metric_type=MetricType.TIMER,
                    scope=MetricScope.SYSTEM,
                    tags={"component": "metrics_collector"}
                )
                
                await asyncio.sleep(max(0, self.collection_interval - collection_duration))
                
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _cleanup_loop(self):
        """Background cleanup of old metrics"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)
                await self._cleanup_old_metrics()
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _collect_system_metrics(self):
        """Collect comprehensive system resource metrics"""
        try:
            system_metrics = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._get_system_resource_metrics
            )
            
            timestamp = datetime.utcnow()
            metrics = [
                MetricPoint("cpu_usage_percent", system_metrics.cpu_percent, timestamp, MetricType.GAUGE, MetricScope.SYSTEM, {"host": self.hostname}),
                MetricPoint("memory_usage_percent", system_metrics.memory_percent, timestamp, MetricType.GAUGE, MetricScope.SYSTEM, {"host": self.hostname}),
                MetricPoint("memory_used_mb", system_metrics.memory_used_mb, timestamp, MetricType.GAUGE, MetricScope.SYSTEM, {"host": self.hostname}),
                MetricPoint("disk_usage_percent", system_metrics.disk_usage_percent, timestamp, MetricType.GAUGE, MetricScope.SYSTEM, {"host": self.hostname}),
                MetricPoint("network_bytes_sent", system_metrics.network_bytes_sent, timestamp, MetricType.COUNTER, MetricScope.SYSTEM, {"host": self.hostname}),
                MetricPoint("network_bytes_recv", system_metrics.network_bytes_recv, timestamp, MetricType.COUNTER, MetricScope.SYSTEM, {"host": self.hostname}),
                MetricPoint("active_connections", system_metrics.active_connections, timestamp, MetricType.GAUGE, MetricScope.SYSTEM, {"host": self.hostname}),
                MetricPoint("thread_count", system_metrics.thread_count, timestamp, MetricType.GAUGE, MetricScope.SYSTEM, {"host": self.hostname}),
                MetricPoint("process_count", system_metrics.process_count, timestamp, MetricType.GAUGE, MetricScope.SYSTEM, {"host": self.hostname}),
            ]
            
            if system_metrics.load_average:
                for i, load in enumerate(system_metrics.load_average):
                    metrics.append(
                        MetricPoint(f"load_average_{i+1}min", load, timestamp, MetricType.GAUGE, MetricScope.SYSTEM, {"host": self.hostname})
                    )
            
            await self._add_metrics_to_buffer(metrics)
            
            await self.redis_client.hset(
                self.redis_keys['system_stats'],
                f"snapshot_{int(timestamp.timestamp())}",
                json.dumps(asdict(system_metrics), default=str)
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _get_system_resource_metrics(self) -> SystemResourceMetrics:
        """✅ FIX: Complete function implementation (was incomplete at line 445)"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            disk_used_gb = disk.used / (1024 ** 3)
            disk_free_gb = disk.free / (1024 ** 3)
            
            net_io = psutil.net_io_counters()
            network_bytes_sent = net_io.bytes_sent
            network_bytes_recv = net_io.bytes_recv
            
            try:
                load_average = list(psutil.getloadavg())
            except (AttributeError, OSError):
                load_average = [0.0, 0.0, 0.0]
            
            try:
                active_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, OSError):
                active_connections = 0
            
            thread_count = threading.active_count()
            process_count = len(psutil.pids())
            
            try:
                process = psutil.Process()
                file_descriptors = process.num_fds() if hasattr(process, 'num_fds') else 0
            except (psutil.AccessDenied, AttributeError):
                file_descriptors = 0
            
            return SystemResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                load_average=load_average,
                active_connections=active_connections,
                thread_count=thread_count,
                process_count=process_count,
                file_descriptors=file_descriptors,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system resource metrics: {e}")
            return SystemResourceMetrics(
                cpu_percent=0.0, memory_percent=0.0, memory_used_mb=0.0,
                memory_available_mb=0.0, disk_usage_percent=0.0, disk_used_gb=0.0,
                disk_free_gb=0.0, network_bytes_sent=0, network_bytes_recv=0,
                load_average=[0.0, 0.0, 0.0], active_connections=0,
                thread_count=0, process_count=0, file_descriptors=0,
                timestamp=datetime.utcnow()
            )
    
    async def _collect_agent_metrics(self):
        """Collect agent performance metrics"""
        try:
            agent_data = await self.redis_client.hgetall("ymera:agents:active")
            
            if not agent_data:
                return
            
            timestamp = datetime.utcnow()
            
            for agent_id, agent_info_json in agent_data.items():
                try:
                    agent_info = json.loads(agent_info_json)
                    
                    metrics = [
                        MetricPoint(f"agent_{agent_id}_task_count", agent_info.get('task_count', 0), 
                                  timestamp, MetricType.COUNTER, MetricScope.AGENT, {"agent_id": agent_id}),
                        MetricPoint(f"agent_{agent_id}_success_rate", agent_info.get('success_rate', 0), 
                                  timestamp, MetricType.GAUGE, MetricScope.AGENT, {"agent_id": agent_id}),
                        MetricPoint(f"agent_{agent_id}_avg_duration", agent_info.get('avg_duration', 0), 
                                  timestamp, MetricType.GAUGE, MetricScope.AGENT, {"agent_id": agent_id}),
                    ]
                    
                    await self._add_metrics_to_buffer(metrics)
                    
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error collecting agent metrics: {e}")
    
    async def _collect_learning_metrics(self):
        """Collect learning engine metrics"""
        try:
            learning_data = await self.redis_client.hgetall("ymera:learning:stats")
            
            if not learning_data:
                return
            
            timestamp = datetime.utcnow()
            metrics = []
            
            for key, value in learning_data.items():
                try:
                    numeric_value = float(value)
                    metrics.append(
                        MetricPoint(f"learning_{key}", numeric_value, timestamp, 
                                  MetricType.GAUGE, MetricScope.LEARNING, {"component": "learning_engine"})
                    )
                except (ValueError, TypeError):
                    continue
            
            if metrics:
                await self._add_metrics_to_buffer(metrics)
                
        except Exception as e:
            self.logger.error(f"Error collecting learning metrics: {e}")
    
    async def _collect_orchestration_metrics(self):
        """Collect orchestration metrics"""
        try:
            orch_data = await self.redis_client.hgetall("ymera:orchestration:stats")
            
            if not orch_data:
                return
            
            timestamp = datetime.utcnow()
            metrics = []
            
            for key, value in orch_data.items():
                try:
                    numeric_value = float(value)
                    metrics.append(
                        MetricPoint(f"orchestration_{key}", numeric_value, timestamp,
                                  MetricType.GAUGE, MetricScope.ORCHESTRATION, {"component": "orchestrator"})
                    )
                except (ValueError, TypeError):
                    continue
            
            if metrics:
                await self._add_metrics_to_buffer(metrics)
                
        except Exception as e:
            self.logger.error(f"Error collecting orchestration metrics: {e}")
    
    async def _collect_api_metrics(self):
        """Collect API performance metrics"""
        try:
            api_data = await self.redis_client.hgetall("ymera:api:stats")
            
            if not api_data:
                return
            
            timestamp = datetime.utcnow()
            metrics = []
            
            for endpoint, stats_json in api_data.items():
                try:
                    stats = json.loads(stats_json)
                    
                    metrics.extend([
                        MetricPoint(f"api_{endpoint}_requests", stats.get('requests', 0),
                                  timestamp, MetricType.COUNTER, MetricScope.API, {"endpoint": endpoint}),
                        MetricPoint(f"api_{endpoint}_avg_latency", stats.get('avg_latency', 0),
                                  timestamp, MetricType.GAUGE, MetricScope.API, {"endpoint": endpoint}),
                        MetricPoint(f"api_{endpoint}_error_rate", stats.get('error_rate', 0),
                                  timestamp, MetricType.GAUGE, MetricScope.API, {"endpoint": endpoint}),
                    ])
                    
                except json.JSONDecodeError:
                    continue
            
            if metrics:
                await self._add_metrics_to_buffer(metrics)
                
        except Exception as e:
            self.logger.error(f"Error collecting API metrics: {e}")
    
    async def _add_metrics_to_buffer(self, metrics: List[MetricPoint]):
        """Add metrics to buffer for batch processing"""
        async with self.buffer_lock:
            self.metrics_buffer.extend(metrics)
            
            for metric in metrics:
                self.aggregator.add_metric(metric)
    
    async def _flush_metrics_buffer(self):
        """Flush metrics buffer to Redis"""
        async with self.buffer_lock:
            if not self.metrics_buffer:
                return
            
            try:
                pipeline = self.redis_client.pipeline()
                
                for metric in self.metrics_buffer:
                    metric_key = f"{self.redis_keys['metrics']}:{metric.scope.value}:{metric.name}"
                    pipeline.lpush(metric_key, json.dumps(metric.to_dict()))
                    pipeline.ltrim(metric_key, 0, 999)
                
                await pipeline.execute()
                
                self.metrics_buffer.clear()
                
            except Exception as e:
                self.logger.error(f"Error flushing metrics buffer: {e}")
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
            
            keys = await self.redis_client.keys(f"{self.redis_keys['metrics']}:*")
            
            for key in keys:
                try:
                    metrics_data = await self.redis_client.lrange(key, 0, -1)
                    
                    valid_metrics = []
                    for metric_json in metrics_data:
                        try:
                            metric = json.loads(metric_json)
                            metric_time = datetime.fromisoformat(metric['timestamp'])
                            
                            if metric_time > cutoff_time:
                                valid_metrics.append(metric_json)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue
                    
                    if valid_metrics:
                        await self.redis_client.delete(key)
                        pipeline = self.redis_client.pipeline()
                        for metric in valid_metrics:
                            pipeline.rpush(key, metric)
                        await pipeline.execute()
                    else:
                        await self.redis_client.delete(key)
                        
                except Exception as e:
                    self.logger.warning(f"Error cleaning up key {key}: {e}")
            
            self.logger.info(f"Cleaned up metrics older than {self.retention_hours} hours")
            
        except Exception as e:
            self.logger.error(f"Error in metrics cleanup: {e}")
    
    async def _record_metric(self, name: str, value: float, metric_type: MetricType, 
                           scope: MetricScope, tags: Dict[str, str]):
        """Record a single metric"""
        metric = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            scope=scope,
            tags=tags
        )
        
        await self._add_metrics_to_buffer([metric])
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        try:
            return {
                "collection_status": "running" if self.is_running else "stopped",
                "instance_id": self.instance_id,
                "hostname": self.hostname,
                "collection_count": self.collection_count,
                "error_count": self.error_count,
                "last_collection": self.last_collection_time.isoformat() if self.last_collection_time else None,
                "buffer_size": len(self.metrics_buffer),
                "platform_info": self.platform_info,
                "statistics": {
                    key: self.aggregator.get_statistics(key)
                    for key in list(self.aggregator.data_windows.keys())[:20]
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {e}")
            return {"error": str(e)}

# ===================== EXPORTS =====================

__all__ = [
    'MetricsCollector',
    'MetricType',
    'MetricScope',
    'MetricPoint',
    'SystemResourceMetrics',
    'AgentPerformanceMetrics',
    'LearningEngineMetrics',
    'OrchestrationMetrics',
    'MetricsAggregator',
]