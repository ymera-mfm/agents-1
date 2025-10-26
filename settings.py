"""
Unified Agent System Configuration
Production-Ready Settings with Environment Variable Support
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Unified system settings"""
    
    # Application
    APP_NAME: str = "Unified Agent System"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://agent_user:secure_password@localhost:5432/unified_agent_db",
        env="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_ECHO: bool = Field(default=False, env="DB_ECHO")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: List[str] = Field(
        default=["localhost:9092"],
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    KAFKA_CONSUMER_GROUP: str = Field(default="unified_agent_group", env="KAFKA_CONSUMER_GROUP")
    
    # Security - CRITICAL: Must be set via environment variable
    SECRET_KEY: str = Field(
        ...,  # Required field - no default
        min_length=32,
        env="SECRET_KEY",
        description="Secret key for encryption (minimum 32 characters)"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        """Validate that SECRET_KEY is secure"""
        if v == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed from default value")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    # API Keys
    API_KEY_HEADER: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    API_KEYS: List[str] = Field(default=[], env="API_KEYS")
    
    # Vault (HashiCorp Vault)
    VAULT_ENABLED: bool = Field(default=False, env="VAULT_ENABLED")
    VAULT_URL: str = Field(default="http://localhost:8200", env="VAULT_URL")
    VAULT_TOKEN: Optional[str] = Field(default=None, env="VAULT_TOKEN")
    VAULT_NAMESPACE: Optional[str] = Field(default=None, env="VAULT_NAMESPACE")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=100 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 100MB
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[".py", ".js", ".java", ".cpp", ".txt", ".md", ".json", ".yaml", ".xml"],
        env="ALLOWED_EXTENSIONS"
    )
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    
    # Agent Configuration
    PROJECT_AGENT_ENABLED: bool = Field(default=True, env="PROJECT_AGENT_ENABLED")
    LEARNING_AGENT_ENABLED: bool = Field(default=True, env="LEARNING_AGENT_ENABLED")
    
    # Project Agent Settings
    PROJECT_QUALITY_THRESHOLD: float = Field(default=0.85, env="PROJECT_QUALITY_THRESHOLD")
    PROJECT_MAX_RETRIES: int = Field(default=3, env="PROJECT_MAX_RETRIES")
    PROJECT_TIMEOUT_SECONDS: int = Field(default=300, env="PROJECT_TIMEOUT_SECONDS")
    
    # Learning Agent Settings
    LEARNING_BATCH_SIZE: int = Field(default=32, env="LEARNING_BATCH_SIZE")
    LEARNING_UPDATE_INTERVAL: int = Field(default=3600, env="LEARNING_UPDATE_INTERVAL")  # 1 hour
    KNOWLEDGE_RETENTION_DAYS: int = Field(default=90, env="KNOWLEDGE_RETENTION_DAYS")
    
    # Vector Database
    VECTOR_DB_TYPE: str = Field(default="chromadb", env="VECTOR_DB_TYPE")  # chromadb, faiss
    VECTOR_DB_PATH: str = Field(default="./vector_db", env="VECTOR_DB_PATH")
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    EMBEDDING_DIMENSION: int = Field(default=384, env="EMBEDDING_DIMENSION")
    
    # Knowledge Graph
    NEO4J_ENABLED: bool = Field(default=False, env="NEO4J_ENABLED")
    NEO4J_URI: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    
    # Machine Learning
    ML_MODEL_DIR: str = Field(default="./models", env="ML_MODEL_DIR")
    ML_DEVICE: str = Field(default="cpu", env="ML_DEVICE")  # cpu, cuda
    ML_BATCH_SIZE: int = Field(default=16, env="ML_BATCH_SIZE")
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # OpenTelemetry
    OTEL_ENABLED: bool = Field(default=False, env="OTEL_ENABLED")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="http://localhost:4317",
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    OTEL_SERVICE_NAME: str = Field(default="unified-agent-system", env="OTEL_SERVICE_NAME")
    
    # Jaeger Tracing
    JAEGER_ENABLED: bool = Field(default=False, env="JAEGER_ENABLED")
    JAEGER_HOST: str = Field(default="localhost", env="JAEGER_HOST")
    JAEGER_PORT: int = Field(default=6831, env="JAEGER_PORT")
    
    # Alerting
    ALERT_ENABLED: bool = Field(default=False, env="ALERT_ENABLED")
    ALERT_WEBHOOK_URL: Optional[str] = Field(default=None, env="ALERT_WEBHOOK_URL")
    ALERT_EMAIL_ENABLED: bool = Field(default=False, env="ALERT_EMAIL_ENABLED")
    ALERT_EMAIL_FROM: Optional[str] = Field(default=None, env="ALERT_EMAIL_FROM")
    ALERT_EMAIL_TO: List[str] = Field(default=[], env="ALERT_EMAIL_TO")
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # Circuit Breaker
    CIRCUIT_BREAKER_ENABLED: bool = Field(default=True, env="CIRCUIT_BREAKER_ENABLED")
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = Field(default=60, env="CIRCUIT_BREAKER_TIMEOUT_SECONDS")
    
    # Retry Policy
    RETRY_MAX_ATTEMPTS: int = Field(default=3, env="RETRY_MAX_ATTEMPTS")
    RETRY_BACKOFF_BASE: float = Field(default=2.0, env="RETRY_BACKOFF_BASE")
    RETRY_BACKOFF_MAX: float = Field(default=60.0, env="RETRY_BACKOFF_MAX")
    
    # WebSocket
    WEBSOCKET_ENABLED: bool = Field(default=True, env="WEBSOCKET_ENABLED")
    WEBSOCKET_PING_INTERVAL: int = Field(default=30, env="WEBSOCKET_PING_INTERVAL")
    WEBSOCKET_PING_TIMEOUT: int = Field(default=10, env="WEBSOCKET_PING_TIMEOUT")
    
    # Background Tasks
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # Backup & Archiving
    BACKUP_ENABLED: bool = Field(default=True, env="BACKUP_ENABLED")
    BACKUP_INTERVAL_HOURS: int = Field(default=24, env="BACKUP_INTERVAL_HOURS")
    BACKUP_RETENTION_DAYS: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    BACKUP_PATH: str = Field(default="./backups", env="BACKUP_PATH")
    
    # Audit Logging
    AUDIT_LOG_ENABLED: bool = Field(default=True, env="AUDIT_LOG_ENABLED")
    AUDIT_LOG_PATH: str = Field(default="./logs/audit", env="AUDIT_LOG_PATH")
    
    # Resource Limits
    MAX_CONCURRENT_TASKS: int = Field(default=100, env="MAX_CONCURRENT_TASKS")
    MAX_MEMORY_MB: int = Field(default=4096, env="MAX_MEMORY_MB")
    MAX_CPU_PERCENT: float = Field(default=80.0, env="MAX_CPU_PERCENT")
    
    # Graceful Shutdown
    SHUTDOWN_TIMEOUT_SECONDS: int = Field(default=30, env="SHUTDOWN_TIMEOUT_SECONDS")
    
    @field_validator("CORS_ORIGINS", mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("KAFKA_BOOTSTRAP_SERVERS", mode='before')
    @classmethod
    def parse_kafka_servers(cls, v):
        if isinstance(v, str):
            return [server.strip() for server in v.split(",")]
        return v
    
    @field_validator("API_KEYS", mode='before')
    @classmethod
    def parse_api_keys(cls, v):
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v
    
    @field_validator("ALLOWED_EXTENSIONS", mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
