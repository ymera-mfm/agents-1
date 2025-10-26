# YMERA Learning Agent - Integration Guide

## Overview

The YMERA Learning Agent is the **knowledge hub and learning coordinator** for the entire multi-agent platform. It captures, stores, analyzes, and distributes knowledge across all agents to enable continuous learning and improvement.

## Architecture

```
┌─────────────────┐
│  Manager Agent  │ ← Orchestrates tasks, queries knowledge
└────────┬────────┘
         │
    ┌────▼──────────────────────────────────┐
    │     Learning Agent (Coordinator)      │
    │  - Knowledge Capture                  │
    │  - Pattern Recognition                │
    │  - Knowledge Distribution             │
    │  - Inter-Agent Learning               │
    └────┬──────────────────────────────────┘
         │
    ┌────▼─────────────────────────────────────┐
    │         Specialized Agents                │
    │                                           │
    │  Developer │ Tester │ Debugger │ etc.   │
    │     ↕️         ↕️         ↕️                │
    │  Report outcomes, query knowledge        │
    └──────────────────────────────────────────┘
```

## Key Responsibilities

### 1. Knowledge Capture
- **From Code Analysis**: Extracts patterns, best practices, anti-patterns
- **From Task Outcomes**: Learns what works and what doesn't
- **From User Feedback**: Understands user preferences and expectations
- **From Errors**: Captures resolution patterns for future reference
- **From Agent Interactions**: Learns collaboration patterns

### 2. Knowledge Distribution
- **Automatic**: Pushes relevant knowledge to agents proactively
- **Query-Based**: Agents query for specific knowledge
- **Collaborative**: Facilitates knowledge exchange between agents

### 3. Pattern Recognition
- Identifies success patterns across agents
- Detects failure patterns to prevent recurrence
- Recognizes effective collaboration patterns
- Analyzes code patterns and best practices

### 4. Quality Management
- Tracks knowledge effectiveness
- Updates quality levels based on outcomes
- Validates knowledge through multiple applications
- Maintains confidence scores

---

## Integration Examples

### Example 1: Manager Agent Receives Files from User

```python
# Manager Agent code
import httpx

class ManagerAgent:
    def __init__(self):
        self.learning_api = "http://localhost:8001"
    
    async def handle_user_files(self, files, user_request):
        """When user uploads files and provides instructions"""
        
        # 1. Analyze files
        analysis = await self.analyze_files(files)
        
        # 2. Report to Learning Agent
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.learning_api}/manager/file-received",
                json={
                    "manager_id": self.agent_id,
                    "file_info": {
                        "type": "python_code",
                        "count": len(files),
                        "language": "python"
                    },
                    "analysis": {
                        "complexity": "medium",
                        "issues_found": analysis['issues'],
                        "recommendations": analysis['recommendations']
                    }
                }
            )
        
        # 3. Query for similar solutions
        if analysis['issues']:
            similar = await client.post(
                f"{self.learning_api}/manager/query-solutions",
                json={
                    "problem_description": analysis['issues'][0],
                    "context": {"language": "python"}
                }
            )
            
            solutions = similar.json()['solutions']
            print(f"Found {len(solutions)} similar solutions from past work")
        
        # 4. Get agent recommendations for task
        recommendations = await client.post(
            f"{self.learning_api}/manager/agent-recommendations",
            json={
                "task_type": "code_enhancement",
                "task_description": user_request,
                "available_agents": [
                    "developer_001", 
                    "developer_002",
                    "optimizer_001"
                ]
            }
        )
        
        best_agent = recommendations.json()['top_choice']
        print(f"Recommended agent: {best_agent['agent_id']}")
        print(f"Reason: Success rate {best_agent['success_rate']:.1%}")
        
        # 5. Dispatch task to best agent
        await self.dispatch_task(best_agent['agent_id'], user_request, files)
```

### Example 2: Developer Agent Reports Task Completion

```python
# Developer Agent code
class DeveloperAgent:
    async def complete_task(self, task_id, code_produced, duration):
        """After completing code generation/modification"""
        
        # Report outcome to Learning Agent
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8001/capture/task-outcome",
                json={
                    "agent_id": self.agent_id,
                    "task_id": task_id,
                    "task_type": "code_generation",
                    "outcome": "success",
                    "duration_seconds": duration,
                    "code_produced": code_produced,
                    "errors_encountered": [],
                    "solutions_applied": [
                        "Used async pattern for I/O operations",
                        "Applied error handling best practices"
                    ],
                    "context": {
                        "language": "python",
                        "complexity": "medium"
                    }
                }
            )
        
        print("✓ Task outcome reported for learning")
```

### Example 3: Debugger Agent Resolves Error

