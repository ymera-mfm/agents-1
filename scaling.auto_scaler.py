# scaling/auto_scaler.py
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

@dataclass
class ScalingMetric:
    name: str
    value: float
    threshold: float
    weight: float

class AdvancedAutoScaler:
    def __init__(self):
        self.prometheus = PrometheusConnect(
            url=os.getenv('PROMETHEUS_URL', 'http://prometheus:9090'),
            disable_ssl=True
        )
        self.k8s_client = self._init_k8s_client()
        self.metrics_window = 300  # 5 minutes window
        self.scaling_cooldown = 60  # 1 minute cooldown
        self.last_scaling_time = 0
        
    def _init_k8s_client(self):
        """Initialize Kubernetes client"""
        try:
            config.load_incluster_config()
            return client.AppsV1Api()
        except config.ConfigException:
            logger.warning("Not running in cluster, using local config")
            config.load_kube_config()
            return client.AppsV1Api()
    
    async def scale_based_on_metrics(self, deployment_name: str, namespace: str = "ymera-enterprise"):
        """Scale deployment based on multiple metrics"""
        if time.time() - self.last_scaling_time < self.scaling_cooldown:
            logger.info("In scaling cooldown period")
            return
        
        # Collect metrics from multiple sources
        metrics = await self._collect_metrics(deployment_name)
        
        # Calculate scaling decision
        scaling_decision = self._calculate_scaling_decision(metrics)
        
        if scaling_decision.scale_up:
            await self._scale_deployment(deployment_name, namespace, scaling_decision.replicas)
        elif scaling_decision.scale_down:
            await self._scale_deployment(deployment_name, namespace, scaling_decision.replicas)
    
    async def _collect_metrics(self, deployment_name: str) -> List[ScalingMetric]:
        """Collect metrics from various sources"""
        metrics = []
        
        # CPU utilization
        cpu_usage = await self._get_cpu_usage(deployment_name)
        metrics.append(ScalingMetric(
            name="cpu_usage",
            value=cpu_usage,
            threshold=70.0,  # 70% CPU utilization
            weight=0.4
        ))
        
        # Memory utilization
        memory_usage = await self._get_memory_usage(deployment_name)
        metrics.append(ScalingMetric(
            name="memory_usage",
            value=memory_usage,
            threshold=80.0,  # 80% memory utilization
            weight=0.3
        ))
        
        # Request rate
        request_rate = await self._get_request_rate(deployment_name)
        metrics.append(ScalingMetric(
            name="request_rate",
            value=request_rate,
            threshold=100.0,  # 100 requests per second per pod
            weight=0.2
        ))
        
        # Queue depth (for async processing)
        queue_depth = await self._get_queue_depth()
        metrics.append(ScalingMetric(
            name="queue_depth",
            value=queue_depth,
            threshold=1000.0,  # 1000 messages in queue
            weight=0.1
        ))
        
        # Business metrics (custom)
        active_users = await self._get_active_users()
        metrics.append(ScalingMetric(
            name="active_users",
            value=active_users,
            threshold=1000.0,  # 1000 active users per pod
            weight=0.05
        ))
        
        return metrics
    
    async def _get_cpu_usage(self, deployment_name: str) -> float:
        """Get CPU usage for deployment"""
        query = f'''
            sum(rate(container_cpu_usage_seconds_total{{container="ymera-api", pod=~"{deployment_name}-.*"}}[1m])) 
            / 
            sum(kube_pod_container_resource_limits{{resource="cpu", container="ymera-api", pod=~"{deployment_name}-.*"}})
            * 100
        '''
        result = self.prometheus.custom_query(query)
        return float(result[0]['value'][1]) if result else 0.0
    
    async def _get_memory_usage(self, deployment_name: str) -> float:
        """Get memory usage for deployment"""
        query = f'''
            sum(container_memory_working_set_bytes{{container="ymera-api", pod=~"{deployment_name}-.*"}})
            /
            sum(kube_pod_container_resource_limits{{resource="memory", container="ymera-api", pod=~"{deployment_name}-.*"}})
            * 100
        '''
        result = self.prometheus.custom_query(query)
        return float(result[0]['value'][1]) if result else 0.0
    
    async def _get_request_rate(self, deployment_name: str) -> float:
        """Get HTTP request rate"""
        query = f'''
            sum(rate(istio_requests_total{{destination_workload="{deployment_name}", response_code!~"5.*"}}[1m]))
        '''
        result = self.prometheus.custom_query(query)
        return float(result[0]['value'][1]) if result else 0.0
    
    async def _get_queue_depth(self) -> float:
        """Get message queue depth"""
        query = 'kafka_consumergroup_lag'
        result = self.prometheus.custom_query(query)
        return float(result[0]['value'][1]) if result else 0.0
    
    async def _get_active_users(self) -> float:
        """Get active users count"""
        query = 'sum(ymera_active_users)'
        result = self.prometheus.custom_query(query)
        return float(result[0]['value'][1]) if result else 0.0
    
    def _calculate_scaling_decision(self, metrics: List[ScalingMetric]) -> 'ScalingDecision':
        """Calculate scaling decision based on weighted metrics"""
        current_replicas = self._get_current_replicas()
        
        # Calculate weighted score
        total_score = 0.0
        for metric in metrics:
            if metric.value > metric.threshold:
                excess = metric.value - metric.threshold
                score = (excess / metric.threshold) * metric.weight
                total_score += score
        
        # Determine scaling action
        scaling_decision = ScalingDecision()
        
        if total_score > 0.5:  # Scale up threshold
            scaling_decision.scale_up = True
            scaling_decision.replicas = min(
                current_replicas + max(1, int(total_score * 2)),
                50  # Max replicas
            )
        elif total_score < -0.3:  # Scale down threshold
            scaling_decision.scale_down = True
            scaling_decision.replicas = max(
                3,  # Min replicas
                current_replicas - max(1, int(abs(total_score) * 2))
            )
        
        return scaling_decision
    
    def _get_current_replicas(self) -> int:
        """Get current replica count"""
        deployment = self.k8s_client.read_namespaced_deployment(
            name="ymera-api",
            namespace="ymera-enterprise"
        )
        return deployment.spec.replicas
    
    async def _scale_deployment(self, deployment_name: str, namespace: str, replicas: int):
        """Scale deployment to specified replica count"""
        try:
            # Get current deployment
            deployment = self.k8s_client.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            
            # Update replica count
            deployment.spec.replicas = replicas
            self.k8s_client.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            
            logger.info(f"Scaled deployment {deployment_name} to {replicas} replicas")
            self.last_scaling_time = time.time()
            
        except client.ApiException as e:
            logger.error(f"Failed to scale deployment: {e}")

