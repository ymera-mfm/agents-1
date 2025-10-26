#!/usr/bin/env python3
"""
Agent System Catalog Analyzer
Analyzes all agent files and creates comprehensive inventory with actual measurements
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any


def analyze_agent_file(filepath: str) -> Dict[str, Any]:
    """Analyze a single agent file and extract metadata"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        # Extract classes
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        # Extract functions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        # Extract async functions
        async_functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)]
        
        # Check for BaseAgent inheritance
        has_base_agent = 'BaseAgent' in content
        
        # Count async methods
        async_methods = len(async_functions)
        
        # Get imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Count lines
        lines = len(content.split('\n'))
        
        # Check for specific patterns
        has_async_init = 'async def initialize' in content or 'async def __init__' in content
        has_process_method = 'def process' in content or 'async def process' in content
        has_cleanup = 'def cleanup' in content or 'async def cleanup' in content
        
        # Check for database usage
        has_database = any(imp in ['sqlalchemy', 'asyncpg', 'database', 'db'] for imp in imports)
        
        # Check for API usage
        has_api = any(imp in ['fastapi', 'httpx', 'aiohttp', 'requests'] for imp in imports)
        
        # Check for file operations
        has_file_ops = 'aiofiles' in imports or 'open(' in content
        
        return {
            "file": filepath,
            "classes": classes,
            "class_count": len(classes),
            "functions": functions[:10],  # First 10 functions
            "function_count": len(functions),
            "async_functions": async_functions[:10],  # First 10 async functions
            "async_function_count": len(async_functions),
            "has_base_agent": has_base_agent,
            "async_methods": async_methods,
            "lines": lines,
            "imports": imports[:15],  # First 15 imports
            "has_async_init": has_async_init,
            "has_process_method": has_process_method,
            "has_cleanup": has_cleanup,
            "has_database": has_database,
            "has_api": has_api,
            "has_file_ops": has_file_ops,
            "status": "analyzed"
        }
    except SyntaxError as e:
        return {
            "file": filepath,
            "error": f"SyntaxError: {str(e)}",
            "status": "syntax_error"
        }
    except Exception as e:
        return {
            "file": filepath,
            "error": str(e),
            "status": "error"
        }


def create_agent_catalog() -> Dict[str, Any]:
    """Create complete agent catalog from discovered files"""
    
    # Read agent files list
    with open('/tmp/agent_files_found.txt', 'r') as f:
        agent_files = [line.strip() for line in f.readlines()]
    
    catalog = {
        "total_files": len(agent_files),
        "total_classes": 0,
        "total_functions": 0,
        "total_async_functions": 0,
        "total_lines": 0,
        "agents_detail": [],
        "summary_stats": {}
    }
    
    # Analyze each file
    for filepath in agent_files:
        if not os.path.exists(filepath):
            # Try with relative path from cwd
            full_path = os.path.join(os.getcwd(), filepath.lstrip('./'))
            if os.path.exists(full_path):
                filepath = full_path
            else:
                print(f"Warning: File not found: {filepath}")
                continue
        
        print(f"Analyzing: {filepath}")
        analysis = analyze_agent_file(filepath)
        catalog["agents_detail"].append(analysis)
        
        # Aggregate stats
        if "error" not in analysis:
            catalog["total_classes"] += analysis.get("class_count", 0)
            catalog["total_functions"] += analysis.get("function_count", 0)
            catalog["total_async_functions"] += analysis.get("async_function_count", 0)
            catalog["total_lines"] += analysis.get("lines", 0)
    
    # Calculate summary statistics
    analyzed_count = sum(1 for a in catalog["agents_detail"] if a.get("status") == "analyzed")
    error_count = sum(1 for a in catalog["agents_detail"] if "error" in a)
    with_base_agent = sum(1 for a in catalog["agents_detail"] if a.get("has_base_agent", False))
    with_async = sum(1 for a in catalog["agents_detail"] if a.get("async_methods", 0) > 0)
    with_database = sum(1 for a in catalog["agents_detail"] if a.get("has_database", False))
    with_api = sum(1 for a in catalog["agents_detail"] if a.get("has_api", False))
    
    catalog["summary_stats"] = {
        "analyzed_successfully": analyzed_count,
        "analysis_errors": error_count,
        "with_base_agent_inheritance": with_base_agent,
        "with_async_methods": with_async,
        "with_database_integration": with_database,
        "with_api_integration": with_api,
        "average_lines_per_file": catalog["total_lines"] // len(agent_files) if agent_files else 0
    }
    
    return catalog


if __name__ == "__main__":
    print("=" * 60)
    print("AGENT SYSTEM CATALOG ANALYZER")
    print("=" * 60)
    print()
    
    catalog = create_agent_catalog()
    
    # Save catalog
    output_file = "agent_catalog_complete.json"
    with open(output_file, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    print()
    print("=" * 60)
    print("CATALOG COMPLETE")
    print("=" * 60)
    print(f"Total files analyzed: {catalog['total_files']}")
    print(f"Successfully analyzed: {catalog['summary_stats']['analyzed_successfully']}")
    print(f"Analysis errors: {catalog['summary_stats']['analysis_errors']}")
    print(f"Total classes found: {catalog['total_classes']}")
    print(f"Total functions: {catalog['total_functions']}")
    print(f"Total async functions: {catalog['total_async_functions']}")
    print(f"Total lines of code: {catalog['total_lines']}")
    print(f"Average lines per file: {catalog['summary_stats']['average_lines_per_file']}")
    print()
    print(f"With BaseAgent inheritance: {catalog['summary_stats']['with_base_agent_inheritance']}")
    print(f"With async methods: {catalog['summary_stats']['with_async_methods']}")
    print(f"With database integration: {catalog['summary_stats']['with_database_integration']}")
    print(f"With API integration: {catalog['summary_stats']['with_api_integration']}")
    print()
    print(f"Catalog saved to: {output_file}")
    print("=" * 60)
