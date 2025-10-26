#!/usr/bin/env python3
"""
Agent Dependency Analysis Tool

This tool analyzes Python agent files to identify their dependencies and
categorize them by complexity level. This helps prioritize which agents
to fix first in the agent system repair process.

Usage:
    python3 analyze_agent_dependencies.py

Output:
    agent_dependency_analysis.json - Detailed dependency report
"""

import os
import ast
import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set, Tuple


class AgentDependencyAnalyzer:
    """Analyzes agent dependencies to categorize by complexity level."""
    
    def __init__(self, repo_root: Path = None):
        """Initialize the analyzer.
        
        Args:
            repo_root: Root directory of the repository. Defaults to script location.
        """
        self.repo_root = repo_root or Path(__file__).parent
        self.internal_keywords = [
            'agent', 'base_agent', 'shared', 'core', 
            'middleware', 'engine', 'config', 'models',
            'utils', 'communication', 'orchestrator'
        ]
        
    def analyze_imports(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """Extract all imports from a Python file.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Tuple of (internal_imports, external_imports)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            imports = []
            
            # Extract import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                    # Also capture relative imports
                    elif node.level > 0:
                        # Relative import like "from . import something"
                        imports.append(f".{'.' * (node.level - 1)}")
            
            # Categorize imports
            internal_imports = []
            external_imports = []
            
            for imp in imports:
                # Check if it's an internal dependency
                is_internal = any(
                    keyword in imp.lower() 
                    for keyword in self.internal_keywords
                )
                
                # Also check for relative imports
                if imp.startswith('.') or is_internal:
                    internal_imports.append(imp)
                else:
                    external_imports.append(imp)
            
            return internal_imports, external_imports
            
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return [], []
    
    def find_agent_files(self) -> List[Path]:
        """Find all agent Python files in the repository.
        
        Returns:
            List of paths to agent files
        """
        agent_files = []
        
        # Search in root directory for *_agent.py files
        for file_path in self.repo_root.glob("*_agent.py"):
            if file_path.is_file():
                agent_files.append(file_path)
        
        # Also search in subdirectories (agents/, core/, etc.)
        for pattern in ["agents/*_agent.py", "core/*_agent.py", "*/agents/*_agent.py"]:
            for file_path in self.repo_root.glob(pattern):
                if file_path.is_file() and file_path not in agent_files:
                    agent_files.append(file_path)
        
        return sorted(agent_files)
    
    def categorize_by_dependency_level(
        self, 
        dependency_map: Dict[str, Dict]
    ) -> Dict[str, List[str]]:
        """Categorize agents by their dependency complexity level.
        
        Args:
            dependency_map: Map of agent names to their dependency info
            
        Returns:
            Dictionary with agents grouped by level (0, 1, 2, 3+)
        """
        levels = {
            'level_0': [],  # No internal dependencies
            'level_1': [],  # 1-2 internal dependencies
            'level_2': [],  # 3-5 internal dependencies
            'level_3': []   # 6+ internal dependencies
        }
        
        for agent, info in dependency_map.items():
            count = info['internal_count']
            if count == 0:
                levels['level_0'].append(agent)
            elif count <= 2:
                levels['level_1'].append(agent)
            elif count <= 5:
                levels['level_2'].append(agent)
            else:
                levels['level_3'].append(agent)
        
        return levels
    
    def analyze(self) -> Dict:
        """Run the dependency analysis.
        
        Returns:
            Dictionary containing the analysis results
        """
        print("=" * 70)
        print("AGENT DEPENDENCY ANALYSIS")
        print("=" * 70)
        
        # Find all agent files
        agent_files = self.find_agent_files()
        print(f"\nFound {len(agent_files)} agent files")
        
        if not agent_files:
            print("Warning: No agent files found!")
            return {
                'summary': {
                    'total_agents': 0,
                    'level_0_independent': 0,
                    'level_1_minimal': 0,
                    'level_2_moderate': 0,
                    'level_3_complex': 0
                },
                'level_0_agents': [],
                'level_1_agents': [],
                'level_2_agents': [],
                'level_3_agents': [],
                'detailed_dependencies': {}
            }
        
        # Analyze each agent
        dependency_map = {}
        
        for agent_file in agent_files:
            agent_name = agent_file.name
            internal_deps, external_deps = self.analyze_imports(agent_file)
            
            dependency_map[agent_name] = {
                'internal_dependencies': internal_deps,
                'external_dependencies': external_deps,
                'internal_count': len(internal_deps),
                'external_count': len(external_deps),
                'dependency_level': len(internal_deps),
                'file_path': str(agent_file.relative_to(self.repo_root))
            }
        
        # Categorize by dependency level
        levels = self.categorize_by_dependency_level(dependency_map)
        
        # Build report
        report = {
            'summary': {
                'total_agents': len(dependency_map),
                'level_0_independent': len(levels['level_0']),
                'level_1_minimal': len(levels['level_1']),
                'level_2_moderate': len(levels['level_2']),
                'level_3_complex': len(levels['level_3'])
            },
            'level_0_agents': sorted(levels['level_0']),
            'level_1_agents': sorted(levels['level_1']),
            'level_2_agents': sorted(levels['level_2']),
            'level_3_agents': sorted(levels['level_3']),
            'detailed_dependencies': dependency_map
        }
        
        # Print summary
        print(f"\nTotal Agents: {report['summary']['total_agents']}")
        print(f"Level 0 (Independent): {report['summary']['level_0_independent']}")
        print(f"Level 1 (Minimal deps): {report['summary']['level_1_minimal']}")
        print(f"Level 2 (Moderate deps): {report['summary']['level_2_moderate']}")
        print(f"Level 3 (Complex deps): {report['summary']['level_3_complex']}")
        print("=" * 70)
        
        if levels['level_0']:
            print("\nLevel 0 Agents (Fix These First):")
            for agent in sorted(levels['level_0']):
                print(f"  - {agent}")
        
        if levels['level_1']:
            print("\nLevel 1 Agents (Minimal Dependencies):")
            for agent in sorted(levels['level_1']):
                deps = dependency_map[agent]['internal_dependencies']
                print(f"  - {agent} (deps: {len(deps)})")
        
        return report
    
    def save_report(self, report: Dict, output_path: Path = None):
        """Save the analysis report to a JSON file.
        
        Args:
            report: The analysis report dictionary
            output_path: Path where to save the report. Defaults to 
                        'agent_dependency_analysis.json' in repo root.
        """
        if output_path is None:
            output_path = self.repo_root / 'agent_dependency_analysis.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, sort_keys=False)
        
        print(f"\nDetailed report saved to: {output_path}")


def main():
    """Main entry point for the script."""
    analyzer = AgentDependencyAnalyzer()
    report = analyzer.analyze()
    analyzer.save_report(report)
    
    # Print next steps
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Review the generated 'agent_dependency_analysis.json' file")
    print("2. Start fixing Level 0 agents (no internal dependencies)")
    print("3. Once Level 0 agents pass, move to Level 1 agents")
    print("4. Continue progressing through levels")
    print("\nRecommended workflow:")
    print("  - Fix ModuleNotFoundError issues first")
    print("  - Update import statements to use correct paths")
    print("  - Add missing __init__.py files if needed")
    print("  - Test each agent individually after fixing")
    print()

if __name__ == "__main__":
    main()
