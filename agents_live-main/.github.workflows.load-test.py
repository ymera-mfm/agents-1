# .github/workflows/load-test.yml
name: Load Testing

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install locust
    
    - name: Run load test
      run: |
        locust -f tests/performance/test_load.py \
          --headless \
          -u 1000 \
          -r 100 \
          -t 10m \
          --host=https://staging.api.ymera.example.com \
          --html load-test-report.html \
          --csv load-test
    
    - name: Upload load test report
      uses: actions/upload-artifact@v3
      with:
        name: load-test-report
        path: |
          load-test-report.html
          load-test_requests.csv
          load-test_stats.csv
    
    - name: Check performance metrics
      run: |
        # This would parse the CSV results and check against performance SLOs
        python scripts/check_performance.py