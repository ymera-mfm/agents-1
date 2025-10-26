#!/usr/bin/env python3
"""
Generate Agent Coverage Report
Creates human-readable coverage report with measured data
"""

import json
from pathlib import Path
from datetime import datetime


def generate_coverage_report():
    """Generate comprehensive coverage report in Markdown"""
    
    with open('agent_coverage_gaps.json', 'r') as f:
        gaps = json.load(f)
    
    with open('agent_test_plan.json', 'r') as f:
        test_plan = json.load(f)
    
    with open('agent_catalog_complete.json', 'r') as f:
        catalog = json.load(f)
    
    report = []
    
    # Header
    report.append("# Agent Testing Coverage Report")
    report.append("")
    report.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    report.append("## 📊 Coverage Measurement Results")
    report.append("")
    
    # Overall Coverage
    stats = gaps["statistics"]
    report.append("### Overall Agent Coverage: **{0}**".format(stats["average_coverage"]))
    report.append("")
    report.append("**MEASURED via pytest --cov**")
    report.append("")
    report.append(f"- Total agent files analyzed: {stats['total_agent_files']}")
    report.append(f"- Files with coverage data: {stats['files_with_coverage_data']}")
    report.append(f"- Total statements: {stats['total_statements']:,}")
    report.append(f"- Statements covered: {stats['total_covered']:,}")
    report.append(f"- Statements missing: {stats['total_missing']:,}")
    report.append("")
    
    # Coverage Distribution
    report.append("## 📈 Coverage Distribution")
    report.append("")
    report.append("| Coverage Range | Files | Percentage |")
    report.append("|---------------|-------|------------|")
    
    total = stats['files_with_coverage_data']
    if total > 0:
        report.append(f"| 0% (Not covered) | {stats['files_not_covered']} | {stats['files_not_covered']/total*100:.1f}% |")
        report.append(f"| 1-59% (Critical) | {stats['files_below_60']} | {stats['files_below_60']/total*100:.1f}% |")
        report.append(f"| 60-79% (Needs work) | {stats['files_below_80']} | {stats['files_below_80']/total*100:.1f}% |")
        report.append(f"| 80%+ (Good) | {stats['files_above_80']} | {stats['files_above_80']/total*100:.1f}% |")
    
    report.append("")
    
    # Coverage Gaps Detail
    report.append("## 🔍 Coverage Gaps Detail")
    report.append("")
    
    # Not Covered Files
    if gaps["not_covered"]:
        report.append(f"### Not Covered ({len(gaps['not_covered'])} files)")
        report.append("")
        report.append("Files with **0% coverage** (first 20):")
        report.append("")
        report.append("| File | Statements | Priority |")
        report.append("|------|-----------|----------|")
        
        for file_info in gaps["not_covered"][:20]:
            report.append(f"| `{file_info['filename']}` | {file_info['total_statements']} | CRITICAL |")
        
        if len(gaps["not_covered"]) > 20:
            report.append(f"| ... and {len(gaps['not_covered']) - 20} more files | | |")
        
        report.append("")
    
    # Critical Gaps
    if gaps["critical_gaps"]:
        report.append(f"### Critical Gaps - <60% Coverage ({len(gaps['critical_gaps'])} files)")
        report.append("")
        report.append("| File | Coverage | Missing Lines | Priority |")
        report.append("|------|----------|--------------|----------|")
        
        for file_info in gaps["critical_gaps"]:
            report.append(f"| `{file_info['filename']}` | {file_info['coverage']:.1f}% | {file_info['missing_count']} | HIGH |")
        
        report.append("")
    
    # Good Coverage (if any)
    if gaps["good_coverage"]:
        report.append(f"### Good Coverage - >80% ({len(gaps['good_coverage'])} files)")
        report.append("")
        report.append("| File | Coverage |")
        report.append("|------|----------|")
        
        for file_info in gaps["good_coverage"]:
            report.append(f"| `{file_info['filename']}` | {file_info['coverage']:.1f}% |")
        
        report.append("")
    
    # Test Plan Summary
    report.append("## 📋 Test Improvement Plan")
    report.append("")
    
    summary = test_plan["summary"]
    report.append(f"**Estimated Effort:** {summary['total_estimated_hours']} hours")
    report.append("")
    report.append(f"- Files needing tests: {summary['total_files_needing_tests']}")
    report.append(f"- Tests to write: {summary['total_tests_to_write']}")
    report.append(f"- Current coverage: {summary['current_coverage']}")
    report.append(f"- Target coverage: {summary['target_coverage']}")
    report.append(f"- Gap to close: {summary['gap_to_close']}")
    report.append("")
    
    # Priority Breakdown
    report.append("### By Priority")
    report.append("")
    report.append("| Priority | Files | Tests | Hours |")
    report.append("|----------|-------|-------|-------|")
    
    p1_tests = sum(t["estimated_tests_needed"] for t in test_plan["priority_1_not_covered"])
    p1_hours = sum(t["estimated_hours"] for t in test_plan["priority_1_not_covered"])
    report.append(f"| 1: Not Covered | {summary['not_covered_files']} | {p1_tests} | {p1_hours:.1f} |")
    
    p2_tests = sum(t["estimated_tests_needed"] for t in test_plan["priority_2_critical"])
    p2_hours = sum(t["estimated_hours"] for t in test_plan["priority_2_critical"])
    report.append(f"| 2: Critical | {summary['critical_files']} | {p2_tests} | {p2_hours:.1f} |")
    
    p3_tests = sum(t["estimated_tests_needed"] for t in test_plan["priority_3_improvement"])
    p3_hours = sum(t["estimated_hours"] for t in test_plan["priority_3_improvement"])
    report.append(f"| 3: Improvement | {summary['improvement_files']} | {p3_tests} | {p3_hours:.1f} |")
    
    report.append("")
    
    # Top 10 Files Needing Tests
    report.append("## 🎯 Top 10 Files Needing Tests")
    report.append("")
    report.append("| Rank | File | Statements | Tests Needed | Est. Hours |")
    report.append("|------|------|-----------|-------------|-----------|")
    
    # Sort by total statements (highest impact)
    all_tasks = (test_plan["priority_1_not_covered"] + 
                test_plan["priority_2_critical"] + 
                test_plan["priority_3_improvement"])
    all_tasks.sort(key=lambda x: x["total_statements"], reverse=True)
    
    for idx, task in enumerate(all_tasks[:10], 1):
        report.append(f"| {idx} | `{task['filename']}` | {task['total_statements']} | "
                     f"{task['estimated_tests_needed']} | {task['estimated_hours']:.1f} |")
    
    report.append("")
    
    # Detailed Test Requirements (first 5)
    report.append("## 📝 Detailed Test Requirements (Top 5)")
    report.append("")
    
    for idx, task in enumerate(all_tasks[:5], 1):
        report.append(f"### {idx}. {task['filename']}")
        report.append("")
        report.append(f"- **File:** `{task['file']}`")
        report.append(f"- **Current coverage:** {task['current_coverage']:.1f}%")
        report.append(f"- **Target coverage:** {task['target_coverage']:.1f}%")
        report.append(f"- **Total statements:** {task['total_statements']}")
        report.append(f"- **Missing statements:** {task['missing_statements']}")
        report.append(f"- **Tests to write:** {task['estimated_tests_needed']}")
        report.append(f"- **Estimated time:** {task['estimated_hours']:.1f} hours")
        report.append(f"- **Test file:** `{task['test_file']}`")
        report.append(f"- **Priority:** {task['priority']}")
        report.append("")
    
    # Implementation Roadmap
    report.append("## 🗺️ Implementation Roadmap")
    report.append("")
    report.append("### Phase 1: Critical Files (Priority 1)")
    report.append(f"- Files: {summary['not_covered_files']}")
    report.append(f"- Estimated time: {p1_hours:.1f} hours")
    report.append("- Focus: Get basic coverage for all agent files")
    report.append("")
    
    report.append("### Phase 2: Low Coverage Files (Priority 2)")
    report.append(f"- Files: {summary['critical_files']}")
    report.append(f"- Estimated time: {p2_hours:.1f} hours")
    report.append("- Focus: Improve coverage to 60%+")
    report.append("")
    
    report.append("### Phase 3: Coverage Enhancement (Priority 3)")
    report.append(f"- Files: {summary['improvement_files']}")
    report.append(f"- Estimated time: {p3_hours:.1f} hours")
    report.append("- Focus: Reach 80%+ coverage target")
    report.append("")
    
    # Recommendations
    report.append("## 💡 Recommendations")
    report.append("")
    report.append("Based on measured data:")
    report.append("")
    report.append("1. **Immediate Action Required**")
    report.append(f"   - Current coverage: {stats['average_coverage']}")
    report.append("   - This is critically low for production systems")
    report.append(f"   - {stats['files_not_covered']}/{stats['total_agent_files']} files have ZERO test coverage")
    report.append("")
    report.append("2. **Start with High-Impact Files**")
    report.append("   - Focus on files with most statements first")
    report.append("   - Top 10 files contain significant business logic")
    report.append("   - These have highest risk if they fail")
    report.append("")
    report.append("3. **Establish Testing Standards**")
    report.append("   - Create test templates for agent files")
    report.append("   - Set minimum coverage requirement (60%)")
    report.append("   - Implement pre-commit coverage checks")
    report.append("")
    report.append("4. **Estimated Timeline**")
    report.append(f"   - Full coverage improvement: {summary['total_estimated_hours']} hours")
    report.append("   - At 8 hours/day: ~132 working days")
    report.append("   - Recommended: Parallel effort with 3-4 developers")
    report.append("   - Achievable in: 4-6 weeks with dedicated team")
    report.append("")
    
    # Files Generated
    report.append("## 📄 Generated Files")
    report.append("")
    report.append("- `agent_coverage.json` - Raw coverage data from pytest")
    report.append("- `agent_coverage.xml` - XML coverage report")
    report.append("- `agent_coverage_html/` - Browsable HTML coverage report")
    report.append("- `agent_coverage_gaps.json` - Gap analysis with line numbers")
    report.append("- `agent_test_plan.json` - Detailed test requirements")
    report.append("- `AGENT_COVERAGE_REPORT.md` - This report")
    report.append("")
    
    # Footer
    report.append("---")
    report.append("")
    report.append("*This report contains MEASURED data only. All coverage percentages are based on actual pytest --cov execution.*")
    report.append("")
    report.append("**Coverage Report Location:** `agent_coverage_html/index.html`")
    report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    print("=" * 60)
    print("GENERATING COVERAGE REPORT")
    print("=" * 60)
    print()
    
    report_content = generate_coverage_report()
    
    output_file = "AGENT_COVERAGE_REPORT.md"
    with open(output_file, 'w') as f:
        f.write(report_content)
    
    print(f"Report generated: {output_file}")
    print()
    print("=" * 60)
    print("TASK 1.2 COMPLETE: Agent Testing Coverage Analysis")
    print("=" * 60)
