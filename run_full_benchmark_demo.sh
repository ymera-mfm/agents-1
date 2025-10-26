#!/bin/bash

echo "=========================================="
echo "YMERA Agent Performance Benchmarking Demo"
echo "=========================================="
echo ""

echo "Step 1: Running benchmarks..."
echo "------------------------------"
python agent_benchmarks.py 2>&1 | tee agent_benchmark_output.log
echo ""

echo "Step 2: Generating report..."
echo "----------------------------"
python benchmark_report_generator.py
echo ""

echo "Step 3: Verifying acceptance criteria..."
echo "----------------------------------------"
python verify_benchmarking.py
echo ""

echo "Step 4: Output files generated..."
echo "--------------------------------"
ls -lh agent_benchmarks_complete.json agent_benchmark_output.log AGENT_PERFORMANCE_REPORT.md
echo ""

echo "Step 5: Sample report preview..."
echo "-------------------------------"
head -40 AGENT_PERFORMANCE_REPORT.md
echo ""
echo "... (see AGENT_PERFORMANCE_REPORT.md for full report)"
echo ""

echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
