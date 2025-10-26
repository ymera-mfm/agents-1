#!/usr/bin/env python3
"""
Generate agent_coverage.json based on actual test results
Uses MEASURED data from test execution
"""

import json
from datetime import datetime
from pathlib import Path


def generate_coverage_data():
    """Generate coverage data from test results"""
    
    # Load test results
    with open('agent_test_results_complete.json', 'r') as f:
        test_data = json.load(f)
    
    # Load agent catalog
    with open('agent_catalog_complete.json', 'r') as f:
        catalog_data = json.load(f)
    
    # Calculate coverage metrics
    metrics = test_data.get('metrics', {})
    agents_tested = metrics.get('agents_tested', 0)
    total_agents = catalog_data.get('metrics', {}).get('total_agents', 0)
    
    # Calculate coverage percentage
    agent_coverage_pct = (agents_tested / total_agents * 100) if total_agents > 0 else 0
    
    # Calculate test coverage (from test results)
    tests_passed = metrics.get('tests_passed', 0)
    total_tests = metrics.get('total_tests', 0)
    test_coverage_pct = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Identify agents with low/no coverage
    test_results = test_data.get('test_results', [])
    
    uncovered_agents = []
    partially_covered = []
    fully_covered = []
    
    for result in test_results:
        agent_name = result.get('agent_name', 'Unknown')
        status = result.get('status', 'UNKNOWN')
        tests_run = result.get('tests_run', 0)
        
        if status == 'FAILED' or tests_run == 0:
            uncovered_agents.append({
                "agent": agent_name,
                "file": result.get('file', 'Unknown'),
                "reason": result.get('error', 'No tests run')[:100]
            })
        elif tests_run < 3:  # Less than 3 tests is considered partial
            partially_covered.append({
                "agent": agent_name,
                "tests_run": tests_run
            })
        else:
            fully_covered.append({
                "agent": agent_name,
                "tests_run": tests_run
            })
    
    # Create coverage data structure
    coverage_data = {
        "coverage_timestamp": datetime.now().isoformat(),
        "measurement_method": "Actual test execution via agent_test_runner_complete.py",
        "coverage_type": "Agent testing coverage (not line coverage)",
        "note": "This represents agents tested, not code line coverage. For line coverage, run pytest --cov",
        
        "summary": {
            "total_agents": total_agents,
            "agents_tested": agents_tested,
            "agent_coverage_percentage": round(agent_coverage_pct, 2),
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "test_pass_percentage": round(test_coverage_pct, 2)
        },
        
        "coverage_breakdown": {
            "fully_covered": len(fully_covered),
            "partially_covered": len(partially_covered),
            "uncovered": len(uncovered_agents)
        },
        
        "uncovered_agents": uncovered_agents[:50],  # Limit to first 50
        "partially_covered_agents": partially_covered[:20],  # Limit to first 20
        
        "coverage_gaps": [
            {
                "gap": "Low test pass rate",
                "impact": f"{metrics.get('agents_failed', 0)} agents failing tests",
                "reason": "Missing dependencies (anthropic, openai, etc.)",
                "priority": "high"
            },
            {
                "gap": "Untested agents",
                "impact": f"{total_agents - agents_tested} agents not tested",
                "reason": "Not included in test runner catalog",
                "priority": "medium"
            }
        ],
        
        "measurement_metadata": {
            "test_timestamp": test_data.get('test_timestamp'),
            "test_duration_ms": metrics.get('duration_ms', 0),
            "environment": {
                "python_version": "3.12.3",
                "test_framework": "agent_test_runner_complete.py"
            }
        }
    }
    
    return coverage_data


def main():
    """Generate and save coverage data"""
    print("=" * 70)
    print("GENERATING AGENT COVERAGE DATA")
    print("=" * 70)
    print()
    
    coverage_data = generate_coverage_data()
    
    # Save to file
    output_file = "agent_coverage.json"
    with open(output_file, 'w') as f:
        json.dump(coverage_data, f, indent=2)
    
    # Print summary
    summary = coverage_data['summary']
    print("📊 COVERAGE SUMMARY:")
    print(f"  Total Agents: {summary['total_agents']}")
    print(f"  Agents Tested: {summary['agents_tested']}")
    print(f"  Agent Coverage: {summary['agent_coverage_percentage']}%")
    print(f"  Test Pass Rate: {summary['test_pass_percentage']}%")
    print()
    
    breakdown = coverage_data['coverage_breakdown']
    print("📈 BREAKDOWN:")
    print(f"  Fully Covered: {breakdown['fully_covered']}")
    print(f"  Partially Covered: {breakdown['partially_covered']}")
    print(f"  Uncovered: {breakdown['uncovered']}")
    print()
    
    print(f"✅ Coverage data saved to: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
