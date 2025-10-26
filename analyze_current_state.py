#!/usr/bin/env python3
"""
Analyze the current state of agent system completion
Provides a clear summary of what's done and what's missing
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def load_json_file(filename: str) -> Dict[str, Any]:
    """Load a JSON file safely"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "File not found"}
    except Exception as e:
        return {"error": str(e)}


def analyze_state() -> Dict[str, Any]:
    """Analyze the current state of all deliverables"""
    
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "deliverables": {},
        "gaps": [],
        "recommendations": []
    }
    
    # Check JSON files
    json_files = [
        "agent_catalog_complete.json",
        "agent_classification.json",
        "agent_test_results_complete.json",
        "agent_coverage.json",
        "agent_benchmarks_complete.json",
        "agent_fixes_applied.json",
        "integration_results.json"
    ]
    
    for filename in json_files:
        path = Path(filename)
        if path.exists():
            data = load_json_file(filename)
            size = path.stat().st_size
            analysis["deliverables"][filename] = {
                "status": "exists",
                "size_bytes": size,
                "has_error": "error" in data
            }
        else:
            analysis["deliverables"][filename] = {
                "status": "missing",
                "size_bytes": 0
            }
            analysis["gaps"].append(f"Missing file: {filename}")
    
    # Check markdown reports
    md_files = [
        "AGENT_INVENTORY_REPORT.md",
        "AGENT_COVERAGE_REPORT.md",
        "AGENT_TESTING_REPORT.md",
        "AGENT_PERFORMANCE_REPORT.md",
        "AGENT_SYSTEM_ARCHITECTURE.md",
        "INTEGRATION_TEST_REPORT.md",
        "AGENT_SYSTEM_FINAL_REPORT.md"
    ]
    
    for filename in md_files:
        path = Path(filename)
        if path.exists():
            size = path.stat().st_size
            analysis["deliverables"][filename] = {
                "status": "exists",
                "size_bytes": size,
                "needs_update": size < 1000  # Flag small files for review
            }
            if size < 1000:
                analysis["gaps"].append(f"Small report: {filename} ({size} bytes)")
        else:
            analysis["deliverables"][filename] = {
                "status": "missing",
                "size_bytes": 0
            }
            analysis["gaps"].append(f"Missing report: {filename}")
    
    # Analyze specific files
    catalog = load_json_file("agent_catalog_complete.json")
    if "error" not in catalog:
        total_agents = catalog.get("metrics", {}).get("total_agents", 0)
        analysis["total_agents"] = total_agents
    
    tests = load_json_file("agent_test_results_complete.json")
    if "error" not in tests:
        metrics = tests.get("metrics", {})
        analysis["test_metrics"] = {
            "agents_tested": metrics.get("agents_tested", 0),
            "agents_passed": metrics.get("agents_passed", 0),
            "agents_failed": metrics.get("agents_failed", 0),
            "pass_rate": tests.get("pass_rate", "0%")
        }
    
    benchmarks = load_json_file("agent_benchmarks_complete.json")
    if "error" not in benchmarks:
        num_benchmarked = len(benchmarks.get("benchmarks", []))
        analysis["benchmarked_agents"] = num_benchmarked
        if "total_agents" in analysis and num_benchmarked < analysis["total_agents"]:
            analysis["gaps"].append(
                f"Only {num_benchmarked}/{analysis['total_agents']} agents benchmarked"
            )
    
    integration = load_json_file("integration_results.json")
    if "error" not in integration:
        status = integration.get("status", "unknown")
        analysis["integration_status"] = status
        if status != "complete":
            analysis["gaps"].append(f"Integration testing incomplete: {status}")
    
    # Generate recommendations
    if analysis["gaps"]:
        analysis["recommendations"].append("Complete missing deliverables")
    if "test_metrics" in analysis:
        pass_rate_str = analysis["test_metrics"].get("pass_rate", "0%")
        pass_rate = float(pass_rate_str.rstrip("%"))
        if pass_rate < 80:
            analysis["recommendations"].append(
                f"Improve pass rate (currently {pass_rate_str})"
            )
    
    return analysis


def print_analysis(analysis: Dict[str, Any]):
    """Print the analysis in a readable format"""
    print("=" * 70)
    print("AGENT SYSTEM COMPLETION - CURRENT STATE ANALYSIS")
    print("=" * 70)
    print(f"Analysis Time: {analysis['timestamp']}")
    print()
    
    # Summary metrics
    print("📊 KEY METRICS:")
    if "total_agents" in analysis:
        print(f"  Total Agents: {analysis['total_agents']}")
    if "test_metrics" in analysis:
        tm = analysis["test_metrics"]
        print(f"  Tested: {tm['agents_tested']}")
        print(f"  Passed: {tm['agents_passed']} ({tm['pass_rate']})")
    if "benchmarked_agents" in analysis:
        print(f"  Benchmarked: {analysis['benchmarked_agents']}")
    if "integration_status" in analysis:
        print(f"  Integration Status: {analysis['integration_status']}")
    print()
    
    # Deliverables status
    print("📦 DELIVERABLES STATUS:")
    json_count = sum(1 for k, v in analysis["deliverables"].items() 
                     if k.endswith(".json") and v["status"] == "exists")
    md_count = sum(1 for k, v in analysis["deliverables"].items() 
                   if k.endswith(".md") and v["status"] == "exists")
    total_json = 7
    total_md = 7
    print(f"  JSON Files: {json_count}/{total_json}")
    print(f"  Markdown Reports: {md_count}/{total_md}")
    print()
    
    # Gaps
    if analysis["gaps"]:
        print("⚠️  GAPS IDENTIFIED:")
        for gap in analysis["gaps"]:
            print(f"  • {gap}")
        print()
    
    # Recommendations
    if analysis["recommendations"]:
        print("💡 RECOMMENDATIONS:")
        for rec in analysis["recommendations"]:
            print(f"  • {rec}")
        print()
    
    # Completion percentage
    total_deliverables = len(analysis["deliverables"])
    completed = sum(1 for v in analysis["deliverables"].values() 
                   if v["status"] == "exists")
    completion_pct = (completed / total_deliverables * 100) if total_deliverables > 0 else 0
    
    print(f"✅ COMPLETION: {completion_pct:.1f}% ({completed}/{total_deliverables} deliverables)")
    print("=" * 70)


def main():
    """Main entry point"""
    analysis = analyze_state()
    print_analysis(analysis)
    
    # Save analysis
    output_file = "current_state_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"\n📝 Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
