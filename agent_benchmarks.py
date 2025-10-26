# agent_benchmarks.py
import asyncio
import time
import json
import statistics
from datetime import datetime
import psutil
import os
import sys
import importlib.util


class AgentBenchmark:
    """Benchmark agent performance"""
    
    def __init__(self):
        self.results = {
            "benchmark_timestamp": datetime.now().isoformat(),
            "system_info": self.get_system_info(),
            "agent_benchmarks": []
        }
    
    def get_system_info(self):
        """Get system specifications"""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "python_version": sys.version
        }
    
    async def benchmark_agent_initialization(self, agent_class, iterations=100):
        """Measure agent initialization time"""
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                agent = agent_class()
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms
            except Exception as e:
                return {
                    "status": "FAIL",
                    "error": str(e)
                }
        
        return {
            "status": "PASS",
            "iterations": iterations,
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0
        }

    async def benchmark_agent_operation(self, agent_instance, method_name, iterations=50):
        """Benchmark a specific agent operation"""
        times = []
        memory_before = []
        memory_after = []
        
        process = psutil.Process(os.getpid())
        
        for _ in range(iterations):
            # Measure memory before
            memory_before.append(process.memory_info().rss / 1024 / 1024)  # MB
            
            start = time.perf_counter()
            try:
                method = getattr(agent_instance, method_name)
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
                end = time.perf_counter()
                times.append((end - start) * 1000)  # ms
            except TypeError:
                # Method needs arguments - skip
                return {"status": "SKIP", "reason": "Requires arguments"}
            except Exception as e:
                return {"status": "FAIL", "error": str(e)}
            
            # Measure memory after
            memory_after.append(process.memory_info().rss / 1024 / 1024)  # MB
        
        memory_delta = [after - before for before, after in zip(memory_before, memory_after)]
        
        return {
            "status": "PASS",
            "iterations": iterations,
            "timing": {
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "p50_ms": statistics.median(times),
                "p95_ms": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                "p99_ms": statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0
            },
            "memory": {
                "mean_delta_mb": statistics.mean(memory_delta),
                "max_delta_mb": max(memory_delta),
                "leaked": any(d > 1 for d in memory_delta)  # Flag if >1MB increase
            }
        }

    async def benchmark_agent_comprehensive(self, agent_class, agent_name):
        """Complete benchmark for a single agent"""
        
        benchmark = {
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat(),
            "initialization": None,
            "operations": {}
        }
        
        try:
            # Benchmark initialization
            print(f"  Benchmarking initialization...")
            benchmark["initialization"] = await self.benchmark_agent_initialization(agent_class)
            
            if benchmark["initialization"]["status"] == "PASS":
                # Create instance for operation benchmarks
                agent_instance = agent_class()
                
                # Find and benchmark public methods
                methods = [m for m in dir(agent_instance) if not m.startswith('_') and callable(getattr(agent_instance, m))]
                
                for method_name in methods[:10]:  # Benchmark first 10 methods
                    print(f"  Benchmarking {method_name}...")
                    result = await self.benchmark_agent_operation(agent_instance, method_name)
                    benchmark["operations"][method_name] = result
            
            # Calculate overall performance score
            if benchmark["initialization"]["status"] == "PASS":
                init_time = benchmark["initialization"]["mean_ms"]
                if init_time < 10:
                    score = "EXCELLENT"
                elif init_time < 50:
                    score = "GOOD"
                elif init_time < 100:
                    score = "ACCEPTABLE"
                else:
                    score = "SLOW"
                
                benchmark["performance_score"] = score
                benchmark["status"] = "COMPLETE"
            else:
                benchmark["status"] = "FAILED"
        
        except Exception as e:
            benchmark["status"] = "ERROR"
            benchmark["error"] = str(e)
        
        return benchmark

    async def benchmark_all_agents(self, working_agents):
        """Benchmark all working agents"""
        
        print("Starting Agent Performance Benchmarking...")
        print("=" * 60)
        
        for agent_info in working_agents:
            agent_file = agent_info if isinstance(agent_info, str) else agent_info.get("file")
            
            print(f"\nBenchmarking: {agent_file}")
            
            try:
                # Import agent
                spec = importlib.util.spec_from_file_location("agent_module", agent_file)
                agent_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agent_module)
                
                # Find agent classes
                agent_classes = [
                    (name, getattr(agent_module, name))
                    for name in dir(agent_module)
                    if isinstance(getattr(agent_module, name), type)
                    and name.endswith('Agent')
                ]
                
                for agent_name, agent_class in agent_classes:
                    benchmark = await self.benchmark_agent_comprehensive(agent_class, agent_name)
                    self.results["agent_benchmarks"].append(benchmark)
                    
                    if benchmark["status"] == "COMPLETE":
                        score = benchmark.get("performance_score", "UNKNOWN")
                        print(f"  ✅ {agent_name}: {score}")
                    else:
                        print(f"  ❌ {agent_name}: {benchmark['status']}")
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
                self.results["agent_benchmarks"].append({
                    "agent_file": agent_file,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        # Calculate summary statistics
        successful = [b for b in self.results["agent_benchmarks"] if b["status"] == "COMPLETE"]
        if successful:
            init_times = [b["initialization"]["mean_ms"] for b in successful]
            self.results["summary"] = {
                "total_benchmarked": len(self.results["agent_benchmarks"]),
                "successful": len(successful),
                "failed": len(self.results["agent_benchmarks"]) - len(successful),
                "average_init_time_ms": statistics.mean(init_times),
                "fastest_init_ms": min(init_times),
                "slowest_init_ms": max(init_times),
                "performance_distribution": {
                    "excellent": sum(1 for b in successful if b.get("performance_score") == "EXCELLENT"),
                    "good": sum(1 for b in successful if b.get("performance_score") == "GOOD"),
                    "acceptable": sum(1 for b in successful if b.get("performance_score") == "ACCEPTABLE"),
                    "slow": sum(1 for b in successful if b.get("performance_score") == "SLOW")
                }
            }
        
        # Save results
        with open('agent_benchmarks_complete.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.results


async def main():
    # Load working agents from test results
    with open('agent_test_analysis.json', 'r') as f:
        analysis = json.load(f)
    working_agents = analysis["working_agents"]

    if not working_agents:
        print("No working agents found to benchmark!")
        return

    benchmarker = AgentBenchmark()
    results = await benchmarker.benchmark_all_agents(working_agents)

    print("\n" + "=" * 60)
    print("BENCHMARKING COMPLETE")
    print("=" * 60)
    if "summary" in results:
        summary = results["summary"]
        print(f"Agents Benchmarked: {summary['total_benchmarked']}")
        print(f"Successful: {summary['successful']}")
        print(f"Average Init Time: {summary['average_init_time_ms']:.2f}ms")
        print(f"Performance Distribution:")
        perf = summary['performance_distribution']
        print(f"  Excellent: {perf['excellent']}")
        print(f"  Good: {perf['good']}")
        print(f"  Acceptable: {perf['acceptable']}")
        print(f"  Slow: {perf['slow']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
