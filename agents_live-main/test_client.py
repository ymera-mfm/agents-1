"""
Coding Agent Test Client
========================
Comprehensive test client for the Coding Agent with examples
for all functionality including monitoring and error handling.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
import nats
from nats.aio.client import Client as NATS


class CodingAgentClient:
    """Client for interacting with the Coding Agent"""
    
    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc: Optional[NATS] = None
        self.agent_subject = "agent.coding_agent"
    
    async def connect(self):
        """Connect to NATS"""
        self.nc = await nats.connect(self.nats_url)
        print(f"✓ Connected to NATS at {self.nats_url}")
    
    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()
            print("✓ Disconnected from NATS")
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout_seconds: int = 30,
        max_memory_mb: int = 512,
        allow_network: bool = False,
        allow_filesystem: bool = False,
        environment_vars: Optional[Dict[str, str]] = None,
        stdin_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute code via the Coding Agent"""
        
        task = {
            "task_id": f"exec-{int(time.time() * 1000)}",
            "task_type": "execute_code",
            "payload": {
                "code": code,
                "language": language,
                "timeout_seconds": timeout_seconds,
                "max_memory_mb": max_memory_mb,
                "allow_network": allow_network,
                "allow_filesystem": allow_filesystem,
                "environment_vars": environment_vars or {},
                "stdin_data": stdin_data
            },
            "priority": "MEDIUM"
        }
        
        try:
            response = await self.nc.request(
                f"{self.agent_subject}.task",
                json.dumps(task).encode(),
                timeout=timeout_seconds + 5
            )
            return json.loads(response.data.decode())
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Request timed out",
                "task_id": task["task_id"]
            }
    
    async def validate_code(
        self,
        code: str,
        language: str = "python",
        allow_network: bool = False,
        allow_filesystem: bool = False
    ) -> Dict[str, Any]:
        """Validate code for security issues"""
        
        task = {
            "task_id": f"validate-{int(time.time() * 1000)}",
            "task_type": "validate_code",
            "payload": {
                "code": code,
                "language": language,
                "allow_network": allow_network,
                "allow_filesystem": allow_filesystem
            }
        }
        
        response = await self.nc.request(
            f"{self.agent_subject}.task",
            json.dumps(task).encode(),
            timeout=5
        )
        return json.loads(response.data.decode())
    
    async def list_languages(self) -> Dict[str, Any]:
        """List supported languages"""
        
        task = {
            "task_id": f"list-{int(time.time() * 1000)}",
            "task_type": "list_languages",
            "payload": {}
        }
        
        response = await self.nc.request(
            f"{self.agent_subject}.task",
            json.dumps(task).encode(),
            timeout=5
        )
        return json.loads(response.data.decode())
    
    async def get_execution_history(
        self,
        limit: int = 100,
        offset: int = 0,
        language: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get execution history"""
        
        task = {
            "task_id": f"history-{int(time.time() * 1000)}",
            "task_type": "get_execution_history",
            "payload": {
                "limit": limit,
                "offset": offset
            }
        }
        
        if language:
            task["payload"]["language"] = language
        if status:
            task["payload"]["status"] = status
        
        response = await self.nc.request(
            f"{self.agent_subject}.task",
            json.dumps(task).encode(),
            timeout=10
        )
        return json.loads(response.data.decode())
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        response = await self.nc.request(
            f"{self.agent_subject}.status",
            json.dumps({}).encode(),
            timeout=5
        )
        return json.loads(response.data.decode())
    
    async def get_health(self) -> Dict[str, Any]:
        """Get agent health"""
        response = await self.nc.request(
            f"{self.agent_subject}.health",
            json.dumps({}).encode(),
            timeout=5
        )
        return json.loads(response.data.decode())


class TestRunner:
    """Run comprehensive tests on the Coding Agent"""
    
    def __init__(self, client: CodingAgentClient):
        self.client = client
        self.tests_passed = 0
        self.tests_failed = 0
    
    def print_header(self, title: str):
        """Print test section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"       {details}")
        
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    def print_summary(self):
        """Print test summary"""
        total = self.tests_passed + self.tests_failed
        print(f"\n{'='*60}")
        print(f"  Test Summary")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.tests_passed} ({self.tests_passed/total*100:.1f}%)")
        print(f"Failed: {self.tests_failed} ({self.tests_failed/total*100:.1f}%)")
        print(f"{'='*60}\n")
    
    async def test_basic_python_execution(self):
        """Test basic Python code execution"""
        self.print_header("Test 1: Basic Python Execution")
        
        code = """
print("Hello, World!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
        
        result = await self.client.execute_code(code, language="python")
        
        passed = (
            result.get("status") == "success" and
            result["result"].get("status") == "success" and
            "Hello, World!" in result["result"].get("stdout", "") and
            "2 + 2 = 4" in result["result"].get("stdout", "")
        )
        
        self.print_result(
            "Python Hello World",
            passed,
            f"Execution time: {result['result'].get('execution_time_ms', 0):.2f}ms"
        )
    
    async def test_python_with_loops(self):
        """Test Python with loops and data structures"""
        self.print_header("Test 2: Python Loops and Data Structures")
        
        code = """
