# Enhanced YMERA Learning Agent - Complete Integration Guide

## 🎯 Overview

The Enhanced Learning Agent is the **central knowledge hub** managing collective intelligence across all YMERA agents with multi-source knowledge acquisition capabilities.

### Key Enhancements

✅ **Collective Agent Knowledge Tracking** - Complete capability profiles for all agents  
✅ **Permission-Based Knowledge Sharing** - Manager approval for sensitive knowledge  
✅ **Multi-Source External Knowledge** - API, WebSocket, Database integration  
✅ **Automated Log Reporting** - Twice daily reports to Agent Manager  
✅ **Abnormal Request Detection** - Real-time security monitoring  
✅ **Communication Manager Integration** - Seamless message routing  

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Agent Manager                            │
│  - Receives logs twice daily                                  │
│  - Approves sensitive knowledge sharing                       │
│  - Approves external knowledge access                         │
│  - Receives abnormal request alerts                           │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ↕ (Approval Requests & Log Reports)
                    │
┌───────────────────▼──────────────────────────────────────────┐
│             Enhanced Learning Agent                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Collective Knowledge Base                             │  │
│  │  - All agent capabilities tracked                      │  │
│  │  - Complete knowledge catalog                          │  │
│  │  - Knowledge flow monitoring                           │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Permission System                                     │  │
│  │  - Check if knowledge shareable                        │  │
│  │  - Request manager approval                            │  │
│  │  - Handle approval responses                           │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  External Knowledge Sources                            │  │
│  │  - Stack Overflow API                                  │  │
│  │  - GitHub API                                           │  │
│  │  - Documentation Search                                │  │
│  │  - Real-time Learning WebSocket                        │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────┬──────────────────────────────────────────┘
                    │
                    ↕ (Route Requests)
                    │
┌───────────────────▼──────────────────────────────────────────┐
│            Communication Manager                              │
│  - Routes knowledge requests from agents                      │
│  - Delivers knowledge responses                               │
│  - Manages agent messaging                                    │
└───────────────────┬──────────────────────────────────────────┘
                    │
      ┌─────────────┴─────────────┬─────────────┬──────────────┐
      ↕                           ↕             ↕              ↕
┌───────────┐  ┌──────────────┐  ┌───────────┐  ┌─────────────┐
│ Developer │  │   Debugger   │  │  Tester   │  │  Manager    │
│   Agent   │  │    Agent     │  │   Agent   │  │   Agent     │
└───────────┘  └──────────────┘  └───────────┘  └─────────────┘
```

---

## 📋 Complete Flow Examples

### Example 1: Agent Requests Knowledge (Internal Found)

```python
# 1. Developer Agent sends request through Communication Manager
async def developer_needs_knowledge():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://comm-manager:8002/send",
            json={
                'from': 'developer_001',
                'to': 'learning_coordinator_001',
                'message_type': 'knowledge_request',
                'payload': {
                    'query': 'best practice for handling async errors',
                    'knowledge_type': 'best_practice',
                    'context': {
                        'language': 'python',
                        'framework': 'asyncio'
                    }
                }
            }
        )

# 2. Communication Manager routes to Learning Agent
# POST /comm/route-request

# 3. Learning Agent processes request
#    - Searches internal knowledge base
#    - Finds matching knowledge
#    - Checks permission (not required for public knowledge)
#    - Returns knowledge directly

# 4. Learning Agent sends response through Communication Manager
# POST http://comm-manager:8002/send
# {
#   'from': 'learning_coordinator_001',
#   'to': 'developer_001',
#   'message_type': 'knowledge_response',
#   'payload': {
#     'success': True,
#     'source': 'internal',
#     'knowledge': { ... }
#   }
# }

# 5. Developer receives knowledge and applies it
```

### Example 2: Agent Requests Knowledge (Permission Required)

```python
# 1. Debugger Agent requests proprietary debugging technique
async def request_proprietary_knowledge():
    response = await client.post(
        "http://learning-agent:8001/knowledge/request",
        json={
            'requesting_agent_id': 'debugger_001',
            'query': 'advanced debugging technique for memory leaks',
            'urgency': 'high'
        }
    )
    # Response: {'success': False, 'pending_approval': True}

