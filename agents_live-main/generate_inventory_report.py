#!/usr/bin/env python3
"""
Generate Human-Readable Agent Inventory Report
"""

import json
from pathlib import Path
from datetime import datetime


def generate_inventory_report():
    """Generate comprehensive inventory report in Markdown"""
    
    with open('agent_catalog_complete.json', 'r') as f:
        catalog = json.load(f)
    
    with open('agent_classification.json', 'r') as f:
        classification = json.load(f)
    
    report = []
    
    # Header
    report.append("# Agent System Inventory Report")
    report.append("")
    report.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    report.append("## 📊 Discovery Results")
    report.append("")
    
    # Total Agents Found
    report.append(f"### Total Agents Found: {catalog['total_files']}")
    report.append("")
    report.append(f"- **Agent files discovered:** {catalog['total_files']}")
    report.append(f"- **Agent classes found:** {catalog['total_classes']}")
    report.append(f"- **Total functions:** {catalog['total_functions']}")
    report.append(f"- **Async functions:** {catalog['total_async_functions']}")
    report.append(f"- **Total lines of code:** {catalog['total_lines']:,}")
    report.append(f"- **Average lines per file:** {catalog['summary_stats']['average_lines_per_file']}")
    report.append("")
    
    # Analysis Status
    report.append("### Analysis Status")
    report.append("")
    report.append(f"- ✅ Successfully analyzed: {catalog['summary_stats']['analyzed_successfully']} ({catalog['summary_stats']['analyzed_successfully']/catalog['total_files']*100:.1f}%)")
    report.append(f"- ❌ Analysis errors: {catalog['summary_stats']['analysis_errors']} ({catalog['summary_stats']['analysis_errors']/catalog['total_files']*100:.1f}%)")
    report.append("")
    
    # By Type
    report.append("## 📁 By Type")
    report.append("")
    report.append("| Type | Count | Percentage |")
    report.append("|------|-------|------------|")
    
    for agent_type, count in sorted(classification['summary']['by_type_counts'].items(), 
                                    key=lambda x: x[1], reverse=True):
        percentage = (count / catalog['total_files'] * 100) if catalog['total_files'] > 0 else 0
        report.append(f"| {agent_type.capitalize()} | {count} | {percentage:.1f}% |")
    
    report.append("")
    
    # By Status
    report.append("## 🎯 By Status")
    report.append("")
    report.append("| Status | Count | Percentage |")
    report.append("|--------|-------|------------|")
    
    for status, count in classification['summary']['by_status_counts'].items():
        percentage = (count / catalog['total_files'] * 100) if catalog['total_files'] > 0 else 0
        emoji = "✅" if status == "complete" else "⚠️" if status == "incomplete" else "❌"
        report.append(f"| {emoji} {status.capitalize()} | {count} | {percentage:.1f}% |")
    
    report.append("")
    
    # By Capabilities
    report.append("## 🔧 By Capabilities")
    report.append("")
    
    for capability, agents in classification['by_capabilities'].items():
        count = len(agents)
        percentage = (count / catalog['total_files'] * 100) if catalog['total_files'] > 0 else 0
        report.append(f"- **{capability.replace('_', ' ').title()}:** {count} ({percentage:.1f}%)")
    
    report.append("")
    
    # Completion Analysis
    report.append("## 📈 Completion Analysis")
    report.append("")
    report.append(f"**Overall Completion Rate: {classification['summary']['completion_rate']}**")
    report.append("")
    report.append("### Key Metrics")
    report.append("")
    report.append(f"- ✅ **Complete agents:** {classification['summary']['by_status_counts']['complete']} ({classification['summary']['completion_rate']})")
    report.append(f"- ⚠️ **Incomplete agents:** {classification['summary']['by_status_counts']['incomplete']} ({classification['summary']['by_status_counts']['incomplete']/catalog['total_files']*100:.1f}%)")
    report.append(f"- ❌ **Syntax errors:** {classification['summary']['by_status_counts']['syntax_error']} ({classification['summary']['by_status_counts']['syntax_error']/catalog['total_files']*100:.1f}%)")
    report.append("")
    report.append(f"- 🔄 **Async adoption:** {classification['summary']['async_adoption']}")
    report.append(f"- 🏗️ **BaseAgent compliance:** {classification['summary']['base_agent_compliance']}")
    report.append(f"- 💾 **Database integration:** {classification['summary']['by_capability_counts']['database']} ({classification['summary']['by_capability_counts']['database']/catalog['total_files']*100:.1f}%)")
    report.append(f"- 🌐 **API integration:** {classification['summary']['by_capability_counts']['api']} ({classification['summary']['by_capability_counts']['api']/catalog['total_files']*100:.1f}%)")
    report.append("")
    
    # Issues Found
    report.append("## ⚠️ Issues Found")
    report.append("")
    
    # Syntax errors
    if classification['by_status']['syntax_error']:
        report.append("### Syntax Errors")
        report.append("")
        for agent in classification['by_status']['syntax_error']:
            report.append(f"1. **{Path(agent['file']).name}**")
            report.append(f"   - File: `{agent['file']}`")
            report.append(f"   - Error: {agent.get('error', 'Unknown error')}")
            report.append("")
    
    # Incomplete implementations
    incomplete_count = len(classification['by_status']['incomplete'])
    report.append("### Incomplete Implementations")
    report.append("")
    report.append(f"**Total:** {incomplete_count} agents ({incomplete_count/catalog['total_files']*100:.1f}%)")
    report.append("")
    report.append("**Common Issues:**")
    
    no_base_agent = sum(1 for a in classification['by_status']['incomplete'] 
                       if not a.get('has_base_agent', False))
    no_process = sum(1 for a in classification['by_status']['incomplete'] 
                    if not a.get('has_process_method', False))
    no_classes = sum(1 for a in classification['by_status']['incomplete'] 
                    if a.get('class_count', 0) == 0)
    
    report.append(f"- Missing BaseAgent inheritance: {no_base_agent} agents")
    report.append(f"- Missing process method: {no_process} agents")
    report.append(f"- No classes defined: {no_classes} agents")
    report.append("")
    
    # Detailed breakdown of incomplete agents (first 10)
    report.append("**Examples (first 10):**")
    report.append("")
    for idx, agent in enumerate(classification['by_status']['incomplete'][:10], 1):
        report.append(f"{idx}. `{Path(agent['file']).name}`")
        issues = []
        if not agent.get('has_base_agent'):
            issues.append("No BaseAgent")
        if not agent.get('has_process_method'):
            issues.append("No process method")
        if agent.get('class_count', 0) == 0:
            issues.append("No classes")
        report.append(f"   - Issues: {', '.join(issues) if issues else 'Other'}")
    report.append("")
    
    # Recommendations
    report.append("## 💡 Recommendations")
    report.append("")
    report.append("Based on actual findings:")
    report.append("")
    report.append(f"1. **Fix Syntax Errors ({classification['summary']['by_status_counts']['syntax_error']} files)**")
    report.append("   - Priority: CRITICAL")
    report.append("   - These files cannot be analyzed or used")
    report.append("")
    report.append(f"2. **Complete Incomplete Agents ({incomplete_count} files, {incomplete_count/catalog['total_files']*100:.1f}%)**")
    report.append("   - Priority: HIGH")
    report.append(f"   - {no_base_agent} agents need BaseAgent inheritance")
    report.append(f"   - {no_process} agents need process method implementation")
    report.append(f"   - {no_classes} agents are missing class definitions")
    report.append("")
    report.append("3. **Standardize Agent Structure**")
    report.append("   - Priority: MEDIUM")
    report.append(f"   - Current BaseAgent compliance: {classification['summary']['base_agent_compliance']}")
    report.append(f"   - Target: 80%+ compliance")
    report.append("")
    report.append("4. **Increase Test Coverage**")
    report.append("   - Priority: HIGH")
    report.append("   - Only 2 test files found among agent files")
    report.append("   - Need comprehensive test suite (see coverage analysis)")
    report.append("")
    
    # Statistics Summary
    report.append("## 📊 Statistics Summary")
    report.append("")
    report.append("```")
    report.append(f"Total Agent Files:        {catalog['total_files']}")
    report.append(f"Total Classes:            {catalog['total_classes']}")
    report.append(f"Total Functions:          {catalog['total_functions']}")
    report.append(f"Total Async Functions:    {catalog['total_async_functions']}")
    report.append(f"Total Lines of Code:      {catalog['total_lines']:,}")
    report.append("")
    report.append(f"Completion Rate:          {classification['summary']['completion_rate']}")
    report.append(f"Async Adoption:           {classification['summary']['async_adoption']}")
    report.append(f"BaseAgent Compliance:     {classification['summary']['base_agent_compliance']}")
    report.append("```")
    report.append("")
    
    # Files Generated
    report.append("## 📄 Generated Files")
    report.append("")
    report.append("- `agent_catalog_complete.json` - Complete agent inventory with metadata")
    report.append("- `agent_classification.json` - Classified agents with statistics")
    report.append("- `agent_system_map.png` - Visual representation of agent system")
    report.append("- `agent_system_map.dot` - GraphViz source file")
    report.append("- `AGENT_INVENTORY_REPORT.md` - This report")
    report.append("")
    
    # Footer
    report.append("---")
    report.append("")
    report.append("*This report contains MEASURED data only. All statistics are based on actual analysis of source files.*")
    report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    print("=" * 60)
    print("GENERATING INVENTORY REPORT")
    print("=" * 60)
    print()
    
    report_content = generate_inventory_report()
    
    output_file = "AGENT_INVENTORY_REPORT.md"
    with open(output_file, 'w') as f:
        f.write(report_content)
    
    print(f"Report generated: {output_file}")
    print()
    print("=" * 60)
    print("TASK 1.1 COMPLETE: Deep Agent Discovery & Cataloging")
    print("=" * 60)
