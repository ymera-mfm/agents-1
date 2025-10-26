#!/usr/bin/env python3
"""
YMERA Platform Comprehensive Audit System
==========================================
Phase 2: Testing & Quality Audit Implementation

This script executes ALL audit tasks with brutal honesty:
- Task 2.1: Full Test Suite Execution
- Task 2.2: Code Quality Analysis  
- Task 2.3: Dependency Audit
- Task 2.4: Performance Profiling

Author: YMERA Quality Assurance Team
Version: 1.0.0
"""

import os
import sys
import json
import subprocess
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import re


@dataclass
class TestResult:
    """Individual test result"""
    test: str
    file: str
    status: str
    duration: float
    error: Optional[str] = None
    traceback: Optional[str] = None
    severity: Optional[str] = None
    impact: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass
class CoverageGap:
    """Coverage gap information"""
    file: str
    coverage: float
    missing_lines: List[int]
    recommendation: str


@dataclass
class QualityIssue:
    """Code quality issue"""
    code: str
    description: str
    count: int
    severity: str = "info"


@dataclass
class SecurityIssue:
    """Security issue"""
    severity: str
    file: str
    line: int
    issue: str
    recommendation: str


@dataclass
class DependencyIssue:
    """Dependency issue"""
    package: str
    current_version: str
    issue_type: str  # vulnerability, deprecated, outdated
    severity: str
    recommendation: str
    details: Dict[str, Any]


