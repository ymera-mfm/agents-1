"""
Static Analysis Agent - Usage Examples and API Documentation

This file demonstrates how to interact with the production-ready
Static Analysis Agent via NATS messaging.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List
from nats.aio.client import Client as NATS


class StaticAnalysisClient:
    """Client for interacting with Static Analysis Agent"""
    
    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc = None
    
    async def connect(self):
        """Connect to NATS"""
        self.nc = NATS()
        await self.nc.connect(self.nats_url)
        print(f"Connected to NATS at {self.nats_url}")
    
    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()
            print("Disconnected from NATS")
    
    async def analyze_code(
        self,
        source_code: str,
        file_path: str,
        analysis_types: List[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Perform comprehensive code analysis
        
        Args:
            source_code: The source code to analyze
            file_path: Path/name of the file
            analysis_types: List of analysis types to perform
                          Options: security, quality, performance, architecture,
                                  compliance, complexity, maintainability
            force_refresh: Force fresh analysis, skip cache
        
        Returns:
            Analysis result with findings and metrics
        """
        if analysis_types is None:
            analysis_types = [
                "security", "quality", "performance",
                "architecture", "compliance"
            ]
        
        request = {
            "task_type": "analyze_code",
            "payload": {
                "source_code": source_code,
                "file_path": file_path,
                "analysis_types": analysis_types,
                "force_refresh": force_refresh
            }
        }
        
        response = await self.nc.request(
            "agent.static_analysis_agent.task",
            json.dumps(request).encode(),
            timeout=30
        )
        
        return json.loads(response.data.decode())
    
    async def security_scan(
        self,
        source_code: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Perform focused security scan
        
        Args:
            source_code: The source code to scan
            file_path: Path/name of the file
        
        Returns:
            Security analysis result
        """
        request = {
            "source_code": source_code,
            "file_path": file_path
        }
        
        response = await self.nc.request(
            "static_analysis.security_scan",
            json.dumps(request).encode(),
            timeout=15
        )
        
        return json.loads(response.data.decode())
    
    async def quality_check(
        self,
        source_code: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Perform code quality check
        
        Args:
            source_code: The source code to check
            file_path: Path/name of the file
        
        Returns:
            Quality analysis result
        """
        request = {
            "source_code": source_code,
            "file_path": file_path
        }
        
        response = await self.nc.request(
            "static_analysis.quality_check",
            json.dumps(request).encode(),
            timeout=15
        )
        
        return json.loads(response.data.decode())
    
    async def batch_analysis(
        self,
        files: List[Dict[str, str]],
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform batch analysis on multiple files
        
        Args:
            files: List of files with source_code and file_path
            analysis_types: Types of analysis to perform
        
        Returns:
            Batch analysis results
        """
        if analysis_types is None:
            analysis_types = ["security", "quality"]
        
        request = {
            "task_type": "batch_analysis",
            "payload": {
                "files": files,
                "analysis_types": analysis_types
            }
        }
        
        response = await self.nc.request(
            "agent.static_analysis_agent.task",
            json.dumps(request).encode(),
            timeout=120  # Longer timeout for batch
        )
        
        return json.loads(response.data.decode())
    
    async def add_custom_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        rule_type: str,
        severity: str,
        pattern: str,
        remediation: str = None,
        references: List[str] = None
    ) -> Dict[str, Any]:
        """
        Add a custom analysis rule
        
        Args:
            rule_id: Unique rule identifier
            name: Rule name
            description: Rule description
            rule_type: Type (security, quality, etc.)
            severity: Severity level (critical, high, medium, low, info)
            pattern: Regex pattern to match
            remediation: How to fix the issue
            references: List of reference URLs
        
        Returns:
            Operation result
        """
        rule = {
            "id": rule_id,
            "name": name,
            "description": description,
            "rule_type": rule_type,
            "severity": severity,
            "pattern": pattern,
            "enabled": True,
            "metadata": {
                "remediation": remediation or "Review and fix the issue",
                "references": references or []
            }
        }
        
        request = {
            "action": "add",
            "rule": rule
        }
        
        response = await self.nc.request(
            "static_analysis.rule.update",
            json.dumps(request).encode(),
            timeout=10
        )
        
        return json.loads(response.data.decode())
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics
        
        Returns:
            Agent statistics and metrics
        """
        request = {
            "task_type": "get_stats",
            "payload": {}
        }
        
        response = await self.nc.request(
            "agent.static_analysis_agent.task",
            json.dumps(request).encode(),
            timeout=5
        )
        
        return json.loads(response.data.decode())
    
    async def clear_cache(self) -> Dict[str, Any]:
        """
        Clear analysis cache
        
        Returns:
            Operation result
        """
        request = {
            "task_type": "clear_cache",
            "payload": {}
        }
        
        response = await self.nc.request(
            "agent.static_analysis_agent.task",
            json.dumps(request).encode(),
            timeout=5
        )
        
        return json.loads(response.data.decode())


# ============================================================================
# EXAMPLE 1: Basic Security Scan
# ============================================================================

async def example_security_scan():
    """Example: Scan code for security vulnerabilities"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Security Scan")
    print("="*70)
    
    client = StaticAnalysisClient()
    await client.connect()
    
    # Code with security issues
    vulnerable_code = """
import os
import sqlite3

def login(username, password):
    # Security Issue: Hardcoded password
    admin_password = "SuperSecret123!"
    
    # Security Issue: SQL Injection
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    
    # Security Issue: Command Injection
    os.system(f"echo 'User logged in: {username}'")
    
    return cursor.fetchone()
"""
    
    result = await client.security_scan(vulnerable_code, "auth.py")
    
    print(f"\nSecurity Scan Results:")
    print(f"Status: {result['status']}")
    print(f"Total Findings: {result['analysis_result']['total_findings']}")
    print(f"\nFindings by Severity:")
    for severity, count in result['analysis_result']['findings_by_severity'].items():
        if count > 0:
            print(f"  {severity.upper()}: {count}")
    
    print(f"\nTop Findings:")
    for i, finding in enumerate(result['findings'][:3], 1):
        print(f"\n{i}. {finding['title']} ({finding['severity']})")
        print(f"   Line {finding['line_number']}: {finding['description']}")
        print(f"   Fix: {finding['remediation']}")
    
    print(f"\nRecommendations:")
    for rec in result.get('recommendations', []):
        print(f"  • {rec}")
    
    await client.disconnect()


# ============================================================================
# EXAMPLE 2: Quality Check
# ============================================================================

async def example_quality_check():
    """Example: Check code quality"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Code Quality Check")
    print("="*70)
    
    client = StaticAnalysisClient()
    await client.connect()
    
    # Code with quality issues
    poor_quality_code = """
def very_long_function_name_that_does_too_many_things_and_violates_single_responsibility():
    # TODO: Refactor this function
    x = 1
    y = 2
    result = x + y
    print(result)
    # FIXME: This is a hack
    if x > 0 and y > 0 and result > 0 and x < 100 and y < 100 and result < 200:
        return True
    return False

# Line that is way too long and exceeds the recommended maximum line length for Python code style guides
very_long_variable_name_that_should_be_shorter = "This is a very long string that makes the line exceed 88 characters"

import os
import sys
import json  # Unused import
"""
    
    result = await client.quality_check(poor_quality_code, "messy_code.py")
    
    print(f"\nQuality Check Results:")
    print(f"Status: {result['status']}")
    print(f"Total Issues: {result['analysis_result']['total_findings']}")
    
    if 'metrics' in result['analysis_result']:
        metrics = result['analysis_result']['metrics']
        if 'quality' in metrics:
            print(f"\nCode Metrics:")
            print(f"  Lines of Code: {metrics['quality'].get('lines_of_code', 'N/A')}")
            print(f"  Cyclomatic Complexity: {metrics['quality'].get('cyclomatic_complexity', 'N/A')}")
            print(f"  Maintainability Index: {metrics['quality'].get('maintainability_index', 'N/A')}")
    
    print(f"\nQuality Issues:")
    for finding in result['findings']:
        print(f"  • {finding['title']} (line {finding['line_number']})")
    
    await client.disconnect()


# ============================================================================
# EXAMPLE 3: Comprehensive Analysis
# ============================================================================

async def example_comprehensive_analysis():
    """Example: Full multi-type analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Comprehensive Analysis")
    print("="*70)
    
    client = StaticAnalysisClient()
    await client.connect()
    
    # Complex code with multiple issue types
    complex_code = """
import os
import sys

class DataProcessor:
    def __init__(self):
        self.api_key = "sk-1234567890abcdef"  # Security: hardcoded secret
        self.data = []
    
    def process_data(self, user_input, filter_type, sort_order, limit, offset, include_metadata, format_output):
        # Architecture: Too many parameters
        # Performance: Inefficient loop
        for i in range(len(self.data)):
            item = self.data[i]
            
            # Security: Command injection risk
            if filter_type == "system":
                os.system(f"process_item {item}")
            
            # Quality: Complex nested logic
            if item > 0:
                if user_input:
                    if filter_type:
                        if sort_order:
                            if limit:
                                if offset:
                                    if include_metadata:
                                        if format_output:
                                            result = item
        
        # Security: SQL injection
        query = f"SELECT * FROM data WHERE type = '{filter_type}'"
        
        return result
    
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass  # Architecture: God Object
"""
    
    result = await client.analyze_code(
        complex_code,
        "data_processor.py",
        analysis_types=[
            "security",
            "quality", 
            "performance",
            "architecture",
            "complexity"
        ]
    )
    
    print(f"\nComprehensive Analysis Results:")
    print(f"Analysis ID: {result['analysis_result']['analysis_id']}")
    print(f"Execution Time: {result['analysis_result']['execution_time_ms']:.2f}ms")
    print(f"Total Findings: {result['analysis_result']['total_findings']}")
    
    print(f"\nFindings by Type:")
    if 'summary' in result['analysis_result']:
        type_breakdown = result['analysis_result']['summary'].get('type_breakdown', {})
        for analysis_type, count in type_breakdown.items():
            if count > 0:
                print(f"  {analysis_type.capitalize()}: {count}")
    
    print(f"\nRisk Score: {result['analysis_result']['summary'].get('risk_score', 0)}")
    
    print(f"\nCritical Issues:")
    critical = [f for f in result['findings'] if f['severity'] == 'critical']
    for finding in critical:
        print(f"  ⚠️  {finding['title']} (line {finding['line_number']})")
        print(f"      {finding['remediation']}")
    
    await client.disconnect()


# ============================================================================
# EXAMPLE 4: Batch Analysis
# ============================================================================

async def example_batch_analysis():
    """Example: Analyze multiple files at once"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Analysis")
    print("="*70)
    
    client = StaticAnalysisClient()
    await client.connect()
    
    # Multiple files to analyze
    files = [
        {
            "source_code": "password = 'hardcoded123'\nprint(password)",
            "file_path": "config.py"
        },
        {
            "source_code": "def long_line():\n    x = 'this is a very long line that exceeds the maximum recommended length for python code'",
            "file_path": "utils.py"
        },
        {
            "source_code": "import os\nos.system('rm -rf ' + user_input)",
            "file_path": "dangerous.py"
        },
        {
            "source_code": "def clean_code():\n    return 'Hello, World!'",
            "file_path": "clean.py"
        }
    ]
    
    result = await client.batch_analysis(
        files,
        analysis_types=["security", "quality"]
    )
    
    print(f"\nBatch Analysis Results:")
    summary = result['batch_summary']
    print(f"Total Files: {summary['total_files']}")
    print(f"Successfully Analyzed: {summary['analyzed']}")
    print(f"Errors: {summary['errors']}")
    print(f"Total Findings: {summary['total_findings']}")
    
    print(f"\nPer-File Results:")
    for file_result in result['results']:
        file_path = file_result['analysis_result']['target_path']
        findings_count = file_result['analysis_result']['total_findings']
        print(f"  {file_path}: {findings_count} issues found")
    
    if result.get('errors'):
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  {error['file_path']}: {error['error']}")
    
    await client.disconnect()


