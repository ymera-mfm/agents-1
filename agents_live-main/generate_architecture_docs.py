#!/usr/bin/env python3
"""
YMERA Platform Architecture Documentation Generator
Creates comprehensive architecture documentation with Mermaid diagrams
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any
from collections import defaultdict


class ArchitectureDocGenerator:
    """Generate comprehensive architecture documentation"""
    
    def __init__(self, inventory_path: Path):
        self.inventory_path = inventory_path
        with open(inventory_path) as f:
            self.inventory = json.load(f)
        self.components = self.inventory['components']
        self.summary = self.inventory['summary']
    
    def generate_system_architecture_diagram(self) -> str:
        """Generate overall system architecture Mermaid diagram"""
        diagram = [
            "```mermaid",
            "graph TB",
            "    subgraph Client Layer",
            "        HTTP[HTTP Clients]",
            "        WS[WebSocket Clients]",
            "    end",
            "    ",
            "    subgraph API Gateway",
            "        Gateway[FastAPI Gateway]",
            "        RateLimit[Rate Limiter]",
            "        Auth[Authentication]",
            "    end",
            "    ",
            "    subgraph Core Services",
            "        Config[Configuration Manager]",
            "        DB[Database Manager]",
            "        Cache[Redis Cache]",
            "    end",
            "    ",
            "    subgraph Agent Layer"
        ]
        
        # Add agents
        agent_types = {
            'learning': 'Learning Agent',
            'llm': 'LLM Agent',
            'communication': 'Communication Agent',
            'drafting': 'Drafting Agent',
            'editing': 'Editing Agent',
            'metrics': 'Metrics Agent',
            'monitoring': 'Monitoring Agent',
            'security': 'Security Agent'
        }
        
        for key, name in agent_types.items():
            diagram.append(f"        {key.upper()}[{name}]")
        
        diagram.extend([
            "    end",
            "    ",
            "    subgraph Engine Layer"
        ])
        
        # Add engines
        engine_types = {
            'workflow': 'Workflow Engine',
            'performance': 'Performance Engine',
            'intelligence': 'Intelligence Engine',
            'optimization': 'Optimization Engine'
        }
        
        for key, name in engine_types.items():
            diagram.append(f"        {key.upper()}_ENG[{name}]")
        
        diagram.extend([
            "    end",
            "    ",
            "    subgraph Data Layer",
            "        PostgreSQL[(PostgreSQL)]",
            "        Redis[(Redis)]",
            "    end",
            "    ",
            "    %% Connections",
            "    HTTP --> Gateway",
            "    WS --> Gateway",
            "    Gateway --> RateLimit",
            "    RateLimit --> Auth",
            "    Auth --> Config",
            "    ",
            "    Config --> DB",
            "    Config --> Cache",
            "    ",
            "    DB --> PostgreSQL",
            "    Cache --> Redis",
            "    ",
            "    %% Agent Connections",
        ])
        
        for key in agent_types.keys():
            diagram.append(f"    Gateway --> {key.upper()}")
            diagram.append(f"    {key.upper()} --> DB")
        
        diagram.append("    ")
        diagram.append("    %% Engine Connections")
        for key in engine_types.keys():
            diagram.append(f"    Gateway --> {key.upper()}_ENG")
            diagram.append(f"    {key.upper()}_ENG --> DB")
        
        diagram.append("```")
        return "\n".join(diagram)
    
    def generate_database_schema_diagram(self) -> str:
        """Generate database schema relationships diagram"""
        diagram = [
            "```mermaid",
            "erDiagram",
            "    USERS ||--o{ AGENTS : creates",
            "    USERS ||--o{ TASKS : creates",
            "    USERS {",
            "        uuid id PK",
            "        string username",
            "        string email",
            "        string password_hash",
            "        datetime created_at",
            "        boolean is_active",
            "    }",
            "    ",
            "    AGENTS ||--o{ TASKS : processes",
            "    AGENTS {",
            "        uuid id PK",
            "        uuid user_id FK",
            "        string name",
            "        string type",
            "        string status",
            "        json capabilities",
            "        json metadata",
            "        datetime created_at",
            "        datetime last_heartbeat",
            "    }",
            "    ",
            "    TASKS ||--o{ TASK_RESULTS : produces",
            "    TASKS {",
            "        uuid id PK",
            "        uuid user_id FK",
            "        uuid agent_id FK",
            "        string title",
            "        string description",
            "        string status",
            "        string priority",
            "        json input_data",
            "        datetime created_at",
            "        datetime completed_at",
            "    }",
            "    ",
            "    TASK_RESULTS {",
            "        uuid id PK",
            "        uuid task_id FK",
            "        json output_data",
            "        string status",
            "        json metrics",
            "        datetime created_at",
            "    }",
            "    ",
            "    AUDIT_LOGS {",
            "        uuid id PK",
            "        uuid user_id FK",
            "        string event_type",
            "        string resource_type",
            "        string resource_id",
            "        string action",
            "        json details",
            "        datetime timestamp",
            "    }",
            "    ",
            "    USERS ||--o{ AUDIT_LOGS : generates",
            "```"
        ]
        return "\n".join(diagram)
    
    def generate_api_route_map(self) -> str:
        """Generate API route map diagram"""
        diagram = [
            "```mermaid",
            "graph LR",
            "    subgraph Authentication",
            "        Login[POST /auth/login]",
            "        Register[POST /auth/register]",
            "        Logout[POST /auth/logout]",
            "    end",
            "    ",
            "    subgraph User Management",
            "        GetUser[GET /users/:id]",
            "        UpdateUser[PUT /users/:id]",
            "        ListUsers[GET /users]",
            "    end",
            "    ",
            "    subgraph Agent Management",
            "        CreateAgent[POST /agents]",
            "        GetAgent[GET /agents/:id]",
            "        ListAgents[GET /agents]",
            "        UpdateAgent[PUT /agents/:id]",
            "        DeleteAgent[DELETE /agents/:id]",
            "        AgentStatus[GET /agents/:id/status]",
            "    end",
            "    ",
            "    subgraph Task Management",
            "        CreateTask[POST /tasks]",
            "        GetTask[GET /tasks/:id]",
            "        ListTasks[GET /tasks]",
            "        UpdateTask[PUT /tasks/:id]",
            "        CancelTask[POST /tasks/:id/cancel]",
            "    end",
            "    ",
            "    subgraph Monitoring",
            "        Health[GET /health]",
            "        Metrics[GET /metrics]",
            "        Status[GET /status]",
            "    end",
            "    ",
            "    Gateway[API Gateway] --> Login",
            "    Gateway --> Register",
            "    Gateway --> CreateAgent",
            "    Gateway --> CreateTask",
            "    Gateway --> Health",
            "```"
        ]
        return "\n".join(diagram)
    
    def generate_agent_interaction_flow(self) -> str:
        """Generate agent interaction flow diagram"""
        diagram = [
            "```mermaid",
            "sequenceDiagram",
            "    participant Client",
            "    participant Gateway",
            "    participant Auth",
            "    participant TaskQueue",
            "    participant Agent",
            "    participant Engine",
            "    participant Database",
            "    ",
            "    Client->>Gateway: POST /tasks (Create Task)",
            "    Gateway->>Auth: Validate Token",
            "    Auth-->>Gateway: Token Valid",
            "    Gateway->>Database: Store Task",
            "    Database-->>Gateway: Task Created",
            "    Gateway->>TaskQueue: Enqueue Task",
            "    Gateway-->>Client: 202 Accepted",
            "    ",
            "    TaskQueue->>Agent: Assign Task",
            "    Agent->>Database: Update Status (Processing)",
            "    Agent->>Engine: Process Request",
            "    Engine-->>Agent: Processing Result",
            "    Agent->>Database: Store Result",
            "    Agent->>Database: Update Status (Completed)",
            "    Agent->>Client: WebSocket Notification",
            "    ",
            "    Client->>Gateway: GET /tasks/:id",
            "    Gateway->>Database: Fetch Task Result",
            "    Database-->>Gateway: Task Data",
            "    Gateway-->>Client: 200 OK (Result)",
            "```"
        ]
        return "\n".join(diagram)
    
    def generate_deployment_architecture(self) -> str:
        """Generate deployment architecture diagram"""
        diagram = [
            "```mermaid",
            "graph TB",
            "    subgraph Internet",
            "        Users[Users/Clients]",
            "    end",
            "    ",
            "    subgraph Cloud Provider",
            "        LB[Load Balancer]",
            "        ",
            "        subgraph Kubernetes Cluster",
            "            subgraph App Pods",
            "                API1[API Pod 1]",
            "                API2[API Pod 2]",
            "                API3[API Pod 3]",
            "            end",
            "            ",
            "            subgraph Worker Pods",
            "                Worker1[Worker Pod 1]",
            "                Worker2[Worker Pod 2]",
            "            end",
            "            ",
            "            subgraph Agent Pods",
            "                Agent1[Agent Pod 1]",
            "                Agent2[Agent Pod 2]",
            "                Agent3[Agent Pod 3]",
            "            end",
            "        end",
            "        ",
            "        subgraph Data Services",
            "            PG[(PostgreSQL Primary)]",
            "            PGR[(PostgreSQL Replica)]",
            "            Redis[(Redis Cluster)]",
            "        end",
            "        ",
            "        subgraph Monitoring",
            "            Prom[Prometheus]",
            "            Graf[Grafana]",
            "        end",
            "    end",
            "    ",
            "    Users --> LB",
            "    LB --> API1",
            "    LB --> API2",
            "    LB --> API3",
            "    ",
            "    API1 --> PG",
            "    API2 --> PG",
            "    API3 --> PG",
            "    ",
            "    API1 --> Redis",
            "    API2 --> Redis",
            "    API3 --> Redis",
            "    ",
            "    Worker1 --> PG",
            "    Worker2 --> PG",
            "    Worker1 --> Redis",
            "    Worker2 --> Redis",
            "    ",
            "    Agent1 --> PG",
            "    Agent2 --> PG",
            "    Agent3 --> PG",
            "    ",
            "    PG -.-> PGR",
            "    ",
            "    Prom -.-> API1",
            "    Prom -.-> Worker1",
            "    Prom -.-> Agent1",
            "    Graf -.-> Prom",
            "```"
        ]
        return "\n".join(diagram)
    
    def generate_architecture_markdown(self, output_path: Path) -> None:
        """Generate comprehensive architecture documentation"""
        print("📝 Generating architecture documentation...")
        
        md = []
        md.append("# YMERA Platform Architecture Documentation")
        md.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Table of Contents
        md.append("## 📑 Table of Contents\n")
        md.append("1. [High-Level Overview](#high-level-overview)")
        md.append("2. [System Architecture](#system-architecture)")
        md.append("3. [Database Schema](#database-schema)")
        md.append("4. [API Routes](#api-routes)")
        md.append("5. [Agent Interactions](#agent-interactions)")
        md.append("6. [Deployment Architecture](#deployment-architecture)")
        md.append("7. [Component Responsibilities](#component-responsibilities)")
        md.append("8. [Integration Points](#integration-points)")
        md.append("9. [Technology Stack](#technology-stack)")
        md.append("10. [Design Patterns](#design-patterns)")
        md.append("11. [Data Flow](#data-flow)")
        md.append("12. [Authentication & Authorization](#authentication--authorization)")
        md.append("13. [Error Handling Strategy](#error-handling-strategy)")
        md.append("14. [Caching Strategy](#caching-strategy)\n")
        
        # High-Level Overview
        md.append("## 📋 High-Level Overview\n")
        md.append("YMERA is a multi-agent AI platform built with FastAPI, featuring:")
        md.append("- **Microservices Architecture**: Modular components with clear separation of concerns")
        md.append("- **Event-Driven Design**: Asynchronous task processing with message queues")
        md.append("- **Multi-Agent System**: Specialized agents for different tasks")
        md.append("- **Scalable Infrastructure**: Kubernetes-ready with horizontal scaling")
        md.append("- **Production-Ready**: Comprehensive monitoring, logging, and security\n")
        
        # System Architecture
        md.append("## 🏗️ System Architecture\n")
        md.append(self.generate_system_architecture_diagram())
        md.append("")
        
        # Database Schema
        md.append("## 🗄️ Database Schema\n")
        md.append(self.generate_database_schema_diagram())
        md.append("")
        
        # API Routes
        md.append("## 🛣️ API Routes\n")
        md.append(self.generate_api_route_map())
        md.append("")
        
        # Agent Interactions
        md.append("## 🤖 Agent Interactions\n")
        md.append("### Task Processing Flow\n")
        md.append(self.generate_agent_interaction_flow())
        md.append("")
        
        # Deployment Architecture
        md.append("## 🚀 Deployment Architecture\n")
        md.append(self.generate_deployment_architecture())
        md.append("")
        
        # Component Responsibilities
        md.append("## 📦 Component Responsibilities\n")
        md.append("### Core Components\n")
        md.append("- **config.py**: Central configuration management using Pydantic settings")
        md.append("- **database.py**: AsyncPG database connection pool and session management")
        md.append("- **auth.py**: JWT-based authentication and authorization")
        md.append("- **sqlalchemy_models.py**: SQLAlchemy ORM models for database entities\n")
        
        md.append("### Middleware\n")
        md.append("- **rate_limiter.py**: Token-bucket rate limiting per user/IP")
        md.append("- **error_handler.py**: Centralized error handling and logging\n")
        
        md.append("### Agents\n")
        agent_categories = self._get_agent_categories()
        for agent_type, description in agent_categories.items():
            md.append(f"- **{agent_type}**: {description}")
        md.append("")
        
        md.append("### Engines\n")
        engine_categories = self._get_engine_categories()
        for engine_type, description in engine_categories.items():
            md.append(f"- **{engine_type}**: {description}")
        md.append("")
        
        # Integration Points
        md.append("## 🔌 Integration Points\n")
        md.append("### External Services\n")
        md.append("1. **PostgreSQL**: Primary data store")
        md.append("2. **Redis**: Caching and session management")
        md.append("3. **Prometheus**: Metrics collection")
        md.append("4. **External APIs**: LLM providers, third-party services\n")
        
        md.append("### Internal Communication\n")
        md.append("- **REST API**: Synchronous HTTP/HTTPS")
        md.append("- **WebSocket**: Real-time bidirectional communication")
        md.append("- **Message Queue**: Asynchronous task distribution")
        md.append("- **Event Bus**: Publish-subscribe pattern for internal events\n")
        
        # Technology Stack
        md.append("## 🛠️ Technology Stack\n")
        md.append("### Backend\n")
        md.append("- **Framework**: FastAPI 0.104.1")
        md.append("- **Language**: Python 3.11+")
        md.append("- **ASGI Server**: Uvicorn with gunicorn")
        md.append("- **Async Runtime**: asyncio\n")
        
        md.append("### Database\n")
        md.append("- **Primary**: PostgreSQL 14+")
        md.append("- **ORM**: SQLAlchemy 2.0 (async)")
        md.append("- **Migrations**: Alembic")
        md.append("- **Connection**: AsyncPG driver\n")
        
        md.append("### Caching & Queue\n")
        md.append("- **Cache**: Redis 7.0+")
        md.append("- **Client**: redis-py with hiredis\n")
        
        md.append("### Security\n")
        md.append("- **Authentication**: JWT (python-jose)")
        md.append("- **Password Hashing**: bcrypt (passlib)")
        md.append("- **Encryption**: cryptography library\n")
        
        md.append("### Monitoring\n")
        md.append("- **Metrics**: Prometheus client")
        md.append("- **Logging**: structlog")
        md.append("- **Health Checks**: Custom health endpoint\n")
        
        # Design Patterns
        md.append("## 🎨 Design Patterns\n")
        md.append("### Dependency Injection\n")
        md.append("FastAPI's dependency injection system manages:")
        md.append("- Database sessions")
        md.append("- Authentication")
        md.append("- Configuration")
        md.append("- Rate limiting\n")
        
        md.append("### Factory Pattern\n")
        md.append("Used for creating agents and engines dynamically based on configuration.\n")
        
        md.append("### Strategy Pattern\n")
        md.append("Different processing strategies for various agent types.\n")
        
        md.append("### Observer Pattern\n")
        md.append("Event-driven notifications for task status changes.\n")
        
        md.append("### Circuit Breaker\n")
        md.append("Prevents cascading failures in external service calls.\n")
        
        # Data Flow
        md.append("## 🔄 Data Flow\n")
        md.append("### Request Processing\n")
        md.append("1. **Client Request**: HTTP/WebSocket request arrives at API Gateway")
        md.append("2. **Rate Limiting**: Check rate limits via middleware")
        md.append("3. **Authentication**: Validate JWT token")
        md.append("4. **Routing**: FastAPI routes to appropriate endpoint")
        md.append("5. **Business Logic**: Handler processes request")
        md.append("6. **Database**: Async queries via SQLAlchemy")
        md.append("7. **Caching**: Redis cache check/update")
        md.append("8. **Response**: JSON response returned to client\n")
        
        md.append("### Task Processing\n")
        md.append("1. **Task Creation**: User submits task via API")
        md.append("2. **Queue**: Task added to processing queue")
        md.append("3. **Agent Selection**: Task router selects appropriate agent")
        md.append("4. **Processing**: Agent processes task with engine support")
        md.append("5. **Result Storage**: Results stored in database")
        md.append("6. **Notification**: WebSocket notification to client\n")
        
        # Authentication & Authorization
        md.append("## 🔐 Authentication & Authorization\n")
        md.append("### Authentication Flow\n")
        md.append("1. User submits credentials to `/auth/login`")
        md.append("2. Server validates credentials against database")
        md.append("3. JWT access token generated (15-minute expiry)")
        md.append("4. JWT refresh token generated (7-day expiry)")
        md.append("5. Tokens returned to client")
        md.append("6. Client includes access token in `Authorization: Bearer <token>` header")
        md.append("7. Middleware validates token on each request\n")
        
        md.append("### Authorization\n")
        md.append("- Role-based access control (RBAC)")
        md.append("- Permission checks at endpoint level")
        md.append("- Resource ownership validation\n")
        
        # Error Handling
        md.append("## ⚠️ Error Handling Strategy\n")
        md.append("### Exception Hierarchy\n")
        md.append("```python")
        md.append("BaseException")
        md.append("  └─ ApplicationError")
        md.append("       ├─ ValidationError (400)")
        md.append("       ├─ AuthenticationError (401)")
        md.append("       ├─ AuthorizationError (403)")
        md.append("       ├─ NotFoundError (404)")
        md.append("       └─ InternalError (500)")
        md.append("```\n")
        
        md.append("### Error Response Format\n")
        md.append("```json")
        md.append("{")
        md.append('  "error": {')
        md.append('    "code": "VALIDATION_ERROR",')
        md.append('    "message": "Human-readable error message",')
        md.append('    "details": {},')
        md.append('    "timestamp": "2025-10-19T22:00:00Z"')
        md.append("  }")
        md.append("}")
        md.append("```\n")
        
        # Caching Strategy
        md.append("## 💾 Caching Strategy\n")
        md.append("### Cache Layers\n")
        md.append("1. **L1 - Application Cache**: In-memory LRU cache")
        md.append("2. **L2 - Redis Cache**: Distributed cache for shared data")
        md.append("3. **L3 - Database**: PostgreSQL as source of truth\n")
        
        md.append("### Cache Invalidation\n")
        md.append("- **Time-based**: TTL on cached entries")
        md.append("- **Event-based**: Invalidate on data updates")
        md.append("- **Manual**: Admin endpoints for cache clearing\n")
        
        md.append("### Cached Data\n")
        md.append("- User sessions (15 minutes)")
        md.append("- Agent configurations (1 hour)")
        md.append("- Task results (30 minutes)")
        md.append("- Static content (24 hours)\n")
        
        # Database Connection Pooling
        md.append("## 🏊 Database Connection Pooling\n")
        md.append("### Configuration\n")
        md.append("```python")
        md.append("pool_size = 20          # Minimum connections")
        md.append("max_overflow = 10       # Additional connections when needed")
        md.append("pool_timeout = 30       # Seconds to wait for connection")
        md.append("pool_recycle = 3600     # Recycle connections after 1 hour")
        md.append("```\n")
        
        md.append("### Connection Lifecycle\n")
        md.append("1. Connection acquired from pool")
        md.append("2. Transaction executed")
        md.append("3. Connection returned to pool")
        md.append("4. Periodic health checks")
        md.append("5. Stale connections recycled\n")
        
        # Design Decisions
        md.append("## 💡 Design Decisions & Rationale\n")
        md.append("### FastAPI over Flask/Django\n")
        md.append("- Modern async/await support")
        md.append("- Automatic OpenAPI documentation")
        md.append("- Type hints and validation with Pydantic")
        md.append("- High performance (comparable to Node.js)\n")
        
        md.append("### PostgreSQL over MongoDB\n")
        md.append("- ACID compliance for critical data")
        md.append("- Complex query support")
        md.append("- JSON support for flexible schemas")
        md.append("- Mature ecosystem and tooling\n")
        
        md.append("### Redis for Caching\n")
        md.append("- In-memory performance")
        md.append("- Pub/sub for real-time features")
        md.append("- Atomic operations")
        md.append("- TTL support\n")
        
        md.append("### Microservices Architecture\n")
        md.append("- Independent scaling")
        md.append("- Technology flexibility")
        md.append("- Fault isolation")
        md.append("- Team autonomy\n")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(md))
        
        print(f"   ✅ Architecture documentation saved to {output_path}")
    
    def _get_agent_categories(self) -> Dict[str, str]:
        """Get agent categories with descriptions"""
        return {
            "Learning Agent": "Adaptive learning from user interactions and feedback",
            "LLM Agent": "Language model integration and natural language processing",
            "Communication Agent": "Inter-agent communication and message routing",
            "Drafting Agent": "Content generation and document drafting",
            "Editing Agent": "Content editing and refinement",
            "Enhancement Agent": "Feature enhancement and optimization suggestions",
            "Examination Agent": "Code review and quality analysis",
            "Metrics Agent": "Performance metrics collection and reporting",
            "Monitoring Agent": "System health monitoring and alerting",
            "Security Agent": "Security scanning and threat detection",
            "Validation Agent": "Input validation and data quality checks",
            "Orchestrator Agent": "Multi-agent task coordination"
        }
    
    def _get_engine_categories(self) -> Dict[str, str]:
        """Get engine categories with descriptions"""
        return {
            "Workflow Engine": "Business process orchestration and state management",
            "Performance Engine": "Performance optimization and tuning",
            "Intelligence Engine": "AI/ML model serving and inference",
            "Optimization Engine": "Resource allocation and load balancing",
            "Analytics Engine": "Data analysis and reporting",
            "Recommendation Engine": "Personalized recommendations",
            "Learning Engine": "Model training and continuous learning"
        }
    
    def run(self, output_dir: Path) -> None:
        """Run architecture documentation generation"""
        print("\n" + "="*70)
        print("🏗️  YMERA Platform Architecture Documentation")
        print("="*70 + "\n")
        
        arch_dir = output_dir / 'architecture'
        self.generate_architecture_markdown(arch_dir / 'ARCHITECTURE.md')
        
        print("\n" + "="*70)
        print("✅ Architecture Documentation Complete!")
        print("="*70 + "\n")
        print(f"📁 Documentation saved to: {arch_dir}")


def main():
    """Main entry point"""
    repo_path = Path(__file__).parent
    inventory_path = repo_path / 'audit_reports' / 'inventory' / 'platform_inventory.json'
    output_dir = repo_path / 'audit_reports'
    
    if not inventory_path.exists():
        print(f"❌ Error: Inventory file not found at {inventory_path}")
        print("   Please run generate_component_inventory.py first")
        return
    
    generator = ArchitectureDocGenerator(inventory_path)
    generator.run(output_dir)
    
    print("\n✨ Architecture documentation completed successfully!")


if __name__ == '__main__':
    main()