# Test loops
numbers = [1, 2, 3, 4, 5]
squared = [n**2 for n in numbers]
print(f"Squared: {squared}")

# Test dictionaries
person = {"name": "Alice", "age": 30}
print(f"Person: {person['name']}, {person['age']}")

# Test string operations
text = "hello world"
print(f"Uppercase: {text.upper()}")
"""
        
        result = await self.client.execute_code(code, language="python")
        
        passed = (
            result.get("status") == "success" and
            "Squared: [1, 4, 9, 16, 25]" in result["result"].get("stdout", "")
        )
        
        self.print_result("Python Loops & Data Structures", passed)
    
    async def test_javascript_execution(self):
        """Test JavaScript execution"""
        self.print_header("Test 3: JavaScript Execution")
        
        code = """
console.log("Hello from JavaScript!");

const numbers = [1, 2, 3, 4, 5];
const sum = numbers.reduce((a, b) => a + b, 0);
console.log(`Sum: ${sum}`);

const doubled = numbers.map(n => n * 2);
console.log(`Doubled: ${JSON.stringify(doubled)}`);
"""
        
        result = await self.client.execute_code(code, language="javascript")
        
        passed = (
            result.get("status") == "success" and
            "Hello from JavaScript!" in result["result"].get("stdout", "") and
            "Sum: 15" in result["result"].get("stdout", "")
        )
        
        self.print_result("JavaScript Execution", passed)
    
    async def test_bash_execution(self):
        """Test Bash execution"""
        self.print_header("Test 4: Bash Script Execution")
        
        code = """
#!/bin/bash
echo "Hello from Bash!"
echo "Current date: $(date +%Y-%m-%d)"
for i in {1..5}; do
    echo "Count: $i"
done
"""
        
        result = await self.client.execute_code(code, language="bash")
        
        passed = (
            result.get("status") == "success" and
            "Hello from Bash!" in result["result"].get("stdout", "")
        )
        
        self.print_result("Bash Execution", passed)
    
    async def test_environment_variables(self):
        """Test execution with environment variables"""
        self.print_header("Test 5: Environment Variables")
        
        code = """
import os
api_key = os.getenv('API_KEY', 'not_found')
db_url = os.getenv('DATABASE_URL', 'not_found')
print(f"API_KEY: {api_key}")
print(f"DATABASE_URL: {db_url}")
"""
        
        result = await self.client.execute_code(
            code,
            language="python",
            environment_vars={
                "API_KEY": "test-key-123",
                "DATABASE_URL": "postgresql://localhost/testdb"
            }
        )
        
        passed = (
            result.get("status") == "success" and
            "API_KEY: test-key-123" in result["result"].get("stdout", "") and
            "postgresql://localhost/testdb" in result["result"].get("stdout", "")
        )
        
        self.print_result("Environment Variables", passed)
    
    async def test_stdin_input(self):
        """Test execution with stdin input"""
        self.print_header("Test 6: Standard Input")
        
        code = """
import sys
for line in sys.stdin:
    print(f"Received: {line.strip()}")
"""
        
        result = await self.client.execute_code(
            code,
            language="python",
            stdin_data="Hello\nWorld\n"
        )
        
        passed = (
            result.get("status") == "success" and
            "Received: Hello" in result["result"].get("stdout", "") and
            "Received: World" in result["result"].get("stdout", "")
        )
        
        self.print_result("Standard Input", passed)
    
    async def test_timeout_handling(self):
        """Test timeout handling"""
        self.print_header("Test 7: Timeout Handling")
        
        code = """
import time
print("Starting infinite loop...")
while True:
    time.sleep(1)
    print("Still running...")
