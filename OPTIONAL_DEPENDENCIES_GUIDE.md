# Optional Dependencies Guide

## Overview

The YMERA agent system uses **graceful degradation** for optional dependencies. Agents will automatically detect which packages are available and enable/disable features accordingly.

## Architecture

### Pattern

All optional dependencies follow this pattern:

```python
try:
    import expensive_package
    HAS_EXPENSIVE_PACKAGE = True
except ImportError:
    expensive_package = None
    HAS_EXPENSIVE_PACKAGE = False
```

### Usage in Code

Features check availability before use:

```python
if HAS_EXPENSIVE_PACKAGE:
    result = expensive_package.process(data)
else:
    result = fallback_process(data)
```

## Dependency Groups

### Infrastructure & Observability

| Package | Purpose | Used By | Fallback |
|---------|---------|---------|----------|
| `nats-py` | Message broker | base_agent, production_base_agent | Direct calls disabled |
| `redis` | Caching | base_agent, production_base_agent | In-memory cache |
| `asyncpg` | PostgreSQL driver | base_agent, learning_agent | Database operations disabled |
| `consul` | Service discovery | base_agent | Static configuration |
| `opentelemetry-*` | Distributed tracing | Most agents | Logging only |
| `prometheus_client` | Metrics | base_agent, monitoring agents | Basic metrics |
| `structlog` | Structured logging | learning_agent_core | Standard logging |

### Data Science & ML

| Package | Purpose | Used By | Fallback |
|---------|---------|---------|----------|
| `numpy` | Numerical computing | enhancement_agent, examination_agent | Python lists |
| `scikit-learn` | Machine learning | prod_monitoring_agent | Rule-based |
| `sentence-transformers` | Text embeddings | llm_agent | Basic similarity |

### NLP & Language Processing

| Package | Purpose | Used By | Fallback |
|---------|---------|---------|----------|
| `nltk` | NLP toolkit | drafting_agent, editing_agent | Regex patterns |
| `spacy` | Industrial NLP | drafting_agent, editing_agent | Basic parsing |
| `textstat` | Readability metrics | drafting_agent, editing_agent | Simple formulas |
| `language_tool_python` | Grammar checking | editing_agent | Basic rules |
| `tiktoken` | Token counting | llm_agent | Character estimation |

### LLM & Vector Search

| Package | Purpose | Used By | Fallback |
|---------|---------|---------|----------|
| `openai` | OpenAI API | llm_agent | Other providers |
| `anthropic` | Anthropic API | llm_agent | Other providers |
| `qdrant-client` | Vector database | llm_agent | In-memory search |

### Web & Networking

| Package | Purpose | Used By | Fallback |
|---------|---------|---------|----------|
| `aiohttp` | Async HTTP client | monitoring agents, agent_client | HTTP disabled |
| `httpx` | Modern HTTP client | enhanced_learning_agent | HTTP disabled |
| `websockets` | WebSocket protocol | enhanced_learning_agent | Polling |

### Database & Validation

| Package | Purpose | Used By | Fallback |
|---------|---------|---------|----------|
| `sqlalchemy` | ORM | validation_agent, learning_agent | Direct queries |
| `pydantic` | Data validation | validation_agent | Manual validation |
| `jsonschema` | JSON validation | validation_agent | Manual validation |

### System Monitoring

| Package | Purpose | Used By | Fallback |
|---------|---------|---------|----------|
| `psutil` | System utilities | monitoring agents, performance_engine_agent | OS calls |

## Installation Profiles

### Minimal (Core Only)

Required for basic agent functionality:

```bash
pip install pydantic pydantic-settings
```

**Features Enabled:**
- Basic agent imports
- Configuration management
- Minimal validation

**Agents Working:**
- All 23 core agents (imports only)

### Standard (Recommended)

Common dependencies for typical deployment:

```bash
pip install -r requirements-standard.txt
```

Contents of `requirements-standard.txt`:
```
pydantic==2.5.0
pydantic-settings==2.1.0
redis[hiredis]==5.0.1
sqlalchemy[asyncio]==2.0.23
aiohttp==3.9.1
httpx==0.25.2
```

**Features Enabled:**
- Caching
- Database operations
- HTTP clients
- Basic monitoring

**Agents Working:**
- All core agents with basic features

### Full (All Features)

Complete dependency stack:

```bash
pip install -r requirements.txt
```

**Features Enabled:**
- All observability (OpenTelemetry, Prometheus)
- ML & NLP features
- LLM integration
- Advanced monitoring
- All agent capabilities

## Configuration

### Environment Variables

Control which features are enabled in `.env`:

```bash
# Observability
ENABLE_OPENTELEMETRY=true
ENABLE_PROMETHEUS_METRICS=true
ENABLE_STRUCTURED_LOGGING=true

# ML & Data Science
ENABLE_ML_FEATURES=true
ENABLE_VECTOR_SEARCH=true

# NLP Features
ENABLE_NLP_FEATURES=true
ENABLE_GRAMMAR_CHECK=true

# LLM Integration
ENABLE_LLM_INTEGRATION=true
ENABLE_TOKEN_COUNTING=true

# System Monitoring
ENABLE_SYSTEM_MONITORING=true

# Web Services
ENABLE_HTTP_CLIENT=true
ENABLE_WEBSOCKET_SUPPORT=true
```

