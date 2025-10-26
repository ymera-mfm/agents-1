# infrastructure/distributed/__init__.py
"""
Distributed Computing Infrastructure for YMERA Enterprise System
"""
from typing import Dict, List, Any, Optional
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
import uuid
import time

logger = logging.getLogger("ymera.infrastructure.distributed")

class ServiceType(Enum):
    LEARNING_ENGINE = "learning_engine"
    PATTERN_RECOGNITION = "pattern_recognition"
    KNOWLEDGE_BASE = "knowledge_base"
    ADAPTIVE_LEARNING = "adaptive_learning"
    API_GATEWAY = "api_gateway"
    MONITORING = "monitoring"
    SECURITY = "security"

@dataclass
class ServiceInstance:
    service_id: str
    service_type: ServiceType
    host: str
    port: int
    status: str = "healthy"
    last_heartbeat: float = field(default_factory=time.time)
    load: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class ServiceDiscovery:
    """Service discovery and registration system"""
    
    def __init__(self):
        self.services: Dict[ServiceType, List[ServiceInstance]] = {}
        self.health_check_interval = 30  # seconds
    
    async def register_service(self, service_type: ServiceType, host: str, port: int, 
                             metadata: Dict[str, Any] = None) -> str:
        """Register a new service instance"""
        service_id = str(uuid.uuid4())
        instance = ServiceInstance(
            service_id=service_id,
            service_type=service_type,
            host=host,
            port=port,
            metadata=metadata or {}
        )
        
        if service_type not in self.services:
            self.services[service_type] = []
        
        self.services[service_type].append(instance)
        logger.info(f"Registered service {service_type.value} at {host}:{port}")
        
        # Start health checking
        asyncio.create_task(self._health_check_service(instance))
        
        return service_id
    
    async def discover_services(self, service_type: ServiceType) -> List[ServiceInstance]:
        """Discover healthy services of a given type"""
        if service_type not in self.services:
            return []
        
        # Filter out unhealthy services
        healthy_services = [s for s in self.services[service_type] if s.status == "healthy"]
        
        # Sort by load (lowest first)
        healthy_services.sort(key=lambda x: x.load)
        
        return healthy_services
    
    async def _health_check_service(self, instance: ServiceInstance):
        """Periodically check service health"""
        while True:
            try:
                # Simulate health check - in real implementation, this would make an HTTP request
                # For now, we'll just update the heartbeat
                instance.last_heartbeat = time.time()
                
                # Simple load simulation
                instance.load = max(0, min(1.0, instance.load + 0.1 - 0.05))  # Random walk
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health check failed for {instance.service_id}: {str(e)}")
                instance.status = "unhealthy"
                break

