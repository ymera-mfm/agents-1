# YMERA Multi-Agent AI System - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Core Concepts](#core-concepts)
4. [Agent Types](#agent-types)
5. [Managing Agents](#managing-agents)
6. [Task Execution](#task-execution)
7. [Projects and Collaboration](#projects-and-collaboration)
8. [Monitoring and Health](#monitoring-and-health)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Introduction

YMERA is an enterprise-grade multi-agent AI system designed to automate complex workflows across software development, DevOps, and business operations. The platform enables you to deploy specialized AI agents that work independently or collaboratively to accomplish tasks.

### Key Features

- **Specialized Agents**: Purpose-built agents for code generation, DevOps automation, monitoring, and more
- **Scalable Architecture**: Handle hundreds of concurrent agents with built-in fault tolerance
- **Real-time Communication**: WebSocket-based real-time updates and agent coordination
- **State Persistence**: Automatic checkpointing ensures agents can recover from failures
- **Enterprise Security**: Built-in authentication, authorization, and audit logging

## Getting Started

### System Requirements

**Minimum Requirements**:
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM
- 2 CPU cores
- 10GB disk space

**Recommended for Production**:
- Kubernetes 1.24+
- 16GB RAM
- 8 CPU cores
- 100GB SSD storage
- Load balancer (nginx, HAProxy)

### Installation

#### Using Docker Compose (Development)

1. Clone the repository:
```bash
git clone https://github.com/ymera/agents.git
cd agents
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the system:
```bash
docker-compose up -d
```

4. Verify installation:
```bash
curl http://localhost:8000/health
```

#### Using Kubernetes (Production)

1. Apply Kubernetes manifests:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployments/
```

2. Verify deployment:
```bash
kubectl get pods -n ymera
```

See `DEPLOYMENT_GUIDE.md` for detailed production deployment instructions.

### First Login

1. Navigate to `http://localhost:3000` (development) or your configured domain
2. Default credentials:
   - **Username**: admin
   - **Password**: changeme
3. **Important**: Change the default password immediately after first login

## Core Concepts

### Agents

Agents are autonomous AI entities that perform specific tasks. Each agent:
- Has a unique ID
- Belongs to a specific type (code generation, DevOps, monitoring, etc.)
- Maintains internal state
- Can communicate with other agents
- Automatically saves checkpoints for fault tolerance

### Agent States

- **Initialized**: Agent created but not started
- **Running**: Agent actively processing tasks
- **Paused**: Agent temporarily suspended
- **Stopped**: Agent gracefully shut down
- **Error**: Agent encountered an unrecoverable error

### Tasks

Tasks are units of work submitted to agents. Each task:
- Has a unique ID
- Belongs to one agent
- Contains type and parameters
- Returns a result or error
- Can be tracked in real-time

### Projects

Projects group related agents and tasks for complex workflows:
- Can contain multiple agents
- Enable agent collaboration
- Track overall progress
- Provide aggregated metrics

## Agent Types

### Code Generation Agent

**Purpose**: Generate, analyze, refactor, and test code across multiple programming languages.

**Capabilities**:
- Generate code from natural language specifications
- Analyze code quality and suggest improvements
- Refactor existing code for better maintainability
- Generate unit tests automatically

**Supported Languages**:
- Python
- JavaScript/TypeScript
- Java
- Go
- Rust
- C++
- C#

**Example Usage**:

1. Create a code generation agent:
   - Navigate to "Agents" → "Create Agent"
   - Select "Code Generation"
   - Configure supported languages
   - Click "Create"

2. Submit a code generation task:
   - Select the agent
   - Click "New Task"
   - Choose "Generate Code"
   - Enter specification: "Create a REST API endpoint for user registration with email validation"
   - Select language: Python
   - Submit

3. View results:
   - Task status updates in real-time
   - Generated code appears in the results panel
   - Download or copy code to your project

**Configuration Options**:
```json
{
  "supported_languages": ["python", "javascript"],
  "checkpoint_interval": 60,
  "max_code_length": 10000
}
```

### DevOps Agent

**Purpose**: Automate infrastructure management, deployments, and monitoring.

**Capabilities**:
- Deploy services to multiple environments
- Provision infrastructure resources
- Monitor service health
- Analyze logs for issues
- Perform automated rollbacks

**Supported Environments**:
- Development
- Staging
- Production

**Example Usage**:

1. **Deploy a Service**:
   ```
   Task Type: Deploy
   Environment: Production
   Service: api-service
   Version: 1.2.0
   Strategy: Rolling update
   ```

2. **Monitor Health**:
   ```
   Task Type: Monitor
   Environment: Production
   Service: api-service
   ```

3. **Analyze Logs**:
   ```
   Task Type: Analyze Logs
   Environment: Production
   Service: api-service
   Time Range: Last 1 hour
   Severity: Error
   ```

**Configuration Options**:
```json
{
  "environments": ["development", "staging", "production"],
  "deployment_timeout": 300,
  "health_check_interval": 30
}
```

### Monitoring Agent

**Purpose**: Track system health, collect metrics, and generate alerts.

**Capabilities**:
- Monitor CPU, memory, disk usage
- Track agent performance
- Generate alerts for anomalies
- Provide real-time dashboards

**Configuration Options**:
```json
{
  "alert_threshold": 80,
  "check_interval": 30,
  "metrics_retention": 86400
}
```

## Managing Agents

### Creating Agents

**Via Web UI**:
1. Navigate to "Agents" page
2. Click "Create Agent" button
3. Select agent type
4. Configure settings
5. Click "Create"

**Via API**:
```bash
curl -X POST https://api.ymera.io/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "code_generation",
    "config": {
      "supported_languages": ["python", "javascript"]
    }
  }'
```

### Starting and Stopping Agents

**Start Agent**:
- Select agent from list
- Click "Start" button
- Agent transitions to "Running" state

**Stop Agent**:
- Select running agent
- Click "Stop" button
- Agent saves checkpoint and transitions to "Stopped" state

**Pause Agent**:
- Select running agent
- Click "Pause" button
- Agent suspends processing but remains in memory

### Configuring Agents

Agents can be configured at creation or updated afterward:

1. Select agent
2. Click "Configure" button
3. Modify settings
4. Click "Save"

**Note**: Some configuration changes require agent restart.

### Deleting Agents

⚠️ **Warning**: Deleting an agent removes all associated data.

1. Stop the agent first
2. Select agent
3. Click "Delete" button
4. Confirm deletion

## Task Execution

### Submitting Tasks

**Via Web UI**:
1. Select an agent
2. Click "New Task"
3. Choose task type
4. Fill in parameters
5. Submit

**Via API**:
```bash
curl -X POST https://api.ymera.io/v1/agents/agent_id/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "generate_code",
    "parameters": {
      "language": "python",
      "specification": "Create a fibonacci function"
    }
  }'
```

### Monitoring Task Progress

Tasks update in real-time:
- **Status bar**: Shows current progress
- **Logs panel**: Displays execution logs
- **Metrics**: Execution time, resource usage

### Task Results

Access task results:
1. From task list: Click on completed task
2. Via API: `GET /agents/{agent_id}/tasks/{task_id}`
3. Via webhook: Automatic notification on completion

**Result Format**:
```json
{
  "task_id": "task_001",
  "status": "completed",
  "result": {
    "status": "success",
    "data": { ... }
  },
  "execution_time": 5.2,
  "completed_at": "2025-10-26T15:00:00Z"
}
```

## Projects and Collaboration

### Creating Projects

Projects organize multiple agents for complex workflows:

1. Navigate to "Projects"
2. Click "Create Project"
3. Enter project details:
   - Name
   - Description
   - Selected agents
4. Click "Create"

### Multi-Agent Coordination

Agents within a project can communicate:

**Sequential Workflow**:
```
Code Gen Agent → DevOps Agent → Monitoring Agent
    ↓                 ↓               ↓
Generate Code    →  Deploy      →  Monitor
```

**Parallel Workflow**:
```
                    ┌→ Agent A →┐
Main Task → Split → ├→ Agent B →┤ → Merge Results
                    └→ Agent C →┘
```

### Project Dashboard

View project-level metrics:
- Overall progress
- Agent status
- Task completion rate
- Resource usage
- Cost tracking (if enabled)

## Monitoring and Health

### System Health Dashboard

Access at `/monitoring` or "Monitoring" page:

**Key Metrics**:
- CPU Usage
- Memory Usage
- Disk Usage
- Network I/O
- Active Agents
- Task Queue Length

### Agent Health

Each agent reports health status:
- **Healthy**: Operating normally
- **Degraded**: Operating with reduced performance
- **Unhealthy**: Not functioning properly

### Alerts

Configure alerts for:
- High resource usage
- Agent failures
- Task failures
- System errors

**Alert Channels**:
- Email
- Slack
- PagerDuty
- Webhook

### Logs

Access logs:
- **System Logs**: Overall platform logs
- **Agent Logs**: Individual agent logs
- **Task Logs**: Specific task execution logs

**Log Levels**:
- ERROR: Critical issues
- WARNING: Potential problems
- INFO: General information
- DEBUG: Detailed debugging (development only)

## Best Practices

### Agent Configuration

1. **Resource Allocation**: Configure appropriate resource limits based on workload
2. **Checkpoint Interval**: Set based on task duration (default: 60 seconds)
3. **Timeout Values**: Configure realistic timeouts for long-running tasks

### Task Management

1. **Task Sizing**: Break large tasks into smaller, manageable units
2. **Error Handling**: Implement retry logic for transient failures
3. **Result Storage**: Archive task results to external storage for long-term retention

### Security

1. **Rotate API Keys**: Regularly rotate authentication tokens
2. **Least Privilege**: Grant minimum necessary permissions
3. **Audit Logs**: Enable and review audit logs regularly
4. **Network Security**: Use TLS/SSL for all communications

### Performance Optimization

1. **Agent Pooling**: Reuse agents for similar tasks instead of creating new ones
2. **Caching**: Enable result caching for repeated tasks
3. **Load Balancing**: Distribute tasks across multiple agents
4. **Resource Monitoring**: Monitor and adjust resource allocations

### Disaster Recovery

1. **Backup Strategy**: Regular backups of agent configurations and state
2. **Checkpoint Recovery**: Test checkpoint restore procedures
3. **High Availability**: Deploy in HA configuration for production
4. **Monitoring**: Set up comprehensive monitoring and alerting

## Troubleshooting

### Agent Won't Start

**Symptoms**: Agent remains in "Initialized" state

**Solutions**:
1. Check logs: `docker logs <container_id>`
2. Verify configuration: Ensure all required fields are set
3. Check dependencies: Verify database and message broker connections
4. Resource availability: Ensure sufficient CPU/memory

### Task Stuck in Queue

**Symptoms**: Task status remains "queued"

**Solutions**:
1. Check agent status: Ensure agent is "Running"
2. Review task queue: Check for backlog
3. Increase agents: Add more agents to handle load
4. Check resources: Verify system resources available

### Performance Issues

**Symptoms**: Slow task execution, high latency

**Solutions**:
1. Monitor resources: Check CPU, memory, disk usage
2. Scale horizontally: Add more agent instances
3. Optimize tasks: Break down large tasks
4. Review logs: Look for performance bottlenecks

### Connection Errors

**Symptoms**: "Connection refused" or timeout errors

**Solutions**:
1. Check network: Verify network connectivity
2. Check firewall: Ensure required ports are open
3. Verify services: Ensure all services are running
4. Review DNS: Check DNS resolution

### Data Loss

**Symptoms**: Missing task results or agent state

**Solutions**:
1. Check checkpoints: Verify checkpoint files exist
2. Review backups: Restore from backup if necessary
3. Check storage: Ensure storage volumes mounted correctly
4. Enable checkpointing: Ensure checkpointing is enabled

## Getting Help

### Documentation

- **API Reference**: `/docs/PUBLIC_API.md`
- **Architecture Guide**: `/docs/ARCHITECTURE.md`
- **Deployment Guide**: `/docs/DEPLOYMENT_GUIDE.md`

### Support Channels

- **Email**: support@ymera.io
- **Forum**: https://community.ymera.io
- **GitHub Issues**: https://github.com/ymera/agents/issues
- **Slack**: https://ymera-community.slack.com

### FAQ

**Q: Can I create custom agent types?**  
A: Yes, extend the `BaseAgent` class and implement required methods. See developer documentation.

**Q: What happens if an agent crashes?**  
A: Agents automatically save checkpoints. On restart, they recover from the last checkpoint.

**Q: How do I scale the system?**  
A: Deploy on Kubernetes with horizontal pod autoscaling. See deployment guide.

**Q: Is there a limit on concurrent agents?**  
A: Default is 1000 agents. Contact support for higher limits.

**Q: How long are task results retained?**  
A: Default retention is 30 days. Configure in settings or use external storage.

---

**Version**: 1.0.0  
**Last Updated**: October 26, 2025  
**Copyright © 2025 YMERA. All rights reserved.**
