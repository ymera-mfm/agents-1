# Enhanced production configuration
class ProductionConfig(BaseConfig):
    # Security
    ENCRYPTION_ALGORITHM = "AES-256-GCM"
    JWT_ALGORITHM = "RS256"
    JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
    JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY")
    SESSION_TIMEOUT = 28800  # 8 hours
    MFA_REQUIRED = True
    PASSWORD_COMPLEXITY = {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": True
    }
    
    # Performance
    DATABASE_POOL_SIZE = 50
    DATABASE_MAX_OVERFLOW = 100
    REDIS_CONNECTION_POOL = 50
    CACHE_TTL = 300  # 5 minutes
    
    # Monitoring
    METRICS_RETENTION_DAYS = 90
    LOG_RETENTION_DAYS = 365
    TRACE_SAMPLING_RATE = 0.1  # 10% sampling in production
    AUDIT_LOG_RETENTION_DAYS = 365
    
    # Compliance
    GDPR_COMPLIANCE_ENABLED = True
    HIPAA_COMPLIANCE_ENABLED = os.getenv("HIPAA_COMPLIANCE_ENABLED", "false").lower() == "true"
    PCI_COMPLIANCE_ENABLED = os.getenv("PCI_COMPLIANCE_ENABLED", "false").lower() == "true"
    
    # External integrations
    SIEM_ENABLED = True
    HSM_ENABLED = os.getenv("HSM_ENABLED", "false").lower() == "true"
    DLP_ENABLED = True
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 1000  # requests per hour
    RATE_LIMIT_BURST = 100  # burst capacity
    
    # Backup
    BACKUP_ENCRYPTION = True
    BACKUP_RETENTION_DAYS = 30
    BACKUP_SCHEDULE = "0 2 * * *"  # Daily at 2 AM

# Configuration validation
def validate_production_config():
    """Validate production configuration"""
    required_env_vars = [
        "JWT_PUBLIC_KEY", "JWT_PRIVATE_KEY",
        "DATABASE_URL", "REDIS_URL",
        "ENCRYPTION_KEY", "SENTRY_DSN"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise ConfigurationError(f"Missing required environment variables: {missing_vars}")
    
    # Validate JWT keys
    try:
        serialization.load_pem_private_key(
            ProductionConfig.JWT_PRIVATE_KEY.encode(),
            password=None,
            backend=default_backend()
        )
        serialization.load_pem_public_key(
            ProductionConfig.JWT_PUBLIC_KEY.encode(),
            backend=default_backend()
        )
    except Exception as e:
        raise ConfigurationError(f"Invalid JWT keys: {e}")

# Initialize configuration
def init_config():
    """Initialize configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        validate_production_config()
        return ProductionConfig()
    elif env == "staging":
        return StagingConfig()
    else:
        return DevelopmentConfig()

# App initialization with enhanced security
def create_app():
    """Create application with enhanced security"""
    app = FastAPI(
        title="YMERA Enterprise Project Agent",
        description="Production-ready enterprise project management system",
        version="1.0.0",
        docs_url="/api/docs" if os.getenv("ENVIRONMENT") != "production" else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if os.getenv("ENVIRONMENT") != "production" else None
    )
    
    # Add security middleware
    app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))
    app.add_middleware(HTTPSRedirectMiddleware)  # Redirect HTTP to HTTPS
    
    # Initialize database
    init_db()
    
    # Initialize monitoring
    init_monitoring()
    
    # Add routes
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
    app.include_router(compliance_router, prefix="/api/compliance", tags=["Compliance"])
    app.include_router(admin_router, prefix="/api/admin", tags=["Administration"])
    
    return app