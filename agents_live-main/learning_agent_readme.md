# YMERA Learning Agent - Production Documentation

## Overview

The Learning Agent is a comprehensive, production-ready system that manages knowledge acquisition, storage, analysis, and distribution across the YMERA AI platform. It serves as the central intelligence hub for all agents, facilitating continuous learning and knowledge sharing.

## Architecture

### Core Components

1. **Learning Agent (agent.py)** - Main orchestrator
2. **Knowledge Store** - Persistent storage with search capabilities
3. **Knowledge Graph** - Relationship management between knowledge
4. **Pattern Recognizer** - Detects patterns in data and interactions
5. **Insight Generator** - Creates actionable insights from patterns
6. **Knowledge Flow Manager** - Manages knowledge distribution
7. **Recommendation Engine** - Provides intelligent recommendations
8. **Agent Communicator** - Handles agent-to-agent communication

### Database Models

- **KnowledgeEntryModel** - Individual knowledge entries
- **LearningSessionModel** - Learning session tracking
- **PatternModel** - Detected patterns
- **InteractionLogModel** - Agent interaction logs
- **InsightModel** - Generated insights
- **KnowledgeGraphModel** - Graph relationships
- **AgentLearningProfileModel** - Agent learning profiles
- **KnowledgeSubscriptionModel** - Subscription management
- **FeedbackModel** - User and agent feedback
- **ModelVersionModel** - ML model versioning

## Key Features

### 1. Knowledge Management

```python
# Store knowledge
result = await learning_agent.store_knowledge(
    content="Best practice for error handling...",
    category=KnowledgeCategory.BEST_PRACTICES,
    source_agent_id="coding_agent_01",
    tags=["error-handling", "python", "exceptions"],
    metadata={"language": "python", "complexity": "intermediate"}
)

# Retrieve knowledge
knowledge = await learning_agent.retrieve_knowledge(
    query="error handling best practices",
    category=KnowledgeCategory.BEST_PRACTICES,
    limit=10
)

# Update knowledge
await learning_agent.update_knowledge(
    entry_id="knowledge_123",
    content="Updated content...",
    tags=["new-tag"]
)
```

### 2. Learning from Experience

```python
# Learn from task outcomes
await learning_agent.learn_from_outcome(
    task_id="task_456",
    agent_id="coding_agent_01",
    task_type="code_generation",
    outcome="success",
    success=True,
    details={
        "approach": "test-driven-development",
        "metrics": {"lines": 150, "coverage": 95}
    }
)

# Learn from user feedback
await learning_agent.learn_from_user_feedback(
    agent_id="coding_agent_01",
    task_id="task_456",
    rating=5,
    feedback={
        "positives": ["clean code", "good documentation"],
        "improvements": ["performance optimization"]
    }
)

# Log interactions
await learning_agent.log_interaction(
    source_agent_id="coding_agent",
    target_agent_id="testing_agent",
    interaction_type="code_review",
    interaction_data={"files": ["app.py"], "issues": 2},
    outcome="approved"
)
```

### 3. Pattern Recognition

```python
# Detect patterns
patterns = await learning_agent.detect_patterns(
    data_source="interactions",
    time_window=timedelta(days=7)
)

# Extract patterns from content
patterns = await learning_agent.pattern_recognizer.extract_patterns(
    content=code_content,
    category=KnowledgeCategory.CODE_PATTERNS
)
```

### 4. Insight Generation

```python
# Generate insights
insights = await learning_agent.generate_insights(
    context="performance",
    agent_id="coding_agent_01"
)

# Example insight types:
# - TREND: Growing interest in specific topics
# - ANOMALY: Knowledge gaps or unusual patterns
# - OPPORTUNITY: High-value patterns to leverage
# - RISK: Low success rates or outdated knowledge
# - OPTIMIZATION: Performance improvement opportunities
```

### 5. Knowledge Flow

```python
# Subscribe to knowledge updates
subscription_id = await learning_agent.subscribe_to_knowledge(
    agent_id="coding_agent_01",
    categories=[
        KnowledgeCategory.CODE_PATTERNS,
        KnowledgeCategory.BEST_PRACTICES
    ],
    tags=["python", "async"]
)

# Share knowledge with specific agents
await learning_agent.share_knowledge(
    source_agent_id="learning_agent",
    target_agent_ids=["coding_agent_01", "testing_agent_02"],
    knowledge_ids=["knowledge_123", "knowledge_456"]
)

# Request knowledge
await learning_agent.request_knowledge(
    agent_id="coding_agent_01",
    query="async programming patterns",
    urgency="high"
)
```

