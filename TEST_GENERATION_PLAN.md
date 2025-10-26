# Test Generation Plan

**Date:** 2025-10-20  
**Purpose:** Strategic plan to increase test coverage across YMERA agents  
**Status:** 📋 PLANNING PHASE

---

## Executive Summary

Based on the coverage analysis of 23 fixed agents and the broader agent ecosystem, this plan outlines a strategic approach to improve test coverage from the current 27.3% (import-time) to 80%+ (runtime).

### Current State
- **Import Coverage:** 27.3% (1,557/5,700 lines)
- **Import Success Rate:** 100% (23/23 agents)
- **Files Needing Tests:** 60
- **Estimated Total Tests:** 2,116 tests
- **Estimated Effort:** 1,056.6 hours

### Priority Breakdown
- **Priority 1 (Not Covered):** 59 files - Need basic test coverage
- **Priority 2 (Critical <30%):** 1 file - Need immediate improvement  
- **Priority 3 (30-60%):** 0 files - Need optimization
- **Good Coverage (60-80%):** Not yet achieved
- **Excellent (>80%):** Target state

---

## Strategic Approach

### Phase 1: Foundation Tests (Weeks 1-4)
**Goal:** Establish baseline test coverage for critical agents

**Target Files:** 23 fixed agents from Agent System Fixes PR

| Priority | Agents | Current Coverage | Target | Effort |
|----------|--------|------------------|--------|--------|
| High | base_agent.py | 32.2% | 80% | 48h |
| High | production_base_agent.py | 32.9% | 80% | 36h |
| High | performance_engine_agent.py | 40.6% | 85% | 24h |
| High | validation_agent.py | 39.9% | 85% | 20h |
| Medium | llm_agent.py | 25.6% | 75% | 32h |
| Medium | enhanced_learning_agent.py | 24.6% | 75% | 40h |
| Medium | drafting_agent.py | 31.2% | 75% | 28h |
| Medium | editing_agent.py | 27.4% | 75% | 32h |

**Estimated Phase 1 Effort:** 260 hours (6.5 weeks @ 40h/week)

### Phase 2: Infrastructure Tests (Weeks 5-8)
**Goal:** Test monitoring, security, and core infrastructure

**Target Areas:**
- Agent communication and messaging
- Metrics collection and monitoring
- Security and authentication
- Database integration

**Estimated Phase 2 Effort:** 200 hours (5 weeks)

### Phase 3: Integration Tests (Weeks 9-12)
**Goal:** End-to-end workflow and agent interaction tests

**Focus:**
- Multi-agent workflows
- Task orchestration
- Error handling and recovery
- Performance under load

**Estimated Phase 3 Effort:** 180 hours (4.5 weeks)

### Phase 4: Optimization (Weeks 13-16)
**Goal:** Achieve 80%+ coverage across all critical agents

**Activities:**
- Fill remaining coverage gaps
- Edge case testing
- Performance benchmarking
- Documentation updates

**Estimated Phase 4 Effort:** 140 hours (3.5 weeks)

---

## Test Categories & Approach

### 1. Unit Tests
**Coverage Goal:** 80%+ for individual methods

**Approach:**
```python
# Example: Test optional dependency handling
def test_base_agent_nats_optional():
    """Test agent works without NATS dependency"""
    # Mock NATS as unavailable
    with patch('base_agent.HAS_NATS', False):
        agent = BaseAgent(config)
        assert agent.nc is None
        # Verify graceful degradation
        result = await agent.connect()
        assert result is not None  # No crash
```

**Focus Areas:**
- Optional dependency handling (HAS_* flags)
- Error handling and exceptions
- Data validation and sanitization
- State management

### 2. Integration Tests
**Coverage Goal:** 60%+ for agent interactions

**Approach:**
```python
# Example: Test agent communication
async def test_agent_communication():
    """Test two agents can communicate"""
    agent1 = CommunicationAgent(config1)
    agent2 = MetricsAgent(config2)
    
    await agent1.start()
    await agent2.start()
    
    # Send message from agent1 to agent2
    result = await agent1.send_message(agent2.id, data)
    assert result.success
```

