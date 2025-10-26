# Production-ready configuration
class ProductionConfig:
    # Security
    ENCRYPTION_ALGORITHM = "AES-256-GCM"
    JWT_ALGORITHM = "RS256"
    JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
    JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY")
    SESSION_TIMEOUT = 28800  # 8 hours
    MFA_REQUIRED = True
    
    # Performance
    DATABASE_POOL_SIZE = 50
    DATABASE_MAX_OVERFLOW = 100
    REDIS_CONNECTION_POOL = 50
    CACHE_TTL = 300
    
    # Microservices
    SERVICE_DISCOVERY_ENABLED = True
    SERVICE_HEALTH_CHECK_INTERVAL = 30
    SERVICE_TIMEOUT = 30
    
    # Event Sourcing
    EVENT_STORE_ENABLED = True
    KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
    SNAPSHOT_INTERVAL = 100  # Create snapshot every 100 events
    
    # Caching
    CACHE_STRATEGY = "multi_level"  # multi_level, redis_only, memory_only
    CACHE_L1_TTL = 60  # 1 minute
    CACHE_L2_TTL = 300  # 5 minutes
    
    # Database
    READ_REPLICA_ENABLED = os.getenv("READ_REPLICA_ENABLED", "false").lower() == "true"
    SHARDING_ENABLED = os.getenv("SHARDING_ENABLED", "false").lower() == "true"
    MATERIALIZED_VIEWS_ENABLED = True
    
    # Monitoring
    METRICS_RETENTION_DAYS = 90
    LOG_RETENTION_DAYS = 365
    TRACE_SAMPLING_RATE = 0.1
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_REQUESTS = 1000  # per hour
    RATE_LIMIT_BURST = 100  # burst capacity
    
    @classmethod
    def validate(cls):
        """Validate production configuration"""
        required_vars = [
            "JWT_PUBLIC_KEY", "JWT_PRIVATE_KEY",
            "DATABASE_URL", "REDIS_URL"
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        # Validate JWT keys
        try:
            from cryptography.hazmat.primitives import serialization
            serialization.load_pem_private_key(
                cls.JWT_PRIVATE_KEY.encode(),
                password=None
            )
            serialization.load_pem_public_key(
                cls.JWT_PUBLIC_KEY.encode()
            )
        except Exception as e:
            raise ValueError(f"Invalid JWT keys: {e}")

# Configuration initialization
def init_config():
    """Initialize configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        ProductionConfig.validate()
        return ProductionConfig()
    elif env == "staging":
        return StagingConfig()
    else:
        return DevelopmentConfig()

# App initialization with microservices
def create_app():
    """Create FastAPI app with microservices architecture"""
    app = FastAPI(
        title="YMERA Enterprise Microservices API",
        description="Production-ready microservices architecture",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json"
    )
    
    # Initialize services
    services = [
        AuthenticationService(),
        ProjectManagementService(),
        TaskOrchestrationService(),
        FileManagementService(),
        NotificationService(),
        AuditService(),
        AnalyticsService(),
        IntegrationService()
    ]
    
    # Register services
    for service in services:
        app.state.services[service.service_name] = service
    
    # Initialize event store and message queue
    app.state.event_store = EventStore()
    app.state.message_queue = MessageQueueSystem()
    app.state.saga_manager = SagaManager()
    
    # Initialize caching and database
    app.state.cache = MultiLevelCache()
    app.state.db = OptimizedDatabaseUtils()
    app.state.connection_pool = ConnectionPoolManager()
    
    # Add routes
    app.include_router(microservice_router, prefix="/api", tags=["Microservices"])
    app.include_router(event_router, prefix="/api/events", tags=["Events"])
    app.include_router(monitoring_router, prefix="/api/monitoring", tags=["Monitoring"])
    
    # Add startup/shutdown events
    @app.on_event("startup")
    async def startup():
        await init_services(app.state.services)
        await app.state.message_queue.retry_dlq_messages()
    
    @app.on_event("shutdown")
    async def shutdown():
        await shutdown_services(app.state.services)
        await app.state.connection_pool.close()
    
    return app

async def init_services(services: Dict[str, MicroService]):
    """Initialize all microservices"""
    for service_name, service in services.items():
        try:
            await service.service_registry.register_service(
                service_name,
                f"http://{service_name}:8000",  # In Kubernetes, this would be service DNS
                tags=["ymera", "microservice"]
            )
            logger.info(f"Service {service_name} registered successfully")
        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {e}")

async def shutdown_services(services: Dict[str, MicroService]):
    """Shutdown all microservices"""
    for service_name, service in services.items():
        try:
            await service.http_client.aclose()
            logger.info(f"Service {service_name} shutdown successfully")
        except Exception as e:
            logger.error(f"Failed to shutdown service {service_name}: {e}")