@dataclass
class ScalingDecision:
    scale_up: bool = False
    scale_down: bool = False
    replicas: int = 0

# Predictive scaling based on time series analysis
class PredictiveScaler:
    def __init__(self):
        self.prometheus = PrometheusConnect(
            url=os.getenv('PROMETHEUS_URL', 'http://prometheus:9090'),
            disable_ssl=True
        )
        self.history_hours = 24  # 24 hours of history
        self.prediction_horizon = 60  # 60 minutes ahead
    
    async def predict_load(self, metric_name: str) -> List[float]:
        """Predict future load using time series analysis"""
        # Get historical data
        historical_data = await self._get_historical_data(metric_name)
        
        if not historical_data:
            return []
        
        # Use ARIMA or similar for prediction
        predictions = self._arima_forecast(historical_data, self.prediction_horizon)
        
        return predictions
    
    async def _get_historical_data(self, metric_name: str) -> List[float]:
        """Get historical metric data"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=self.history_hours)
        
        query = metric_name
        result = self.prometheus.custom_query_range(
            query=query,
            start_time=start_time,
            end_time=end_time,
            step="1m"
        )
        
        if not result:
            return []
        
        values = [float(point[1]) for point in result[0]['values']]
        return values
    
    def _arima_forecast(self, data: List[float], steps: int) -> List[float]:
        """Simple ARIMA-like forecasting"""
        # For production, use statsmodels or similar library
        # This is a simplified version
        
        if len(data) < 10:
            return [data[-1]] * steps if data else [0] * steps
        
        # Simple moving average prediction
        window_size = min(60, len(data) // 2)
        predictions = []
        
        for i in range(steps):
            # Use weighted average of recent values
            recent_data = data[-window_size:]
            weights = np.linspace(0.1, 1.0, len(recent_data))
            prediction = np.average(recent_data, weights=weights)
            predictions.append(prediction)
        
        return predictions

# Multi-dimensional scaling based on custom metrics
class MultiDimensionalScaler:
    def __init__(self):
        self.metrics_weights = {
            'cpu_usage': 0.25,
            'memory_usage': 0.20,
            'request_rate': 0.20,
            'response_time': 0.15,
            'error_rate': 0.10,
            'business_metric': 0.10
        }
        self.scaling_thresholds = {
            'cpu_usage': (30, 70),  # (scale_down, scale_up)
            'memory_usage': (40, 75),
            'request_rate': (20, 100),
            'response_time': (100, 500),  # ms
            'error_rate': (0.1, 5.0),  # percentage
            'business_metric': (500, 2000)  # custom units
        }
    
    async def calculate_optimal_replicas(self, current_replicas: int) -> int:
        """Calculate optimal replica count based on multiple dimensions"""
        metrics = await self._get_current_metrics()
        
        scaling_factors = []
        for metric_name, (current_value, weight) in metrics.items():
            scale_down_thresh, scale_up_thresh = self.scaling_thresholds[metric_name]
            
            if current_value > scale_up_thresh:
                # Scale up needed
                factor = (current_value - scale_up_thresh) / scale_up_thresh * weight
                scaling_factors.append(factor)
            elif current_value < scale_down_thresh:
                # Scale down possible
                factor = (scale_down_thresh - current_value) / scale_down_thresh * weight * -1
                scaling_factors.append(factor)
            else:
                scaling_factors.append(0)
        
        total_factor = sum(scaling_factors)
        replica_change = int(total_factor * current_replicas)
        
        new_replicas = max(3, min(50, current_replicas + replica_change))
        return new_replicas
    
    async def _get_current_metrics(self) -> Dict[str, tuple]:
        """Get current metric values"""
        # Implementation would query various monitoring systems
        return {
            'cpu_usage': (65.0, 0.25),
            'memory_usage': (60.0, 0.20),
            'request_rate': (85.0, 0.20),
            'response_time': (150.0, 0.15),
            'error_rate': (1.5, 0.10),
            'business_metric': (1200.0, 0.10)
        }

# Main scaling orchestrator
class ScalingOrchestrator:
    def __init__(self):
        self.auto_scaler = AdvancedAutoScaler()
        self.predictive_scaler = PredictiveScaler()
        self.multi_dim_scaler = MultiDimensionalScaler()
        self.scaling_interval = 60  # Check every minute
    
    async def start_scaling_loop(self):
        """Main scaling loop"""
        while True:
            try:
                await self._perform_scaling()
                await asyncio.sleep(self.scaling_interval)
            except Exception as e:
                logger.error(f"Scaling loop error: {e}")
                await asyncio.sleep(30)  # Backoff on error
    
    async def _perform_scaling(self):
        """Perform all scaling operations"""
        # Reactive scaling based on current metrics
        await self.auto_scaler.scale_based_on_metrics("ymera-api")
        
        # Predictive scaling for upcoming load
        predictions = await self.predictive_scaler.predict_load("istio_requests_total")
        if predictions and max(predictions) > 150:  # High predicted load
            current_replicas = self.auto_scaler._get_current_replicas()
            needed_replicas = current_replicas + int(max(predictions) / 100)
            await self.auto_scaler._scale_deployment("ymera-api", "ymera-enterprise", needed_replicas)
        
        # Multi-dimensional optimization
        current_replicas = self.auto_scaler._get_current_replicas()
        optimal_replicas = await self.multi_dim_scaler.calculate_optimal_replicas(current_replicas)
        
        if optimal_replicas != current_replicas:
            await self.auto_scaler._scale_deployment("ymera-api", "ymera-enterprise", optimal_replicas)