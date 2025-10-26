# YMERA Multi-Agent AI System - Testing Guide

## Overview

This guide provides comprehensive instructions for running tests in the YMERA Multi-Agent AI System after successful integration.

---

## Quick Start

### Run All Tests
```bash
# Simple one-command execution
./run_tests.sh
```

### Run Specific Test Categories

#### Backend Unit Tests Only
```bash
PYTHONPATH=/home/runner/work/agents-1/agents-1:$PYTHONPATH pytest tests/test_base_agent.py -v
```

#### Backend Integration Tests Only
```bash
PYTHONPATH=/home/runner/work/agents-1/agents-1:$PYTHONPATH pytest tests/test_integration.py -v
```

#### E2E Integration Tests Only
```bash
PYTHONPATH=/home/runner/work/agents-1/agents-1:$PYTHONPATH pytest tests/test_e2e_integration.py -v
```

#### All Backend Tests
```bash
PYTHONPATH=/home/runner/work/agents-1/agents-1:$PYTHONPATH pytest -v
```

---

## Prerequisites

### System Requirements
- **Python:** 3.11+ (tested with 3.12.3)
- **Node.js:** 18.0.0+ (tested with 20.19.5)
- **npm:** 8.0.0+ (tested with 10.8.2)
- **pip:** Latest version recommended

### Dependencies Installation

#### Backend Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi, pytest, psutil; print('Dependencies OK')"
```

#### Frontend Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Verify installation
npm list --depth=0
```

---

## Test Categories

### 1. Unit Tests (5 tests)
**Location:** `tests/test_base_agent.py`  
**Purpose:** Test individual agent components in isolation  
**Coverage:**
- Agent initialization
- Agent lifecycle (start/stop)
- Message processing
- Status reporting
- Message queuing

**Run Command:**
```bash
PYTHONPATH=.:$PYTHONPATH pytest tests/test_base_agent.py -v
```

### 2. Integration Tests (3 tests)
**Location:** `tests/test_integration.py`  
**Purpose:** Test agent-to-agent interactions  
**Coverage:**
- Communication agent functionality
- Monitoring agent operations
- Multi-agent system coordination

**Run Command:**
```bash
PYTHONPATH=.:$PYTHONPATH pytest tests/test_integration.py -v
```

### 3. E2E Integration Tests (18 tests)
**Location:** `tests/test_e2e_integration.py`  
**Purpose:** Test complete system integration  
**Coverage:**
- API endpoints (9 tests)
- Agent operations (3 tests)
- API integration features (4 tests)
- Performance benchmarks (2 tests)

**Run Command:**
```bash
PYTHONPATH=.:$PYTHONPATH pytest tests/test_e2e_integration.py -v
```

---

## Test Execution Options

### Basic Execution
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with very verbose output
pytest -vv
```

### Coverage Reports
```bash
# Run with coverage
pytest --cov=. --cov-report=term

# Generate HTML coverage report
pytest --cov=. --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Selective Test Execution
```bash
# Run tests by marker
pytest -m unit
pytest -m integration
pytest -m asyncio

# Run specific test file
pytest tests/test_e2e_integration.py

# Run specific test class
pytest tests/test_e2e_integration.py::TestE2EIntegration

# Run specific test function
pytest tests/test_e2e_integration.py::TestE2EIntegration::test_health_endpoint
```

### Test Output Control
```bash
# Short traceback
pytest --tb=short

# No traceback
pytest --tb=no

# Show local variables in traceback
pytest --tb=long

# Show print output
pytest -s

# Capture warnings
pytest -W all
```

### Performance Testing
```bash
# Show slowest tests
pytest --durations=10

# Stop after first failure
pytest -x

# Run until N failures
pytest --maxfail=3
```

---

## Environment Configuration

### Backend Environment (.env)
```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor
```

**Key Configuration Variables:**
```ini
# Application
DEBUG=true
ENVIRONMENT=development

# API
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ymera

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# NATS
NATS_SERVERS=nats://localhost:4222

# Security
SECRET_KEY=your-secret-key-change-in-production

# Logging
LOG_LEVEL=INFO
```

