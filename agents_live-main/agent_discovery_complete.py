"""
Complete Agent Discovery and Inventory System
Discovers all agents in the system with MEASURED data (no estimates)
"""

import ast
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
from collections import defaultdict


class AgentDiscoverySystem:
    """Discovers and catalogs all agents with actual measurements"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.discovered_agents = []
        self.syntax_errors = []
        self.discovery_metrics = {
            "start_time": None,
            "end_time": None,
            "duration_ms": 0,
            "files_scanned": 0,
            "files_with_agents": 0,
            "total_agents": 0,
            "total_classes": 0,
            "total_methods": 0,
            "syntax_errors": 0
        }
        
    def discover_all_agents(self) -> Dict[str, Any]:
        """Discover all agents with MEASURED metrics"""
        self.discovery_metrics["start_time"] = datetime.now().isoformat()
        start = time.time()
        
        # Find all Python files
        py_files = list(self.root_dir.rglob("*.py"))
        self.discovery_metrics["files_scanned"] = len(py_files)
        
        for py_file in py_files:
            # Skip test files, venv, and certain directories
            if self._should_skip_file(py_file):
                continue
                
            try:
                self._analyze_file(py_file)
            except Exception as e:
                self.syntax_errors.append({
                    "file": str(py_file),
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                self.discovery_metrics["syntax_errors"] += 1
        
        # Calculate metrics
        end = time.time()
        self.discovery_metrics["end_time"] = datetime.now().isoformat()
        self.discovery_metrics["duration_ms"] = (end - start) * 1000
        self.discovery_metrics["files_with_agents"] = len(self.discovered_agents)
        self.discovery_metrics["total_agents"] = sum(
            agent["agent_count"] for agent in self.discovered_agents
        )
        self.discovery_metrics["total_classes"] = sum(
            agent["class_count"] for agent in self.discovered_agents
        )
        self.discovery_metrics["total_methods"] = sum(
            agent["method_count"] for agent in self.discovered_agents
        )
        
        return {
            "discovery_timestamp": datetime.now().isoformat(),
            "metrics": self.discovery_metrics,
            "agents": self.discovered_agents,
            "syntax_errors": self.syntax_errors,
            "summary": self._generate_summary()
        }
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            "venv", "env", ".venv", "__pycache__", 
            ".git", ".pytest_cache", "htmlcov",
            "tests", "test_", "conftest", ".backup",
            "enhanced_workspace", "repository_analysis"
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path):
        """Analyze a Python file for agent classes"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.syntax_errors.append({
                "file": str(file_path),
                "error": f"SyntaxError: {e}",
                "line": e.lineno,
                "offset": e.offset
            })
            self.discovery_metrics["syntax_errors"] += 1
            return
        
        agent_info = {
            "file": str(file_path.relative_to(self.root_dir)),
            "absolute_path": str(file_path),
            "classes": [],
            "agent_classes": [],
            "base_classes": [],
            "methods": {},
            "async_methods": {},
            "imports": [],
            "has_base_agent": False,
            "file_size_bytes": file_path.stat().st_size,
            "line_count": len(content.splitlines()),
            "class_count": 0,
            "agent_count": 0,
            "method_count": 0,
            "async_method_count": 0
        }
        
        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    agent_info["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    agent_info["imports"].append(node.module)
        
        # Extract classes and methods
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node)
                agent_info["classes"].append(class_info["name"])
                agent_info["class_count"] += 1
                
                # Check if it's an agent class
                if self._is_agent_class(node, class_info):
                    agent_info["agent_classes"].append(class_info["name"])
                    agent_info["agent_count"] += 1
                    agent_info["has_base_agent"] = True
                
                # Store methods
                agent_info["methods"][class_info["name"]] = class_info["methods"]
                agent_info["async_methods"][class_info["name"]] = class_info["async_methods"]
                agent_info["method_count"] += class_info["method_count"]
                agent_info["async_method_count"] += class_info["async_method_count"]
                
                # Track base classes
                for base in class_info["bases"]:
                    if "agent" in base.lower() or "base" in base.lower():
                        agent_info["base_classes"].append(base)
        
        # Only add if it has agent-related content
        if (agent_info["agent_count"] > 0 or 
            agent_info["has_base_agent"] or
            any("agent" in cls.lower() for cls in agent_info["classes"]) or
            any("agent" in imp.lower() for imp in agent_info["imports"])):
            self.discovered_agents.append(agent_info)
    
    def _extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract detailed information about a class"""
        info = {
            "name": node.name,
            "bases": [self._get_base_name(base) for base in node.bases],
            "methods": [],
            "async_methods": [],
            "method_count": 0,
            "async_method_count": 0,
            "has_init": False,
            "has_cleanup": False,
            "has_process": False,
            "docstring": ast.get_docstring(node) or ""
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name
                info["methods"].append(method_name)
                info["method_count"] += 1
                
                if method_name == "__init__":
                    info["has_init"] = True
                elif "cleanup" in method_name.lower():
                    info["has_cleanup"] = True
                elif "process" in method_name.lower():
                    info["has_process"] = True
                    
            elif isinstance(item, ast.AsyncFunctionDef):
                method_name = item.name
                info["async_methods"].append(method_name)
                info["async_method_count"] += 1
                
                if "cleanup" in method_name.lower():
                    info["has_cleanup"] = True
                elif "process" in method_name.lower():
                    info["has_process"] = True
        
        return info
    
    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name from AST node"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return "Unknown"
    
    def _is_agent_class(self, node: ast.ClassDef, class_info: Dict) -> bool:
        """Determine if a class is an agent class"""
        # Check name
        if "agent" in node.name.lower():
            return True
        
        # Check base classes
        for base in class_info["bases"]:
            if "agent" in base.lower():
                return True
        
        # Check for agent-like methods
        agent_methods = {"process", "initialize", "cleanup", "execute", "handle"}
        has_agent_methods = any(
            any(m in method.lower() for m in agent_methods)
            for method in class_info["methods"] + class_info["async_methods"]
        )
        
        return has_agent_methods
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        agent_types = defaultdict(int)
        capabilities = defaultdict(int)
        
        for agent in self.discovered_agents:
            # Categorize by type
            file_name = agent["file"].lower()
            if "learning" in file_name:
                agent_types["learning"] += 1
            elif "monitoring" in file_name:
                agent_types["monitoring"] += 1
            elif "communication" in file_name:
                agent_types["communication"] += 1
            elif "validation" in file_name:
                agent_types["validation"] += 1
            elif "security" in file_name:
                agent_types["security"] += 1
            elif "editing" in file_name or "drafting" in file_name:
                agent_types["content"] += 1
            elif "orchestrator" in file_name or "coordinator" in file_name:
                agent_types["orchestration"] += 1
            else:
                agent_types["other"] += 1
            
            # Track capabilities
            if agent["async_method_count"] > 0:
                capabilities["async"] += 1
            if any("database" in imp.lower() or "sql" in imp.lower() 
                   for imp in agent["imports"]):
                capabilities["database"] += 1
            if any("fastapi" in imp.lower() or "api" in imp.lower() 
                   for imp in agent["imports"]):
                capabilities["api"] += 1
        
        return {
            "agent_types": dict(agent_types),
            "capabilities": dict(capabilities),
            "average_file_size_bytes": sum(a["file_size_bytes"] for a in self.discovered_agents) / len(self.discovered_agents) if self.discovered_agents else 0,
            "average_line_count": sum(a["line_count"] for a in self.discovered_agents) / len(self.discovered_agents) if self.discovered_agents else 0,
            "average_classes_per_file": sum(a["class_count"] for a in self.discovered_agents) / len(self.discovered_agents) if self.discovered_agents else 0,
            "average_methods_per_file": sum(a["method_count"] for a in self.discovered_agents) / len(self.discovered_agents) if self.discovered_agents else 0,
            "files_with_syntax_errors": len(self.syntax_errors),
            "syntax_error_rate": f"{(len(self.syntax_errors) / self.discovery_metrics['files_scanned'] * 100):.2f}%"
        }


def main():
    """Run complete agent discovery"""
    print("🔍 Starting Complete Agent Discovery System...")
    print("=" * 80)
    
    discovery = AgentDiscoverySystem()
    results = discovery.discover_all_agents()
    
    # Save results
    output_file = "agent_catalog_complete.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Discovery Complete!")
    print(f"⏱️  Duration: {results['metrics']['duration_ms']:.2f}ms")
    print(f"📁 Files Scanned: {results['metrics']['files_scanned']}")
    print(f"🤖 Agent Files Found: {results['metrics']['files_with_agents']}")
    print(f"📊 Total Agent Classes: {results['metrics']['total_agents']}")
    print(f"🏗️  Total Classes: {results['metrics']['total_classes']}")
    print(f"⚡ Total Methods: {results['metrics']['total_methods']}")
    print(f"❌ Syntax Errors: {results['metrics']['syntax_errors']}")
    
    print(f"\n📝 Results saved to: {output_file}")
    print("=" * 80)
    
    # Print summary
    summary = results["summary"]
    print("\n📊 Agent Type Distribution:")
    for agent_type, count in summary["agent_types"].items():
        print(f"  • {agent_type}: {count}")
    
    print("\n🔧 Capability Distribution:")
    for capability, count in summary["capabilities"].items():
        print(f"  • {capability}: {count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
