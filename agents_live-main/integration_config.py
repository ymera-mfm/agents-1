"""
Integration Configuration Module
Settings for seamless integration with broader platform
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Optional
import os


class IntegrationSettings(BaseSettings):
    """
    Integration Settings for platform-wide connectivity
    """
    
    # ============================================================================
    # SERVICE DISCOVERY
    # ============================================================================
    service_name: str = Field(default="ymera-agents", env="SERVICE_NAME")
    service_version: str = Field(default="2.0.0", env="SERVICE_VERSION")
    service_id: Optional[str] = Field(default=None, env="SERVICE_ID")
    
    # ============================================================================
    # EXTERNAL SERVICE ENDPOINTS
    # ============================================================================
    auth_service_url: str = Field(
        default="http://auth-service:8200",
        env="AUTH_SERVICE_URL"
    )
    monitoring_service_url: str = Field(
        default="http://monitoring-service:8300",
        env="MONITORING_SERVICE_URL"
    )
    logging_service_url: str = Field(
        default="http://logging-service:8400",
        env="LOGGING_SERVICE_URL"
    )
    
    # ============================================================================
    # INTEGRATION FEATURES
    # ============================================================================
    enable_distributed_tracing: bool = Field(
        default=True,
        env="ENABLE_DISTRIBUTED_TRACING"
    )
    enable_metrics_export: bool = Field(
        default=True,
        env="ENABLE_METRICS_EXPORT"
    )
    enable_health_checks: bool = Field(
        default=True,
        env="ENABLE_HEALTH_CHECKS"
    )
    enable_service_discovery: bool = Field(
        default=True,
        env="ENABLE_SERVICE_DISCOVERY"
    )
    
    # ============================================================================
    # MESSAGE QUEUE CONFIGURATION
    # ============================================================================
    rabbitmq_url: Optional[str] = Field(
        default=None,
        env="RABBITMQ_URL"
    )
    rabbitmq_exchange: str = Field(
        default="ymera.events",
        env="RABBITMQ_EXCHANGE"
    )
    rabbitmq_queue_prefix: str = Field(
        default="ymera.agents",
        env="RABBITMQ_QUEUE_PREFIX"
    )
    
    kafka_brokers: Optional[List[str]] = Field(
        default=None,
        env="KAFKA_BROKERS"
    )
    kafka_topic_prefix: str = Field(
        default="ymera.agents",
        env="KAFKA_TOPIC_PREFIX"
    )
    
    # ============================================================================
    # DISTRIBUTED TRACING
    # ============================================================================
    tracing_service_name: str = Field(
        default="ymera-agents",
        env="TRACING_SERVICE_NAME"
    )
    tracing_sample_rate: float = Field(
        default=0.1,
        env="TRACING_SAMPLE_RATE"
    )
    tracing_exporter: str = Field(
        default="jaeger",
        env="TRACING_EXPORTER"
    )
    
    # Jaeger
    jaeger_agent_host: str = Field(
        default="localhost",
        env="JAEGER_AGENT_HOST"
    )
    jaeger_agent_port: int = Field(
        default=6831,
        env="JAEGER_AGENT_PORT"
    )
    
    # OTLP
    otlp_endpoint: Optional[str] = Field(
        default=None,
        env="OTLP_ENDPOINT"
    )
    
    # ============================================================================
    # METRICS EXPORT
    # ============================================================================
    metrics_export_interval: int = Field(
        default=60,
        env="METRICS_EXPORT_INTERVAL"
    )
    metrics_export_format: str = Field(
        default="prometheus",
        env="METRICS_EXPORT_FORMAT"
    )
    metrics_endpoint: str = Field(
        default="/metrics",
        env="METRICS_ENDPOINT"
    )
    
    # ============================================================================
    # HEALTH CHECKS
    # ============================================================================
    health_check_interval: int = Field(
        default=30,
        env="HEALTH_CHECK_INTERVAL"
    )
    health_check_timeout: int = Field(
        default=5,
        env="HEALTH_CHECK_TIMEOUT"
    )
    health_check_endpoint: str = Field(
        default="/health",
        env="HEALTH_CHECK_ENDPOINT"
    )
    readiness_endpoint: str = Field(
        default="/ready",
        env="READINESS_ENDPOINT"
    )
    liveness_endpoint: str = Field(
        default="/live",
        env="LIVENESS_ENDPOINT"
    )
    
    # ============================================================================
    # SERVICE REGISTRY
    # ============================================================================
    service_registry_url: Optional[str] = Field(
        default=None,
        env="SERVICE_REGISTRY_URL"
    )
    service_registry_type: str = Field(
        default="consul",
        env="SERVICE_REGISTRY_TYPE"
    )
    service_registry_ttl: int = Field(
        default=30,
        env="SERVICE_REGISTRY_TTL"
    )
    
    # ============================================================================
    # VALIDATORS
    # ============================================================================
    
    @field_validator('tracing_sample_rate')
    @classmethod
    def validate_sample_rate(cls, v):
        """Ensure sample rate is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError('TRACING_SAMPLE_RATE must be between 0 and 1')
        return v
    
    @field_validator('kafka_brokers', mode='before')
    @classmethod
    def parse_kafka_brokers(cls, v):
        """Parse Kafka brokers from string or list"""
        if v is None:
            return None
        if isinstance(v, str):
            return [s.strip() for s in v.split(',') if s.strip()]
        if isinstance(v, list):
            return v
        return None
    
    @field_validator('service_id')
    @classmethod
    def generate_service_id(cls, v, info):
        """Generate service ID if not provided"""
        if v is None:
            import socket
            import uuid
            values = info.data
            hostname = socket.gethostname()
            unique_id = str(uuid.uuid4())[:8]
            return f"{values.get('service_name', 'ymera')}-{hostname}-{unique_id}"
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    def get_message_queue_config(self) -> dict:
        """Get active message queue configuration"""
        if self.rabbitmq_url:
            return {
                "type": "rabbitmq",
                "url": self.rabbitmq_url,
                "exchange": self.rabbitmq_exchange,
                "queue_prefix": self.rabbitmq_queue_prefix
            }
        elif self.kafka_brokers:
            return {
                "type": "kafka",
                "brokers": self.kafka_brokers,
                "topic_prefix": self.kafka_topic_prefix
            }
        return {"type": "none"}
    
    def get_tracing_config(self) -> dict:
        """Get distributed tracing configuration"""
        config = {
            "enabled": self.enable_distributed_tracing,
            "service_name": self.tracing_service_name,
            "sample_rate": self.tracing_sample_rate,
            "exporter": self.tracing_exporter
        }
        
        if self.tracing_exporter == "jaeger":
            config.update({
                "agent_host": self.jaeger_agent_host,
                "agent_port": self.jaeger_agent_port
            })
        elif self.tracing_exporter == "otlp" and self.otlp_endpoint:
            config.update({
                "endpoint": self.otlp_endpoint
            })
        
        return config


# Global integration settings instance
integration_settings = IntegrationSettings()
