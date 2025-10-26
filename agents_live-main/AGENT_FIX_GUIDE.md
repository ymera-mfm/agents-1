# YMERA Agent Fix Guide

**Version**: 1.0  
**Date**: 2025-10-20  
**Status**: Active Implementation

---

## Quick Start

This guide provides a systematic approach to fixing broken agents in the YMERA platform following the bottom-up strategy outlined in the issue.

---

## Overview

**Current State:**
- Total Agents: 26 (in root directory)
- Level 0 (Base agents): 3
- Level 1 (Simple deps): 22
- Level 2 (Complex deps): 1

**Goal:**
- Create standardized, working agents
- Establish common patterns
- Enable systematic testing
- Reduce failure rate from 93.3% to <10%

---

## Phase 1: Foundation (COMPLETED ✅)

### Created Infrastructure

1. **`agents/agent_base.py`** - Shared base module
   - `BaseAgent` class
   - `AgentConfig` dataclass
   - `AgentCapability` class
   - `TaskRequest` and `TaskResponse` dataclasses
   - `Priority` and `TaskStatus` enums

2. **`agents/shared_utils.py`** - Utility functions
   - Configuration loading/saving
   - Payload validation
   - Error formatting
   - String sanitization

3. **`agents/__init__.py`** - Package initialization
   - Exports all common classes
   - Version management

4. **Example Fixed Agents:**
   - `example_agent_fixed.py` - Pattern demonstration
   - `calculator_agent.py` - Mathematical operations
   - `data_processor_agent.py` - Data transformations

---

## Phase 2: Fix Pattern

### Standard Agent Template

```python
"""
[Agent Name] - [Brief Description]

Status: FIXED
Last Modified: 2025-10-20
Dependencies: agents.agent_base (Level 1)
"""

# Standard library imports
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local imports from agents package
from agents.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    TaskRequest,
    TaskResponse,
    Priority,
    TaskStatus
)


class YourAgent(BaseAgent):
    """
    Agent description.
    
    Capabilities:
    - Capability 1
    - Capability 2
    
    Dependencies:
    - agents.agent_base (BaseAgent)
    
    Supported Task Types:
    - task_type_1: Description
    - task_type_2: Description
    """
    
    def __init__(self, agent_id: str = None):
        # Define capabilities
        capabilities = [
            AgentCapability(
                name="capability_name",
                description="Capability description",
                task_types=["task_type_1"],
                required_params=["param1", "param2"]
            )
        ]
        
        # Create config
        config = AgentConfig(
            agent_id=agent_id,
            name="YourAgent",
            description="Your agent description",
            capabilities=capabilities,
            max_concurrent_tasks=10,
            task_timeout=300
        )
        
        # Initialize base
        super().__init__(config)
        
        self.logger.info(f"{self.name} initialized")
    
    def _execute_task(self, task: TaskRequest) -> Any:
        """Execute task based on type."""
        task_type = task.task_type
        
        if task_type == "task_type_1":
            return self._handle_task_1(task.payload)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _handle_task_1(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task_type_1."""
        # Validate
        if "param1" not in payload:
            raise ValueError("Missing required parameter: param1")
        
        # Process
        result = {
            "processed": True,
            "output": "your result here"
        }
        
        return result


# Standalone test
if __name__ == "__main__":
    print("=" * 70)
    print("Testing YourAgent")
    print("=" * 70)
    
    agent = YourAgent()
    
    # Health check
    print("\n1. Health Check:")
    health = agent.health_check()
    print(json.dumps(health, indent=2))
    
    # Test task
    print("\n2. Test Task:")
    task = TaskRequest(
        task_type="task_type_1",
        priority=Priority.MEDIUM,
        payload={"param1": "value1"}
    )
    response = agent.process_task(task)
    print(json.dumps(response.to_dict(), indent=2))
    
    # Statistics
    print("\n3. Statistics:")
    print(json.dumps(agent.stats, indent=2))
    
    print("\n" + "=" * 70)
    print("Tests completed")
    print("=" * 70)
```

---

## Common Fixes

### Fix 1: Import Errors

**Problem:**
```python
from base_agent import BaseAgent  # ModuleNotFoundError
```

**Solution:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.agent_base import BaseAgent
```

### Fix 2: Validation Errors

**Problem:**
```python
config = AgentConfig(name="MyAgent")  # Missing required fields
```

**Solution:**
```python
config = AgentConfig(
    name="MyAgent",
    description="Description",
    capabilities=[]  # Provide all fields
)
```

### Fix 3: Circular Dependencies

**Problem:**
```python
# agent_a.py imports agent_b
# agent_b.py imports agent_a
```

**Solution:**
```python
# Use lazy imports inside methods
def get_other_agent(self):
    from agents.other_agent import OtherAgent
    return OtherAgent()
```

### Fix 4: Name Errors

**Problem:**
```python
result = process_data(data)  # data not defined yet
data = fetch_data()
```

**Solution:**
```python
data = fetch_data()
result = process_data(data)
```

---

## Testing Checklist

For each fixed agent:

- [ ] No import errors
- [ ] Health check works
- [ ] Task processing works
- [ ] Error handling works
- [ ] Statistics tracking works
- [ ] Standalone test passes
- [ ] Documentation complete
- [ ] Follows naming conventions

---

## Priority and TaskStatus Enum Values

Use these exact values for agent configuration:

**Priority Enum Values**
- `Priority.LOW`
- `Priority.MEDIUM`
- `Priority.HIGH`
- `Priority.CRITICAL`

**TaskStatus Enum Values**
- `TaskStatus.PENDING`
- `TaskStatus.RUNNING`
- `TaskStatus.SUCCESS`
- `TaskStatus.ERROR`
- `TaskStatus.TIMEOUT`

---

## Best Practices

1. **Always include sys.path adjustment** for imports to work from anywhere
2. **Validate all inputs** before processing
3. **Use proper error messages** with details
4. **Log important operations** using self.logger
5. **Include standalone tests** in `__main__`
6. **Document capabilities** clearly
7. **Use dataclasses** for structured data
8. **Follow consistent naming** (snake_case for functions, PascalCase for classes)

---

## Example Commands

### Test a fixed agent:
```bash
python3 agents/calculator_agent.py
```

### Run dependency analysis:
```bash
python3 analyze_agent_deps.py
```

### Check import issues:
```bash
python3 -c "from agents.agent_base import BaseAgent; print('OK')"
```

---

## Resources

- **Base Module**: `agents/agent_base.py`
- **Utilities**: `agents/shared_utils.py`
- **Examples**: 
  - `agents/example_agent_fixed.py`
  - `agents/calculator_agent.py`
  - `agents/data_processor_agent.py`
- **Fix Log**: `fix_log.md`
- **Dependency Analysis**: `agent_dependency_analysis_new.json`

---

## Next Steps

1. Fix Level 1 agents in batches of 5
2. Test each batch before moving to next
3. Update fix_log.md with progress
4. Create integration tests
5. Generate final report

---

## Support

For questions or issues:
1. Check this guide first
2. Review example agents
3. Check fix_log.md for known issues
4. Test in isolation using standalone mode