# ============================================================================
# EXAMPLE 5: Custom Rules
# ============================================================================

async def example_custom_rules():
    """Example: Add and use custom analysis rules"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Custom Rules")
    print("="*70)
    
    client = StaticAnalysisClient()
    await client.connect()
    
    # Add custom security rule
    print("\nAdding custom rule...")
    rule_result = await client.add_custom_rule(
        rule_id="custom_deprecated_function",
        name="Deprecated Function Usage",
        description="Detects usage of deprecated functions that should be replaced",
        rule_type="quality",
        severity="medium",
        pattern=r"(gets|strcpy|sprintf)\s*\(",
        remediation="Replace with safer alternatives: fgets, strncpy, snprintf",
        references=["https://wiki.sei.cmu.edu/confluence/display/c/MSC24-C"]
    )
    
    print(f"Rule addition: {rule_result['status']}")
    
    # Test with code using deprecated function
    test_code = """
#include <stdio.h>
#include <string.h>

void unsafe_function(char* input) {
    char buffer[100];
    strcpy(buffer, input);  // Should trigger custom rule
    sprintf(buffer, "Value: %s", input);  // Should trigger custom rule
}
"""
    
    print("\nAnalyzing code with custom rule...")
    result = await client.analyze_code(
        test_code,
        "unsafe.c",
        analysis_types=["quality"],
        force_refresh=True  # Force refresh to use new rule
    )
    
    print(f"\nFindings:")
    for finding in result['findings']:
        if finding['rule_id'] == 'custom_deprecated_function':
            print(f"  ✓ Custom rule detected issue at line {finding['line_number']}")
            print(f"    {finding['title']}: {finding['description']}")
    
    await client.disconnect()


# ============================================================================
# EXAMPLE 6: Caching and Performance
# ============================================================================

async def example_caching():
    """Example: Demonstrate caching behavior"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Caching and Performance")
    print("="*70)
    
    client = StaticAnalysisClient()
    await client.connect()
    
    test_code = """
def hello():
    print('Hello, World!')
"""
    
    # First analysis (cache miss)
    print("\nFirst analysis (cache miss)...")
    import time
    start = time.time()
    result1 = await client.analyze_code(
        test_code,
        "hello.py",
        analysis_types=["quality"]
    )
    time1 = (time.time() - start) * 1000
    
    # Second analysis (cache hit)
    print("Second analysis (cache hit)...")
    start = time.time()
    result2 = await client.analyze_code(
        test_code,
        "hello.py",
        analysis_types=["quality"]
    )
    time2 = (time.time() - start) * 1000
    
    # Third analysis with force refresh
    print("Third analysis (forced refresh)...")
    start = time.time()
    result3 = await client.analyze_code(
        test_code,
        "hello.py",
        analysis_types=["quality"],
        force_refresh=True
    )
    time3 = (time.time() - start) * 1000
    
    print(f"\nPerformance Comparison:")
    print(f"  First analysis (cache miss):  {time1:.2f}ms")
    print(f"  Second analysis (cache hit):   {time2:.2f}ms")
    print(f"  Third analysis (forced):       {time3:.2f}ms")
    print(f"  Cache speedup: {time1/time2:.2f}x faster")
    
    # Get statistics
    stats = await client.get_stats()
    print(f"\nAgent Statistics:")
    print(f"  Total Analyses: {stats['stats']['total_analyses']}")
    print(f"  Cache Hits: {stats['cache_stats']['cache_hits']}")
    print(f"  Cache Misses: {stats['cache_stats']['cache_misses']}")
    print(f"  Hit Rate: {stats['cache_stats']['hit_rate']:.1f}%")
    
    await client.disconnect()