### 6. Recommendations

```python
# Get recommendations for a task
recommendations = await learning_agent.get_recommendations(
    agent_id="coding_agent_01",
    task_type="api_development",
    context={"language": "python", "framework": "fastapi"}
)

# Get collaborator recommendations
collaborators = await learning_agent.recommendation_engine.recommend_collaborators(
    agent_id="coding_agent_01",
    task_type="code_review"
)

# Get learning path
learning_path = await learning_agent.recommendation_engine.recommend_learning_path(
    agent_id="coding_agent_01"
)
```

### 7. Knowledge Graph

```python
# Get related knowledge
related = await learning_agent.knowledge_graph.get_related_nodes(
    entry_id="knowledge_123",
    max_depth=2,
    limit=10
)

# Find path between knowledge entries
path = await learning_agent.knowledge_graph.find_path(
    source_id="knowledge_123",
    target_id="knowledge_789"
)

# Get knowledge clusters
clusters = await learning_agent.knowledge_graph.get_clusters(
    min_cluster_size=3
)

# Get central nodes
central = await learning_agent.knowledge_graph.get_central_nodes(
    limit=10
)
```

## API Endpoints

### Knowledge Management

- `POST /api/v1/learning-agent/knowledge/store` - Store knowledge
- `POST /api/v1/learning-agent/knowledge/search` - Search knowledge
- `GET /api/v1/learning-agent/knowledge/{entry_id}` - Get knowledge
- `PUT /api/v1/learning-agent/knowledge/{entry_id}` - Update knowledge
- `DELETE /api/v1/learning-agent/knowledge/{entry_id}` - Delete knowledge
- `GET /api/v1/learning-agent/knowledge/category/{category}` - Get by category

### Learning

- `POST /api/v1/learning-agent/learning/outcome` - Learn from outcome
- `POST /api/v1/learning-agent/learning/feedback` - Learn from feedback
- `POST /api/v1/learning-agent/learning/interaction` - Log interaction

### Patterns & Insights

- `POST /api/v1/learning-agent/patterns/detect` - Detect patterns
- `POST /api/v1/learning-agent/insights/generate` - Generate insights

### Knowledge Flow

- `POST /api/v1/learning-agent/knowledge-flow/subscribe` - Subscribe
- `POST /api/v1/learning-agent/knowledge-flow/share` - Share knowledge
- `POST /api/v1/learning-agent/knowledge-flow/request` - Request knowledge
- `GET /api/v1/learning-agent/knowledge-flow/subscriptions/{agent_id}` - Get subscriptions

### Recommendations

- `POST /api/v1/learning-agent/recommendations/get` - Get recommendations
- `GET /api/v1/learning-agent/recommendations/collaborators/{agent_id}` - Recommend collaborators
- `GET /api/v1/learning-agent/recommendations/learning-path/{agent_id}` - Get learning path

### Analytics

- `GET /api/v1/learning-agent/analytics/learning-report` - Learning report
- `GET /api/v1/learning-agent/analytics/agent-profile/{agent_id}` - Agent profile
- `GET /api/v1/learning-agent/analytics/knowledge-statistics` - Statistics
- `GET /api/v1/learning-agent/analytics/knowledge-graph` - Graph stats
- `GET /api/v1/learning-agent/analytics/flow-metrics` - Flow metrics

### Knowledge Graph

- `GET /api/v1/learning-agent/graph/related/{entry_id}` - Related knowledge
- `GET /api/v1/learning-agent/graph/path` - Find path
- `GET /api/v1/learning-agent/graph/clusters` - Get clusters
- `GET /api/v1/learning-agent/graph/central-nodes` - Central nodes

## Integration with Agent Manager

The Learning Agent integrates seamlessly with the Agent Manager:

```python
# In Agent Manager
from learning_agent import LearningAgent

# Initialize learning agent
learning_agent = LearningAgent(
    db_session=db_session,
    cache_manager=cache_manager,
    message_broker=message_broker,
    encryption_manager=encryption_manager,
    config=config
)

await learning_agent.start()

# Agent Manager reports to Learning Agent
await learning_agent.log_interaction(
    source_agent_id=agent_id,
    target_agent_id=None,
    interaction_type="task_execution",
    interaction_data=task_data,
    outcome="success"
)
```

## Deployment

### Prerequisites

