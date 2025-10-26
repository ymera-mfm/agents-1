#!/usr/bin/env python3
"""
Systematic Issue Finder and Fixer
Identifies and fixes issues systematically
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

class SystematicFixer:
    def __init__(self):
        self.root = Path(".")
        self.issues = []
        self.fixes = []
    
    def find_unused_imports(self, file_path: Path) -> List[Dict]:
        """Find potentially unused imports"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            imports = []
            for i, line in enumerate(lines, 1):
                # Find import statements
                if line.strip().startswith('import '):
                    match = re.match(r'import\s+(\w+)', line.strip())
                    if match:
                        module = match.group(1)
                        # Check if used
                        if content.count(module + '.') == 0 and content.count(module + '(') == 0:
                            # Might be unused
                            issues.append({
                                "file": str(file_path),
                                "line": i,
                                "type": "potentially_unused_import",
                                "module": module,
                                "content": line.strip()
                            })
                            
                elif line.strip().startswith('from '):
                    match = re.match(r'from\s+\S+\s+import\s+(.+)', line.strip())
                    if match:
                        imported = match.group(1)
                        # Parse imported items
                        items = [item.strip().split(' as ')[0] for item in imported.split(',')]
                        for item in items:
                            item = item.strip()
                            if item and content.count(item) <= 1:  # Only in import line
                                issues.append({
                                    "file": str(file_path),
                                    "line": i,
                                    "type": "potentially_unused_import",
                                    "module": item,
                                    "content": line.strip()
                                })
        except Exception as e:
            pass
        
        return issues
    
    def find_missing_type_hints(self, file_path: Path) -> List[Dict]:
        """Find functions missing type hints"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Find function definitions
                if line.strip().startswith('def ') or line.strip().startswith('async def '):
                    # Check if it has type hints
                    if '->' not in line and 'test_' not in line:  # Skip test functions
                        # Extract function name
                        match = re.search(r'def\s+(\w+)\s*\(', line)
                        if match:
                            func_name = match.group(1)
                            if not func_name.startswith('_'):  # Skip private
                                issues.append({
                                    "file": str(file_path),
                                    "line": i,
                                    "type": "missing_return_type_hint",
                                    "function": func_name,
                                    "content": line.strip()[:80]
                                })
        except Exception as e:
            pass
        
        return issues
    
    def find_print_statements(self, file_path: Path) -> List[Dict]:
        """Find print statements that should be logging"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                if 'print(' in line and not line.strip().startswith('#'):
                    # Skip if in test file
                    if 'test' in file_path.name.lower():
                        continue
                    
                    issues.append({
                        "file": str(file_path),
                        "line": i,
                        "type": "print_statement",
                        "content": line.strip()[:80],
                        "suggestion": "Replace with logging.info/debug/warning"
                    })
        except Exception as e:
            pass
        
        return issues
    
    def find_bare_except(self, file_path: Path) -> List[Dict]:
        """Find bare except clauses"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                if line.strip() == 'except:':
                    issues.append({
                        "file": str(file_path),
                        "line": i,
                        "type": "bare_except",
                        "content": line.strip(),
                        "suggestion": "Specify exception type: except Exception:"
                    })
        except Exception as e:
            pass
        
        return issues
    
    def find_long_functions(self, file_path: Path) -> List[Dict]:
        """Find functions that are too long"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            current_func = None
            func_start = 0
            indent_level = 0
            
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('def ') or line.strip().startswith('async def '):
                    # Save previous function if too long
                    if current_func and (i - func_start) > 50:
                        issues.append({
                            "file": str(file_path),
                            "line": func_start,
                            "type": "long_function",
                            "function": current_func,
                            "lines": i - func_start,
                            "suggestion": "Consider breaking into smaller functions"
                        })
                    
                    # Start new function
                    match = re.search(r'def\s+(\w+)\s*\(', line)
                    if match:
                        current_func = match.group(1)
                        func_start = i
                        indent_level = len(line) - len(line.lstrip())
        except Exception as e:
            pass
        
        return issues
    
    def fix_bare_except(self, file_path: Path) -> bool:
        """Fix bare except clauses"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace bare except with except Exception
            modified = content.replace('\nexcept:', '\nexcept Exception:')
            modified = modified.replace('\n    except:', '\n    except Exception:')
            modified = modified.replace('\n        except:', '\n        except Exception:')
            
            if modified != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified)
                return True
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
        
        return False
    
    def analyze_files(self, file_paths: List[Path]) -> Dict:
        """Analyze files for issues"""
        print("🔍 Analyzing Files for Issues")
        print("-" * 70)
        
        all_issues = {
            "unused_imports": [],
            "missing_type_hints": [],
            "print_statements": [],
            "bare_except": [],
            "long_functions": []
        }
        
        for file_path in file_paths:
            if not file_path.exists():
                continue
            
            # Find various issues
            all_issues["unused_imports"].extend(self.find_unused_imports(file_path))
            all_issues["missing_type_hints"].extend(self.find_missing_type_hints(file_path))
            all_issues["print_statements"].extend(self.find_print_statements(file_path))
            all_issues["bare_except"].extend(self.find_bare_except(file_path))
            all_issues["long_functions"].extend(self.find_long_functions(file_path))
        
        # Print summary
        for issue_type, issues in all_issues.items():
            if issues:
                print(f"   {issue_type.replace('_', ' ').title()}: {len(issues)}")
        
        self.issues = all_issues
        print()
        return all_issues
    
    def apply_fixes(self) -> int:
        """Apply automatic fixes"""
        print("🔧 Applying Automatic Fixes")
        print("-" * 70)
        
        fixes_count = 0
        
        # Fix bare except clauses
        files_to_fix = set()
        for issue in self.issues["bare_except"]:
            files_to_fix.add(Path(issue["file"]))
        
        for file_path in files_to_fix:
            if self.fix_bare_except(file_path):
                print(f"   ✅ Fixed bare except in {file_path.name}")
                fixes_count += 1
                self.fixes.append({
                    "file": str(file_path),
                    "fix": "Replaced bare except with except Exception"
                })
        
        if fixes_count == 0:
            print("   ℹ️  No automatic fixes applied")
        else:
            print(f"\n   🎉 Applied {fixes_count} fixes")
        
        print()
        return fixes_count
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("=" * 70)
        print("📊 SYSTEMATIC ANALYSIS REPORT")
        print("=" * 70)
        
        total_issues = sum(len(issues) for issues in self.issues.values())
        
        print(f"\nTotal Issues Found: {total_issues}")
        print(f"Fixes Applied: {len(self.fixes)}")
        
        print("\n📋 Issue Breakdown:")
        for issue_type, issues in self.issues.items():
            if issues:
                print(f"   - {issue_type.replace('_', ' ').title()}: {len(issues)}")
                # Show examples
                for issue in issues[:2]:
                    print(f"      • {issue['file']}:{issue['line']}")
        
        # Save report
        report = {
            "issues": self.issues,
            "fixes": self.fixes,
            "summary": {
                "total_issues": total_issues,
                "fixes_applied": len(self.fixes)
            }
        }
        
        with open("systematic_analysis_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to: systematic_analysis_report.json")
        print("=" * 70)
    
    def run(self):
        """Run systematic analysis and fixes"""
        print("🚀 Starting Systematic Issue Finder and Fixer\n")
        
        # Get Python files to analyze
        py_files = list(self.root.glob("*.py"))
        py_files = [f for f in py_files if not f.name.startswith('test_')][:50]
        
        print(f"Analyzing {len(py_files)} Python files...\n")
        
        self.analyze_files(py_files)
        self.apply_fixes()
        self.generate_report()

def main():
    fixer = SystematicFixer()
    fixer.run()
    return 0

if __name__ == "__main__":
    sys.exit(main())