```python
# Debugger Agent code
class DebuggerAgent:
    async def resolve_error(self, error_info, fix_applied):
        """After successfully fixing a bug"""
        
        # 1. First, check if similar error was seen before
        async with httpx.AsyncClient() as client:
            # Query for similar errors
            similar_errors = await client.get(
                "http://localhost:8001/query/similar-solutions/"
                f"{hash(error_info['type'])}",
                params={
                    "requesting_agent": self.agent_id,
                    "limit": 5
                }
            )
            
            if similar_errors.json()['found'] > 0:
                print("Similar errors found in knowledge base")
                # Could use these solutions as reference
            
            # 2. Report the resolution for future reference
            await client.post(
                "http://localhost:8001/capture/error-resolution",
                params={
                    "agent_id": self.agent_id,
                    "error_type": error_info['type'],
                    "error_message": error_info['message'],
                    "resolution": fix_applied['description'],
                    "code_fix": fix_applied['code']
                }
            )
        
        print("✓ Error resolution captured and shared with team")
```

### Example 4: Tester Agent Reports Test Results

```python
# Tester Agent code
class TesterAgent:
    async def report_test_results(self, test_suite, results):
        """After running tests"""
        
        # Capture learning from test results
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8001/capture/task-outcome",
                json={
                    "agent_id": self.agent_id,
                    "task_id": test_suite['id'],
                    "task_type": "testing",
                    "outcome": "success" if results['passed'] else "failure",
                    "duration_seconds": results['duration'],
                    "errors_encountered": results['failures'],
                    "solutions_applied": [],
                    "context": {
                        "test_type": test_suite['type'],
                        "coverage": results['coverage'],
                        "tests_run": results['total']
                    }
                }
            )
        
        # If tests failed, query for similar test failures
        if not results['passed']:
            solutions = await client.post(
                "http://localhost:8001/manager/query-solutions",
                json={
                    "problem_description": f"Test failures: {results['failures']}",
                    "context": {"test_type": test_suite['type']}
                }
            )
```

### Example 5: Agent Queries Knowledge Before Task

```python
# Any Agent code
class BaseAgent:
    async def query_relevant_knowledge(self, task_description):
        """Query knowledge base before starting task"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/query/knowledge",
                json={
                    "agent_id": self.agent_id,
                    "query": task_description,
                    "knowledge_types": [
                        "code_pattern",
                        "best_practice",
                        "error_resolution"
                    ],
                    "min_quality": 3,  # Only validated knowledge
                    "limit": 10
                }
            )
            
            knowledge = response.json()['results']
            
            print(f"Found {len(knowledge)} relevant knowledge items")
            
            for item in knowledge:
                print(f"- {item['title']} (Quality: {item['quality']}, "
                      f"Success rate: {item['success_rate']:.1%})")
            
            return knowledge
    
    async def report_knowledge_usage(self, knowledge_id, success):
        """Report whether knowledge was helpful"""
        
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8001/feedback/application",
                json={
                    "knowledge_id": knowledge_id,
                    "agent_id": self.agent_id,
                    "success": success,
                    "feedback": "Applied successfully" if success else "Not applicable",
                    "context": {}
                }
            )
```

### Example 6: Manager Agent Facilitates Collaboration

```python
# Manager Agent code
class ManagerAgent:
    async def setup_agent_collaboration(self, task_requires_multiple_agents):
        """When task requires multiple agents to work together"""
        
        async with httpx.AsyncClient() as client:
            # Get collaboration recommendations
            collab_recs = await client.get(
                f"http://localhost:8001/collaboration/recommendations/"
                f"developer_001",
                params={"objective": task_requires_multiple_agents['goal']}
            )
            
            best_partner = collab_recs.json()['recommendations'][0]
            
            # Setup knowledge exchange
            exchange = await client.post(
                "http://localhost:8001/collaboration/setup",
                json={
                    "initiating_agent": "developer_001",
                    "target_agent": best_partner['agent_id'],
                    "topic": task_requires_multiple_agents['goal'],
                    "objective": "Share complementary knowledge for task"
                }
            )
            
            session = exchange.json()
            
            print(f"Knowledge exchange session created: {session['session_id']}")
            print(f"Agent A can teach: {len(session['exchange']['a_to_b'])} items")
            print(f"Agent B can teach: {len(session['exchange']['b_to_a'])} items")
            
            return session
```

### Example 7: User Feedback Integration

