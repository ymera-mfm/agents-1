# .github/checklists/new_component.md

## New Component Checklist

When creating a new component (agent/engine/module):

**Code:**
- [ ] Implements required interface (BaseAgent/BaseEngine/BaseModule)
- [ ] Has type hints for all methods
- [ ] Includes docstrings with examples
- [ ] Uses async/await for I/O operations
- [ ] Has proper error handling with specific exceptions
- [ ] Logs important events with context

**Testing:**
- [ ] Unit tests for core logic (tests/unit/test_{component}.py)
- [ ] Integration test if uses database/external services
- [ ] Mock external dependencies
- [ ] Coverage ≥ 80%

**Documentation:**
- [ ] README.md in component directory
- [ ] Usage examples
- [ ] Configuration options documented
- [ ] Added to main docs/COMPONENTS.md

**Integration:**
- [ ] Registered in component registry
- [ ] Added to docker-compose.yml if needed
- [ ] Environment variables in .env.example
- [ ] Migration script if database changes

**Verification:**
```bash
pytest tests/unit/test_{component}.py -v
pytest tests/integration/test_{component}_integration.py -v
python -c "from components.{component} import {Class}"
```
