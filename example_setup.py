"""
Example: Complete Database Setup and Basic Operations
YMERA Enterprise Database Core v5.0.0
"""

import asyncio
import os
from datetime import datetime
from DATABASE_CORE import (
    # Core components
    init_database,
    close_database,
    get_database_manager,
    DatabaseConfig,
    
    # Models
    User, Project, Agent, Task, File, AuditLog,
    
    # Repository
    BaseRepository
)

# Set environment variables for this example
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./example_ymera.db"
os.environ["DB_ECHO"] = "false"

async def setup_example_data():
    """Setup example data in the database"""
    print("=" * 60)
    print("YMERA Database Core - Example Setup")
    print("=" * 60)
    
    # Initialize database
    print("\n1️⃣  Initializing database...")
    db_manager = await init_database()
    print("✅ Database initialized successfully")
    
    # Health check
    print("\n2️⃣  Performing health check...")
    health = await db_manager.health_check()
    print(f"✅ Database health: {health['status']}")
    print(f"   Database type: {health['database_type']}")
    
    # Create example data
    print("\n3️⃣  Creating example data...")
    
    async with db_manager.get_session() as session:
        user_repo = BaseRepository(session, User)
        project_repo = BaseRepository(session, Project)
        agent_repo = BaseRepository(session, Agent)
        task_repo = BaseRepository(session, Task)
        
        # Create admin user
        admin_user = await user_repo.create(
            username="admin",
            email="admin@ymera.com",
            password_hash="<hashed_password>",  # Use proper hashing in production
            first_name="System",
            last_name="Administrator",
            role="admin",
            is_active=True,
            permissions=["all"],
            preferences={"theme": "dark", "language": "en"}
        )
        print(f"✅ Created user: {admin_user.username} ({admin_user.id})")
        
        # Create developer user
        dev_user = await user_repo.create(
            username="developer",
            email="dev@ymera.com",
            password_hash="<hashed_password>",
            first_name="John",
            last_name="Developer",
            role="developer",
            is_active=True,
            preferences={"theme": "light", "language": "en"}
        )
        print(f"✅ Created user: {dev_user.username} ({dev_user.id})")
        
        # Create project
        project = await project_repo.create(
            name="YMERA Platform",
            description="Enterprise multi-agent system platform",
            owner_id=admin_user.id,
            project_type="platform",
            programming_language="Python",
            framework="FastAPI",
            status="active",
            priority="high",
            progress=45.5,
            tags=["ai", "automation", "enterprise"],
            settings={
                "auto_deploy": True,
                "notifications_enabled": True,
                "max_concurrent_tasks": 10
            }
        )
        print(f"✅ Created project: {project.name} ({project.id})")
        
        # Create agents
        code_agent = await agent_repo.create(
            name="CodeGenerator",
            agent_type="code_generation",
            description="AI agent for generating code",
            capabilities=["python", "javascript", "typescript", "api_design"],
            configuration={
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            status="active",
            health_status="healthy",
            success_rate=95.5
        )
        print(f"✅ Created agent: {code_agent.name} ({code_agent.id})")
        
        test_agent = await agent_repo.create(
            name="TestAutomator",
            agent_type="testing",
            description="AI agent for automated testing",
            capabilities=["unit_testing", "integration_testing", "e2e_testing"],
            configuration={
                "frameworks": ["pytest", "jest"],
                "coverage_threshold": 80
            },
            status="active",
            health_status="healthy",
            success_rate=92.0
        )
        print(f"✅ Created agent: {test_agent.name} ({test_agent.id})")
        
        # Create tasks
        task1 = await task_repo.create(
            title="Generate REST API endpoints",
            description="Create CRUD endpoints for user management module",
            task_type="code_generation",
            user_id=dev_user.id,
            project_id=project.id,
            agent_id=code_agent.id,
            status="completed",
            priority="high",
            urgency=8,
            progress=100.0,
            execution_time=45.2,
            input_data={
                "module": "user_management",
                "endpoints": ["create", "read", "update", "delete"],
                "authentication": "JWT"
            },
            output_data={
                "files_generated": 5,
                "lines_of_code": 350,
                "tests_included": True
            },
            quality_score=94.5,
            tags=["api", "backend", "user_management"]
        )
        print(f"✅ Created task: {task1.title} ({task1.id})")
        
        task2 = await task_repo.create(
            title="Write unit tests for authentication",
            description="Create comprehensive unit tests for auth module",
            task_type="testing",
            user_id=dev_user.id,
            project_id=project.id,
            agent_id=test_agent.id,
            status="in_progress",
            priority="high",
            urgency=7,
            progress=65.0,
            input_data={
                "module": "authentication",
                "coverage_target": 90,
                "test_types": ["unit", "integration"]
            },
            tags=["testing", "authentication", "security"]
        )
        print(f"✅ Created task: {task2.title} ({task2.id})")
        
        task3 = await task_repo.create(
            title="Generate documentation",
            description="Auto-generate API documentation",
            task_type="documentation",
            user_id=admin_user.id,
            project_id=project.id,
            status="pending",
            priority="medium",
            urgency=5,
            input_data={
                "format": "OpenAPI 3.0",
                "include_examples": True
            },
            tags=["documentation", "api"]
        )
        print(f"✅ Created task: {task3.title} ({task3.id})")
        
        await session.commit()
    
    # Get statistics
    print("\n4️⃣  Retrieving statistics...")
    stats = await db_manager.get_statistics()
    print(f"✅ Database statistics:")
    print(f"   Users: {stats.get('users_count', 0)}")
    print(f"   Projects: {stats.get('projects_count', 0)}")
    print(f"   Agents: {stats.get('agents_count', 0)}")
    print(f"   Tasks: {stats.get('tasks_count', 0)}")
    
    # Query examples
    print("\n5️⃣  Running example queries...")
    
    async with db_manager.get_session() as session:
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload
        
        # Get project with all tasks
        result = await session.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.status == "active")
        )
        projects = result.scalars().all()
        
        for proj in projects:
            print(f"\n📊 Project: {proj.name}")
            print(f"   Status: {proj.status}")
            print(f"   Progress: {proj.progress}%")
            print(f"   Tasks: {len(proj.tasks)}")
            for task in proj.tasks[:3]:  # Show first 3 tasks
                print(f"      - {task.title} ({task.status})")
        
        # Get agent statistics
        result = await session.execute(
            select(
                Agent.agent_type,
                func.count(Agent.id).label('count'),
                func.avg(Agent.success_rate).label('avg_success')
            )
            .group_by(Agent.agent_type)
        )
        
        print("\n🤖 Agent Statistics:")
        for row in result:
            print(f"   {row.agent_type}: {row.count} agents, {row.avg_success:.1f}% success rate")
        
        # Get task summary
        result = await session.execute(
            select(
                Task.status,
                func.count(Task.id).label('count')
            )
            .group_by(Task.status)
        )
        
        print("\n📋 Task Summary:")
        for row in result:
            print(f"   {row.status}: {row.count}")
    
    # Optimization
    print("\n6️⃣  Running database optimization...")
    optimization_result = await db_manager.optimize_database()
    if optimization_result['success']:
        print("✅ Database optimized successfully")
        for opt in optimization_result['optimizations']:
            print(f"   - {opt}")
    
    print("\n" + "=" * 60)
    print("✅ Example setup completed successfully!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Explore the database using SQLite Browser")
    print("  2. Run example_queries.py for more query examples")
    print("  3. Run example_api.py to see FastAPI integration")
    print("  4. Check example_ymera.db file created in current directory")
    print("\n")

async def cleanup_example():
    """Cleanup and close database"""
    print("\n🧹 Cleaning up...")
    await close_database()
    print("✅ Database closed successfully\n")

async def main():
    """Main execution"""
    try:
        await setup_example_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cleanup_example()

if __name__ == "__main__":
    asyncio.run(main())
