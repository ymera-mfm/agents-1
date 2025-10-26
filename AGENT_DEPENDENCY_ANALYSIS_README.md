# Agent Dependency Analysis Tool

## Overview

The Agent Dependency Analysis Tool helps systematically fix failing agents by analyzing their import dependencies and categorizing them by complexity level. This enables a bottom-up fix strategy where agents with zero internal dependencies are fixed first, followed by agents that depend on those fixed agents.

## Purpose

**Goal**: Fix 152 failing agents (93.3% failure rate → target: <10% failure rate)

**Strategy**: 
1. Fix agents in isolation (code-level issues)
2. Progress from simple to complex (dependency-based ordering)
3. Avoid cascading failures by fixing foundation agents first

## Installation

No additional installation required. The tool uses only Python standard library modules:
- `ast` - For parsing Python source code
- `json` - For generating reports
- `pathlib` - For file system operations

## Usage

### Run the Analysis

```bash
python3 analyze_agent_dependencies.py
```

### Output

The tool generates:
1. **Console Output**: Summary statistics and top-priority agents
2. **JSON Report**: `agent_dependency_analysis.json` with detailed dependency information

### Example Output

```
======================================================================
AGENT DEPENDENCY ANALYSIS
======================================================================

Found 31 agent files

Total Agents: 31
Level 0 (Independent): 3
Level 1 (Minimal deps): 23
Level 2 (Moderate deps): 5
Level 3 (Complex deps): 0
======================================================================

Level 0 Agents (Fix These First):
  - base_agent.py
  - enhanced_base_agent.py
  - production_base_agent.py
```

## Dependency Levels

### Level 0: Independent Agents (Priority 1)
- **Criteria**: Zero internal dependencies
- **Characteristics**: Only import external libraries
- **Fix Priority**: **HIGHEST** - Start here
- **Example**: `base_agent.py`, `enhanced_base_agent.py`

### Level 1: Minimal Dependencies (Priority 2)
- **Criteria**: 1-2 internal dependencies
- **Characteristics**: Depend on 1-2 other agents/modules
- **Fix Priority**: **HIGH** - Fix after Level 0
- **Example**: `communication_agent.py`, `coding_agent.py`

### Level 2: Moderate Dependencies (Priority 3)
- **Criteria**: 3-5 internal dependencies
- **Characteristics**: Integrate multiple system components
- **Fix Priority**: **MEDIUM** - Fix after Level 1
- **Example**: `learning_agent.py`

### Level 3: Complex Dependencies (Priority 4)
- **Criteria**: 6+ internal dependencies
- **Characteristics**: Heavy integration across system
- **Fix Priority**: **LOW** - Fix last
- **Example**: Complex orchestration agents

## JSON Report Structure

```json
{
  "summary": {
    "total_agents": 31,
    "level_0_independent": 3,
    "level_1_minimal": 23,
    "level_2_moderate": 5,
    "level_3_complex": 0
  },
  "level_0_agents": ["base_agent.py", ...],
  "level_1_agents": ["coding_agent.py", ...],
  "level_2_agents": ["learning_agent.py", ...],
  "level_3_agents": [],
  "detailed_dependencies": {
    "base_agent.py": {
      "internal_dependencies": [],
      "external_dependencies": ["asyncio", "logging", ...],
      "internal_count": 0,
      "external_count": 29,
      "dependency_level": 0,
      "file_path": "base_agent.py"
    }
  }
}
```

## Fix Strategy Workflow

### Phase 1: Foundation (Week 1)
**Target**: Level 0 agents

```bash
# 1. Run analysis
python3 analyze_agent_dependencies.py

# 2. Identify Level 0 agents
# 3. For each Level 0 agent:
#    - Fix ModuleNotFoundError issues
#    - Fix ImportError issues
#    - Fix ValidationError issues
#    - Test individually
```

### Phase 2: Core Layer (Week 2)
**Target**: Level 1 agents (only after Level 0 passes)

```bash
# Same process as Phase 1, but for Level 1 agents
```

### Phase 3: Integration Layer (Week 3)
**Target**: Level 2 agents