**Focus Areas:**
- Agent-to-agent communication
- Task distribution and orchestration
- Shared resource management
- Cross-agent workflows

### 3. Functional Tests
**Coverage Goal:** 70%+ for complete workflows

**Approach:**
```python
# Example: Test complete task workflow
async def test_task_workflow():
    """Test complete task from submission to completion"""
    orchestrator = OrchestratorAgent(config)
    
    task = TaskRequest(
        task_type="analysis",
        payload={"code": "def test(): pass"}
    )
    
    result = await orchestrator.execute_task(task)
    assert result.success
    assert result.result["analysis"] is not None
```

**Focus Areas:**
- Complete user workflows
- Error recovery scenarios
- Performance benchmarks
- Resource cleanup

### 4. Mock Strategy
**Approach:** Mock external dependencies for testing

**Dependencies to Mock:**
- NATS messaging
- Redis cache
- PostgreSQL database
- External APIs (OpenAI, Anthropic)
- File system operations
- Network calls

---

## Test File Organization

### Structure
```
tests/
├── agents/
│   ├── test_base_agent.py           # Unit tests
│   ├── test_communication_agent.py
│   ├── test_llm_agent.py
│   └── ...
├── integration/
│   ├── test_agent_workflows.py      # Integration tests
│   ├── test_task_orchestration.py
│   └── ...
├── functional/
│   ├── test_complete_workflows.py   # E2E tests
│   └── ...
└── fixtures/
    ├── conftest.py                  # Shared fixtures
    ├── mock_agents.py
    └── test_data.py
```

### Naming Convention
- Test files: `test_[module_name].py`
- Test functions: `test_[feature]_[scenario]`
- Fixtures: `[resource]_fixture`

---

## Top Priority Files (Immediate Action)

### Priority 1: Not Covered Files (59 files)

**Top 10 Files by Impact:**

| Rank | File | Statements | Tests Needed | Estimated Hours | Impact |
|------|------|------------|--------------|-----------------|--------|
| 1 | agent_client.py | 225 | 22 | 11.0 | High - Used by multiple agents |
| 2 | agent_coordinator.py | 279 | 27 | 13.5 | High - Orchestration core |
| 3 | agent_lifecycle_manager.py | 115 | 11 | 5.5 | High - Critical lifecycle |
| 4 | agent_discovery.py | 119 | 11 | 5.5 | Medium - Service discovery |
| 5 | agent_communicator.py | 41 | 4 | 2.0 | Medium - Communication |
| 6 | agent_registry.py | 88 | 8 | 4.0 | Medium - Agent registration |
| 7 | agent_surveillance.py | 186 | 18 | 9.0 | Medium - Monitoring |
| 8 | agent_manager_*.py | ~500 | ~50 | 25.0 | High - Management layer |

### Priority 2: Critical Coverage Files (1 file)

| File | Current | Target | Gap | Tests Needed | Hours |
|------|---------|--------|-----|--------------|-------|
| agent.py | 18.5% | 80% | 61.5% | 25 | 12.5 |

---

## Test Templates

### Template 1: Optional Dependency Test
```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_dependency():
    """Mock external dependency"""
    with patch('module.HAS_DEPENDENCY', False):
        yield

def test_agent_without_dependency(mock_dependency):
    """Test agent gracefully handles missing dependency"""
    agent = Agent(config)
    
    # Verify no crash on init
    assert agent is not None
    
    # Verify fallback behavior
    result = agent.method_using_dependency()
    assert result is not None  # Got fallback result
```

### Template 2: Integration Test
```python
@pytest.mark.asyncio
async def test_agent_integration():
    """Test two agents working together"""
    # Setup
    agent1 = AgentType1(config1)
    agent2 = AgentType2(config2)
    
    await agent1.start()
    await agent2.start()
    
    # Execute
    result = await agent1.interact_with(agent2)
    
    # Assert
    assert result.success
    assert result.data is not None
    
    # Cleanup
    await agent1.stop()
    await agent2.stop()
```

