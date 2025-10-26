"""
Test Suite for YMERA Database Core v5.0.0
Run comprehensive tests to verify all functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_database_initialization():
    """Test 1: Database Initialization"""
    print("\n" + "="*60)
    print("TEST 1: Database Initialization")
    print("="*60)
    
    try:
        from DATABASE_CORE import init_database, close_database, DatabaseConfig
        
        # Set test database
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_ymera.db"
        
        print("✓ Imports successful")
        
        # Initialize database
        db_manager = await init_database()
        print("✓ Database initialized")
        
        # Check configuration
        assert db_manager.config.db_type == "sqlite"
        print(f"✓ Database type: {db_manager.config.db_type}")
        
        # Close
        await close_database()
        print("✓ Database closed")
        
        print("\n✅ TEST 1 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

async def test_health_and_stats():
    """Test 2: Health Check and Statistics"""
    print("\n" + "="*60)
    print("TEST 2: Health Check and Statistics")
    print("="*60)
    
    try:
        from DATABASE_CORE import init_database, close_database, get_database_manager
        
        db_manager = await init_database()
        
        # Health check
        health = await db_manager.health_check()
        assert health["healthy"] == True
        print(f"✓ Health check: {health['status']}")
        print(f"  Database type: {health['database_type']}")
        
        # Statistics
        stats = await db_manager.get_statistics()
        print(f"✓ Statistics retrieved:")
        print(f"  Users: {stats.get('users_count', 0)}")
        print(f"  Projects: {stats.get('projects_count', 0)}")
        print(f"  Agents: {stats.get('agents_count', 0)}")
        print(f"  Tasks: {stats.get('tasks_count', 0)}")
        
        await close_database()
        print("\n✅ TEST 2 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

async def test_user_crud():
    """Test 3: User CRUD Operations"""
    print("\n" + "="*60)
    print("TEST 3: User CRUD Operations")
    print("="*60)
    
    try:
        from DATABASE_CORE import (
            init_database, close_database, get_db_session,
            User, BaseRepository
        )
        
        db_manager = await init_database()
        
        async with db_manager.get_session() as session:
            repo = BaseRepository(session, User)
            
            # CREATE
            user = await repo.create(
                username="testuser",
                email="test@example.com",
                password_hash="hashed_password",
                first_name="Test",
                last_name="User",
                role="user"
            )
            print(f"✓ Created user: {user.username} (ID: {user.id})")
            user_id = user.id
            
            # READ
            retrieved = await repo.get_by_id(user_id)
            assert retrieved is not None
            assert retrieved.username == "testuser"
            print(f"✓ Retrieved user: {retrieved.email}")
            
            # UPDATE
            updated = await repo.update(user_id, first_name="Updated", last_name="Name")
            assert updated.first_name == "Updated"
            print(f"✓ Updated user: {updated.first_name} {updated.last_name}")
            
            # LIST
            users = await repo.get_all(limit=10)
            assert len(users) > 0
            print(f"✓ Listed users: {len(users)} found")
            
            # SOFT DELETE
            success = await repo.soft_delete(user_id)
            assert success == True
            print(f"✓ Soft deleted user")
            
            await session.commit()
        
        await close_database()
        print("\n✅ TEST 3 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

async def test_project_management():
    """Test 4: Project Management"""
    print("\n" + "="*60)
    print("TEST 4: Project Management")
    print("="*60)
    
    try:
        from DATABASE_CORE import (
            init_database, close_database,
            User, Project, BaseRepository
        )
        
        db_manager = await init_database()
        
        async with db_manager.get_session() as session:
            # Create user first
            user_repo = BaseRepository(session, User)
            user = await user_repo.create(
                username="projectowner",
                email="owner@example.com",
                password_hash="hashed"
            )
            print(f"✓ Created user: {user.username}")
            
            # Create project
            project_repo = BaseRepository(session, Project)
            project = await project_repo.create(
                name="Test Project",
                description="A test project",
                owner_id=user.id,
                project_type="test",
                programming_language="Python",
                framework="FastAPI",
                priority="high",
                tags=["test", "demo"]
            )
            print(f"✓ Created project: {project.name}")
            assert project.owner_id == user.id
            
            # Update project
            updated_project = await project_repo.update(
                project.id,
                progress=50.0,
                total_tasks=10,
                completed_tasks=5
            )
            assert updated_project.progress == 50.0
            print(f"✓ Updated project progress: {updated_project.progress}%")
            
            # List projects
            projects = await project_repo.get_all(
                filters={"status": "active"}
            )
            print(f"✓ Listed projects: {len(projects)} found")
            
            await session.commit()
        
        await close_database()
        print("\n✅ TEST 4 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_task_workflow():
    """Test 5: Agent and Task Workflow"""
    print("\n" + "="*60)
    print("TEST 5: Agent and Task Workflow")
    print("="*60)
    
    try:
        from DATABASE_CORE import (
            init_database, close_database,
            User, Project, Agent, Task, BaseRepository
        )
        
        db_manager = await init_database()
        
        async with db_manager.get_session() as session:
            # Create user
            user_repo = BaseRepository(session, User)
            user = await user_repo.create(
                username="taskuser",
                email="task@example.com",
                password_hash="hashed"
            )
            print(f"✓ Created user: {user.username}")
            
            # Create project
            project_repo = BaseRepository(session, Project)
            project = await project_repo.create(
                name="Task Project",
                owner_id=user.id
            )
            print(f"✓ Created project: {project.name}")
            
            # Create agent
            agent_repo = BaseRepository(session, Agent)
            agent = await agent_repo.create(
                name="Test Agent",
                agent_type="test",
                capabilities=["testing"],
                status="active"
            )
            print(f"✓ Created agent: {agent.name}")
            
            # Create task
            task_repo = BaseRepository(session, Task)
            task = await task_repo.create(
                title="Test Task",
                description="Testing task creation",
                task_type="test",
                user_id=user.id,
                project_id=project.id,
                agent_id=agent.id,
                status="pending",
                priority="high",
                urgency=7
            )
            print(f"✓ Created task: {task.title}")
            
            # Update task status
            updated_task = await task_repo.update(
                task.id,
                status="completed",
                progress=100.0,
                execution_time=45.5
            )
            assert updated_task.status == "completed"
            print(f"✓ Updated task status: {updated_task.status}")
            
            # Update agent stats
            updated_agent = await agent_repo.update(
                agent.id,
                tasks_completed=1,
                success_rate=100.0
            )
            assert updated_agent.tasks_completed == 1
            print(f"✓ Updated agent stats: {updated_agent.tasks_completed} completed")
            
            await session.commit()
        
        await close_database()
        print("\n✅ TEST 5 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

async def test_optimization_and_cleanup():
    """Test 6: Database Optimization and Cleanup"""
    print("\n" + "="*60)
    print("TEST 6: Database Optimization and Cleanup")
    print("="*60)
    
    try:
        from DATABASE_CORE import init_database, close_database, get_database_manager
        
        db_manager = await init_database()
        
        # Optimize database
        opt_result = await db_manager.optimize_database()
        assert opt_result["success"] == True
        print(f"✓ Database optimized")
        for opt in opt_result["optimizations"]:
            print(f"  - {opt}")
        
        # Cleanup old data (90 days retention)
        cleanup_result = await db_manager.cleanup_old_data(days_to_keep=90)
        assert cleanup_result["success"] == True
        print(f"✓ Cleanup completed")
        print(f"  Cleaned records: {cleanup_result['cleaned']}")
        
        await close_database()
        print("\n✅ TEST 6 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

async def test_query_operations():
    """Test 7: Complex Query Operations"""
    print("\n" + "="*60)
    print("TEST 7: Complex Query Operations")
    print("="*60)
    
    try:
        from DATABASE_CORE import (
            init_database, close_database,
            User, Project, Task, Agent
        )
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload
        
        db_manager = await init_database()
        
        async with db_manager.get_session() as session:
            # Count queries
            user_count = await session.execute(select(func.count(User.id)))
            count = user_count.scalar()
            print(f"✓ User count query: {count} users")
            
            # Aggregate query
            task_stats = await session.execute(
                select(
                    Task.status,
                    func.count(Task.id).label('count')
                )
                .group_by(Task.status)
            )
            print(f"✓ Task statistics:")
            for row in task_stats:
                print(f"  {row.status}: {row.count}")
            
            # Join query with eager loading
            projects = await session.execute(
                select(Project)
                .options(selectinload(Project.tasks))
                .limit(5)
            )
            project_list = projects.scalars().all()
            print(f"✓ Projects with tasks loaded: {len(project_list)}")
            
            # Agent statistics
            agent_stats = await session.execute(
                select(
                    Agent.agent_type,
                    func.count(Agent.id).label('count'),
                    func.avg(Agent.success_rate).label('avg_success')
                )
                .group_by(Agent.agent_type)
            )
            print(f"✓ Agent statistics:")
            for row in agent_stats:
                print(f"  {row.agent_type}: {row.count} agents, {row.avg_success or 0:.1f}% success")
        
        await close_database()
        print("\n✅ TEST 7 PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 7 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# YMERA DATABASE CORE - COMPREHENSIVE TEST SUITE")
    print("# Version 5.0.0")
    print("#"*60)
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Health Check & Statistics", test_health_and_stats),
        ("User CRUD Operations", test_user_crud),
        ("Project Management", test_project_management),
        ("Agent & Task Workflow", test_agent_task_workflow),
        ("Optimization & Cleanup", test_optimization_and_cleanup),
        ("Complex Query Operations", test_query_operations),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}\n")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print(f"TOTAL: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Database system is fully functional.\n")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.\n")
    
    # Cleanup test database
    try:
        test_db = Path("./test_ymera.db")
        if test_db.exists():
            test_db.unlink()
            print("✓ Cleaned up test database\n")
    except:
        pass
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
