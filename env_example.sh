# .env.example
# Copy this file to .env and fill in your actual values

# ============================================================================
# AGENT CONFIGURATION
# ============================================================================
AGENT_ID=agent-001
AGENT_NAME=my_agent
AGENT_TYPE=custom
AGENT_VERSION=1.0.0

# ============================================================================
# CORE SERVICES
# ============================================================================

# NATS Message Broker
NATS_URL=nats://localhost:4222
# For production with auth:
# NATS_URL=nats://username:password@nats-server:4222
# For TLS:
# NATS_URL=tls://nats-server:4222

# PostgreSQL Database
POSTGRES_URL=postgresql://agent:secure_password@localhost:5432/agentdb
# Connection pool settings
POSTGRES_MIN_POOL_SIZE=5
POSTGRES_MAX_POOL_SIZE=20
POSTGRES_COMMAND_TIMEOUT=60
POSTGRES_CONNECTION_TIMEOUT=10

# Redis Cache
REDIS_URL=redis://localhost:6379
# With password:
# REDIS_URL=redis://:password@localhost:6379
# With SSL:
# REDIS_URL=rediss://localhost:6380
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5

# ============================================================================
# LLM PROVIDERS
# ============================================================================

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=  # Optional

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini (Optional)
GEMINI_API_KEY=

# Cohere (Optional)
COHERE_API_KEY=

# ============================================================================
# VECTOR DATABASE (RAG)
# ============================================================================

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Optional, for cloud/secured instances
# Collection settings
QDRANT_COLLECTION_SIZE=384
EMBEDDING_MODEL=all-MiniLM-L6-v2
# Alternative models:
# EMBEDDING_MODEL=all-mpnet-base-v2  # Better quality, slower
# EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2  # Multilingual

# ============================================================================
# AGENT BEHAVIOR
# ============================================================================

# Task Management
MAX_CONCURRENT_TASKS=100
REQUEST_TIMEOUT_SECONDS=30
MAX_RETRY_ATTEMPTS=3
RETRY_BASE_DELAY_SECONDS=1.0
RETRY_MAX_DELAY_SECONDS=60.0

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS=3

# Health & Monitoring
STATUS_PUBLISH_INTERVAL=30
HEARTBEAT_INTERVAL=10
HEALTH_CHECK_INTERVAL=60
CONNECTION_CHECK_INTERVAL=30

# Graceful Shutdown
SHUTDOWN_TIMEOUT_SECONDS=30
SHUTDOWN_FORCE_TIMEOUT_SECONDS=10

# ============================================================================
# LLM AGENT SPECIFIC
# ============================================================================

# Conversation Management
MAX_CONVERSATION_AGE=86400  # 24 hours in seconds
MAX_CONVERSATION_MESSAGES=50
MAX_CONVERSATION_TOKENS=100000

# Model Selection
DEFAULT_MODEL=gpt35
FAST_MODEL=claude-haiku
SMART_MODEL=gpt4-turbo
CREATIVE_MODEL=claude-sonnet

# Cost Limits (Optional)
MAX_DAILY_COST=100.0  # USD
MAX_TOKENS_PER_REQUEST=4096
ENABLE_COST_ALERTS=true
COST_ALERT_THRESHOLD=80.0  # Percentage of MAX_DAILY_COST

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json or text
LOG_FILE=/var/log/agents/agent.log  # Optional, leave empty for stdout only
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# ============================================================================
# MONITORING & OBSERVABILITY
# ============================================================================

# Metrics
ENABLE_METRICS=true
METRICS_PORT=8080
METRICS_PATH=/metrics

# Tracing (Optional - for distributed tracing)
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
ENABLE_TRACING=false

# Prometheus (Optional)
PROMETHEUS_PUSHGATEWAY=http://localhost:9091

# ============================================================================
# SECURITY
# ============================================================================

# API Authentication
API_KEY=  # For securing HTTP endpoints
API_SECRET=

# TLS/SSL
ENABLE_TLS=false
TLS_CERT_PATH=/path/to/cert.pem
TLS_KEY_PATH=/path/to/key.pem
TLS_CA_PATH=/path/to/ca.pem

# Rate Limiting
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# ============================================================================
# DEPLOYMENT
# ============================================================================

# Environment
ENVIRONMENT=development  # development, staging, production
DEPLOYMENT_REGION=us-east-1
DATACENTER=dc1

# Resource Limits
MAX_MEMORY_MB=2048
MAX_CPU_CORES=2

# Feature Flags
ENABLE_RAG=true
ENABLE_STREAMING=false
ENABLE_BATCH_PROCESSING=true
ENABLE_AUTO_SCALING=false

# ============================================================================
# DEVELOPMENT & DEBUGGING
# ============================================================================

DEBUG=false
VERBOSE_LOGGING=false
ENABLE_PROFILING=false
PROFILE_OUTPUT=/tmp/agent_profile

# Testing
TEST_MODE=false
MOCK_LLM_RESPONSES=false
MOCK_EXTERNAL_SERVICES=false

# ============================================================================
# CUSTOM AGENT CONFIGURATION
# ============================================================================

# Add your custom configuration variables here
CUSTOM_API_ENDPOINT=
CUSTOM_API_KEY=
CUSTOM_FEATURE_FLAG=true