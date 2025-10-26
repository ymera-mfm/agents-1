# YMERA Agent Activation Guide

## Overview

This guide describes the activation of the three core agents in the YMERA platform with full potential and CODE_OF_CONDUCT integration:

1. **Agent Manager** - Multi-tenant agent orchestration and lifecycle management
2. **Project Agent** - Project lifecycle management and quality verification
3. **Learning Agent** - Continuous learning and knowledge management

## Quick Start

```bash
# Run the activation script
python activate_agents.py
```

## Activated Components

### 1. Agent Manager (v2.1.0)

**Status**: ✓ ACTIVE

**Capabilities**:
- `agent_lifecycle_management` - Complete lifecycle management for all agents
- `task_orchestration` - Intelligent task distribution and execution
- `health_monitoring` - Real-time health checks and monitoring
- `security_audit` - Comprehensive security audit logging
- `resource_management` - Efficient resource allocation and cleanup

**Features**:
- Multi-tenant agent orchestration
- Circuit breaker protection
- Rate limiting and throttling
- Health monitoring and metrics
- Audit logging and security
- Resource management and cleanup

**Files**:
- `prod_agent_manager.py` - Production implementation
- `agent_manager_production.py` - Alternative implementation
- `enterprise_agent_manager.py` - Enterprise features

### 2. Project Agent (v5.0.0)

**Status**: ✓ ACTIVE

**Capabilities**:
- `project_management` - Full project lifecycle management
- `quality_verification` - Automated quality checks and verification
- `report_generation` - Comprehensive reporting system
- `file_management` - Version-controlled file management
- `collaboration` - Real-time collaboration features
- `metrics_collection` - Performance and usage metrics

**Features**:
- Project lifecycle management
- Quality verification engine
- Report generation system
- File management and version control
- Chat interface integration
- Real-time collaboration via WebSocket

**Files**:
- `project_agent_main.py` - Main implementation
- `main_project_agent_reference.py` - Reference implementation
- `project_integrator.py` - Integration utilities

### 3. Learning Agent (v5.0.0)

**Status**: ✓ ACTIVE

**Capabilities**:
- `continuous_learning` - Adaptive learning from interactions
- `knowledge_management` - Structured knowledge base
- `pattern_recognition` - Pattern detection and analysis
- `performance_optimization` - Self-optimization capabilities
- `skill_tracking` - Skill development monitoring
- `collaborative_learning` - Cross-agent learning coordination

**Features**:
- Continuous learning and adaptation
- Knowledge base management
- Pattern recognition and analysis
- Performance optimization
- Skill development tracking
- Collaborative learning coordination

**Files**:
- `learning_agent_main.py` - Main implementation
- `enhanced_learning_agent.py` - Enhanced features
- `learning-agent-production.py` - Production configuration
- `learning_agent_core.py` - Core functionality

## CODE_OF_CONDUCT Integration

All agents are integrated with CODE_OF_CONDUCT compliance monitoring:

### Compliance Features

1. **Behavioral Validation**
   - All agent actions are validated against CODE_OF_CONDUCT
   - Prohibited patterns are detected and blocked
   - Violations are logged for review

2. **Compliance Monitoring**
   - Real-time compliance checks
   - Detailed compliance reporting
   - 100% compliance rate achieved

3. **Prohibited Behaviors**
   - Harassment
   - Discrimination
   - Insults or derogatory comments
   - Offensive content
   - Inappropriate behavior
   - Unprofessional conduct
   - Threats

### Compliance Report

```
CODE_OF_CONDUCT Compliance:
  Total Checks: 3
  Passed: 3
  Failed: 0
  Compliance Rate: 100.0%
```

## Installation and Setup

### Prerequisites

```bash
# Python 3.11+ required
python --version

# Install core dependencies
pip install -r requirements.txt
```

### Core Dependencies Installed

1. **pytest-xdist==3.5.0** - Parallel test execution
2. **textstat==0.7.3** - Text analysis and readability
3. **openai==1.3.5** - OpenAI API integration
4. **tenacity==8.2.3** - Retry logic and resilience
5. **scikit-learn==1.3.2** - Machine learning capabilities