```bash
# Required Python packages
sqlalchemy>=2.0.0
asyncpg>=0.28.0
redis>=4.5.0
fastapi>=0.104.0
pydantic>=2.0.0
structlog>=23.0.0
prometheus-client>=0.17.0
```

### Database Setup

```sql
-- Create tables (automated via SQLAlchemy)
-- Tables are created automatically when the agent starts
-- Ensure PostgreSQL is running and configured

-- Required indexes are created automatically
-- Custom indexes can be added for optimization
```

### Configuration

```python
config = {
    # Learning intervals (seconds)
    "learning_interval": 300,      # 5 minutes
    "pattern_interval": 600,       # 10 minutes
    "insight_interval": 1800,      # 30 minutes
    
    # Knowledge retention
    "report_retention_days": 90,
    "log_retention_days": 90,
    "knowledge_retention_days": 365,
    
    # Performance tuning
    "max_knowledge_cache_size": 1000,
    "search_result_limit": 50,
    "graph_traversal_max_depth": 5,
    
    # Learning thresholds
    "min_confidence_score": 0.3,
    "min_pattern_confidence": 0.5,
    "min_success_rate": 0.7,
    
    # Flow management
    "max_subscriptions_per_agent": 20,
    "broadcast_batch_size": 100
}
```

### Starting the Learning Agent

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/ymera_db",
    echo=False,
    pool_size=20,
    max_overflow=40
)

# Create session factory
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def main():
    async with async_session_factory() as session:
        # Initialize learning agent
        learning_agent = LearningAgent(
            db_session=session,
            cache_manager=cache_manager,
            message_broker=message_broker,
            encryption_manager=encryption_manager,
            config=config
        )
        
        # Start learning agent
        await learning_agent.start()
        
        try:
            # Keep running
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            # Graceful shutdown
            await learning_agent.stop()

# Run
asyncio.run(main())
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/ymera
ENV REDIS_URL=redis://redis:6379/0