# ============================================================================
# EXAMPLE 7: Real-World Scenario - API Endpoint Analysis
# ============================================================================

async def example_api_endpoint_analysis():
    """Example: Analyze a real API endpoint for security and quality"""
    print("\n" + "="*70)
    print("EXAMPLE 7: API Endpoint Analysis")
    print("="*70)
    
    client = StaticAnalysisClient()
    await client.connect()
    
    api_code = """
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Security Issue: Hardcoded secret
SECRET_KEY = "my-secret-key-12345"

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    # Security Issue: SQL Injection
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    user = cursor.fetchone()
    
    # Security Issue: No input validation
    return jsonify(user)

@app.route('/api/execute', methods=['POST'])
def execute_command():
    # Security Issue: Command Injection
    cmd = request.json.get('command')
    result = os.system(cmd)
    return jsonify({'result': result})

@app.route('/api/search', methods=['GET'])
def search():
    # Performance Issue: Inefficient loop
    query = request.args.get('q')
    results = []
    all_items = get_all_items()
    
    for i in range(len(all_items)):
        if query in all_items[i]:
            results.append(all_items[i])
    
    return jsonify(results)

def get_all_items():
    # TODO: Implement caching
    # FIXME: This queries the database every time
    return []
"""
    
    result = await client.analyze_code(
        api_code,
        "api.py",
        analysis_types=["security", "quality", "performance"]
    )
    
    print(f"\nAPI Endpoint Analysis:")
    print(f"File: {result['analysis_result']['target_path']}")
    print(f"Total Issues: {result['analysis_result']['total_findings']}")
    print(f"Risk Score: {result['analysis_result']['summary'].get('risk_score', 0)}")
    
    # Group findings by endpoint
    print(f"\nSecurity Issues by Severity:")
    security_findings = [f for f in result['findings'] if f['type'] == 'security']
    for severity in ['critical', 'high', 'medium', 'low']:
        issues = [f for f in security_findings if f['severity'] == severity]
        if issues:
            print(f"\n  {severity.upper()} ({len(issues)} issues):")
            for issue in issues:
                print(f"    • Line {issue['line_number']}: {issue['title']}")
                print(f"      Fix: {issue['remediation']}")
    
    print(f"\nRecommendations:")
    for i, rec in enumerate(result.get('recommendations', []), 1):
        print(f"  {i}. {rec}")
    
    await client.disconnect()


