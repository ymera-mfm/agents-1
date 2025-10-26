# Code Quality Report

**Timestamp:** 2025-10-19T23:11:43.623580

## Quality Score: 0.0/100

**Status:** 🔴 CRITICAL


## Critical Issues Requiring Immediate Attention

### 🔴 HIGH Security Issues: 10


## Style Issues: 30607


### Top Violations:

- **W293** (style violation): 18230 occurrences
- **E501** (line too long): 7045 occurrences
- **E302** (expected 2 blank lines): 1039 occurrences
- **F401** (imported but unused): 1011 occurrences
- **F821** (style violation): 989 occurrences

## Technical Debt Assessment

- **Style Issues:** 30607
- **Security Issues:** 62
- **Formatting Issues:** 93 files need formatting

## Refactoring Recommendations

1. Run `black .` to auto-format code
2. Fix HIGH severity security issues immediately
3. Address top style violations (see flake8_report.txt)
4. Add type hints to improve type coverage