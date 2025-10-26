"""
Configuration Management for YMERA Multi-Agent AI System
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application
    app_name: str = "YMERA Multi-Agent AI System"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ymera"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # NATS
    nats_servers: str = "nats://localhost:4222"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    
    # Agent System
    max_agents: int = 1000
    agent_timeout: int = 300
    message_queue_size: int = 10000
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