# 2. Learning Agent finds knowledge but it's proprietary
#    - Knowledge owned by senior_developer_001
#    - Not in shared_knowledge list
#    - Requires manager approval

# 3. Learning Agent requests approval from Agent Manager
# POST http://agent-manager:8003/approvals/knowledge-sharing
# {
#   'request_id': 'req_12345',
#   'requesting_agent': 'debugger_001',
#   'knowledge_summary': {...},
#   'reason': 'Sensitive knowledge sharing',
#   'urgency': 'high'
# }

# 4. Agent Manager reviews and approves
# POST http://learning-agent:8001/manager/approval-response
# {
#   'request_id': 'req_12345',
#   'approved': True
# }

# 5. Learning Agent fulfills request
# Knowledge sent to debugger_001 through Communication Manager
```

### Example 3: Knowledge Not Found - External Query

```python
# 1. Tester Agent requests testing strategy not in system
async def request_unknown_knowledge():
    response = await client.post(
        "http://learning-agent:8001/knowledge/request",
        json={
            'requesting_agent_id': 'tester_001',
            'query': 'integration testing for GraphQL mutations',
            'knowledge_type': 'testing_strategy'
        }
    )
    # Response: {'success': False, 'not_found': True}

# 2. Learning Agent searches internal knowledge
#    - No matching knowledge found

# 3. Learning Agent requests external access approval
# POST http://agent-manager:8003/approvals/external-access
# {
#   'request_id': 'req_67890',
#   'requesting_agent': 'tester_001',
#   'query': 'integration testing for GraphQL mutations',
#   'reason': 'Knowledge not found internally'
# }

# 4. Agent Manager approves external access
# POST http://learning-agent:8001/manager/approval-response
# {
#   'request_id': 'req_67890',
#   'approved': True
# }

# 5. Learning Agent queries external sources
#    a) Stack Overflow API
#    b) GitHub API (search for test examples)
#    c) Documentation Search

# 6. External knowledge found and stored internally
await learning_agent._store_external_knowledge(
    external_results={
        'source': 'stackoverflow_api',
        'knowledge': {...}
    },
    request=request
)

# 7. Knowledge returned to tester_001
# Now available for future queries from other agents
```

### Example 4: Abnormal Request Pattern Detected

```python
# 1. Agent makes excessive requests (>10 per minute)
for i in range(15):
    await client.post(
        "http://learning-agent:8001/knowledge/request",
        json={
            'requesting_agent_id': 'suspicious_agent_001',
            'query': f'random query {i}'
        }
    )

# 2. Learning Agent detects abnormal pattern
#    - Tracks request frequency per agent
#    - Detects >10 requests in 1 minute
#    - Flags as abnormal

# 3. Immediate alert sent to Agent Manager
# POST http://agent-manager:8003/alerts/abnormal-request
# {
#   'agent_id': 'suspicious_agent_001',
#   'request_count': 15,
#   'alert_level': 'high',
#   'timestamp': '2025-01-01T10:30:00Z'
# }

# 4. All subsequent requests require manager approval
# Agent Manager can:
#  - Block agent temporarily
#  - Require manual approval for each request
#  - Investigate the agent
```

### Example 5: Scheduled Log Reporting (Twice Daily)

```python
# Automatic process running in background

async def _log_reporting_loop():
    """Runs in Learning Agent background"""
    while running:
        current_time = datetime.utcnow()
        
        # Check if 12 hours passed since last log
        if not last_log_sent or (current_time - last_log_sent) >= timedelta(hours=12):
            # Generate comprehensive log
            log = await generate_collective_knowledge_log()
            
            # Log contains:
            # - All agent capabilities
            # - Complete knowledge catalog
            # - Recent requests
            # - Abnormal patterns
            # - External source usage
            
            # Send to Agent Manager
            await send_log_to_agent_manager(log, reason="scheduled")
        
        await asyncio.sleep(3600)  # Check hourly