### Template 3: Workflow Test
```python
@pytest.mark.asyncio
async def test_complete_workflow():
    """Test complete user workflow"""
    # Arrange
    system = AgentSystem(config)
    await system.start()
    
    # Act
    task = create_test_task()
    result = await system.execute(task)
    
    # Assert
    assert result.status == "completed"
    assert result.output is not None
    
    # Verify side effects
    assert_metrics_recorded()
    assert_logs_created()
```

---

## Success Metrics

### Coverage Targets

| Phase | Duration | Target Coverage | Files Tested |
|-------|----------|----------------|--------------|
| Phase 1 | 4 weeks | 50% overall | 23 critical |
| Phase 2 | 4 weeks | 65% overall | +20 infrastructure |
| Phase 3 | 4 weeks | 75% overall | +15 integration |
| Phase 4 | 4 weeks | 80% overall | All remaining |

### Quality Metrics
- **Test Pass Rate:** 100%
- **Code Coverage:** 80%+
- **Test Execution Time:** <5 minutes
- **No Flaky Tests:** 100% reliability
- **Documentation:** All tests documented

---

## Tools & Infrastructure

### Required Tools
- ✅ pytest - Test framework
- ✅ pytest-cov - Coverage reporting
- ✅ pytest-asyncio - Async test support
- ⚠️ pytest-mock - Mocking framework (install needed)
- ⚠️ pytest-timeout - Test timeouts (install needed)
- ⚠️ coverage[toml] - Advanced coverage (install needed)

### CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pytest tests/ -v \
            --cov=. \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term-missing
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Implementation Timeline

### Month 1: Foundation
- **Week 1-2:** Base agent tests (base_agent, production_base_agent)
- **Week 3-4:** Infrastructure agent tests (monitoring, performance)

### Month 2: Core Features
- **Week 5-6:** LLM and learning agent tests
- **Week 7-8:** NLP agent tests (drafting, editing)

### Month 3: Integration
- **Week 9-10:** Agent communication tests
- **Week 11-12:** Workflow orchestration tests

### Month 4: Polish
- **Week 13-14:** Coverage gap filling
- **Week 15-16:** Performance and edge case testing

---

## Resource Requirements

### Team Composition (Recommended)
- **Senior Developer:** 1 FTE - Architecture and complex tests
- **Mid-Level Developer:** 2 FTE - Feature tests and integration
- **Junior Developer:** 1 FTE - Unit tests and documentation

### Infrastructure
- CI/CD pipeline with test automation
- Coverage tracking dashboard
- Test data management system
- Mock service infrastructure

---

## Risk Assessment

### High Risk
- **Time Estimate:** 1,000+ hours may be underestimated
- **Dependency Mocking:** Complex dependencies hard to mock
- **Async Testing:** Timing issues and flaky tests

### Mitigation
- Start with highest-impact files
- Build robust mocking infrastructure early
- Use pytest-asyncio best practices
- Regular code reviews

---

## Next Steps

### Immediate Actions (This Week)
1. ✅ Review this test generation plan
2. ⬜ Install additional pytest plugins
3. ⬜ Create base test fixtures and mocks
4. ⬜ Write tests for base_agent.py (highest priority)
5. ⬜ Set up CI/CD test automation

### Week 2
1. Complete base_agent.py tests
2. Start production_base_agent.py tests
3. Create reusable test utilities
4. Document testing patterns

### Week 3-4
1. Complete Phase 1 foundation tests
2. Achieve 50% overall coverage
3. Review and refine approach

---

## Conclusion

This test generation plan provides a structured approach to increase coverage from 27.3% to 80%+ over 16 weeks. The phased approach prioritizes high-impact files and builds test infrastructure incrementally.

**Key Success Factors:**
- Focus on critical agents first
- Build reusable test infrastructure
- Mock external dependencies properly
- Maintain 100% test pass rate
- Document patterns and best practices

**Files Generated:**
- `test_generation_plan.json` - Machine-readable plan
- `agent_test_plan.json` - Detailed file-by-file breakdown
- `TEST_GENERATION_PLAN.md` - This strategic document

---

**Ready to start?** Begin with Phase 1, Week 1: base_agent.py tests.
