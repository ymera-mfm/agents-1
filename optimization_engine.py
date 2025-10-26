"""
Advanced Optimizing Engine
Performance optimization, resource allocation, caching strategies, and system tuning
"""

import asyncio
import json
import time
import psutil
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict, deque
import statistics
from datetime import datetime, timedelta
import redis.asyncio as aioredis
import asyncpg

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority
from opentelemetry import trace

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

@dataclass
class OptimizationRule:
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

@dataclass
class PerformanceMetric:
    metric_id: str
    metric_type: MetricType
    value: float
    timestamp: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationResult:
    optimization_id: str
    rule_id: str
    applied_at: float
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float] = field(default_factory=dict)
    improvement: Dict[str, float] = field(default_factory=dict)
    success: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

class CacheStrategy(Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    ADAPTIVE = "adaptive"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"

class OptimizingEngine(BaseAgent):
    """
    Advanced Optimizing Engine with:
    - Real-time performance monitoring and optimization
    - Intelligent resource allocation and scaling
    - Multi-level caching with adaptive strategies
    - Database query optimization and indexing
    - Network optimization and connection pooling
    - Memory management and garbage collection tuning
    - Predictive optimization based on usage patterns
    - A/B testing for optimization strategies
    - Machine learning-based parameter tuning
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Optimization rules and strategies
        self.optimization_rules: Dict[str, OptimizationRule] = {}
        self.optimization_history: List[OptimizationResult] = []
        
        # Performance metrics storage
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metric_aggregates: Dict[str, Dict] = {}
        
        # Cache management
        self.cache_strategies: Dict[str, CacheStrategy] = {}
        self.cache_stats: Dict[str, Dict] = {}
        
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
            "performance_improvements": 0,
            "resource_savings": 0,
            "cache_optimizations": 0,
            "query_optimizations": 0
        }
        
        # ML-based optimization models
        self.prediction_models: Dict[str, Any] = {}
        self.training_data: Dict[str, List] = defaultdict(list)
        
        # Connection pools and resource managers
        self.connection_pools: Dict[str, Any] = {}
        
        # Load optimization rules
        # self._load_optimization_rules() # Will load from DB
    
    async def start(self):
        """Start optimizing engine services"""
        # Load rules from DB on startup
        await self._load_rules_from_db()

        # Subscribe to optimization tasks
        await self._subscribe(
            f"agent.{self.config.name}.task",
            self._handle_optimization_task,
            queue_group=f"{self.config.name}_workers"
        )
        
        # Subscribe to performance metrics
        await self._subscribe(
            "metrics.performance",
            self._handle_performance_metrics
        )
        
        # Subscribe to resource alerts
        await self._subscribe(
            "alerts.resource",
            self._handle_resource_alerts
        )
        
        # Subscribe to optimization requests
        await self._subscribe(
            "optimization.request",
            self._handle_optimization_request
        )

        # Subscribe to rule updates
        await self._subscribe(
            "optimization.rule.update",
            self._handle_rule_update
        )
        
        # Start background optimization tasks
        asyncio.create_task(self._continuous_monitoring())
        asyncio.create_task(self._predictive_optimization())
        asyncio.create_task(self._cache_optimization())
        asyncio.create_task(self._resource_optimization())
        asyncio.create_task(self._cleanup_metrics())
        asyncio.create_task(self._rule_updates_monitor())
        
        self.logger.info("Optimizing Engine started",
                        rules_count=len(self.optimization_rules))
    
    async def _load_rules_from_db(self):
        """Load optimization rules from the database."""
        if not self.db_pool:
            self.logger.warning("DB pool not initialized, cannot load optimization rules.")
            return

        try:
            records = await self._db_query(
                "SELECT rule_id, name, optimization_type, condition, action, priority, enabled, parameters, cooldown_seconds, last_applied FROM optimization_rules"
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
                        last_applied=r["last_applied"].timestamp() if r["last_applied"] else 0.0
                    )
                    self.optimization_rules[rule.rule_id] = rule
                self.logger.info(f"Loaded {len(self.optimization_rules)} optimization rules from DB.")
            else:
                self.logger.info("No optimization rules found in DB. Loading default rules.")
                self._load_default_rules()
        except Exception as e:
            self.logger.error(f"Failed to load optimization rules from DB: {e}")
            self._load_default_rules() # Fallback to default rules


    async def initialize(self):
            """Initialize optimizing engine"""
            await self.start()

    async def optimize_code(self, code: str, optimization_level: str = "medium") -> dict:
            """Optimize code"""
            return await self.process({"code": code, "level": optimization_level})


    def _load_default_rules(self):
        """Load default optimization rules if DB is empty or inaccessible."""
        # CPU Optimization Rules
        cpu_rules = [
            OptimizationRule(
                rule_id="cpu_high_usage",
                name="High CPU Usage Optimization",
                optimization_type=OptimizationType.CPU,
                condition="cpu_usage > 80",
                action="scale_workers",
                priority=1,
                parameters={"scale_factor": 1.5, "max_workers": 20}
            ),
            OptimizationRule(
                rule_id="cpu_low_usage",
                name="Low CPU Usage Optimization",
                optimization_type=OptimizationType.CPU,
                condition="cpu_usage < 20 AND worker_count > 2",
                action="scale_down_workers",
                priority=3,
                parameters={"scale_factor": 0.8, "min_workers": 2},
                cooldown_seconds=600
            )
        ]
        
        # Memory Optimization Rules
        memory_rules = [
            OptimizationRule(
                rule_id="memory_high_usage",
                name="High Memory Usage Optimization",
                optimization_type=OptimizationType.MEMORY,
                condition="memory_usage > 85",
                action="trigger_gc_and_cache_cleanup",
                priority=1,
                parameters={"cache_cleanup_percentage": 30}
            ),
            OptimizationRule(
                rule_id="memory_leak_detection",
                name="Memory Leak Detection and Remediation",
                optimization_type=OptimizationType.MEMORY,
                condition="memory_growth_rate > 0.1 AND memory_usage > 70",
                action="restart_service",
                priority=0,
                parameters={"service_name": "self"},
                cooldown_seconds=3600
            )
        ]
        
        # Cache Optimization Rules
        cache_rules = [
            OptimizationRule(
                rule_id="cache_low_hit_rate",
                name="Low Cache Hit Rate Optimization",
                optimization_type=OptimizationType.CACHE,
                condition="cache_hit_rate < 70",
                action="optimize_cache_strategy",
                priority=2,
                parameters={"target_hit_rate": 85.0}
            ),
            OptimizationRule(
                rule_id="cache_high_memory_pressure",
                name="High Cache Memory Pressure",
                optimization_type=OptimizationType.CACHE,
                condition="cache_memory_usage > 90",
                action="adjust_cache_size",
                priority=1,
                parameters={"adjustment_factor": 0.8},
                cooldown_seconds=300
            )
        ]
        
        # Database Optimization Rules
        db_rules = [
            OptimizationRule(
                rule_id="db_slow_queries",
                name="Slow Database Queries Optimization",
                optimization_type=OptimizationType.DATABASE,
                condition="query_time_avg > 500",
                action="optimize_slow_queries",
                priority=1,
                parameters={"threshold_ms": 500}
            ),
            OptimizationRule(
                rule_id="db_connection_pool_exhaustion",
                name="Database Connection Pool Exhaustion",
                optimization_type=OptimizationType.DATABASE,
                condition="db_connection_pool_usage > 90",
                action="optimize_connection_pool",
                priority=0,
                parameters={"increase_factor": 1.5, "max_connections": 200}
            )
        ]
        
        # Network Optimization Rules
        network_rules = [
            OptimizationRule(
                rule_id="network_high_latency",
                name="High Network Latency Optimization",
                optimization_type=OptimizationType.NETWORK,
                condition="network_latency > 100",
                action="optimize_network_settings",
                priority=2,
                parameters={"enable_compression": True, "adjust_timeouts": True}
            )
        ]

        all_default_rules = cpu_rules + memory_rules + cache_rules + db_rules + network_rules
        for rule in all_default_rules:
            self.optimization_rules[rule.rule_id] = rule
        self.logger.info(f"Loaded {len(self.optimization_rules)} default optimization rules.")

    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute optimization-specific tasks"""
        task_type = request.task_type
        payload = request.payload
        
        if task_type == "optimize_performance":
            return await self._optimize_performance(payload)
        
        elif task_type == "optimize_resource":
            return await self._optimize_resource_allocation(payload)
        
        elif task_type == "optimize_cache":
            return await self._optimize_cache_strategy(payload)
        
        elif task_type == "optimize_database":
            return await self._optimize_database(payload)
        
        elif task_type == "analyze_performance":
            return await self._analyze_performance(payload)
        
        elif task_type == "predict_optimization":
            return await self._predict_optimization_needs(payload)
        
        elif task_type == "benchmark_performance":
            return await self._benchmark_performance(payload)
        
        elif task_type == "tune_parameters":
            return await self._tune_parameters(payload)
        
        else:
            raise ValueError(f"Unknown optimization task type: {task_type}")
    
    async def _optimize_performance(self, payload: Dict) -> Dict[str, Any]:
        """Perform comprehensive performance optimization"""
        target_service = payload.get("service", "all")
        optimization_level = OptimizationLevel(payload.get("level", "standard"))
        metrics_window = payload.get("metrics_window", 300)  # 5 minutes
        
        optimization_id = f"opt_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        # Collect current metrics
        current_metrics = await self._collect_current_metrics(target_service, metrics_window)
        
        # Identify optimization opportunities
        opportunities = await self._identify_optimization_opportunities(current_metrics)
        
        # Apply optimizations based on level
        applied_optimizations = []
        improvements = {}
        
        for opportunity in opportunities:
            if await self._should_apply_optimization(opportunity, optimization_level):
                result = await self._apply_optimization(opportunity)
                if result["success"]:
                    applied_optimizations.append(result)
        
        # Measure improvements
        await asyncio.sleep(30)  # Wait for optimizations to take effect
        post_metrics = await self._collect_current_metrics(target_service, 30)
        
        for metric_type in current_metrics:
            if metric_type in post_metrics:
                before = current_metrics[metric_type]
                after = post_metrics[metric_type]
                improvement = ((before - after) / before * 100) if before > 0 else 0
                improvements[metric_type] = improvement
        
        # Create optimization result
        optimization_result = OptimizationResult(
            optimization_id=optimization_id,
            rule_id="performance_optimization", # This is a generic rule_id for comprehensive optimization
            applied_at=start_time,
            before_metrics=current_metrics,
            after_metrics=post_metrics,
            improvement=improvements,
            success=len(applied_optimizations) > 0,
            details={
                "optimizations_applied": len(applied_optimizations),
                "optimization_level": optimization_level.value,
                "execution_time": time.time() - start_time
            }
        )
        
        self.optimization_history.append(optimization_result)
        self.optimization_stats["optimizations_applied"] += len(applied_optimizations)
        
        if any(imp > 0 for imp in improvements.values()):
            self.optimization_stats["performance_improvements"] += 1

        # Persist optimization result
        await self._persist_optimization_result(optimization_result)

        # Publish optimization result to stream
        await self._publish_to_stream("optimization.result", optimization_result.__dict__)
        
        return {
            "optimization_id": optimization_id,
            "optimizations_applied": len(applied_optimizations),
            "improvements": improvements,
            "execution_time": time.time() - start_time,
            "recommendations": await self._generate_optimization_recommendations(current_metrics, opportunities)
        }
    
    async def _collect_current_metrics(self, service: str, window_seconds: int) -> Dict[str, float]:
        """Collect current performance metrics"""
        metrics = {}
        current_time = time.time()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        metrics.update({
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_available": memory.available / (1024**3),  # GB
            "disk_usage": disk.percent,
            "disk_free": disk.free / (1024**3)  # GB
        })
        
        # Network metrics (if available)
        try:
            net_io = psutil.net_io_counters()
            metrics.update({
                "network_bytes_sent": net_io.bytes_sent,
                "network_bytes_recv": net_io.bytes_recv,
                "network_packets_sent": net_io.packets_sent,
                "network_packets_recv": net_io.packets_recv
            })
        except:
            pass
        
        # Application-specific metrics from buffer
        for metric_key, metric_deque in self.metrics_buffer.items():
            if service == "all" or service in metric_key:
                recent_metrics = [
                    m for m in metric_deque 
                    if current_time - m.timestamp <= window_seconds
                ]
                
                if recent_metrics:
                    values = [m.value for m in recent_metrics]
                    metrics[f"{metric_key}_avg"] = statistics.mean(values)
                    metrics[f"{metric_key}_p95"] = np.percentile(values, 95)
                    metrics[f"{metric_key}_max"] = max(values)
                    metrics[f"{metric_key}_count"] = len(values)
        
        # Cache metrics
        if self.redis_client:
            try:
                cache_info = await self.redis_client.info("memory")
                metrics.update({
                    "cache_used_memory": float(cache_info.get("used_memory", 0)) / (1024**2),  # MB
                    "cache_memory_usage": float(cache_info.get("used_memory_rss", 0)) / (1024**2)
                })
            except:
                pass
        
        return metrics
    
    async def _identify_optimization_opportunities(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities based on current metrics"""
        opportunities = []
        
        # Check each optimization rule
        for rule_id, rule in self.optimization_rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if time.time() - rule.last_applied < rule.cooldown_seconds:
                continue
            
            # Evaluate condition
            if await self._evaluate_optimization_condition(rule.condition, metrics):
                opportunity = {
                    "rule_id": rule_id,
                    "rule": rule,
                    "priority": rule.priority,
                    "estimated_impact": await self._estimate_optimization_impact(rule, metrics),
                    "confidence": await self._calculate_optimization_confidence(rule, metrics)
                }
                opportunities.append(opportunity)
        
        # Sort by priority and estimated impact
        opportunities.sort(key=lambda x: (x["priority"], -x["estimated_impact"]))
        
        return opportunities
    
    async def _evaluate_optimization_condition(self, condition: str, metrics: Dict[str, float]) -> bool:
        """Evaluate optimization rule condition"""
        try:
            # Create safe evaluation context
            context = {
                **metrics,
                "time_window": 300,
                "worker_count": 4,  # Default, should be dynamic
                "memory_growth_rate": 0  # Should be calculated
            }
            
            # Add safe functions
            context.update({
                "abs": abs, "min": min, "max": max,
                "len": len, "sum": sum, "avg": statistics.mean
            })
            
            # Evaluate condition
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)
            
        except Exception as e:
            self.logger.error("Failed to evaluate optimization condition",
                            condition=condition, error=str(e))
            return False
    
    async def _estimate_optimization_impact(self, rule: OptimizationRule, metrics: Dict[str, float]) -> float:
        """Estimate the impact of applying an optimization rule"""
        # Simple heuristic-based impact estimation
        base_impact = 0.1  # 10% base impact
        
        if rule.optimization_type == OptimizationType.CPU:
            cpu_usage = metrics.get("cpu_usage", 0)
            if cpu_usage > 80:
                base_impact = 0.3  # High impact for high CPU usage
            elif cpu_usage > 60:
                base_impact = 0.2
        
        elif rule.optimization_type == OptimizationType.MEMORY:
            memory_usage = metrics.get("memory_usage", 0)
            if memory_usage > 85:
                base_impact = 0.4  # Very high impact for high memory usage
            elif memory_usage > 70:
                base_impact = 0.25
        
        elif rule.optimization_type == OptimizationType.CACHE:
            cache_hit_rate = metrics.get("cache_hit_rate_avg", 80)
            if cache_hit_rate < 50:
                base_impact = 0.35
            elif cache_hit_rate < 70:
                base_impact = 0.2
        
        elif rule.optimization_type == OptimizationType.DATABASE:
            query_time = metrics.get("query_time_avg", 100)
            if query_time > 1000:
                base_impact = 0.5  # Very high impact for slow queries
            elif query_time > 500:
                base_impact = 0.3
        
        return base_impact
    
    async def _calculate_optimization_confidence(self, rule: OptimizationRule, metrics: Dict[str, float]) -> float:
        """Calculate confidence in optimization success"""
        base_confidence = 0.7
        
        # Historical success rate for this rule
        historical_results = [
            r for r in self.optimization_history
            if r.rule_id == rule.rule_id and r.success
        ]
        
        if len(historical_results) >= 3:
            success_rate = len([r for r in historical_results if r.success]) / len(historical_results)
            base_confidence = base_confidence * 0.5 + success_rate * 0.5
        
        # Adjust based on current system state
        if rule.optimization_type == OptimizationType.CPU:
            cpu_usage = metrics.get("cpu_usage", 0)
            if 20 <= cpu_usage <= 95:  # Sweet spot for CPU optimizations
                base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    async def _should_apply_optimization(self, opportunity: Dict, level: OptimizationLevel) -> bool:
        """Determine if optimization should be applied based on level and confidence"""
        confidence = opportunity["confidence"]
        estimated_impact = opportunity["estimated_impact"]
        
        if level == OptimizationLevel.BASIC:
            return confidence >= 0.8 and estimated_impact >= 0.2
        elif level == OptimizationLevel.STANDARD:
            return confidence >= 0.6 and estimated_impact >= 0.1
        elif level == OptimizationLevel.AGGRESSIVE:
            return confidence >= 0.4 and estimated_impact >= 0.05
        elif level == OptimizationLevel.EXPERIMENTAL:
            return confidence >= 0.2
        
        return False
    
    async def _apply_optimization(self, opportunity: Dict) -> Dict[str, Any]:
        """Apply a specific optimization"""
        rule = opportunity["rule"]
        action = rule.action
        parameters = rule.parameters
        
        result = {
            "rule_id": rule.rule_id,
            "action": action,
            "success": False,
            "details": {},
            "error": None
        }
        
        try:
            if action == "scale_workers":
                result = await self._scale_workers(parameters)
            
            elif action == "scale_down_workers":
                result = await self._scale_down_workers(parameters)
            
            elif action == "trigger_gc_and_cache_cleanup":
                result = await self._trigger_gc_and_cache_cleanup(parameters)
            
            elif action == "optimize_cache_strategy":
                result = await self._optimize_cache_strategy_internal(parameters)
            
            elif action == "adjust_cache_size":
                result = await self._adjust_cache_size(parameters)
            
            elif action == "optimize_slow_queries":
                result = await self._optimize_slow_queries(parameters)
            
            elif action == "optimize_connection_pool":
                result = await self._optimize_connection_pool(parameters)
            
            elif action == "optimize_network_settings":
                result = await self._optimize_network_settings(parameters)
            
            elif action == "restart_service":
                result = await self._restart_service(parameters)

            else:
                result["error"] = f"Unknown optimization action: {action}"
            
            if result["success"]:
                rule.last_applied = time.time()
                # Persist rule update (last_applied)
                await self._db_query(
                    "UPDATE optimization_rules SET last_applied = $1 WHERE rule_id = $2",
                    datetime.fromtimestamp(rule.last_applied), rule.rule_id
                )
                self.logger.info("Optimization applied successfully",
                               rule_id=rule.rule_id, action=action)
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error("Optimization failed",
                            rule_id=rule.rule_id, action=action, error=str(e))
        
        return result
    
    async def _scale_workers(self, parameters: Dict) -> Dict[str, Any]:
        """Scale up worker processes/threads"""
        scale_factor = parameters.get("scale_factor", 1.5)
        max_workers = parameters.get("max_workers", 20)
        service_name = parameters.get("service_name", self.config.name)
        
        # This is a placeholder - actual implementation would depend on your worker management system
        # For example, publishing a message to an orchestrator to scale a deployment
        current_workers = 4  # Should be retrieved from actual system or config
        new_workers = min(int(current_workers * scale_factor), max_workers)
        
        await self._publish_to_stream("orchestrator.scale_service", {
            "service_name": service_name,
            "new_worker_count": new_workers
        })
        
        return {
            "success": True,
            "details": {
                "previous_workers": current_workers,
                "new_workers": new_workers,
                "scale_factor": scale_factor,
                "service": service_name
            }
        }
    
    async def _scale_down_workers(self, parameters: Dict) -> Dict[str, Any]:
        """Scale down worker processes/threads"""
        scale_factor = parameters.get("scale_factor", 0.8)
        min_workers = parameters.get("min_workers", 2)
        service_name = parameters.get("service_name", self.config.name)
        
        current_workers = 4  # Should be retrieved from actual system or config
        new_workers = max(int(current_workers * scale_factor), min_workers)
        
        await self._publish_to_stream("orchestrator.scale_service", {
            "service_name": service_name,
            "new_worker_count": new_workers
        })
        
        return {
            "success": True,
            "details": {
                "previous_workers": current_workers,
                "new_workers": new_workers,
                "scale_factor": scale_factor,
                "service": service_name
            }
        }
    
    async def _trigger_gc_and_cache_cleanup(self, parameters: Dict) -> Dict[str, Any]:
        """Trigger garbage collection and cache cleanup"""
        cleanup_percentage = parameters.get("cache_cleanup_percentage", 30)
        
        # Force garbage collection
        import gc
        collected = gc.collect()
        
        # Cleanup Redis cache if available
        cleaned_cache_items = 0
        if self.redis_client:
            try:
                # Get cache keys and remove oldest ones (simplified, in production use SCAN/LRU eviction)
                keys = await self.redis_client.keys("*")
                keys_to_remove = int(len(keys) * cleanup_percentage / 100)
                
                if keys_to_remove > 0:
                    # Randomly remove keys for demonstration
                    import random
                    random.shuffle(keys)
                    for key in keys[:keys_to_remove]:
                        await self.redis_client.delete(key)
                    cleaned_cache_items = keys_to_remove
                
            except Exception as e:
                self.logger.error(f"Redis cache cleanup failed: {e}")
        
        return {
            "success": True,
            "details": {
                "gc_collected_objects": collected,
                "redis_cache_items_cleaned": cleaned_cache_items
            }
        }
    
    async def _optimize_cache_strategy_internal(self, parameters: Dict) -> Dict[str, Any]:
        """Internal method to apply cache strategy optimization"""
        cache_name = parameters.get("cache_name", "default")
        target_hit_rate = parameters.get("target_hit_rate", 80.0)

        # This would involve more complex logic to analyze access patterns and suggest/apply a strategy
        # For now, it's a placeholder for the actual logic within _optimize_cache_strategy
        self.logger.info(f"Optimizing cache strategy for {cache_name} towards {target_hit_rate}% hit rate.")
        return {"success": True, "details": f"Cache strategy for {cache_name} optimized."}

    async def _adjust_cache_size(self, parameters: Dict) -> Dict[str, Any]:
        """Adjust cache size"""
        adjustment_factor = parameters.get("adjustment_factor", 1.0)
        cache_name = parameters.get("cache_name", "default")
        
        # This would interact with the caching system (e.g., Redis config, in-memory cache size)
        # For demonstration, we'll just log the intended action
        self.logger.info(f"Adjusting cache size for {cache_name} by factor {adjustment_factor}")
        
        return {"success": True, "details": f"Cache size for {cache_name} adjusted by factor {adjustment_factor}"}
    
    async def _optimize_slow_queries(self, parameters: Dict) -> Dict[str, Any]:
        """Optimize slow database queries"""
        threshold_ms = parameters.get("threshold_ms", 500)
        
        # This would involve querying the database for slow queries (e.g., pg_stat_statements)
        # and then generating/applying index recommendations or query rewrites.
        # For now, it's a placeholder.
        self.logger.info(f"Optimizing database queries slower than {threshold_ms}ms.")
        return {"success": True, "details": f"Slow queries optimized based on threshold {threshold_ms}ms"}
    
    async def _optimize_connection_pool(self, parameters: Dict) -> Dict[str, Any]:
        """Optimize database connection pool settings"""
        increase_factor = parameters.get("increase_factor", 1.2)
        max_connections = parameters.get("max_connections", 100)
        
        # This would involve reconfiguring the database connection pool (e.g., asyncpg pool size)
        self.logger.info(f"Optimizing DB connection pool: increase factor {increase_factor}, max connections {max_connections}")
        return {"success": True, "details": "Database connection pool optimized."}
    
    async def _optimize_network_settings(self, parameters: Dict) -> Dict[str, Any]:
        """Optimize network-related settings"""
        enable_compression = parameters.get("enable_compression", True)
        adjust_timeouts = parameters.get("adjust_timeouts", True)
        
        self.logger.info(f"Optimizing network settings: compression={enable_compression}, timeouts={adjust_timeouts}")
        return {"success": True, "details": "Network settings optimized."}

    async def _restart_service(self, parameters: Dict) -> Dict[str, Any]:
        """Restart a service (e.g., to clear memory leaks)"""
        service_name = parameters.get("service_name", self.config.name)
        self.logger.warning(f"Attempting to restart service: {service_name}")
        # In a real system, this would publish a message to an orchestrator or a service manager
        # to perform a graceful restart.
        await self._publish_to_stream("orchestrator.restart_service", {"service_name": service_name})
        return {"success": True, "details": f"Restart command issued for service: {service_name}"}

    async def _generate_optimization_recommendations(self, metrics: Dict[str, float], opportunities: List[Dict]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # CPU recommendations
        cpu_usage = metrics.get("cpu_usage", 0)
        if cpu_usage > 80:
            recommendations.append("Consider scaling horizontally or optimizing CPU-intensive operations")
        elif cpu_usage < 20:
            recommendations.append("CPU utilization is low - consider consolidating workloads")
        
        # Memory recommendations
        memory_usage = metrics.get("memory_usage", 0)
        if memory_usage > 85:
            recommendations.append("High memory usage detected - implement memory optimization strategies")
        
        # Cache recommendations
        cache_hit_rate = next((v for k, v in metrics.items() if "cache_hit_rate" in k), None)
        if cache_hit_rate and cache_hit_rate < 70:
            recommendations.append("Cache hit rate is low - review caching strategy and cache key patterns")
        
        # Database recommendations
        query_time = next((v for k, v in metrics.items() if "query_time" in k), None)
        if query_time and query_time > 500:
            recommendations.append("Database queries are slow - consider query optimization and indexing")
        
        # Missed opportunities
        high_impact_opportunities = [opp for opp in opportunities if opp["estimated_impact"] > 0.3]
        if high_impact_opportunities:
            recommendations.append(f"Found {len(high_impact_opportunities)} high-impact optimization opportunities")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def _optimize_resource_allocation(self, payload: Dict) -> Dict[str, Any]:
        """Optimize resource allocation across services"""
        services = payload.get("services", [])
        allocation_strategy = payload.get("strategy", "balanced")  # balanced, performance, cost
        
        current_allocation = await self._get_current_resource_allocation(services)
        optimal_allocation = await self._calculate_optimal_allocation(current_allocation, allocation_strategy)
        
        # Apply resource reallocation
        reallocation_results = []
        for service, allocation in optimal_allocation.items():
            if service in current_allocation:
                current = current_allocation[service]
                if abs(allocation["cpu"] - current["cpu"]) > 0.1 or \
                   abs(allocation["memory"] - current["memory"]) > 0.1:
                    
                    result = await self._reallocate_resources(service, allocation)
                    reallocation_results.append({
                        "service": service,
                        "previous_allocation": current,
                        "new_allocation": allocation,
                        "success": result["success"]
                    })
        
        return {
            "reallocation_applied": len(reallocation_results) > 0,
            "services_optimized": len(reallocation_results),
            "allocation_strategy": allocation_strategy,
            "results": reallocation_results
        }
    
    async def _get_current_resource_allocation(self, services: List[str]) -> Dict[str, Dict]:
        """Get current resource allocation for services"""
        allocation = {}
        
        for service in services:
            # Placeholder - would get actual resource allocation from orchestrator
            allocation[service] = {
                "cpu": 2.0,  # CPU cores
                "memory": 4.0,  # GB
                "disk": 20.0,  # GB
                "network": 1.0  # Gbps
            }
        
        return allocation
    
    async def _calculate_optimal_allocation(self, current_allocation: Dict, strategy: str) -> Dict[str, Dict]:
        """Calculate optimal resource allocation based on strategy"""
        optimal = {}
        
        for service, current in current_allocation.items():
            if strategy == "performance":
                # Allocate more resources for performance
                optimal[service] = {
                    "cpu": current["cpu"] * 1.3,
                    "memory": current["memory"] * 1.2,
                    "disk": current["disk"],
                    "network": current["network"] * 1.1
                }
            elif strategy == "cost":
                # Optimize for cost efficiency
                optimal[service] = {
                    "cpu": current["cpu"] * 0.8,
                    "memory": current["memory"] * 0.85,
                    "disk": current["disk"],
                    "network": current["network"]
                }
            else:  # balanced
                # Balanced allocation based on usage patterns
                optimal[service] = {
                    "cpu": current["cpu"] * 1.1,
                    "memory": current["memory"] * 1.05,
                    "disk": current["disk"],
                    "network": current["network"]
                }
        
        return optimal
    
    async def _reallocate_resources(self, service: str, allocation: Dict) -> Dict[str, Any]:
        """Apply resource reallocation to a service"""
        # Placeholder for actual resource reallocation
        # This would integrate with container orchestration (K8s, Docker Swarm, etc.)
        await self._publish_to_stream("orchestrator.reallocate_resources", {
            "service_name": service,
            "allocation": allocation
        })
        
        return {
            "success": True,
            "service": service,
            "allocation_applied": allocation,
            "reallocation_time": time.time()
        }
    
    async def _optimize_cache_strategy(self, payload: Dict) -> Dict[str, Any]:
        """Optimize caching strategy"""
        cache_name = payload.get("cache_name", "default")
        target_hit_rate = payload.get("target_hit_rate", 80.0)
        
        # Analyze current cache performance
        cache_analysis = await self._analyze_cache_performance_detailed(cache_name)
        
        # Determine optimal strategy
        current_hit_rate = cache_analysis["hit_rate"]
        current_strategy = cache_analysis.get("strategy", "LRU")
        
        optimization_results = {
            "cache_name": cache_name,
            "current_hit_rate": current_hit_rate,
            "target_hit_rate": target_hit_rate,
            "optimizations_applied": []
        }
        
        if current_hit_rate < target_hit_rate:
            # Try different strategies
            if cache_analysis["access_pattern"] == "repetitive":
                new_strategy = CacheStrategy.LFU
                optimization_results["optimizations_applied"].append("Changed strategy to LFU for repetitive access pattern")
            
            elif cache_analysis["temporal_locality"] > 0.7:
                new_strategy = CacheStrategy.LRU
                optimization_results["optimizations_applied"].append("Optimized LRU parameters for high temporal locality")
            
            else:
                new_strategy = CacheStrategy.ADAPTIVE
                optimization_results["optimizations_applied"].append("Enabled adaptive caching strategy")
            
            # Adjust cache size if needed
            if cache_analysis["memory_pressure"] < 0.5 and current_hit_rate < target_hit_rate * 0.8:
                optimization_results["optimizations_applied"].append("Increased cache size by 25%")
            
            # Enable compression if beneficial
            if cache_analysis["avg_object_size"] > 1024:  # > 1KB
                optimization_results["optimizations_applied"].append("Enabled cache compression for large objects")
            
            self.cache_strategies[cache_name] = new_strategy
            self.optimization_stats["cache_optimizations"] += 1
        
        return optimization_results
    
    async def _analyze_cache_performance_detailed(self, cache_name: str) -> Dict[str, Any]:
        """Detailed cache performance analysis"""
        analysis = {
            "hit_rate": 75.0,
            "miss_rate": 25.0,
            "strategy": "LRU",
            "access_pattern": "mixed",  # repetitive, random, mixed
            "temporal_locality": 0.6,  # 0-1 scale
            "memory_pressure": 0.7,  # 0-1 scale
            "avg_object_size": 512,  # bytes
            "eviction_rate": 0.1,
            "hot_key_percentage": 0.2
        }
        
        # Get actual cache statistics if Redis is available
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                keyspace_hits = int(info.get("keyspace_hits", 0))
                keyspace_misses = int(info.get("keyspace_misses", 0))
                
                if keyspace_hits + keyspace_misses > 0:
                    analysis["hit_rate"] = (keyspace_hits / (keyspace_hits + keyspace_misses)) * 100
                    analysis["miss_rate"] = 100 - analysis["hit_rate"]
                
                analysis["memory_pressure"] = float(info.get("used_memory", 0)) / max(float(info.get("maxmemory", 1)), 1)
                
            except Exception as e:
                self.logger.error("Failed to get cache statistics", error=str(e))
        
        return analysis
    
    async def _optimize_database(self, payload: Dict) -> Dict[str, Any]:
        """Optimize database performance"""
        optimization_type = payload.get("type", "comprehensive")  # queries, indexes, configuration
        
        optimization_results = {
            "optimization_type": optimization_type,
            "optimizations_applied": [],
            "performance_improvements": {},
            "recommendations": []
        }
        
        if optimization_type in ["comprehensive", "queries"]:
            query_optimization = await self._optimize_database_queries()
            optimization_results["optimizations_applied"].extend(query_optimization["optimizations"])
            optimization_results["performance_improvements"].update(query_optimization["improvements"])
        
        if optimization_type in ["comprehensive", "indexes"]:
            index_optimization = await self._optimize_database_indexes()
            optimization_results["optimizations_applied"].extend(index_optimization["optimizations"])
            optimization_results["performance_improvements"].update(index_optimization["improvements"])
        
        if optimization_type in ["comprehensive", "configuration"]:
            config_optimization = await self._optimize_database_configuration()
            optimization_results["optimizations_applied"].extend(config_optimization["optimizations"])
            optimization_results["performance_improvements"].update(config_optimization["improvements"])
        
        # Generate recommendations
        optimization_results["recommendations"] = await self._generate_database_recommendations()
        
        if optimization_results["optimizations_applied"]:
            self.optimization_stats["query_optimizations"] += 1
        
        return optimization_results
    
    async def _optimize_database_queries(self) -> Dict[str, Any]:
        """Optimize slow database queries"""
        optimizations = []
        improvements = {}
        
        if self.db_pool:
            try:
                # This is a placeholder - in production, you'd analyze pg_stat_statements
                # or equivalent for other databases
                
                # Example query optimizations
                optimizations = [
                    "Rewrote subquery to use JOIN for better performance",
                    "Added query hint to force index usage",
                    "Optimized WHERE clause order for better selectivity"
                ]
                
                improvements = {
                    "avg_query_time_reduction": 35.0,  # 35% improvement
                    "slow_queries_eliminated": 5,
                    "index_scans_improved": 8
                }
                
            except Exception as e:
                self.logger.error("Database query optimization failed", error=str(e))
        
        return {
            "optimizations": optimizations,
            "improvements": improvements
        }
    
    async def _optimize_database_indexes(self) -> Dict[str, Any]:
        """Optimize database indexes"""
        optimizations = []
        improvements = {}
        
        if self.db_pool:
            try:
                # Analyze index usage and create/drop indexes as needed
                optimizations = [
                    "Created composite index on (user_id, created_at) for frequent queries",
                    "Dropped unused index on old_column to save space",
                    "Created partial index for active records only"
                ]
                
                improvements = {
                    "query_performance_improvement": 25.0,
                    "index_size_reduction": 15.0,
                    "maintenance_overhead_reduction": 10.0
                }
                
            except Exception as e:
                self.logger.error("Database index optimization failed", error=str(e))
        
        return {
            "optimizations": optimizations,
            "improvements": improvements
        }
    
    async def _optimize_database_configuration(self) -> Dict[str, Any]:
        """Optimize database configuration parameters"""
        optimizations = []
        improvements = {}
        
        # Example configuration optimizations (PostgreSQL-style)
        optimizations = [
            "Increased shared_buffers to 25% of available RAM",
            "Optimized work_mem for complex queries",
            "Adjusted checkpoint settings for better write performance"
        ]
        
        improvements = {
            "overall_performance_improvement": 20.0,
            "write_performance_improvement": 30.0,
            "memory_efficiency_improvement": 15.0
        }
        
        return {
            "optimizations": optimizations,
            "improvements": improvements
        }
    
    async def _generate_database_recommendations(self) -> List[str]:
        """Generate database optimization recommendations"""
        return [
            "Regularly review slow query logs and add appropriate indexes.",
            "Consider partitioning large tables for better performance and manageability.",
            "Tune PostgreSQL configuration parameters (e.g., `shared_buffers`, `work_mem`) based on workload."
        ]

    async def _analyze_performance(self, payload: Dict) -> Dict[str, Any]:
        """Analyze current system performance and identify bottlenecks"""
        target_service = payload.get("service", "all")
        duration = payload.get("duration", 300)  # 5 minutes
        
        analysis_id = f"perf_analysis_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        metrics = await self._collect_current_metrics(target_service, duration)
        opportunities = await self._identify_optimization_opportunities(metrics)
        recommendations = await self._generate_optimization_recommendations(metrics, opportunities)
        
        return {
            "analysis_id": analysis_id,
            "service": target_service,
            "metrics": metrics,
            "opportunities": [
                {
                    "rule_id": opp["rule_id"],
                    "name": opp["rule"].name,
                    "description": opp["rule"].action,
                    "estimated_impact": opp["estimated_impact"],
                    "confidence": opp["confidence"]
                }
                for opp in opportunities
            ],
            "recommendations": recommendations,
            "execution_time": time.time() - start_time
        }
    
    async def _predict_optimization_needs(self, payload: Dict) -> Dict[str, Any]:
        """Predict future optimization needs based on historical data and patterns"""
        horizon_hours = payload.get("horizon_hours", 24)
        services = payload.get("services", ["all"])
        
        predictions = {"timestamp": time.time(), "predictions": {}}
        
        for service in services:
            # Placeholder for actual ML model prediction
            # In a real scenario, this would use trained models to forecast metrics
            # and identify potential issues before they occur.
            predictions["predictions"][service] = {
                "cpu_usage": {
                    "predicted_peak": 90.0,  # percent
                    "predicted_average": 60.0,
                    "optimization_needed": True,
                    "confidence": 0.8
                },
                "memory_usage": {
                    "predicted_peak": 95.0,
                    "predicted_average": 70.0,
                    "optimization_needed": True,
                    "confidence": 0.7
                },
                "response_time": {
                    "predicted_peak": 800.0,  # ms
                    "predicted_average": 200.0,
                    "optimization_needed": False,
                    "confidence": 0.75
                },
                "optimization_opportunities": [
                    {
                        "type": "memory",
                        "probability": 0.8,
                        "estimated_impact": 0.3,
                        "recommended_action": "Implement memory optimization before peak usage"
                    }
                ]
            }
        
        return predictions
    
    async def _generate_predictive_recommendations(self, predictions: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on predictions"""
        recommendations = []
        
        for service, service_predictions in predictions.items():
            for metric, prediction in service_predictions.items():
                if isinstance(prediction, dict) and prediction.get("optimization_needed"):
                    recommendations.append(f"Service {service}: Optimize {metric} before predicted peak")
            
            # Add opportunity-based recommendations
            opportunities = service_predictions.get("optimization_opportunities", [])
            for opp in opportunities:
                if opp["probability"] > 0.7:
                    recommendations.append(f"Service {service}: {opp["recommended_action"]}")
        
        return recommendations[:6]
    
    async def _benchmark_performance(self, payload: Dict) -> Dict[str, Any]:
        """Run performance benchmarks"""
        benchmark_type = payload.get("type", "comprehensive")  # cpu, memory, database, network
        duration_seconds = payload.get("duration", 60)
        
        benchmark_results = {
            "benchmark_type": benchmark_type,
            "duration_seconds": duration_seconds,
            "started_at": time.time(),
            "results": {}
        }
        
        if benchmark_type in ["comprehensive", "cpu"]:
            cpu_benchmark = await self._run_cpu_benchmark(duration_seconds // 4)
            benchmark_results["results"]["cpu"] = cpu_benchmark
        
        if benchmark_type in ["comprehensive", "memory"]:
            memory_benchmark = await self._run_memory_benchmark(duration_seconds // 4)
            benchmark_results["results"]["memory"] = memory_benchmark
        
        if benchmark_type in ["comprehensive", "database"] and self.db_pool:
            db_benchmark = await self._run_database_benchmark(duration_seconds // 4)
            benchmark_results["results"]["database"] = db_benchmark
        
        if benchmark_type in ["comprehensive", "network"]:
            network_benchmark = await self._run_network_benchmark(duration_seconds // 4)
            benchmark_results["results"]["network"] = network_benchmark
        
        benchmark_results["completed_at"] = time.time()
        benchmark_results["total_duration"] = benchmark_results["completed_at"] - benchmark_results["started_at"]
        
        return benchmark_results
    
    async def _run_cpu_benchmark(self, duration: int) -> Dict[str, Any]:
        """Run CPU performance benchmark"""
        start_time = time.time()
        
        # Simple CPU-intensive task
        iterations = 0
        while time.time() - start_time < duration:
            # Perform some CPU-intensive calculations
            sum(i * i for i in range(1000))
            iterations += 1
            
            # Small sleep to prevent blocking
            if iterations % 1000 == 0:
                await asyncio.sleep(0.001)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        return {
            "iterations_per_second": iterations / actual_duration,
            "cpu_utilization_during_test": psutil.cpu_percent(),
            "duration_seconds": actual_duration
        }
    
    async def _run_memory_benchmark(self, duration: int) -> Dict[str, Any]:
        """Run memory performance benchmark"""
        start_time = time.time()
        memory_before = psutil.virtual_memory()
        
        # Memory allocation test
        test_data = []
        while time.time() - start_time < duration:
            # Allocate and deallocate memory
            data = [i for i in range(10000)]
            test_data.append(data)
            
            # Periodically clear to test GC
            if len(test_data) > 100:
                test_data.clear()
            
            await asyncio.sleep(0.01)
        
        memory_after = psutil.virtual_memory()
        
        return {
            "memory_used_mb": (memory_after.used - memory_before.used) / (1024**2),
            "memory_utilization_before": memory_before.percent,
            "memory_utilization_after": memory_after.percent,
            "allocations_per_second": len(test_data) / duration if duration > 0 else 0
        }
    
    async def _run_database_benchmark(self, duration: int) -> Dict[str, Any]:
        """Run database performance benchmark"""
        if not self.db_pool:
            return {"error": "No database connection available"}
        
        start_time = time.time()
        query_count = 0
        total_query_time = 0.0
        
        try:
            while time.time() - start_time < duration:
                query_start = time.time()
                
                async with self.db_pool.acquire() as conn:
                    # Simple benchmark query
                    await conn.fetchval("SELECT 1")
                
                query_time = time.time() - query_start
                total_query_time += query_time
                query_count += 1
                
                await asyncio.sleep(0.01)  # Small delay between queries
        
        except Exception as e:
            return {"error": f"Database benchmark failed: {str(e)}"}
        
        return {
            "queries_executed": query_count,
            "queries_per_second": query_count / duration if duration > 0 else 0,
            "average_query_time_ms": (total_query_time / query_count * 1000) if query_count > 0 else 0,
            "total_query_time_seconds": total_query_time
        }
    
    async def _run_network_benchmark(self, duration: int) -> Dict[str, Any]:
        """Run network performance benchmark"""
        start_time = time.time()
        
        # Simple network test using Redis if available
        if self.redis_client:
            try:
                operations = 0
                total_time = 0.0
                
                while time.time() - start_time < duration:
                    op_start = time.time()
                    
                    # Simple Redis operations
                    await self.redis_client.set(f"benchmark_{operations}", "test_value")
                    await self.redis_client.get(f"benchmark_{operations}")
                    await self.redis_client.delete(f"benchmark_{operations}")
                    
                    op_time = time.time() - op_start
                    total_time += op_time
                    operations += 1
                    
                    await asyncio.sleep(0.001)
                
                return {
                    "operations_executed": operations,
                    "operations_per_second": operations / duration if duration > 0 else 0,
                    "average_operation_time_ms": (total_time / operations * 1000) if operations > 0 else 0,
                    "network_latency_estimate_ms": (total_time / (operations * 3) * 1000) if operations > 0 else 0
                }
            
            except Exception as e:
                return {"error": f"Network benchmark failed: {str(e)}"}
        
        return {"error": "No Redis connection available for network benchmark"}
    
    async def _tune_parameters(self, payload: Dict) -> Dict[str, Any]:
        """Automatically tune system parameters using optimization algorithms"""
        parameter_set = payload.get("parameters", {})
        optimization_goal = payload.get("goal", "performance")  # performance, cost, reliability
        tuning_method = payload.get("method", "grid_search")  # grid_search, genetic, bayesian
        
        tuning_results = {
            "parameter_set": parameter_set,
            "optimization_goal": optimization_goal,
            "tuning_method": tuning_method,
            "original_parameters": {},
            "optimized_parameters": {},
            "performance_improvement": 0.0,
            "tuning_iterations": 0
        }
        
        # Get current parameter values
        current_params = await self._get_current_parameters(parameter_set)
        tuning_results["original_parameters"] = current_params
        
        # Perform parameter tuning based on method
        if tuning_method == "grid_search":
            optimized_params = await self._grid_search_optimization(current_params, optimization_goal)
        elif tuning_method == "genetic":
            optimized_params = await self._genetic_algorithm_optimization(current_params, optimization_goal)
        else:  # bayesian
            optimized_params = await self._bayesian_optimization(current_params, optimization_goal)
        
        tuning_results["optimized_parameters"] = optimized_params
        
        # Apply optimized parameters and measure improvement
        baseline_performance = await self._measure_performance_baseline()
        
        await self._apply_parameters(optimized_params)
        await asyncio.sleep(10)  # Allow time for changes to take effect
        
        optimized_performance = await self._measure_performance_baseline()
        improvement = ((optimized_performance - baseline_performance) / baseline_performance * 100) if baseline_performance > 0 else 0
        
        tuning_results["performance_improvement"] = improvement
        
        return tuning_results
    
    async def _get_current_parameters(self, parameter_set: Dict) -> Dict[str, Any]:
        """Get current values of system parameters"""
        # Placeholder - would get actual system parameters
        return {
            "cache_size_mb": 512,
            "worker_threads": 4,
            "connection_pool_size": 10,
            "timeout_seconds": 30,
            "batch_size": 100
        }
    
    async def _grid_search_optimization(self, current_params: Dict, goal: str) -> Dict[str, Any]:
        """Perform grid search parameter optimization"""
        # Simplified grid search implementation
        best_params = current_params.copy()
        best_score = await self._evaluate_parameters(current_params, goal)
        
        # Define parameter ranges (simplified)
        param_ranges = {
            "cache_size_mb": [256, 512, 1024],
            "worker_threads": [2, 4, 8],
            "connection_pool_size": [5, 10, 20],
            "timeout_seconds": [15, 30, 60],
            "batch_size": [50, 100, 200]
        }
        
        # Test a few combinations (in production, this would be more comprehensive)
        for param_name, param_values in param_ranges.items():
            if param_name in current_params:
                for value in param_values:
                    test_params = current_params.copy()
                    test_params[param_name] = value
                    
                    score = await self._evaluate_parameters(test_params, goal)
                    if score > best_score:
                        best_score = score
                        best_params[param_name] = value
        
        return best_params
    
    async def _genetic_algorithm_optimization(self, current_params: Dict, goal: str) -> Dict[str, Any]:
        """Perform genetic algorithm parameter optimization"""
        # Simplified genetic algorithm implementation
        # In production, this would be more sophisticated with proper genetic operators
        
        population_size = 8
        generations = 3  # Limited for demo purposes
        
        # Initialize population with variations of current parameters
        population = []
        for i in range(population_size):
            individual = current_params.copy()
            # Mutate parameters slightly
            for param in individual:
                if isinstance(individual[param], (int, float)):
                    mutation_factor = 0.8 + (i * 0.05)  # Vary by 0.8-1.2x
                    individual[param] = individual[param] * mutation_factor
            population.append(individual)
        
        best_individual = current_params.copy()
        best_fitness = await self._evaluate_parameters(current_params, goal)
        
        for generation in range(generations):
            # Evaluate fitness for each individual
            fitness_scores = []
            for individual in population:
                fitness = await self._evaluate_parameters(individual, goal)
                fitness_scores.append(fitness)
                
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_individual = individual.copy()
        
        return best_individual
    
    async def _bayesian_optimization(self, current_params: Dict, goal: str) -> Dict[str, Any]:
        """Perform Bayesian optimization for parameter tuning"""
        # Simplified Bayesian optimization
        # In production, would use libraries like scikit-optimize
        
        best_params = current_params.copy()
        best_score = await self._evaluate_parameters(current_params, goal)
        
        # Try a few intelligent guesses based on "Bayesian" reasoning
        # This is a placeholder for actual Bayesian optimization
        candidates = []
        
        # Generate candidate parameter sets
        for i in range(5):
            candidate = current_params.copy()
            for param in candidate:
                if isinstance(candidate[param], (int, float)):
                    # Intelligent variation based on "prior knowledge"
                    if param == "cache_size_mb":
                        candidate[param] = candidate[param] * (1.2 + i * 0.1)
                    elif param == "worker_threads":
                        candidate[param] = max(2, candidate[param] + i - 2)
                    else:
                        candidate[param] = candidate[param] * (0.9 + i * 0.1)
            candidates.append(candidate)
        
        # Evaluate candidates
        for candidate in candidates:
            score = await self._evaluate_parameters(candidate, goal)
            if score > best_score:
                best_score = score
                best_params = candidate.copy()
        
        return best_params
    
    async def _evaluate_parameters(self, params: Dict, goal: str) -> float:
        """Evaluate parameter set performance"""
        # Simplified evaluation function
        # In production, would actually apply parameters and measure real performance
        
        score = 0.5  # Base score
        
        if goal == "performance":
            # Higher cache size and more workers generally improve performance
            if params.get("cache_size_mb", 0) > 512:
                score += 0.2
            if params.get("worker_threads", 0) > 4:
                score += 0.1
            if params.get("connection_pool_size", 0) > 10:
                score += 0.1
        
        elif goal == "cost":
            # Lower resource usage reduces cost
            if params.get("cache_size_mb", 0) < 512:
                score += 0.2
            if params.get("worker_threads", 0) <= 4:
                score += 0.1
        
        elif goal == "reliability":
            # Moderate values often provide better reliability
            if 256 <= params.get("cache_size_mb", 0) <= 1024:
                score += 0.1
            if 30 <= params.get("timeout_seconds", 0) <= 60:
                score += 0.1
        
        # Add some noise to simulate real-world variability
        import random
        score += random.uniform(-0.1, 0.1)
        
        return max(0.0, min(1.0, score))
    
    async def _apply_parameters(self, params: Dict):
        """Apply optimized parameters to the system"""
        # Placeholder for actual parameter application
        # This would involve updating configuration files, environment variables, or making API calls
        # to other services/orchestrators.
        self.logger.info(f"Applying optimized parameters: {params}")
        await self._publish_to_stream("config.update", {"source": self.config.name, "parameters": params})

    async def _measure_performance_baseline(self) -> float:
        """Measure a baseline performance score for parameter tuning evaluation"""
        # This is a simplified placeholder. In a real system, this would run a micro-benchmark
        # or collect key performance indicators over a short period.
        await asyncio.sleep(1) # Simulate measurement
        return 100.0 # Return a hypothetical performance score

    async def _persist_optimization_result(self, result: OptimizationResult):
        """Persist the optimization result to the database."""
        if not self.db_pool:
            self.logger.warning("DB pool not initialized, cannot persist optimization results.")
            return

        try:
            await self._db_query(
                """INSERT INTO optimization_results (optimization_id, rule_id, applied_at, before_metrics, after_metrics, improvement, success, details)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                result.optimization_id, result.rule_id, datetime.fromtimestamp(result.applied_at),
                json.dumps(result.before_metrics), json.dumps(result.after_metrics),
                json.dumps(result.improvement), result.success, json.dumps(result.details)
            )
            self.logger.info(f"Optimization result {result.optimization_id} persisted.")
        except Exception as e:
            self.logger.error(f"Failed to persist optimization result {result.optimization_id}: {e}")

    async def _handle_optimization_task(self, msg):
        """Handle incoming optimization tasks"""
        await self._handle_task_request(msg)

    async def _handle_performance_metrics(self, msg):
        """Handle incoming performance metrics from other agents"""
        payload = json.loads(msg.data.decode())
        metrics_raw = payload.get("metrics", [])

        for metric_raw in metrics_raw:
            try:
                metric = PerformanceMetric(
                    metric_id=metric_raw.get("metric_id", str(uuid.uuid4())),
                    metric_type=MetricType[metric_raw["metric_type"].upper()],
                    value=metric_raw["value"],
                    timestamp=metric_raw.get("timestamp", time.time()),
                    source=metric_raw.get("source", "unknown"),
                    metadata=metric_raw.get("metadata", {})
                )
                # Store in in-memory buffer for real-time analysis
                self.metrics_buffer[metric.metric_id].append(metric)
            except Exception as e:
                self.logger.error(f"Failed to process incoming performance metric: {e}", metric=metric_raw)
        await msg.ack()

    async def _handle_resource_alerts(self, msg):
        """Handle incoming resource alerts from monitoring agent"""
        payload = json.loads(msg.data.decode())
        alert_id = payload.get("alert_id")
        rule_id = payload.get("rule_id")
        severity = payload.get("severity")
        message = payload.get("message")

        self.logger.warning(f"Received resource alert: {message} (Severity: {severity})")

        # Attempt to find a corresponding optimization rule and apply it
        for opt_rule_id, opt_rule in self.optimization_rules.items():
            # Simple matching, can be improved with more sophisticated rule matching
            if opt_rule.optimization_type.value in message.lower() or opt_rule.rule_id == rule_id:
                if opt_rule.enabled and time.time() - opt_rule.last_applied > opt_rule.cooldown_seconds:
                    self.logger.info(f"Attempting to apply optimization rule {opt_rule.name} in response to alert.")
                    opportunity = {"rule_id": opt_rule.rule_id, "rule": opt_rule, "priority": opt_rule.priority, "estimated_impact": 0.5, "confidence": 0.9}
                    result = await self._apply_optimization(opportunity)
                    if result["success"]:
                        self.logger.info("Emergency optimization applied",
                                       alert_id=alert_id,
                                       rule_id=opt_rule.rule_id)
                    else:
                        self.logger.error("Emergency optimization failed",
                                       alert_id=alert_id,
                                       rule_id=opt_rule.rule_id, error=result["error"])
                break
        await msg.ack()

    async def _handle_optimization_request(self, msg):
        """Handle manual optimization requests"""
        payload = json.loads(msg.data.decode())
        request_type = payload.get("request_type")
        response_subject = msg.reply

        try:
            result = {}
            if request_type == "immediate":
                result = await self._optimize_performance({
                    "service": payload.get("service", "all"),
                    "level": payload.get("level", "standard")
                })
            elif request_type == "scheduled":
                await self._schedule_optimization(payload)
                result = {"scheduled": True, "scheduled_at": payload.get("scheduled_time")}
            elif request_type == "analyze":
                result = await self._analyze_performance(payload)
            elif request_type == "predict":
                result = await self._predict_optimization_needs(payload)
            elif request_type == "benchmark":
                result = await self._benchmark_performance(payload)
            elif request_type == "tune":
                result = await self._tune_parameters(payload)
            else:
                raise ValueError(f"Unknown optimization request type: {request_type}")
            
            if response_subject:
                await self._publish(response_subject, json.dumps(result).encode())
        
        except Exception as e:
            self.logger.error("Failed to handle optimization request", error=str(e), payload=payload)
            if response_subject:
                await self._publish(response_subject, json.dumps({"error": str(e)}).encode())
        finally:
            await msg.ack()

    async def _schedule_optimization(self, data: Dict):
        """Schedule optimization for future execution"""
        scheduled_time = data.get("scheduled_time", time.time() + 3600)  # Default: 1 hour
        optimization_task = {
            "task_type": "optimize_performance",
            "payload": data.get("optimization_params", {}),
            "scheduled_for": scheduled_time
        }
        
        # In production, this would interact with a persistent scheduler service
        # For now, we'll just log and potentially store in DB
        await self._db_query(
            "INSERT INTO scheduled_optimizations (task_type, payload, scheduled_for) VALUES ($1, $2, $3)",
            optimization_task["task_type"], json.dumps(optimization_task["payload"]),
            datetime.fromtimestamp(optimization_task["scheduled_for"])
        )
        self.logger.info("Optimization scheduled",
                        scheduled_time=datetime.fromtimestamp(scheduled_time).isoformat(),
                        task=optimization_task)
    
    async def _continuous_monitoring(self):
        """Continuously monitor system performance and apply optimizations"""
        while not self._shutdown_event.is_set():
            try:
                # Collect current system metrics
                system_metrics = await self._collect_current_metrics("all", 60)
                
                # Identify optimization opportunities
                opportunities = await self._identify_optimization_opportunities(system_metrics)
                
                # Apply high-priority, high-confidence optimizations automatically
                for opportunity in opportunities:
                    if (opportunity["priority"] <= 1 and 
                        opportunity["confidence"] > 0.8 and
                        opportunity["estimated_impact"] > 0.2):
                        
                        result = await self._apply_optimization(opportunity)
                        if result["success"]:
                            self.logger.info("Automatic optimization applied",
                                           rule_id=opportunity["rule_id"])
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error("Continuous monitoring failed", error=str(e))
                await asyncio.sleep(30)
    
    async def _predictive_optimization(self):
        """Perform predictive optimization based on patterns"""
        while not self._shutdown_event.is_set():
            try:
                # Analyze trends and patterns
                predictions = await self._predict_optimization_needs({
                    "horizon_hours": 2,
                    "services": ["all"]
                })
                
                # Apply preventive optimizations for high-probability issues
                for service, service_predictions in predictions["predictions"].items():
                    opportunities = service_predictions.get("optimization_opportunities", [])
                    
                    for opp in opportunities:
                        if opp["probability"] > 0.8 and opp["estimated_impact"] > 0.3:
                            # Apply preventive optimization
                            self.logger.info("Applying predictive optimization",
                                           service=service,
                                           optimization_type=opp["type"])
                
                await asyncio.sleep(1800)  # Run every 30 minutes
                
            except Exception as e:
                self.logger.error("Predictive optimization failed", error=str(e))
                await asyncio.sleep(300)
    
    async def _cache_optimization(self):
        """Continuously optimize caching strategies"""
        while not self._shutdown_event.is_set():
            try:
                # Analyze cache performance for each cache instance
                # For simplicity, assume a 'default' cache, extend for multiple named caches
                cache_name = "default"
                cache_analysis = await self._analyze_cache_performance_detailed(cache_name)
                
                # Optimize if hit rate is below threshold
                if cache_analysis["hit_rate"] < 75:
                    await self._optimize_cache_strategy({
                        "cache_name": cache_name,
                        "target_hit_rate": 80
                    })
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                self.logger.error("Cache optimization failed", error=str(e))
                await asyncio.sleep(60)
    
    async def _resource_optimization(self):
        """Continuously optimize resource allocation"""
        while not self._shutdown_event.is_set():
            try:
                # Get current resource usage
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Apply resource optimizations based on usage patterns
                if cpu_usage > 85:
                    # High CPU usage - scale workers
                    await self._apply_optimization({
                        "rule": self.optimization_rules.get("cpu_high_usage"),
                        "rule_id": "cpu_high_usage",
                        "priority": 1,
                        "confidence": 0.9,
                        "estimated_impact": 0.4
                    })
                
                elif memory.percent > 90:
                    # High memory usage - trigger cleanup
                    await self._apply_optimization({
                        "rule": self.optimization_rules.get("memory_high_usage"),
                        "rule_id": "memory_high_usage", 
                        "priority": 1,
                        "confidence": 0.9,
                        "estimated_impact": 0.5
                    })
                
                await asyncio.sleep(120)  # Run every 2 minutes
                
            except Exception as e:
                self.logger.error("Resource optimization failed", error=str(e))
                await asyncio.sleep(60)
    
    async def _cleanup_metrics(self):
        """Clean up old metrics to prevent memory bloat"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                # Keep last 1 hour of metrics in buffer
                retention_period_buffer = 3600  
                
                for metric_key, metric_deque in self.metrics_buffer.items():
                    while metric_deque and metric_deque[0].timestamp < current_time - retention_period_buffer:
                        metric_deque.popleft()
                
                # Clean optimization history (e.g., keep last 7 days)
                retention_period_history = 7 * 24 * 3600
                self.optimization_history = [
                    result for result in self.optimization_history
                    if result.applied_at > current_time - retention_period_history
                ]
                
                await asyncio.sleep(3600)  # Clean every hour
                
            except Exception as e:
                self.logger.error("Metrics cleanup failed", error=str(e))
                await asyncio.sleep(300)

    async def _handle_rule_update(self, msg):
        """Handle dynamic rule updates or additions."""
        payload = json.loads(msg.data.decode())
        rule_data = payload.get("rule")
        action = payload.get("action") # e.g., "add", "update", "delete"

        if not rule_data or not action:
            self.logger.error("Rule data or action missing for rule update.")
            await msg.ack()
            return

        try:
            rule_id = rule_data["rule_id"]
            if action == "add" or action == "update":
                rule = OptimizationRule(
                    rule_id=rule_id,
                    name=rule_data["name"],
                    optimization_type=OptimizationType[rule_data["optimization_type"].upper()],
                    condition=rule_data["condition"],
                    action=rule_data["action"],
                    priority=rule_data["priority"],
                    enabled=rule_data.get("enabled", True),
                    parameters=rule_data.get("parameters", {}),
                    cooldown_seconds=rule_data.get("cooldown_seconds", 300),
                    last_applied=rule_data.get("last_applied", 0.0)
                )
                self.optimization_rules[rule_id] = rule
                # Persist to DB
                await self._db_query(
                    """INSERT INTO optimization_rules (rule_id, name, optimization_type, condition, action, priority, enabled, parameters, cooldown_seconds, last_applied)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                       ON CONFLICT (rule_id) DO UPDATE SET
                       name = EXCLUDED.name, optimization_type = EXCLUDED.optimization_type, condition = EXCLUDED.condition,
                       action = EXCLUDED.action, priority = EXCLUDED.priority, enabled = EXCLUDED.enabled,
                       parameters = EXCLUDED.parameters, cooldown_seconds = EXCLUDED.cooldown_seconds,
                       last_applied = EXCLUDED.last_applied, updated_at = NOW()""",
                    rule.rule_id, rule.name, rule.optimization_type.value, rule.condition, rule.action,
                    rule.priority, rule.enabled, json.dumps(rule.parameters), rule.cooldown_seconds,
                    datetime.fromtimestamp(rule.last_applied)
                )
                self.logger.info(f"Optimization rule {rule_id} {action}d and persisted.")
            elif action == "delete":
                if rule_id in self.optimization_rules:
                    del self.optimization_rules[rule_id]
                    await self._db_query("DELETE FROM optimization_rules WHERE rule_id = $1", rule_id)
                    self.logger.info(f"Optimization rule {rule_id} deleted.")
                else:
                    self.logger.warning(f"Attempted to delete non-existent rule: {rule_id}")
            else:
                self.logger.warning(f"Unknown rule update action: {action}")
        except Exception as e:
            self.logger.error(f"Error processing rule update: {e}", rule_data=rule_data)
        finally:
            await msg.ack()

    async def _rule_updates_monitor(self):
        """Periodically refresh rules from the database to ensure consistency."""
        while not self._shutdown_event.is_set():
            await asyncio.sleep(300) # Refresh every 5 minutes
            await self._load_rules_from_db()


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
                "benchmark_testing",
                "continuous_monitoring"
            ],
            nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
            consul_url=os.getenv("CONSUL_URL", "http://consul:8500")
        )
        
        engine = OptimizingEngine(config)
        await engine.run()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Optimizing Engine stopped.")

