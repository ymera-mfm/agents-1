#!/usr/bin/env python3
"""
Performance Benchmark Script
Can be re-run to measure system performance
"""

import asyncio
import time
import httpx
import psutil
from typing import Dict, List, Any


async def benchmark_api_endpoint(endpoint: str, method: str = "GET") -> Dict[str, Any]:
    """Benchmark a single API endpoint"""
    times = []
    
    async with httpx.AsyncClient() as client:
        # Warmup
        for _ in range(5):
            try:
                await client.request(method, endpoint, timeout=5.0)
            except:
                pass
        
        # Measure
        for _ in range(100):
            start = time.perf_counter()
            try:
                response = await client.request(method, endpoint, timeout=5.0)
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
            except Exception as e:
                print(f"Error: {e}")
    
    if times:
        times.sort()
        return {
            "endpoint": endpoint,
            "avg_response_time_ms": sum(times) / len(times),
            "p50_ms": times[len(times) // 2],
            "p95_ms": times[int(len(times) * 0.95)],
            "p99_ms": times[int(len(times) * 0.99)],
        }
    return {"endpoint": endpoint, "error": "No successful requests"}


async def main():
    """Run all benchmarks"""
    print("Starting performance benchmarks...")
    
    # Benchmark API endpoints
    endpoints = [
        "http://localhost:8000/health",
        "http://localhost:8000/api/v1/agents",
    ]
    
    for endpoint in endpoints:
        result = await benchmark_api_endpoint(endpoint)
        print(f"Endpoint: {result['endpoint']}")
        if 'avg_response_time_ms' in result:
            print(f"  Avg: {result.get('avg_response_time_ms', 'N/A')}ms")
    
    # Memory usage
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"\nMemory Usage: {memory_mb:.2f} MB")


if __name__ == "__main__":
    asyncio.run(main())
