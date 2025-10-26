# Production Agent System - Complete Integration Guide

## 🎯 Overview

This guide integrates **all production-ready agents and engines** into a cohesive platform.

### Components Delivered

#### **Engines** (Core Processing)
1. ✅ **Parser Engine v3.0** - Multi-language code parsing
2. ✅ **Generator Engine v3.0** - Intelligent code generation
3. ✅ **Intelligence Engine v3.0** - Agent orchestration & routing

#### **Agents** (Specialized Workers)
1. ✅ **AI Agents System v3.0** - Claude-powered analysis agents
2. ✅ **Metrics Agent v3.0** - System-wide metrics collection
3. ✅ **Validation Agent v3.0** - Data validation & compliance
4. ✅ **Static Analysis Agent v2.0** - Code quality analysis

---

## 📦 Installation

### 1. System Requirements

```bash
# Python 3.10+
python --version

# PostgreSQL 13+
psql --version

# Redis 6+
redis-cli --version

# NATS 2.9+
nats-server --version
```

### 2. Python Dependencies

Create `requirements.txt`:

```txt
# Core
asyncio>=3.4.3
asyncpg>=0.27.0
redis>=4.5.0
nats-py>=2.3.0

# AI & Processing
anthropic>=0.18.0
jinja2>=3.1.2

# Code Analysis (Optional)
esprima>=4.0.1
tree-sitter-languages>=1.7.0

# Validation (Optional)
jsonschema>=4.17.0
pydantic>=2.0.0

# Monitoring
structlog>=23.1.0
opentelemetry-api>=1.20.0
```

Install:

```bash
pip install -r requirements.txt
```

### 3. Database Setup

```sql
-- Create database
CREATE DATABASE agent_platform;

-- Run schemas (execute in order)
\i engines/parser_engine_schema.sql
\i engines/generator_engine_schema.sql
\i engines/intelligence_engine_schema.sql
\i agents/ai_agents_schema.sql
\i agents/metrics_agent_schema.sql
\i agents/validation_agent_schema.sql
\i agents/static_analysis_schema.sql
```

---

## 🚀 Quick Start

### Configuration

Create `.env`:

```bash
# Infrastructure
NATS_URL=nats://localhost:4222
POSTGRES_URL=postgresql://user:password@localhost:5432/agent_platform
REDIS_URL=redis://localhost:6379

# AI Agents (if using)
ANTHROPIC_API_KEY=your_key_here

# Agent Configuration
LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=100
METRICS_BUFFER_SIZE=1000
```

### Start Services

```bash
# Start infrastructure
docker-compose up -d nats postgres redis

# Start Intelligence Engine (orchestrator)
python -m engines.intelligence_engine_prod

# Start Agents (in separate terminals)
python -m agents.ai_agents_production
python -m agents.metrics_agent_production
python -m agents.validation_agent_complete
python -m agents.static_analysis_agent

# Start Engines
python -m engines.parser_engine_prod
python -m engines.generator_engine_prod
```

---

## 🔧 Integration Examples

### Example 1: Parse and Analyze Code

```python
import asyncio
from engines.parser_engine_prod import ParserEngine
from engines.intelligence_engine_prod import IntelligenceEngine

async def analyze_code():
    # Initialize engines
    parser = ParserEngine(max_workers=4)
    intelligence = IntelligenceEngine(max_agents=100)
    
    await intelligence.initialize()
    
    # Parse code
    code = """
    def calculate_sum(a: int, b: int) -> int:
        return a + b
    """
    
    parse_result = await parser.parse(code, "python")
    
    print(f"Parse success: {parse_result.success}")
    print(f"Symbols found: {len(parse_result.symbols)}")
    
    # Route to analysis agent
    decision = await intelligence.route_task(
        task_type="code_analysis",
        requirements={"language": "python"}
    )
    
    print(f"Routed to: {decision.agent_id}")
    print(f"Confidence: {decision.confidence}")

asyncio.run(analyze_code())
```

### Example 2: AI-Powered Code Review

```python
from agents.ai_agents_production import AIAgentOrchestrator

async def ai_code_review():
    # Initialize with database
    db_pool = await asyncpg.create_pool(POSTGRES_URL)
    
    orchestrator = AIAgentOrchestrator(
        api_key=ANTHROPIC_API_KEY,
        db_pool=db_pool
    )
    
    await orchestrator.initialize()
    
    # Automatic agent selection
    response = await orchestrator.analyze_with_best_agent(
        task="Review this function for security issues and performance",
        context={
            "code": your_code,
            "language": "python"
        }
    )
    
    print(f"Analysis: {response.executive_summary}")
    print(f"Recommendations: {len(response.recommendations)}")
    
    # Collaborative analysis
    collab = await orchestrator.collaborative_analysis(
        task="Full security and quality audit",
        agent_types=[
            AgentType.SECURITY_SCANNER,
            AgentType.QUALITY_ASSURANCE,
            AgentType.CODE_ANALYZER
        ]
    )
    
    for agent_type, result in collab.items():
        print(f"{agent_type.value}: {result.confidence_level}")

asyncio.run(ai_code_review())
```