```python
# Manager Agent code
class ManagerAgent:
    async def handle_user_feedback(self, session_id, user_feedback):
        """When user provides feedback on work"""
        
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8001/capture/user-feedback",
                json={
                    "session_id": session_id,
                    "rating": user_feedback['rating'],
                    "feedback_text": user_feedback['comments'],
                    "aspect": user_feedback['aspect'],  # code_quality, speed, etc.
                    "agent_involved": user_feedback.get('agent_id'),
                    "context": {
                        "task_type": user_feedback['task_type'],
                        "complexity": user_feedback['complexity']
                    }
                }
            )
        
        print("✓ User feedback captured for continuous improvement")
```

---

## Knowledge Flow Patterns

### Pattern 1: Proactive Knowledge Distribution

```
Developer Agent creates new solution
    ↓
Learning Agent captures and analyzes
    ↓
Identifies relevant agents automatically
    ↓
Distributes to Developer, Optimizer, Debugger agents
    ↓
Agents receive notification of new knowledge
```

### Pattern 2: Query-Response Pattern

```
Agent encounters problem
    ↓
Queries Learning Agent
    ↓
Learning Agent searches knowledge base
    ↓
Returns ranked relevant knowledge
    ↓
Agent applies knowledge
    ↓
Reports success/failure back to Learning Agent
    ↓
Learning Agent updates knowledge quality
```

### Pattern 3: Collaborative Learning

```
Manager identifies collaboration opportunity
    ↓
Requests Learning Agent to facilitate
    ↓
Learning Agent analyzes both agents' profiles
    ↓
Identifies complementary knowledge
    ↓
Sets up exchange session
    ↓
Agents share knowledge bidirectionally
```

---

## API Endpoints Reference

### Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/status` | GET | System status and metrics |

### Knowledge Capture

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/capture/code-analysis` | POST | Capture learning from code analysis |
| `/capture/task-outcome` | POST | Report task completion outcome |
| `/capture/user-feedback` | POST | Capture user feedback |
| `/capture/error-resolution` | POST | Record error resolution |

### Knowledge Query

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/query/knowledge` | POST | Search knowledge base |
| `/query/similar-solutions/{hash}` | GET | Find similar problems |
| `/query/best-practices/{domain}` | GET | Get domain best practices |

### Feedback & Quality

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/feedback/application` | POST | Report knowledge application outcome |
| `/feedback/validate/{knowledge_id}` | POST | Validate knowledge item |

### Collaboration

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/collaboration/setup` | POST | Setup knowledge exchange |
| `/collaboration/recommendations/{agent_id}` | GET | Get collaboration recommendations |

### Agent Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agents/register` | POST | Register new agent |
| `/agents/{agent_id}/report` | GET | Get learning report |
| `/agents/{agent_id}/recommendations` | GET | Get learning recommendations |

### Analytics

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/analytics/patterns` | GET | Get analyzed patterns |
| `/analytics/knowledge-graph/{id}` | GET | Get knowledge relationships |
| `/analytics/team-learning` | GET | Team-wide analytics |

### Manager-Specific

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/manager/file-received` | POST | Report file reception |
| `/manager/task-dispatch` | POST | Report task dispatch |
| `/manager/agent-recommendations` | POST | Get agent recommendations |
| `/manager/query-solutions` | POST | Query for solutions |

---

## Knowledge Types

### 1. CODE_PATTERN
Reusable code patterns and structures
- **Example**: Async/await patterns, design patterns
- **Quality Metric**: Number of successful reuses

### 2. BUG_SOLUTION
Solutions to specific bugs
- **Example**: "Fixed NullPointerException by adding null check"
- **Quality Metric**: Resolution success rate

### 3. OPTIMIZATION_TECHNIQUE
Performance optimization approaches
- **Example**: "Reduced query time by 80% using index"
- **Quality Metric**: Performance improvement percentage

### 4. TESTING_STRATEGY
Effective testing approaches
- **Example**: "Unit test pattern for async functions"
- **Quality Metric**: Bug catch rate

### 5. BEST_PRACTICE
Proven best practices
- **Example**: "Always validate input before processing"
- **Quality Metric**: Consistency of application

### 6. USER_PREFERENCE
User preferences and expectations
- **Example**: "User prefers detailed comments in code"
- **Quality Metric**: User satisfaction scores

### 7. ERROR_RESOLUTION
Error patterns and resolutions
- **Example**: "ImportError resolved by updating dependencies"
- **Quality Metric**: Resolution time reduction

---

## Quality Levels

1. **EXPERIMENTAL** (Quality 1)
   - Newly captured, unproven
   - Confidence: 0.3-0.5

2. **PROMISING** (Quality 2)
   - Some positive outcomes (2-4 successful uses)
   - Confidence: 0.5-0.7

3. **VALIDATED** (Quality 3)
   - Multiple successful applications (5-9)
   - Confidence: 0.7-0.85

