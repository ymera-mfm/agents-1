#!/usr/bin/env python3
"""
Comprehensive Component Testing and Activation Report Generator
Tests all agents, engines, and utilities to identify non-functional components
"""

import ast
import importlib.util
import json
import os
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class ComponentIssue:
    """Represents an issue found in a component"""
    type: str  # 'syntax_error', 'import_error', 'missing_dependency', 'initialization_error', 'other'
    message: str
    traceback: Optional[str] = None
    fix_suggestion: Optional[str] = None


@dataclass
class ComponentResult:
    """Result of testing a single component"""
    path: str
    name: str
    category: str  # 'agent', 'engine', 'utility'
    status: str  # 'working', 'fixable', 'broken', 'syntax_error'
    issues: List[ComponentIssue] = field(default_factory=list)
    classes_found: List[str] = field(default_factory=list)
    functions_found: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    can_activate: bool = False
    activation_blockers: List[str] = field(default_factory=list)


class ComponentTester:
    """Comprehensive component tester"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.results: List[ComponentResult] = []
        self.missing_dependencies: Dict[str, int] = {}
        
    def find_components(self) -> Dict[str, List[Path]]:
        """Find all components in the repository"""
        components = {
            'agents': [],
            'engines': [],
            'utilities': []
        }
        
        # Find agent files
        for pattern in ['*agent*.py', '*Agent*.py']:
            components['agents'].extend(self.repo_path.glob(pattern))
            
        # Find engine files
        for pattern in ['*engine*.py', '*Engine*.py']:
            components['engines'].extend(self.repo_path.glob(pattern))
            
        # Find utility files (excluding tests, migrations, and common patterns)
        exclude_patterns = {
            'test_', '__pycache__', '.git', 'migrations', 
            'alembic', 'venv', '.env', '__init__.py'
        }
        
        for py_file in self.repo_path.glob('*.py'):
            if any(ex in str(py_file) for ex in exclude_patterns):
                continue
            if py_file not in components['agents'] and py_file not in components['engines']:
                components['utilities'].append(py_file)
        
        # Remove duplicates
        for key in components:
            components[key] = list(set(components[key]))
            
        return components
    
    def analyze_syntax(self, file_path: Path) -> Optional[ComponentIssue]:
        """Check for syntax errors"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            ast.parse(content)
            return None
        except SyntaxError as e:
            return ComponentIssue(
                type='syntax_error',
                message=f"Syntax error at line {e.lineno}: {e.msg}",
                traceback=traceback.format_exc(),
                fix_suggestion=f"Fix syntax error in file at line {e.lineno}"
            )
        except Exception as e:
            return ComponentIssue(
                type='syntax_error',
                message=f"Parse error: {str(e)}",
                traceback=traceback.format_exc(),
                fix_suggestion="Fix file encoding or structure issues"
            )
    
    def extract_imports(self, file_path: Path) -> Set[str]:
        """Extract all imports from a file"""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except:
            pass
        
        return imports
    
    def extract_classes_and_functions(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """Extract class and function names"""
        classes = []
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    if not node.name.startswith('_'):  # Skip private functions
                        functions.append(node.name)
        except:
            pass
        
        return classes, functions
    
    def check_import_errors(self, file_path: Path, imports: Set[str]) -> List[ComponentIssue]:
        """Check which imports are missing"""
        issues = []
        
        # Common standard library modules
        stdlib_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'typing',
            'asyncio', 'logging', 'collections', 'itertools', 'functools',
            'dataclasses', 'enum', 're', 'traceback', 'abc', 'contextlib'
        }
        
        for module in imports:
            if module in stdlib_modules:
                continue
                
            try:
                importlib.import_module(module)
            except (ImportError, SyntaxError, Exception):
                # Treat all import failures as missing dependencies
                self.missing_dependencies[module] = self.missing_dependencies.get(module, 0) + 1
                
                # Provide specific fix suggestions
                fix_map = {
                    'fastapi': 'pip install fastapi',
                    'uvicorn': 'pip install uvicorn',
                    'pydantic': 'pip install pydantic',
                    'sqlalchemy': 'pip install sqlalchemy',
                    'redis': 'pip install redis',
                    'nats': 'pip install nats-py',
                    'structlog': 'pip install structlog',
                    'psutil': 'pip install psutil',
                    'numpy': 'pip install numpy',
                    'tiktoken': 'pip install tiktoken',
                    'httpx': 'pip install httpx',
                    'aioredis': 'DEPRECATED: Use redis.asyncio instead (pip install redis)',
                    'hvac': 'pip install hvac',
                    'nltk': 'pip install nltk',
                    'spacy': 'pip install spacy',
                }
                
                issues.append(ComponentIssue(
                    type='missing_dependency',
                    message=f"Missing module: {module}",
                    fix_suggestion=fix_map.get(module, f"pip install {module}")
                ))
        
        return issues
    
    def test_component(self, file_path: Path, category: str) -> ComponentResult:
        """Test a single component"""
        result = ComponentResult(
            path=str(file_path.relative_to(self.repo_path)),
            name=file_path.stem,
            category=category,
            status='working'
        )
        
        # Check syntax
        syntax_issue = self.analyze_syntax(file_path)
        if syntax_issue:
            result.status = 'syntax_error'
            result.issues.append(syntax_issue)
            result.activation_blockers.append("Syntax error must be fixed")
            return result
        
        # Extract metadata
        result.dependencies = self.extract_imports(file_path)
        result.classes_found, result.functions_found = self.extract_classes_and_functions(file_path)
        
        # Check imports
        import_issues = self.check_import_errors(file_path, result.dependencies)
        result.issues.extend(import_issues)
        
        # Determine status
        if not result.classes_found and not result.functions_found:
            result.status = 'broken'
            result.issues.append(ComponentIssue(
                type='other',
                message="No classes or functions found",
                fix_suggestion="File appears to be empty or improperly structured"
            ))
            result.activation_blockers.append("No functional code found")
        elif import_issues:
            result.status = 'fixable'
            result.activation_blockers.append(f"{len(import_issues)} missing dependencies")
        else:
            result.status = 'working'
            result.can_activate = True
        
        # Check if it's an agent and has BaseAgent
        if category == 'agent':
            if 'BaseAgent' not in result.classes_found:
                result.issues.append(ComponentIssue(
                    type='other',
                    message="Does not inherit from BaseAgent",
                    fix_suggestion="Implement BaseAgent interface for consistency"
                ))
        
        return result
    
    def generate_report(self) -> str:
        """Generate comprehensive markdown report"""
        report_lines = [
            "# Comprehensive Component Testing and Activation Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Statistics
        total = len(self.results)
        by_status = {}
        by_category = {}
        
        for result in self.results:
            by_status[result.status] = by_status.get(result.status, 0) + 1
            by_category[result.category] = by_category.get(result.category, 0) + 1
        
        working = by_status.get('working', 0)
        fixable = by_status.get('fixable', 0)
        broken = by_status.get('broken', 0)
        syntax_errors = by_status.get('syntax_error', 0)
        
        report_lines.extend([
            f"- **Total Components Tested:** {total}",
            f"- **Working (Activatable):** {working} ({working/total*100:.1f}%)",
            f"- **Fixable (Missing Dependencies):** {fixable} ({fixable/total*100:.1f}%)",
            f"- **Broken:** {broken} ({broken/total*100:.1f}%)",
            f"- **Syntax Errors:** {syntax_errors} ({syntax_errors/total*100:.1f}%)",
            "",
            "### By Category",
            ""
        ])
        
        for cat, count in sorted(by_category.items()):
            report_lines.append(f"- **{cat.title()}:** {count}")
        
        report_lines.extend([
            "",
            "## Detailed Findings",
            ""
        ])
        
        # Organize by category
        for category in ['agents', 'engines', 'utilities']:
            cat_results = [r for r in self.results if r.category == category]
            if not cat_results:
                continue
                
            report_lines.extend([
                f"### {category.title()} ({len(cat_results)} files)",
                ""
            ])
            
            # Group by status
            for status in ['working', 'fixable', 'syntax_error', 'broken']:
                status_results = [r for r in cat_results if r.status == status]
                if not status_results:
                    continue
                
                status_label = {
                    'working': '✅ Working & Activatable',
                    'fixable': '⚠️ Fixable (Missing Dependencies)',
                    'syntax_error': '❌ Syntax Errors',
                    'broken': '❌ Broken'
                }
                
                report_lines.extend([
                    f"#### {status_label[status]} ({len(status_results)} files)",
                    ""
                ])
                
                for result in sorted(status_results, key=lambda x: x.name):
                    report_lines.append(f"**{result.name}** (`{result.path}`)")
                    
                    if result.issues:
                        report_lines.append("")
                        report_lines.append("Issues:")
                        for issue in result.issues:
                            report_lines.append(f"- {issue.type.upper()}: {issue.message}")
                            if issue.fix_suggestion:
                                report_lines.append(f"  - Fix: {issue.fix_suggestion}")
                    
                    if result.activation_blockers:
                        report_lines.append("")
                        report_lines.append("Activation Blockers:")
                        for blocker in result.activation_blockers:
                            report_lines.append(f"- {blocker}")
                    
                    if result.classes_found:
                        report_lines.append(f"- Classes: {', '.join(result.classes_found[:5])}")
                    
                    report_lines.append("")
        
        # Missing dependencies summary
        if self.missing_dependencies:
            report_lines.extend([
                "## Missing Dependencies Summary",
                "",
                "The following dependencies are missing and affecting multiple components:",
                ""
            ])
            
            for dep, count in sorted(self.missing_dependencies.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"- **{dep}** - affects {count} component(s)")
            
            report_lines.extend([
                "",
                "### Installation Commands",
                "",
                "To fix most dependency issues, run:",
                "```bash"
            ])
            
            # Group installation commands
            standard_deps = []
            special_cases = {
                'aioredis': '# DEPRECATED: Use redis[hiredis] instead',
                'nats': 'pip install nats-py'
            }
            
            for dep in sorted(self.missing_dependencies.keys()):
                if dep in special_cases:
                    report_lines.append(special_cases[dep])
                else:
                    standard_deps.append(dep)
            
            if standard_deps:
                report_lines.append(f"pip install {' '.join(standard_deps)}")
            
            report_lines.append("```")
            report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "## Recommendations & Next Steps",
            "",
            "### Priority 1: Fix Syntax Errors (Critical)",
            ""
        ])
        
        syntax_error_results = [r for r in self.results if r.status == 'syntax_error']
        if syntax_error_results:
            for result in syntax_error_results:
                report_lines.append(f"- Fix `{result.path}`")
                for issue in result.issues:
                    if issue.type == 'syntax_error':
                        report_lines.append(f"  - {issue.message}")
        else:
            report_lines.append("✅ No syntax errors found!")
        
        report_lines.extend([
            "",
            "### Priority 2: Install Missing Dependencies (High)",
            "",
            f"Run the installation commands above to enable {fixable} fixable components.",
            "",
            "### Priority 3: Review Broken Components (Medium)",
            ""
        ])
        
        broken_results = [r for r in self.results if r.status == 'broken']
        if broken_results:
            report_lines.append(f"Review and refactor {len(broken_results)} broken components:")
            for result in broken_results[:10]:  # Show first 10
                report_lines.append(f"- `{result.path}`")
        
        report_lines.extend([
            "",
            "### Priority 4: Activate Working Components (Low)",
            "",
            f"{working} components are ready for activation. Ensure they are:",
            "- Integrated into the main application",
            "- Properly configured with environment variables",
            "- Documented for users",
            ""
        ])
        
        return "\n".join(report_lines)
    
    def run_tests(self):
        """Run all tests and generate report"""
        print("🔍 Discovering components...")
        components = self.find_components()
        
        total_files = sum(len(files) for files in components.values())
        print(f"Found {total_files} component files")
        
        for category, files in components.items():
            print(f"\n📝 Testing {len(files)} {category}...")
            
            for i, file_path in enumerate(files, 1):
                print(f"  [{i}/{len(files)}] {file_path.name}...", end=' ')
                result = self.test_component(file_path, category.rstrip('s'))  # Remove 's' from category
                self.results.append(result)
                
                status_icon = {
                    'working': '✅',
                    'fixable': '⚠️',
                    'syntax_error': '❌',
                    'broken': '❌'
                }
                print(f"{status_icon.get(result.status, '❓')} {result.status}")
        
        print("\n" + "="*80)
        print("📊 Generating report...")
        report = self.generate_report()
        
        # Save report
        report_path = self.repo_path / "COMPONENT_ACTIVATION_REPORT.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"✅ Report saved to: {report_path}")
        
        # Also save JSON data
        json_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': len(self.results),
                'working': sum(1 for r in self.results if r.status == 'working'),
                'fixable': sum(1 for r in self.results if r.status == 'fixable'),
                'broken': sum(1 for r in self.results if r.status == 'broken'),
                'syntax_errors': sum(1 for r in self.results if r.status == 'syntax_error')
            },
            'components': [
                {
                    'path': r.path,
                    'name': r.name,
                    'category': r.category,
                    'status': r.status,
                    'can_activate': r.can_activate,
                    'issues': [
                        {
                            'type': i.type,
                            'message': i.message,
                            'fix_suggestion': i.fix_suggestion
                        } for i in r.issues
                    ],
                    'classes': r.classes_found,
                    'functions': r.functions_found[:10],  # Limit to first 10
                    'activation_blockers': r.activation_blockers
                } for r in self.results
            ],
            'missing_dependencies': self.missing_dependencies
        }
        
        json_path = self.repo_path / "component_activation_data.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"✅ JSON data saved to: {json_path}")
        print("\n" + "="*80)
        print("🎉 Testing complete!")


def main():
    """Main entry point"""
    repo_path = Path(__file__).parent
    
    print("="*80)
    print("COMPREHENSIVE COMPONENT TESTING & ACTIVATION REPORT")
    print("="*80)
    print()
    
    tester = ComponentTester(repo_path)
    tester.run_tests()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
