"""
Distributed Tracing Module
Implements OpenTelemetry for distributed tracing across services
"""

from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.trace import Status, StatusCode
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logging.warning("OpenTelemetry not installed. Distributed tracing will be disabled.")

from core.integration_config import integration_settings

logger = logging.getLogger(__name__)


class DistributedTracing:
    """
    Distributed Tracing Manager
    Handles OpenTelemetry setup and span management
    """
    
    def __init__(self):
        self.tracer = None
        self.enabled = integration_settings.enable_distributed_tracing and OPENTELEMETRY_AVAILABLE
        
        if self.enabled:
            self._setup_tracing()
    
    def _setup_tracing(self):
        """Initialize OpenTelemetry tracing"""
        try:
            # Create resource
            resource = Resource.create({
                SERVICE_NAME: integration_settings.tracing_service_name,
                SERVICE_VERSION: integration_settings.service_version,
            })
            
            # Create tracer provider
            provider = TracerProvider(resource=resource)
            
            # Configure exporter based on settings
            if integration_settings.tracing_exporter == "jaeger":
                exporter = JaegerExporter(
                    agent_host_name=integration_settings.jaeger_agent_host,
                    agent_port=integration_settings.jaeger_agent_port,
                )
                provider.add_span_processor(BatchSpanProcessor(exporter))
            
            # Set as global tracer provider
            trace.set_tracer_provider(provider)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            logger.info(
                "Distributed tracing initialized",
                extra={
                    "service_name": integration_settings.tracing_service_name,
                    "exporter": integration_settings.tracing_exporter,
                    "sample_rate": integration_settings.tracing_sample_rate,
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize distributed tracing: {e}")
            self.enabled = False
    
    def instrument_app(self, app):
        """
        Instrument FastAPI application
        
        Args:
            app: FastAPI application instance
        """
        if not self.enabled:
            return
        
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")
    
    def instrument_database(self, engine):
        """
        Instrument SQLAlchemy database
        
        Args:
            engine: SQLAlchemy engine instance
        """
        if not self.enabled:
            return
        
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument SQLAlchemy: {e}")
    
    def instrument_redis(self):
        """Instrument Redis client"""
        if not self.enabled:
            return
        
        try:
            RedisInstrumentor().instrument()
            logger.info("Redis instrumented for tracing")
        except Exception as e:
            logger.error(f"Failed to instrument Redis: {e}")
    
    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: Optional[trace.SpanKind] = None
    ):
        """
        Create a new span
        
        Args:
            name: Span name
            attributes: Span attributes
            kind: Span kind
            
        Yields:
            Span context
        """
        if not self.enabled or not self.tracer:
            # No-op context manager when tracing is disabled
            yield None
            return
        
        with self.tracer.start_as_current_span(name, kind=kind) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                raise
    
    def get_current_span(self):
        """Get current active span"""
        if not self.enabled:
            return None
        return trace.get_current_span()
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add event to current span
        
        Args:
            name: Event name
            attributes: Event attributes
        """
        if not self.enabled:
            return
        
        span = self.get_current_span()
        if span:
            span.add_event(name, attributes or {})
    
    def set_attribute(self, key: str, value: Any):
        """
        Set attribute on current span
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        if not self.enabled:
            return
        
        span = self.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    def record_exception(self, exception: Exception):
        """
        Record exception on current span
        
        Args:
            exception: Exception to record
        """
        if not self.enabled:
            return
        
        span = self.get_current_span()
        if span:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(exception)


# Global tracing instance
tracing = DistributedTracing()


def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace a function
    
    Args:
        name: Span name
        attributes: Span attributes
        
    Returns:
        Decorated function
    """
    def decorator(func):
        if not tracing.enabled:
            return func
        
        def wrapper(*args, **kwargs):
            with tracing.span(name, attributes):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def trace_async_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace an async function
    
    Args:
        name: Span name
        attributes: Span attributes
        
    Returns:
        Decorated function
    """
    def decorator(func):
        if not tracing.enabled:
            return func
        
        async def wrapper(*args, **kwargs):
            with tracing.span(name, attributes):
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
