# benchmark_report_generator.py
import json


def generate_performance_report():
    """Create human-readable performance report"""
    
    with open('agent_benchmarks_complete.json', 'r') as f:
        benchmarks = json.load(f)
    
    report_lines = []
    report_lines.append("# Agent Performance Benchmark Report")
    report_lines.append("")
    report_lines.append(f"**Benchmark Date:** {benchmarks['benchmark_timestamp']}")
    report_lines.append("")
    
    # System info
    report_lines.append("## Test Environment")
    sys_info = benchmarks['system_info']
    report_lines.append(f"- CPU Cores: {sys_info['cpu_count']}")
    report_lines.append(f"- Memory: {sys_info['memory_total_gb']:.1f} GB")
    report_lines.append(f"- Python: {sys_info['python_version'].split()[0]}")
    report_lines.append("")
    
    # Summary
    if "summary" in benchmarks:
        summary = benchmarks["summary"]
        report_lines.append("## Summary Statistics")
        report_lines.append("")
        report_lines.append(f"- **Total Agents Benchmarked:** {summary['total_benchmarked']}")
        report_lines.append(f"- **Successful Benchmarks:** {summary['successful']}")
        report_lines.append(f"- **Failed Benchmarks:** {summary['failed']}")
        report_lines.append(f"- **Average Initialization Time:** {summary['average_init_time_ms']:.2f}ms")
        report_lines.append(f"- **Fastest Initialization:** {summary['fastest_init_ms']:.2f}ms")
        report_lines.append(f"- **Slowest Initialization:** {summary['slowest_init_ms']:.2f}ms")
        report_lines.append("")
        
        # Performance distribution
        report_lines.append("### Performance Distribution")
        perf = summary['performance_distribution']
        total = sum(perf.values())
        report_lines.append("")
        report_lines.append("| Rating | Count | Percentage |")
        report_lines.append("|--------|-------|------------|")
        for rating, count in perf.items():
            pct = (count / total * 100) if total > 0 else 0
            report_lines.append(f"| {rating.title()} | {count} | {pct:.1f}% |")
        report_lines.append("")
    
    # Detailed results
    report_lines.append("## Detailed Results")
    report_lines.append("")
    
    successful_benchmarks = [b for b in benchmarks['agent_benchmarks'] if b['status'] == 'COMPLETE']
    
    if successful_benchmarks:
        report_lines.append("### Initialization Performance")
        report_lines.append("")
        report_lines.append("| Agent | Mean (ms) | Median (ms) | Min (ms) | Max (ms) | Score |")
        report_lines.append("|-------|-----------|-------------|----------|----------|-------|")
        
        for bench in sorted(successful_benchmarks, key=lambda x: x['initialization']['mean_ms']):
            init = bench['initialization']
            name = bench['agent_name']
            score = bench.get('performance_score', 'N/A')
            report_lines.append(
                f"| {name} | {init['mean_ms']:.2f} | {init['median_ms']:.2f} | "
                f"{init['min_ms']:.2f} | {init['max_ms']:.2f} | {score} |"
            )
        report_lines.append("")
        
        # Operation benchmarks
        report_lines.append("### Operation Performance (Selected Methods)")
        report_lines.append("")
        
        for bench in successful_benchmarks[:5]:  # Show top 5
            if bench['operations']:
                report_lines.append(f"#### {bench['agent_name']}")
                report_lines.append("")
                report_lines.append("| Method | P50 (ms) | P95 (ms) | P99 (ms) | Memory Delta (MB) |")
                report_lines.append("|--------|----------|----------|----------|-------------------|")
                
                for method, result in bench['operations'].items():
                    if result['status'] == 'PASS':
                        timing = result['timing']
                        memory = result['memory']
                        report_lines.append(
                            f"| {method} | {timing['p50_ms']:.2f} | {timing['p95_ms']:.2f} | "
                            f"{timing['p99_ms']:.2f} | {memory['mean_delta_mb']:.2f} |"
                        )
                report_lines.append("")
    
    # Failed benchmarks
    failed_benchmarks = [b for b in benchmarks['agent_benchmarks'] if b['status'] != 'COMPLETE']
    if failed_benchmarks:
        report_lines.append("### Failed Benchmarks")
        report_lines.append("")
        report_lines.append("| Agent | Status | Error |")
        report_lines.append("|-------|--------|-------|")
        for bench in failed_benchmarks:
            name = bench.get('agent_name', bench.get('agent_file', 'Unknown'))
            status = bench['status']
            error = bench.get('error', 'N/A')[:50]  # Truncate long errors
            report_lines.append(f"| {name} | {status} | {error} |")
        report_lines.append("")
    
    # Performance insights
    report_lines.append("## Performance Insights")
    report_lines.append("")
    
    if "summary" in benchmarks and successful_benchmarks:
        avg_time = benchmarks["summary"]["average_init_time_ms"]
        
        if avg_time < 10:
            report_lines.append("✅ **Overall Performance: EXCELLENT**")
            report_lines.append("- Average initialization time is very fast (<10ms)")
        elif avg_time < 50:
            report_lines.append("✅ **Overall Performance: GOOD**")
            report_lines.append("- Average initialization time is acceptable (10-50ms)")
        elif avg_time < 100:
            report_lines.append("⚠️ **Overall Performance: ACCEPTABLE**")
            report_lines.append("- Average initialization time could be improved (50-100ms)")
        else:
            report_lines.append("❌ **Overall Performance: NEEDS IMPROVEMENT**")
            report_lines.append("- Average initialization time is slow (>100ms)")
        
        report_lines.append("")
        
        # Memory leaks
        memory_leaks = [
            b for b in successful_benchmarks
            if any(op['memory'].get('leaked', False) for op in b['operations'].values() if op['status'] == 'PASS')
        ]
        
        if memory_leaks:
            report_lines.append("⚠️ **Memory Leak Warning:**")
            report_lines.append(f"- {len(memory_leaks)} agents show potential memory leaks")
            report_lines.append("- Review these agents for proper resource cleanup")
            report_lines.append("")
    
    # Recommendations
    report_lines.append("## Recommendations")
    report_lines.append("")
    
    slow_agents = [b for b in successful_benchmarks if b.get('performance_score') in ['SLOW', 'ACCEPTABLE']]
    if slow_agents:
        report_lines.append("### Optimization Candidates")
        report_lines.append("")
        for bench in slow_agents:
            init_time = bench['initialization']['mean_ms']
            report_lines.append(f"- **{bench['agent_name']}**: {init_time:.2f}ms initialization")
            report_lines.append(f"  - Consider lazy loading or caching")
        report_lines.append("")
    
    # Write report
    report_content = '\n'.join(report_lines)
    with open('AGENT_PERFORMANCE_REPORT.md', 'w') as f:
        f.write(report_content)
    
    return report_content


if __name__ == "__main__":
    report = generate_performance_report()
    print("Performance report generated: AGENT_PERFORMANCE_REPORT.md")
    print("\nPreview:")
    print(report[:500])