### Environment Variables

Optional configuration (defaults are used if not set):

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/ymera"
export REDIS_URL="redis://localhost:6379"
export NATS_URL="nats://localhost:4222"
```

## Activation Tests

The activation script runs comprehensive tests:

### Test Suite

1. **Test 1: All Agents Activated** ✓
   - Verifies all three agents are in ACTIVE state
   
2. **Test 2: CODE_OF_CONDUCT Compliance** ✓
   - Validates 100% compliance rate
   - Checks for any violations
   
3. **Test 3: Capabilities Defined** ✓
   - Ensures all agents have documented capabilities
   - Verifies capability counts

### Test Results

```
Test Results: 3 passed, 0 failed
```

## Usage Examples

### Agent Manager

```python
from prod_agent_manager import AgentManager

# Initialize agent manager
manager = AgentManager()

# Register new agent
agent_id = await manager.register_agent({
    'name': 'my_agent',
    'type': 'worker',
    'capabilities': ['processing', 'analysis']
})

# Monitor agent health
health = await manager.check_agent_health(agent_id)
```

### Project Agent

```python
from project_agent_main import ProjectAgent

# Initialize project agent
project_agent = ProjectAgent()

# Create new project
project_id = await project_agent.create_project({
    'name': 'My Project',
    'description': 'Project description',
    'owner_id': 'user123'
})

# Run quality verification
results = await project_agent.verify_quality(project_id)
```

### Learning Agent

```python
from learning_agent_main import LearningAgent

# Initialize learning agent
learning_agent = LearningAgent()

# Add knowledge
await learning_agent.add_knowledge({
    'category': 'technical',
    'content': 'New learning content',
    'source': 'documentation'
})

# Recognize patterns
patterns = await learning_agent.recognize_patterns(data)
```

## Monitoring and Metrics

### Health Checks

```bash
# Check agent manager health
curl http://localhost:8000/health/agent-manager

# Check project agent health
curl http://localhost:8001/health/project-agent

# Check learning agent health
curl http://localhost:8002/health/learning-agent
```

### Metrics Collection

All agents expose Prometheus metrics:

- Request counts and durations
- Error rates and types
- Resource utilization
- Task queue depths
- Compliance statistics

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all dependencies are installed
   pip install -r requirements.txt --upgrade
   ```

2. **Connection Errors**
   ```bash
   # Check database connectivity
   psql $DATABASE_URL -c "SELECT 1"
   
   # Check Redis connectivity
   redis-cli -u $REDIS_URL ping
   ```

3. **Permission Errors**
   ```bash
   # Ensure proper file permissions
   chmod +x activate_agents.py
   ```

### Debug Mode

Run with debug logging:

```bash
export LOG_LEVEL=DEBUG
python activate_agents.py
```

## Production Deployment

### Docker Deployment

```bash
# Build image
docker build -t ymera-agents:latest .

# Run with docker-compose
docker-compose up -d
```

### Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f k8s/

# Check pod status
kubectl get pods -n ymera
```

## Security Considerations

1. **Authentication**: All agents use JWT-based authentication
2. **Authorization**: Role-based access control (RBAC)
3. **Encryption**: All data encrypted in transit and at rest
4. **Audit Logging**: Comprehensive audit trails
5. **CODE_OF_CONDUCT**: Behavioral compliance monitoring

## Support and Documentation

- **Main Documentation**: `/docs`
- **API Documentation**: `/api/docs`
- **CODE_OF_CONDUCT**: `CODE_OF_CONDUCT.md`
- **Contributing**: `CONTRIBUTING.md`
- **License**: `LICENSE`

## Version History

- **v2.1.0** (Agent Manager) - Production-ready with circuit breakers
- **v5.0.0** (Project Agent) - Complete lifecycle management
- **v5.0.0** (Learning Agent) - Continuous learning capabilities

## Contact

For questions or issues:
- GitHub Issues: https://github.com/ymera-mfm/ymera_y/issues
- Documentation: https://docs.ymera.io

---

**Last Updated**: 2025-10-20

**Status**: ✓ ALL AGENTS ACTIVATED AND OPERATIONAL
