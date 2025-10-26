#!/usr/bin/env python3
"""
Repository Status Validator

This script validates the repository is in a clean, ready state for future operations.
It checks for:
- Essential files and directories
- Python environment compatibility
- Basic file integrity
- Git repository status

Date: October 25, 2025
Purpose: Establish baseline repository health check
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple


class RepositoryStatusChecker:
    """Validates repository readiness for future commands."""
    
    def __init__(self, repo_root: str = None):
        self.repo_root = Path(repo_root or os.getcwd())
        self.results = {
            "status": "unknown",
            "checks": {},
            "warnings": [],
            "errors": []
        }
    
    def check_essential_files(self) -> bool:
        """Check that essential project files exist."""
        essential_files = [
            "README.md",
            "requirements.txt",
            "main.py",
            ".gitignore",
            ".env.example"
        ]
        
        missing = []
        for file in essential_files:
            file_path = self.repo_root / file
            if not file_path.exists():
                missing.append(file)
        
        if missing:
            self.results["errors"].append(f"Missing essential files: {', '.join(missing)}")
            return False
        
        self.results["checks"]["essential_files"] = "PASS"
        return True
    
    def check_directory_structure(self) -> bool:
        """Check that key directories exist."""
        key_dirs = [
            "tests",
            "agents",
            "core",
            ".github"
        ]
        
        missing = []
        for dir_name in key_dirs:
            dir_path = self.repo_root / dir_name
            if not dir_path.exists():
                missing.append(dir_name)
        
        if missing:
            self.results["warnings"].append(f"Missing directories: {', '.join(missing)}")
        
        self.results["checks"]["directory_structure"] = "PASS" if not missing else "WARN"
        return True
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        version_info = sys.version_info
        
        if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 11):
            self.results["errors"].append(
                f"Python 3.11+ required, found {version_info.major}.{version_info.minor}"
            )
            return False
        
        self.results["checks"]["python_version"] = f"PASS ({version_info.major}.{version_info.minor})"
        return True
    
    def check_git_status(self) -> bool:
        """Check git repository status."""
        git_dir = self.repo_root / ".git"
        
        if not git_dir.exists():
            self.results["errors"].append("Not a git repository")
            return False
        
        self.results["checks"]["git_repository"] = "PASS"
        return True
    
    def check_file_counts(self) -> bool:
        """Count Python files to ensure repository has content."""
        py_files = list(self.repo_root.glob("*.py"))
        test_files = list((self.repo_root / "tests").glob("**/*.py")) if (self.repo_root / "tests").exists() else []
        
        if len(py_files) < 5:
            self.results["warnings"].append(f"Only {len(py_files)} Python files in root directory")
        
        self.results["checks"]["python_files"] = f"PASS ({len(py_files)} root, {len(test_files)} test files)"
        return True
    
    def run_all_checks(self) -> Dict:
        """Run all validation checks."""
        checks = [
            ("Python Version", self.check_python_version),
            ("Git Repository", self.check_git_status),
            ("Essential Files", self.check_essential_files),
            ("Directory Structure", self.check_directory_structure),
            ("File Counts", self.check_file_counts)
        ]
        
        all_passed = True
        for name, check_func in checks:
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.results["errors"].append(f"{name} check failed: {str(e)}")
                all_passed = False
        
        # Determine overall status
        if self.results["errors"]:
            self.results["status"] = "FAIL"
        elif self.results["warnings"]:
            self.results["status"] = "WARN"
        else:
            self.results["status"] = "PASS"
        
        return self.results
    
    def print_report(self):
        """Print a formatted status report."""
        print("\n" + "="*70)
        print("REPOSITORY STATUS REPORT")
        print("="*70)
        print(f"\nOverall Status: {self.results['status']}")
        print(f"Repository: {self.repo_root}")
        print(f"Date: October 25, 2025")
        
        print("\n" + "-"*70)
        print("CHECKS:")
        print("-"*70)
        for check_name, result in self.results["checks"].items():
            print(f"  ✓ {check_name:.<50} {result}")
        
        if self.results["warnings"]:
            print("\n" + "-"*70)
            print("WARNINGS:")
            print("-"*70)
            for warning in self.results["warnings"]:
                print(f"  ⚠ {warning}")
        
        if self.results["errors"]:
            print("\n" + "-"*70)
            print("ERRORS:")
            print("-"*70)
            for error in self.results["errors"]:
                print(f"  ✗ {error}")
        
        print("\n" + "="*70)
        print()


def main():
    """Main entry point."""
    checker = RepositoryStatusChecker()
    results = checker.run_all_checks()
    checker.print_report()
    
    # Save results to JSON
    output_file = Path("repository_status_report.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Detailed report saved to: {output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if results["status"] in ["PASS", "WARN"] else 1)


if __name__ == "__main__":
    main()
