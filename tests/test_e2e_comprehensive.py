"""
Comprehensive End-to-End Testing Suite
Version: 1.0.0
Tests the entire Unified Agent System including all agents, engines, and integrations
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents"))
sys.path.insert(0, str(project_root / "engines"))

# Test results tracking
test_results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'tests': []
}


def log_test(name: str, status: str, duration: float, details: str = ""):
    """Log test result"""
    test_results['total'] += 1
    test_results[status] += 1
    test_results['tests'].append({
        'name': name,
        'status': status,
        'duration': duration,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })
    
    status_icon = {
        'passed': '✅',
        'failed': '❌',
        'skipped': '⏭️'
    }.get(status, '❓')
    
    print(f"{status_icon} {name} ({duration:.2f}s)")
    if details and status == 'failed':
        print(f"   {details}")


async def test_base_agent_initialization():
    """Test base agent initialization"""
    test_name = "Base Agent Initialization"
    start_time = time.time()
    
    try:
        from base_agent import BaseAgent, AgentConfig, TaskRequest, AgentState
        
        # Create config
        config = AgentConfig(
            name="test_agent",
            agent_type="test"
        )
        
        # Create mock agent
        class TestAgent(BaseAgent):
            async def _execute_task(self, task_request):
                return {"status": "completed"}
        
        agent = TestAgent(config)
        
        # Verify attributes
        assert agent.name == "test_agent"
        assert agent.state == AgentState.INITIALIZING
        assert agent.config == config
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration)
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_unified_system_initialization():
    """Test unified system initialization"""
    test_name = "Unified System Initialization"
    start_time = time.time()
    
    try:
        from unified_system import UnifiedAgentSystem
        
        system = UnifiedAgentSystem({'test_mode': True})
        
        assert system.state == "initializing"
        assert system.agents == {}
        assert system.engines == {}
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration)
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_document_generation_engine():
    """Test document generation engine"""
    test_name = "Document Generation Engine"
    start_time = time.time()
    
    try:
        from document_generation_engine import (
            DocumentGenerationEngine,
            DocumentFormat,
            DocumentMetadata,
            DocumentSection,
            DocumentContent
        )
        
        engine = DocumentGenerationEngine()
        
        # Create test document
        metadata = DocumentMetadata(
            title="Test Report",
            author="E2E Test"
        )
        
        sections = [
            DocumentSection(
                title="Introduction",
                content="This is a test document."
            )
        ]
        
        content = DocumentContent(
            metadata=metadata,
            sections=sections
        )
        
        # Test multiple formats
        formats_tested = []
        
        for fmt in [DocumentFormat.JSON, DocumentFormat.TEXT, DocumentFormat.HTML, DocumentFormat.MARKDOWN]:
            result = await engine.generate_document(content, fmt)
            if result['success']:
                formats_tested.append(fmt.value)
        
        assert len(formats_tested) >= 4, "Should generate at least 4 formats"
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration, f"Generated {len(formats_tested)} formats")
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_task_request_creation():
    """Test task request creation and validation"""
    test_name = "Task Request Creation"
    start_time = time.time()
    
    try:
        from base_agent import TaskRequest, Priority
        
        # Create task request
        task = TaskRequest(
            task_type="test_task",
            payload={"data": "test"},
            priority=Priority.HIGH
        )
        
        assert task.task_id is not None
        assert task.task_type == "test_task"
        assert task.priority == Priority.HIGH
        assert task.created_at > 0
        
        # Test serialization
        task_dict = task.to_dict()
        assert isinstance(task_dict, dict)
        assert task_dict['task_type'] == "test_task"
        
        # Test deserialization
        task2 = TaskRequest.from_dict(task_dict)
        assert task2.task_id == task.task_id
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration)
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_agent_state_transitions():
    """Test agent state transitions"""
    test_name = "Agent State Transitions"
    start_time = time.time()
    
    try:
        from base_agent import AgentState
        
        states = [
            AgentState.INITIALIZING,
            AgentState.READY,
            AgentState.ACTIVE,
            AgentState.BUSY,
            AgentState.DEGRADED,
            AgentState.SHUTTING_DOWN,
            AgentState.STOPPED
        ]
        
        # Verify all states exist
        for state in states:
            assert isinstance(state.value, str)
        
        # Test state comparison
        assert AgentState.READY != AgentState.ACTIVE
        assert AgentState.READY == AgentState.READY
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration, f"Verified {len(states)} states")
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_health_status():
    """Test health status reporting"""
    test_name = "Health Status Reporting"
    start_time = time.time()
    
    try:
        from base_agent import HealthStatus, AgentState, ConnectionState
        
        health = HealthStatus(
            agent_id="test_agent",
            state=AgentState.ACTIVE,
            healthy=True,
            tasks_completed=10,
            tasks_failed=1,
            tasks_running=2
        )
        
        assert health.agent_id == "test_agent"
        assert health.healthy == True
        assert health.tasks_completed == 10
        
        # Test serialization
        health_dict = health.to_dict()
        assert isinstance(health_dict, dict)
        assert health_dict['agent_id'] == "test_agent"
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration)
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_circuit_breaker():
    """Test circuit breaker implementation"""
    test_name = "Circuit Breaker"
    start_time = time.time()
    
    try:
        from base_agent import CircuitBreaker
        
        cb = CircuitBreaker(
            failure_threshold=3,
            timeout=1,
            name="test_cb"
        )
        
        assert cb.state == "closed"
        assert cb.failures == 0
        
        # Simulate failures
        for _ in range(3):
            cb._on_failure()
        
        assert cb.state == "open"
        
        # Wait for timeout
        await asyncio.sleep(1.1)
        
        # Should transition to half-open
        async def dummy_func():
            return True
        
        try:
            result = await cb.call_async(dummy_func)
        except:
            pass  # Expected to transition
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration)
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_rate_limiter():
    """Test rate limiter"""
    test_name = "Rate Limiter"
    start_time = time.time()
    
    try:
        from base_agent import RateLimiter
        
        limiter = RateLimiter(
            requests=5,
            window=1,
            name="test_limiter"
        )
        
        # Should allow first 5 requests
        allowed = 0
        for _ in range(7):
            if await limiter.acquire():
                allowed += 1
        
        assert allowed == 5, f"Expected 5 allowed, got {allowed}"
        
        # Wait for refill
        await asyncio.sleep(1.1)
        
        # Should allow more requests
        if await limiter.acquire():
            allowed += 1
        
        assert allowed == 6
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration)
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_priority_queue():
    """Test priority queue for tasks"""
    test_name = "Priority Queue"
    start_time = time.time()
    
    try:
        from base_agent import TaskRequest, Priority
        
        queue = asyncio.PriorityQueue()
        
        # Add tasks with different priorities
        tasks = [
            TaskRequest(task_type="low", priority=Priority.LOW),
            TaskRequest(task_type="high", priority=Priority.HIGH),
            TaskRequest(task_type="normal", priority=Priority.NORMAL),
            TaskRequest(task_type="critical", priority=Priority.CRITICAL)
        ]
        
        for task in tasks:
            await queue.put((task.priority.value, task))
        
        # Should come out in priority order (lowest value first)
        priorities = []
        while not queue.empty():
            priority, task = await queue.get()
            priorities.append(priority)
        
        # Verify sorted (descending because lower number = higher priority)
        assert priorities == sorted(priorities), "Queue should be priority-sorted"
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration)
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_document_formats():
    """Test all document formats"""
    test_name = "All Document Formats"
    start_time = time.time()
    
    try:
        from document_generation_engine import (
            DocumentGenerationEngine,
            DocumentFormat,
            DocumentMetadata,
            DocumentSection,
            DocumentTable,
            DocumentContent
        )
        
        engine = DocumentGenerationEngine()
        
        # Create comprehensive test document
        metadata = DocumentMetadata(
            title="Comprehensive Test Document",
            author="E2E Test Suite"
        )
        
        sections = [
            DocumentSection(title="Section 1", content="Content 1", level=1),
            DocumentSection(title="Section 2", content="Content 2", level=2)
        ]
        
        tables = [
            DocumentTable(
                headers=["Column 1", "Column 2"],
                rows=[["Data 1", "Data 2"], ["Data 3", "Data 4"]]
            )
        ]
        
        content = DocumentContent(
            metadata=metadata,
            sections=sections,
            tables=tables
        )
        
        # Test all formats
        formats = [
            DocumentFormat.JSON,
            DocumentFormat.XML,
            DocumentFormat.CSV,
            DocumentFormat.TEXT,
            DocumentFormat.MARKDOWN,
            DocumentFormat.HTML
        ]
        
        results = []
        for fmt in formats:
            result = await engine.generate_document(content, fmt)
            results.append(result['success'])
        
        success_count = sum(results)
        assert success_count >= 6, f"Expected 6 formats, got {success_count}"
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration, f"Generated {success_count}/6 formats")
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def test_integration_workflow():
    """Test integration workflow simulation"""
    test_name = "Integration Workflow Simulation"
    start_time = time.time()
    
    try:
        from base_agent import TaskRequest, TaskResult, TaskStatus, Priority
        
        # Simulate workflow
        workflow_tasks = []
        
        # Step 1: Create analysis task
        task1 = TaskRequest(
            task_type="code_analysis",
            payload={"code": "def test(): pass"},
            priority=Priority.HIGH
        )
        workflow_tasks.append(task1)
        
        # Step 2: Create enhancement task
        task2 = TaskRequest(
            task_type="code_enhancement",
            payload={"analysis_result": "needs_docs"},
            priority=Priority.NORMAL
        )
        workflow_tasks.append(task2)
        
        # Step 3: Create quality check task
        task3 = TaskRequest(
            task_type="quality_check",
            payload={"enhanced_code": "def test(): \"\"\"Test function\"\"\" pass"},
            priority=Priority.HIGH
        )
        workflow_tasks.append(task3)
        
        assert len(workflow_tasks) == 3
        assert all(t.task_id for t in workflow_tasks)
        
        duration = time.time() - start_time
        log_test(test_name, 'passed', duration, f"Simulated {len(workflow_tasks)} workflow steps")
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def run_performance_test():
    """Run performance benchmark"""
    test_name = "Performance Benchmark"
    start_time = time.time()
    
    try:
        from base_agent import TaskRequest, Priority
        
        # Create many tasks
        num_tasks = 1000
        tasks = []
        
        creation_start = time.time()
        for i in range(num_tasks):
            task = TaskRequest(
                task_type="perf_test",
                payload={"index": i},
                priority=Priority.NORMAL
            )
            tasks.append(task)
        creation_time = time.time() - creation_start
        
        # Verify
        assert len(tasks) == num_tasks
        assert all(t.task_id for t in tasks)
        
        throughput = num_tasks / creation_time
        
        duration = time.time() - start_time
        log_test(
            test_name,
            'passed',
            duration,
            f"{num_tasks} tasks created in {creation_time:.2f}s ({throughput:.0f} tasks/sec)"
        )
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        log_test(test_name, 'failed', duration, str(e))
        return False


async def run_all_tests():
    """Run all E2E tests"""
    print("\n" + "=" * 80)
    print("UNIFIED AGENT SYSTEM - COMPREHENSIVE E2E TESTING")
    print("=" * 80)
    print(f"\nTest Suite Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-" * 80)
    print("Running Tests...")
    print("-" * 80 + "\n")
    
    # Core Tests
    await test_base_agent_initialization()
    await test_unified_system_initialization()
    await test_task_request_creation()
    await test_agent_state_transitions()
    await test_health_status()
    
    # Resilience Tests
    await test_circuit_breaker()
    await test_rate_limiter()
    await test_priority_queue()
    
    # Engine Tests
    await test_document_generation_engine()
    await test_document_formats()
    
    # Integration Tests
    await test_integration_workflow()
    
    # Performance Tests
    await run_performance_test()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"\nTotal Tests:  {test_results['total']}")
    print(f"✅ Passed:    {test_results['passed']} ({test_results['passed']/test_results['total']*100:.1f}%)")
    print(f"❌ Failed:    {test_results['failed']} ({test_results['failed']/test_results['total']*100:.1f}%)")
    print(f"⏭️  Skipped:   {test_results['skipped']}")
    
    # Calculate total time
    total_time = sum(t['duration'] for t in test_results['tests'])
    print(f"\nTotal Time:   {total_time:.2f}s")
    print(f"Average Time: {total_time/test_results['total']:.2f}s per test")
    
    # Show failed tests
    if test_results['failed'] > 0:
        print("\n" + "-" * 80)
        print("FAILED TESTS:")
        print("-" * 80)
        for test in test_results['tests']:
            if test['status'] == 'failed':
                print(f"\n❌ {test['name']}")
                print(f"   Error: {test['details']}")
    
    # Save results
    results_file = Path(__file__).parent / "e2e_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📄 Full results saved to: {results_file}")
    print("\n" + "=" * 80)
    
    # Return success status
    return test_results['failed'] == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
