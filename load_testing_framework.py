#!/usr/bin/env python3
"""
Load Testing Framework for Agents
Tests agent performance under realistic concurrent loads
"""

import asyncio
import time
import statistics
import json
from datetime import datetime
from typing import Dict, List, Any, Callable
from pathlib import Path
import importlib.util
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


class AgentLoadTester:
    """Load testing framework for agents"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "max_workers": max_workers,
            "load_tests": []
        }
    
    def load_agent_module(self, file_path: str, agent_name: str):
        """Dynamically load an agent module"""
        try:
            if not Path(file_path).is_absolute():
                file_path = str(Path.cwd() / file_path)
            
            if not Path(file_path).exists():
                return None
            
            spec = importlib.util.spec_from_file_location(agent_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[agent_name] = module
                spec.loader.exec_module(module)
                return module
        except Exception:
            return None
        return None
    
    def find_agent_class(self, module, agent_name: str):
        """Find the main agent class in a module"""
        possible_names = [
            agent_name,
            agent_name.replace('_', ''),
            ''.join(word.capitalize() for word in agent_name.split('_')),
        ]
        
        for name in possible_names:
            if hasattr(module, name):
                return getattr(module, name)
        
        # Try to find any class that looks like an agent
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and 'agent' in attr_name.lower():
                return attr
        
        return None
    
    def _worker_task(self, agent_class, task_id: int) -> Dict[str, Any]:
        """Single worker task for load testing"""
        start = time.perf_counter()
        try:
            # Create agent instance
            agent = agent_class()
            
            # Try to execute a simple operation if available
            if hasattr(agent, 'process'):
                if asyncio.iscoroutinefunction(agent.process):
                    asyncio.run(agent.process())
                else:
                    agent.process()
            
            # Cleanup
            if hasattr(agent, 'cleanup'):
                if asyncio.iscoroutinefunction(agent.cleanup):
                    asyncio.run(agent.cleanup())
                else:
                    agent.cleanup()
            
            end = time.perf_counter()
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "duration_ms": (end - start) * 1000
            }
        except Exception as e:
            end = time.perf_counter()
            return {
                "task_id": task_id,
                "status": "FAILED",
                "duration_ms": (end - start) * 1000,
                "error": str(e)[:100]
            }
    
    def load_test_agent(
        self, 
        agent_class, 
        agent_name: str,
        num_requests: int = 100,
        concurrent_workers: int = None
    ) -> Dict[str, Any]:
        """
        Load test a single agent with concurrent requests
        
        Args:
            agent_class: The agent class to test
            agent_name: Name of the agent
            num_requests: Total number of requests to make
            concurrent_workers: Number of concurrent workers (default: self.max_workers)
        """
        if concurrent_workers is None:
            concurrent_workers = self.max_workers
        
        print(f"Load testing {agent_name}...")
        print(f"  Requests: {num_requests}, Workers: {concurrent_workers}")
        
        results = {
            "agent_name": agent_name,
            "num_requests": num_requests,
            "concurrent_workers": concurrent_workers,
            "timestamp": datetime.now().isoformat()
        }
        
        task_results = []
        start_time = time.perf_counter()
        
        # Execute load test with thread pool
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = [
                executor.submit(self._worker_task, agent_class, i)
                for i in range(num_requests)
            ]
            
            for future in as_completed(futures):
                task_results.append(future.result())
        
        end_time = time.perf_counter()
        total_duration = end_time - start_time
        
        # Analyze results
        successful = [r for r in task_results if r["status"] == "SUCCESS"]
        failed = [r for r in task_results if r["status"] == "FAILED"]
        
        if successful:
            durations = [r["duration_ms"] for r in successful]
            
            results["status"] = "SUCCESS"
            results["performance"] = {
                "total_duration_s": round(total_duration, 2),
                "requests_per_second": round(num_requests / total_duration, 2),
                "successful_requests": len(successful),
                "failed_requests": len(failed),
                "success_rate": round(len(successful) / num_requests * 100, 2),
                "latency": {
                    "mean_ms": round(statistics.mean(durations), 2),
                    "median_ms": round(statistics.median(durations), 2),
                    "p95_ms": round(
                        statistics.quantiles(durations, n=20)[18] if len(durations) >= 20
                        else sorted(durations)[max(0, int(0.95 * len(durations)) - 1)]
                    , 2),
                    "p99_ms": round(
                        statistics.quantiles(durations, n=100)[98] if len(durations) >= 100
                        else sorted(durations)[max(0, int(0.99 * len(durations)) - 1)]
                    , 2),
                    "min_ms": round(min(durations), 2),
                    "max_ms": round(max(durations), 2)
                }
            }
            
            # Performance degradation analysis
            # Compare first 10% vs last 10% to detect degradation
            first_batch = durations[:max(1, len(durations) // 10)]
            last_batch = durations[-max(1, len(durations) // 10):]
            
            first_avg = statistics.mean(first_batch)
            last_avg = statistics.mean(last_batch)
            degradation_pct = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            
            results["performance"]["degradation"] = {
                "first_batch_avg_ms": round(first_avg, 2),
                "last_batch_avg_ms": round(last_avg, 2),
                "degradation_pct": round(degradation_pct, 2),
                "has_degradation": degradation_pct > 10  # Flag if >10% degradation
            }
            
            print(f"  ✅ {len(successful)}/{num_requests} successful")
            print(f"  ⚡ {results['performance']['requests_per_second']:.1f} req/s")
            print(f"  📊 Latency: {results['performance']['latency']['median_ms']:.2f}ms (p50)")
            
            if results["performance"]["degradation"]["has_degradation"]:
                print(f"  ⚠️  Performance degraded by {degradation_pct:.1f}%")
        else:
            results["status"] = "FAILED"
            results["error"] = f"All {num_requests} requests failed"
            print(f"  ❌ All requests failed")
        
        return results
    
    def run_load_tests(
        self, 
        test_results_file: str = "agent_test_results_complete.json",
        num_requests: int = 100,
        concurrent_workers: int = None,
        max_agents: int = 10
    ):
        """
        Run load tests on passing agents
        
        Args:
            test_results_file: Path to test results JSON
            num_requests: Number of requests per agent
            concurrent_workers: Number of concurrent workers
            max_agents: Maximum number of agents to test
        """
        if concurrent_workers is None:
            concurrent_workers = self.max_workers
        
        print("=" * 70)
        print("AGENT LOAD TESTING")
        print("=" * 70)
        print(f"Requests per agent: {num_requests}")
        print(f"Concurrent workers: {concurrent_workers}")
        print()
        
        # Load test results
        with open(test_results_file, 'r') as f:
            test_data = json.load(f)
        
        test_results = test_data.get('test_results', [])
        passing_agents = [
            result for result in test_results 
            if result.get('status') == 'PASS'
        ]
        
        # Limit to max_agents
        agents_to_test = passing_agents[:max_agents]
        
        print(f"Testing {len(agents_to_test)} agents (of {len(passing_agents)} passing)")
        print()
        
        # Test each agent
        for i, agent_info in enumerate(agents_to_test, 1):
            file_path = agent_info.get('file', '')
            agent_classes = agent_info.get('agent_classes', [])
            agent_name = agent_classes[0] if agent_classes else 'Unknown'
            
            print(f"[{i}/{len(agents_to_test)}] {agent_name}")
            
            try:
                # Load agent
                module = self.load_agent_module(file_path, agent_name)
                if not module:
                    print(f"  ❌ Could not load module")
                    continue
                
                agent_class = self.find_agent_class(module, agent_name)
                if not agent_class:
                    print(f"  ❌ Could not find agent class")
                    continue
                
                # Run load test
                result = self.load_test_agent(
                    agent_class, 
                    agent_name,
                    num_requests=num_requests,
                    concurrent_workers=concurrent_workers
                )
                self.results["load_tests"].append(result)
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)[:100]}")
                self.results["load_tests"].append({
                    "agent_name": agent_name,
                    "status": "ERROR",
                    "error": str(e)[:200]
                })
            
            print()
        
        # Calculate summary
        successful_tests = [t for t in self.results["load_tests"] if t.get("status") == "SUCCESS"]
        
        if successful_tests:
            self.results["summary"] = {
                "total_agents_tested": len(self.results["load_tests"]),
                "successful_tests": len(successful_tests),
                "failed_tests": len(self.results["load_tests"]) - len(successful_tests),
                "avg_requests_per_second": round(
                    statistics.mean([t["performance"]["requests_per_second"] for t in successful_tests]), 2
                ),
                "agents_with_degradation": sum(
                    1 for t in successful_tests 
                    if t.get("performance", {}).get("degradation", {}).get("has_degradation", False)
                )
            }
        
        # Save results
        output_file = "agent_load_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print("=" * 70)
        print("LOAD TEST SUMMARY:")
        if successful_tests:
            summary = self.results["summary"]
            print(f"  Tests completed: {summary['successful_tests']}/{summary['total_agents_tested']}")
            print(f"  Avg throughput: {summary['avg_requests_per_second']:.1f} req/s")
            
            if summary["agents_with_degradation"] > 0:
                print(f"  ⚠️  Agents with degradation: {summary['agents_with_degradation']}")
        else:
            print("  No successful tests")
        
        print()
        print(f"✅ Results saved to: {output_file}")
        print("=" * 70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test agents")
    parser.add_argument('--requests', type=int, default=100,
                       help='Number of requests per agent (default: 100)')
    parser.add_argument('--workers', type=int, default=10,
                       help='Number of concurrent workers (default: 10)')
    parser.add_argument('--max-agents', type=int, default=10,
                       help='Maximum number of agents to test (default: 10)')
    args = parser.parse_args()
    
    tester = AgentLoadTester(max_workers=args.workers)
    tester.run_load_tests(
        num_requests=args.requests,
        concurrent_workers=args.workers,
        max_agents=args.max_agents
    )


if __name__ == "__main__":
    main()