# Log structure sent to Agent Manager:
{
    'log_id': 'log_abc123',
    'timestamp': '2025-01-01T08:00:00Z',
    'reason': 'scheduled',
    'summary': {
        'total_agents': 15,
        'active_agents': 12,
        'total_knowledge': 1247,
        'agents_by_role': {
            'developer': 5,
            'tester': 3,
            'debugger': 2,
            ...
        }
    },
    'agent_capabilities': {
        'developer_001': {
            'role': 'developer',
            'skills': ['python', 'fastapi', 'async'],
            'expertise_level': {
                'code_pattern': 0.85,
                'best_practice': 0.72
            },
            'owned_knowledge_count': 24,
            'availability': 'available'
        },
        ...
    },
    'knowledge_catalog_summary': {
        'total_items': 1247,
        'by_quality': {
            '1': 120,  # Experimental
            '2': 340,  # Promising
            '3': 520,  # Validated
            '4': 200,  # Proven
            '5': 67    # Gold Standard
        }
    },
    'abnormal_requests': ['req_789'],
    'security_events': []
}
```

---

## 🔧 Agent Integration Examples

### Manager Agent Integration

```python
class ManagerAgent:
    def __init__(self):
        self.learning_agent_url = "http://learning-agent:8001"
        self.comm_manager_url = "http://comm-manager:8002"
    
    async def receive_user_files(self, files, user_request):
        """When user uploads files"""
        
        # 1. Query for similar past solutions
        similar = await self.query_learning_agent_for_solutions(
            user_request['description']
        )
        
        if similar:
            print(f"Found {len(similar)} similar past solutions")
            # Use to inform decision
        
        # 2. Get agent recommendations based on learning
        agents = await self.get_recommended_agents(
            task_type="code_enhancement",
            requirements=user_request['requirements']
        )
        
        best_agent = agents[0]
        print(f"Recommended: {best_agent['agent_id']} "
              f"(success rate: {best_agent['success_rate']})")
        
        # 3. Dispatch task
        await self.dispatch_task(best_agent['agent_id'], files, user_request)
    
    async def query_learning_agent_for_solutions(self, description):
        """Query Learning Agent through Communication Manager"""
        async with httpx.AsyncClient() as client:
            # Send through Communication Manager
            response = await client.post(
                f"{self.comm_manager_url}/send",
                json={
                    'from': self.agent_id,
                    'to': 'learning_coordinator_001',
                    'message_type': 'knowledge_request',
                    'payload': {
                        'query': description,
                        'knowledge_type': 'error_resolution',
                        'urgency': 'normal'
                    }
                }
            )
            
            # Wait for response (handled by Communication Manager)
            return await self.wait_for_response(response.json()['message_id'])
    
    async def get_recommended_agents(self, task_type, requirements):
        """Get agent recommendations from Learning Agent"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.learning_agent_url}/capabilities/search/expertise",
                params={
                    'domain': task_type,
                    'min_expertise': 0.6
                }
            )
            
            return response.json()['agents']
    
    async def handle_abnormal_request_alert(self, alert):
        """Handle abnormal request alert from Learning Agent"""
        agent_id = alert['agent_id']
        request_count = alert['request_count']
        
        # Investigate the agent
        self.logger.warning(
            f"Abnormal behavior from {agent_id}: {request_count} requests/min"
        )
        
        # Take action
        if request_count > 20:
            # Block temporarily
            await self.temporarily_block_agent(agent_id, minutes=15)
        
        # Send approval response for pending requests
        await self.review_pending_requests(agent_id)
```

### Developer Agent Integration

```python
class DeveloperAgent:
    async def start_coding_task(self, task):
        """Before starting, query relevant knowledge"""
        
        # 1. Request knowledge through Communication Manager
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://comm-manager:8002/send",
                json={
                    'from': self.agent_id,
                    'to': 'learning_coordinator_001',
                    'message_type': 'knowledge_request',
                    'payload': {
                        'query': f"best practices for {task['type']}",
                        'knowledge_type': 'best_practice',
                        'context': {
                            'language': task['language'],
                            'complexity': task['complexity']
                        }
                    }
                }
            )
        
        # 2. Wait for knowledge response
        knowledge = await self.wait_for_knowledge_response()
        
        if knowledge['success']:
            # 3. Apply knowledge
            code = await self.generate_code(task, knowledge['knowledge'])
            
            # 4. Report knowledge usage
            await self.report_knowledge_usage(
                knowledge['knowledge']['items'][0]['knowledge_id'],
                success=True
            )
        else:
            # 5. No knowledge available, use default approach
            code = await self.generate_code_default(task)
        
        return code
    
    async def complete_task(self, task, code, success):
        """After completing task, contribute knowledge"""
        
        # Track capability update
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://learning-agent:8001/capabilities/track/contribution",
                json={
                    'agent_id': self.agent_id,
                    'knowledge_id': task['generated_knowledge_id']
                }
            )
        
        # Report outcome for learning
        await client.post(
            "http://learning-agent:8001/capture/task-outcome",
            json={
                'agent_id': self.agent_id,
                'task_id': task['id'],
                'task_type': task['type'],
                'outcome': 'success' if success else 'failure',
                'duration_seconds': task['duration'],
                'code_produced': code,
                'context': task['context']
            }
        )
```

### Debugger Agent Integration

```python
class DebuggerAgent:
    async def investigate_error(self, error_info):
        """Investigate error with Learning Agent help"""
        
        # 1. First check if similar error seen before
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://comm-manager:8002/send",
                json={
                    'from': self.agent_id,
                    'to': 'learning_coordinator_001',
                    'message_type': 'knowledge_request',
                    'payload': {
                        'query': f"{error_info['type']}: {error_info['message']}",
                        'knowledge_type': 'error_resolution',
                        'urgency': 'high'
                    }
                }
            )
        
        knowledge = await self.wait_for_knowledge_response()
        
        if knowledge['success']:
            # Similar error found, try known solutions
            for solution in knowledge['knowledge']['items']:
                if await self.try_solution(solution['content']):
                    # Solution worked!
                    await self.report_success(solution['knowledge_id'])
                    return solution
        
        # 2. No known solution, investigate manually
        solution = await self.manual_investigation(error_info)
        
        # 3. Contribute new solution
        await client.post(
            "http://learning-agent:8001/capture/error-resolution",
            json={
                'agent_id': self.agent_id,
                'error_type': error_info['type'],
                'error_message': error_info['message'],
                'resolution': solution['description'],
                'code_fix': solution['code']
            }
        )
        
        return solution
```

### Tester Agent Integration

```python
class TesterAgent:
    async def plan_test_strategy(self, code_info):
        """Plan testing with learned strategies"""
        
        # Query for testing strategies
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://comm-manager:8002/send",
                json={
                    'from': self.agent_id,
                    'to': 'learning_coordinator_001',
                    'message_type': 'knowledge_request',
                    'payload': {
                        'query': f"testing strategy for {code_info['type']}",
                        'knowledge_type': 'testing_strategy',
                        'context': code_info
                    }
                }
            )
        
        strategies = await self.wait_for_knowledge_response()
        
        if strategies['success']:
            # Use learned strategies
            test_plan = self.create_test_plan_from_knowledge(
                strategies['knowledge']
            )
        else:
            # Use default strategy
            test_plan = self.create_default_test_plan(code_info)
        
        return test_plan
```

---

## 📊 Agent Manager Integration

### Receiving Scheduled Logs

```python
# Agent Manager receives logs twice daily

from fastapi import FastAPI

app = FastAPI()

@app.post("/reports/collective-knowledge")
async def receive_knowledge_log(log_data: Dict[str, Any]):
    """Receive collective knowledge log from Learning Agent"""
    
    log_id = log_data['log_id']
    reason = log_data['reason']
    
    print(f"Received log {log_id} (reason: {reason})")
    
    # Store log
    await store_log_in_database(log_data)
    
    # Analyze for insights
    summary = log_data['summary']
    print(f"Total agents: {summary['total_agents']}")
    print(f"Active agents: {summary['active_agents']}")
    print(f"Total knowledge: {summary['total_knowledge']}")
    
    # Check for issues
    if log_data['abnormal_requests']:
        print(f"⚠️  {len(log_data['abnormal_requests'])} abnormal requests detected")
        await investigate_abnormal_requests(log_data['abnormal_requests'])
    
    if log_data['security_events']:
        print(f"🚨 {len(log_data['security_events'])} security events")
        await handle_security_events(log_data['security_events'])
    
    # Update agent performance metrics
    for agent_id, capability in log_data['agent_capabilities'].items():
        await update_agent_metrics(agent_id, capability)
    
    # Identify learning opportunities
    await identify_learning_opportunities(log_data)
    
    return {'success': True, 'acknowledged': True}
```

### Approving Knowledge Sharing

```python
@app.post("/approvals/knowledge-sharing")
async def approve_knowledge_sharing(request: Dict[str, Any]):
    """Approve or deny knowledge sharing request"""
    
    request_id = request['request_id']
    requesting_agent = request['requesting_agent']
    knowledge_summary = request['knowledge_summary']
    urgency = request['urgency']
    
    # Check agent permissions
    agent = await get_agent(requesting_agent)
    
    # Auto-approve for certain roles/agents
    if agent['role'] in ['manager', 'architect']:
        decision = True
        reason = 'Auto-approved for senior role'
    
    # Check if urgent
    elif urgency == 'critical':
        decision = True
        reason = 'Approved due to critical urgency'
    
    # Require manual approval for others
    else:
        decision = await manual_review(request)
        reason = 'Manual review completed'
    
    # Send decision back to Learning Agent
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://learning-agent:8001/manager/approval-response",
            json={
                'request_id': request_id,
                'approved': decision,
                'reason': reason
            }
        )
    
    return {'success': True, 'decision_sent': True}
```

### Approving External Knowledge Access

```python
@app.post("/approvals/external-access")
async def approve_external_access(request: Dict[str, Any]):
    """Approve or deny external knowledge access"""
    
    request_id = request['request_id']
    requesting_agent = request['requesting_agent']
    query = request['query']
    
    # Check budget/rate limits
    daily_external_queries = await get_external_query_count_today()
    
    if daily_external_queries > 100:
        # Exceeded daily limit
        decision = False
        reason = 'Daily external query limit exceeded'
    
    # Check agent authorization
    elif not await agent_authorized_for_external(requesting_agent):
        decision = False
        reason = 'Agent not authorized for external access'
    
    # Approve if within limits
    else:
        decision = True
        reason = 'Approved within limits'
        await increment_external_query_count()
    
    # Send decision
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://learning-agent:8001/manager/approval-response",
            json={
                'request_id': request_id,
                'approved': decision,
                'reason': reason
            }
        )
    
    return {'success': True}
```

### Handling Abnormal Request Alerts

```python
@app.post("/alerts/abnormal-request")
async def handle_abnormal_request_alert(alert: Dict[str, Any]):
    """Handle abnormal request pattern alert"""
    
    agent_id = alert['agent_id']
    request_count = alert['request_count']
    
    # Log security event
    await log_security_event({
        'type': 'abnormal_request_pattern',
        'agent_id': agent_id,
        'request_count': request_count,
        'timestamp': alert['timestamp']
    })
    
    # Get agent details
    agent = await get_agent(agent_id)
    
    # Take immediate action
    if request_count > 20:
        # Block temporarily
        await temporarily_block_agent(agent_id, duration_minutes=30)
        
        # Notify admin
        await send_admin_notification(
            f"Agent {agent_id} temporarily blocked due to "
            f"excessive requests ({request_count}/min)"
        )
    
    elif request_count > 10:
        # Require approval for next requests
        await set_agent_approval_required(agent_id, duration_minutes=15)
    
    # Request immediate log from Learning Agent
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://learning-agent:8001/manager/command",
            json={
                'command': 'generate_report',
                'parameters': {
                    'reason': 'abnormal_request_investigation',
                    'focus_agent': agent_id
                }
            }
        )
    
    return {'success': True, 'action_taken': True}
```

---

## 🔌 Communication Manager Integration

### Routing Knowledge Requests

```python
# Communication Manager routes messages between agents

from fastapi import FastAPI

app = FastAPI()

@app.post("/send")
async def send_message(message: Dict[str, Any]):
    """Route message from one agent to another"""
    
    from_agent = message['from']
    to_agent = message['to']
    message_type = message['message_type']
    payload = message['payload']
    
    # If it's a knowledge request to Learning Agent
    if (to_agent == 'learning_coordinator_001' and 
        message_type == 'knowledge_request'):
        
        # Route to Learning Agent
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://learning-agent:8001/comm/route-request",
                json={
                    'request_id': str(uuid.uuid4()),
                    'from_agent': from_agent,
                    'to_agent': to_agent,
                    'message_type': message_type,
                    'payload': payload
                }
            )
        
        # Learning Agent will send response back through us
        return {'success': True, 'routed': True}
    
    # Route to other agents
    return await route_to_agent(to_agent, message)
```

---

## 📈 Monitoring & Observability

### Real-time WebSocket Monitoring

```python
# Connect to Learning Agent for real-time updates

import asyncio
import websockets
import json

async def monitor_knowledge_stream():
    uri = "ws://learning-agent:8001/ws/knowledge-stream"
    
    async with websockets.connect(uri) as websocket:
        # Identify as monitoring client
        await websocket.send(json.dumps({
            'agent_id': 'monitor_dashboard',
            'type': 'monitor'
        }))
        
        # Receive updates
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'initial_summary':
                print(f"Connected. Total knowledge: {data['data']['total_knowledge']}")
            
            elif data['type'] == 'new_knowledge':
                print(f"New knowledge added: {data['count']} items")
                for item in data['items']:
                    print(f"  - {item['title']} ({item['type']})")

asyncio.run(monitor_knowledge_stream())
```

### Analytics Queries

```python
# Query analytics from Learning Agent

async def get_system_insights():
    async with httpx.AsyncClient() as client:
        # Get collective summary
        summary = await client.get(
            "http://learning-agent:8001/collective/summary"
        )
        print("Collective Summary:", summary.json())
        
        # Get knowledge flow statistics
        flows = await client.get(
            "http://learning-agent:8001/collective/flow-statistics"
        )
        print("Knowledge Flows:", flows.json())
        
        # Identify knowledge gaps
        gaps = await client.get(
            "http://learning-agent:8001/analytics/knowledge-gaps"
        )
        print("Knowledge Gaps:", gaps.json())
        
        # Get external sources status
        sources = await client.get(
            "http://learning-agent:8001/external-sources/status"
        )
        print("External Sources:", sources.json())
```

---

## 🎯 Key Configuration

### Environment Variables

```bash
# Learning Agent
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/ymera
REDIS_URL=redis://redis:6379/0
COMMUNICATION_MANAGER_URL=http://comm-manager:8002
AGENT_MANAGER_URL=http://agent-manager:8003

# External Sources
STACKOVERFLOW_API_KEY=your_key_here
GITHUB_API_TOKEN=your_token_here
EXTERNAL_LEARNING_WS=ws://learning-source:9001

# Thresholds
ABNORMAL_REQUEST_THRESHOLD=10
LOG_REPORT_INTERVAL_HOURS=12
KNOWLEDGE_RETENTION_DAYS=365
```

### Docker Compose

```yaml
version: '3.8'

services:
  learning-agent:
    build: ./learning-agent
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/ymera
      - REDIS_URL=redis://redis:6379/0
      - COMMUNICATION_MANAGER_URL=http://comm-manager:8002
      - AGENT_MANAGER_URL=http://agent-manager:8003
    depends_on:
      - postgres
      - redis
      - comm-manager
      - agent-manager
    networks:
      - ymera-network

  agent-manager:
    build: ./agent-manager
    ports:
      - "8003:8003"
    networks:
      - ymera-network

  comm-manager:
    build: ./comm-manager
    ports:
      - "8002:8002"
    networks:
      - ymera-network

networks:
  ymera-network:
    driver: bridge
```

---

## ✅ Summary

The Enhanced Learning Agent provides:

1. **Collective Intelligence** - Tracks all agent capabilities and knowledge
2. **Permission System** - Manager approval for sensitive operations
3. **Multi-Source Knowledge** - External API/WebSocket integration
4. **Automated Reporting** - Twice daily logs to Agent Manager
5. **Security Monitoring** - Real-time abnormal pattern detection
6. **Seamless Integration** - Works through Communication Manager

This creates a truly intelligent, self-improving multi-agent system!