"""
        
        result = await self.client.execute_code(
            code,
            language="python",
            timeout_seconds=3
        )
        
        passed = result["result"].get("status") == "timeout"
        
        self.print_result("Timeout Handling", passed, "Expected timeout occurred")
    
    async def test_security_validation_dangerous_imports(self):
        """Test security validation for dangerous imports"""
        self.print_header("Test 8: Security - Dangerous Imports")
        
        code = """
import os
import subprocess
os.system('echo "This should be blocked"')
"""
        
        result = await self.client.validate_code(code, language="python")
        
        passed = (
            result.get("status") == "success" and
            result["result"].get("is_safe") == False and
            len(result["result"].get("issues", [])) > 0
        )
        
        self.print_result(
            "Security Validation - Dangerous Imports",
            passed,
            f"Detected {len(result['result'].get('issues', []))} issues"
        )
    
    async def test_security_validation_file_operations(self):
        """Test security validation for file operations"""
        self.print_header("Test 9: Security - File Operations")
        
        code = """
with open('/etc/passwd', 'r') as f:
    data = f.read()
    print(data)
"""
        
        result = await self.client.validate_code(
            code,
            language="python",
            allow_filesystem=False
        )
        
        passed = result["result"].get("is_safe") == False
        
        self.print_result("Security Validation - File Operations", passed)
    
    async def test_security_validation_safe_code(self):
        """Test security validation for safe code"""
        self.print_header("Test 10: Security - Safe Code")
        
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
"""
        
        result = await self.client.validate_code(code, language="python")
        
        passed = (
            result.get("status") == "success" and
            result["result"].get("is_safe") == True
        )
        
        self.print_result("Security Validation - Safe Code", passed)
    
    async def test_execution_with_errors(self):
        """Test execution with syntax/runtime errors"""
        self.print_header("Test 11: Error Handling")
        
        code = """
print("This will work")
undefined_variable
print("This won't execute")
"""
        
        result = await self.client.execute_code(code, language="python")
        
        passed = (
            result.get("status") == "success" and
            result["result"].get("status") == "error" and
            len(result["result"].get("stderr", "")) > 0
        )
        
        self.print_result(
            "Error Handling",
            passed,
            "Runtime error correctly captured"
        )
    
    async def test_large_output(self):
        """Test handling of large output"""
        self.print_header("Test 12: Large Output Handling")
        
        code = """
for i in range(1000):
    print(f"Line {i}: " + "x" * 100)
"""
        
        result = await self.client.execute_code(
            code,
            language="python",
            max_memory_mb=256
        )
        
        passed = (
            result.get("status") == "success" and
            len(result["result"].get("stdout", "")) > 0
        )
        
        truncated = result["result"].get("output_truncated", False)
        
        self.print_result(
            "Large Output Handling",
            passed,
            f"Output truncated: {truncated}"
        )
    
    async def test_caching(self):
        """Test result caching"""
        self.print_header("Test 13: Result Caching")
        
        code = """
import random
import time
print(f"Random: {random.random()}")
print(f"Time: {time.time()}")
"""
        
        # First execution
        result1 = await self.client.execute_code(code, language="python")
        
        # Second execution (should be cached)
        await asyncio.sleep(0.5)
        result2 = await self.client.execute_code(code, language="python")
        
        # Note: In production with caching enabled, outputs would be identical
        passed = (
            result1.get("status") == "success" and
            result2.get("status") == "success"
        )
        
        cached = result2["result"].get("cached", False)
        
        self.print_result(
            "Result Caching",
            passed,
            f"Second execution cached: {cached}"
        )
    
    async def test_list_languages(self):
        """Test listing supported languages"""
        self.print_header("Test 14: List Supported Languages")
        
        result = await self.client.list_languages()
        
        passed = (
            result.get("status") == "success" and
            "languages" in result.get("result", {}) and
            "python" in result["result"]["languages"]
        )
        
        if passed:
            languages = result["result"]["languages"]
            print("Supported Languages:")
            for lang, info in languages.items():
                status = "✓" if info['available'] else "✗"
                print(f"  {status} {lang}: {info.get('version', 'unknown')}")
        
        self.print_result("List Languages", passed)
    
    async def test_agent_status(self):
        """Test agent status retrieval"""
        self.print_header("Test 15: Agent Status")
        
        status = await self.client.get_status()
        
        passed = (
            "agent_id" in status and
            "state" in status and
            "metrics" in status and
            "coding_metrics" in status
        )
        
        if passed:
            print(f"Agent State: {status['state']}")
            print(f"Uptime: {status.get('uptime_seconds', 0):.1f}s")
            coding_metrics = status.get('coding_metrics', {})
            print(f"Total Executions: {coding_metrics.get('total_executions', 0)}")
            print(f"Success Rate: {coding_metrics.get('successful_executions', 0)}/{coding_metrics.get('total_executions', 1)}")
        
        self.print_result("Agent Status", passed)
    
    async def test_agent_health(self):
        """Test agent health check"""
        self.print_header("Test 16: Agent Health Check")
        
        health = await self.client.get_health()
        
        passed = (
            "agent_id" in health and
            "status" in health
        )
        
        if passed:
            print(f"Health Status: {health['status']}")
            if health.get('issues'):
                print(f"Issues: {', '.join(health['issues'])}")
            else:
                print("No issues detected")
        
        self.print_result("Agent Health", passed)
    
    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("  CODING AGENT TEST SUITE")
        print("="*60)
        
        try:
            # Basic functionality tests
            await self.test_basic_python_execution()
            await self.test_python_with_loops()
            await self.test_javascript_execution()
            await self.test_bash_execution()
            
            # Advanced features
            await self.test_environment_variables()
            await self.test_stdin_input()
            await self.test_timeout_handling()
            
            # Security tests
            await self.test_security_validation_dangerous_imports()
            await self.test_security_validation_file_operations()
            await self.test_security_validation_safe_code()
            
            # Error handling
            await self.test_execution_with_errors()
            await self.test_large_output()
            
            # Performance and caching
            await self.test_caching()
            
            # Agent management
            await self.test_list_languages()
            await self.test_agent_status()
            await self.test_agent_health()
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            print(f"\n✗ Test suite error: {e}")
            import traceback
            traceback.print_exc()


