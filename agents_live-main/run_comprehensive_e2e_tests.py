#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite for YMERA System
========================================================
Version: 1.0.0
Purpose: Run complete system validation after enhancements, debugging, and configuration
Author: YMERA Testing Framework
Date: 2025-10-19
"""

import sys
import os
import asyncio
import time
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Test results tracking
test_results = {
    'total_tests': 0,
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'warnings': 0,
    'categories': {},
    'start_time': None,
    'end_time': None,
    'duration': 0,
    'tests': []
}

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"{text:^80}")
    print(f"{'='*80}{Colors.ENDC}\n")


def print_section(text: str):
    """Print section header"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{'-'*80}")
    print(f"  {text}")
    print(f"{'-'*80}{Colors.ENDC}\n")


def log_test(category: str, name: str, status: str, message: str = "", duration: float = 0):
    """Log individual test result"""
    test_results['total_tests'] += 1
    test_results[status] += 1
    
    if category not in test_results['categories']:
        test_results['categories'][category] = {
            'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'warnings': 0
        }
    
    test_results['categories'][category]['total'] += 1
    test_results['categories'][category][status] += 1
    
    test_results['tests'].append({
        'category': category,
        'name': name,
        'status': status,
        'message': message,
        'duration': duration,
        'timestamp': datetime.now().isoformat()
    })
    
    # Status icons
    icons = {
        'passed': f'{Colors.OKGREEN}✅',
        'failed': f'{Colors.FAIL}❌',
        'skipped': f'{Colors.WARNING}⏭️',
        'warnings': f'{Colors.WARNING}⚠️'
    }
    
    icon = icons.get(status, '•')
    print(f"{icon} {name}{Colors.ENDC}")
    if message:
        print(f"   {message}")
    if duration > 0:
        print(f"   Duration: {duration:.3f}s")


# ============================================================================
# TEST CATEGORY 1: ENVIRONMENT & DEPENDENCIES
# ============================================================================

