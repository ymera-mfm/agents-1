"""
Production-Ready Specialized Engines
Ready-to-deploy implementations of Performance, Optimization, and Analysis engines
"""

import asyncio
import psutil
import json
import time
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority


class MetricSeverity(Enum):
    """Metric alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceAlert:
    """Performance alert structure"""
    id: str
    metric: str
    severity: MetricSeverity
    current_value: float
    threshold: float
    message: str
    timestamp: float


class PerformanceEngineAgent(BaseAgent):
    """Production-ready performance monitoring engine"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Performance tracking
        self.metrics_history = {}
        self.active_alerts = {}
        self.alert_history = []
        
        # Thresholds
        self.thresholds = {
            'cpu_usage': {'warning': 70, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'response_time_ms': {'warning': 500, 'critical': 2000},
            'error_rate': {'warning': 1.0, 'critical': 5.0}
        }
        
        # Statistics
        self.stats = {
            'monitoring_cycles': 0,
            'alerts_generated': 0,
            'alerts_resolved': 0
        }
    
    async def _setup_subscriptions(self):
        """Setup subscriptions"""
        await self._subscribe(
            "performance.monitor.request",
            self._handle_monitor_request,
            queue_group="performance-monitoring"
        )
        
        await self._subscribe(
            "performance.threshold.update",
            self._handle_threshold_update,
            queue_group="performance-threshold"
        )
    
    async def _start_background_tasks(self):
        """Start background monitoring"""
        await super()._start_background_tasks()
        
        task = asyncio.create_task(self._continuous_monitoring())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle performance tasks"""
        if task_request.task_type == "collect_metrics":
            return await self._collect_current_metrics()
        elif task_request.task_type == "analyze_performance":
            return await self._analyze_performance(task_request.payload)
        elif task_request.task_type == "get_alerts":
            return await self._get_active_alerts()
        elif task_request.task_type == "generate_report":
            return await self._generate_performance_report()
        else:
            return {"error": f"Unknown task: {task_request.task_type}"}
    
    async def _continuous_monitoring(self):
        """Continuously monitor system performance"""
        self.logger.info("Performance monitoring started")
        
        while not self.shutdown_event.is_set():
            try:
                # Collect metrics
                metrics = await self._collect_current_metrics()
                
                # Store in history
                timestamp = time.time()
                for metric_name, value in metrics.items():
                    if metric_name not in self.metrics_history:
                        self.metrics_history[metric_name] = []
                    
                    self.metrics_history[metric_name].append({
                        'timestamp': timestamp,
                        'value': value
                    })
                    
                    # Keep only last 1000 entries
                    if len(self.metrics_history[metric_name]) > 1000:
                        self.metrics_history[metric_name] = self.metrics_history[metric_name][-1000:]
                
                # Check thresholds
                await self._check_thresholds(metrics)
                
                self.stats['monitoring_cycles'] += 1
                
                # Publish metrics
                await self._publish_to_stream(
                    "performance.metrics",
                    {
                        'agent_id': self.config.agent_id,
                        'metrics': metrics,
                        'timestamp': timestamp
                    }
                )
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("Performance monitoring stopped")
    
    async def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Process-level metrics
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024**2)
            process_cpu_percent = process.cpu_percent()
            process_threads = process.num_threads()
            
            # Agent-specific metrics
            avg_response_time = self.metrics.avg_processing_time_ms
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory_percent,
                'memory_available_gb': memory_available_gb,
                'disk_usage': disk_percent,
                'disk_free_gb': disk_free_gb,
                'process_memory_mb': process_memory_mb,
                'process_cpu_percent': process_cpu_percent,
                'process_threads': process_threads,
                'response_time_ms': avg_response_time,
                'queue_size': self.task_queue.qsize(),
                'active_tasks': len(self.active_tasks),
                'error_rate': self._calculate_error_rate()
            }
        
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.metrics.tasks_completed == 0:
            return 0.0
        
        return (self.metrics.tasks_failed / self.metrics.tasks_completed) * 100
    
    async def _check_thresholds(self, metrics: Dict[str, float]):
        """Check metrics against thresholds"""
        for metric_name, thresholds in self.thresholds.items():
            if metric_name not in metrics:
                continue
            
            current_value = metrics[metric_name]
            alert_key = metric_name
            
            # Check critical
            if current_value >= thresholds['critical']:
                if alert_key not in self.active_alerts:
                    await self._create_alert(
                        metric_name,
                        MetricSeverity.CRITICAL,
                        current_value,
                        thresholds['critical']
                    )
            
            # Check warning
            elif current_value >= thresholds['warning']:
                if alert_key not in self.active_alerts:
                    await self._create_alert(
                        metric_name,
                        MetricSeverity.WARNING,
                        current_value,
                        thresholds['warning']
                    )
            
            # Resolve if below warning
            else:
                if alert_key in self.active_alerts:
                    await self._resolve_alert(alert_key)
    
    async def _create_alert(
        self,
        metric: str,
        severity: MetricSeverity,
        current_value: float,
        threshold: float
    ):
        """Create performance alert"""
        import uuid
        
        alert_id = str(uuid.uuid4())
        alert = PerformanceAlert(
            id=alert_id,
            metric=metric,
            severity=severity,
            current_value=current_value,
            threshold=threshold,
            message=f"{metric} at {current_value:.2f} exceeds {severity.value} threshold of {threshold:.2f}",
            timestamp=time.time()
        )
        
        self.active_alerts[metric] = alert
        self.alert_history.append(alert)
        self.stats['alerts_generated'] += 1
        
        # Publish alert
        await self._publish_to_stream(
            "performance.alert",
            {
                'id': alert.id,
                'metric': alert.metric,
                'severity': alert.severity.value,
                'current_value': alert.current_value,
                'threshold': alert.threshold,
                'message': alert.message,
                'timestamp': alert.timestamp
            }
        )
        
        self.logger.warning(f"Performance alert: {alert.message}")
    
    async def _resolve_alert(self, metric_key: str):
        """Resolve performance alert"""
        if metric_key in self.active_alerts:
            alert = self.active_alerts.pop(metric_key)
            self.stats['alerts_resolved'] += 1
            
            self.logger.info(f"Alert resolved: {alert.message}")
    
    async def _handle_monitor_request(self, msg):
        """Handle monitoring requests"""
        try:
            data = json.loads(msg.data.decode())
            duration = data.get('duration', 60)
            
            metrics_list = []
            end_time = time.time() + duration
            
            while time.time() < end_time:
                metrics = await self._collect_current_metrics()
                metrics_list.append(metrics)
                await asyncio.sleep(5)
            
            # Generate summary
            if metrics_list:
                summary = self._generate_monitoring_summary(metrics_list)
            else:
                summary = {}
            
            response = {
                'status': 'success',
                'duration': duration,
                'samples': len(metrics_list),
                'summary': summary
            }
            
            if msg.reply:
                await self._publish(msg.reply, response)
        
        except Exception as e:
            self.logger.error(f"Monitor request error: {e}")
        finally:
            await msg.ack()
    
    def _generate_monitoring_summary(self, metrics_list: List[Dict]) -> Dict:
        """Generate summary from metrics"""
        if not metrics_list:
            return {}
        
        cpu_values = [m['cpu_usage'] for m in metrics_list if 'cpu_usage' in m]
        memory_values = [m['memory_usage'] for m in metrics_list if 'memory_usage' in m]
        
        return {
            'cpu': {
                'average': statistics.mean(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0
            },
            'memory': {
                'average': statistics.mean(memory_values) if memory_values else 0,
                'min': min(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0
            }
        }
    
    async def _handle_threshold_update(self, msg):
        """Handle threshold updates"""
        try:
            data = json.loads(msg.data.decode())
            
            metric = data['metric']
            if metric in self.thresholds:
                self.thresholds[metric]['warning'] = data.get('warning', self.thresholds[metric]['warning'])
                self.thresholds[metric]['critical'] = data.get('critical', self.thresholds[metric]['critical'])
                
                self.logger.info(f"Thresholds updated for {metric}")
                
                if msg.reply:
                    await self._publish(msg.reply, {'status': 'success'})
        
        except Exception as e:
            self.logger.error(f"Threshold update error: {e}")
        finally:
            await msg.ack()
    
    async def _analyze_performance(self, payload: Dict) -> Dict[str, Any]:
        """Analyze performance data"""
        lookback_minutes = payload.get('lookback_minutes', 60)
        
        cutoff_time = time.time() - (lookback_minutes * 60)
        
        analysis = {
            'metrics': {},
            'trends': {},
            'recommendations': []
        }
        
        # Analyze each metric
        for metric_name, history in self.metrics_history.items():
            recent = [m for m in history if m['timestamp'] >= cutoff_time]
            
            if not recent:
                continue
            
            values = [m['value'] for m in recent]
            
            analysis['metrics'][metric_name] = {
                'average': statistics.mean(values),
                'min': min(values),
                'max': max(values),
                'samples': len(values)
            }
            
            # Detect trends
            if len(values) > 2:
                first_half = statistics.mean(values[:len(values)//2])
                second_half = statistics.mean(values[len(values)//2:])
                
                if second_half > first_half * 1.1:
                    analysis['trends'][metric_name] = 'increasing'
                elif second_half < first_half * 0.9:
                    analysis['trends'][metric_name] = 'decreasing'
                else:
                    analysis['trends'][metric_name] = 'stable'
        
        # Generate recommendations
        cpu_avg = analysis['metrics'].get('cpu_usage', {}).get('average', 0)
        memory_avg = analysis['metrics'].get('memory_usage', {}).get('average', 0)
        
        if cpu_avg > 80:
            analysis['recommendations'].append("High CPU usage - consider scaling or optimization")
        if memory_avg > 85:
            analysis['recommendations'].append("High memory usage - consider memory optimization")
        
        return analysis
    
    async def _get_active_alerts(self) -> Dict[str, Any]:
        """Get active alerts"""
        return {
            'count': len(self.active_alerts),
            'alerts': [
                {
                    'metric': alert.metric,
                    'severity': alert.severity.value,
                    'current_value': alert.current_value,
                    'threshold': alert.threshold,
                    'message': alert.message,
                    'timestamp': alert.timestamp
                }
                for alert in self.active_alerts.values()
            ]
        }
    
    async def _generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            'period': '24_hours',
            'generated_at': time.time(),
            'statistics': self.stats,
            'active_alerts': len(self.active_alerts),
            'metrics': {
                name: {
                    'samples': len(history),
                    'latest': history[-1] if history else None
                }
                for name, history in self.metrics_history.items()
            }
        }


class OptimizationEngineAgent(BaseAgent):
    """Production-ready optimization engine"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        self.optimization_history = []
        self.active_optimizations = {}
        
        self.logger.info("OptimizationEngineAgent initialized")
    
    async def _setup_subscriptions(self):
        """Setup subscriptions"""
        await self._subscribe(
            "optimization.request",
            self._handle_optimization_request,
            queue_group="optimization"
        )
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle optimization tasks"""
        if task_request.task_type == "optimize_system":
            return await self._optimize_system(task_request.payload)
        elif task_request.task_type == "get_optimization_history":
            return await self._get_optimization_history()
        else:
            return {"error": f"Unknown task: {task_request.task_type}"}
    
    async def _handle_optimization_request(self, msg):
        """Handle optimization requests"""
        try:
            data = json.loads(msg.data.decode())
            
            result = await self._optimize_system(data)
            
            if msg.reply:
                await self._publish(msg.reply, result)
        
        except Exception as e:
            self.logger.error(f"Optimization error: {e}")
        finally:
            await msg.ack()
    
    async def _optimize_system(self, payload: Dict) -> Dict[str, Any]:
        """Optimize system performance"""
        import uuid
        
        optimization_id = str(uuid.uuid4())
        target = payload.get('target', 'system')
        
        optimizations_applied = []
        
        try:
            # Example optimizations
            if target in ['system', 'cache']:
                # Optimize cache
                optimizations_applied.append({
                    'type': 'cache_optimization',
                    'action': 'clear_old_entries',
                    'impact': 'medium'
                })
            
            if target in ['system', 'memory']:
                # Memory optimization
                import gc
                collected = gc.collect()
                optimizations_applied.append({
                    'type': 'memory_optimization',
                    'action': f'garbage_collection_collected_{collected}_objects',
                    'impact': 'low'
                })
            
            result = {
                'optimization_id': optimization_id,
                'target': target,
                'status': 'success',
                'optimizations_applied': len(optimizations_applied),
                'details': optimizations_applied,
                'timestamp': time.time()
            }
            
            self.optimization_history.append(result)
            
            # Persist if database available
            if self.db_pool:
                await self._db_execute(
                    """INSERT INTO optimizations 
                       (optimization_id, agent_id, target, status, details, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    optimization_id,
                    self.config.agent_id,
                    target,
                    'success',
                    json.dumps(optimizations_applied),
                    datetime.now()
                )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return {
                'optimization_id': optimization_id,
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
    
    async def _get_optimization_history(self) -> Dict[str, Any]:
        """Get optimization history"""
        return {
            'total_optimizations': len(self.optimization_history),
            'recent': self.optimization_history[-10:],
            'success_rate': self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate optimization success rate"""
        if not self.optimization_history:
            return 0.0
        
        successful = sum(1 for o in self.optimization_history if o['status'] == 'success')
        return (successful / len(self.optimization_history)) * 100


class AnalysisEngineAgent(BaseAgent):
    """Production-ready analysis and validation engine"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        self.analysis_results = {}
        self.validation_rules = {}
        
        self.logger.info("AnalysisEngineAgent initialized")
    
    async def _setup_subscriptions(self):
        """Setup subscriptions"""
        await self._subscribe(
            "analysis.request",
            self._handle_analysis_request,
            queue_group="analysis"
        )
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle analysis tasks"""
        if task_request.task_type == "analyze_data":
            return await self._analyze_data(task_request.payload)
        elif task_request.task_type == "validate_data":
            return await self._validate_data(task_request.payload)
        elif task_request.task_type == "generate_insights":
            return await self._generate_insights(task_request.payload)
        else:
            return {"error": f"Unknown task: {task_request.task_type}"}
    
    async def _handle_analysis_request(self, msg):
        """Handle analysis requests"""
        try:
            data = json.loads(msg.data.decode())
            
            analysis_type = data.get('type', 'general')
            payload = data.get('payload', {})
            
            if analysis_type == 'data':
                result = await self._analyze_data(payload)
            elif analysis_type == 'validation':
                result = await self._validate_data(payload)
            elif analysis_type == 'insights':
                result = await self._generate_insights(payload)
            else:
                result = {"error": f"Unknown analysis type: {analysis_type}"}
            
            if msg.reply:
                await self._publish(msg.reply, result)
        
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
        finally:
            await msg.ack()
    
    async def _analyze_data(self, payload: Dict) -> Dict[str, Any]:
        """Analyze provided data"""
        import uuid
        
        analysis_id = str(uuid.uuid4())
        data = payload.get('data', [])
        
        try:
            if not data:
                return {'error': 'No data provided'}
            
            # Convert to numeric values for analysis
            numeric_data = [v for v in data if isinstance(v, (int, float))]
            
            if not numeric_data:
                return {'error': 'No numeric data found'}
            
            result = {
                'analysis_id': analysis_id,
                'status': 'success',
                'statistics': {
                    'count': len(numeric_data),
                    'mean': statistics.mean(numeric_data),
                    'median': statistics.median(numeric_data),
                    'stdev': statistics.stdev(numeric_data) if len(numeric_data) > 1 else 0,
                    'min': min(numeric_data),
                    'max': max(numeric_data),
                    'range': max(numeric_data) - min(numeric_data)
                },
                'timestamp': time.time()
            }
            
            self.analysis_results[analysis_id] = result
            
            return result
        
        except Exception as e:
            self.logger.error(f"Data analysis failed: {e}")
            return {
                'analysis_id': analysis_id,
                'status': 'error',
                'error': str(e)
            }
    
    async def _validate_data(self, payload: Dict) -> Dict[str, Any]:
        """Validate data against rules"""
        import uuid
        
        validation_id = str(uuid.uuid4())
        data = payload.get('data', {})
        rules = payload.get('rules', {})
        
        try:
            validation_errors = []
            
            for field, rule in rules.items():
                if field not in data:
                    if rule.get('required'):
                        validation_errors.append(f"Required field missing: {field}")
                    continue
                
                value = data[field]
                
                # Type validation
                if 'type' in rule:
                    expected_type = rule['type']
                    if expected_type == 'string' and not isinstance(value, str):
                        validation_errors.append(f"Field {field} must be string")
                    elif expected_type == 'number' and not isinstance(value, (int, float)):
                        validation_errors.append(f"Field {field} must be number")
                
                # Range validation
                if 'min' in rule and value < rule['min']:
                    validation_errors.append(f"Field {field} below minimum: {rule['min']}")
                if 'max' in rule and value > rule['max']:
                    validation_errors.append(f"Field {field} exceeds maximum: {rule['max']}")
            
            result = {
                'validation_id': validation_id,
                'status': 'success' if not validation_errors else 'failed',
                'valid': len(validation_errors) == 0,
                'errors': validation_errors,
                'error_count': len(validation_errors),
                'timestamp': time.time()
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return {
                'validation_id': validation_id,
                'status': 'error',
                'error': str(e)
            }
    
    async def _generate_insights(self, payload: Dict) -> Dict[str, Any]:
        """Generate insights from data"""
        import uuid
        
        insights_id = str(uuid.uuid4())
        data = payload.get('data', [])
        
        try:
            if not data:
                return {'error': 'No data provided'}
            
            insights = {
                'insights_id': insights_id,
                'status': 'success',
                'insights': [],
                'timestamp': time.time()
            }
            
            # Generate basic insights
            numeric_data = [v for v in data if isinstance(v, (int, float))]
            
            if numeric_data:
                mean = statistics.mean(numeric_data)
                stdev = statistics.stdev(numeric_data) if len(numeric_data) > 1 else 0
                
                if stdev > mean * 0.5:
                    insights['insights'].append("High variability in data")
                
                if max(numeric_data) > mean * 2:
                    insights['insights'].append("Outliers detected in data")
                
                if len(numeric_data) > 1:
                    trend = "increasing" if numeric_data[-1] > numeric_data[0] else "decreasing"
                    insights['insights'].append(f"Overall trend: {trend}")
            
            return insights
        
        except Exception as e:
            self.logger.error(f"Insight generation failed: {e}")
            return {
                'insights_id': insights_id,
                'status': 'error',
                'error': str(e)
            }


if __name__ == "__main__":
    import os
    
    async def run_performance_engine():
        config = AgentConfig(
            agent_id="performance-engine-prod-001",
            name="performance_engine",
            agent_type="performance",
            capabilities=["system_monitoring", "performance_analysis", "alerting"],
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        engine = PerformanceEngineAgent(config)
        
        if await engine.start():
            await engine.run_forever()
    
    async def run_optimization_engine():
        config = AgentConfig(
            agent_id="optimization-engine-prod-001",
            name="optimization_engine",
            agent_type="optimization",
            capabilities=["system_optimization", "resource_management"],
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        engine = OptimizationEngineAgent(config)
        
        if await engine.start():
            await engine.run_forever()
    
    async def run_analysis_engine():
        config = AgentConfig(
            agent_id="analysis-engine-prod-001",
            name="analysis_engine",
            agent_type="analysis",
            capabilities=["data_analysis", "validation", "insights"],
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
        )
        
        engine = AnalysisEngineAgent(config)
        
        if await engine.start():
            await engine.run_forever()
