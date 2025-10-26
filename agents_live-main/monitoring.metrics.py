# monitoring/metrics.py
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest
from prometheus_client.exposition import start_http_server
import asyncio
import logging

logger = logging.getLogger(__name__)

class AdvancedMetricsCollector:
    """Comprehensive metrics collection for all three pillars"""
    
    # Infrastructure metrics
    CPU_USAGE = Gauge('system_cpu_usage', 'CPU usage percentage', ['node', 'pod'])
    MEMORY_USAGE = Gauge('system_memory_usage', 'Memory usage percentage', ['node', 'pod'])
    DISK_USAGE = Gauge('system_disk_usage', 'Disk usage percentage', ['node', 'mountpoint'])
    NETWORK_BYTES = Counter('system_network_bytes', 'Network bytes transferred', ['node', 'direction'])
    
    # Application metrics
    HTTP_REQUESTS = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
    HTTP_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
    DB_QUERY_DURATION = Histogram('db_query_duration_seconds', 'Database query duration', ['query_type', 'table'])
    CACHE_HITS = Counter('cache_hits_total', 'Cache hits', ['cache_type', 'key_pattern'])
    CACHE_MISSES = Counter('cache_misses_total', 'Cache misses', ['cache_type', 'key_pattern'])
    
    # Business metrics
    PROJECTS_CREATED = Counter('business_projects_created', 'Projects created', ['plan_type', 'region'])
    TASKS_COMPLETED = Counter('business_tasks_completed', 'Tasks completed', ['project_type', 'priority'])
    ACTIVE_USERS = Gauge('business_active_users', 'Active users count', ['tier'])
    REVENUE_GENERATED = Counter('business_revenue', 'Revenue generated', ['product', 'region'])
    
    # Error metrics
    ERROR_RATE = Gauge('error_rate', 'Error rate percentage', ['error_type', 'component'])
    RETRY_ATTEMPTS = Counter('retry_attempts', 'Retry attempts', ['operation', 'service'])
    TIMEOUTS = Counter('timeouts_total', 'Timeout occurrences', ['operation', 'service'])
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_server_started = False
    
    def start_metrics_server(self, port=9090):
        """Start Prometheus metrics server"""
        if not self.metrics_server_started:
            start_http_server(port)
            self.metrics_server_started = True
            logger.info(f"Metrics server started on port {port}")
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.HTTP_REQUESTS.labels(method, endpoint, status_code).inc()
        self.HTTP_DURATION.labels(method, endpoint).observe(duration)
    
    def record_db_query(self, query_type: str, table: str, duration: float):
        """Record database query metrics"""
        self.DB_QUERY_DURATION.labels(query_type, table).observe(duration)
    
    def record_business_event(self, event_type: str, labels: Dict[str, str], value: float = 1):
        """Record business metrics"""
        if event_type == "project_created":
            self.PROJECTS_CREATED.labels(**labels).inc(value)
        elif event_type == "task_completed":
            self.TASKS_COMPLETED.labels(**labels).inc(value)
        elif event_type == "revenue":
            self.REVENUE_GENERATED.labels(**labels).inc(value)
    
    def record_error(self, error_type: str, component: str):
        """Record error metrics"""
        self.ERROR_RATE.labels(error_type, component).inc()
    
    async def collect_system_metrics(self):
        """Collect system-level metrics periodically"""
        while True:
            try:
                # Collect CPU, memory, disk, network metrics
                # This would use psutil or node exporter in production
                await self._collect_cpu_metrics()
                await self._collect_memory_metrics()
                await self._collect_disk_metrics()
                await self._collect_network_metrics()
                
                await asyncio.sleep(15)  # Collect every 15 seconds
            except Exception as e:
                logger.error(f"Failed to collect system metrics: {e}")
                await asyncio.sleep(60)  # Backoff on error
    
    async def _collect_cpu_metrics(self):
        """Collect CPU metrics"""
        # Implementation would use psutil or node exporter
        pass
    
    async def _collect_memory_metrics(self):
        """Collect memory metrics"""
        # Implementation would use psutil or node exporter
        pass
    
    async def _collect_disk_metrics(self):
        """Collect disk metrics"""
        # Implementation would use psutil or node exporter
        pass
    
    async def _collect_network_metrics(self):
        """Collect network metrics"""
        # Implementation would use psutil or node exporter
        pass

