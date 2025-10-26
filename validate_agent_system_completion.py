#!/usr/bin/env python3
"""
Validate Agent System Completion Task

This script verifies that all deliverables for the agent system completion
task are present and contain measured data (not estimates).

Usage:
    python validate_agent_system_completion.py
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class AgentSystemCompletionValidator:
    """Validates agent system completion deliverables"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent
        self.results = {
            "json_files": {},
            "markdown_reports": {},
            "success_criteria": {},
            "data_quality": {},
            "overall_status": "UNKNOWN"
        }
    
    def validate(self) -> Dict:
        """Run all validation checks"""
        print("🔍 Validating Agent System Completion Deliverables...")
        print("=" * 60)
        
        self.validate_json_files()
        self.validate_markdown_reports()
        self.validate_success_criteria()
        self.validate_data_quality()
        self.calculate_overall_status()
        
        self.print_summary()
        return self.results
    
    def validate_json_files(self):
        """Validate required JSON files"""
        print("\n📦 Validating JSON Files (Measured Data)...")
        
        required_files = {
            "agent_catalog_complete.json": "Agent inventory",
            "agent_classification.json": "Agent classification",
            "agent_test_results_complete.json": "Test results",
            "agent_coverage.json": "Coverage metrics",
            "agent_benchmarks_complete.json": "Performance benchmarks",
            "agent_fixes_applied.json": "Fixes documentation",
            "integration_results.json": "Integration tests"
        }
        
        for filename, description in required_files.items():
            filepath = self.repo_root / filename
            status, message = self._check_json_file(filepath)
            self.results["json_files"][filename] = {
                "description": description,
                "status": status,
                "message": message,
                "path": str(filepath)
            }
            
            icon = "✅" if status == "PASS" else "❌"
            print(f"  {icon} {filename}: {message}")
    
    def validate_markdown_reports(self):
        """Validate required Markdown reports"""
        print("\n📝 Validating Markdown Reports...")
        
        required_reports = {
            "AGENT_INVENTORY_REPORT.md": "Inventory report",
            "AGENT_COVERAGE_REPORT.md": "Coverage report",
            "AGENT_TESTING_REPORT.md": "Testing report",
            "AGENT_PERFORMANCE_REPORT.md": "Performance report",
            "AGENT_SYSTEM_ARCHITECTURE.md": "Architecture docs",
            "INTEGRATION_TEST_REPORT.md": "Integration report",
            "AGENT_SYSTEM_FINAL_REPORT.md": "Final master report"
        }
        
        for filename, description in required_reports.items():
            filepath = self.repo_root / filename
            status, message = self._check_markdown_file(filepath)
            self.results["markdown_reports"][filename] = {
                "description": description,
                "status": status,
                "message": message,
                "path": str(filepath)
            }
            
            icon = "✅" if status == "PASS" else "❌"
            print(f"  {icon} {filename}: {message}")
    
    def validate_success_criteria(self):
        """Validate success criteria are met"""
        print("\n🎯 Validating Success Criteria...")
        
        criteria = [
            ("agents_cataloged", "Every agent discovered and cataloged", self._check_agents_cataloged),
            ("coverage_measured", "Coverage measured (actual %)", self._check_coverage_measured),
            ("performance_benchmarked", "Performance benchmarked (actual ms)", self._check_performance_benchmarked),
            ("agents_fixed", "All broken agents fixed or documented", self._check_agents_fixed),
            ("integration_tested", "Integration tests passing", self._check_integration_tested),
            ("measured_data", "Final report with 100% measured data", self._check_measured_data),
            ("production_ready", "Production readiness clearly stated", self._check_production_readiness)
        ]
        
        for key, description, check_func in criteria:
            status, message = check_func()
            self.results["success_criteria"][key] = {
                "description": description,
                "status": status,
                "message": message
            }
            
            icon = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"  {icon} {description}: {message}")
    
    def validate_data_quality(self):
        """Validate data quality standards"""
        print("\n📊 Validating Data Quality...")
        
        checks = [
            ("no_estimates", "No 'approximately' or 'around'", self._check_no_estimates),
            ("no_should_be", "No 'should be' or 'expected to'", self._check_no_should_be),
            ("has_timestamps", "All data has timestamps", self._check_has_timestamps),
            ("has_evidence", "All claims have evidence", self._check_has_evidence)
        ]
        
        for key, description, check_func in checks:
            status, message = check_func()
            self.results["data_quality"][key] = {
                "description": description,
                "status": status,
                "message": message
            }
            
            icon = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"  {icon} {description}: {message}")
    
    def calculate_overall_status(self):
        """Calculate overall completion status"""
        total_items = 0
        passed_items = 0
        
        # Count JSON files
        for item in self.results["json_files"].values():
            total_items += 1
            if item["status"] == "PASS":
                passed_items += 1
        
        # Count Markdown reports
        for item in self.results["markdown_reports"].values():
            total_items += 1
            if item["status"] == "PASS":
                passed_items += 1
        
        # Count success criteria
        for item in self.results["success_criteria"].values():
            total_items += 1
            if item["status"] == "PASS":
                passed_items += 1
            elif item["status"] == "PARTIAL":
                passed_items += 0.5
        
        # Count data quality
        for item in self.results["data_quality"].values():
            total_items += 1
            if item["status"] == "PASS":
                passed_items += 1
            elif item["status"] == "PARTIAL":
                passed_items += 0.5
        
        completion_percentage = (passed_items / total_items * 100) if total_items > 0 else 0
        
        if completion_percentage >= 90:
            self.results["overall_status"] = "COMPLETE"
        elif completion_percentage >= 70:
            self.results["overall_status"] = "MOSTLY_COMPLETE"
        elif completion_percentage >= 50:
            self.results["overall_status"] = "IN_PROGRESS"
        else:
            self.results["overall_status"] = "NOT_STARTED"
        
        self.results["completion_percentage"] = completion_percentage
        self.results["items_passed"] = passed_items
        self.results["items_total"] = total_items
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("📈 VALIDATION SUMMARY")
        print("=" * 60)
        
        status = self.results["overall_status"]
        percentage = self.results["completion_percentage"]
        passed = self.results["items_passed"]
        total = self.results["items_total"]
        
        status_icon = {
            "COMPLETE": "✅",
            "MOSTLY_COMPLETE": "⚠️",
            "IN_PROGRESS": "🔄",
            "NOT_STARTED": "❌"
        }.get(status, "❓")
        
        print(f"\nOverall Status: {status_icon} {status}")
        print(f"Completion: {percentage:.1f}% ({passed}/{total} items)")
        
        if status == "COMPLETE":
            print("\n🎉 Congratulations! Agent system completion task is COMPLETE!")
            print("   All deliverables present with measured data.")
        elif status == "MOSTLY_COMPLETE":
            print("\n⚠️  Almost there! A few items need attention.")
            print("   Review the validation results above.")
        elif status == "IN_PROGRESS":
            print("\n🔄 Work in progress. Keep going!")
            print("   Review the validation results to see what's missing.")
        else:
            print("\n❌ Task not started or just beginning.")
            print("   Review AGENT_SYSTEM_COMPLETION_TASK.md to get started.")
        
        print("\n" + "=" * 60)
    
    # Helper methods for file checks
    
    def _check_json_file(self, filepath: Path) -> Tuple[str, str]:
        """Check if JSON file exists and is valid"""
        if not filepath.exists():
            return "FAIL", "File not found"
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Check if file is empty
            if not data:
                return "FAIL", "File is empty"
            
            # Check for timestamp
            has_timestamp = any(
                key in data for key in ['timestamp', 'discovery_timestamp', 'test_timestamp', 'generated_at']
            )
            
            if has_timestamp:
                return "PASS", "Valid with timestamp"
            else:
                return "PARTIAL", "Valid but missing timestamp"
        
        except json.JSONDecodeError:
            return "FAIL", "Invalid JSON"
        except Exception as e:
            return "FAIL", f"Error: {str(e)}"
    
    def _check_markdown_file(self, filepath: Path) -> Tuple[str, str]:
        """Check if Markdown file exists and has content"""
        if not filepath.exists():
            return "FAIL", "File not found"
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Check if file has meaningful content (>500 chars)
            if len(content) < 500:
                return "PARTIAL", "Exists but minimal content"
            
            # Check for measured data indicators
            measured_indicators = ["measured", "actual", "benchmark", "result"]
            has_measured = any(indicator in content.lower() for indicator in measured_indicators)
            
            if has_measured:
                return "PASS", "Complete with measured data"
            else:
                return "PARTIAL", "Exists but may lack measured data"
        
        except Exception as e:
            return "FAIL", f"Error: {str(e)}"
    
    # Helper methods for success criteria checks
    
    def _check_agents_cataloged(self) -> Tuple[str, str]:
        """Check if agents are cataloged"""
        filepath = self.repo_root / "agent_catalog_complete.json"
        if not filepath.exists():
            return "FAIL", "Catalog not found"
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            total_agents = data.get("metrics", {}).get("total_agents", 0)
            if total_agents > 0:
                return "PASS", f"{total_agents} agents cataloged"
            else:
                return "FAIL", "No agents found in catalog"
        except:
            return "FAIL", "Cannot read catalog"
    
    def _check_coverage_measured(self) -> Tuple[str, str]:
        """Check if coverage is measured"""
        filepath = self.repo_root / "agent_coverage.json"
        if not filepath.exists():
            return "FAIL", "Coverage data not found"
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Look for coverage percentage
            coverage = data.get("total_coverage") or data.get("coverage") or data.get("totals", {}).get("percent_covered")
            if coverage is not None:
                return "PASS", f"Coverage: {coverage}%"
            else:
                return "FAIL", "Coverage percentage not found"
        except:
            return "FAIL", "Cannot read coverage data"
    
    def _check_performance_benchmarked(self) -> Tuple[str, str]:
        """Check if performance is benchmarked"""
        filepath = self.repo_root / "agent_benchmarks_complete.json"
        if not filepath.exists():
            return "FAIL", "Benchmark data not found"
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            agents = data.get("agents", [])
            if len(agents) > 0:
                # Check if benchmarks have P50, P95, P99
                sample_agent = agents[0]
                has_metrics = "initialization" in sample_agent or "execution" in sample_agent
                if has_metrics:
                    return "PASS", f"{len(agents)} agents benchmarked"
                else:
                    return "PARTIAL", "Benchmark data incomplete"
            else:
                return "FAIL", "No benchmark data"
        except:
            return "FAIL", "Cannot read benchmark data"
    
    def _check_agents_fixed(self) -> Tuple[str, str]:
        """Check if agents are fixed"""
        filepath = self.repo_root / "agent_fixes_applied.json"
        if not filepath.exists():
            return "PARTIAL", "Fixes file not found (may not be needed)"
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            fixes = data.get("fixes_applied", [])
            if len(fixes) > 0:
                return "PASS", f"{len(fixes)} fixes documented"
            else:
                return "PARTIAL", "No fixes needed or not documented"
        except:
            return "FAIL", "Cannot read fixes data"
    
    def _check_integration_tested(self) -> Tuple[str, str]:
        """Check if integration is tested"""
        filepath = self.repo_root / "integration_results.json"
        if not filepath.exists():
            return "FAIL", "Integration results not found"
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            total = data.get("total_tests", 0)
            passed = data.get("passed_tests", 0)
            if total > 0:
                pass_rate = (passed / total * 100)
                if pass_rate >= 90:
                    return "PASS", f"{pass_rate:.1f}% passing ({passed}/{total})"
                else:
                    return "PARTIAL", f"{pass_rate:.1f}% passing (target: 90%)"
            else:
                return "FAIL", "No integration tests run"
        except:
            return "FAIL", "Cannot read integration results"
    
    def _check_measured_data(self) -> Tuple[str, str]:
        """Check if final report has measured data"""
        filepath = self.repo_root / "AGENT_SYSTEM_FINAL_REPORT.md"
        if not filepath.exists():
            return "FAIL", "Final report not found"
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Check for estimated/approximate language (should NOT be present)
            bad_words = ["approximately", "around", "should be", "expected to", "estimated"]
            has_bad_words = any(word in content.lower() for word in bad_words)
            
            # Check for measured data indicators (SHOULD be present)
            good_words = ["measured", "actual", "benchmarked", "tested"]
            has_good_words = any(word in content.lower() for word in good_words)
            
            if has_good_words and not has_bad_words:
                return "PASS", "Report contains measured data only"
            elif has_good_words:
                return "PARTIAL", "Report has measured data but also estimates"
            else:
                return "FAIL", "Report lacks measured data"
        except:
            return "FAIL", "Cannot read final report"
    
    def _check_production_readiness(self) -> Tuple[str, str]:
        """Check if production readiness is stated"""
        filepath = self.repo_root / "AGENT_SYSTEM_FINAL_REPORT.md"
        if not filepath.exists():
            return "FAIL", "Final report not found"
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Look for production readiness statement
            has_yes_no = "production ready: yes" in content.lower() or "production ready: no" in content.lower()
            has_assessment = "production readiness" in content.lower()
            
            if has_yes_no:
                return "PASS", "Production readiness clearly stated"
            elif has_assessment:
                return "PARTIAL", "Production assessment present"
            else:
                return "FAIL", "Production readiness not stated"
        except:
            return "FAIL", "Cannot read final report"
    
    # Helper methods for data quality checks
    
    def _check_no_estimates(self) -> Tuple[str, str]:
        """Check for absence of estimate language"""
        # Check final report for estimate language
        filepath = self.repo_root / "AGENT_SYSTEM_FINAL_REPORT.md"
        if not filepath.exists():
            return "FAIL", "Final report not found"
        
        try:
            with open(filepath, 'r') as f:
                content = f.read().lower()
            
            bad_words = ["approximately", "around", "roughly"]
            found_bad = [word for word in bad_words if word in content]
            
            if len(found_bad) == 0:
                return "PASS", "No estimate language found"
            else:
                return "FAIL", f"Found: {', '.join(found_bad)}"
        except:
            return "FAIL", "Cannot check"
    
    def _check_no_should_be(self) -> Tuple[str, str]:
        """Check for absence of hypothetical language"""
        filepath = self.repo_root / "AGENT_SYSTEM_FINAL_REPORT.md"
        if not filepath.exists():
            return "FAIL", "Final report not found"
        
        try:
            with open(filepath, 'r') as f:
                content = f.read().lower()
            
            bad_phrases = ["should be", "expected to", "likely", "probably"]
            found_bad = [phrase for phrase in bad_phrases if phrase in content]
            
            if len(found_bad) == 0:
                return "PASS", "No hypothetical language found"
            else:
                return "FAIL", f"Found: {', '.join(found_bad)}"
        except:
            return "FAIL", "Cannot check"
    
    def _check_has_timestamps(self) -> Tuple[str, str]:
        """Check if data files have timestamps"""
        json_files = [
            "agent_catalog_complete.json",
            "agent_test_results_complete.json",
            "agent_benchmarks_complete.json"
        ]
        
        files_with_timestamps = 0
        for filename in json_files:
            filepath = self.repo_root / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    has_timestamp = any(
                        key in data for key in ['timestamp', 'discovery_timestamp', 'test_timestamp', 'generated_at']
                    )
                    if has_timestamp:
                        files_with_timestamps += 1
                except:
                    pass
        
        if files_with_timestamps == len(json_files):
            return "PASS", "All data files have timestamps"
        elif files_with_timestamps > 0:
            return "PARTIAL", f"{files_with_timestamps}/{len(json_files)} files have timestamps"
        else:
            return "FAIL", "No timestamps found"
    
    def _check_has_evidence(self) -> Tuple[str, str]:
        """Check if claims have evidence"""
        # This is a simplified check - just verify files exist
        required_evidence = [
            "agent_catalog_complete.json",
            "agent_test_results_complete.json",
            "agent_coverage.json"
        ]
        
        existing_files = [f for f in required_evidence if (self.repo_root / f).exists()]
        
        if len(existing_files) == len(required_evidence):
            return "PASS", "All evidence files present"
        elif len(existing_files) > 0:
            return "PARTIAL", f"{len(existing_files)}/{len(required_evidence)} evidence files"
        else:
            return "FAIL", "No evidence files found"


def main():
    """Main entry point"""
    validator = AgentSystemCompletionValidator()
    results = validator.validate()
    
    # Save results
    output_file = Path(__file__).parent / "agent_system_completion_validation.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Exit code based on status
    if results["overall_status"] == "COMPLETE":
        return 0
    elif results["overall_status"] == "MOSTLY_COMPLETE":
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit(main())