### Frontend Environment (frontend/.env)
```bash
# Copy example configuration
cd frontend
cp .env.example .env

# Edit configuration
nano .env
```

**Key Configuration Variables:**
```ini
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# Feature Flags
REACT_APP_ENABLE_3D_VISUALIZATION=true
REACT_APP_ENABLE_REAL_TIME_COLLABORATION=true

# Development
REACT_APP_DEBUG_MODE=true
REACT_APP_MOCK_API=false
```

---

## Continuous Integration

### GitHub Actions Workflow
Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          PYTHONPATH=.:$PYTHONPATH pytest -v --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem:** `ModuleNotFoundError: No module named 'base_agent'`

**Solution:**
```bash
# Set PYTHONPATH
export PYTHONPATH=/path/to/project:$PYTHONPATH

# Or run with PYTHONPATH
PYTHONPATH=.:$PYTHONPATH pytest
```

#### 2. Missing Dependencies
**Problem:** `ModuleNotFoundError: No module named 'psutil'`

**Solution:**
```bash
# Install missing dependency
pip install psutil

# Verify requirements.txt is updated
grep psutil requirements.txt
```

#### 3. Test Failures
**Problem:** Tests fail with database connection errors

**Solution:**
```bash
# Check if services are running
docker-compose ps

# Start services
docker-compose up -d postgres redis nats

# Verify connectivity
curl http://localhost:8000/api/v1/health
```

#### 4. Permission Issues
**Problem:** `Permission denied: './run_tests.sh'`

**Solution:**
```bash
# Make script executable
chmod +x run_tests.sh

# Run script
./run_tests.sh
```

---

## Test Data Management

### Mock Data
Tests use in-memory mock data by default. No external services required for unit tests.

### Test Database
For integration tests requiring a database:
```bash
# Use SQLite for testing
export DATABASE_URL=sqlite:///./test.db

# Or use PostgreSQL test database
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ymera_test
```

---

## Performance Benchmarks

### Current Benchmarks
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| API Response Time | < 100ms | < 50ms | ✅ |
| Health Check | < 50ms | < 50ms | ✅ |
| Concurrent Requests (10) | 100% success | 100% success | ✅ |
| Test Suite Duration | < 5 min | ~3 sec | ✅ |

---

## Writing New Tests

### Test Template
```python
"""
Test module description
"""
import pytest
from typing import Any, Dict


class TestFeatureName:
    """Test suite for feature"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        expected = "value"
        
        # Act
        result = function_to_test()
        
        # Assert
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality"""
        result = await async_function()
        assert result is not None
```

### Best Practices
1. **Use descriptive test names:** `test_agent_lifecycle_start_stop`
2. **Follow AAA pattern:** Arrange, Act, Assert
3. **One assertion per test** (when possible)
4. **Use fixtures** for common setup
5. **Mock external dependencies**
6. **Test edge cases and errors**
7. **Keep tests independent**

---

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Async Testing Guide](https://pytest-asyncio.readthedocs.io/)

### Test Reports
- **E2E Test Report:** `E2E_TEST_REPORT.md`
- **Coverage Report:** `htmlcov/index.html` (after running with `--cov`)
- **Test Logs:** `backend_test_results.log`

### Support
For issues or questions:
1. Check this guide
2. Review test logs
3. Consult `E2E_TEST_REPORT.md`
4. Contact development team

---

## Next Steps

### After Running Tests Successfully
1. ✅ Review test coverage report
2. ✅ Address any warnings
3. ✅ Run linters (black, flake8, mypy)
4. ✅ Update documentation if needed
5. ✅ Commit changes
6. ✅ Create pull request

### Continuous Improvement
- Add more test coverage for edge cases
- Implement frontend E2E tests with Playwright
- Add load testing scenarios
- Set up automated CI/CD pipeline
- Monitor test performance over time

---

**Last Updated:** October 26, 2025  
**Version:** 1.0.0  
**Status:** Production Ready