# Structured logging with correlation IDs
class StructuredLogger:
    def __init__(self):
        self.logger = logging.getLogger("ymera")
        self._configure_logging()
    
    def _configure_logging(self):
        """Configure structured JSON logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s", "trace_id": "%(trace_id)s", "span_id": "%(span_id)s", "service": "ymera-api"}',
            handlers=[logging.StreamHandler()]
        )
    
    def info(self, message: str, trace_id: str = None, span_id: str = None, **kwargs):
        """Log info message with structured data"""
        extra = {"trace_id": trace_id or "", "span_id": span_id or "", **kwargs}
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, trace_id: str = None, span_id: str = None, **kwargs):
        """Log error message with structured data"""
        extra = {"trace_id": trace_id or "", "span_id": span_id or "", **kwargs}
        self.logger.error(message, extra=extra)
    
    def warning(self, message: str, trace_id: str = None, span_id: str = None, **kwargs):
        """Log warning message with structured data"""
        extra = {"trace_id": trace_id or "", "span_id": span_id or "", **kwargs}
        self.logger.warning(message, extra=extra)

# Distributed tracing implementation
class DistributedTracer:
    def __init__(self):
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        from opentelemetry.sdk.resources import Resource
        
        trace.set_tracer_provider(TracerProvider(
            resource=Resource.create({
                "service.name": "ymera-api",
                "service.version": "2.0.0",
                "deployment.environment": "production"
            })
        ))
        
        # Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv('JAEGER_HOST', 'localhost'),
            agent_port=int(os.getenv('JAEGER_PORT', 6831)),
        )
        
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        
        self.tracer = trace.get_tracer(__name__)
    
    def start_span(self, name: str, context: Any = None) -> Any:
        """Start a new span"""
        return self.tracer.start_span(name, context)
    
    def inject_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject tracing context into headers"""
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
        
        propagator = TraceContextTextMapPropagator()
        propagator.inject(headers)
        return headers
    
    def extract_context(self, headers: Dict[str, str]) -> Any:
        """Extract tracing context from headers"""
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
        
        propagator = TraceContextTextMapPropagator()
        return propagator.extract(headers)

# ELK Stack integration for logging
class ELKIntegration:
    def __init__(self):
        self.elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        self.logstash_url = os.getenv('LOGSTASH_URL', 'http://localhost:9600')
        self.kibana_url = os.getenv('KIBANA_URL', 'http://localhost:5601')
        self._init_elasticsearch()
    
    def _init_elasticsearch(self):
        """Initialize Elasticsearch client"""
        try:
            from elasticsearch import Elasticsearch
            self.es = Elasticsearch([self.elasticsearch_url])
            self._create_index_templates()
        except ImportError:
            logger.warning("Elasticsearch not available")
            self.es = None
    
    def _create_index_templates(self):
        """Create Elasticsearch index templates"""
        if not self.es:
            return
        
        # Application logs template
        app_logs_template = {
            "index_patterns": ["ymera-logs-*"],
            "template": {
                "settings": {
                    "number_of_shards": 3,
                    "number_of_replicas": 1,
                    "index.lifecycle.name": "ymera-logs-policy"
                },
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "level": {"type": "keyword"},
                        "message": {"type": "text"},
                        "trace_id": {"type": "keyword"},
                        "span_id": {"type": "keyword"},
                        "service": {"type": "keyword"},
                        "host": {"type": "keyword"},
                        "environment": {"type": "keyword"}
                    }
                }
            }
        }
        
        try:
            self.es.indices.put_template("ymera-logs-template", body=app_logs_template)
        except Exception as e:
            logger.error(f"Failed to create index template: {e}")
    
    async def send_log(self, log_data: Dict[str, Any]):
        """Send log to Elasticsearch"""
        if not self.es:
            return
        
        try:
            index_name = f"ymera-logs-{datetime.utcnow().strftime('%Y.%m.%d')}"
            self.es.index(index=index_name, body=log_data)
        except Exception as e:
            logger.error(f"Failed to send log to Elasticsearch: {e}")
    
    async def query_logs(self, query: Dict[str, Any], size: int = 100) -> List[Dict[str, Any]]:
        """Query logs from Elasticsearch"""
        if not self.es:
            return []
        
        try:
            index_name = f"ymera-logs-*"
            response = self.es.search(index=index_name, body=query, size=size)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            logger.error(f"Failed to query logs: {e}")
            return []