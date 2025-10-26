#!/usr/bin/env python3
"""
YMERA Database Core - Quick Start Script
Run this script to quickly verify the database system is working
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./quickstart_test.db"

async def quick_start():
    """Quick start demo"""
    
    print("\n" + "="*70)
    print("🚀 YMERA DATABASE CORE - QUICK START")
    print("="*70 + "\n")
    
    try:
        # Step 1: Import
        print("📦 Step 1: Importing DATABASE_CORE...")
        from DATABASE_CORE import (
            init_database,
            close_database,
            get_database_manager,
            User, Project, Agent, Task,
            BaseRepository
        )
        print("✅ Import successful!\n")
        
        # Step 2: Initialize
        print("🔧 Step 2: Initializing database...")
        db_manager = await init_database()
        print("✅ Database initialized!\n")
        
        # Step 3: Health Check
        print("💓 Step 3: Performing health check...")
        health = await db_manager.health_check()
        print(f"✅ Database is {health['status']}")
        print(f"   Type: {health['database_type']}\n")
        
        # Step 4: Create User
        print("👤 Step 4: Creating a user...")
        async with db_manager.get_session() as session:
            user_repo = BaseRepository(session, User)
            user = await user_repo.create(
                username="quickstart_user",
                email="quickstart@example.com",
                password_hash="hashed_password_here",
                first_name="Quick",
                last_name="Start"
            )
            print(f"✅ Created user: {user.username} (ID: {user.id})\n")
            
            # Step 5: Create Project
            print("📁 Step 5: Creating a project...")
            project_repo = BaseRepository(session, Project)
            project = await project_repo.create(
                name="Quick Start Project",
                description="Testing YMERA Database Core",
                owner_id=user.id,
                status="active"
            )
            print(f"✅ Created project: {project.name} (ID: {project.id})\n")
            
            # Step 6: Create Agent
            print("🤖 Step 6: Creating an agent...")
            agent_repo = BaseRepository(session, Agent)
            agent = await agent_repo.create(
                name="Quick Start Agent",
                agent_type="test_agent",
                status="active"
            )
            print(f"✅ Created agent: {agent.name} (ID: {agent.id})\n")
            
            # Step 7: Create Task
            print("📋 Step 7: Creating a task...")
            task_repo = BaseRepository(session, Task)
            task = await task_repo.create(
                title="Quick Start Task",
                description="Test task creation",
                task_type="test",
                user_id=user.id,
                project_id=project.id,
                agent_id=agent.id,
                status="pending"
            )
            print(f"✅ Created task: {task.title} (ID: {task.id})\n")
            
            await session.commit()
        
        # Step 8: Query Data
        print("🔍 Step 8: Querying data...")
        stats = await db_manager.get_statistics()
        print(f"✅ Database statistics:")
        print(f"   Users: {stats['users_count']}")
        print(f"   Projects: {stats['projects_count']}")
        print(f"   Agents: {stats['agents_count']}")
        print(f"   Tasks: {stats['tasks_count']}\n")
        
        # Step 9: Update Task
        print("🔄 Step 9: Updating task status...")
        async with db_manager.get_session() as session:
            task_repo = BaseRepository(session, Task)
            updated_task = await task_repo.update(
                task.id,
                status="completed",
                progress=100.0
            )
            print(f"✅ Task status updated to: {updated_task.status}\n")
            await session.commit()
        
        # Step 10: Cleanup
        print("🧹 Step 10: Closing database...")
        await close_database()
        print("✅ Database closed!\n")
        
        print("="*70)
        print("🎉 SUCCESS! YMERA Database Core is working perfectly!")
        print("="*70)
        print("\n📚 Next steps:")
        print("   1. Read README.md for complete documentation")
        print("   2. Run example_setup.py for more detailed examples")
        print("   3. Run test_database.py to verify all functionality")
        print("   4. Check example_api.py for FastAPI integration")
        print("\n✨ Your database system is ready to use!\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup test database
        try:
            test_db = Path("./quickstart_test.db")
            if test_db.exists():
                test_db.unlink()
                print("✓ Cleaned up test database")
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(quick_start())
    sys.exit(0 if success else 1)
