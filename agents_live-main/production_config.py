"""
YMERA Enterprise Platform - Production Configuration
Complete configuration management with environment-based settings
Version: 2.0.0
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Optional
from enum import Enum
import os

class Environment(str, Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.
    
    Environment variables can be prefixed with YMERA_ (e.g., YMERA_DATABASE_URL)
    """
    
    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================
    app_name: str = Field(default="YMERA Enterprise Platform")
    version: str = Field(default="2.0.0")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    
    # Server configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)
    
    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    database_url: str = Field(
        ...,
        description="PostgreSQL database URL"
    )
    database_pool_size: int = Field(default=20, ge=5, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=50)
    database_pool_timeout: int = Field(default=30, ge=5, le=300)
    database_pool_recycle: int = Field(default=3600, ge=300)
    
    @validator('database_url')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError("Database URL must be PostgreSQL")
        return v
    
    # ========================================================================
    # REDIS CACHE CONFIGURATION
    # ========================================================================
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_db: int = Field(default=0, ge=0, le=15)
    redis_password: Optional[str] = Field(default=None)
    redis_ssl: bool = Field(default=False)
    redis_pool_size: int = Field(default=10, ge=1, le=50)
    
    # ========================================================================
    # SECURITY CONFIGURATION
    # ========================================================================
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=60, ge=5, le=1440)
    jwt_refresh_expiration_days: int = Field(default=30, ge=1, le=90)
    
    # Password requirements
    password_min_length: int = Field(default=8, ge=8, le=128)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_digits: bool = Field(default=True)
    password_require_special: bool = Field(default=True)
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    rate_limit_per_hour: int = Field(default=1000, ge=1)
    
    # ========================================================================
    # AI SERVICE CONFIGURATION
    # ========================================================================
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_organization: Optional[str] = Field(default=None)
    openai_default_model: str = Field(default="gpt-4-turbo-preview")
    openai_timeout: int = Field(default=60, ge=10, le=300)
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_default_model: str = Field(default="claude-3-5-sonnet-20241022")
    anthropic_timeout: int = Field(default=60, ge=10, le=300)
    
    # Google
    google_api_key: Optional[str] = Field(default=None)
    google_default_model: str = Field(default="gemini-pro")
    google_timeout: int = Field(default=60, ge=10, le=300)
    
    # Cohere
    cohere_api_key: Optional[str] = Field(default=None)
    cohere_default_model: str = Field(default="command")
    cohere_timeout: int = Field(default=60, ge=10, le=300)
    
    # AI Service settings
    ai_max_retries: int = Field(default=3, ge=1, le=5)
    ai_retry_delay: int = Field(default=1, ge=1, le=10)
    ai_fallback_enabled: bool = Field(default=True)
    
    # ========================================================================
    # GITHUB INTEGRATION
    # ========================================================================
    github_token: Optional[str] = Field(default=None)
    github_api_url: str = Field(default="https://api.github.com")
    github_timeout: int = Field(default=30, ge=10, le=120)
    github_max_file_size: int = Field(default=1_000_000, ge=100_000)
    
    # ========================================================================
    # KIBANA INTEGRATION
    # ========================================================================
    kibana_url: Optional[str] = Field(default=None)
    kibana_username: Optional[str] = Field(default=None)
    kibana_password: Optional[str] = Field(default=None)
    kibana_timeout: int = Field(default=30, ge=10, le=120)
    
    elasticsearch_url: Optional[str] = Field(default=None)
    elasticsearch_username: Optional[str] = Field(default=None)
    elasticsearch_password: Optional[str] = Field(default=None)
    
    # ========================================================================
    # VECTOR DATABASE (PINECONE)
    # ========================================================================
    pinecone_api_key: Optional[str] = Field(default=None)
    pinecone_environment: Optional[str] = Field(default=None)
    pinecone_index_name: str = Field(default="ymera-embeddings")
    pinecone_dimension: int = Field(default=1536, ge=128)
    
    # ========================================================================
    # CORS CONFIGURATION
    # ========================================================================
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
        ]
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # ========================================================================
    # LOGGING CONFIGURATION
    # ========================================================================
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_format: str = Field(default="json")
    log_file: Optional[str] = Field(default=None)
    log_rotation: str = Field(default="1 day")
    log_retention: str = Field(default="30 days")
    
    # ========================================================================
    # MONITORING & METRICS
    # ========================================================================
    metrics_enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090, ge=1024, le=65535)
    
    sentry_dsn: Optional[str] = Field(default=None)
    sentry_environment: Optional[str] = Field(default=None)
    sentry_traces_sample_rate: float = Field(default=0.1, ge=0, le=1)
    
    # ========================================================================
    # PERFORMANCE TUNING
    # ========================================================================
    max_request_size: int = Field(default=10_000_000, ge=1_000_000)  # 10MB
    request_timeout: int = Field(default=300, ge=30, le=600)
    
    # Background tasks
    background_workers: int = Field(default=4, ge=1, le=16)
    background_queue_size: int = Field(default=1000, ge=100)
    
    # Analysis limits
    max_concurrent_analyses: int = Field(default=50, ge=10, le=500)
    analysis_timeout: int = Field(default=300, ge=60, le=3600)
    max_code_size: int = Field(default=500_000, ge=10_000)
    
    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    feature_code_analysis: bool = Field(default=True)
    feature_chat: bool = Field(default=True)
    feature_learning_engine: bool = Field(default=True)
    feature_github_integration: bool = Field(default=True)
    feature_kibana_integration: bool = Field(default=False)
    feature_batch_processing: bool = Field(default=True)
    
    # ========================================================================
    # SECURITY HEADERS & HOSTS
    # ========================================================================
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"]
    )
    trusted_proxies: List[str] = Field(default=["*"])
    
    # ========================================================================
    # STORAGE CONFIGURATION
    # ========================================================================
    storage_backend: str = Field(default="local", regex="^(local|s3|gcs)$")
    storage_path: str = Field(default="./storage")
    
    # S3 configuration
    s3_bucket: Optional[str] = Field(default=None)
    s3_region: Optional[str] = Field(default=None)
    s3_access_key: Optional[str] = Field(default=None)
    s3_secret_key: Optional[str] = Field(default=None)
    
    # ========================================================================
    # EMAIL CONFIGURATION
    # ========================================================================
    email_enabled: bool = Field(default=False)
    smtp_host: Optional[str] = Field(default=None)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_use_tls: bool = Field(default=True)
    email_from: Optional[str] = Field(default=None)
    
    model_config = SettingsConfigDict(
        env_prefix="YMERA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v, info):
        """Enforce production requirements"""
        if v == Environment.PRODUCTION:
            # Ensure critical settings are configured for production
            values = info.data
            if values.get('debug', False):
                raise ValueError("Debug mode must be disabled in production")
        return v
    
    def get_database_url(self, async_driver: bool = True) -> str:
        """Get database URL with optional async driver"""
        url = self.database_url
        if async_driver and not url.startswith('postgresql+asyncpg://'):
            url = url.replace('postgresql://', 'postgresql+asyncpg://')
        return url
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT

# ============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# ============================================================================

class DevelopmentSettings(Settings):
    """Development environment settings"""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: LogLevel = LogLevel.DEBUG
    workers: int = 1
    
    model_config = SettingsConfigDict(env_file=".env.development")

class StagingSettings(Settings):
    """Staging environment settings"""
    environment: Environment = Environment.STAGING
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    
    model_config = SettingsConfigDict(env_file=".env.staging")

class ProductionSettings(Settings):
    """Production environment settings"""
    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    log_level: LogLevel = LogLevel.WARNING
    
    model_config = SettingsConfigDict(env_file=".env.production")

# ============================================================================
# SETTINGS FACTORY
# ============================================================================

def get_settings() -> Settings:
    """
    Get settings based on environment variable.
    
    Set YMERA_ENVIRONMENT to 'development', 'staging', or 'production'
    """
    env = os.getenv("YMERA_ENVIRONMENT", "development").lower()
    
    settings_map = {
        "development": DevelopmentSettings,
        "staging": StagingSettings,
        "production": ProductionSettings
    }
    
    settings_class = settings_map.get(env, Settings)
    return settings_class()

# ============================================================================
# EXAMPLE .env FILE TEMPLATE
# ============================================================================

ENV_TEMPLATE = """
# YMERA Enterprise Platform Configuration
# Copy this file to .env and fill in your values

# Application
YMERA_ENVIRONMENT=development
YMERA_DEBUG=true
YMERA_HOST=0.0.0.0
YMERA_PORT=8000

# Database
YMERA_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ymera

# Redis
YMERA_REDIS_HOST=localhost
YMERA_REDIS_PORT=6379
YMERA_REDIS_PASSWORD=

# Security
YMERA_JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
YMERA_JWT_ALGORITHM=HS256

# OpenAI
YMERA_OPENAI_API_KEY=sk-...
YMERA_OPENAI_ORGANIZATION=

# Anthropic
YMERA_ANTHROPIC_API_KEY=sk-ant-...

# Google
YMERA_GOOGLE_API_KEY=

# Cohere
YMERA_COHERE_API_KEY=

# GitHub
YMERA_GITHUB_TOKEN=ghp_...

# Kibana & Elasticsearch
YMERA_KIBANA_URL=http://localhost:5601
YMERA_KIBANA_USERNAME=elastic
YMERA_KIBANA_PASSWORD=
YMERA_ELASTICSEARCH_URL=http://localhost:9200

# Pinecone
YMERA_PINECONE_API_KEY=
YMERA_PINECONE_ENVIRONMENT=

# CORS
YMERA_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Monitoring
YMERA_SENTRY_DSN=
YMERA_METRICS_ENABLED=true

# Email
YMERA_EMAIL_ENABLED=false
YMERA_SMTP_HOST=smtp.gmail.com
YMERA_SMTP_PORT=587
YMERA_SMTP_USERNAME=
YMERA_SMTP_PASSWORD=
YMERA_EMAIL_FROM=noreply@ymera.com
"""

def generate_env_template(output_file: str = ".env.template"):
    """Generate .env template file"""
    with open(output_file, 'w') as f:
        f.write(ENV_TEMPLATE)
    print(f"Generated environment template: {output_file}")

if __name__ == "__main__":
    # Generate template
    generate_env_template()
    
    # Validate settings
    try:
        settings = get_settings()
        print(f"✓ Configuration valid for environment: {settings.environment}")
        print(f"  - Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'Not configured'}")
        print(f"  - Redis: {settings.redis_host}:{settings.redis_port}")
        print(f"  - Workers: {settings.workers}")
        print(f"  - Debug: {settings.debug}")
    except Exception as e:
        print(f"✗ Configuration error: {str(e)}")
        exit(1)
