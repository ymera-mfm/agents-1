#!/usr/bin/env python3
"""
YMERA System - Deployment Verification Script
Verifies that the system is ready for deployment
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_status(check, status, message=""):
    """Print check status"""
    icon = "✅" if status else "❌"
    print(f"{icon} {check}")
    if message:
        print(f"   → {message}")


def check_dependencies():
    """Check if all dependencies are installed"""
    print_header("Checking Dependencies")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'sqlalchemy',
        'asyncpg',
        'redis',
        'pytest',
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print_status(package, True)
        except ImportError:
            print_status(package, False, "Not installed")
            all_ok = False
    
    return all_ok


def check_structure():
    """Check project structure"""
    print_header("Checking Project Structure")
    
    required_paths = [
        'core/__init__.py',
        'core/config.py',
        'core/auth.py',
        'core/database.py',
        'middleware/__init__.py',
        'main.py',
        'requirements.txt',
        '.env',
    ]
    
    all_ok = True
    for path_str in required_paths:
        path = Path(path_str)
        exists = path.exists()
        print_status(path_str, exists)
        if not exists:
            all_ok = False
    
    return all_ok


def check_imports():
    """Check critical imports"""
    print_header("Checking Critical Imports")
    
    all_ok = True
    
    # Check main app
    try:
        from main import app
        print_status("main.app", True, f"App: {app.title}")
    except Exception as e:
        print_status("main.app", False, str(e))
        all_ok = False
    
    # Check core modules
    try:
        from core.config import Settings
        print_status("core.config.Settings", True)
    except Exception as e:
        print_status("core.config.Settings", False, str(e))
        all_ok = False
    
    try:
        from core.auth import AuthService
        print_status("core.auth.AuthService", True)
    except Exception as e:
        print_status("core.auth.AuthService", False, str(e))
        all_ok = False
    
    return all_ok


def run_tests():
    """Run test suite"""
    print_header("Running Test Suite")
    
    try:
        result = subprocess.run(
            ['pytest', 'test_e2e_standalone.py', '-q', '--tb=no'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        success = result.returncode == 0
        output_lines = result.stdout.split('\n')
        summary = [line for line in output_lines if 'passed' in line.lower() or 'failed' in line.lower()]
        
        if summary:
            print_status("Test Suite", success, summary[-1])
        else:
            print_status("Test Suite", success)
        
        return success
    except Exception as e:
        print_status("Test Suite", False, str(e))
        return False


def main():
    """Run all verification checks"""
    print_header("YMERA System - Deployment Verification")
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Project Structure", check_structure),
        ("Critical Imports", check_imports),
        ("Test Suite", run_tests),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    # Final summary
    print_header("Verification Summary")
    
    all_passed = all(results.values())
    
    for name, passed in results.items():
        print_status(name, passed)
    
    print()
    if all_passed:
        print("🎉 " + "="*54 + " 🎉")
        print("   ✅ ALL CHECKS PASSED - SYSTEM READY FOR DEPLOYMENT!")
        print("🎉 " + "="*54 + " 🎉")
        print()
        print("Next steps:")
        print("  1. Update .env with production values")
        print("  2. Configure production database")
        print("  3. Run: uvicorn main:app --host 0.0.0.0 --port 8000")
        print()
        return 0
    else:
        print("❌ " + "="*54 + " ❌")
        print("   ⚠️  SOME CHECKS FAILED - REVIEW ISSUES ABOVE")
        print("❌ " + "="*54 + " ❌")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
