#!/usr/bin/env python3
"""
YMERA Platform Audit System
Comprehensive component inventory and architecture documentation generator
"""

import os
import json
import ast
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, asdict


@dataclass
class ComponentInfo:
    """Detailed information about a component"""
    name: str
    path: str
    category: str
    purpose: str
    dependencies: List[str]
    public_api: List[str]
    state: str  # complete, incomplete, deprecated
    loc: int
    has_tests: bool
    test_coverage: Optional[float]
    last_modified: str
    imports: List[str]
    exports: List[str]
    classes: List[str]
    functions: List[str]


class PlatformAuditor:
    """Comprehensive platform auditing and documentation system"""
    
    CATEGORIES = {
        'core': ['config', 'auth', 'database', 'manager', 'models'],
        'middleware': ['rate_limiter', 'middleware', 'circuit_breaker'],
        'agents': ['agent', 'learning', 'llm', 'communication', 'drafting', 
                   'editing', 'enhancement', 'examination', 'metrics', 'orchestrator',
                   'monitoring', 'security', 'validation', 'coding', 'surveillance'],
        'engines': ['engine', 'workflow', 'performance', 'intelligence', 
                    'optimization', 'analytics', 'recommendation', 'learning_engine'],
        'api': ['routes', 'api', 'gateway', 'endpoints', 'main'],
        'database': ['models', 'schema', 'migration', 'alembic'],
        'testing': ['test_', 'conftest', 'pytest', 'fixture'],
        'deployment': ['docker', 'terraform', 'k8s', 'deploy', 'config'],
        'utilities': ['utils', 'helper', 'cache', 'logger', 'monitor'],
        'documentation': ['.md', '.txt', 'readme', 'guide'],
    }
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.components: Dict[str, List[ComponentInfo]] = defaultdict(list)
        self.all_files: List[Path] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.orphaned_files: List[str] = []
        self.missing_tests: List[str] = []
        self.total_loc = 0
        
    def scan_repository(self) -> None:
        """Recursively scan repository for all Python files"""
        print("📂 Scanning repository...")
        
        exclude_dirs = {'.git', '__pycache__', 'venv', 'env', '.pytest_cache', 
                       '.mypy_cache', 'node_modules', 'dist', 'build'}
        
        for py_file in self.repo_path.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue
            self.all_files.append(py_file)
        
        print(f"   Found {len(self.all_files)} Python files")
    
    def categorize_file(self, file_path: Path) -> str:
        """Determine the category of a file based on its name and content"""
        file_name = file_path.name.lower()
        file_content = file_path.read_text(errors='ignore').lower()
        
        # Check each category
        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in file_name or keyword in file_content[:500]:
                    return category
        
        return 'utilities'
    
    def extract_imports(self, content: str) -> List[str]:
        """Extract import statements from Python code"""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            # Fallback to regex if AST parsing fails
            import_pattern = r'^(?:from|import)\s+([\w\.]+)'
            imports = re.findall(import_pattern, content, re.MULTILINE)
        
        return list(set(imports))
    
    def extract_public_api(self, content: str, file_path: Path) -> Dict[str, List[str]]:
        """Extract public classes and functions"""
        classes = []
        functions = []
        exports = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):
                        classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        functions.append(node.name)
                        
            # Check for __all__ export
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__all__':
                            if isinstance(node.value, ast.List):
                                exports = [elt.s for elt in node.value.elts 
                                         if isinstance(elt, ast.Constant)]
        except:
            pass
        
        return {
            'classes': classes,
            'functions': functions,
            'exports': exports if exports else classes + functions
        }
    
    def determine_state(self, content: str, file_path: Path) -> str:
        """Determine if component is complete, incomplete, or deprecated"""
        content_lower = content.lower()
        
        if 'deprecated' in content_lower or 'todo: remove' in content_lower:
            return 'deprecated'
        elif 'todo' in content_lower or 'fixme' in content_lower or 'wip' in content_lower:
            return 'incomplete'
        elif len(content.strip()) < 100:
            return 'incomplete'
        else:
            return 'complete'
    
    def find_test_file(self, file_path: Path) -> Optional[Path]:
        """Find corresponding test file for a component"""
        test_patterns = [
            f"test_{file_path.stem}.py",
            f"{file_path.stem}_test.py",
            f"tests/test_{file_path.stem}.py",
            f"tests/unit/test_{file_path.stem}.py",
            f"tests/integration/test_{file_path.stem}.py",
        ]
        
        for pattern in test_patterns:
            test_path = self.repo_path / pattern
            if test_path.exists():
                return test_path
        
        return None
    
    def analyze_component(self, file_path: Path) -> ComponentInfo:
        """Perform deep analysis of a single component"""
        try:
            content = file_path.read_text(errors='ignore')
            
            # Extract information
            imports = self.extract_imports(content)
            api_info = self.extract_public_api(content, file_path)
            state = self.determine_state(content, file_path)
            loc = len([line for line in content.split('\n') if line.strip()])
            
            # Determine purpose from docstrings or comments
            purpose = self.extract_purpose(content, file_path)
            
            # Check for tests
            test_file = self.find_test_file(file_path)
            has_tests = test_file is not None
            
            # Get last modified time
            last_modified = datetime.fromtimestamp(
                file_path.stat().st_mtime
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            # Categorize
            category = self.categorize_file(file_path)
            
            # Create component info
            component = ComponentInfo(
                name=file_path.stem,
                path=str(file_path.relative_to(self.repo_path)),
                category=category,
                purpose=purpose,
                dependencies=imports,
                public_api=api_info['exports'],
                state=state,
                loc=loc,
                has_tests=has_tests,
                test_coverage=None,  # Would need coverage data
                last_modified=last_modified,
                imports=imports,
                exports=api_info['exports'],
                classes=api_info['classes'],
                functions=api_info['functions']
            )
            
            self.total_loc += loc
            
            # Track dependencies
            for imp in imports:
                self.dependency_graph[file_path.stem].add(imp)
            
            # Track missing tests
            if not has_tests and category in ['agents', 'engines', 'core', 'api']:
                self.missing_tests.append(str(file_path.relative_to(self.repo_path)))
            
            return component
            
        except Exception as e:
            print(f"   ⚠️  Error analyzing {file_path}: {e}")
            return None
    
    def extract_purpose(self, content: str, file_path: Path) -> str:
        """Extract purpose from docstrings or initial comments"""
        lines = content.split('\n')
        
        # Try to extract from module docstring
        if content.strip().startswith('"""') or content.strip().startswith("'''"):
            docstring_match = re.search(r'^["\']{{3}}([^"\']+)["\']{{3}}', content, re.MULTILINE | re.DOTALL)
            if docstring_match:
                doc = docstring_match.group(1).strip()
                # Get first meaningful line
                for line in doc.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        return line[:200]
        
        # Try to extract from first comment
        for line in lines[:20]:
            line = line.strip()
            if line.startswith('#') and len(line) > 3:
                comment = line.lstrip('#').strip()
                if len(comment) > 10:
                    return comment[:200]
        
        # Use filename as fallback
        return f"{file_path.stem.replace('_', ' ').title()}"
    
    def find_orphaned_files(self) -> None:
        """Identify files that are not imported anywhere"""
        print("🔍 Finding orphaned files...")
        
        imported_modules = set()
        for deps in self.dependency_graph.values():
            imported_modules.update(deps)
        
        for file_path in self.all_files:
            module_name = file_path.stem
            # Check if module is imported
            is_imported = any(
                module_name in dep or dep.endswith(module_name)
                for dep in imported_modules
            )
            
            # Skip special files
            special_files = {'__init__', 'main', 'conftest', 'setup'}
            if module_name not in special_files and not is_imported:
                # Additional check: is it a test file or script?
                if not (module_name.startswith('test_') or 
                       module_name.endswith('_test') or
                       'script' in module_name):
                    self.orphaned_files.append(str(file_path.relative_to(self.repo_path)))
    
    def generate_inventory_json(self, output_path: Path) -> None:
        """Generate machine-readable JSON inventory"""
        print("📝 Generating JSON inventory...")
        
        # Prepare summary
        summary = {
            'total_files': len(self.all_files),
            'total_lines': self.total_loc,
            'categories': {
                category: len(components)
                for category, components in self.components.items()
            },
            'scan_date': datetime.now().isoformat(),
            'orphaned_files': len(self.orphaned_files),
            'missing_tests': len(self.missing_tests)
        }
        
        # Prepare components data
        components_data = {}
        for category, components in self.components.items():
            components_data[category] = [
                {
                    'name': c.name,
                    'path': c.path,
                    'purpose': c.purpose,
                    'dependencies': c.dependencies,
                    'public_api': c.public_api,
                    'state': c.state,
                    'loc': c.loc,
                    'has_tests': c.has_tests,
                    'test_coverage': c.test_coverage,
                    'last_modified': c.last_modified,
                    'classes': c.classes,
                    'functions': c.functions
                }
                for c in components
            ]
        
        inventory = {
            'summary': summary,
            'components': components_data,
            'dependency_graph': {
                k: list(v) for k, v in self.dependency_graph.items()
            },
            'orphaned_files': self.orphaned_files,
            'missing_tests': self.missing_tests
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(inventory, f, indent=2)
        
        print(f"   ✅ JSON inventory saved to {output_path}")
    
    def generate_inventory_markdown(self, output_path: Path) -> None:
        """Generate human-readable Markdown report"""
        print("📝 Generating Markdown report...")
        
        md = []
        md.append("# YMERA Platform Component Inventory")
        md.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Executive Summary
        md.append("## 📊 Executive Summary\n")
        md.append(f"- **Total Files**: {len(self.all_files)}")
        md.append(f"- **Total Lines of Code**: {self.total_loc:,}")
        md.append(f"- **Component Categories**: {len(self.components)}")
        md.append(f"- **Orphaned Files**: {len(self.orphaned_files)}")
        md.append(f"- **Files Missing Tests**: {len(self.missing_tests)}\n")
        
        # Category Breakdown
        md.append("### Component Breakdown by Category\n")
        for category, components in sorted(self.components.items()):
            total_loc = sum(c.loc for c in components)
            md.append(f"- **{category.title()}**: {len(components)} files ({total_loc:,} LOC)")
        md.append("")
        
        # Component Details by Category
        md.append("## 📦 Component Details\n")
        
        for category in sorted(self.components.keys()):
            components = self.components[category]
            if not components:
                continue
                
            md.append(f"### {category.title()} ({len(components)} components)\n")
            
            for comp in sorted(components, key=lambda x: x.name):
                md.append(f"#### `{comp.name}`")
                md.append(f"- **Path**: `{comp.path}`")
                md.append(f"- **Purpose**: {comp.purpose}")
                md.append(f"- **State**: {comp.state.upper()}")
                md.append(f"- **Lines of Code**: {comp.loc}")
                md.append(f"- **Has Tests**: {'✅' if comp.has_tests else '❌'}")
                
                if comp.classes:
                    md.append(f"- **Classes**: {', '.join(comp.classes[:5])}")
                    if len(comp.classes) > 5:
                        md.append(f"  *(+{len(comp.classes)-5} more)*")
                
                if comp.functions:
                    md.append(f"- **Functions**: {', '.join(comp.functions[:5])}")
                    if len(comp.functions) > 5:
                        md.append(f"  *(+{len(comp.functions)-5} more)*")
                
                if comp.dependencies:
                    md.append(f"- **Dependencies**: {len(comp.dependencies)} modules")
                
                md.append(f"- **Last Modified**: {comp.last_modified}")
                md.append("")
        
        # Dependency Information
        md.append("## 🔗 Dependency Analysis\n")
        md.append("### Most Depended Upon Modules\n")
        
        # Count how many times each module is imported
        import_counts = defaultdict(int)
        for deps in self.dependency_graph.values():
            for dep in deps:
                import_counts[dep] += 1
        
        top_imports = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        for module, count in top_imports:
            md.append(f"- `{module}`: imported {count} times")
        md.append("")
        
        # Orphaned Files
        if self.orphaned_files:
            md.append("## 🔍 Orphaned Files\n")
            md.append("*Files that appear not to be imported anywhere:*\n")
            for file in self.orphaned_files[:30]:
                md.append(f"- `{file}`")
            if len(self.orphaned_files) > 30:
                md.append(f"\n*...and {len(self.orphaned_files)-30} more*")
            md.append("")
        
        # Missing Tests
        if self.missing_tests:
            md.append("## ❌ Files Missing Tests\n")
            md.append("*Core components without test coverage:*\n")
            for file in self.missing_tests[:30]:
                md.append(f"- `{file}`")
            if len(self.missing_tests) > 30:
                md.append(f"\n*...and {len(self.missing_tests)-30} more*")
            md.append("")
        
        # Documentation Gaps
        md.append("## 📚 Documentation Gaps\n")
        incomplete_components = [
            c for components in self.components.values() 
            for c in components 
            if c.state == 'incomplete'
        ]
        md.append(f"\nFound {len(incomplete_components)} components marked as incomplete:\n")
        for comp in incomplete_components[:20]:
            md.append(f"- `{comp.path}` - {comp.purpose}")
        md.append("")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(md))
        
        print(f"   ✅ Markdown report saved to {output_path}")
    
    def run_audit(self, output_dir: Path) -> None:
        """Run complete audit process"""
        print("\n" + "="*70)
        print("🔍 YMERA Platform Comprehensive Audit")
        print("="*70 + "\n")
        
        # Step 1: Scan repository
        self.scan_repository()
        
        # Step 2: Analyze all components
        print("🔬 Analyzing components...")
        for i, file_path in enumerate(self.all_files, 1):
            if i % 20 == 0:
                print(f"   Processed {i}/{len(self.all_files)} files...")
            
            component = self.analyze_component(file_path)
            if component:
                self.components[component.category].append(component)
        
        print(f"   ✅ Analyzed {len(self.all_files)} files")
        
        # Step 3: Find orphaned files
        self.find_orphaned_files()
        
        # Step 4: Generate outputs
        inventory_dir = output_dir / 'inventory'
        self.generate_inventory_json(inventory_dir / 'platform_inventory.json')
        self.generate_inventory_markdown(inventory_dir / 'platform_inventory.md')
        
        print("\n" + "="*70)
        print("✅ Audit Complete!")
        print("="*70 + "\n")
        print(f"📊 Summary:")
        print(f"   • Analyzed {len(self.all_files)} files")
        print(f"   • Total {self.total_loc:,} lines of code")
        print(f"   • Found {len(self.orphaned_files)} orphaned files")
        print(f"   • Found {len(self.missing_tests)} files without tests")
        print(f"\n📁 Reports saved to: {output_dir}")


def main():
    """Main entry point"""
    repo_path = Path(__file__).parent
    output_dir = repo_path / 'audit_reports'
    
    auditor = PlatformAuditor(repo_path)
    auditor.run_audit(output_dir)
    
    print("\n✨ Audit system completed successfully!")


if __name__ == '__main__':
    main()
