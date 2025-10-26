#!/usr/bin/env python3
"""
Agent Coverage Gap Analyzer
Analyzes coverage data specifically for agent files and identifies gaps
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def analyze_coverage_gaps() -> Dict[str, Any]:
    """Find untested code in agents"""
    
    with open('agent_coverage.json', 'r') as f:
        coverage = json.load(f)
    
    # Get the list of agent files from our catalog
    with open('agent_catalog_complete.json', 'r') as f:
        catalog = json.load(f)
    
    agent_files = [Path(agent['file']).name for agent in catalog['agents_detail']]
    
    gaps = {
        "critical_gaps": [],  # <60% coverage
        "needs_improvement": [],  # 60-80%
        "good_coverage": [],  # >80%
        "not_covered": [],  # 0% coverage
        "statistics": {}
    }
    
    # Track total coverage
    total_covered = 0
    total_statements = 0
    files_analyzed = 0
    
    for filepath, data in coverage['files'].items():
        filename = Path(filepath).name
        
        # Check if this is an agent file
        if filename not in agent_files:
            continue
        
        files_analyzed += 1
        
        # Get coverage data
        summary = data['summary']
        covered_lines = summary['covered_lines']
        missing_lines = summary['missing_lines']
        total_lines = summary['num_statements']
        
        if total_lines == 0:
            continue
        
        coverage_pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        total_covered += covered_lines
        total_statements += total_lines
        
        # Get missing line numbers
        missing_line_nums = data.get('missing_lines', [])
        
        file_info = {
            "file": filepath,
            "filename": filename,
            "coverage": coverage_pct,
            "covered_lines": covered_lines,
            "missing_lines": missing_lines,
            "total_statements": total_lines,
            "missing_line_numbers": missing_line_nums,
            "missing_count": len(missing_line_nums)
        }
        
        if coverage_pct == 0:
            gaps["not_covered"].append(file_info)
        elif coverage_pct < 60:
            gaps["critical_gaps"].append(file_info)
        elif coverage_pct < 80:
            gaps["needs_improvement"].append(file_info)
        else:
            gaps["good_coverage"].append(file_info)
    
    # Sort each category by coverage percentage
    for category in ['critical_gaps', 'needs_improvement', 'good_coverage', 'not_covered']:
        gaps[category].sort(key=lambda x: x['coverage'])
    
    # Calculate statistics
    all_files = (gaps["critical_gaps"] + gaps["needs_improvement"] + 
                 gaps["good_coverage"] + gaps["not_covered"])
    
    if all_files:
        avg_coverage = (total_covered / total_statements * 100) if total_statements > 0 else 0
        gaps["statistics"] = {
            "total_agent_files": files_analyzed,
            "files_with_coverage_data": len(all_files),
            "average_coverage": f"{avg_coverage:.2f}%",
            "files_not_covered": len(gaps["not_covered"]),
            "files_below_60": len(gaps["critical_gaps"]),
            "files_below_80": len(gaps["needs_improvement"]),
            "files_above_80": len(gaps["good_coverage"]),
            "total_statements": total_statements,
            "total_covered": total_covered,
            "total_missing": total_statements - total_covered
        }
    else:
        gaps["statistics"] = {
            "total_agent_files": files_analyzed,
            "files_with_coverage_data": 0,
            "average_coverage": "0.00%",
            "files_not_covered": 0,
            "files_below_60": 0,
            "files_below_80": 0,
            "files_above_80": 0,
            "total_statements": 0,
            "total_covered": 0,
            "total_missing": 0
        }
    
    return gaps


if __name__ == "__main__":
    print("=" * 60)
    print("AGENT COVERAGE GAP ANALYZER")
    print("=" * 60)
    print()
    
    gaps = analyze_coverage_gaps()
    
    # Save gaps
    output_file = "agent_coverage_gaps.json"
    with open(output_file, 'w') as f:
        json.dump(gaps, f, indent=2)
    
    print("Coverage Gap Analysis:")
    print("-" * 60)
    stats = gaps["statistics"]
    print(f"Total agent files: {stats['total_agent_files']}")
    print(f"Files with coverage data: {stats['files_with_coverage_data']}")
    print()
    print(f"Average Coverage: {stats['average_coverage']}")
    print(f"Total Statements: {stats['total_statements']:,}")
    print(f"Total Covered: {stats['total_covered']:,}")
    print(f"Total Missing: {stats['total_missing']:,}")
    print()
    print("Coverage Distribution:")
    print(f"  Not covered (0%):     {stats['files_not_covered']:3d}")
    print(f"  Critical (<60%):      {stats['files_below_60']:3d}")
    print(f"  Needs work (60-80%):  {stats['files_below_80']:3d}")
    print(f"  Good (>80%):          {stats['files_above_80']:3d}")
    print()
    
    # Show examples
    if gaps["not_covered"]:
        print("Not Covered (first 5):")
        for file_info in gaps["not_covered"][:5]:
            print(f"  - {file_info['filename']}: 0% ({file_info['total_statements']} statements)")
    
    if gaps["critical_gaps"]:
        print()
        print("Critical Gaps (first 5):")
        for file_info in gaps["critical_gaps"][:5]:
            print(f"  - {file_info['filename']}: {file_info['coverage']:.1f}% "
                  f"({file_info['missing_count']} lines missing)")
    
    print()
    print(f"Gap analysis saved to: {output_file}")
    print("=" * 60)
