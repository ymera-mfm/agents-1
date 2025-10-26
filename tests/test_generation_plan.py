#!/usr/bin/env python3
"""
Test Generation Plan Creator
Creates specific test requirements for each coverage gap
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def create_test_plan() -> Dict[str, Any]:
    """Generate specific test requirements for each gap"""
    
    with open('agent_coverage_gaps.json', 'r') as f:
        gaps = json.load(f)
    
    test_plan = {
        "priority_1_not_covered": [],
        "priority_2_critical": [],
        "priority_3_improvement": [],
        "estimated_hours": 0,
        "summary": {}
    }
    
    # Not covered files - highest priority
    for gap in gaps["not_covered"]:
        statements = gap["total_statements"]
        # Estimate: 1 test per 10 statements, 0.5 hours per test
        estimated_tests = max(1, statements // 10)
        estimated_hours = estimated_tests * 0.5
        
        task = {
            "file": gap["file"],
            "filename": gap["filename"],
            "current_coverage": gap["coverage"],
            "target_coverage": 80.0,
            "total_statements": statements,
            "missing_statements": statements,
            "estimated_tests_needed": estimated_tests,
            "estimated_hours": estimated_hours,
            "test_file": f"tests/agents/test_{Path(gap['filename']).stem}.py",
            "priority": "CRITICAL - NO COVERAGE"
        }
        test_plan["priority_1_not_covered"].append(task)
        test_plan["estimated_hours"] += estimated_hours
    
    # Critical gaps (<60%) - high priority
    for gap in gaps["critical_gaps"]:
        missing = gap["missing_count"]
        # Estimate: 1 test per 15 statements, 0.3 hours per test
        estimated_tests = max(1, missing // 15)
        estimated_hours = estimated_tests * 0.3
        
        task = {
            "file": gap["file"],
            "filename": gap["filename"],
            "current_coverage": gap["coverage"],
            "target_coverage": 80.0,
            "total_statements": gap["total_statements"],
            "missing_statements": missing,
            "estimated_tests_needed": estimated_tests,
            "estimated_hours": estimated_hours,
            "test_file": f"tests/agents/test_{Path(gap['filename']).stem}.py",
            "priority": "HIGH - LOW COVERAGE"
        }
        test_plan["priority_2_critical"].append(task)
        test_plan["estimated_hours"] += estimated_hours
    
    # Needs improvement (60-80%) - medium priority
    for gap in gaps["needs_improvement"]:
        missing = gap["missing_count"]
        # Estimate: 1 test per 20 statements, 0.2 hours per test
        estimated_tests = max(1, missing // 20)
        estimated_hours = estimated_tests * 0.2
        
        task = {
            "file": gap["file"],
            "filename": gap["filename"],
            "current_coverage": gap["coverage"],
            "target_coverage": 85.0,
            "total_statements": gap["total_statements"],
            "missing_statements": missing,
            "estimated_tests_needed": estimated_tests,
            "estimated_hours": estimated_hours,
            "test_file": f"tests/agents/test_{Path(gap['filename']).stem}.py",
            "priority": "MEDIUM"
        }
        test_plan["priority_3_improvement"].append(task)
        test_plan["estimated_hours"] += estimated_hours
    
    # Calculate summary
    test_plan["summary"] = {
        "total_files_needing_tests": (len(test_plan["priority_1_not_covered"]) + 
                                     len(test_plan["priority_2_critical"]) + 
                                     len(test_plan["priority_3_improvement"])),
        "total_estimated_hours": f"{test_plan['estimated_hours']:.1f}",
        "not_covered_files": len(test_plan["priority_1_not_covered"]),
        "critical_files": len(test_plan["priority_2_critical"]),
        "improvement_files": len(test_plan["priority_3_improvement"]),
        "total_tests_to_write": sum(t["estimated_tests_needed"] for t in 
                                   test_plan["priority_1_not_covered"] + 
                                   test_plan["priority_2_critical"] + 
                                   test_plan["priority_3_improvement"]),
        "current_coverage": gaps["statistics"]["average_coverage"],
        "target_coverage": "80%",
        "gap_to_close": f"{80.0 - float(gaps['statistics']['average_coverage'].rstrip('%')):.1f}%"
    }
    
    return test_plan


if __name__ == "__main__":
    print("=" * 60)
    print("TEST GENERATION PLAN CREATOR")
    print("=" * 60)
    print()
    
    plan = create_test_plan()
    
    # Save plan
    output_file = "agent_test_plan.json"
    with open(output_file, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print("Test Plan Summary:")
    print("-" * 60)
    summary = plan["summary"]
    print(f"Total files needing tests: {summary['total_files_needing_tests']}")
    print(f"Total tests to write: {summary['total_tests_to_write']}")
    print(f"Total estimated hours: {summary['total_estimated_hours']}")
    print()
    print("By Priority:")
    print(f"  Not covered (Priority 1): {summary['not_covered_files']} files")
    print(f"  Critical (Priority 2):    {summary['critical_files']} files")
    print(f"  Improvement (Priority 3): {summary['improvement_files']} files")
    print()
    print("Coverage Goals:")
    print(f"  Current coverage:  {summary['current_coverage']}")
    print(f"  Target coverage:   {summary['target_coverage']}")
    print(f"  Gap to close:      {summary['gap_to_close']}")
    print()
    
    # Show top 5 priority files
    if plan["priority_1_not_covered"]:
        print("Top 5 Priority Files (Not Covered):")
        for idx, task in enumerate(plan["priority_1_not_covered"][:5], 1):
            print(f"  {idx}. {task['filename']}")
            print(f"     - Statements: {task['total_statements']}")
            print(f"     - Tests needed: {task['estimated_tests_needed']}")
            print(f"     - Estimated hours: {task['estimated_hours']:.1f}")
    
    print()
    print(f"Test plan saved to: {output_file}")
    print("=" * 60)
