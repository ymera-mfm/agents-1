#!/usr/bin/env python3
"""
YMERA System Validation Script
Validates the system setup and readiness for deployment
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str) -> None:
    """Print section header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_check(name: str, passed: bool, message: str = "") -> None:
    """Print check result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if message:
        print(f"        {message}")


def check_file_exists(file_path: str) -> bool:
    """Check if file exists"""
    return Path(file_path).exists()


def check_directory_structure() -> List[Tuple[str, bool, str]]:
    """Validate directory structure"""
    checks = []
    
    # Core files
    core_files = [
        ('base_agent.py', 'Base agent implementation'),
        ('config.py', 'Configuration management'),
        ('database.py', 'Database setup'),
        ('logger.py', 'Logging configuration'),
        ('main.py', 'Application entry point'),
        ('requirements.txt', 'Python dependencies'),
        ('requirements-minimal.txt', 'Minimal dependencies'),
    ]
    
    for file, desc in core_files:
        exists = check_file_exists(file)
        checks.append((f"{desc} ({file})", exists, ""))
    
    # Agent files
    agent_files = [
        ('agent_communication.py', 'Communication agent'),
        ('agent_monitoring.py', 'Monitoring agent'),
    ]
    
    for file, desc in agent_files:
        exists = check_file_exists(file)
        checks.append((f"{desc} ({file})", exists, ""))
    
    # Configuration files
    config_files = [
        ('.env.example', 'Environment template'),
        ('docker-compose.yml', 'Docker Compose config'),
        ('Dockerfile', 'Docker image definition'),
        ('pytest.ini', 'Pytest configuration'),
        ('prometheus.yml', 'Prometheus config'),
    ]
    
    for file, desc in config_files:
        exists = check_file_exists(file)
        checks.append((f"{desc} ({file})", exists, ""))
    
    # Scripts
    script_files = [
        ('start_system.sh', 'Linux/Mac startup script'),
        ('start_system.bat', 'Windows startup script'),
    ]
    
    for file, desc in script_files:
        exists = check_file_exists(file)
        checks.append((f"{desc} ({file})", exists, ""))
    
    # Directories
    directories = [
        ('tests/', 'Test directory'),
        ('docs/', 'Documentation directory'),
        ('.github/', 'GitHub configuration'),
    ]
    
    for dir_path, desc in directories:
        exists = Path(dir_path).is_dir()
        checks.append((f"{desc} ({dir_path})", exists, ""))
    
    return checks


def check_test_files() -> List[Tuple[str, bool, str]]:
    """Validate test files"""
    checks = []
    
    test_files = [
        ('tests/conftest.py', 'Test configuration'),
        ('tests/test_base_agent.py', 'Base agent tests'),
        ('tests/test_integration.py', 'Integration tests'),
    ]
    
    for file, desc in test_files:
        exists = check_file_exists(file)
        checks.append((f"{desc} ({file})", exists, ""))
    
    return checks


def check_documentation() -> List[Tuple[str, bool, str]]:
    """Validate documentation"""
    checks = []
    
    docs = [
        ('README.md', 'Main README'),
        ('docs/ARCHITECTURE.md', 'Architecture documentation'),
        ('docs/DEPLOYMENT.md', 'Deployment guide'),
        ('.github/copilot-instructions.md', 'Copilot instructions'),
    ]
    
    for file, desc in docs:
        exists = check_file_exists(file)
        checks.append((f"{desc} ({file})", exists, ""))
    
    return checks


def check_python_syntax() -> List[Tuple[str, bool, str]]:
    """Check Python files for syntax errors"""
    checks = []
    
    python_files = [
        'base_agent.py',
        'config.py',
        'database.py',
        'logger.py',
        'main.py',
        'agent_communication.py',
        'agent_monitoring.py',
    ]
    
    for file in python_files:
        if check_file_exists(file):
            try:
                with open(file, 'r') as f:
                    compile(f.read(), file, 'exec')
                checks.append((f"Syntax validation: {file}", True, ""))
            except SyntaxError as e:
                checks.append((f"Syntax validation: {file}", False, f"Line {e.lineno}: {e.msg}"))
        else:
            checks.append((f"Syntax validation: {file}", False, "File not found"))
    
    return checks


def check_imports() -> List[Tuple[str, bool, str]]:
    """Check if key modules can be imported"""
    checks = []
    
    # Add current directory to path
    sys.path.insert(0, os.getcwd())
    
    modules = [
        ('config', 'Configuration module'),
        ('logger', 'Logger module'),
        ('base_agent', 'Base agent module'),
    ]
    
    for module, desc in modules:
        try:
            __import__(module)
            checks.append((f"Import {desc}", True, ""))
        except ImportError as e:
            checks.append((f"Import {desc}", False, str(e)))
        except Exception as e:
            checks.append((f"Import {desc}", False, f"Error: {str(e)}"))
    
    return checks


def check_git_status() -> List[Tuple[str, bool, str]]:
    """Check git repository status"""
    checks = []
    
    # Check if .git exists
    git_exists = Path('.git').is_dir()
    checks.append(("Git repository initialized", git_exists, ""))
    
    # Check .gitignore
    gitignore_exists = check_file_exists('.gitignore')
    checks.append(("Git ignore file", gitignore_exists, ""))
    
    return checks


def main():
    """Run all validation checks"""
    print_header("YMERA System Validation")
    print(f"{YELLOW}Validating system setup and readiness for deployment...{RESET}\n")
    
    total_checks = 0
    passed_checks = 0
    
    # Directory structure
    print_header("Directory Structure & Files")
    for name, passed, msg in check_directory_structure():
        print_check(name, passed, msg)
        total_checks += 1
        if passed:
            passed_checks += 1
    
    # Test files
    print_header("Test Infrastructure")
    for name, passed, msg in check_test_files():
        print_check(name, passed, msg)
        total_checks += 1
        if passed:
            passed_checks += 1
    
    # Documentation
    print_header("Documentation")
    for name, passed, msg in check_documentation():
        print_check(name, passed, msg)
        total_checks += 1
        if passed:
            passed_checks += 1
    
    # Python syntax
    print_header("Python Syntax Validation")
    for name, passed, msg in check_python_syntax():
        print_check(name, passed, msg)
        total_checks += 1
        if passed:
            passed_checks += 1
    
    # Module imports (only if dependencies installed)
    if check_file_exists('venv'):
        print_header("Module Import Validation")
        for name, passed, msg in check_imports():
            print_check(name, passed, msg)
            total_checks += 1
            if passed:
                passed_checks += 1
    
    # Git status
    print_header("Git Repository")
    for name, passed, msg in check_git_status():
        print_check(name, passed, msg)
        total_checks += 1
        if passed:
            passed_checks += 1
    
    # Summary
    print_header("Validation Summary")
    percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {GREEN}{passed_checks}{RESET}")
    print(f"Failed: {RED}{total_checks - passed_checks}{RESET}")
    print(f"Success Rate: {percentage:.1f}%\n")
    
    if passed_checks == total_checks:
        print(f"{GREEN}✓ All checks passed! System is ready.{RESET}\n")
        return 0
    elif percentage >= 80:
        print(f"{YELLOW}⚠ Most checks passed. Review failures before deployment.{RESET}\n")
        return 0
    else:
        print(f"{RED}✗ Critical checks failed. Fix issues before deployment.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
