#!/usr/bin/env python3
logger = logging.getLogger(__name__)

"""
Generate Agent Testing Report
Creates comprehensive markdown report with actual test results
"""

import logging

import json
from datetime import datetime
from collections import defaultdict


def generate_report():
    """Generate comprehensive testing report"""
    
    # Load test results
    with open('agent_test_results_complete.json', 'r') as f:
        results = json.load(f)
    
    # Load analysis
    with open('agent_test_analysis.json', 'r') as f:
        analysis = json.load(f)
    
    # Count failure types
    failure_types = defaultdict(int)
    error_messages = defaultdict(list)
    
    for test in results["test_details"]:
        status = test["status"]
        if status == "ERROR":
            error = test.get("error", "Unknown error")
            if "No module named" in error:
                module = error.split("'")[1] if "'" in error else "unknown"
                failure_types[f"Missing module: {module}"] += 1
                error_messages[f"Missing module: {module}"].append(test["agent_file"])
            elif "import" in error.lower():
                failure_types["Import error"] += 1
                error_messages["Import error"].append(test["agent_file"])
            else:
                failure_types["Other error"] += 1
                error_messages["Other error"].append(test["agent_file"])
        elif status == "FAIL":
            # Check if it's initialization failure
            has_init_failure = False
            for agent_name, agent_test in test.get("tests", {}).items():
                if agent_test["initialization"]["status"] == "FAIL":
                    failure_types["Initialization failure"] += 1
                    error_messages["Initialization failure"].append(f"{test['agent_file']} ({agent_name})")
                    has_init_failure = True
            if not has_init_failure:
                failure_types["Method failure"] += 1
                error_messages["Method failure"].append(test["agent_file"])
        elif status == "SKIP":
            failure_types["No agent classes found"] += 1
            error_messages["No agent classes found"].append(test["agent_file"])
    
    # Start building report
    report = []
    report.append("# Agent Functionality Testing Report")
    report.append("")
    report.append("## Test Execution")
    report.append(f"- **Date:** {datetime.fromisoformat(results['test_timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"- **Agents Tested:** {results['agents_tested']}")
    report.append("")
    
    report.append("## Results")
    report.append("")
    report.append("### Overall Statistics")
    report.append(f"- **Fully Working:** {analysis['statistics']['fully_working']} agents ({analysis['statistics']['working_percentage']})")
    report.append(f"- **Partially Working:** {analysis['statistics']['partially_working']} agents")
    report.append(f"- **Broken:** {analysis['statistics']['broken']} agents ({analysis['statistics']['broken_percentage']})")
    report.append(f"- **Pass Rate:** {results.get('pass_rate', '0%')}")
    report.append("")
    
    # Working agents section
    report.append(f"### Working Agents ({len(analysis['working_agents'])} total)")
    if analysis['working_agents']:
        for i, agent in enumerate(analysis['working_agents'], 1):
            report.append(f"{i}. `{agent}`")
    else:
        report.append("*No fully working agents found*")
    report.append("")
    
    # Broken agents section
    report.append(f"### Broken Agents ({len(analysis['broken_agents'])} total)")
    report.append("")
    report.append("| Agent | Issue | Type |")
    report.append("|-------|-------|------|")
    for broken in analysis['broken_agents'][:50]:  # Limit to first 50
        agent_file = broken.get('file', 'Unknown')
        error = broken.get('error', broken.get('reason', 'Unknown'))
        error_type = "Import Error" if "import" in error.lower() or "module" in error.lower() else "Other"
        # Truncate long errors
        error_display = error[:80] + "..." if len(error) > 80 else error
        report.append(f"| `{agent_file}` | {error_display} | {error_type} |")
    
    if len(analysis['broken_agents']) > 50:
        report.append(f"| ... | ... | ... |")
        report.append(f"*({len(analysis['broken_agents']) - 50} more broken agents not shown)*")
    report.append("")
    
    # Partially working agents section
    report.append(f"### Partially Working Agents ({len(analysis['partially_working'])} total)")
    if analysis['partially_working']:
        report.append("")
        report.append("| Agent | Status |")
        report.append("|-------|--------|")
        for agent in analysis['partially_working']:
            report.append(f"| `{agent}` | Initialization passed, some methods failed |")
    else:
        report.append("*No partially working agents found*")
    report.append("")
    
    # Failure Analysis
    report.append("## Failure Analysis")
    report.append("")
    report.append("### By Failure Type")
    for failure_type, count in sorted(failure_types.items(), key=lambda x: x[1], reverse=True):
        report.append(f"- **{failure_type}:** {count} agents")
    report.append("")
    
    # Most common issues
    report.append("### Most Common Issues")
    sorted_issues = sorted(failure_types.items(), key=lambda x: x[1], reverse=True)
    for i, (issue, count) in enumerate(sorted_issues[:5], 1):
        report.append(f"{i}. **{issue}** - affects {count} agents")
        # Show first few affected agents
        if error_messages[issue]:
            report.append(f"   - Examples: {', '.join([f'`{a}`' for a in error_messages[issue][:3]])}")
    report.append("")
    
    # Recommendations
    report.append("## Recommendations")
    report.append("")
    
    if any("Missing module" in k for k in failure_types.keys()):
        report.append("### 1. Install Missing Dependencies")
        report.append("")
        report.append("Many agents fail due to missing Python modules. Install them:")
        report.append("```bash")
        missing_modules = set()
        for issue in failure_types.keys():
            if "Missing module" in issue:
                module = issue.replace("Missing module: ", "")
                missing_modules.add(module)
        for module in sorted(missing_modules):
            report.append(f"pip install {module}")
        report.append("```")
        report.append("")
    
    if failure_types.get("Import error", 0) > 0:
        report.append("### 2. Fix Import Errors")
        report.append("")
        report.append(f"{failure_types.get('Import error', 0)} agents have import-related issues that need investigation.")
        report.append("")
    
    if failure_types.get("Initialization failure", 0) > 0:
        report.append("### 3. Fix Initialization Failures")
        report.append("")
        report.append(f"{failure_types.get('Initialization failure', 0)} agents fail during initialization. These likely require:")
        report.append("- Configuration files or environment variables")
        report.append("- Database connections")
        report.append("- External service dependencies")
        report.append("")
    
    report.append(f"**MEASURED PASS RATE: {results.get('pass_rate', '0%')}**")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Write report
    with open('AGENT_TESTING_REPORT.md', 'w') as f:
        f.write('\n'.join(report))
    
    logger.info("Report generated: AGENT_TESTING_REPORT.md")


if __name__ == "__main__":
    generate_report()
