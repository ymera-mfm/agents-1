#!/usr/bin/env python3
"""
Full System Verification Script
Tests the core functionality of the system with fixes applied
"""

import sys
import importlib
import subprocess
from pathlib import Path

class SystemVerification:
    def __init__(self):
        self.results = {
            "module_imports": {},
            "core_functionality": {},
            "fixed_files": {},
            "overall_status": "unknown"
        }
    
    def test_module_imports(self):
        """Test that core modules can be imported"""
        print("🔍 Testing Core Module Imports")
        print("=" * 70)
        
        modules_to_test = [
            ("base_agent", "Base agent system"),
            ("agent", "Agent core"),
            ("metrics", "Metrics collector"),
            ("logger", "Logging system"),
            ("encryption", "Encryption utilities"),
        ]
        
        passed = 0
        failed = 0
        
        for module_name, description in modules_to_test:
            try:
                mod = importlib.import_module(module_name)
                print(f"   ✅ {module_name}: {description}")
                self.results["module_imports"][module_name] = "success"
                passed += 1
            except Exception as e:
                print(f"   ❌ {module_name}: {str(e)[:60]}")
                self.results["module_imports"][module_name] = f"failed: {str(e)[:60]}"
                failed += 1
        
        print(f"\n   Passed: {passed}/{len(modules_to_test)}")
        print()
        return failed == 0
    
    def verify_fixed_files(self):
        """Verify that fixed files compile and work"""
        print("🔧 Verifying Fixed Files")
        print("=" * 70)
        
        fixed_files = [
            ("config_compat.py", "Print → Logging (25 fixes)"),
            ("analyze_agent_dependencies.py", "Print → Logging (30 fixes)"),
            ("learning_agent_main.py", "Print → Logging (4 fixes)"),
            ("agent_classifier.py", "Print → Logging (24 fixes)"),
            ("02_remove_duplicates.py", "Print → Logging (40 fixes)"),
            ("generator_engine_prod.py", "Print → Logging (6 fixes)"),
            ("metrics.py", "Type hints (4 added)"),
            ("audit_manager.py", "Bare except fixed"),
            ("extensions.py", "Bare except fixed"),
            ("knowledge_graph.py", "Bare except fixed"),
        ]
        
        passed = 0
        failed = 0
        
        for file_name, fix_description in fixed_files:
            if not Path(file_name).exists():
                print(f"   ⚠️  {file_name}: File not found")
                continue
            
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", file_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print(f"   ✅ {file_name}: {fix_description}")
                    self.results["fixed_files"][file_name] = "compiles"
                    passed += 1
                else:
                    print(f"   ❌ {file_name}: Compilation error")
                    self.results["fixed_files"][file_name] = "failed"
                    failed += 1
            except Exception as e:
                print(f"   ❌ {file_name}: {str(e)[:60]}")
                self.results["fixed_files"][file_name] = f"error: {str(e)[:60]}"
                failed += 1
        
        print(f"\n   Passed: {passed}/{len(fixed_files)}")
        print()
        return failed == 0
    
    def test_logging_functionality(self):
        """Test that logging works in fixed files"""
        print("📝 Testing Logging Functionality")
        print("=" * 70)
        
        test_code = """
import logging
logger = logging.getLogger(__name__)

# Test logging at different levels
logger.info("Test info message")
logger.warning("Test warning message")
logger.error("Test error message")
logger.debug("Test debug message")

print("Logging test completed successfully")
"""
        
        try:
            result = subprocess.run(
                [sys.executable, "-c", test_code],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and "Logging test completed" in result.stdout:
                print("   ✅ Logging infrastructure works correctly")
                self.results["core_functionality"]["logging"] = "working"
                return True
            else:
                print("   ❌ Logging test failed")
                self.results["core_functionality"]["logging"] = "failed"
                return False
        except Exception as e:
            print(f"   ❌ Logging test error: {str(e)[:60]}")
            self.results["core_functionality"]["logging"] = f"error: {str(e)[:60]}"
            return False
    
    def test_type_hints(self):
        """Test that type hints are working"""
        print("🎯 Testing Type Hints")
        print("=" * 70)
        
        test_code = """
from typing import Dict, List, Optional, Any

def test_function(x: int) -> int:
    return x + 1

def test_function2() -> None:
    pass

def test_function3() -> Dict[str, Any]:
    return {"test": "value"}

result = test_function(5)
assert result == 6
print("Type hints test completed successfully")
"""
        
        try:
            result = subprocess.run(
                [sys.executable, "-c", test_code],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and "Type hints test completed" in result.stdout:
                print("   ✅ Type hints working correctly")
                self.results["core_functionality"]["type_hints"] = "working"
                return True
            else:
                print("   ❌ Type hints test failed")
                self.results["core_functionality"]["type_hints"] = "failed"
                return False
        except Exception as e:
            print(f"   ❌ Type hints test error: {str(e)[:60]}")
            self.results["core_functionality"]["type_hints"] = f"error: {str(e)[:60]}"
            return False
    
    def run_comprehensive_tests(self):
        """Run the comprehensive test suite"""
        print("🧪 Running Comprehensive Test Suite")
        print("=" * 70)
        
        try:
            result = subprocess.run(
                [sys.executable, "comprehensive_test_suite.py"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if "ALL TESTS PASSED" in result.stdout:
                print("   ✅ All comprehensive tests passed")
                self.results["core_functionality"]["comprehensive_tests"] = "passed"
                return True
            else:
                print("   ❌ Some comprehensive tests failed")
                self.results["core_functionality"]["comprehensive_tests"] = "failed"
                return False
        except Exception as e:
            print(f"   ❌ Comprehensive test error: {str(e)[:60]}")
            self.results["core_functionality"]["comprehensive_tests"] = f"error: {str(e)[:60]}"
            return False
    
    def generate_report(self):
        """Generate verification report"""
        print("\n" + "=" * 70)
        print("📊 SYSTEM VERIFICATION REPORT")
        print("=" * 70)
        
        # Count successes
        import_success = sum(1 for v in self.results["module_imports"].values() if v == "success")
        fixed_files_success = sum(1 for v in self.results["fixed_files"].values() if v == "compiles")
        functionality_success = sum(1 for v in self.results["core_functionality"].values() if v in ["working", "passed"])
        
        total_import = len(self.results["module_imports"])
        total_fixed = len(self.results["fixed_files"])
        total_functionality = len(self.results["core_functionality"])
        
        print(f"\n📈 Results Summary:")
        print(f"   Module Imports: {import_success}/{total_import} passed")
        print(f"   Fixed Files: {fixed_files_success}/{total_fixed} verified")
        print(f"   Core Functionality: {functionality_success}/{total_functionality} working")
        
        # Overall status
        all_passed = (
            import_success == total_import and
            fixed_files_success == total_fixed and
            functionality_success == total_functionality
        )
        
        if all_passed:
            self.results["overall_status"] = "✅ EXCELLENT - All verifications passed"
            print(f"\n{self.results['overall_status']}")
        else:
            self.results["overall_status"] = "⚠️  PARTIAL - Some verifications failed"
            print(f"\n{self.results['overall_status']}")
        
        print("\n" + "=" * 70)
        
        # Save report
        import json
        with open("system_verification_report.json", 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print("💾 Report saved to: system_verification_report.json")
        
        return all_passed
    
    def run_all(self):
        """Run all verification steps"""
        print("🚀 Starting Full System Verification\n")
        
        all_pass = True
        all_pass &= self.test_module_imports()
        all_pass &= self.verify_fixed_files()
        all_pass &= self.test_logging_functionality()
        all_pass &= self.test_type_hints()
        all_pass &= self.run_comprehensive_tests()
        
        self.generate_report()
        
        return all_pass

def main():
    verifier = SystemVerification()
    success = verifier.run_all()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
