#!/usr/bin/env python3
"""
Simple integration test for repository_status.py

This test validates the repository status checker without requiring pytest or other
external dependencies. It can be run standalone.

Date: October 25, 2025
"""

import sys
import json
import subprocess
from pathlib import Path


def test_repository_status_script():
    """Test that repository_status.py runs successfully."""
    print("Testing repository_status.py...")
    
    # Run the script
    result = subprocess.run(
        [sys.executable, "repository_status.py"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    
    # Check exit code
    assert result.returncode == 0, f"Script failed with exit code {result.returncode}"
    print("✓ Script executed successfully")
    
    # Check output contains expected strings
    assert "REPOSITORY STATUS REPORT" in result.stdout, "Missing report header"
    assert "Overall Status:" in result.stdout, "Missing status line"
    assert "PASS" in result.stdout, "Expected PASS status"
    print("✓ Output format correct")
    
    # Check JSON file was created
    json_path = Path.cwd() / "repository_status_report.json"
    assert json_path.exists(), "JSON report not created"
    print("✓ JSON report created")
    
    # Validate JSON content
    with open(json_path) as f:
        data = json.load(f)
    
    assert "status" in data, "Missing status field"
    assert "checks" in data, "Missing checks field"
    assert data["status"] in ["PASS", "WARN", "FAIL"], f"Invalid status: {data['status']}"
    print(f"✓ JSON valid with status: {data['status']}")
    
    # Validate checks
    expected_checks = ["python_version", "git_repository", "essential_files", 
                      "directory_structure", "python_files"]
    for check in expected_checks:
        assert check in data["checks"], f"Missing check: {check}"
    print(f"✓ All {len(expected_checks)} checks present")
    
    return True


def test_repository_readiness_doc():
    """Test that REPOSITORY_READINESS.md exists and has content."""
    print("\nTesting REPOSITORY_READINESS.md...")
    
    readme_path = Path.cwd() / "REPOSITORY_READINESS.md"
    assert readme_path.exists(), "REPOSITORY_READINESS.md not found"
    print("✓ File exists")
    
    content = readme_path.read_text()
    assert len(content) > 1000, f"Content too short: {len(content)} bytes"
    assert "Repository Readiness Status" in content, "Missing title"
    assert "October 25, 2025" in content, "Missing date"
    assert "READY" in content, "Missing ready status"
    print("✓ Content validated")
    
    return True


def main():
    """Run all tests."""
    print("="*70)
    print("INTEGRATION TEST SUITE")
    print("="*70)
    print()
    
    tests = [
        test_repository_status_script,
        test_repository_readiness_doc
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__} PASSED\n")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_func.__name__} FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} ERROR: {e}\n")
    
    print("="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
