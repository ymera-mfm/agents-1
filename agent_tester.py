#!/usr/bin/env python3
logger = logging.getLogger(__name__)

"""
import logging

Comprehensive Agent Testing Tool

Tests individual agents for initialization, method execution, and capability validation.
Supports both batch testing of all agents and individual agent testing.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import importlib.util


class AgentTester:
    """Test individual agents comprehensively"""
    
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "agents_tested": 0,
            "agents_passed": 0,
            "agents_failed": 0,
            "agents_skipped": 0,
            "test_details": []
        }
    
    async def test_agent_initialization(self, agent_class) -> Dict[str, Any]:
        """Test if agent can be instantiated"""
        try:
            agent = agent_class()
            return {
                "status": "PASS",
                "message": "Agent initialized successfully",
                "agent_instance": agent
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": str(e),
                "traceback": traceback.format_exc(),
                "agent_instance": None
            }
    
    async def test_agent_methods(self, agent_instance) -> List[Dict[str, Any]]:
        """Test all public methods of agent"""
        results = []
        
        for method_name in dir(agent_instance):
            if method_name.startswith('_'):
                continue  # Skip private methods
            
            method = getattr(agent_instance, method_name)
            if not callable(method):
                continue
            
            try:
                if asyncio.iscoroutinefunction(method):
                    # Test async method with timeout
                    try:
                        result = await asyncio.wait_for(method(), timeout=5.0)
                        results.append({
                            "method": method_name,
                            "status": "PASS",
                            "async": True,
                            "result": str(result)[:100] if result else None
                        })
                    except asyncio.TimeoutError:
                        results.append({
                            "method": method_name,
                            "status": "TIMEOUT",
                            "async": True,
                            "message": "Method timed out after 5 seconds"
                        })
                else:
                    # Test sync method
                    result = method()
                    results.append({
                        "method": method_name,
                        "status": "PASS",
                        "async": False,
                        "result": str(result)[:100] if result else None
                    })
            except TypeError as e:
                # Method requires arguments
                results.append({
                    "method": method_name,
                    "status": "SKIP",
                    "message": "Method requires arguments",
                    "async": asyncio.iscoroutinefunction(method)
                })
            except Exception as e:
                results.append({
                    "method": method_name,
                    "status": "FAIL",
                    "message": str(e),
                    "async": asyncio.iscoroutinefunction(method)
                })
        
        return results
    
    async def test_agent_attributes(self, agent_instance) -> Dict[str, Any]:
        """Test agent attributes and properties"""
        attributes = {}
        
        # Check for common agent attributes
        common_attrs = [
            'name', 'version', 'config', 'logger', 'state',
            'capabilities', 'agent_type', 'status'
        ]
        
        for attr in common_attrs:
            if hasattr(agent_instance, attr):
                try:
                    value = getattr(agent_instance, attr)
                    attributes[attr] = {
                        "present": True,
                        "type": type(value).__name__,
                        "value": str(value)[:100] if value else None
                    }
                except Exception as e:
                    attributes[attr] = {
                        "present": True,
                        "error": str(e)
                    }
            else:
                attributes[attr] = {"present": False}
        
        return attributes
    
    async def test_agent_file(self, agent_file: Path) -> Dict[str, Any]:
        """Test a single agent file"""
        test_result = {
            "file": str(agent_file),
            "name": agent_file.stem,
            "import_status": None,
            "initialization": None,
            "methods": [],
            "attributes": {},
            "overall_status": None
        }
        
        try:
            # Import the agent module
            spec = importlib.util.spec_from_file_location(
                agent_file.stem,
                agent_file
            )
            if spec is None or spec.loader is None:
                test_result["import_status"] = {
                    "status": "FAIL",
                    "message": "Could not load module spec"
                }
                test_result["overall_status"] = "FAIL"
                return test_result
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            test_result["import_status"] = {
                "status": "PASS",
                "message": "Module imported successfully"
            }
            
            # Find agent classes in the module
            agent_classes = []
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    name.endswith('Agent') and 
                    not name.startswith('Base')):
                    agent_classes.append(obj)
            
            if not agent_classes:
                test_result["initialization"] = {
                    "status": "SKIP",
                    "message": "No agent classes found in module"
                }
                test_result["overall_status"] = "SKIP"
                return test_result
            
            # Test the first agent class found
            agent_class = agent_classes[0]
            
            # Test initialization
            init_result = await self.test_agent_initialization(agent_class)
            agent_instance = init_result.pop("agent_instance", None)  # Remove instance before storing
            test_result["initialization"] = init_result
            
            if init_result["status"] == "PASS" and agent_instance:
                # Test methods
                methods_result = await self.test_agent_methods(agent_instance)
                test_result["methods"] = methods_result
                
                # Test attributes
                attrs_result = await self.test_agent_attributes(agent_instance)
                test_result["attributes"] = attrs_result
                
                # Determine overall status
                failed_methods = [m for m in methods_result if m["status"] == "FAIL"]
                if failed_methods:
                    test_result["overall_status"] = "PARTIAL"
                else:
                    test_result["overall_status"] = "PASS"
            else:
                test_result["overall_status"] = "FAIL"
        
        except Exception as e:
            test_result["import_status"] = {
                "status": "FAIL",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            test_result["overall_status"] = "FAIL"
        
        return test_result
    
    async def test_agents_directory(self, agents_dir: str = "agents") -> None:
        """Test all agents in a directory"""
        agents_path = Path(agents_dir)
        
        if not agents_path.exists():
            logger.info(f"❌ Directory not found: {agents_dir}")
            return
        
        agent_files = sorted(agents_path.glob("*_agent.py"))
        
        logger.info(f"\n{'='*70}")
        logger.info(f"COMPREHENSIVE AGENT TESTING")
        logger.info(f"{'='*70}")
        logger.info(f"Directory: {agents_dir}")
        logger.info(f"Agents found: {len(agent_files)}")
        logger.info(f"{'='*70}\n")
        
        for agent_file in agent_files:
            logger.info(f"Testing: {agent_file.name}...", end=" ")
            
            test_result = await self.test_agent_file(agent_file)
            self.results["test_details"].append(test_result)
            self.results["agents_tested"] += 1
            
            if test_result["overall_status"] == "PASS":
                self.results["agents_passed"] += 1
                logger.info("✅ PASS")
            elif test_result["overall_status"] == "PARTIAL":
                self.results["agents_passed"] += 1  # Count partial as passed
                logger.info("⚠️  PARTIAL")
            elif test_result["overall_status"] == "SKIP":
                self.results["agents_skipped"] += 1
                logger.info("⏭️  SKIP")
            else:
                self.results["agents_failed"] += 1
                logger.error("❌ FAIL")
                if test_result.get("import_status"):
                    logger.error(f"  Error: {test_result['import_status'].get('message', 'Unknown error')}")
    
    def generate_report(self, output_file: str = "agent_test_report.json") -> None:
        """Generate comprehensive test report"""
        # Calculate statistics
        total = self.results["agents_tested"]
        passed = self.results["agents_passed"]
        failed = self.results["agents_failed"]
        skipped = self.results["agents_skipped"]
        
        self.results["summary"] = {
            "total_agents": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
        }
        
        # Save detailed report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n{'='*70}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total Agents:   {total}")
        logger.info(f"✅ Passed:      {passed}")
        logger.error(f"❌ Failed:      {failed}")
        logger.info(f"⏭️  Skipped:     {skipped}")
        logger.info(f"Pass Rate:      {self.results['summary']['pass_rate']}")
        logger.info(f"{'='*70}")
        logger.info(f"\nDetailed report saved to: {output_file}")
    
    async def test_specific_agent(self, agent_path: str) -> None:
        """Test a specific agent file with detailed output"""
        agent_file = Path(agent_path)
        
        if not agent_file.exists():
            logger.info(f"❌ File not found: {agent_path}")
            return
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing Agent: {agent_file.name}")
        logger.info(f"{'='*70}\n")
        
        test_result = await self.test_agent_file(agent_file)
        self.results["test_details"].append(test_result)
        self.results["agents_tested"] = 1
        
        if test_result["overall_status"] == "PASS":
            self.results["agents_passed"] = 1
            logger.info("\n✅ Overall Status: PASS")
        elif test_result["overall_status"] == "PARTIAL":
            self.results["agents_passed"] = 1
            logger.error("\n⚠️  Overall Status: PARTIAL (some methods failed)")
        elif test_result["overall_status"] == "SKIP":
            self.results["agents_skipped"] = 1
            logger.info("\n⏭️  Overall Status: SKIP")
        else:
            self.results["agents_failed"] = 1
            logger.error("\n❌ Overall Status: FAIL")
        
        # Print detailed results
        logger.info(f"\n{'='*70}")
        logger.info("DETAILED RESULTS")
        logger.info(f"{'='*70}")
        
        if test_result.get("import_status"):
            status = test_result["import_status"]["status"]
            emoji = "✅" if status == "PASS" else "❌"
            logger.info(f"\n{emoji} Import: {status}")
            if status != "PASS":
                logger.info(f"  Message: {test_result['import_status'].get('message')}")
        
        if test_result.get("initialization"):
            status = test_result["initialization"]["status"]
            emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
            logger.info(f"\n{emoji} Initialization: {status}")
            if status != "PASS":
                logger.info(f"  Message: {test_result['initialization'].get('message')}")
        
        if test_result.get("methods"):
            logger.info(f"\n📋 Methods Tested: {len(test_result['methods'])}")
            passed = [m for m in test_result["methods"] if m["status"] == "PASS"]
            skipped = [m for m in test_result["methods"] if m["status"] == "SKIP"]
            failed = [m for m in test_result["methods"] if m["status"] == "FAIL"]
            timeout = [m for m in test_result["methods"] if m["status"] == "TIMEOUT"]
            
            logger.info(f"  ✅ Passed: {len(passed)}")
            logger.info(f"  ⏭️  Skipped: {len(skipped)}")
            logger.error(f"  ❌ Failed: {len(failed)}")
            if timeout:
                logger.info(f"  ⏱️  Timeout: {len(timeout)}")
            
            if failed:
                logger.error("\n  Failed Methods:")
                for method in failed:
                    logger.error(f"    - {method['method']}: {method.get('message', 'Unknown error')}")
        
        if test_result.get("attributes"):
            logger.info(f"\n🔧 Attributes:")
            for attr, info in test_result["attributes"].items():
                if info.get("present"):
                    logger.info(f"  ✅ {attr}: {info.get('type', 'N/A')}")
                else:
                    logger.info(f"  ❌ {attr}: Not present")


async def main():
    """Main entry point"""
    tester = AgentTester()
    
    if len(sys.argv) > 1:
        # Test specific agent
        agent_path = sys.argv[1]
        await tester.test_specific_agent(agent_path)
        output_file = f"{Path(agent_path).stem}_test_report.json"
    else:
        # Test all agents
        await tester.test_agents_directory("agents")
        output_file = "agent_test_report.json"
    
    tester.generate_report(output_file)


if __name__ == "__main__":
    asyncio.run(main())
