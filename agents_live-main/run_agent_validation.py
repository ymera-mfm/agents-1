#!/usr/bin/env python3
"""
Complete Agent System Validation Runner
Master script to run all analysis and generate all reports
"""

import subprocess
import sys
import os
from datetime import datetime


def run_command(description, command):
    """Run a command and report results"""
    print()
    print("=" * 70)
    print(f"RUNNING: {description}")
    print("=" * 70)
    print()
    
    result = subprocess.run(command, shell=True, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n⚠️  Warning: {description} exited with code {result.returncode}")
        return False
    
    print(f"\n✅ {description} completed successfully")
    return True


def main():
    """Run complete agent system validation"""
    
    print("=" * 70)
    print("COMPLETE AGENT SYSTEM VALIDATION")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Track results
    results = {}
    
    # Phase 1: Agent Discovery & Cataloging
    print()
    print("🔍 PHASE 1: AGENT DISCOVERY & CATALOGING")
    print("=" * 70)
    
    # Step 1: Find agent files
    results["find_agents"] = run_command(
        "Finding agent files",
        "find . -name '*agent*.py' -o -name '*Agent*.py' | grep -v __pycache__ | grep -v .git > /tmp/agent_files_found.txt"
    )
    
    # Step 2: Catalog agents
    results["catalog"] = run_command(
        "Cataloging agents",
        "python agent_catalog_analyzer.py"
    )
    
    # Step 3: Classify agents
    results["classify"] = run_command(
        "Classifying agents",
        "python agent_classifier.py"
    )
    
    # Step 4: Generate visual map
    results["map"] = run_command(
        "Generating agent map",
        "python agent_mapper.py"
    )
    
    # Step 5: Generate inventory report
    results["inventory_report"] = run_command(
        "Generating inventory report",
        "python generate_inventory_report.py"
    )
    
    # Phase 2: Coverage Analysis
    print()
    print("📊 PHASE 2: COVERAGE ANALYSIS")
    print("=" * 70)
    
    # Step 6: Run coverage
    results["coverage"] = run_command(
        "Running coverage analysis",
        "pytest tests/ -v --cov=. --cov-report=json:agent_coverage.json --cov-report=html:agent_coverage_html --cov-report=term-missing --cov-report=xml:agent_coverage.xml"
    )
    
    # Step 7: Analyze coverage gaps
    results["gaps"] = run_command(
        "Analyzing coverage gaps",
        "python coverage_gap_analyzer.py"
    )
    
    # Step 8: Generate test plan
    results["test_plan"] = run_command(
        "Generating test plan",
        "python test_generation_plan.py"
    )
    
    # Step 9: Generate coverage report
    results["coverage_report"] = run_command(
        "Generating coverage report",
        "python generate_coverage_report.py"
    )
    
    # Summary
    print()
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print()
    
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Results: {successful}/{total} steps completed successfully")
    print()
    
    print("Generated Files:")
    files = [
        "agent_catalog_complete.json",
        "agent_classification.json",
        "agent_system_map.png",
        "AGENT_INVENTORY_REPORT.md",
        "agent_coverage.json",
        "agent_coverage_html/index.html",
        "agent_coverage_gaps.json",
        "agent_test_plan.json",
        "AGENT_COVERAGE_REPORT.md"
    ]
    
    for file in files:
        exists = "✅" if os.path.exists(file) else "❌"
        print(f"  {exists} {file}")
    
    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return 0 if successful == total else 1


if __name__ == "__main__":
    sys.exit(main())
