#!/usr/bin/env python3
"""
Test Result Analyzer
Analyze comprehensive test results and classify failures
"""

import json


def analyze_test_results():
    """Analyze comprehensive test results"""
    
    with open('agent_test_results_complete.json', 'r') as f:
        results = json.load(f)
    
    analysis = {
        "working_agents": [],
        "broken_agents": [],
        "partially_working": [],
        "by_failure_type": {
            "initialization_failed": [],
            "missing_dependencies": [],
            "method_failures": [],
            "import_errors": []
        },
        "statistics": {}
    }
    
    for test_detail in results["test_details"]:
        agent_file = test_detail["agent_file"]
        status = test_detail["status"]
        
        if status == "PASS":
            analysis["working_agents"].append(agent_file)
        elif status == "ERROR":
            analysis["broken_agents"].append({
                "file": agent_file,
                "error": test_detail.get("error", "Unknown error")
            })
            
            # Classify error type
            error_msg = test_detail.get("error", "").lower()
            if "import" in error_msg or "module" in error_msg:
                analysis["by_failure_type"]["import_errors"].append(agent_file)
            elif "no module named" in error_msg:
                analysis["by_failure_type"]["missing_dependencies"].append(agent_file)
        elif status == "FAIL":
            # Check if partially working
            tests = test_detail.get("tests", {})
            if any(
                isinstance(t, dict)
                and "initialization" in t
                and isinstance(t["initialization"], dict)
                and "status" in t["initialization"]
                and t["initialization"]["status"] == "PASS"
                for t in tests.values()
            ):
                analysis["partially_working"].append(agent_file)
            else:
                analysis["broken_agents"].append({
                    "file": agent_file,
                    "reason": "Initialization failed"
                })
        elif status == "SKIP":
            # SKIP means no agent classes found, count as broken
            analysis["broken_agents"].append({
                "file": agent_file,
                "reason": test_detail.get("reason", "Skipped")
            })
    
    # Statistics
    total = len(results["test_details"])
    analysis["statistics"] = {
        "total_tested": total,
        "fully_working": len(analysis["working_agents"]),
        "partially_working": len(analysis["partially_working"]),
        "broken": len(analysis["broken_agents"]),
        "working_percentage": f"{len(analysis['working_agents']) / total * 100:.1f}%" if total > 0 else "0%",
        "broken_percentage": f"{len(analysis['broken_agents']) / total * 100:.1f}%" if total > 0 else "0%"
    }
    
    with open('agent_test_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    return analysis


if __name__ == "__main__":
    analysis = analyze_test_results()
    print(json.dumps(analysis["statistics"], indent=2))