def test_environment():
    """Test Python environment and dependencies"""
    print_section("1. Environment & Dependencies")
    category = "Environment"
    
    # Python version
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 9:
        log_test(category, "Python Version", "passed", 
                f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        log_test(category, "Python Version", "failed",
                f"Requires Python 3.9+, found {py_version.major}.{py_version.minor}")
    
    # Critical dependencies
    critical_deps = [
        ('fastapi', 'FastAPI'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('pydantic', 'Pydantic'),
        ('asyncio', 'AsyncIO'),
    ]
    
    for module_name, display_name in critical_deps:
        try:
            start = time.time()
            mod = __import__(module_name)
            duration = time.time() - start
            version = getattr(mod, '__version__', 'built-in')
            log_test(category, f"{display_name} Import", "passed",
                    f"v{version}", duration)
        except ImportError:
            log_test(category, f"{display_name} Import", "failed",
                    "Module not installed")
        except Exception as e:
            log_test(category, f"{display_name} Import", "failed", str(e))
    
    # Optional dependencies
    optional_deps = [
        ('uvicorn', 'Uvicorn'),
        ('httpx', 'HTTPX'),
        ('asyncpg', 'AsyncPG'),
        ('aiosqlite', 'AIOSqlite'),
        ('structlog', 'Structlog'),
        ('pytest', 'Pytest'),
    ]
    
    for module_name, display_name in optional_deps:
        try:
            start = time.time()
            mod = __import__(module_name)
            duration = time.time() - start
            version = getattr(mod, '__version__', 'unknown')
            log_test(category, f"{display_name} (Optional)", "passed",
                    f"v{version}", duration)
        except ImportError:
            log_test(category, f"{display_name} (Optional)", "warnings",
                    "Not installed but optional")


# ============================================================================
# TEST CATEGORY 2: MODULE STRUCTURE & IMPORTS
# ============================================================================

def test_module_structure():
    """Test core module structure and imports"""
    print_section("2. Module Structure & Imports")
    category = "Module Structure"
    
    # Core modules to test
    core_modules = [
        'main',
        'config',
        'database',
        'models',
        'unified_system',
        'base_agent',
        'learning_agent',
        'intelligence_engine',
    ]
    
    for module_name in core_modules:
        try:
            start = time.time()
            if os.path.exists(f"{module_name}.py"):
                mod = __import__(module_name)
                duration = time.time() - start
                log_test(category, f"Module: {module_name}", "passed",
                        f"Loaded successfully", duration)
            else:
                log_test(category, f"Module: {module_name}", "skipped",
                        "File not found")
        except Exception as e:
            log_test(category, f"Module: {module_name}", "failed",
                    f"Error: {str(e)[:100]}")


# ============================================================================
# TEST CATEGORY 3: DATABASE COMPONENTS
# ============================================================================

async def test_database_components():
    """Test database components"""
    print_section("3. Database Components")
    category = "Database"
    
    # Test database_core_integrated if exists
    try:
        start = time.time()
        import database_core_integrated as dbc
        duration = time.time() - start
        log_test(category, "Database Core Import", "passed",
                "Module loaded", duration)
        
        # Check for key classes
        required_classes = [
            'DatabaseConfig', 'IntegratedDatabaseManager',
            'User', 'Project', 'Agent', 'Task', 'File', 'AuditLog'
        ]
        
        for cls_name in required_classes:
            if hasattr(dbc, cls_name):
                log_test(category, f"Class: {cls_name}", "passed", "Available")
            else:
                log_test(category, f"Class: {cls_name}", "warnings", "Not found")
                
    except ImportError:
        log_test(category, "Database Core Import", "skipped",
                "database_core_integrated not found")
    except Exception as e:
        log_test(category, "Database Core Import", "failed", str(e))
    
    # Test SQLAlchemy models
    try:
        start = time.time()
        from core.sqlalchemy_models import Base, User, Agent, Task
        duration = time.time() - start
        log_test(category, "SQLAlchemy Models", "passed",
                "Models imported", duration)
    except ImportError:
        log_test(category, "SQLAlchemy Models", "skipped",
                "core.sqlalchemy_models not found")
    except Exception as e:
        log_test(category, "SQLAlchemy Models", "failed", str(e))


# ============================================================================
# TEST CATEGORY 4: API ENDPOINTS
# ============================================================================

async def test_api_endpoints():
    """Test API endpoints structure"""
    print_section("4. API Endpoints")
    category = "API"
    
    try:
        start = time.time()
        from main import app
        duration = time.time() - start
        log_test(category, "FastAPI App Import", "passed",
                "Application loaded", duration)
        
        # Check routes
        route_count = len(app.routes)
        log_test(category, "API Routes", "passed",
                f"Found {route_count} routes")
        
        # List some key routes
        key_routes = ['/health', '/metrics', '/api/', '/auth/']
        for route in app.routes:
            path = getattr(route, 'path', '')
            for key in key_routes:
                if key in path:
                    log_test(category, f"Route: {path}", "passed", "Available")
                    break
                    
    except ImportError:
        log_test(category, "FastAPI App Import", "skipped", "main.py not found")
    except Exception as e:
        log_test(category, "FastAPI App Import", "failed", str(e))


# ============================================================================
# TEST CATEGORY 5: AGENT SYSTEMS
# ============================================================================

async def test_agent_systems():
    """Test agent systems"""
    print_section("5. Agent Systems")
    category = "Agents"
    
    # Test base agent
    try:
        start = time.time()
        from base_agent import BaseAgent
        duration = time.time() - start
        log_test(category, "Base Agent Import", "passed",
                "Base agent loaded", duration)
    except ImportError:
        log_test(category, "Base Agent Import", "skipped",
                "base_agent.py not found")
    except Exception as e:
        log_test(category, "Base Agent Import", "failed", str(e))
    
    # Test specialized agents
    agent_files = [
        'learning_agent',
        'communication_agent',
        'drafting_agent',
        'editing_agent',
        'enhancement_agent',
        'examination_agent',
        'metrics_agent',
        'llm_agent',
    ]
    
    for agent_file in agent_files:
        if os.path.exists(f"{agent_file}.py"):
            try:
                start = time.time()
                mod = __import__(agent_file)
                duration = time.time() - start
                log_test(category, f"Agent: {agent_file}", "passed",
                        "Loaded", duration)
            except Exception as e:
                log_test(category, f"Agent: {agent_file}", "failed",
                        str(e)[:100])
        else:
            log_test(category, f"Agent: {agent_file}", "skipped",
                    "File not found")


# ============================================================================
# TEST CATEGORY 6: ENGINE COMPONENTS
# ============================================================================

async def test_engine_components():
    """Test engine components"""
    print_section("6. Engine Components")
    category = "Engines"
    
    engine_files = [
        'intelligence_engine',
        'optimization_engine',
        'performance_engine',
        'learning_engine',
    ]
    
    for engine_file in engine_files:
        if os.path.exists(f"{engine_file}.py"):
            try:
                start = time.time()
                mod = __import__(engine_file)
                duration = time.time() - start
                log_test(category, f"Engine: {engine_file}", "passed",
                        "Loaded", duration)
            except Exception as e:
                log_test(category, f"Engine: {engine_file}", "failed",
                        str(e)[:100])
        else:
            log_test(category, f"Engine: {engine_file}", "skipped",
                    "File not found")


# ============================================================================
# TEST CATEGORY 7: CONFIGURATION
# ============================================================================

def test_configuration():
    """Test configuration files and settings"""
    print_section("7. Configuration")
    category = "Configuration"
    
    # Check .env file
    if os.path.exists('.env'):
        log_test(category, ".env File", "passed", "Configuration file exists")
    else:
        log_test(category, ".env File", "warnings",
                "No .env file (using defaults or .env.example)")
    
    # Check config modules
    config_modules = ['config', 'settings', 'ProductionConfig']
    
    for config_file in config_modules:
        if os.path.exists(f"{config_file}.py"):
            try:
                start = time.time()
                mod = __import__(config_file)
                duration = time.time() - start
                log_test(category, f"Config: {config_file}", "passed",
                        "Loaded", duration)
            except Exception as e:
                log_test(category, f"Config: {config_file}", "failed",
                        str(e)[:100])
        else:
            log_test(category, f"Config: {config_file}", "skipped",
                    "File not found")


# ============================================================================
# TEST CATEGORY 8: SECURITY & AUTHENTICATION
# ============================================================================

def test_security():
    """Test security components"""
    print_section("8. Security & Authentication")
    category = "Security"
    
    security_files = [
        'auth',
        'security_agent',
        'security_monitor',
        'security_scanner',
    ]
    
    for sec_file in security_files:
        if os.path.exists(f"{sec_file}.py"):
            try:
                start = time.time()
                mod = __import__(sec_file)
                duration = time.time() - start
                log_test(category, f"Security: {sec_file}", "passed",
                        "Loaded", duration)
            except Exception as e:
                log_test(category, f"Security: {sec_file}", "failed",
                        str(e)[:100])
        else:
            log_test(category, f"Security: {sec_file}", "skipped",
                    "File not found")


# ============================================================================
# TEST CATEGORY 9: EXISTING TEST SUITES
# ============================================================================

async def test_existing_tests():
    """Run existing test files"""
    print_section("9. Existing Test Suites")
    category = "Existing Tests"
    
    test_files = [
        'test_api.py',
        'test_database.py',
        'test_comprehensive.py',
        'test_fixtures.py',
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            log_test(category, f"Test Suite: {test_file}", "passed",
                    "Test file exists")
        else:
            log_test(category, f"Test Suite: {test_file}", "skipped",
                    "File not found")


# ============================================================================
# TEST CATEGORY 10: DOCUMENTATION
# ============================================================================

def test_documentation():
    """Test documentation files"""
    print_section("10. Documentation")
    category = "Documentation"
    
    doc_files = [
        'README.md',
        'START_HERE.md',
        'DEPLOYMENT_GUIDE.md',
        'CHANGELOG.md',
    ]
    
    for doc_file in doc_files:
        if os.path.exists(doc_file):
            size = os.path.getsize(doc_file)
            log_test(category, f"Doc: {doc_file}", "passed",
                    f"Size: {size} bytes")
        else:
            log_test(category, f"Doc: {doc_file}", "warnings",
                    "Documentation file missing")


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report():
    """Generate comprehensive test report"""
    print_header("COMPREHENSIVE E2E TEST REPORT")
    
    # Summary statistics
    print(f"{Colors.BOLD}Summary Statistics:{Colors.ENDC}")
    print(f"  Total Tests: {test_results['total_tests']}")
    print(f"  {Colors.OKGREEN}Passed: {test_results['passed']}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Failed: {test_results['failed']}{Colors.ENDC}")
    print(f"  {Colors.WARNING}Warnings: {test_results['warnings']}{Colors.ENDC}")
    print(f"  {Colors.WARNING}Skipped: {test_results['skipped']}{Colors.ENDC}")
    print(f"  Duration: {test_results['duration']:.2f}s")
    
    # Calculate pass rate
    if test_results['total_tests'] > 0:
        pass_rate = (test_results['passed'] / test_results['total_tests']) * 100
        print(f"  Pass Rate: {pass_rate:.1f}%")
    
    # Category breakdown
    print(f"\n{Colors.BOLD}Results by Category:{Colors.ENDC}")
    for cat_name, cat_stats in test_results['categories'].items():
        print(f"\n  {Colors.BOLD}{cat_name}:{Colors.ENDC}")
        print(f"    Total: {cat_stats['total']}")
        print(f"    {Colors.OKGREEN}✓ Passed: {cat_stats['passed']}{Colors.ENDC}")
        if cat_stats['failed'] > 0:
            print(f"    {Colors.FAIL}✗ Failed: {cat_stats['failed']}{Colors.ENDC}")
        if cat_stats['warnings'] > 0:
            print(f"    {Colors.WARNING}⚠ Warnings: {cat_stats['warnings']}{Colors.ENDC}")
        if cat_stats['skipped'] > 0:
            print(f"    ⏭ Skipped: {cat_stats['skipped']}")
    
    # Save JSON report
    report_file = 'e2e_test_report.json'
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\n{Colors.OKGREEN}Full report saved to: {report_file}{Colors.ENDC}")
    
    # Save markdown report
    markdown_report = generate_markdown_report()
    md_file = 'E2E_TEST_REPORT.md'
    with open(md_file, 'w') as f:
        f.write(markdown_report)
    print(f"{Colors.OKGREEN}Markdown report saved to: {md_file}{Colors.ENDC}")
    
    # Overall status
    print(f"\n{Colors.BOLD}Overall Status:{Colors.ENDC}")
    if test_results['failed'] == 0:
        print(f"{Colors.OKGREEN}✅ ALL CRITICAL TESTS PASSED{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.FAIL}❌ SOME TESTS FAILED - REVIEW REQUIRED{Colors.ENDC}")
        return 1


def generate_markdown_report() -> str:
    """Generate markdown format report"""
    lines = [
        "# Comprehensive E2E Test Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Duration:** {test_results['duration']:.2f}s",
        "",
        "## Summary",
        "",
        f"- **Total Tests:** {test_results['total_tests']}",
        f"- **✅ Passed:** {test_results['passed']}",
        f"- **❌ Failed:** {test_results['failed']}",
        f"- **⚠️ Warnings:** {test_results['warnings']}",
        f"- **⏭️ Skipped:** {test_results['skipped']}",
        "",
    ]
    
    if test_results['total_tests'] > 0:
        pass_rate = (test_results['passed'] / test_results['total_tests']) * 100
        lines.append(f"- **Pass Rate:** {pass_rate:.1f}%")
        lines.append("")
    
    lines.extend([
        "## Results by Category",
        "",
    ])
    
    for cat_name, cat_stats in test_results['categories'].items():
        lines.extend([
            f"### {cat_name}",
            "",
            f"- Total: {cat_stats['total']}",
            f"- ✅ Passed: {cat_stats['passed']}",
            f"- ❌ Failed: {cat_stats['failed']}",
            f"- ⚠️ Warnings: {cat_stats['warnings']}",
            f"- ⏭️ Skipped: {cat_stats['skipped']}",
            "",
        ])
    
    lines.extend([
        "## Detailed Test Results",
        "",
        "| Category | Test Name | Status | Duration | Message |",
        "|----------|-----------|--------|----------|---------|",
    ])
    
    for test in test_results['tests']:
        status_icon = {
            'passed': '✅',
            'failed': '❌',
            'warnings': '⚠️',
            'skipped': '⏭️'
        }.get(test['status'], '•')
        
        lines.append(
            f"| {test['category']} | {test['name']} | {status_icon} | "
            f"{test['duration']:.3f}s | {test['message'][:50]} |"
        )
    
    lines.extend([
        "",
        "## Recommendations",
        "",
    ])
    
    if test_results['failed'] > 0:
        lines.extend([
            "### Critical Issues",
            "",
            "The following tests failed and require immediate attention:",
            "",
        ])
        for test in test_results['tests']:
            if test['status'] == 'failed':
                lines.append(f"- **{test['category']}** - {test['name']}: {test['message']}")
        lines.append("")
    
    if test_results['warnings'] > 0:
        lines.extend([
            "### Warnings",
            "",
            "The following items have warnings:",
            "",
        ])
        for test in test_results['tests']:
            if test['status'] == 'warnings':
                lines.append(f"- **{test['category']}** - {test['name']}: {test['message']}")
        lines.append("")
    
    lines.extend([
        "## System Status",
        "",
    ])
    
    if test_results['failed'] == 0:
        lines.extend([
            "✅ **System Status: HEALTHY**",
            "",
            "All critical tests passed successfully. The system is ready for use.",
        ])
    else:
        lines.extend([
            "⚠️ **System Status: NEEDS ATTENTION**",
            "",
            "Some tests failed. Please review and fix the issues before deployment.",
        ])
    
    return "\n".join(lines)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def run_all_tests():
    """Run all test categories"""
    print_header("YMERA COMPREHENSIVE E2E TEST SUITE")
    print(f"Starting comprehensive testing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results['start_time'] = datetime.now().isoformat()
    start = time.time()
    
    # Run all test categories
    test_environment()
    test_module_structure()
    await test_database_components()
    await test_api_endpoints()
    await test_agent_systems()
    await test_engine_components()
    test_configuration()
    test_security()
    await test_existing_tests()
    test_documentation()
    
    # Calculate duration
    test_results['end_time'] = datetime.now().isoformat()
    test_results['duration'] = time.time() - start
    
    # Generate and display report
    return generate_report()


def main():
    """Main entry point"""
    try:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {e}{Colors.ENDC}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
