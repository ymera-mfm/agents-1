#!/usr/bin/env python3
"""
Actual Agent Testing - Measures real state with evidence
Tests all agents and generates detailed metrics
"""

import sys
import json
import importlib.util
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

def test_agent_import(agent_file: Path) -> Tuple[bool, str, str]:
    """
    Test if an agent can be imported.
    Returns: (success, error_type, error_message)
    """
    try:
        spec = importlib.util.spec_from_file_location("test_module", agent_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return (True, None, None)
    except ModuleNotFoundError as e:
        return (False, "ModuleNotFoundError", str(e))
    except ImportError as e:
        return (False, "ImportError", str(e))
    except SyntaxError as e:
        return (False, "SyntaxError", str(e))
    except Exception as e:
        return (False, type(e).__name__, str(e))

def test_all_agents() -> Dict[str, Any]:
    """Test all agent files and return results."""
    
    # Find all agent files in root
    agent_files = sorted(Path(".").glob("*_agent.py"))
    
    results = {
        "test_timestamp": datetime.now().isoformat(),
        "total_agents": len(agent_files),
        "passed": 0,
        "failed": 0,
        "agents": []
    }
    
    error_types = {}
    
    for agent_file in agent_files:
        print(f"Testing {agent_file.name}...", end=" ")
        
        success, error_type, error_msg = test_agent_import(agent_file)
        
        agent_result = {
            "file": agent_file.name,
            "success": success,
            "error_type": error_type,
            "error_message": error_msg
        }
        
        results["agents"].append(agent_result)
        
        if success:
            results["passed"] += 1
            print("✅ PASS")
        else:
            results["failed"] += 1
            print(f"❌ FAIL ({error_type})")
            
            # Count error types
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(agent_file.name)
    
    results["error_types"] = error_types
    results["pass_rate"] = (results["passed"] / results["total_agents"] * 100) if results["total_agents"] > 0 else 0
    
    return results

def main():
    """Run tests and generate report."""
    print("=" * 80)
    print("ACTUAL AGENT TESTING - WITH EVIDENCE")
    print("=" * 80)
    print()
    
    # Run tests
    results = test_all_agents()
    
    # Save results
    output_file = "agent_test_actual_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY - MEASURED RESULTS")
    print("=" * 80)
    print(f"Total Agents Tested: {results['total_agents']}")
    print(f"✅ Passed: {results['passed']} ({results['passed']/results['total_agents']*100:.1f}%)")
    print(f"❌ Failed: {results['failed']} ({results['failed']/results['total_agents']*100:.1f}%)")
    print(f"📊 Pass Rate: {results['pass_rate']:.1f}%")
    print()
    
    # Error breakdown
    if results["error_types"]:
        print("Error Breakdown by Type:")
        for error_type, agents in sorted(results["error_types"].items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {error_type}: {len(agents)} agents")
            for agent in agents[:3]:
                print(f"    - {agent}")
            if len(agents) > 3:
                print(f"    ... and {len(agents) - 3} more")
    
    print()
    print(f"📝 Detailed results saved to: {output_file}")
    print("=" * 80)
    
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