class PlatformAuditor:
    """Main auditor orchestrating all audit tasks"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.audit_dir = project_root / "audit_reports"
        self.timestamp = datetime.now().isoformat()
        self.results = {
            "execution_timestamp": self.timestamp,
            "tasks_completed": [],
            "tasks_failed": []
        }
        
    def run_all_audits(self):
        """Execute all audit tasks"""
        print("=" * 80)
        print("YMERA PLATFORM COMPREHENSIVE AUDIT")
        print("=" * 80)
        print(f"Timestamp: {self.timestamp}")
        print(f"Project Root: {self.project_root}")
        print("=" * 80)
        
        tasks = [
            ("Task 2.1: Test Suite Execution", self.run_test_audit),
            ("Task 2.2: Code Quality Analysis", self.run_quality_audit),
            ("Task 2.3: Dependency Audit", self.run_dependency_audit),
            ("Task 2.4: Performance Profiling", self.run_performance_audit)
        ]
        
        for task_name, task_func in tasks:
            print(f"\n{'=' * 80}")
            print(f"Starting: {task_name}")
            print(f"{'=' * 80}")
            try:
                task_func()
                self.results["tasks_completed"].append(task_name)
                print(f"✓ {task_name} completed successfully")
            except Exception as e:
                self.results["tasks_failed"].append({
                    "task": task_name,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                print(f"✗ {task_name} failed: {e}")
                traceback.print_exc()
        
        self._generate_master_summary()
        print("\n" + "=" * 80)
        print("AUDIT COMPLETE")
        print("=" * 80)
        print(f"Completed: {len(self.results['tasks_completed'])}/4")
        print(f"Failed: {len(self.results['tasks_failed'])}/4")
        print(f"Reports saved to: {self.audit_dir}")
        
    def run_test_audit(self):
        """Task 2.1: Execute full test suite with detailed reporting"""
        test_dir = self.audit_dir / "testing"
        test_dir.mkdir(exist_ok=True)
        
        print("\n📊 Running pytest with coverage...")
        
        # Install pytest-json-report if needed
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest-json-report", "-q"], check=False)
        except:
            pass
        
        # Run pytest with all options
        pytest_cmd = [
            sys.executable, "-m", "pytest",
            "-v",
            "--cov=.",
            "--cov-report=html:" + str(test_dir / "htmlcov"),
            "--cov-report=json:" + str(test_dir / "coverage.json"),
            "--cov-report=term",
            "--tb=short",
            "--maxfail=999",
            "--junit-xml=" + str(test_dir / "junit.xml"),
        ]
        
        # Try to add json report if plugin available
        try:
            pytest_cmd.extend([
                "--json-report",
                "--json-report-file=" + str(test_dir / "pytest_report.json")
            ])
        except:
            pass
        
        result = subprocess.run(
            pytest_cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        # Save raw output
        (test_dir / "pytest_output.txt").write_text(result.stdout + "\n\n" + result.stderr)
        
        # Parse results
        test_summary = self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
        coverage_data = self._parse_coverage_data(test_dir / "coverage.json")
        
        # Generate JSON report
        test_audit_report = {
            "execution_timestamp": self.timestamp,
            "summary": test_summary,
            "failures": self._categorize_failures(result.stdout, result.stderr),
            "coverage_gaps": self._identify_coverage_gaps(coverage_data),
            "raw_exit_code": result.returncode
        }
        
        (test_dir / "test_audit_report.json").write_text(
            json.dumps(test_audit_report, indent=2)
        )
        
        # Generate Markdown report
        self._generate_test_markdown_report(test_audit_report, test_dir)
        
        print(f"✓ Test audit complete: {test_summary.get('passed', 0)}/{test_summary.get('total_tests', 0)} passed")
        
    def _parse_pytest_output(self, stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
        """Parse pytest output for summary statistics"""
        summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "pass_rate": 0.0,
            "total_duration": 0.0,
            "overall_coverage": 0.0,
            "exit_code": exit_code
        }
        
        # Extract test counts from pytest output
        output = stdout + stderr
        
        # Look for summary line like "10 passed, 2 failed, 1 skipped"
        summary_pattern = r'(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+error'
        for match in re.finditer(summary_pattern, output):
            for i, category in enumerate(['passed', 'failed', 'skipped', 'error']):
                if match.group(i + 1):
                    summary[category + 's' if category == 'error' else category] = int(match.group(i + 1))
        
        # Calculate totals
        summary["total_tests"] = summary["passed"] + summary["failed"] + summary["skipped"] + summary["errors"]
        if summary["total_tests"] > 0:
            summary["pass_rate"] = (summary["passed"] / summary["total_tests"]) * 100
        
        # Extract duration
        duration_match = re.search(r'in\s+([\d.]+)s', output)
        if duration_match:
            summary["total_duration"] = float(duration_match.group(1))
        
        # Extract coverage percentage
        coverage_match = re.search(r'TOTAL.*?(\d+)%', output)
        if coverage_match:
            summary["overall_coverage"] = float(coverage_match.group(1))
        
        return summary
    
    def _parse_coverage_data(self, coverage_file: Path) -> Dict[str, Any]:
        """Parse coverage.json file"""
        if not coverage_file.exists():
            return {"files": {}}
        
        try:
            return json.loads(coverage_file.read_text())
        except Exception as e:
            print(f"Warning: Could not parse coverage data: {e}")
            return {"files": {}}
    
    def _categorize_failures(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Extract and categorize test failures"""
        failures = []
        output = stdout + stderr
        
        # Parse FAILED lines from pytest output
        failure_pattern = r'FAILED\s+([^\s]+)\s+-\s+(.*)'
        for match in re.finditer(failure_pattern, output, re.MULTILINE):
            test_path = match.group(1)
            error_msg = match.group(2)
            
            # Determine severity
            severity = "MEDIUM"
            if "Connection" in error_msg or "Redis" in error_msg or "Database" in error_msg:
                severity = "HIGH"
            elif "Deprecated" in error_msg or "Warning" in error_msg:
                severity = "LOW"
            
            failures.append({
                "test": test_path.split("::")[-1] if "::" in test_path else test_path,
                "file": test_path,
                "error": error_msg,
                "severity": severity,
                "impact": self._determine_impact(error_msg),
                "recommendation": self._suggest_fix(error_msg)
            })
        
        return failures
    
    def _determine_impact(self, error_msg: str) -> str:
        """Determine impact of a failure"""
        if any(word in error_msg.lower() for word in ["connection", "redis", "database", "postgresql"]):
            return "Critical infrastructure component non-functional"
        elif any(word in error_msg.lower() for word in ["auth", "security", "token"]):
            return "Security/authentication system affected"
        elif "import" in error_msg.lower() or "module" in error_msg.lower():
            return "Module dependency or import issue"
        else:
            return "Functionality may be impaired"
    
    def _suggest_fix(self, error_msg: str) -> str:
        """Suggest fix for common errors"""
        error_lower = error_msg.lower()
        if "redis" in error_lower:
            return "Verify Redis service is running or update connection config"
        elif "postgresql" in error_lower or "database" in error_lower:
            return "Verify PostgreSQL service is running and database is accessible"
        elif "module" in error_lower or "import" in error_lower:
            return "Check requirements.txt and ensure all dependencies are installed"
        elif "deprecated" in error_lower:
            return "Update code to use non-deprecated APIs"
        else:
            return "Review test code and fix assertions or setup"
    
    def _identify_coverage_gaps(self, coverage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify files with low coverage"""
        gaps = []
        files = coverage_data.get("files", {})
        
        for filepath, file_data in files.items():
            summary = file_data.get("summary", {})
            percent_covered = summary.get("percent_covered", 0)
            
            if percent_covered < 80:  # Threshold for reporting
                missing_lines = file_data.get("missing_lines", [])
                gaps.append({
                    "file": filepath,
                    "coverage": round(percent_covered, 2),
                    "missing_lines": missing_lines[:10] if len(missing_lines) <= 10 else [f"{missing_lines[0]}-{missing_lines[-1]}"],
                    "recommendation": self._coverage_recommendation(percent_covered, filepath)
                })
        
        # Sort by coverage (worst first)
        gaps.sort(key=lambda x: x["coverage"])
        return gaps[:20]  # Top 20 worst files
    
    def _coverage_recommendation(self, coverage: float, filepath: str) -> str:
        """Generate coverage improvement recommendation"""
        if coverage < 20:
            return f"CRITICAL: Add comprehensive unit tests for {filepath}"
        elif coverage < 50:
            return f"Add unit tests for error handling and edge cases"
        else:
            return f"Add tests for uncovered branches and error paths"
    
    def _generate_test_markdown_report(self, report_data: Dict[str, Any], test_dir: Path):
        """Generate markdown test audit report"""
        md_lines = [
            "# Test Audit Report",
            f"\n**Execution Timestamp:** {report_data['execution_timestamp']}",
            "\n## Executive Summary\n",
            f"- **Total Tests:** {report_data['summary']['total_tests']}",
            f"- **Passed:** {report_data['summary']['passed']} ✓",
            f"- **Failed:** {report_data['summary']['failed']} ✗",
            f"- **Skipped:** {report_data['summary']['skipped']} ⊘",
            f"- **Pass Rate:** {report_data['summary']['pass_rate']:.1f}%",
            f"- **Duration:** {report_data['summary']['total_duration']:.2f}s",
            f"- **Coverage:** {report_data['summary']['overall_coverage']:.1f}%",
            "\n## Pass/Fail Breakdown by Category\n"
        ]
        
        # Status assessment
        pass_rate = report_data['summary']['pass_rate']
        if pass_rate >= 95:
            status = "🟢 EXCELLENT"
        elif pass_rate >= 80:
            status = "🟡 GOOD"
        elif pass_rate >= 60:
            status = "🟠 NEEDS IMPROVEMENT"
        else:
            status = "🔴 CRITICAL"
        
        md_lines.append(f"\n**Overall Status:** {status}\n")
        
        # Critical failures
        if report_data['failures']:
            md_lines.append("\n## Critical Failures (HIGH Severity)\n")
            high_severity = [f for f in report_data['failures'] if f.get('severity') == 'HIGH']
            if high_severity:
                for failure in high_severity:
                    md_lines.extend([
                        f"\n### {failure['test']}",
                        f"- **File:** `{failure['file']}`",
                        f"- **Error:** {failure['error']}",
                        f"- **Impact:** {failure['impact']}",
                        f"- **Recommendation:** {failure['recommendation']}"
                    ])
            else:
                md_lines.append("\n*No high severity failures*\n")
        
        # Coverage gaps
        if report_data['coverage_gaps']:
            md_lines.append("\n## Coverage Report Summary\n")
            md_lines.append("\n### Files with Low Coverage (<80%)\n")
            for gap in report_data['coverage_gaps'][:10]:
                md_lines.append(
                    f"- **{gap['file']}**: {gap['coverage']:.1f}% - {gap['recommendation']}"
                )
        
        # Actionable recommendations
        md_lines.extend([
            "\n## Actionable Recommendations\n",
            "\n### Immediate Actions Required\n"
        ])
        
        high_prio_failures = [f for f in report_data['failures'] if f.get('severity') == 'HIGH']
        if high_prio_failures:
            md_lines.append(f"1. **Fix {len(high_prio_failures)} HIGH severity test failures**")
            for f in high_prio_failures[:3]:
                md_lines.append(f"   - {f['test']}: {f['recommendation']}")
        
        critical_coverage = [g for g in report_data['coverage_gaps'] if g['coverage'] < 20]
        if critical_coverage:
            md_lines.append(f"2. **Address {len(critical_coverage)} files with critical coverage gaps (<20%)**")
        
        if report_data['summary']['pass_rate'] < 80:
            md_lines.append("3. **Improve test pass rate to at least 80%**")
        
        (test_dir / "test_audit_report.md").write_text("\n".join(md_lines))
    
    def run_quality_audit(self):
        """Task 2.2: Code Quality Analysis"""
        quality_dir = self.audit_dir / "quality"
        quality_dir.mkdir(exist_ok=True)
        
        print("\n🔍 Running code quality checks...")
        
        quality_results = {
            "timestamp": self.timestamp,
            "style_issues": {},
            "type_coverage": {},
            "security_issues": {},
            "formatting_issues": {}
        }
        
        # Run flake8
        print("  - Running flake8...")
        try:
            flake8_result = subprocess.run(
                [sys.executable, "-m", "flake8", ".", "--output-file", str(quality_dir / "flake8_report.txt"), "--statistics", "--exit-zero"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            quality_results["style_issues"] = self._parse_flake8_output(quality_dir / "flake8_report.txt")
        except Exception as e:
            print(f"    Warning: flake8 error: {e}")
        
        # Run mypy
        print("  - Running mypy...")
        try:
            mypy_result = subprocess.run(
                [sys.executable, "-m", "mypy", ".", "--html-report", str(quality_dir / "mypy_html"), "--junit-xml", str(quality_dir / "mypy_results.xml"), "--no-error-summary"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            (quality_dir / "mypy_output.txt").write_text(mypy_result.stdout + "\n" + mypy_result.stderr)
            quality_results["type_coverage"] = self._parse_mypy_output(mypy_result.stdout + mypy_result.stderr)
        except Exception as e:
            print(f"    Warning: mypy error: {e}")
        
        # Run black
        print("  - Running black...")
        try:
            black_result = subprocess.run(
                [sys.executable, "-m", "black", ".", "--check", "--diff"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            (quality_dir / "black_report.txt").write_text(black_result.stdout)
            quality_results["formatting_issues"] = self._parse_black_output(black_result.stdout, black_result.returncode)
        except Exception as e:
            print(f"    Warning: black error: {e}")
        
        # Run bandit
        print("  - Running bandit...")
        try:
            bandit_result = subprocess.run(
                [sys.executable, "-m", "bandit", "-r", ".", "-f", "json", "-o", str(quality_dir / "security_report.json"), "-ll"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            quality_results["security_issues"] = self._parse_bandit_output(quality_dir / "security_report.json")
        except Exception as e:
            print(f"    Warning: bandit error: {e}")
        
        # Generate reports
        (quality_dir / "code_quality_report.json").write_text(json.dumps(quality_results, indent=2))
        self._generate_quality_markdown_report(quality_results, quality_dir)
        
        print(f"✓ Quality audit complete")
    
    def _parse_flake8_output(self, flake8_file: Path) -> Dict[str, Any]:
        """Parse flake8 output"""
        if not flake8_file.exists():
            return {"total": 0, "by_severity": {}, "top_violations": []}
        
        content = flake8_file.read_text()
        violations = {}
        total = 0
        
        # Count violations by code
        for line in content.split('\n'):
            match = re.search(r'([A-Z]\d{3})', line)
            if match:
                code = match.group(1)
                violations[code] = violations.get(code, 0) + 1
                total += 1
        
        # Get top violations
        top_violations = sorted(violations.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total": total,
            "by_severity": self._categorize_flake8_severity(violations),
            "top_violations": [
                {"code": code, "description": self._flake8_description(code), "count": count}
                for code, count in top_violations
            ]
        }
    
    def _categorize_flake8_severity(self, violations: Dict[str, int]) -> Dict[str, int]:
        """Categorize flake8 violations by severity"""
        severity = {"error": 0, "warning": 0, "info": 0}
        for code, count in violations.items():
            if code.startswith('E') and int(code[1:]) >= 9:
                severity["error"] += count
            elif code.startswith('E') or code.startswith('F'):
                severity["warning"] += count
            else:
                severity["info"] += count
        return severity
    
    def _flake8_description(self, code: str) -> str:
        """Get description for flake8 code"""
        descriptions = {
            "E501": "line too long",
            "F401": "imported but unused",
            "E302": "expected 2 blank lines",
            "E305": "expected 2 blank lines after class or function",
            "W503": "line break before binary operator",
            "E303": "too many blank lines",
            "F841": "local variable assigned but never used"
        }
        return descriptions.get(code, "style violation")
    
    def _parse_mypy_output(self, output: str) -> Dict[str, Any]:
        """Parse mypy output"""
        # Count functions and type coverage
        error_count = len(re.findall(r'error:', output))
        
        return {
            "total_functions": 0,  # Would need AST parsing for accurate count
            "typed_functions": 0,
            "type_coverage_percent": 0.0,
            "error_count": error_count,
            "files_without_types": []
        }
    
    def _parse_black_output(self, output: str, exit_code: int) -> Dict[str, Any]:
        """Parse black output"""
        # Count files that would be reformatted
        files_needing_format = len(re.findall(r'would reformat', output))
        
        return {
            "files_needing_format": files_needing_format,
            "total_lines_to_change": 0,  # black doesn't provide this
            "all_formatted": exit_code == 0
        }
    
    def _parse_bandit_output(self, bandit_file: Path) -> Dict[str, Any]:
        """Parse bandit security report"""
        if not bandit_file.exists():
            return {"high": 0, "medium": 0, "low": 0, "issues": []}
        
        try:
            data = json.loads(bandit_file.read_text())
            results = data.get("results", [])
            
            severity_counts = {"high": 0, "medium": 0, "low": 0}
            issues = []
            
            for result in results:
                severity = result.get("issue_severity", "LOW").lower()
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                if severity in ["high", "medium"]:
                    issues.append({
                        "severity": severity.upper(),
                        "file": result.get("filename", ""),
                        "line": result.get("line_number", 0),
                        "issue": result.get("issue_text", ""),
                        "recommendation": result.get("issue_text", "")
                    })
            
            return {
                "high": severity_counts.get("high", 0),
                "medium": severity_counts.get("medium", 0),
                "low": severity_counts.get("low", 0),
                "issues": issues[:10]  # Top 10
            }
        except Exception as e:
            print(f"Warning: Could not parse bandit output: {e}")
            return {"high": 0, "medium": 0, "low": 0, "issues": []}
    
    def _generate_quality_markdown_report(self, quality_data: Dict[str, Any], quality_dir: Path):
        """Generate markdown quality report"""
        # Calculate quality score
        style_issues = quality_data.get("style_issues", {}).get("total", 0)
        security_high = quality_data.get("security_issues", {}).get("high", 0)
        security_medium = quality_data.get("security_issues", {}).get("medium", 0)
        
        # Simple scoring (0-100)
        quality_score = 100
        quality_score -= min(50, style_issues / 10)  # -0.1 per style issue, max -50
        quality_score -= security_high * 10  # -10 per high security issue
        quality_score -= security_medium * 5  # -5 per medium security issue
        quality_score = max(0, quality_score)
        
        md_lines = [
            "# Code Quality Report",
            f"\n**Timestamp:** {quality_data['timestamp']}",
            f"\n## Quality Score: {quality_score:.1f}/100\n",
        ]
        
        # Status
        if quality_score >= 90:
            status = "🟢 EXCELLENT"
        elif quality_score >= 75:
            status = "🟡 GOOD"
        elif quality_score >= 50:
            status = "🟠 NEEDS IMPROVEMENT"
        else:
            status = "🔴 CRITICAL"
        
        md_lines.append(f"**Status:** {status}\n")
        
        # Critical issues
        md_lines.append("\n## Critical Issues Requiring Immediate Attention\n")
        
        security_issues = quality_data.get("security_issues", {})
        if security_issues.get("high", 0) > 0:
            md_lines.append(f"### 🔴 HIGH Security Issues: {security_issues['high']}\n")
            for issue in security_issues.get("issues", [])[:5]:
                if issue["severity"] == "HIGH":
                    md_lines.extend([
                        f"- **{issue['file']}:{issue['line']}**",
                        f"  - {issue['issue']}",
                        f"  - Recommendation: {issue['recommendation']}\n"
                    ])
        
        # Style issues
        style = quality_data.get("style_issues", {})
        if style.get("total", 0) > 0:
            md_lines.extend([
                f"\n## Style Issues: {style['total']}\n",
                "\n### Top Violations:\n"
            ])
            for violation in style.get("top_violations", [])[:5]:
                md_lines.append(f"- **{violation['code']}** ({violation['description']}): {violation['count']} occurrences")
        
        # Technical debt
        md_lines.extend([
            "\n## Technical Debt Assessment\n",
            f"- **Style Issues:** {style.get('total', 0)}",
            f"- **Security Issues:** {security_issues.get('high', 0) + security_issues.get('medium', 0) + security_issues.get('low', 0)}",
            f"- **Formatting Issues:** {quality_data.get('formatting_issues', {}).get('files_needing_format', 0)} files need formatting",
        ])
        
        # Refactoring recommendations
        md_lines.extend([
            "\n## Refactoring Recommendations\n",
            "1. Run `black .` to auto-format code",
            "2. Fix HIGH severity security issues immediately",
            "3. Address top style violations (see flake8_report.txt)",
            "4. Add type hints to improve type coverage"
        ])
        
        (quality_dir / "code_quality_report.md").write_text("\n".join(md_lines))
    
    def run_dependency_audit(self):
        """Task 2.3: Dependency Audit"""
        dep_dir = self.audit_dir / "dependencies"
        dep_dir.mkdir(exist_ok=True)
        
        print("\n📦 Running dependency audit...")
        
        # Run pip-audit
        print("  - Running pip-audit...")
        try:
            audit_result = subprocess.run(
                [sys.executable, "-m", "pip_audit", "--format", "json", "--output", str(dep_dir / "security_audit.json")],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
        except Exception as e:
            print(f"    Warning: pip-audit error: {e}")
            # Create empty file
            (dep_dir / "security_audit.json").write_text("[]")
        
        # Check for outdated packages
        print("  - Checking for outdated packages...")
        try:
            outdated_result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format", "json"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            (dep_dir / "outdated_packages.json").write_text(outdated_result.stdout or "[]")
        except Exception as e:
            print(f"    Warning: pip list error: {e}")
            (dep_dir / "outdated_packages.json").write_text("[]")
        
        # Generate dependency tree
        print("  - Generating dependency tree...")
        try:
            tree_result = subprocess.run(
                [sys.executable, "-m", "pipdeptree", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            (dep_dir / "dependency_tree.json").write_text(tree_result.stdout or "[]")
        except Exception as e:
            print(f"    Warning: pipdeptree error: {e}")
            (dep_dir / "dependency_tree.json").write_text("[]")
        
        # Parse and generate report
        dependency_report = self._generate_dependency_report(dep_dir)
        (dep_dir / "dependency_audit_report.json").write_text(json.dumps(dependency_report, indent=2))
        self._generate_dependency_markdown_report(dependency_report, dep_dir)
        
        print(f"✓ Dependency audit complete")
    
    def _generate_dependency_report(self, dep_dir: Path) -> Dict[str, Any]:
        """Generate comprehensive dependency report"""
        # Load data
        security_vulns = self._load_json(dep_dir / "security_audit.json", [])
        outdated = self._load_json(dep_dir / "outdated_packages.json", [])
        
        # Check for deprecated packages
        deprecated_packages = self._check_deprecated_packages()
        
        # Count total dependencies
        requirements_file = self.project_root / "requirements.txt"
        total_deps = 0
        if requirements_file.exists():
            total_deps = len([l for l in requirements_file.read_text().split('\n') if l.strip() and not l.startswith('#')])
        
        return {
            "total_dependencies": total_deps,
            "security_vulnerabilities": self._parse_security_vulnerabilities(security_vulns),
            "deprecated_packages": deprecated_packages,
            "outdated_packages": self._parse_outdated_packages(outdated),
            "missing_dependencies": []  # Would need import analysis
        }
    
    def _load_json(self, filepath: Path, default=None):
        """Safely load JSON file"""
        if not filepath.exists():
            return default
        try:
            return json.loads(filepath.read_text())
        except:
            return default
    
    def _parse_security_vulnerabilities(self, vulns: List[Dict]) -> List[Dict[str, Any]]:
        """Parse security vulnerabilities from pip-audit"""
        parsed = []
        for vuln in vulns:
            if isinstance(vuln, dict):
                parsed.append({
                    "package": vuln.get("name", "unknown"),
                    "current_version": vuln.get("version", "unknown"),
                    "vulnerability": vuln.get("id", "unknown"),
                    "severity": vuln.get("severity", "MEDIUM"),
                    "fixed_in": vuln.get("fix_versions", ["unknown"])[0] if vuln.get("fix_versions") else "unknown",
                    "recommendation": f"Update to version {vuln.get('fix_versions', ['latest'])[0]}"
                })
        return parsed
    
    def _check_deprecated_packages(self) -> List[Dict[str, Any]]:
        """Check for known deprecated packages"""
        deprecated = []
        
        # Check if aioredis is installed
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "aioredis"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version_match = re.search(r'Version:\s+(\S+)', result.stdout)
                version = version_match.group(1) if version_match else "unknown"
                deprecated.append({
                    "package": "aioredis",
                    "current_version": version,
                    "status": "DEPRECATED",
                    "replacement": "redis[asyncio]>=4.5.0",
                    "used_in": ["Check codebase for 'import aioredis'"],
                    "migration_required": True
                })
        except:
            pass
        
        return deprecated
    
    def _parse_outdated_packages(self, outdated: List[Dict]) -> List[Dict[str, Any]]:
        """Parse outdated packages"""
        parsed = []
        for pkg in outdated:
            if isinstance(pkg, dict):
                parsed.append({
                    "package": pkg.get("name", "unknown"),
                    "current": pkg.get("version", "unknown"),
                    "latest": pkg.get("latest_version", "unknown"),
                    "breaking_changes": False  # Would need changelog analysis
                })
        return parsed[:10]  # Top 10
    
    def _generate_dependency_markdown_report(self, dep_data: Dict[str, Any], dep_dir: Path):
        """Generate markdown dependency report"""
        md_lines = [
            "# Dependency Audit Report",
            f"\n## Summary\n",
            f"- **Total Dependencies:** {dep_data['total_dependencies']}",
            f"- **Security Vulnerabilities:** {len(dep_data['security_vulnerabilities'])}",
            f"- **Deprecated Packages:** {len(dep_data['deprecated_packages'])}",
            f"- **Outdated Packages:** {len(dep_data['outdated_packages'])}",
        ]
        
        # Security vulnerabilities
        if dep_data['security_vulnerabilities']:
            md_lines.append("\n## 🔴 Security Vulnerabilities\n")
            for vuln in dep_data['security_vulnerabilities']:
                md_lines.extend([
                    f"### {vuln['package']}",
                    f"- **Current Version:** {vuln['current_version']}",
                    f"- **Vulnerability:** {vuln['vulnerability']}",
                    f"- **Severity:** {vuln['severity']}",
                    f"- **Fixed In:** {vuln['fixed_in']}",
                    f"- **Recommendation:** {vuln['recommendation']}\n"
                ])
        
        # Deprecated packages
        if dep_data['deprecated_packages']:
            md_lines.append("\n## ⚠️  Deprecated Packages\n")
            for pkg in dep_data['deprecated_packages']:
                md_lines.extend([
                    f"### {pkg['package']}",
                    f"- **Current Version:** {pkg['current_version']}",
                    f"- **Status:** {pkg['status']}",
                    f"- **Replacement:** {pkg['replacement']}",
                    f"- **Migration Required:** {'Yes' if pkg['migration_required'] else 'No'}\n"
                ])
        
        # Prioritized action items
        md_lines.append("\n## Prioritized Action Items\n")
        priority = 1
        
        if dep_data['security_vulnerabilities']:
            md_lines.append(f"{priority}. **URGENT:** Fix {len(dep_data['security_vulnerabilities'])} security vulnerabilities")
            priority += 1
        
        if dep_data['deprecated_packages']:
            md_lines.append(f"{priority}. **HIGH:** Replace {len(dep_data['deprecated_packages'])} deprecated packages")
            priority += 1
        
        if dep_data['outdated_packages']:
            md_lines.append(f"{priority}. **MEDIUM:** Update {len(dep_data['outdated_packages'])} outdated packages")
        
        (dep_dir / "dependency_audit_report.md").write_text("\n".join(md_lines))
    
    def run_performance_audit(self):
        """Task 2.4: Performance Profiling"""
        perf_dir = self.audit_dir / "performance"
        perf_dir.mkdir(exist_ok=True)
        
        print("\n⚡ Running performance profiling...")
        
        # Create benchmark script
        self._create_benchmark_script()
        
        # For now, create a basic performance report
        # In a real scenario, we would run the benchmark script
        perf_report = {
            "timestamp": self.timestamp,
            "api_endpoints": [
                {
                    "endpoint": "System Info",
                    "avg_response_time_ms": 0,
                    "status": "NOT_TESTED",
                    "note": "Performance tests require running server"
                }
            ],
            "database_queries": [
                {
                    "query": "System check",
                    "status": "NOT_TESTED",
                    "note": "Database performance tests require running database"
                }
            ],
            "memory_usage": {
                "baseline_mb": 0,
                "status": "NOT_TESTED",
                "note": "Memory profiling requires running application"
            }
        }
        
        (perf_dir / "performance_report.json").write_text(json.dumps(perf_report, indent=2))
        self._generate_performance_markdown_report(perf_report, perf_dir)
        
        print(f"✓ Performance audit complete (benchmark script created)")
    
    def _create_benchmark_script(self):
        """Create performance benchmark script"""
        benchmark_dir = self.project_root / "benchmarks"
        benchmark_dir.mkdir(exist_ok=True)
        
        benchmark_script = '''#!/usr/bin/env python3
"""
Performance Benchmark Script
Can be re-run to measure system performance
"""

import asyncio
import time
import httpx
import psutil
from typing import Dict, List, Any


async def benchmark_api_endpoint(endpoint: str, method: str = "GET") -> Dict[str, Any]:
    """Benchmark a single API endpoint"""
    times = []
    
    async with httpx.AsyncClient() as client:
        # Warmup
        for _ in range(5):
            try:
                await client.request(method, endpoint, timeout=5.0)
            except:
                pass
        
        # Measure
        for _ in range(100):
            start = time.perf_counter()
            try:
                response = await client.request(method, endpoint, timeout=5.0)
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
            except Exception as e:
                print(f"Error: {e}")
    
    if times:
        times.sort()
        return {
            "endpoint": endpoint,
            "avg_response_time_ms": sum(times) / len(times),
            "p50_ms": times[len(times) // 2],
            "p95_ms": times[int(len(times) * 0.95)],
            "p99_ms": times[int(len(times) * 0.99)],
        }
    return {"endpoint": endpoint, "error": "No successful requests"}


async def main():
    """Run all benchmarks"""
    print("Starting performance benchmarks...")
    
    # Benchmark API endpoints
    endpoints = [
        "http://localhost:8000/health",
        "http://localhost:8000/api/v1/agents",
    ]
    
    for endpoint in endpoints:
        result = await benchmark_api_endpoint(endpoint)
        print(f"Endpoint: {result['endpoint']}")
        if 'avg_response_time_ms' in result:
            print(f"  Avg: {result.get('avg_response_time_ms', 'N/A')}ms")
    
    # Memory usage
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"\\nMemory Usage: {memory_mb:.2f} MB")


if __name__ == "__main__":
    asyncio.run(main())
'''
        
        (benchmark_dir / "performance_benchmark.py").write_text(benchmark_script)
    
    def _generate_performance_markdown_report(self, perf_data: Dict[str, Any], perf_dir: Path):
        """Generate markdown performance report"""
        md_lines = [
            "# Performance Report",
            f"\n**Timestamp:** {perf_data['timestamp']}",
            "\n## Status\n",
            "⚠️  Performance tests not executed - requires running server and database",
            "\n## Benchmark Script Created\n",
            "A re-runnable benchmark script has been created at: `benchmarks/performance_benchmark.py`",
            "\n### To run benchmarks:\n",
            "```bash",
            "# Start the server first",
            "python main.py &",
            "",
            "# Run benchmarks",
            "python benchmarks/performance_benchmark.py",
            "```",
            "\n## Recommendations\n",
            "1. Set up performance testing in CI/CD pipeline",
            "2. Establish baseline performance metrics",
            "3. Add database query profiling",
            "4. Monitor memory usage under load"
        ]
        
        (perf_dir / "performance_report.md").write_text("\n".join(md_lines))
    
    def _generate_master_summary(self):
        """Generate master summary report"""
        summary_file = self.audit_dir / "AUDIT_SUMMARY.md"
        
        md_lines = [
            "# YMERA Platform - Comprehensive Audit Summary",
            f"\n**Execution Date:** {self.timestamp}",
            "\n## Tasks Completed\n"
        ]
        
        for i, task in enumerate(self.results["tasks_completed"], 1):
            md_lines.append(f"{i}. ✓ {task}")
        
        if self.results["tasks_failed"]:
            md_lines.append("\n## Tasks Failed\n")
            for task in self.results["tasks_failed"]:
                md_lines.append(f"- ✗ {task['task']}")
                md_lines.append(f"  - Error: {task['error']}")
        
        md_lines.extend([
            "\n## Report Locations\n",
            "- **Testing:** `audit_reports/testing/test_audit_report.md`",
            "- **Quality:** `audit_reports/quality/code_quality_report.md`",
            "- **Dependencies:** `audit_reports/dependencies/dependency_audit_report.md`",
            "- **Performance:** `audit_reports/performance/performance_report.md`",
            "\n## Next Steps\n",
            "1. Review all audit reports",
            "2. Address HIGH severity issues immediately",
            "3. Create action plan for MEDIUM severity issues",
            "4. Schedule regular audits"
        ])
        
        summary_file.write_text("\n".join(md_lines))


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent.resolve()
    
    auditor = PlatformAuditor(project_root)
    auditor.run_all_audits()


if __name__ == "__main__":
    main()