class APIGateway:
    """API Gateway with rate limiting and authentication"""
    
    def __init__(self, service_discovery: ServiceDiscovery):
        self.service_discovery = service_discovery
        self.rate_limits: Dict[str, Dict[str, Any]] = {}  # client_id -> rate limit info
        self.request_queue = asyncio.Queue()
    
    async def handle_request(self, client_id: str, service_type: ServiceType, 
                           request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming API request"""
        # Check rate limiting
        if not await self._check_rate_limit(client_id, service_type):
            return {"error": "Rate limit exceeded", "status_code": 429}
        
        # Discover healthy service instances
        services = await self.service_discovery.discover_services(service_type)
        if not services:
            return {"error": "Service unavailable", "status_code": 503}
        
        # Select the least loaded service
        selected_service = services[0]
        
        # Forward request to the service (simulated)
        try:
            response = await self._forward_to_service(selected_service, request_data)
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": "Internal server error", "status_code": 500}
    
    async def _check_rate_limit(self, client_id: str, service_type: ServiceType) -> bool:
        """Check if client has exceeded rate limits"""
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = {
                'last_reset': time.time(),
                'requests': 0,
                'limit': 1000  # requests per minute
            }
        
        rate_info = self.rate_limits[client_id]
        
        # Reset counter if minute has passed
        if time.time() - rate_info['last_reset'] > 60:
            rate_info['last_reset'] = time.time()
            rate_info['requests'] = 0
        
        # Check if limit exceeded
        if rate_info['requests'] >= rate_info['limit']:
            return False
        
        rate_info['requests'] += 1
        return True
    
    async def _forward_to_service(self, service: ServiceInstance, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward request to the actual service"""
        # In real implementation, this would make an HTTP/gRPC call
        # For simulation, we'll just return a mock response
        await asyncio.sleep(0.01)  # Simulate network latency
        
        return {
            "status": "success",
            "service_id": service.service_id,
            "data": f"Processed by {service.service_type.value}"
        }

class DistributedTrainingManager:
    """Manager for distributed training operations"""
    
    def __init__(self):
        self.workers: List[Dict[str, Any]] = []
        self.parameter_servers: List[Dict[str, Any]] = []
        self.training_jobs: Dict[str, Dict[str, Any]] = {}
    
    async def start_distributed_training(self, model_config: Dict[str, Any], 
                                      data_shards: List[Any]) -> str:
        """Start a distributed training job"""
        job_id = str(uuid.uuid4())
        
        # Initialize training job
        self.training_jobs[job_id] = {
            'status': 'initializing',
            'model_config': model_config,
            'data_shards': data_shards,
            'workers': [],
            'start_time': time.time(),
            'metrics': {}
        }
        
        # Assign workers and parameter servers
        await self._assign_resources(job_id)
        
        # Start training
        asyncio.create_task(self._run_training_job(job_id))
        
        return job_id
    
    async def _assign_resources(self, job_id: str):
        """Assign computational resources for training"""
        # This would interface with Kubernetes or cloud resources
        # For simulation, we'll just create virtual workers
        job = self.training_jobs[job_id]
        
        num_workers = min(4, len(job['data_shards']))
        for i in range(num_workers):
            worker_id = f"worker_{i}_{job_id}"
            job['workers'].append({
                'id': worker_id,
                'status': 'assigned',
                'data_shard': job['data_shards'][i] if i < len(job['data_shards']) else None
            })
        
        job['status'] = 'resources_assigned'
    
    async def _run_training_job(self, job_id: str):
        """Execute distributed training"""
        job = self.training_jobs[job_id]
        job['status'] = 'training'
        
        # Simulate distributed training
        training_tasks = []
        for worker in job['workers']:
            task = asyncio.create_task(self._train_worker(worker, job['model_config']))
            training_tasks.append(task)
        
        # Wait for all workers to complete
        results = await asyncio.gather(*training_tasks)
        
        # Aggregate results (simulate parameter server)
        aggregated_metrics = await self._aggregate_results(results)
        
        job['metrics'] = aggregated_metrics
        job['status'] = 'completed'
        job['end_time'] = time.time()
        job['duration'] = job['end_time'] - job['start_time']
    
    async def _train_worker(self, worker: Dict[str, Any], model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Train on a single worker"""
        # Simulate training time based on data size and model complexity
        training_time = 2.0 + (len(worker.get('data_shard', [])) * 0.001)
        await asyncio.sleep(training_time)
        
        # Simulate training metrics
        return {
            'worker_id': worker['id'],
            'loss': 0.1 + (time.time() % 0.1),  # Random loss
            'accuracy': 0.8 + (time.time() % 0.15),  # Random accuracy
            'training_time': training_time
        }
    
    async def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from all workers"""
        total_loss = sum(r['loss'] for r in results)
        total_accuracy = sum(r['accuracy'] for r in results)
        total_time = sum(r['training_time'] for r in results)
        
        return {
            'avg_loss': total_loss / len(results),
            'avg_accuracy': total_accuracy / len(results),
            'total_training_time': total_time,
            'num_workers': len(results)
        }

class MessageQueue:
    """Message queue system for inter-service communication"""
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[Any]] = {}
        self.dead_letter_queues: Dict[str, asyncio.Queue] = {}
    
    async def create_queue(self, queue_name: str):
        """Create a new message queue"""
        if queue_name not in self.queues:
            self.queues[queue_name] = asyncio.Queue()
            self.dead_letter_queues[queue_name] = asyncio.Queue()
            self.subscribers[queue_name] = []
    
    async def publish(self, queue_name: str, message: Any, priority: int = 0):
        """Publish a message to a queue"""
        if queue_name not in self.queues:
            await self.create_queue(queue_name)
        
        await self.queues[queue_name].put((priority, message))
        
        # Notify subscribers
        for callback in self.subscribers[queue_name]:
            asyncio.create_task(callback(message))
    
    async def subscribe(self, queue_name: str, callback: Any):
        """Subscribe to messages from a queue"""
        if queue_name not in self.subscribers:
            self.subscribers[queue_name] = []
        
        self.subscribers[queue_name].append(callback)
    
    async def consume(self, queue_name: str, max_retries: int = 3) -> Any:
        """Consume a message from a queue with retry logic"""
        if queue_name not in self.queues:
            return None
        
        try:
            priority, message = await self.queues[queue_name].get()
            
            # Simulate message processing
            success = await self._process_message(message)
            
            if not success and max_retries > 0:
                # Retry processing
                await self.publish(queue_name, message, priority + 1)
            elif not success:
                # Move to dead letter queue
                await self.dead_letter_queues[queue_name].put(message)
            
            return message
            
        except Exception as e:
            logger.error(f"Message consumption failed: {str(e)}")
            return None
    
    async def _process_message(self, message: Any) -> bool:
        """Process a message (simulated)"""
        # 90% success rate for simulation
        return time.time() % 10 > 1
