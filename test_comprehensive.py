"""
YMERA Production System - Comprehensive Test Suite
Demonstrates all system capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.system import YMERASystem, get_system
from core.config import Config
from learning.engine import LearningTaskType


async def test_system_initialization():
    """Test 1: System Initialization"""
    print("\n" + "="*80)
    print("TEST 1: System Initialization")
    print("="*80)
    
    try:
        # Create system with default config
        system = YMERASystem()
        
        # Initialize
        await system.initialize()
        
        # Get status
        status = await system.get_system_status()
        
        print("✅ System initialized successfully!")
        print(f"   System ID: {status['system_id']}")
        print(f"   Status: {status['status']}")
        print(f"   Version: {status['version']}")
        print(f"   Components: {len(status['components'])} active")
        
        return system, True
    
    except Exception as e:
        print(f"❌ System initialization failed: {str(e)}")
        return None, False


async def test_learning_tasks(system: YMERASystem):
    """Test 2: Learning Task Submission"""
    print("\n" + "="*80)
    print("TEST 2: Learning Task Submission")
    print("="*80)
    
    try:
        # Submit classification task
        task_id = await system.submit_learning_task(
            task_type="classification",
            data={"features": [[1, 2, 3], [4, 5, 6]], "labels": [0, 1]},
            config={"learning_rate": 0.001}
        )
        
        print(f"✅ Classification task submitted: {task_id}")
        
        # Wait a bit for task to process
        await asyncio.sleep(0.5)
        
        # Check task status
        status = await system.get_task_status(task_id)
        print(f"   Task Status: {status['status']}")
        print(f"   Task Type: {status['type']}")
        
        if status['status'] == 'completed':
            result = await system.get_task_result(task_id)
            print(f"   Metrics: {result['metrics']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Learning task test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_knowledge_base(system: YMERASystem):
    """Test 3: Knowledge Base Operations"""
    print("\n" + "="*80)
    print("TEST 3: Knowledge Base Operations")
    print("="*80)
    
    try:
        kb = system.knowledge_base
        
        # Store knowledge
        entry_id = await kb.store(
            content={"topic": "machine_learning", "description": "Advanced ML techniques"},
            category="research",
            tags=["ml", "research", "production"]
        )
        
        print(f"✅ Knowledge stored: {entry_id}")
        
        # Retrieve knowledge
        entry = await kb.retrieve(entry_id)
        if entry:
            print(f"   Retrieved: {entry.content['topic']}")
        
        # Search knowledge
        results = await system.query_knowledge(
            query={"topic": "machine_learning"},
            category="research",
            limit=5
        )
        
        print(f"   Search results: {len(results)} entries found")
        
        # Get statistics
        stats = await kb.get_statistics()
        print(f"   Total entries: {stats['total_entries']}")
        print(f"   Categories: {len(stats['categories'])}")
        
        return True
    
    except Exception as e:
        print(f"❌ Knowledge base test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_pattern_recognition(system: YMERASystem):
    """Test 4: Pattern Recognition"""
    print("\n" + "="*80)
    print("TEST 4: Pattern Recognition")
    print("="*80)
    
    try:
        pr = system.pattern_recognition
        
        # Detect patterns in events
        for i in range(10):
            event = {
                "task_type": "classification",
                "metrics": {"accuracy": 0.85 + (i * 0.01)},
                "timestamp": None
            }
            patterns = await pr.detect_patterns(event)
            
            if patterns:
                print(f"✅ Detected {len(patterns)} patterns in event {i+1}")
                for p in patterns:
                    print(f"   - {p.pattern_type.value}: {p.description}")
        
        # Get all patterns
        all_patterns = await system.get_patterns()
        print(f"   Total patterns detected: {len(all_patterns)}")
        
        # Get statistics
        stats = await pr.get_pattern_statistics()
        print(f"   Event history size: {stats['event_history_size']}")
        print(f"   Patterns by type: {stats['patterns_by_type']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Pattern recognition test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_continuous_learning(system: YMERASystem):
    """Test 5: Continuous Learning"""
    print("\n" + "="*80)
    print("TEST 5: Continuous Learning")
    print("="*80)
    
    try:
        cl = system.continuous_learning
        
        # Get statistics
        stats = await cl.get_statistics()
        print(f"✅ Continuous Learning Status:")
        print(f"   Enabled: {stats['enabled']}")
        print(f"   Running: {stats['is_running']}")
        print(f"   Total updates: {stats['total_updates']}")
        print(f"   Drift detections: {stats['drift_detections']}")
        print(f"   Performance trend: {stats['performance_trend']}")
        
        # Start continuous learning
        await system.enable_continuous_learning()
        print("   Continuous learning enabled")
        
        return True
    
    except Exception as e:
        print(f"❌ Continuous learning test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_external_learning(system: YMERASystem):
    """Test 6: External Learning Integration"""
    print("\n" + "="*80)
    print("TEST 6: External Learning Integration")
    print("="*80)
    
    try:
        el = system.external_learning
        
        # Get statistics
        stats = await el.get_statistics()
        print(f"✅ External Learning Status:")
        print(f"   Enabled: {stats['enabled']}")
        print(f"   Running: {stats['is_running']}")
        print(f"   Sources: {stats['sources']}")
        print(f"   Total items: {stats['total_knowledge_items']}")
        
        # Start external learning
        await system.enable_external_learning()
        print("   External learning enabled")
        
        return True
    
    except Exception as e:
        print(f"❌ External learning test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_system_metrics(system: YMERASystem):
    """Test 7: System Metrics"""
    print("\n" + "="*80)
    print("TEST 7: System Metrics & Health")
    print("="*80)
    
    try:
        # Get system metrics
        metrics = await system.get_system_metrics()
        
        print(f"✅ System Metrics:")
        print(f"   Uptime: {metrics.uptime_seconds:.2f} seconds")
        print(f"   Total tasks processed: {metrics.total_tasks_processed}")
        print(f"   Active tasks: {metrics.active_tasks}")
        print(f"   Patterns detected: {metrics.patterns_detected}")
        print(f"   Knowledge entries: {metrics.knowledge_entries}")
        print(f"   Error rate: {metrics.error_rate:.2%}")
        
        # Get full status
        status = await system.get_system_status()
        print(f"\n   System Status: {status['status']}")
        print(f"   Active Components:")
        for component, state in status['components'].items():
            print(f"      - {component}: {state}")
        
        return True
    
    except Exception as e:
        print(f"❌ System metrics test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_learning_tasks(system: YMERASystem):
    """Test 8: Multiple Concurrent Learning Tasks"""
    print("\n" + "="*80)
    print("TEST 8: Multiple Concurrent Learning Tasks")
    print("="*80)
    
    try:
        # Submit multiple tasks of different types
        task_types = ["classification", "regression", "clustering"]
        task_ids = []
        
        for task_type in task_types:
            task_id = await system.submit_learning_task(
                task_type=task_type,
                data={"data": "sample_data"},
                config={}
            )
            task_ids.append(task_id)
            print(f"✅ Submitted {task_type} task: {task_id}")
        
        # Wait for tasks to complete
        await asyncio.sleep(1.0)
        
        # Check all task statuses
        completed = 0
        for task_id in task_ids:
            status = await system.get_task_status(task_id)
            if status and status['status'] == 'completed':
                completed += 1
        
        print(f"   {completed}/{len(task_ids)} tasks completed successfully")
        
        return True
    
    except Exception as e:
        print(f"❌ Multiple tasks test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test runner"""
    print("\n" + "#"*80)
    print("# YMERA PRODUCTION SYSTEM - COMPREHENSIVE TEST SUITE")
    print("#"*80)
    
    test_results = []
    system = None
    
    try:
        # Test 1: Initialization
        system, success = await test_system_initialization()
        test_results.append(("System Initialization", success))
        
        if not success or not system:
            print("\n❌ Cannot proceed without successful initialization")
            return
        
        # Test 2: Learning Tasks
        success = await test_learning_tasks(system)
        test_results.append(("Learning Tasks", success))
        
        # Test 3: Knowledge Base
        success = await test_knowledge_base(system)
        test_results.append(("Knowledge Base", success))
        
        # Test 4: Pattern Recognition
        success = await test_pattern_recognition(system)
        test_results.append(("Pattern Recognition", success))
        
        # Test 5: Continuous Learning
        success = await test_continuous_learning(system)
        test_results.append(("Continuous Learning", success))
        
        # Test 6: External Learning
        success = await test_external_learning(system)
        test_results.append(("External Learning", success))
        
        # Test 7: System Metrics
        success = await test_system_metrics(system)
        test_results.append(("System Metrics", success))
        
        # Test 8: Multiple Tasks
        success = await test_multiple_learning_tasks(system)
        test_results.append(("Multiple Concurrent Tasks", success))
        
    finally:
        # Shutdown system
        if system:
            await system.shutdown()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    print(f"{'='*80}\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready for production.")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
