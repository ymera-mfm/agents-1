"""
Agent Dependency Analyzer
Categorizes agents by dependency level.
"""

import os
import ast
import json
from pathlib import Path
from collections import defaultdict


MAX_FILE_SIZE = 1024 * 1024  # 1 MB

def analyze_imports(file_path):
    """Extract all imports from a Python file."""
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    except Exception as e:
        return []


def categorize_agents():
    """Categorize agents by dependency level."""
    # Look for agent files in root directory
    root_dir = Path(".")
    agent_files = list(root_dir.glob("*_agent.py"))
    
    dependency_map = {}
    
    for agent_file in agent_files:
        imports = analyze_imports(agent_file)
        
        # Filter for internal dependencies only
        internal_deps = [
            imp for imp in imports 
            if any(keyword in imp for keyword in [
                'agent', 'base_agent', 'shared', 'core', 
                'middleware', 'engine'
            ])
        ]
        
        # Count external vs internal
        external_deps = [
            imp for imp in imports
            if imp not in internal_deps and not imp.startswith('.')
        ]
        
        dependency_map[agent_file.name] = {
            'internal_dependencies': internal_deps,
            'external_dependencies': external_deps,
            'internal_count': len(internal_deps),
            'external_count': len(external_deps),
            'dependency_level': len(internal_deps)
        }
    
    # Categorize by dependency level
    level_0 = []  # No internal dependencies
    level_1 = []  # 1-2 internal dependencies
    level_2 = []  # 3-5 internal dependencies
    level_3 = []  # 6+ internal dependencies
    
    for agent, info in dependency_map.items():
        count = info['dependency_level']
        if count == 0:
            level_0.append(agent)
        elif count <= 2:
            level_1.append(agent)
        elif count <= 5:
            level_2.append(agent)
        else:
            level_3.append(agent)
    
    # Generate report
    report = {
        'summary': {
            'total_agents': len(dependency_map),
            'level_0_independent': len(level_0),
            'level_1_minimal': len(level_1),
            'level_2_moderate': len(level_2),
            'level_3_complex': len(level_3)
        },
        'level_0_agents': level_0,
        'level_1_agents': level_1,
        'level_2_agents': level_2,
        'level_3_agents': level_3,
        'detailed_dependencies': dependency_map
    }
    
    # Save report
    with open('agent_dependency_analysis_new.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("=" * 70)
    print("AGENT DEPENDENCY ANALYSIS")
    print("=" * 70)
    print(f"Total Agents: {report['summary']['total_agents']}")
    print(f"Level 0 (Independent): {report['summary']['level_0_independent']}")
    print(f"Level 1 (Minimal deps): {report['summary']['level_1_minimal']}")
    print(f"Level 2 (Moderate deps): {report['summary']['level_2_moderate']}")
    print(f"Level 3 (Complex deps): {report['summary']['level_3_complex']}")
    print("=" * 70)
    
    if level_0:
        print("\nLevel 0 Agents (Fix These First):")
        for agent in sorted(level_0):
            print(f"  - {agent}")
    
    if level_1:
        print(f"\nLevel 1 Agents ({len(level_1)} agents):")
        for agent in sorted(level_1)[:10]:
            print(f"  - {agent}")
        if len(level_1) > 10:
            print(f"  ... and {len(level_1) - 10} more")
    
    print(f"\nDetailed report saved to: agent_dependency_analysis_new.json")
    
    return report


if __name__ == "__main__":
    categorize_agents()
