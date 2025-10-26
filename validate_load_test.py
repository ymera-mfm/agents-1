#!/usr/bin/env python3
"""
Validation script for the load test
Checks that all issues have been fixed
"""
import ast
import re
import sys

def check_file(filename):
    """Validate the load test file"""
    with open(filename, 'r') as f:
        content = f.read()
    
    issues = []
    warnings = []
    successes = []
    
    # 1. Check for proper error handling in login
    if 'def login(self):' in content:
        login_sections = re.findall(r'def login\(self\):.*?(?=\n    def |\n    @task|\nclass )', content, re.DOTALL)
        for section in login_sections:
            if 'try:' in section and 'except' in section:
                successes.append("✓ login() has try/except error handling")
            else:
                issues.append("✗ login() missing try/except")
            
            if 'catch_response=True' in section:
                successes.append("✓ login() uses catch_response for proper tracking")
            else:
                warnings.append("⚠ login() should use catch_response")
    
    # 2. Check for environment variable usage
    if 'os.getenv(' in content:
        if "os.getenv('LOAD_TEST_USERNAME'" in content:
            successes.append("✓ Uses environment variable for username")
        if "os.getenv('LOAD_TEST_PASSWORD'" in content:
            successes.append("✓ Uses environment variable for password")
    else:
        warnings.append("⚠ No environment variable usage found")
    
    # 3. Check response.json() calls have error handling
    json_pattern = r'response\.json\(\)'
    json_matches = list(re.finditer(json_pattern, content))
    protected_json_calls = 0
    
    for match in json_matches:
        start = max(0, match.start() - 500)
        end = min(len(content), match.end() + 100)
        context = content[start:end]
        
        if 'try:' in context or 'except' in context:
            protected_json_calls += 1
    
    if len(json_matches) > 0:
        if protected_json_calls == len(json_matches):
            successes.append(f"✓ All {len(json_matches)} response.json() calls have error handling")
        elif protected_json_calls > len(json_matches) // 2:
            warnings.append(f"⚠ Only {protected_json_calls}/{len(json_matches)} response.json() calls protected")
        else:
            issues.append(f"✗ Only {protected_json_calls}/{len(json_matches)} response.json() calls have error handling")
    
    # 4. Check for catch_response usage in tasks
    task_pattern = r'@task\([0-9]+\)\s+def\s+(\w+)\(self\):.*?(?=\n    @task|\n    def |\nclass |\Z)'
    tasks = re.findall(task_pattern, content, re.DOTALL)
    
    tasks_with_catch = 0
    for task in tasks:
        if 'catch_response=True' in task:
            tasks_with_catch += 1
    
    if len(tasks) > 0:
        if tasks_with_catch == len(tasks):
            successes.append(f"✓ All {len(tasks)} tasks use catch_response")
        elif tasks_with_catch > len(tasks) // 2:
            successes.append(f"✓ Most tasks ({tasks_with_catch}/{len(tasks)}) use catch_response")
        else:
            warnings.append(f"⚠ Only {tasks_with_catch}/{len(tasks)} tasks use catch_response")
    
    # 5. Check for response status validation
    if 'response.status_code' in content:
        status_checks = content.count('response.status_code')
        if status_checks > 5:
            successes.append(f"✓ Response status codes are checked ({status_checks} checks)")
        else:
            warnings.append(f"⚠ Limited status code checking ({status_checks} checks)")
    else:
        issues.append("✗ No response status code validation found")
    
    # 6. Check for proper response.success() and response.failure()
    if 'response.success()' in content and 'response.failure(' in content:
        successes.append("✓ Uses response.success() and response.failure() for tracking")
    else:
        warnings.append("⚠ Should use response.success/failure for better tracking")
    
    # 7. Check for authentication state tracking
    if 'self.authenticated' in content:
        successes.append("✓ Tracks authentication state")
    else:
        warnings.append("⚠ No authentication state tracking")
    
    # 8. Check for list boundary checks
    if 'if self.agent_ids' in content or 'if len(self.agent_ids)' in content:
        successes.append("✓ Checks agent_ids list before using")
    else:
        issues.append("✗ Missing boundary checks for agent_ids list")
    
    # 9. Check for timeout on heavy operations
    if 'timeout=' in content:
        timeout_count = content.count('timeout=')
        successes.append(f"✓ Timeouts configured for operations ({timeout_count} operations)")
    else:
        warnings.append("⚠ No timeouts configured for long operations")
    
    # 10. Check for proper event handlers
    if '@events.test_start.add_listener' in content:
        successes.append("✓ Has test start event handler")
    
    if '@events.test_stop.add_listener' in content:
        successes.append("✓ Has test stop event handler")
    
    if '@events.request.add_listener' in content:
        successes.append("✓ Has request event handler")
    
    # 11. Check for hardcoded credentials warning
    if 'testpass123' in content:
        # Check if it's only used as default fallback
        if "os.getenv('LOAD_TEST_PASSWORD', 'testpass123')" in content:
            successes.append("✓ Hardcoded password is only a fallback")
        else:
            warnings.append("⚠ Hardcoded credentials still present")
    
    # 12. Check for configuration via environment
    if 'os.getenv(' in content:
        env_vars = re.findall(r"os\.getenv\(['\"]([^'\"]+)['\"]", content)
        if env_vars:
            successes.append(f"✓ Uses {len(set(env_vars))} environment variables for configuration")
    
    # 13. Check syntax
    try:
        ast.parse(content)
        successes.append("✓ Python syntax is valid")
    except SyntaxError as e:
        issues.append(f"✗ Syntax error: {e}")
    
    # Print results
    print("=" * 70)
    print("LOAD TEST VALIDATION RESULTS")
    print("=" * 70)
    
    if successes:
        print("\n✅ PASSED CHECKS:")
        for success in successes:
            print(f"  {success}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    
    print("\n" + "=" * 70)
    print(f"Summary: {len(successes)} passed, {len(warnings)} warnings, {len(issues)} issues")
    print("=" * 70)
    
    return len(issues) == 0

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "locust_api_load_test.py"
    success = check_file(filename)
    sys.exit(0 if success else 1)
