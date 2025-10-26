#!/usr/bin/env python3
"""
Comprehensive System Analysis Tool
Analyzes code quality, structure, dependencies, and identifies issues
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
import re

class SystemAnalyzer:
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.results = {
            "summary": {},
            "code_metrics": {},
            "duplicates": [],
            "security_issues": [],
            "performance_issues": [],
            "structure_issues": [],
            "dependency_issues": []
        }
    
    def analyze_structure(self):
        """Analyze directory structure and file organization"""
        print("📁 Analyzing directory structure...")
        
        py_files = list(self.root_dir.glob("**/*.py"))
        md_files = list(self.root_dir.glob("**/*.md"))
        test_files = [f for f in py_files if "test" in f.name.lower()]
        
        # Count files by directory
        dir_counts = defaultdict(int)
        for f in py_files:
            if ".git" not in str(f) and "venv" not in str(f):
                dir_counts[f.parent] += 1
        
        # Find files in root (should be organized)
        root_py_files = [f for f in py_files if f.parent == self.root_dir]
        
        self.results["summary"]["total_py_files"] = len(py_files)
        self.results["summary"]["total_md_files"] = len(md_files)
        self.results["summary"]["test_files"] = len(test_files)
        self.results["summary"]["root_py_files"] = len(root_py_files)
        
        if len(root_py_files) > 50:
            self.results["structure_issues"].append({
                "type": "disorganized_root",
                "severity": "high",
                "message": f"{len(root_py_files)} Python files in root directory - should be organized into subdirectories",
                "files": [str(f.name) for f in root_py_files[:20]]
            })
        
        # Find duplicate file names
        file_names = defaultdict(list)
        for f in py_files:
            if ".git" not in str(f):
                file_names[f.name].append(str(f))
        
        duplicates = {name: paths for name, paths in file_names.items() if len(paths) > 1}
        if duplicates:
            self.results["structure_issues"].append({
                "type": "duplicate_filenames",
                "severity": "medium",
                "count": len(duplicates),
                "examples": dict(list(duplicates.items())[:10])
            })
        
        return self.results["summary"]
    
    def analyze_code_quality(self):
        """Analyze code quality metrics"""
        print("📊 Analyzing code quality...")
        
        py_files = [str(f) for f in self.root_dir.glob("**/*.py") 
                    if ".git" not in str(f) and "venv" not in str(f)]
        
        if not py_files:
            print("No Python files found!")
            return
        
        # Calculate lines of code
        total_lines = 0
        total_code_lines = 0
        total_comment_lines = 0
        blank_lines = 0
        large_files = []
        
        for file_path in py_files[:100]:  # Sample first 100 files
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            blank_lines += 1
                        elif stripped.startswith('#'):
                            total_comment_lines += 1
                        else:
                            total_code_lines += 1
                    
                    if len(lines) > 500:
                        large_files.append({
                            "file": file_path,
                            "lines": len(lines)
                        })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        self.results["code_metrics"]["total_lines"] = total_lines
        self.results["code_metrics"]["code_lines"] = total_code_lines
        self.results["code_metrics"]["comment_lines"] = total_comment_lines
        self.results["code_metrics"]["blank_lines"] = blank_lines
        self.results["code_metrics"]["comment_ratio"] = (
            total_comment_lines / total_code_lines * 100 if total_code_lines > 0 else 0
        )
        
        if large_files:
            self.results["code_metrics"]["large_files"] = sorted(
                large_files, key=lambda x: x["lines"], reverse=True
            )[:10]
    
    def detect_duplicates(self):
        """Detect duplicate code patterns"""
        print("🔍 Detecting duplicate code...")
        
        # Find files with similar names
        py_files = list(self.root_dir.glob("**/*.py"))
        
        # Check for old/backup files
        old_patterns = ['old', 'backup', 'deprecated', 'copy', 'temp', '_bak']
        old_files = []
        
        for f in py_files:
            if any(pattern in f.name.lower() for pattern in old_patterns):
                old_files.append(str(f))
        
        if old_files:
            self.results["duplicates"].append({
                "type": "old_backup_files",
                "count": len(old_files),
                "files": old_files[:20]
            })
        
        # Find files with wrong extensions
        wrong_ext = list(self.root_dir.glob("**/*.jsx")) + list(self.root_dir.glob("**/*.js.jsx"))
        if wrong_ext:
            self.results["duplicates"].append({
                "type": "wrong_extensions",
                "count": len(wrong_ext),
                "files": [str(f) for f in wrong_ext[:20]]
            })
    
    def check_security(self):
        """Run security checks"""
        print("🔒 Checking security issues...")
        
        # Check for common security issues in Python files
        py_files = [str(f) for f in self.root_dir.glob("**/*.py") 
                    if ".git" not in str(f)][:50]
        
        security_patterns = {
            "sql_injection": re.compile(r'(execute|query)\s*\(\s*["\'].*%s.*["\'].*%'),
            "hardcoded_password": re.compile(r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
            "hardcoded_key": re.compile(r'(secret_key|api_key|private_key)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
            "eval_usage": re.compile(r'\beval\s*\('),
            "exec_usage": re.compile(r'\bexec\s*\('),
        }
        
        for file_path in py_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    for issue_type, pattern in security_patterns.items():
                        matches = pattern.findall(content)
                        if matches:
                            self.results["security_issues"].append({
                                "type": issue_type,
                                "file": file_path,
                                "occurrences": len(matches),
                                "severity": "high" if issue_type in ["eval_usage", "sql_injection"] else "medium"
                            })
            except Exception as e:
                continue
    
    def analyze_dependencies(self):
        """Analyze project dependencies"""
        print("📦 Analyzing dependencies...")
        
        req_file = self.root_dir / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    self.results["summary"]["total_dependencies"] = len(deps)
                    self.results["summary"]["dependencies_sample"] = deps[:20]
            except Exception as e:
                print(f"Error reading requirements.txt: {e}")
    
    def check_tests(self):
        """Check test coverage and structure"""
        print("🧪 Analyzing test structure...")
        
        test_files = list(self.root_dir.glob("**/test_*.py"))
        test_files += list(self.root_dir.glob("**/*_test.py"))
        test_files += list(self.root_dir.glob("**/tests/**/*.py"))
        
        self.results["summary"]["test_files_found"] = len(test_files)
        
        # Try to run pytest to get coverage info
        if test_files:
            print("  Found test files, attempting pytest discovery...")
            try:
                result = subprocess.run(
                    ["pytest", "--collect-only", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.root_dir
                )
                if result.returncode == 0:
                    # Parse output to count tests
                    output = result.stdout
                    self.results["summary"]["pytest_collection"] = "success"
            except Exception as e:
                self.results["summary"]["pytest_collection"] = f"failed: {str(e)}"
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE SYSTEM ANALYSIS REPORT")
        print("="*80)
        
        print("\n📊 SUMMARY")
        print("-"*80)
        for key, value in self.results["summary"].items():
            if isinstance(value, list):
                print(f"{key}: {len(value)} items")
            else:
                print(f"{key}: {value}")
        
        print("\n📈 CODE METRICS")
        print("-"*80)
        for key, value in self.results["code_metrics"].items():
            if key != "large_files":
                print(f"{key}: {value}")
        
        if "large_files" in self.results["code_metrics"]:
            print("\n⚠️  Large Files (>500 lines):")
            for f in self.results["code_metrics"]["large_files"][:10]:
                print(f"  - {f['file']}: {f['lines']} lines")
        
        print("\n🔄 DUPLICATES & STRUCTURE ISSUES")
        print("-"*80)
        if self.results["duplicates"]:
            for dup in self.results["duplicates"]:
                print(f"  [{dup['type']}] Found {dup['count']} issues")
        else:
            print("  ✅ No obvious duplicates found")
        
        if self.results["structure_issues"]:
            for issue in self.results["structure_issues"]:
                print(f"  [{issue['severity'].upper()}] {issue['type']}: {issue['message']}")
        
        print("\n🔒 SECURITY ISSUES")
        print("-"*80)
        if self.results["security_issues"]:
            sec_by_type = defaultdict(int)
            for issue in self.results["security_issues"]:
                sec_by_type[issue['type']] += 1
            
            for issue_type, count in sec_by_type.items():
                print(f"  ⚠️  {issue_type}: {count} occurrences")
        else:
            print("  ✅ No obvious security issues detected")
        
        # Save to JSON
        output_file = self.root_dir / "system_analysis_report.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Full report saved to: {output_file}")
        print("="*80)
        
        return self.results
    
    def run_full_analysis(self):
        """Run all analysis steps"""
        print("🚀 Starting Comprehensive System Analysis\n")
        
        self.analyze_structure()
        self.analyze_code_quality()
        self.detect_duplicates()
        self.check_security()
        self.analyze_dependencies()
        self.check_tests()
        
        return self.generate_report()

def main():
    analyzer = SystemAnalyzer()
    results = analyzer.run_full_analysis()
    
    # Return exit code based on critical issues
    critical_issues = sum(
        1 for issue in results["security_issues"] 
        if issue.get("severity") == "high"
    )
    
    if critical_issues > 0:
        print(f"\n⚠️  WARNING: {critical_issues} critical security issues found!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
