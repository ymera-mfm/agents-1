#!/usr/bin/env python3
"""
Complete Agent Benchmarking System
Benchmarks all operational agents with MEASURED performance data
"""

import json
import time
import statistics
import asyncio
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import importlib.util
import sys


class ComprehensiveAgentBenchmark:
    """Benchmark all operational agents"""
    
    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results = {
            "benchmark_timestamp": datetime.now().isoformat(),
            "iterations_per_agent": iterations,
            "measurement_method": "Performance timing with statistics.median/quantiles",
            "benchmarks": []
        }
        self.benchmarked_count = 0
        self.failed_count = 0
    
    def load_agent_module(self, file_path: str, agent_name: str):
        """Dynamically load an agent module"""
        try:
            # Make sure file_path is absolute
            from pathlib import Path
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
        except Exception as e:
            return None
        return None
    
    def find_agent_class(self, module, agent_name: str):
        """Find the main agent class in a module"""
        # Common agent class name patterns
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
    
    def benchmark_initialization(self, agent_class) -> Dict[str, Any]:
        """Benchmark agent initialization time with memory tracking"""
        times = []
        memory_before = []
        memory_after = []
        
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            has_psutil = True
        except:
            has_psutil = False
        
        for _ in range(self.iterations):
            if has_psutil:
                memory_before.append(process.memory_info().rss / 1024 / 1024)  # MB
            
            start = time.perf_counter()
            try:
                # Try to instantiate agent
                agent = agent_class()
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms
                
                if has_psutil:
                    memory_after.append(process.memory_info().rss / 1024 / 1024)  # MB
                
                # Clean up
                if hasattr(agent, 'cleanup'):
                    try:
                        if asyncio.iscoroutinefunction(agent.cleanup):
                            asyncio.run(agent.cleanup())
                        else:
                            agent.cleanup()
                    except:
                        pass
            except Exception as e:
                # If init fails, record it but continue
                return {
                    "status": "FAILED",
                    "error": str(e)[:200],
                    "iterations_completed": len(times)
                }
        
        if not times:
            return {"status": "FAILED", "error": "No successful iterations"}
        
        result = {
            "status": "SUCCESS",
            "iterations": len(times),
            "initialization": {
                "mean_ms": round(statistics.mean(times), 2),
                "median_ms": round(statistics.median(times), 2),
                "p50_ms": round(statistics.median(times), 2),
                "p95_ms": round(statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times), 2),
                "p99_ms": round(statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times), 2),
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2),
                "std_dev_ms": round(statistics.stdev(times) if len(times) > 1 else 0, 2)
            }
        }
        
        # Add memory statistics if available
        if has_psutil and memory_before and memory_after:
            memory_delta = [after - before for before, after in zip(memory_before, memory_after)]
            result["memory"] = {
                "mean_delta_mb": round(statistics.mean(memory_delta), 2),
                "median_delta_mb": round(statistics.median(memory_delta), 2),
                "max_delta_mb": round(max(memory_delta), 2),
                "min_delta_mb": round(min(memory_delta), 2),
                "leaked": any(d > 1 for d in memory_delta)  # Flag if >1MB increase
            }
        
        return result
    
    def benchmark_operations(self, agent_instance, operation_iterations: int = 50) -> Dict[str, Any]:
        """Benchmark agent operations/methods"""
        operations = {}
        
        # Find public methods to benchmark
        methods = [
            m for m in dir(agent_instance) 
            if not m.startswith('_') 
            and callable(getattr(agent_instance, m))
            and m not in ['cleanup', 'initialize']  # Skip special methods
        ]
        
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            has_psutil = True
        except:
            has_psutil = False
        
        # Benchmark up to 5 methods to keep execution time reasonable
        for method_name in methods[:5]:
            times = []
            memory_before = []
            memory_after = []
            errors = 0
            
            for _ in range(operation_iterations):
                try:
                    if has_psutil:
                        memory_before.append(process.memory_info().rss / 1024 / 1024)
                    
                    method = getattr(agent_instance, method_name)
                    start = time.perf_counter()
                    
                    # Handle async methods
                    if asyncio.iscoroutinefunction(method):
                        asyncio.run(method())
                    else:
                        method()
                    
                    end = time.perf_counter()
                    times.append((end - start) * 1000)
                    
                    if has_psutil:
                        memory_after.append(process.memory_info().rss / 1024 / 1024)
                except TypeError:
                    # Method requires arguments - skip
                    operations[method_name] = {"status": "SKIP", "reason": "Requires arguments"}
                    break
                except Exception as e:
                    errors += 1
                    if errors >= 3:  # Stop after 3 consecutive errors
                        operations[method_name] = {"status": "FAIL", "error": str(e)[:100]}
                        break
            
            if times:
                op_result = {
                    "status": "SUCCESS",
                    "iterations": len(times),
                    "timing": {
                        "mean_ms": round(statistics.mean(times), 2),
                        "median_ms": round(statistics.median(times), 2),
                        "p95_ms": round(statistics.quantiles(times, n=100)[94] if len(times) >= 100 else max(times), 2),
                        "min_ms": round(min(times), 2),
                        "max_ms": round(max(times), 2)
                    }
                }
                
                if has_psutil and memory_before and memory_after:
                    memory_delta = [after - before for before, after in zip(memory_before, memory_after)]
                    op_result["memory"] = {
                        "mean_delta_mb": round(statistics.mean(memory_delta), 2),
                        "max_delta_mb": round(max(memory_delta), 2)
                    }
                
                operations[method_name] = op_result
        
        return operations
    
    def benchmark_agent(self, agent_info: Dict[str, Any], benchmark_operations: bool = True) -> Dict[str, Any]:
        """Benchmark a single agent"""
        # Extract info from test result structure
        file_path = agent_info.get('file', '')
        agent_classes = agent_info.get('agent_classes', [])
        agent_name = agent_classes[0] if agent_classes else 'Unknown'
        
        result = {
            "agent_name": agent_name,
            "file": file_path,
            "benchmark_timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Load module
            module = self.load_agent_module(file_path, agent_name)
            if not module:
                result["status"] = "FAILED"
                result["error"] = "Could not load module"
                return result
            
            # Find agent class
            agent_class = self.find_agent_class(module, agent_name)
            if not agent_class:
                result["status"] = "FAILED"
                result["error"] = "Could not find agent class"
                return result
            
            # Benchmark initialization
            benchmark_result = self.benchmark_initialization(agent_class)
            result.update(benchmark_result)
            
            # Benchmark operations if initialization succeeded
            if result["status"] == "SUCCESS" and benchmark_operations:
                try:
                    agent_instance = agent_class()
                    operations = self.benchmark_operations(agent_instance, operation_iterations=50)
                    if operations:
                        result["operations"] = operations
                    
                    # Cleanup
                    if hasattr(agent_instance, 'cleanup'):
                        try:
                            if asyncio.iscoroutinefunction(agent_instance.cleanup):
                                asyncio.run(agent_instance.cleanup())
                            else:
                                agent_instance.cleanup()
                        except:
                            pass
                except Exception as e:
                    result["operations_error"] = str(e)[:200]
            
            if result["status"] == "SUCCESS":
                self.benchmarked_count += 1
            else:
                self.failed_count += 1
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)[:200]
            self.failed_count += 1
        
        return result
    
    def run_benchmarks(self, test_results_file: str = "agent_test_results_complete.json", benchmark_operations: bool = True):
        """Run benchmarks on all agents that passed tests"""
        print("=" * 70)
        print("COMPREHENSIVE AGENT BENCHMARKING")
        print("=" * 70)
        print(f"Iterations per agent: {self.iterations}")
        print(f"Benchmark operations: {'Yes' if benchmark_operations else 'No (initialization only)'}")
        print()
        
        # Load test results to find passing agents
        with open(test_results_file, 'r') as f:
            test_data = json.load(f)
        
        test_results = test_data.get('test_results', [])
        
        # Filter to only agents that passed tests
        passing_agents = [
            result for result in test_results 
            if result.get('status') == 'PASS'
        ]
        
        total = len(passing_agents)
        print(f"Found {total} passing agents to benchmark")
        print()
        
        # Benchmark each agent
        for i, agent_info in enumerate(passing_agents, 1):
            agent_classes = agent_info.get('agent_classes', [])
            agent_name = agent_classes[0] if agent_classes else 'Unknown'
            print(f"[{i}/{total}] Benchmarking {agent_name}...", end=" ", flush=True)
            
            benchmark_result = self.benchmark_agent(agent_info, benchmark_operations=benchmark_operations)
            self.results["benchmarks"].append(benchmark_result)
            
            if benchmark_result.get("status") == "SUCCESS":
                init_time = benchmark_result.get("initialization", {}).get("median_ms", 0)
                ops_count = len(benchmark_result.get("operations", {}))
                print(f"✅ {init_time:.2f}ms init, {ops_count} ops")
            else:
                error = benchmark_result.get("error", "Unknown error")
                print(f"❌ {error[:50]}")
        
        # Calculate summary statistics
        successful = [b for b in self.results["benchmarks"] if b.get("status") == "SUCCESS"]
        
        if successful:
            # Initialization stats
            init_times = [b["initialization"]["median_ms"] for b in successful]
            
            # Operation stats
            ops_benchmarked = sum(1 for b in successful if "operations" in b)
            total_operations = sum(len(b.get("operations", {})) for b in successful)
            
            # Memory leak detection
            memory_leaks = []
            for b in successful:
                if b.get("memory", {}).get("leaked"):
                    memory_leaks.append(b["agent_name"])
                for op_name, op_data in b.get("operations", {}).items():
                    if isinstance(op_data, dict) and op_data.get("memory", {}).get("mean_delta_mb", 0) > 1:
                        memory_leaks.append(f"{b['agent_name']}.{op_name}")
            
            self.results["summary"] = {
                "total_agents_benchmarked": total,
                "successful_benchmarks": self.benchmarked_count,
                "failed_benchmarks": self.failed_count,
                "success_rate": f"{(self.benchmarked_count/total*100) if total > 0 else 0:.2f}%",
                "initialization": {
                    "mean_ms": round(statistics.mean(init_times), 2),
                    "median_ms": round(statistics.median(init_times), 2),
                    "fastest_ms": round(min(init_times), 2),
                    "slowest_ms": round(max(init_times), 2)
                },
                "operations": {
                    "agents_with_ops": ops_benchmarked,
                    "total_operations": total_operations,
                    "avg_ops_per_agent": round(total_operations / ops_benchmarked, 1) if ops_benchmarked > 0 else 0
                },
                "memory": {
                    "potential_leaks": len(memory_leaks),
                    "leaky_components": memory_leaks[:10] if memory_leaks else []
                }
            }
        else:
            self.results["summary"] = {
                "total_agents_benchmarked": total,
                "successful_benchmarks": 0,
                "failed_benchmarks": total,
                "success_rate": "0.00%"
            }
        
        # Save results
        output_file = "agent_benchmarks_complete.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print()
        print("=" * 70)
        print("BENCHMARK SUMMARY:")
        print(f"  Successful: {self.benchmarked_count}/{total}")
        print(f"  Failed: {self.failed_count}/{total}")
        print(f"  Success Rate: {self.results['summary']['success_rate']}")
        
        if successful:
            summary = self.results["summary"]
            print(f"\nInitialization Performance:")
            print(f"  Median: {summary['initialization']['median_ms']}ms")
            print(f"  Range: {summary['initialization']['fastest_ms']}ms - {summary['initialization']['slowest_ms']}ms")
            
            if benchmark_operations and summary["operations"]["total_operations"] > 0:
                print(f"\nOperation Benchmarking:")
                print(f"  Agents with operations: {summary['operations']['agents_with_ops']}")
                print(f"  Total operations: {summary['operations']['total_operations']}")
                print(f"  Avg ops/agent: {summary['operations']['avg_ops_per_agent']}")
            
            if summary["memory"]["potential_leaks"]:
                print(f"\n⚠️  Memory Concerns:")
                print(f"  Potential leaks detected: {summary['memory']['potential_leaks']}")
                for leak in summary["memory"]["leaky_components"][:5]:
                    print(f"    - {leak}")
        
        print()
        print(f"✅ Results saved to: {output_file}")
        print("=" * 70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark all operational agents")
    parser.add_argument('--iterations', type=int, default=100,
                       help='Number of iterations per agent (default: 100)')
    parser.add_argument('--operations', action='store_true',
                       help='Benchmark operations in addition to initialization')
    parser.add_argument('--init-only', action='store_true',
                       help='Benchmark initialization only (skip operations)')
    args = parser.parse_args()
    
    benchmark_ops = args.operations and not args.init_only
    
    benchmark = ComprehensiveAgentBenchmark(iterations=args.iterations)
    benchmark.run_benchmarks(benchmark_operations=benchmark_ops)


if __name__ == "__main__":
    main()