# ============================================================================
# EXAMPLE 8: Integration with CI/CD Pipeline
# ============================================================================

async def example_cicd_integration():
    """Example: Use in CI/CD pipeline"""
    print("\n" + "="*70)
    print("EXAMPLE 8: CI/CD Pipeline Integration")
    print("="*70)
    
    client = StaticAnalysisClient()
    await client.connect()
    
    # Simulating a code change in PR
    changed_files = [
        {
            "source_code": """
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE name='{username}'"
    # Critical security issue
""",
            "file_path": "src/auth.py"
        },
        {
            "source_code": """
def process_payment(amount):
    # FIXME: Add proper validation
    return charge_card(amount)
""",
            "file_path": "src/payment.py"
        }
    ]
    
    print("\n🔍 Running static analysis on changed files...")
    result = await client.batch_analysis(
        changed_files,
        analysis_types=["security", "quality"]
    )
    
    # Check if analysis should fail the build
    critical_count = 0
    high_count = 0
    
    for file_result in result['results']:
        for finding in file_result['findings']:
            if finding['severity'] == 'critical':
                critical_count += 1
            elif finding['severity'] == 'high':
                high_count += 1
    
    print(f"\n📊 Analysis Summary:")
    print(f"  Files Analyzed: {result['batch_summary']['analyzed']}")
    print(f"  Total Issues: {result['batch_summary']['total_findings']}")
    print(f"  Critical: {critical_count}")
    print(f"  High: {high_count}")
    
    # CI/CD Decision Logic
    if critical_count > 0:
        print(f"\n❌ BUILD FAILED: {critical_count} critical security issues found")
        print("   Please fix critical issues before merging.")
        exit_code = 1
    elif high_count > 2:
        print(f"\n⚠️  BUILD WARNING: {high_count} high-severity issues found")
        print("   Consider fixing before merging.")
        exit_code = 0
    else:
        print(f"\n✅ BUILD PASSED: No blocking issues found")
        exit_code = 0
    
    print(f"\n📝 Detailed Report:")
    for file_result in result['results']:
        file_path = file_result['analysis_result']['target_path']
        findings = file_result['findings']
        
        if findings:
            print(f"\n  {file_path}:")
            for finding in findings:
                icon = "🔴" if finding['severity'] in ['critical', 'high'] else "🟡"
                print(f"    {icon} Line {finding['line_number']}: {finding['title']}")
    
    await client.disconnect()
    return exit_code


# ============================================================================
# Main Runner
# ============================================================================

async def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("STATIC ANALYSIS AGENT - USAGE EXAMPLES")
    print("="*70)
    
    examples = [
        ("Security Scan", example_security_scan),
        ("Quality Check", example_quality_check),
        ("Comprehensive Analysis", example_comprehensive_analysis),
        ("Batch Analysis", example_batch_analysis),
        ("Custom Rules", example_custom_rules),
        ("Caching & Performance", example_caching),
        ("API Endpoint Analysis", example_api_endpoint_analysis),
        ("CI/CD Integration", example_cicd_integration)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...\n")
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
        
        # Pause between examples
        await asyncio.sleep(1)
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
