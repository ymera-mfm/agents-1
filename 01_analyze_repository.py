#!/usr/bin/env python3
"""
Complete Repository Analysis
Identifies all files, duplicates, versions, and issues
"""

import os
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set
import ast
from datetime import datetime

class RepositoryAnalyzer:
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'agents': {},
            'engines': {},
            'utilities': {},
            'configs': {},
            'duplicates': {},
            'versions': {},
            'recommendations': []
        }
    
    def analyze(self):
        """Run complete analysis."""
        print("=" * 80)
        print("YMERA REPOSITORY ANALYSIS")
        print("=" * 80)
        
        # Step 1: Catalog all files
        print("\n1. Cataloging all files...")
        self._catalog_files()
        
        # Step 2: Find duplicates
        print("\n2. Finding duplicate files...")
        self._find_duplicates()
        
        # Step 3: Analyze versions
        print("\n3. Analyzing file versions...")
        self._analyze_versions()
        
        # Step 4: Analyze agents
        print("\n4. Analyzing agents...")
        self._analyze_agents()
        
        # Step 5: Analyze engines
        print("\n5. Analyzing engines...")
        self._analyze_engines()
        
        # Step 6: Analyze utilities
        print("\n6. Analyzing utilities...")
        self._analyze_utilities()
        
        # Step 7: Analyze configurations
        print("\n7. Analyzing configurations...")
        self._analyze_configs()
        
        # Step 8: Generate recommendations
        print("\n8. Generating recommendations...")
        self._generate_recommendations()
        
        # Step 9: Save report
        print("\n9. Saving analysis report...")
        self._save_report()
        
        print("\n" + "=" * 80)
        print("✅ Analysis Complete!")
        print("=" * 80)
    
    def _catalog_files(self):
        """Catalog all Python files."""
        file_types = defaultdict(list)
        
        for py_file in self.root.rglob("*.py"):
            # Skip venv and hidden directories
            if any(part.startswith('.') or part == 'venv' for part in py_file.parts):
                continue
            
            relative_path = py_file.relative_to(self.root)
            file_info = {
                'path': str(relative_path),
                'name': py_file.name,
                'size': py_file.stat().st_size,
                'lines': self._count_lines(py_file),
                'hash': self._file_hash(py_file)
            }
            
            # Categorize by directory
            if 'agents' in py_file.parts:
                file_types['agents'].append(file_info)
            elif 'engines' in py_file.parts or 'engine' in py_file.name.lower():
                file_types['engines'].append(file_info)
            elif 'utils' in py_file.parts or 'utilities' in py_file.parts:
                file_types['utilities'].append(file_info)
            elif 'core' in py_file.parts:
                file_types['core'].append(file_info)
            elif 'shared' in py_file.parts:
                file_types['shared'].append(file_info)
            elif 'config' in py_file.name.lower():
                file_types['configs'].append(file_info)
            else:
                file_types['other'].append(file_info)
        
        self.results['file_catalog'] = dict(file_types)
        self.results['summary']['total_files'] = sum(len(files) for files in file_types.values())
        
        print(f"   Found {self.results['summary']['total_files']} Python files")
        for category, files in file_types.items():
            print(f"   - {category}: {len(files)} files")
    
    def _find_duplicates(self):
        """Find duplicate files by content hash."""
        hash_map = defaultdict(list)
        
        for category, files in self.results['file_catalog'].items():
            for file_info in files:
                hash_map[file_info['hash']].append({
                    'category': category,
                    **file_info
                })
        
        # Find duplicates (same hash, multiple files)
        duplicates = {
            h: files for h, files in hash_map.items() 
            if len(files) > 1
        }
        
        self.results['duplicates'] = duplicates
        self.results['summary']['duplicate_groups'] = len(duplicates)
        self.results['summary']['duplicate_files'] = sum(len(files) for files in duplicates.values())
        
        print(f"   Found {len(duplicates)} groups of duplicate files")
        print(f"   Total duplicate files: {self.results['summary']['duplicate_files']}")
        
        if duplicates:
            print("\n   Top duplicates:")
            for i, (hash_val, files) in enumerate(list(duplicates.items())[:5], 1):
                print(f"   {i}. {len(files)} copies:")
                for f in files[:3]:
                    print(f"      - {f['path']}")
    
    def _analyze_versions(self):
        """Analyze file versions (e.g., file.py, file_v2.py, file_old.py)."""
        version_groups = defaultdict(list)
        
        version_indicators = [
            '_v1', '_v2', '_v3', '_v4', '_v5',
            '_old', '_new', '_backup', '_bak',
            '_copy', '_2', '_final', '_temp',
            '_test', '_draft', '_wip', ' (1)', ' (2)',
            '_complete', '_prod', '_production'
        ]
        
        for category, files in self.results['file_catalog'].items():
            for file_info in files:
                name = file_info['name'].replace('.py', '')
                
                # Check for version indicators
                base_name = name
                version = None
                
                for indicator in version_indicators:
                    if indicator in name.lower():
                        base_name = name.lower().split(indicator)[0]
                        version = indicator
                        break
                
                version_groups[base_name].append({
                    'category': category,
                    'version': version or 'main',
                    **file_info
                })
        
        # Filter to only groups with multiple versions
        multi_version = {
            name: versions for name, versions in version_groups.items()
            if len(versions) > 1
        }
        
        self.results['versions'] = multi_version
        self.results['summary']['versioned_files'] = len(multi_version)
        
        print(f"   Found {len(multi_version)} files with multiple versions")
        
        if multi_version:
            print("\n   Top versioned files:")
            for i, (base_name, versions) in enumerate(list(multi_version.items())[:5], 1):
                print(f"   {i}. {base_name}: {len(versions)} versions")
                for v in versions[:3]:
                    print(f"      - {v['name']} ({v['version']})")
    
    def _analyze_agents(self):
        """Analyze all agent files."""
        if 'agents' not in self.results['file_catalog']:
            print("   No agents directory found")
            return
        
        agents = []
        for file_info in self.results['file_catalog']['agents']:
            file_path = self.root / file_info['path']
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                # Find agent class
                agent_class = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if 'Agent' in node.name:
                            agent_class = node.name
                            break
                
                # Find imports
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                agents.append({
                    **file_info,
                    'agent_class': agent_class,
                    'has_base_agent': any('base_agent' in imp.lower() or 'agent_base' in imp.lower() for imp in imports),
                    'import_count': len(imports),
                    'imports': imports[:10]  # First 10 imports
                })
            except Exception as e:
                agents.append({
                    **file_info,
                    'error': f'Failed to parse: {str(e)}'
                })
        
        self.results['agents'] = {
            'total': len(agents),
            'with_base_agent': sum(1 for a in agents if a.get('has_base_agent')),
            'parseable': sum(1 for a in agents if 'error' not in a),
            'files': agents
        }
        
        print(f"   Total agents: {len(agents)}")
        print(f"   Using base_agent: {self.results['agents']['with_base_agent']}")
        print(f"   Parseable: {self.results['agents']['parseable']}")
    
    def _analyze_engines(self):
        """Analyze all engine files."""
        if 'engines' not in self.results['file_catalog']:
            print("   No engines found in dedicated directory")
            # Check for engine files in other categories
            engine_files = []
            for category, files in self.results['file_catalog'].items():
                for file_info in files:
                    if 'engine' in file_info['name'].lower():
                        engine_files.append(file_info)
            
            if engine_files:
                print(f"   Found {len(engine_files)} engine files in other locations")
                self.results['engines'] = {
                    'total': len(engine_files),
                    'parseable': 0,
                    'files': engine_files
                }
            return
        
        engines = []
        for file_info in self.results['file_catalog']['engines']:
            file_path = self.root / file_info['path']
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                # Find engine class
                engine_class = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if 'Engine' in node.name:
                            engine_class = node.name
                            break
                
                engines.append({
                    **file_info,
                    'engine_class': engine_class
                })
            except Exception as e:
                engines.append({
                    **file_info,
                    'error': f'Failed to parse: {str(e)}'
                })
        
        self.results['engines'] = {
            'total': len(engines),
            'parseable': sum(1 for e in engines if 'error' not in e),
            'files': engines
        }
        
        print(f"   Total engines: {len(engines)}")
        print(f"   Parseable: {self.results['engines']['parseable']}")
    
    def _analyze_utilities(self):
        """Analyze utility files."""
        if 'utilities' not in self.results['file_catalog']:
            print("   No utilities directory found")
            return
        
        utilities = self.results['file_catalog']['utilities']
        self.results['utilities'] = {
            'total': len(utilities),
            'files': utilities
        }
        
        print(f"   Total utilities: {len(utilities)}")
    
    def _analyze_configs(self):
        """Analyze configuration files."""
        config_files = []
        
        # Find all config-related files
        for ext in ['*.py', '*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.env*', '*.txt']:
            for config_file in self.root.rglob(ext):
                if any(part.startswith('.') or part == 'venv' for part in config_file.parts):
                    continue
                
                name_lower = config_file.name.lower()
                if any(keyword in name_lower for keyword in ['config', 'setting', 'requirement', '.env']):
                    config_files.append({
                        'path': str(config_file.relative_to(self.root)),
                        'name': config_file.name,
                        'size': config_file.stat().st_size,
                        'type': config_file.suffix
                    })
        
        # Group by type
        by_type = defaultdict(list)
        for cf in config_files:
            key = cf['name'].lower().replace('.py', '').replace('.json', '').replace('.txt', '')
            if 'config' in key:
                by_type['config'].append(cf)
            elif 'requirement' in key:
                by_type['requirements'].append(cf)
            elif 'env' in key:
                by_type['environment'].append(cf)
            elif 'setting' in key:
                by_type['settings'].append(cf)
            else:
                by_type['other'].append(cf)
        
        self.results['configs'] = {
            'total': len(config_files),
            'by_type': dict(by_type),
            'files': config_files
        }
        
        print(f"   Total config files: {len(config_files)}")
        for config_type, files in by_type.items():
            print(f"   - {config_type}: {len(files)} files")
    
    def _generate_recommendations(self):
        """Generate actionable recommendations."""
        recs = []
        
        # Duplicates
        if self.results['summary'].get('duplicate_files', 0) > 0:
            recs.append({
                'priority': 'HIGH',
                'category': 'Duplicates',
                'issue': f"{self.results['summary']['duplicate_files']} duplicate files found",
                'action': 'Remove duplicate files, keep best version',
                'impact': 'Reduces confusion, improves maintainability'
            })
        
        # Versions
        if self.results['summary'].get('versioned_files', 0) > 0:
            recs.append({
                'priority': 'HIGH',
                'category': 'Versions',
                'issue': f"{self.results['summary']['versioned_files']} files have multiple versions",
                'action': 'Consolidate into single best version',
                'impact': 'Single source of truth'
            })
        
        # Configs
        config_count = len(self.results['configs'].get('by_type', {}).get('config', []))
        if config_count > 1:
            recs.append({
                'priority': 'HIGH',
                'category': 'Configuration',
                'issue': f"{config_count} different config files found",
                'action': 'Unify into single core/config.py',
                'impact': 'Simplified configuration management'
            })
        
        # Requirements
        req_count = len(self.results['configs'].get('by_type', {}).get('requirements', []))
        if req_count > 1:
            recs.append({
                'priority': 'HIGH',
                'category': 'Dependencies',
                'issue': f"{req_count} different requirements files found",
                'action': 'Consolidate into single requirements.txt',
                'impact': 'Consistent dependencies'
            })
        
        # Agents without base
        agents_without_base = (
            self.results['agents'].get('total', 0) - 
            self.results['agents'].get('with_base_agent', 0)
        )
        if agents_without_base > 0:
            recs.append({
                'priority': 'MEDIUM',
                'category': 'Agents',
                'issue': f"{agents_without_base} agents not using base_agent",
                'action': 'Refactor to inherit from BaseAgent',
                'impact': 'Standardized agent interface'
            })
        
        self.results['recommendations'] = sorted(recs, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['priority']])
    
    def _save_report(self):
        """Save analysis report."""
        # Save JSON
        json_path = self.root / 'cleanup' / '01_analysis_report.json'
        json_path.parent.mkdir(exist_ok=True)
        
        with open(json_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"   JSON report: {json_path}")
        
        # Save Markdown
        md_path = self.root / 'cleanup' / '01_ANALYSIS_REPORT.md'
        with open(md_path, 'w') as f:
            f.write(self._generate_markdown())
        
        print(f"   Markdown report: {md_path}")
    
    def _generate_markdown(self) -> str:
        """Generate markdown report."""
        md = f"""# YMERA Repository Analysis Report

**Generated:** {self.results['timestamp']}

---

## Executive Summary

- **Total Files:** {self.results['summary'].get('total_files', 0)}
- **Duplicate Files:** {self.results['summary'].get('duplicate_files', 0)}
- **Files with Multiple Versions:** {self.results['summary'].get('versioned_files', 0)}
- **Configuration Files:** {self.results['configs'].get('total', 0)}

---

## File Breakdown

| Category | Count |
|----------|-------|
| Agents | {len(self.results['file_catalog'].get('agents', []))} |
| Engines | {len(self.results['file_catalog'].get('engines', []))} |
| Utilities | {len(self.results['file_catalog'].get('utilities', []))} |
| Core | {len(self.results['file_catalog'].get('core', []))} |
| Shared | {len(self.results['file_catalog'].get('shared', []))} |
| Other | {len(self.results['file_catalog'].get('other', []))} |

---

## Duplicate Files

Found **{len(self.results['duplicates'])}** groups of duplicate files:

"""
        
        for i, (hash_val, files) in enumerate(list(self.results['duplicates'].items())[:10], 1):
            md += f"\n### Duplicate Group {i} ({len(files)} copies)\n\n"
            for f in files:
                md += f"- `{f['path']}` ({f['size']} bytes)\n"
        
        md += "\n---\n\n## Files with Multiple Versions\n\n"
        
        for i, (base_name, versions) in enumerate(list(self.results['versions'].items())[:10], 1):
            md += f"\n### {i}. {base_name} ({len(versions)} versions)\n\n"
            for v in versions:
                md += f"- `{v['name']}` - {v['version']} ({v['lines']} lines)\n"
        
        md += "\n---\n\n## Recommendations\n\n"
        
        for rec in self.results['recommendations']:
            md += f"""
### {rec['priority']}: {rec['category']}

**Issue:** {rec['issue']}

**Action:** {rec['action']}

**Impact:** {rec['impact']}

---
"""
        
        return md
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0
    
    def _file_hash(self, file_path: Path) -> str:
        """Calculate file hash."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ''


if __name__ == "__main__":
    analyzer = RepositoryAnalyzer(Path.cwd())
    analyzer.analyze()
    
    print("\n📊 Analysis complete!")
    print("📁 Reports saved to cleanup/")
    print("\nNext step: Review cleanup/01_ANALYSIS_REPORT.md")
