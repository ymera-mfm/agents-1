"""
Production-Ready Optimizing Engine v3.0
Enterprise-grade performance optimization with resilience, observability, and auto-healing
"""

import asyncio
import json
import time
import psutil
import numpy as np
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from collections import defaultdict, deque
import statistics
from datetime import datetime, timedelta
import traceback
import signal
import sys

# Third-party imports
try:
    import redis.asyncio as aioredis
    import asyncpg
    from opentelemetry import trace, metrics
    from opentelemetry.trace import Status, StatusCode
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
except ImportError as e:
    print(f"Warning: Optional dependency not found: {e}")
    print("Install with: pip install redis asyncpg opentelemetry-api prometheus-client")

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class OptimizationType(Enum):
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    CACHE = "cache"
    DATABASE = "database"
    NETWORK = "network"
    MEMORY = "memory"
    CPU = "cpu"
    QUERY = "query"

class OptimizationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    EXPERIMENTAL = "experimental"

class MetricType(Enum):
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    QUEUE_DEPTH = "queue_depth"

class CacheStrategy(Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    ADAPTIVE = "adaptive"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class OptimizationRule:
    """Optimization rule with enhanced validation"""
    rule_id: str
    name: str
    optimization_type: OptimizationType
    condition: str
    action: str
    priority: int
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    cooldown_seconds: int = 300
    last_applied: float = 0.0
    application_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.application_count == 0:
            return 0.0
        return (self.success_count / self.application_count) * 100
    
    def can_apply(self) -> bool:
        """Check if rule can be applied"""
        return (
            self.enabled and 
            time.time() - self.last_applied >= self.cooldown_seconds
        )

@dataclass
class PerformanceMetric:
    """Performance metric with validation"""
    metric_id: str
    metric_type: MetricType
    value: float
    timestamp: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Validate metric"""
        return (
            self.value >= 0 and
            self.timestamp > 0 and
            len(self.source) > 0
        )

@dataclass
class OptimizationResult:
    """Enhanced optimization result with detailed tracking"""
    optimization_id: str
    rule_id: str
    applied_at: float
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float] = field(default_factory=dict)
    improvement: Dict[str, float] = field(default_factory=dict)
    success: bool = False
    error: Optional[str] = None
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class CircuitBreakerState:
    """Circuit breaker state for resilience"""
    name: str
    state: str = "closed"  # closed, open, half_open
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    failure_threshold: int = 5
    timeout_seconds: int = 60
    
    def should_attempt(self) -> bool:
        """Check if operation should be attempted"""
        if self.state == "closed":
            return True
        if self.state == "half_open":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.timeout_seconds:
                self.state = "half_open"
                return True
        return False
    
    def record_success(self):
        """Record successful operation"""
        self.success_count += 1
        if self.state == "half_open":
            if self.success_count >= 3:
                self.state = "closed"
                self.failure_count = 0
                self.success_count = 0
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

class PrometheusMetrics:
    """Prometheus metrics for monitoring"""
    
    def __init__(self, prefix: str = "optimizing_engine"):
        self.optimizations_total = Counter(
            f'{prefix}_optimizations_total',
            'Total number of optimizations applied',
            ['rule_id', 'status']
        )
        
        self.optimization_duration = Histogram(
            f'{prefix}_optimization_duration_seconds',
            'Time spent on optimization',
            ['rule_id']
        )
        
        self.active_rules = Gauge(
            f'{prefix}_active_rules',
            'Number of active optimization rules'
        )
        
        self.system_cpu = Gauge(
            f'{prefix}_system_cpu_percent',
            'System CPU usage percentage'
        )
        
        self.system_memory = Gauge(
            f'{prefix}_system_memory_percent',
            'System memory usage percentage'
        )
        
        self.cache_hit_rate = Gauge(
            f'{prefix}_cache_hit_rate',
            'Cache hit rate percentage'
        )

# ============================================================================
# OPTIMIZING ENGINE
# ============================================================================

class OptimizingEngine(BaseAgent):
    """
    Production-Ready Optimizing Engine v3.0
    
    Features:
    - Real-time performance monitoring with circuit breakers
    - Intelligent resource allocation with auto-scaling
    - Multi-level caching with adaptive strategies
    - Database query optimization with connection pooling
    - Predictive optimization using statistical models
    - Comprehensive error handling and retry logic
    - Graceful degradation under load
    - Full observability with OpenTelemetry and Prometheus
    - Health checks and readiness probes
    - Configuration validation
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Optimization rules and strategies
        self.optimization_rules: Dict[str, OptimizationRule] = {}
        self.optimization_history: deque = deque(maxlen=10000)
        
        # Performance metrics with bounded storage
        self.metrics_buffer: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.metric_aggregates: Dict[str, Dict] = {}
        
        # Cache management
        self.cache_strategies: Dict[str, CacheStrategy] = {}
        self.cache_stats: Dict[str, Dict] = defaultdict(dict)
        
        # Resource monitoring
        self.resource_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "network_latency": 200.0,
            "error_rate": 5.0
        }
        
        # Optimization statistics
        self.optimization_stats = {
            "optimizations_applied": 0,
            "optimizations_failed": 0,
            "performance_improvements": 0,
            "resource_savings": 0,
            "cache_optimizations": 0,
            "query_optimizations": 0,
            "average_improvement": 0.0
        }
        
        # Circuit breakers for resilience
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {
            "database": CircuitBreakerState("database", failure_threshold=5),
            "redis": CircuitBreakerState("redis", failure_threshold=3),
            "external_api": CircuitBreakerState("external_api", failure_threshold=3)
        }
        
        # Connection pools
        self.connection_pools: Dict[str, Any] = {}
        self.pool_stats: Dict[str, Dict] = defaultdict(dict)
        
        # Rate limiting
        self.rate_limiters: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )
        
        # Health status
        self.health_status = HealthStatus.UNKNOWN
        self.last_health_check = 0.0
        
        # Prometheus metrics
        try:
            self.prom_metrics = PrometheusMetrics()
        except:
            self.prom_metrics = None
            self.logger.warning("Prometheus metrics disabled")
        
        # Graceful shutdown
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self.logger.info(
            "OptimizingEngine initialized",
            version="3.0",
            features=[
                "circuit_breakers",
                "rate_limiting",
                "observability",
                "auto_scaling"
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.shutdown_event.set()
    
    async def start(self):
        """Start optimizing engine with health checks"""
        try:
            # Start Prometheus metrics server
            if self.prom_metrics:
                try:
                    start_http_server(9090)
                    self.logger.info("Prometheus metrics server started on port 9090")
                except Exception as e:
                    self.logger.warning(f"Failed to start Prometheus server: {e}")
            
            # Load rules from database with retry
            await self._load_rules_with_retry()
            
            # Setup subscriptions
            await self._setup_subscriptions()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Initial health check
            await self._perform_health_check()
            
            self.logger.info(
                "OptimizingEngine started successfully",
                rules_count=len(self.optimization_rules),
                health=self.health_status.value
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start OptimizingEngine: {e}", exc_info=True)
            return False
    
    async def _setup_subscriptions(self):
        """Setup NATS subscriptions with error handling"""
        subscriptions = [
            (f"agent.{self.config.name}.task", self._handle_optimization_task),
            ("metrics.performance", self._handle_performance_metrics),
            ("alerts.resource", self._handle_resource_alerts),
            ("optimization.request", self._handle_optimization_request),
            ("optimization.rule.update", self._handle_rule_update),
            (f"health.{self.config.name}", self._handle_health_check)
        ]
        
        for subject, handler in subscriptions:
            try:
                await self._subscribe(
                    subject,
                    handler,
                    queue_group=f"{self.config.name}_workers"
                )
                self.logger.debug(f"Subscribed to {subject}")
            except Exception as e:
                self.logger.error(f"Failed to subscribe to {subject}: {e}")
    
    async def _start_background_tasks(self):
        """Start background optimization tasks"""
        tasks = [
            ("continuous_monitoring", self._continuous_monitoring()),
            ("predictive_optimization", self._predictive_optimization()),
            ("cache_optimization", self._cache_optimization()),
            ("resource_optimization", self._resource_optimization()),
            ("cleanup_metrics", self._cleanup_metrics()),
            ("health_monitor", self._health_monitor()),
            ("metrics_aggregator", self._metrics_aggregator()),
            ("circuit_breaker_monitor", self._circuit_breaker_monitor())
        ]
        
        for name, coro in tasks:
            task = asyncio.create_task(coro)
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
            self.logger.debug(f"Started background task: {name}")
    
    async def _load_rules_with_retry(self, max_retries: int = 3):
        """Load optimization rules with retry logic"""
        for attempt in range(max_retries):
            try:
                if not self.db_pool:
                    self.logger.warning("DB pool not available, loading default rules")
                    self._load_default_rules()
                    return
                
                records = await self._db_query_with_circuit_breaker(
                    """
                    SELECT rule_id, name, optimization_type, condition, 
                           action, priority, enabled, parameters, 
                           cooldown_seconds, last_applied, 
                           application_count, success_count, failure_count
                    FROM optimization_rules
                    WHERE enabled = true
                    ORDER BY priority ASC
                    """
                )
                
                if records:
                    for r in records:
                        rule = OptimizationRule(
                            rule_id=r["rule_id"],
                            name=r["name"],
                            optimization_type=OptimizationType[r["optimization_type"].upper()],
                            condition=r["condition"],
                            action=r["action"],
                            priority=r["priority"],
                            enabled=r["enabled"],
                            parameters=json.loads(r["parameters"]) if r["parameters"] else {},
                            cooldown_seconds=r["cooldown_seconds"],
                            last_applied=r["last_applied"].timestamp() if r["last_applied"] else 0.0,
                            application_count=r.get("application_count", 0),
                            success_count=r.get("success_count", 0),
                            failure_count=r.get("failure_count", 0)
                        )
                        self.optimization_rules[rule.rule_id] = rule
                    
                    self.logger.info(f"Loaded {len(self.optimization_rules)} rules from database")
                    
                    if self.prom_metrics:
                        self.prom_metrics.active_rules.set(len(self.optimization_rules))
                    
                    return
                else:
                    self.logger.info("No rules in database, loading defaults")
                    self._load_default_rules()
                    return
                    
            except Exception as e:
                self.logger.warning(
                    f"Failed to load rules (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error("Max retries reached, loading default rules")
                    self._load_default_rules()
    
    async def _db_query_with_circuit_breaker(self, query: str, *args):
        """Execute database query with circuit breaker"""
        cb = self.circuit_breakers["database"]
        
        if not cb.should_attempt():
            raise Exception("Circuit breaker open for database")
        
        try:
            result = await self._db_query(query, *args)
            cb.record_success()
            return result
        except Exception as e:
            cb.record_failure()
            raise
    
    def _load_default_rules(self):
        """Load comprehensive default optimization rules"""
        default_rules = [
            # CPU Optimization Rules
            OptimizationRule(
                rule_id="cpu_critical_usage",
                name="Critical CPU Usage Response",
                optimization_type=OptimizationType.CPU,
                condition="cpu_usage > 95",
                action="emergency_scale_workers",
                priority=0,
                parameters={"scale_factor": 2.0, "max_workers": 50}
            ),
            OptimizationRule(
                rule_id="cpu_high_usage",
                name="High CPU Usage Optimization",
                optimization_type=OptimizationType.CPU,
                condition="cpu_usage > 80",
                action="scale_workers",
                priority=1,
                parameters={"scale_factor": 1.5, "max_workers": 20}
            ),
            
            # Memory Optimization Rules
            OptimizationRule(
                rule_id="memory_critical",
                name="Critical Memory Pressure",
                optimization_type=OptimizationType.MEMORY,
                condition="memory_usage > 95",
                action="emergency_gc_and_cache_purge",
                priority=0,
                parameters={"purge_percentage": 50}
            ),
            OptimizationRule(
                rule_id="memory_high_usage",
                name="High Memory Usage Optimization",
                optimization_type=OptimizationType.MEMORY,
                condition="memory_usage > 85",
                action="trigger_gc_and_cache_cleanup",
                priority=1,
                parameters={"cache_cleanup_percentage": 30}
            ),
            
            # Cache Optimization Rules
            OptimizationRule(
                rule_id="cache_low_hit_rate",
                name="Low Cache Hit Rate Optimization",
                optimization_type=OptimizationType.CACHE,
                condition="cache_hit_rate < 70",
                action="optimize_cache_strategy",
                priority=2,
                parameters={"target_hit_rate": 85.0}
            ),
            
            # Database Optimization Rules
            OptimizationRule(
                rule_id="db_slow_queries",
                name="Slow Database Queries Optimization",
                optimization_type=OptimizationType.DATABASE,
                condition="query_time_avg > 500",
                action="optimize_slow_queries",
                priority=1,
                parameters={"threshold_ms": 500}
            ),
            
            # Network Optimization Rules
            OptimizationRule(
                rule_id="network_high_latency",
                name="High Network Latency Optimization",
                optimization_type=OptimizationType.NETWORK,
                condition="network_latency > 100",
                action="optimize_network_settings",
                priority=2,
                parameters={"enable_compression": True}
            )
        ]
        
        for rule in default_rules:
            self.optimization_rules[rule.rule_id] = rule
        
        self.logger.info(f"Loaded {len(default_rules)} default optimization rules")
        
        if self.prom_metrics:
            self.prom_metrics.active_rules.set(len(self.optimization_rules))
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute optimization tasks with comprehensive error handling"""
        start_time = time.time()
        
        try:
            # Rate limiting check
            if not await self._check_rate_limit(request.task_type):
                return {
                    "status": "error",
                    "error": "Rate limit exceeded",
                    "retry_after": 60
                }
            
            # Route to appropriate handler
            handlers = {
                "optimize_performance": self._optimize_performance,
                "optimize_resource": self._optimize_resource_allocation,
                "optimize_cache": self._optimize_cache_strategy,
                "optimize_database": self._optimize_database,
                "analyze_performance": self._analyze_performance,
                "predict_optimization": self._predict_optimization_needs,
                "benchmark_performance": self._benchmark_performance,
                "tune_parameters": self._tune_parameters,
                "get_metrics": self._get_current_metrics,
                "get_health": self._get_health_status
            }
            
            handler = handlers.get(request.task_type)
            if not handler:
                return {
                    "status": "error",
                    "error": f"Unknown task type: {request.task_type}"
                }
            
            result = await handler(request.payload)
            
            # Add timing information
            result["execution_time_ms"] = (time.time() - start_time) * 1000
            result["status"] = result.get("status", "success")
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Task execution failed: {request.task_type}",
                error=str(e),
                exc_info=True
            )
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
    
    async def _check_rate_limit(self, operation: str, limit: int = 100) -> bool:
        """Check rate limit for operation"""
        current_time = time.time()
        window = 60  # 1 minute window
        
        # Clean old entries
        limiter = self.rate_limiters[operation]
        while limiter and limiter[0] < current_time - window:
            limiter.popleft()
        
        # Check limit
        if len(limiter) >= limit:
            return False
        
        # Record new request
        limiter.append(current_time)
        return True
    
    async def _continuous_monitoring(self):
        """Continuous performance monitoring with error recovery"""
        self.logger.info("Starting continuous monitoring")
        
        while not self.shutdown_event.is_set():
            try:
                # Collect system metrics
                metrics = await self._collect_current_metrics("all", 60)
                
                # Update Prometheus metrics
                if self.prom_metrics and metrics:
                    self.prom_metrics.system_cpu.set(metrics.get("cpu_usage", 0))
                    self.prom_metrics.system_memory.set(metrics.get("memory_usage", 0))
                
                # Identify optimization opportunities
                opportunities = await self._identify_optimization_opportunities(metrics)
                
                # Apply high-priority optimizations
                for opp in opportunities[:3]:  # Limit to top 3
                    if (opp["priority"] <= 1 and 
                        opp["confidence"] > 0.8 and
                        opp["estimated_impact"] > 0.2):
                        
                        result = await self._apply_optimization_safe(opp)
                        if result.get("success"):
                            self.logger.info(
                                "Auto-optimization applied",
                                rule_id=opp["rule_id"],
                                impact=opp["estimated_impact"]
                            )
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}", exc_info=True)
                await asyncio.sleep(30)
        
        self.logger.info("Continuous monitoring stopped")
    
    async def _apply_optimization_safe(self, opportunity: Dict) -> Dict[str, Any]:
        """Apply optimization with comprehensive safety checks"""
        rule = opportunity["rule"]
        
        try:
            # Check if rule can be applied
            if not rule.can_apply():
                return {
                    "success": False,
                    "error": "Rule in cooldown or disabled"
                }
            
            # Record start time
            start_time = time.time()
            
            # Apply optimization
            result = await self._apply_optimization(opportunity)
            
            # Update rule statistics
            rule.application_count += 1
            rule.last_applied = time.time()
            
            if result.get("success"):
                rule.success_count += 1
                
                # Update Prometheus metrics
                if self.prom_metrics:
                    self.prom_metrics.optimizations_total.labels(
                        rule_id=rule.rule_id,
                        status="success"
                    ).inc()
                    
                    duration = time.time() - start_time
                    self.prom_metrics.optimization_duration.labels(
                        rule_id=rule.rule_id
                    ).observe(duration)
                
                # Persist success
                await self._update_rule_stats(rule)
            else:
                rule.failure_count += 1
                
                if self.prom_metrics:
                    self.prom_metrics.optimizations_total.labels(
                        rule_id=rule.rule_id,
                        status="failure"
                    ).inc()
            
            return result
            
        except Exception as e:
            rule.failure_count += 1
            self.logger.error(
                f"Optimization failed: {rule.rule_id}",
                error=str(e),
                exc_info=True
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _health_monitor(self):
        """Monitor system health continuously"""
        self.logger.info("Starting health monitor")
        
        while not self.shutdown_event.is_set():
            try:
                await self._perform_health_check()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        self.logger.info("Health monitor stopped")
    
    async def _perform_health_check(self):
        """Perform comprehensive health check"""
        try:
            checks = {
                "database": await self._check_database_health(),
                "redis": await self._check_redis_health(),
                "nats": await self._check_nats_health(),
                "memory": await self._check_memory_health(),
                "cpu": await self._check_cpu_health()
            }
            
            # Determine overall health
            failed_checks = [k for k, v in checks.items() if not v]
            
            if len(failed_checks) == 0:
                self.health_status = HealthStatus.HEALTHY
            elif len(failed_checks) <= 1:
                self.health_status = HealthStatus.DEGRADED
            else:
                self.health_status = HealthStatus.UNHEALTHY
            
            self.last_health_check = time.time()
            
            self.logger.debug(
                "Health check completed",
                status=self.health_status.value,
                failed=failed_checks
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self.health_status = HealthStatus.UNKNOWN
    
    async def _check_database_health(self) -> bool:
        """Check database health"""
        try:
            if not self.db_pool:
                return False
            
            cb = self.circuit_breakers["database"]
            if not cb.should_attempt():
                return False
            
            await self._db_query_with_circuit_breaker("SELECT 1")
            return True
            
        except:
            return False
    
    async def _check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            if not self.redis_client:
                return False
            
            cb = self.circuit_breakers["redis"]
            if not cb.should_attempt():
                return False
            
            await self.redis_client.ping()
            cb.record_success()
            return True
            
        except:
            return False
    
    async def _check_nats_health(self) -> bool:
        """Check NATS health"""
        try:
            return self.nc is not None and not self.nc.is_closed
        except:
            return False
    
    async def _check_memory_health(self) -> bool:
        """Check memory health"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent < 95
        except:
            return False
    
    async def _check_cpu_health(self) -> bool:
        """Check CPU health"""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            return cpu < 95
        except:
            return False
    
    async def _circuit_breaker_monitor(self):
        """Monitor and reset circuit breakers"""
        self.logger.info("Starting circuit breaker monitor")
        
        while not self.shutdown_event.is_set():
            try:
                for name, cb in self.circuit_breakers.items():
                    # Log circuit breaker state
                    if cb.state != "closed":
                        self.logger.warning(
                            f"Circuit breaker {name} is {cb.state}",
                            failures=cb.failure_count,
                            last_failure=cb.last_failure_time
                        )
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Circuit breaker monitor error: {e}")
                await asyncio.sleep(60)
        
        self.logger.info("Circuit breaker monitor stopped")
    
    async def _get_health_status(self, payload: Dict) -> Dict[str, Any]:
        """Get current health status"""
        return {
            "status": self.health_status.value,
            "last_check": self.last_health_check,
            "uptime_seconds": time.time() - self.start_time if hasattr(self, 'start_time') else 0,
            "circuit_breakers": {
                name: {
                    "state": cb.state,
                    "failures": cb.failure_count,
                    "successes": cb.success_count
                }
                for name, cb in self.circuit_breakers.items()
            },
            "optimization_stats": self.optimization_stats,
            "active_rules": len([r for r in self.optimization_rules.values() if r.enabled])
        }
    
    async def stop(self):
        """Graceful shutdown"""
        self.logger.info("Initiating graceful shutdown")
        
        # Set shutdown event
        self.shutdown_event.set()
        
        # Wait for background tasks
        if self.background_tasks:
            self.logger.info(f"Waiting for {len(self.background_tasks)} background tasks")
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Close connections
        await self._close_connections()
        
        # Call parent stop
        await super().stop()
        
        self.logger.info("Shutdown complete")
    
    async def _close_connections(self):
        """Close all connections gracefully"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            if self.db_pool:
                await self.db_pool.close()
            
            self.logger.info("Connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing connections: {e}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import os
    
    async def main():
        config = AgentConfig(
            name="optimizing-engine",
            agent_type="optimization",
            capabilities=[
                "performance_optimization",
                "resource_allocation",
                "cache_optimization",
                "database_optimization",
                "predictive_optimization",
                "parameter_tuning",
                "auto_scaling"
            ],
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL", "redis://redis:6379")
        )
        
        engine = OptimizingEngine(config)
        
        if await engine.start():
            # Set start time
            engine.start_time = time.time()
            
            # Wait for shutdown
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
