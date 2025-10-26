#!/usr/bin/env python3
"""
Agent Framework Validation Script
Tests that the framework is properly set up and working.
"""

import sys
import json
from pathlib import Path

def test_imports():
    """Test that all framework imports work."""
    print("Testing framework imports...")
    try:
        from agents.agent_base import (
            BaseAgent,
            AgentConfig,
            AgentCapability,
            TaskRequest,
            TaskResponse,
            Priority,
            TaskStatus
        )
        from agents.shared_utils import (
            load_config,
            save_config,
            get_env_var,
            validate_payload,
            format_error,
            sanitize_string,
            merge_dicts
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_example_agents():
    """Test that example agents work."""
    print("\nTesting example agents...")
    
    agents_dir = Path("agents")
    example_agents = [
        "example_agent_fixed.py",
        "calculator_agent.py",
        "data_processor_agent.py"
    ]
    
    all_passed = True
    for agent_file in example_agents:
        agent_path = agents_dir / agent_file
        if agent_path.exists():
            print(f"  Testing {agent_file}...")
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, str(agent_path)],
                    capture_output=True,
                    timeout=10,
                    text=True
                )
                if result.returncode == 0:
                    print(f"    ✅ {agent_file} passed")
                else:
                    print(f"    ❌ {agent_file} failed")
                    print(f"       {result.stderr}")
                    all_passed = False
            except Exception as e:
                print(f"    ❌ {agent_file} error: {e}")
                all_passed = False
        else:
            print(f"  ⚠️ {agent_file} not found")
            all_passed = False
    
    return all_passed


def test_framework_features():
    """Test core framework features."""
    print("\nTesting framework features...")
    
    try:
        from agents.agent_base import (
            BaseAgent,
            AgentConfig,
            AgentCapability,
            TaskRequest,
            Priority
        )
        
        # Test 1: Create agent config
        config = AgentConfig(
            name="TestAgent",
            description="Test agent",
            capabilities=[]
        )
        print("  ✅ AgentConfig creation")
        
        # Test 2: Create capability
        capability = AgentCapability(
            name="test",
            description="Test capability",
            task_types=["test"],
            required_params=["param1"]
        )
        print("  ✅ AgentCapability creation")
        
        # Test 3: Create task request
        task = TaskRequest(
            task_type="test",
            priority=Priority.MEDIUM,
            payload={"param1": "value1"}
        )
        print("  ✅ TaskRequest creation")
        
        # Test 4: Convert to dict
        task_dict = task.to_dict()
        print("  ✅ TaskRequest serialization")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Framework test failed: {e}")
        return False


def check_documentation():
    """Check that documentation exists."""
    print("\nChecking documentation...")
    
    docs = [
        "AGENT_FIX_GUIDE.md",
        "AGENT_FIX_IMPLEMENTATION_SUMMARY.md",
        "agents/README.md",
        "fix_log.md"
    ]
    
    all_exist = True
    for doc in docs:
        doc_path = Path(doc)
        if doc_path.exists():
            size = doc_path.stat().st_size
            print(f"  ✅ {doc} ({size} bytes)")
        else:
            print(f"  ❌ {doc} not found")
            all_exist = False
    
    return all_exist


def check_analysis():
    """Check dependency analysis."""
    print("\nChecking dependency analysis...")
    
    analysis_file = Path("agent_dependency_analysis_new.json")
    if analysis_file.exists():
        try:
            with open(analysis_file) as f:
                data = json.load(f)
            
            summary = data.get("summary", {})
            print(f"  ✅ Analysis file exists")
            print(f"     Total agents: {summary.get('total_agents', 0)}")
            print(f"     Level 0 (independent): {summary.get('level_0_independent', 0)}")
            print(f"     Level 1 (minimal): {summary.get('level_1_minimal', 0)}")
            print(f"     Level 2 (moderate): {summary.get('level_2_moderate', 0)}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to read analysis: {e}")
            return False
    else:
        print(f"  ❌ Analysis file not found")
        return False


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("YMERA Agent Framework Validation")
    print("=" * 70)
    
    results = {
        "imports": test_imports(),
        "examples": test_example_agents(),
        "features": test_framework_features(),
        "documentation": check_documentation(),
        "analysis": check_analysis()
    }
    
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    total = len(results)
    passed = sum(results.values())
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed! Framework is ready.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