4. **PROVEN** (Quality 4)
   - Consistently successful (10-19)
   - Confidence: 0.85-0.95

5. **GOLD_STANDARD** (Quality 5)
   - Best practice, highly reliable (20+)
   - Confidence: 0.95-1.0

---

## Learning Metrics

### Agent-Level Metrics
- **Learning Velocity**: Knowledge items acquired per day
- **Knowledge Contribution**: Items contributed to team
- **Teaching Score**: Quality of shared knowledge
- **Task Success Rate**: Percentage of successful tasks
- **Improvement Rate**: Rate of skill improvement

### System-Level Metrics
- **Total Knowledge Items**: Size of knowledge base
- **Knowledge Flows**: Inter-agent knowledge transfers
- **Application Success Rate**: How often knowledge helps
- **Pattern Recognition Accuracy**: Quality of insights
- **Team Learning Velocity**: Average across all agents

---

## Best Practices for Integration

### 1. Report Everything
```python
# Good: Report all outcomes
await learning_api.report_outcome(success=True, details=...)
await learning_api.report_outcome(success=False, details=...)

# Bad: Only report successes
if success:
    await learning_api.report_outcome(...)
```

### 2. Query Before Acting
```python
# Good: Check knowledge base first
knowledge = await learning_api.query_knowledge(task)
if knowledge:
    apply_learned_approach(knowledge)
else:
    use_default_approach()

# Bad: Never checking existing knowledge
always_use_default_approach()
```

### 3. Provide Feedback
```python
# Good: Always report whether knowledge helped
knowledge_id = await learning_api.query_knowledge(...)
success = apply_knowledge(knowledge_id)
await learning_api.report_application(knowledge_id, success)

# Bad: Query but never report outcome
knowledge = await learning_api.query_knowledge(...)
apply_knowledge(knowledge)
# No feedback!
```

### 4. Use Context
```python
# Good: Provide rich context
await learning_api.capture_knowledge(
    code=code,
    context={
        "language": "python",
        "framework": "fastapi",
        "complexity": "high",
        "performance": "critical"
    }
)

# Bad: No context
await learning_api.capture_knowledge(code=code)
```

### 5. Collaborate
```python
# Good: Setup collaboration when beneficial
if task_requires_multiple_specializations:
    session = await learning_api.setup_collaboration(
        agent_a, agent_b, objective
    )

# Bad: Agents work in silos
work_alone_always()
```

---

## Deployment Configuration

### Docker Compose Integration
```yaml
services:
  learning-agent:
    build: ./learning-agent
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - ymera-network

  manager-agent:
    build: ./manager-agent
    environment:
      - LEARNING_AGENT_URL=http://learning-agent:8001
    depends_on:
      - learning-agent
```

### Environment Variables
```bash
# Learning Agent
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ymera
REDIS_URL=redis://localhost:6379/0
KNOWLEDGE_RETENTION_DAYS=365
AUTO_DISTRIBUTION=true
PATTERN_ANALYSIS_INTERVAL=1800

# Manager Agent
LEARNING_AGENT_URL=http://localhost:8001
AUTO_QUERY_KNOWLEDGE=true
COLLABORATION_ENABLED=true
```

---

## Monitoring & Observability

### Health Check
```bash
curl http://localhost:8001/health
```

### System Status
```bash
curl http://localhost:8001/status
```

### Real-Time Learning Events
```bash
curl http://localhost:8001/stream/learning-events
```

### Team Analytics Dashboard
```bash
curl http://localhost:8001/analytics/team-learning
```

---

## Troubleshooting

### Knowledge Not Being Captured
1. Check agent is registered: `GET /agents/{agent_id}/report`
2. Verify API calls are successful (check status codes)
3. Review logs for errors
4. Ensure events have proper outcome ("success"/"failure")

### Knowledge Not Being Found
1. Check knowledge quality filters (may be filtering out)
2. Verify search query terms
3. Check if knowledge expired
4. Review applicable_roles and tags

### Low Learning Velocity
1. Agents not reporting outcomes regularly
2. Not enough knowledge variation
3. Check if knowledge distribution is enabled
4. Review collaboration patterns

---

## Summary

The Learning Agent is the **central nervous system** of the YMERA platform, enabling:

✅ **Continuous Learning**: Every action teaches the system
✅ **Knowledge Sharing**: Agents learn from each other
✅ **Pattern Recognition**: Identifies what works and what doesn't
✅ **Quality Improvement**: Knowledge improves over time
✅ **Collaboration**: Facilitates effective teamwork
✅ **Decision Support**: Helps Manager make better choices

By integrating with the Learning Agent, your agents become part of an ever-improving, collaborative AI team.