### Phase 4: Complex Layer (Week 4)
**Target**: Level 3 agents

## Common Error Patterns

### 1. ModuleNotFoundError (31.3% of failures)

**Problem**: Python can't find the module
```python
# BROKEN
from base_agent import BaseAgent
```

**Solutions**:
```python
# FIX 1: Add to Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_agent import BaseAgent

# FIX 2: Use relative imports
from .base_agent import BaseAgent

# FIX 3: Use absolute imports
from agents.base_agent import BaseAgent
```

### 2. ImportError (16.0% of failures)

**Problem**: Circular dependencies or syntax errors
```python
# BROKEN: Circular dependency
# agent_a.py imports agent_b
# agent_b.py imports agent_a
```

**Solution**:
```python
# FIX: Lazy imports
def get_agent_b():
    from agent_b import AgentB
    return AgentB
```

### 3. ValidationError (5.5% of failures)

**Problem**: Pydantic validation fails
```python
# BROKEN: Missing required fields
config = AgentConfig(name="MyAgent")
```

**Solution**:
```python
# FIX: Provide all required fields or defaults
config = AgentConfig(
    name="MyAgent",
    agent_id=str(uuid.uuid4()),
    capabilities=["task1"],
    priority=Priority.MEDIUM
)
```

## How the Tool Works

### 1. File Discovery
- Searches for `*_agent.py` files in repository
- Checks root directory and subdirectories
- Supports nested agent directories

### 2. Import Extraction
- Uses Python's `ast` module to parse source code
- Extracts both `import` and `from ... import` statements
- Handles relative imports (e.g., `from . import ...`)

### 3. Dependency Classification
- **Internal**: Imports containing keywords like 'agent', 'base_agent', 'shared', 'core', 'middleware', 'engine'
- **External**: Standard library and third-party packages

### 4. Level Categorization
- Counts internal dependencies
- Groups agents into levels (0, 1, 2, 3+)
- Generates JSON report with detailed information

## Integration with Testing

After fixing agents at each level, validate with:

```bash
# Run tests for specific agent
pytest tests/agents/test_base_agent.py -v

# Run all agent tests
pytest tests/agents/ -v

# Check coverage
pytest --cov=. --cov-report=html
```

## Customization

### Adjust Internal Keywords

Edit the `internal_keywords` list in `analyze_agent_dependencies.py`:

```python
self.internal_keywords = [
    'agent', 'base_agent', 'shared', 'core', 
    'middleware', 'engine', 'config', 'models',
    'utils', 'communication', 'orchestrator',
    # Add custom keywords here
]
```

### Change Dependency Level Thresholds

Modify the categorization logic:

```python
def categorize_by_dependency_level(self, dependency_map):
    # Adjust thresholds here
    if count == 0:
        levels['level_0'].append(agent)
    elif count <= 2:  # Change this threshold
        levels['level_1'].append(agent)
    # etc.
```

## Next Steps After Analysis

1. **Review Report**: Examine `agent_dependency_analysis.json`
2. **Start with Level 0**: Fix independent agents first
3. **Test Each Fix**: Run agent-specific tests after fixes
4. **Progress Incrementally**: Move to next level only after current level passes
5. **Document Fixes**: Track what was changed and why

## Expected Results

After completing the fix strategy:
- ✅ 100% of agents passing import validation
- ✅ <10% failure rate on agent tests
- ✅ Clean dependency graph
- ✅ Documented fix patterns for future agents

## Troubleshooting

### No agents found
- Check that you're running from repository root
- Verify agent files match `*_agent.py` pattern

### Missing dependencies in report
- Check if keywords match your import patterns
- Adjust `internal_keywords` list if needed

### Parse errors
- Review the warning messages for specific files
- Check Python syntax in failing agent files

## Support

For issues or questions:
1. Check the JSON report for detailed dependency information
2. Review agent import statements manually
3. Compare with successfully passing agents
4. Document patterns for reuse

---

**Generated by**: YMERA Platform Agent Dependency Analysis Tool  
**Version**: 1.0.0  
**Last Updated**: 2025-10-20
