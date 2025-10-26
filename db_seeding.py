"""
Database Seeding Module
Create seed data for development, testing, and initial production setup
"""

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List
import uuid

from core.sqlalchemy_models import User, Agent, Task, AgentStatus, TaskStatus, TaskPriority
from core.auth import AuthService


class DatabaseSeeder:
    """Database seeding utility"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.auth_service = AuthService()
    
    async def seed_development_data(self):
        """
        Seed data for development environment
        Creates sample users, agents, and tasks
        """
        print("Seeding development data...")
        
        # Create test users
        users = await self._create_test_users()
        
        # Create test agents
        agents = await self._create_test_agents(users)
        
        # Create test tasks
        tasks = await self._create_test_tasks(users, agents)
        
        await self.session.commit()
        
        print(f"Created {len(users)} users, {len(agents)} agents, {len(tasks)} tasks")
        return {
            "users": users,
            "agents": agents,
            "tasks": tasks
        }
    
    async def seed_test_data(self):
        """
        Seed data for testing environment
        Creates minimal data for running tests
        """
        print("Seeding test data...")
        
        # Create single test user
        user = User(
            id=str(uuid.uuid4()),
            username="testuser",
            email="test@example.com",
            password_hash=self.auth_service.hash_password("testpassword123"),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(user)
        
        # Create test agent
        agent = Agent(
            id=str(uuid.uuid4()),
            name="Test Agent",
            description="Agent for testing",
            capabilities=["test", "development"],
            status=AgentStatus.ACTIVE,
            owner_id=user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(agent)
        
        await self.session.commit()
        
        print("Test data seeded successfully")
        return {"user": user, "agent": agent}
    
    async def seed_production_data(self):
        """
        Seed initial production data
        Creates admin user and essential system agents
        """
        print("Seeding production data...")
        
        # Create admin user
        admin = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@ymera.com",
            password_hash=self.auth_service.hash_password("CHANGE_ME_IMMEDIATELY"),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(admin)
        
        # Create system monitoring agent
        monitoring_agent = Agent(
            id=str(uuid.uuid4()),
            name="System Monitor",
            description="Monitors system health and performance",
            capabilities=["monitoring", "alerting", "health-check"],
            status=AgentStatus.ACTIVE,
            owner_id=admin.id,
            config={"type": "system", "auto_start": True},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(monitoring_agent)
        
        await self.session.commit()
        
        print("Production data seeded successfully")
        print("⚠️  IMPORTANT: Change admin password immediately!")
        
        return {"admin": admin, "monitoring_agent": monitoring_agent}
    
    async def _create_test_users(self) -> List[User]:
        """Create test users"""
        users = []
        
        user_data = [
            {"username": "john_doe", "email": "john@example.com", "password": "password123"},
            {"username": "jane_smith", "email": "jane@example.com", "password": "password123"},
            {"username": "bob_wilson", "email": "bob@example.com", "password": "password123"},
        ]
        
        for data in user_data:
            user = User(
                id=str(uuid.uuid4()),
                username=data["username"],
                email=data["email"],
                password_hash=self.auth_service.hash_password(data["password"]),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(user)
            users.append(user)
        
        return users
    
    async def _create_test_agents(self, users: List[User]) -> List[Agent]:
        """Create test agents"""
        agents = []
        
        agent_configs = [
            {
                "name": "Code Generator",
                "description": "Generates code based on requirements",
                "capabilities": ["code-generation", "python", "javascript"],
                "owner": users[0]
            },
            {
                "name": "Test Runner",
                "description": "Runs automated tests",
                "capabilities": ["testing", "pytest", "jest"],
                "owner": users[0]
            },
            {
                "name": "Documentation Agent",
                "description": "Generates documentation",
                "capabilities": ["documentation", "markdown", "api-docs"],
                "owner": users[1]
            },
            {
                "name": "Code Reviewer",
                "description": "Reviews code for quality",
                "capabilities": ["review", "quality-check", "security"],
                "owner": users[1]
            },
        ]
        
        for config in agent_configs:
            agent = Agent(
                id=str(uuid.uuid4()),
                name=config["name"],
                description=config["description"],
                capabilities=config["capabilities"],
                status=AgentStatus.ACTIVE if agents else AgentStatus.INACTIVE,
                owner_id=config["owner"].id,
                last_heartbeat=datetime.utcnow() if agents else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(agent)
            agents.append(agent)
        
        return agents
    
    async def _create_test_tasks(self, users: List[User], agents: List[Agent]) -> List[Task]:
        """Create test tasks"""
        tasks = []
        
        task_configs = [
            {
                "name": "Generate user authentication module",
                "description": "Create user auth with JWT",
                "task_type": "code-generation",
                "priority": TaskPriority.HIGH,
                "status": TaskStatus.COMPLETED,
                "user": users[0],
                "agent": agents[0],
                "completed": True
            },
            {
                "name": "Write unit tests for API",
                "description": "Create comprehensive test suite",
                "task_type": "testing",
                "priority": TaskPriority.NORMAL,
                "status": TaskStatus.RUNNING,
                "user": users[0],
                "agent": agents[1],
                "completed": False
            },
            {
                "name": "Generate API documentation",
                "description": "Create OpenAPI docs",
                "task_type": "documentation",
                "priority": TaskPriority.NORMAL,
                "status": TaskStatus.PENDING,
                "user": users[1],
                "agent": None,
                "completed": False
            },
            {
                "name": "Review database schema",
                "description": "Check for optimization opportunities",
                "task_type": "review",
                "priority": TaskPriority.LOW,
                "status": TaskStatus.FAILED,
                "user": users[1],
                "agent": agents[3],
                "completed": True,
                "error": "Schema validation failed"
            },
        ]
        
        for i, config in enumerate(task_configs):
            now = datetime.utcnow()
            created_at = now - timedelta(hours=24-i*6)
            
            task = Task(
                id=str(uuid.uuid4()),
                name=config["name"],
                description=config["description"],
                task_type=config["task_type"],
                priority=config["priority"],
                status=config["status"],
                user_id=config["user"].id,
                agent_id=config["agent"].id if config["agent"] else None,
                created_at=created_at,
                updated_at=now,
                started_at=created_at + timedelta(minutes=5) if config["status"] != TaskStatus.PENDING else None,
                completed_at=now - timedelta(hours=1) if config["completed"] else None,
                error_message=config.get("error")
            )
            self.session.add(task)
            tasks.append(task)
        
        return tasks


async def seed_database(session: AsyncSession, environment: str = "development"):
    """
    Seed database based on environment
    
    Args:
        session: Database session
        environment: Environment name (development, test, production)
    """
    seeder = DatabaseSeeder(session)
    
    if environment == "development":
        return await seeder.seed_development_data()
    elif environment == "test":
        return await seeder.seed_test_data()
    elif environment == "production":
        return await seeder.seed_production_data()
    else:
        raise ValueError(f"Unknown environment: {environment}")