### Runtime Detection

Agents automatically detect available packages:

```python
import base_agent

# Check what's available
print(f"NATS available: {base_agent.HAS_NATS}")
print(f"Redis available: {base_agent.HAS_REDIS}")
print(f"OpenTelemetry available: {base_agent.HAS_OPENTELEMETRY}")
```

## Testing

### Import Validation

Test that all agents import successfully:

```bash
python -m pytest tests/test_agent_imports_integration.py -v
```

### Feature Detection

Check which features are available:

```bash
python3 << 'EOF'
import sys
agents = ['base_agent', 'llm_agent', 'validation_agent']

for agent in agents:
    mod = __import__(agent)
    print(f"\n{agent}:")
    for attr in dir(mod):
        if attr.startswith('HAS_'):
            value = getattr(mod, attr)
            status = "✅" if value else "❌"
            print(f"  {status} {attr}: {value}")
EOF
```

### Dependency Analysis

Run the analysis tool:

```bash
python3 analyze_agent_dependencies.py
```

## CI/CD Integration

### GitHub Actions Workflow

The repository includes `.github/workflows/agent-import-validation.yml` which:

1. **Validates imports** - Tests that agents import with minimal dependencies
2. **Runs dependency analysis** - Generates dependency report
3. **Executes integration tests** - Validates optional dependency patterns
4. **Generates reports** - Uploads artifacts for review

### Triggering Validation

The workflow runs automatically on:
- Push to main/develop branches (agent files only)
- Pull requests
- Manual dispatch

## Troubleshooting

### Import Errors

**Problem:** Agent fails to import with `ModuleNotFoundError`

**Solution:** Check if it's an optional dependency:
```bash
python3 -c "import agent_name" 2>&1 | grep "No module named"
```

If the module is optional, the agent should handle it gracefully. If not, it's a bug.

### Feature Not Working

**Problem:** Feature is disabled even though package is installed

**Check:**
```python
import agent_name
print(agent_name.HAS_FEATURE_NAME)  # Should be True
```

If False but package is installed, restart Python or check for import errors.

### ValidationError on Learning Agent

**Problem:** `learning_agent` raises Pydantic ValidationError

**Solution:** Configure required environment variables:
```bash
# In .env file
LEARNING_AGENT_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ymera_learning
LEARNING_AGENT_JWT_SECRET_KEY=your-secure-secret-key-minimum-32-chars
```

This is expected behavior - the agent imports successfully but needs configuration.

## Best Practices

### For Developers

1. **Always use try-except** for optional imports
2. **Define HAS_* flags** for feature detection
3. **Provide fallbacks** when features are disabled
4. **Document requirements** in agent docstrings
5. **Test both modes** (with and without dependencies)

### For Deployment

1. **Start minimal** - Install only what you need
2. **Monitor features** - Log which features are enabled
3. **Scale gradually** - Add dependencies as needed
4. **Test locally** - Verify behavior without optional deps
5. **Document choices** - Record why certain features are disabled

### For Testing

1. **Test imports first** - Ensure agents load
2. **Mock optional deps** - Use mocks for testing
3. **Test fallbacks** - Verify behavior without deps
4. **Check feature flags** - Validate HAS_* values
5. **Measure coverage** - Include optional paths

## Migration Guide

### From Hard Dependencies

If you have agents with hard dependencies:

1. **Wrap imports:**
   ```python
   # Before
   import expensive_package
   
   # After
   try:
       import expensive_package
       HAS_EXPENSIVE_PACKAGE = True
   except ImportError:
       expensive_package = None
       HAS_EXPENSIVE_PACKAGE = False
   ```

2. **Add feature checks:**
   ```python
   # Before
   result = expensive_package.process(data)
   
   # After
   if HAS_EXPENSIVE_PACKAGE:
       result = expensive_package.process(data)
   else:
       result = fallback_process(data)
   ```

3. **Update tests:**
   ```python
   # Add to tests
   @pytest.mark.skipif(not HAS_EXPENSIVE_PACKAGE, reason="Requires expensive_package")
   def test_expensive_feature():
       ...
   ```

## FAQ

**Q: Will agents work with no optional dependencies?**
A: Yes! All 23 core agents import successfully with just pydantic/pydantic-settings.

**Q: How do I know which features require which packages?**
A: Check the tables above or run `python3 -c "import agent; print([x for x in dir(agent) if x.startswith('HAS_')])"`

**Q: Can I disable a feature even if the package is installed?**
A: Yes, set `ENABLE_FEATURE_NAME=false` in your `.env` file.

**Q: What's the minimum Python version?**
A: Python 3.11+ (follows YMERA platform requirements)

**Q: How often should I run import validation?**
A: Automatically on every agent file change via CI/CD, manually before releases.

## Support

For issues or questions:
1. Check this guide
2. Run import validation tests
3. Review dependency analysis report
4. Check agent-specific documentation
5. Create an issue with reproduction steps

---

**Last Updated:** 2025-10-20
**Version:** 1.0.0
**Status:** Production Ready