async def run_interactive_demo():
    """Run an interactive demonstration"""
    print("\n" + "="*60)
    print("  CODING AGENT INTERACTIVE DEMO")
    print("="*60 + "\n")
    
    client = CodingAgentClient()
    await client.connect()
    
    demos = [
        {
            "title": "Demo 1: Calculate Fibonacci Numbers",
            "code": """
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(n-1):
        a, b = b, a + b
    return b

for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
""",
            "language": "python"
        },
        {
            "title": "Demo 2: Array Operations in JavaScript",
            "code": """
const data = [5, 2, 8, 1, 9, 3, 7, 4, 6];

console.log("Original:", data);
console.log("Sorted:", [...data].sort((a, b) => a - b));
console.log("Sum:", data.reduce((a, b) => a + b, 0));
console.log("Average:", data.reduce((a, b) => a + b, 0) / data.length);
console.log("Max:", Math.max(...data));
console.log("Min:", Math.min(...data));
""",
            "language": "javascript"
        },
        {
            "title": "Demo 3: Text Processing in Bash",
            "code": """
#!/bin/bash
echo "=== Text Processing Demo ==="
echo ""
echo "Creating sample text..."
text="The quick brown fox jumps over the lazy dog"
echo "Original: $text"
echo ""
echo "Uppercase: ${text^^}"
echo "Lowercase: ${text,,}"
echo "Word count: $(echo $text | wc -w)"
echo "Character count: $(echo -n $text | wc -c)"
""",
            "language": "bash"
        }
    ]
    
    for demo in demos:
        print(f"\n{'='*60}")
        print(f"  {demo['title']}")
        print(f"{'='*60}\n")
        print(f"Language: {demo['language']}")
        print(f"\nCode:\n{demo['code']}\n")
        
        print("Executing...")
        result = await client.execute_code(demo['code'], language=demo['language'])
        
        if result.get("status") == "success":
            exec_result = result["result"]
            print(f"\n✓ Execution successful!")
            print(f"Time: {exec_result.get('execution_time_ms', 0):.2f}ms")
            print(f"Memory: {exec_result.get('memory_used_mb', 0):.2f}MB")
            print(f"\nOutput:\n{exec_result.get('stdout', '')}")
            
            if exec_result.get('stderr'):
                print(f"\nErrors:\n{exec_result.get('stderr')}")
        else:
            print(f"\n✗ Execution failed: {result.get('message', 'Unknown error')}")
        
        await asyncio.sleep(1)
    
    await client.disconnect()


async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        await run_interactive_demo()
    else:
        client = CodingAgentClient()
        await client.connect()
        
        runner = TestRunner(client)
        await runner.run_all_tests()
        
        await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()