### Example 3: Generate and Validate Code

```python
from engines.generator_engine_prod import GeneratorEngine, GenerationSpec, GenerationType
from agents.validation_agent_complete import ValidationAgent

async def generate_and_validate():
    generator = GeneratorEngine()
    
    # Generate code
    spec = GenerationSpec(
        type=GenerationType.FUNCTION,
        name="process_payment",
        description="Process payment with validation",
        language="python",
        parameters=[
            {"name": "amount", "type": "float", "description": "Payment amount"},
            {"name": "currency", "type": "str", "description": "Currency code"}
        ],
        return_type="bool",
        error_handling=True,
        logging=True
    )
    
    artifact = await generator.generate(
        spec,
        language="python",
        include_tests=True,
        include_docs=True
    )
    
    print(f"Generated code ({artifact.quality_score:.0f}% quality)")
    print(artifact.code)
    
    # Validate generated code
    validation_config = AgentConfig(
        agent_id="validator-001",
        name="validation_agent",
        agent_type="validation"
    )
    
    validator = ValidationAgent(validation_config)
    await validator.start()
    
    validation_result = await validator._validate_data({
        "data": {"code": artifact.code},
        "rule_sets": ["schema", "security"],
        "level": "strict"
    })
    
    print(f"Validation: {validation_result['report']['overall_result']}")

asyncio.run(generate_and_validate())
```

### Example 4: Complete Pipeline

```python
async def complete_pipeline():
    """Complete code analysis, generation, and validation pipeline"""
    
    # 1. Parse existing code
    parser = ParserEngine()
    parse_result = await parser.parse(existing_code, "python")
    
    # 2. Route to Intelligence Engine
    intelligence = IntelligenceEngine()
    await intelligence.initialize()
    
    decision = await intelligence.route_task(
        task_type="code_review",
        requirements={"symbols": len(parse_result.symbols)}
    )
    
    # 3. AI Analysis
    orchestrator = AIAgentOrchestrator(api_key=API_KEY, db_pool=db_pool)
    await orchestrator.initialize()
    
    analysis = await orchestrator.analyze_with_best_agent(
        task="Analyze and suggest improvements",
        context={"parsed_data": parse_result.to_dict()}
    )
    
    # 4. Generate improved code
    generator = GeneratorEngine()
    
    improved_code = await generator.generate(
        specification=analysis.recommendations[0]["action"],
        language="python",
        include_tests=True
    )
    
    # 5. Validate improved code
    validator = ValidationAgent(config)
    await validator.start()
    
    validation = await validator._validate_data({
        "data": {"code": improved_code.code},
        "rule_sets": ["schema", "security", "compliance"]
    })
    
    # 6. Collect metrics
    await nats_client.publish(
        "metrics.pipeline",
        json.dumps({
            "agent_id": "pipeline",
            "metrics": {
                "parse_time": parse_result.parse_time_ms,
                "generation_time": improved_code.generation_time_ms,
                "quality_score": improved_code.quality_score,
                "validation_result": validation["report"]["overall_result"]
            }
        }).encode()
    )
    
    return {
        "original_analysis": analysis,
        "improved_code": improved_code,
        "validation": validation
    }

asyncio.run(complete_pipeline())
```

---

## 📊 Monitoring & Metrics

### Access Metrics

```python
# Get system metrics
async def get_metrics():
    intelligence = IntelligenceEngine()
    await intelligence.initialize()
    
    # System status
    status = intelligence.get_system_status()
    print(f"System state: {status['state']}")
    print(f"Agents: {status['agents']['healthy']}/{status['agents']['total']}")
    
    # Routing performance
    print(f"Success rate: {status['routing']['success_rate']:.2%}")
    print(f"Avg time: {status['routing']['avg_time_ms']:.2f}ms")
    
    # Agent-specific metrics
    parser = ParserEngine()
    parser_metrics = parser.get_metrics()
    print(f"Cache hit rate: {parser_metrics['cache_stats']['hit_rate']:.2%}")
```

### Health Checks

```python
async def health_check():
    # Intelligence Engine
    intelligence = IntelligenceEngine()
    health = await intelligence.health_check()
    print(f"Intelligence: {health['status']} ({health['score']:.2f})")
    
    # Metrics Agent
    metrics_agent = MetricsAgent(config)
    metrics_health = await metrics_agent._get_health_status()
    print(f"Metrics: {metrics_health['health']['overall']}")
```