# Run learning agent
CMD ["python", "-m", "learning_agent.main"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  learning-agent:
    build: .
    environment:
      - DATABASE_URL=postgresql+asyncpg://ymera:password@postgres:5432/ymera_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=ymera
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=ymera_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Monitoring & Metrics

### Prometheus Metrics

The Learning Agent exposes the following metrics:

```python
# Operations
learning_agent_operations_total{operation="store", status="success"}
learning_agent_operations_total{operation="retrieve", status="success"}

# Knowledge base
learning_agent_knowledge_entries{category="code_patterns"}
learning_agent_knowledge_entries{category="best_practices"}

# Learning sessions
learning_agent_sessions_total{type="outcome_based"}
learning_agent_sessions_total{type="feedback_based"}

# Insights
learning_agent_insights_total{type="trend"}
learning_agent_insights_total{type="anomaly"}

# Performance
learning_agent_pattern_detection_seconds
learning_agent_operation_latency_seconds{operation="store"}
```

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/api/v1/learning-agent/health

# Detailed system status
curl http://localhost:8000/api/v1/learning-agent/system/status
```

### Logging

Structured logging with context:

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info("Knowledge stored",
           entry_id=entry_id,
           category=category,
           source_agent=agent_id)

logger.error("Failed to store knowledge",
            error=str(e),
            entry_id=entry_id)
```

## Performance Optimization

### Caching Strategy

1. **Knowledge Cache**: Recently accessed knowledge entries
2. **Search Results Cache**: Frequent search queries
3. **Graph Traversal Cache**: Common graph queries
4. **Recommendation Cache**: Agent recommendations

```python
# Cache configuration
cache_config = {
    "knowledge_ttl": 3600,      # 1 hour
    "search_ttl": 1800,         # 30 minutes
    "graph_ttl": 3600,          # 1 hour
    "recommendation_ttl": 7200  # 2 hours
}
```

### Database Optimization

1. **Indexes**: Created on frequently queried fields
2. **Connection Pooling**: Configured for high concurrency
3. **Query Optimization**: Use of select_in_load for relationships
4. **Partitioning**: Time-based partitioning for logs

### Background Tasks

- **Continuous Learning**: Every 5 minutes
- **Pattern Detection**: Every 10 minutes
- **Insight Generation**: Every 30 minutes
- **Maintenance**: Daily at 3 AM

## Security Considerations

### Data Protection

1. **Encryption**: Sensitive data encrypted at rest
2. **Access Control**: Knowledge access based on agent permissions
3. **Audit Trail**: All operations logged with timestamps
4. **Data Retention**: Automatic cleanup of old data

### API Security

```python
# Authentication middleware
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Security(security)):
    # Verify JWT token
    token = credentials.credentials
    # Validate token logic
    return agent_id
```

## Best Practices

### 1. Knowledge Storage

- **Be Specific**: Include detailed metadata and tags
- **Use Categories**: Properly categorize knowledge
- **Add Context**: Include relevant context in metadata
- **Version Control**: Track knowledge versions

### 2. Learning from Outcomes

- **Immediate Feedback**: Log outcomes immediately
- **Rich Details**: Include comprehensive outcome data
- **Success Metrics**: Define clear success criteria
- **Error Information**: Capture detailed error data

### 3. Pattern Recognition

- **Sufficient Data**: Ensure adequate sample sizes
- **Time Windows**: Use appropriate time windows
- **Validation**: Validate patterns before applying
- **Continuous Update**: Regularly update patterns

### 4. Knowledge Flow

- **Targeted Subscriptions**: Subscribe to relevant categories
- **Filter Appropriately**: Use tags and filters effectively
- **Manage Load**: Avoid overwhelming agents with notifications
- **Feedback Loop**: Provide feedback on knowledge usefulness

## Troubleshooting

### Common Issues

**Issue**: Knowledge not being retrieved

```python
# Check if knowledge exists
knowledge = await learning_agent.knowledge_store.get(entry_id)
if not knowledge:
    logger.error("Knowledge not found", entry_id=entry_id)

# Check search index
await learning_agent.knowledge_store.rebuild_index()
```

**Issue**: Slow pattern detection

```python
# Reduce time window
patterns = await learning_agent.detect_patterns(
    data_source="interactions",
    time_window=timedelta(days=3)  # Reduced from 7
)

# Check data volume
stats = await learning_agent.get_knowledge_statistics()
logger.info("Data volume", total_entries=stats['total_entries'])
```

**Issue**: Memory usage growing

```python
# Clear caches
await learning_agent.cache.clear_pattern("knowledge:*")
await learning_agent.cache.clear_pattern("search:*")

# Optimize knowledge graph
await learning_agent.knowledge_graph.optimize()
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable SQL query logging
engine = create_async_engine(
    database_url,
    echo=True  # Log all SQL queries
)
```

## Testing

### Unit Tests

```python
import pytest
from learning_agent import LearningAgent

@pytest.mark.asyncio
async def test_store_knowledge(learning_agent):
    result = await learning_agent.store_knowledge(
        content="Test knowledge",
        category=KnowledgeCategory.GENERAL,
        source_agent_id="test_agent",
        tags=["test"]
    )
    
    assert result['status'] == 'stored'
    assert 'entry_id' in result

@pytest.mark.asyncio
async def test_retrieve_knowledge(learning_agent):
    # Store first
    store_result = await learning_agent.store_knowledge(
        content="Python async patterns",
        category=KnowledgeCategory.CODE_PATTERNS,
        source_agent_id="test_agent",
        tags=["python", "async"]
    )
    
    # Retrieve
    results = await learning_agent.retrieve_knowledge(
        query="async patterns",
        limit=10
    )
    
    assert len(results) > 0
    assert any(r['entry_id'] == store_result['entry_id'] for r in results)
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_learning_flow(learning_agent):
    # Log interaction
    await learning_agent.log_interaction(
        source_agent_id="agent_1",
        target_agent_id="agent_2",
        interaction_type="collaboration",
        interaction_data={"task": "code_review"},
        outcome="success"
    )
    
    # Detect patterns
    patterns = await learning_agent.detect_patterns(
        data_source="interactions",
        time_window=timedelta(days=1)
    )
    
    # Generate insights
    insights = await learning_agent.generate_insights()
    
    assert len(patterns) >= 0
    assert len(insights) >= 0
```

## Maintenance

### Regular Tasks

1. **Daily**: Cleanup old logs and optimize database
2. **Weekly**: Review knowledge quality and update categories
3. **Monthly**: Analyze learning effectiveness and adjust parameters
4. **Quarterly**: Review and archive old knowledge

### Backup Strategy

```bash
# Database backup
pg_dump -h localhost -U ymera ymera_db > backup_$(date +%Y%m%d).sql

# Knowledge export
curl http://localhost:8000/api/v1/learning-agent/analytics/knowledge-statistics > stats.json
```

## Support & Contributing

For issues, questions, or contributions:
- GitHub: [YMERA Platform Repository]
- Documentation: [docs.ymera.ai/learning-agent]
- Email: support@ymera.ai

## License

Copyright © 2025 YMERA AI Platform. All rights reserved.