---

## 🔒 Security Best Practices

### 1. API Key Management

```python
# Use environment variables
import os

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("API key not configured")
```

### 2. Input Validation

```python
# Always validate input before processing
validator = ValidationAgent(config)

result = await validator._validate_data({
    "data": user_input,
    "rule_sets": ["schema", "security"],
    "level": "strict"
})

if result["report"]["overall_result"] != "valid":
    raise ValueError("Invalid input")
```

### 3. Rate Limiting

```python
# Implement rate limiting
from collections import defaultdict
import time

rate_limits = defaultdict(list)

def check_rate_limit(client_id: str, max_per_minute: int = 60):
    now = time.time()
    minute_ago = now - 60
    
    # Clean old requests
    rate_limits[client_id] = [
        t for t in rate_limits[client_id] if t > minute_ago
    ]
    
    if len(rate_limits[client_id]) >= max_per_minute:
        return False
    
    rate_limits[client_id].append(now)
    return True
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue: Connection timeout**
```bash
# Check NATS is running
nats-server -v

# Test connection
nats-sub test &
nats-pub test "hello"
```

**Issue: High memory usage**
```python
# Reduce cache sizes
parser = ParserEngine(cache_size=100)  # Default: 500
intelligence = IntelligenceEngine(decision_cache_size=1000)  # Default: 5000
```

**Issue: Slow parsing**
```python
# Increase workers
parser = ParserEngine(max_workers=16)  # Default: 4
```

**Issue: Database connection errors**
```python
# Check connection pool
async with db_pool.acquire() as conn:
    result = await conn.fetchval("SELECT 1")
    print(f"Database OK: {result}")
```

---

## 📈 Performance Tuning

### Optimize Parser Engine

```python
parser = ParserEngine(
    max_workers=8,           # CPU cores
    cache_size=500,          # Parsed files
    max_file_size_mb=20,     # Skip huge files
    enable_metrics=True
)
```

### Optimize Intelligence Engine

```python
intelligence = IntelligenceEngine(
    max_agents=200,          # Max agents to track
    decision_cache_size=5000,# Routing decisions
    enable_circuit_breakers=True,
    enable_metrics=True
)
```

### Optimize Metrics Agent

```bash
export METRICS_BUFFER_SIZE=2000
export METRICS_BATCH_SIZE=200
export METRICS_BATCH_INTERVAL=15
```

---

## 🧪 Testing

### Unit Tests

```python
import pytest

@pytest.mark.asyncio
async def test_parser_engine():
    parser = ParserEngine()
    
    code = "def hello(): pass"
    result = await parser.parse(code, "python")
    
    assert result.success
    assert len(result.symbols) > 0
    assert result.language == "python"

@pytest.mark.asyncio
async def test_intelligence_routing():
    engine = IntelligenceEngine()
    await engine.initialize()
    
    # Register test agent
    await engine.register_agent("test-agent", {
        "capabilities": ["code_analysis"]
    })
    
    # Route task
    decision = await engine.route_task("code_analysis")
    
    assert decision.agent_id == "test-agent"
    assert decision.confidence > 0.5
```

### Integration Tests

```bash
# Run all tests
pytest tests/ -v --asyncio-mode=auto

# Run specific test
pytest tests/test_integration.py -v

# Run with coverage
pytest --cov=engines --cov=agents tests/
```

---

## 📚 API Reference

See individual component documentation:
- [Parser Engine API](engines/parser_engine_prod.py)
- [Generator Engine API](engines/generator_engine_prod.py)
- [Intelligence Engine API](engines/intelligence_engine_prod.py)
- [AI Agents API](agents/ai_agents_production.py)
- [Metrics Agent API](agents/metrics_agent_production.py)
- [Validation Agent API](agents/validation_agent_complete.py)

---

## 🎓 Best Practices Summary

### ✅ DO:
- Use async/await throughout
- Implement proper error handling
- Cache frequently accessed data
- Monitor metrics and health
- Validate all inputs
- Use connection pooling
- Implement circuit breakers
- Log structured data
- Clean up resources

### ❌ DON'T:
- Block the event loop
- Use SQLite in production
- Store secrets in code
- Ignore health checks
- Skip input validation
- Use synchronous DB calls
- Leave connections open
- Log sensitive data

---

## 📞 Support

For issues or questions:
- GitHub Issues: [your-repo]/issues
- Documentation: [your-docs-site]
- Email: support@your-domain.com

---

## 📄 License

MIT License - See LICENSE file for details

---

**Your production-ready agent platform is now complete and ready for deployment!** 🚀