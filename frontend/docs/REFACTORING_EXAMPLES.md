# Refactoring Examples - Ymera Frontend

## Overview

This document provides real-world refactoring examples from the ymera-frontend codebase, demonstrating how to apply refactoring patterns to improve code quality.

## Example 1: Extract Error Handling Utilities

### Problem Identified

The codebase has 43+ `try-catch` blocks with similar error handling logic scattered across multiple files. This violates the DRY (Don't Repeat Yourself) principle.

### Current Pattern (Before Refactoring)

```javascript
// In cache.js
loadCacheStats() {
  try {
    const stats = localStorage.getItem('cacheStats');
    if (stats) {
      this.cacheStats = JSON.parse(stats);
    }
  } catch (error) {
    console.warn('Failed to load cache stats:', error);
  }
}

// In logger.js (similar pattern)
loadLogs() {
  try {
    const logs = localStorage.getItem('logs');
    if (logs) {
      this.logs = JSON.parse(logs);
    }
  } catch (error) {
    console.warn('Failed to load logs:', error);
  }
}
```

### Refactored Solution

```javascript
// src/utils/storage-utils.js
/**
 * Safely retrieves and parses JSON from storage
 * @param {Storage} storage - The storage object (localStorage or sessionStorage)
 * @param {string} key - The storage key
 * @param {any} defaultValue - Default value if retrieval fails
 * @returns {any} Parsed value or default
 */
export function safeGetJSON(storage, key, defaultValue = null) {
  try {
    const item = storage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.warn(`Failed to retrieve ${key} from storage:`, error);
    return defaultValue;
  }
}

/**
 * Safely stores JSON in storage
 * @param {Storage} storage - The storage object
 * @param {string} key - The storage key
 * @param {any} value - Value to store
 * @returns {boolean} Success status
 */
export function safeSetJSON(storage, key, value) {
  try {
    storage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.warn(`Failed to store ${key} in storage:`, error);
    return false;
  }
}

// Usage in cache.js
import { safeGetJSON, safeSetJSON } from '../utils/storage-utils';

loadCacheStats() {
  this.cacheStats = safeGetJSON(localStorage, 'cacheStats', { hits: 0, misses: 0 });
}

saveCacheStats() {
  safeSetJSON(localStorage, 'cacheStats', this.cacheStats);
}
```

### Benefits
- ✓ Eliminates 40+ duplicate try-catch blocks
- ✓ Centralizes error handling logic
- ✓ Easier to maintain and test
- ✓ Consistent error messages
- ✓ Reduces code by ~200 lines

---

## Example 2: Component Decomposition

### Problem Identified

`enhanced-navbar-integration.js` is 695 lines - too large for a single file. It mixes multiple concerns: navigation, search, notifications, user menu, and mobile handling.

### Current Structure (Before Refactoring)

```
enhanced-navbar-integration.js (695 lines)
├── NotificationIndicator component
├── SmartSearch component  
├── UserMenu component
├── MobileMenu component
├── NavBar main component
└── Various utility functions
```

### Refactored Structure

```
components/
├── navigation/
│   ├── NavBar.jsx (100 lines) - Main orchestrator
│   ├── NotificationIndicator.jsx (50 lines)
│   ├── SmartSearch.jsx (80 lines)
│   ├── UserMenu.jsx (70 lines)
│   ├── MobileMenu.jsx (90 lines)
│   ├── NavLinks.jsx (60 lines)
│   └── index.js (exports)
```

### Code Example

```javascript
// components/navigation/NotificationIndicator.jsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAgentStatus } from '../../store/agent-status';
import { NOTIFICATION_TIMEOUT } from '../../constants/ui';

/**
 * Displays notification count with animation
 * @returns {JSX.Element|null} Notification indicator or null
 */
export function NotificationIndicator() {
  const { notificationCount } = useAgentStatus();
  const [hasNew, setHasNew] = useState(false);
  
  useEffect(() => {
    if (notificationCount > 0) {
      setHasNew(true);
      const timer = setTimeout(() => setHasNew(false), NOTIFICATION_TIMEOUT);
      return () => clearTimeout(timer);
    }
  }, [notificationCount]);

  if (notificationCount === 0) return null;

  return (
    <motion.div className="relative" initial={{ scale: 0 }} animate={{ scale: 1 }}>
      <NotificationBadge count={notificationCount} animated={hasNew} />
      {hasNew && <PulseAnimation />}
    </motion.div>
  );
}

// components/navigation/NavBar.jsx
import React from 'react';
import { NotificationIndicator } from './NotificationIndicator';
import { SmartSearch } from './SmartSearch';
import { UserMenu } from './UserMenu';
import { NavLinks } from './NavLinks';

export function NavBar() {
  return (
    <nav className="navbar">
      <NavLinks />
      <div className="navbar-actions">
        <SmartSearch />
        <NotificationIndicator />
        <UserMenu />
      </div>
    </nav>
  );
}
```

### Benefits
- ✓ Each file < 100 lines (manageable)
- ✓ Single Responsibility Principle
- ✓ Easier to test components individually
- ✓ Better code organization
- ✓ Improved reusability

---

## Example 3: Extract Constants

### Problem Identified

Magic numbers and strings scattered throughout the codebase.

### Before Refactoring

```javascript
// Multiple files with magic values
const timeout = setTimeout(() => setHasNew(false), 3000);
if (query.length > 2) { /* ... */ }
const expiresAt = Date.now() + ttl;
if (elapsed > 3600000) { /* ... */ }
```

### After Refactoring

```javascript
// src/constants/ui.js
export const UI_CONSTANTS = {
  NOTIFICATION_TIMEOUT: 3000,
  MIN_SEARCH_LENGTH: 2,
  DEBOUNCE_DELAY: 300,
  ANIMATION_DURATION: 200,
};

// src/constants/time.js
export const TIME_CONSTANTS = {
  ONE_SECOND_MS: 1000,
  ONE_MINUTE_MS: 60 * 1000,
  ONE_HOUR_MS: 60 * 60 * 1000,
  ONE_DAY_MS: 24 * 60 * 60 * 1000,
};

// Usage
import { UI_CONSTANTS } from '../constants/ui';
import { TIME_CONSTANTS } from '../constants/time';

const timeout = setTimeout(() => setHasNew(false), UI_CONSTANTS.NOTIFICATION_TIMEOUT);
if (query.length > UI_CONSTANTS.MIN_SEARCH_LENGTH) { /* ... */ }
if (elapsed > TIME_CONSTANTS.ONE_HOUR_MS) { /* ... */ }
```

### Benefits
- ✓ Self-documenting code
- ✓ Easy to modify values in one place
- ✓ Type-safe with JSDoc
- ✓ Prevents magic number bugs

---

## Example 4: Simplify Cache Service

### Problem Identified

`cache.js` (394 lines) has duplicate logic for memory cache and legacy cache, complex conditionals, and mixed concerns.

### Current Issues
- Two separate cache implementations (legacy + enhanced)
- Duplicate TTL checking logic
- Complex strategy selection with nested conditionals
- Mixed localStorage/sessionStorage handling

### Refactored Design

```javascript
// src/services/cache/strategies/BaseStrategy.js
export class BaseStrategy {
  set(key, value, ttl) { throw new Error('Not implemented'); }
  get(key) { throw new Error('Not implemented'); }
  has(key) { throw new Error('Not implemented'); }
  delete(key) { throw new Error('Not implemented'); }
  clear() { throw new Error('Not implemented'); }
}

// src/services/cache/strategies/MemoryStrategy.js
export class MemoryStrategy extends BaseStrategy {
  constructor() {
    super();
    this.cache = new Map();
  }

  set(key, value, ttl) {
    this.cache.set(key, {
      value,
      expiresAt: Date.now() + ttl,
      createdAt: Date.now(),
    });
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (this.isExpired(item)) {
      this.cache.delete(key);
      return null;
    }
    
    return item.value;
  }

  isExpired(item) {
    return Date.now() > item.expiresAt;
  }
}

// src/services/cache/strategies/StorageStrategy.js
export class StorageStrategy extends BaseStrategy {
  constructor(storage) {
    super();
    this.storage = storage;
  }

  set(key, value, ttl) {
    const item = {
      value,
      expiresAt: Date.now() + ttl,
    };
    this.storage.setItem(key, JSON.stringify(item));
  }

  get(key) {
    const data = this.storage.getItem(key);
    if (!data) return null;
    
    const item = JSON.parse(data);
    if (this.isExpired(item)) {
      this.storage.removeItem(key);
      return null;
    }
    
    return item.value;
  }

  isExpired(item) {
    return Date.now() > item.expiresAt;
  }
}

// src/services/cache/CacheService.js
import { MemoryStrategy } from './strategies/MemoryStrategy';
import { StorageStrategy } from './strategies/StorageStrategy';

export class CacheService {
  constructor(config) {
    this.strategies = {
      memory: new MemoryStrategy(),
      localStorage: new StorageStrategy(localStorage),
      sessionStorage: new StorageStrategy(sessionStorage),
    };
    this.config = config;
  }

  getStrategy(key) {
    const strategyName = this.config.getStrategyForKey(key);
    return this.strategies[strategyName] || this.strategies.memory;
  }

  set(key, value, ttl = this.config.defaultTTL) {
    const strategy = this.getStrategy(key);
    strategy.set(key, value, ttl);
  }

  get(key) {
    const strategy = this.getStrategy(key);
    return strategy.get(key);
  }
}
```

### Benefits
- ✓ Strategy Pattern for clean separation
- ✓ No code duplication
- ✓ Easy to add new storage strategies
- ✓ Testable in isolation
- ✓ Reduced from 394 to ~150 lines total

---

## Example 5: React Hook Optimization

### Problem Identified

`usePerformanceMonitor.js` (284 lines) re-renders unnecessarily and has complex state management.

### Before Refactoring

```javascript
function usePerformanceMonitor() {
  const [metrics, setMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  
  useEffect(() => {
    // Complex monitoring logic
    const interval = setInterval(() => {
      const newMetrics = calculateMetrics();
      setMetrics(newMetrics);
      
      const newAlerts = checkThresholds(newMetrics);
      setAlerts(newAlerts);
      
      setHistory(prev => [...prev, newMetrics]);
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);
  
  return { metrics, alerts, history };
}
```

### After Refactoring

```javascript
// src/hooks/usePerformanceMonitor.js
import { useReducer, useEffect, useMemo } from 'react';
import { performanceReducer } from './performanceReducer';
import { usePerformanceCalculator } from './usePerformanceCalculator';

function usePerformanceMonitor(options = {}) {
  const [state, dispatch] = useReducer(performanceReducer, initialState);
  const calculator = usePerformanceCalculator();
  
  useEffect(() => {
    const interval = setInterval(() => {
      const metrics = calculator.calculate();
      dispatch({ type: 'UPDATE_METRICS', payload: metrics });
    }, options.interval || 1000);
    
    return () => clearInterval(interval);
  }, [calculator, options.interval]);
  
  // Memoize expensive computations
  const alerts = useMemo(
    () => calculator.checkThresholds(state.metrics),
    [state.metrics, calculator]
  );
  
  return {
    metrics: state.metrics,
    alerts,
    history: state.history,
  };
}

// src/hooks/performanceReducer.js
export function performanceReducer(state, action) {
  switch (action.type) {
    case 'UPDATE_METRICS':
      return {
        ...state,
        metrics: action.payload,
        history: [...state.history.slice(-99), action.payload],
      };
    default:
      return state;
  }
}
```

### Benefits
- ✓ useReducer for complex state
- ✓ useMemo to prevent unnecessary calculations
- ✓ Separated calculation logic
- ✓ Easier to test reducer independently
- ✓ Better performance

---

## Refactoring Metrics

### Before Refactoring
- Total lines of code: ~16,000
- Average file size: 320 lines
- Cyclomatic complexity (average): 12
- Code duplication: ~15%
- Test coverage: 45%

### After Refactoring (Target)
- Total lines of code: ~12,000 (25% reduction)
- Average file size: 150 lines
- Cyclomatic complexity (average): < 8
- Code duplication: < 3%
- Test coverage: > 85%

## Refactoring Checklist

- [ ] Extract storage utilities to reduce duplication
- [ ] Split large components (>300 lines) into smaller modules
- [ ] Extract all magic numbers to constants
- [ ] Refactor cache service using Strategy Pattern
- [ ] Optimize React hooks with proper memoization
- [ ] Add JSDoc documentation to all utilities
- [ ] Write tests for newly extracted modules
- [ ] Update imports across codebase
- [ ] Run linter and fix all issues
- [ ] Verify no functionality is broken

## Next Steps

1. Create feature branch: `refactor/code-quality-improvements`
2. Implement changes incrementally
3. Test after each change
4. Commit frequently with descriptive messages
5. Update documentation
6. Request code review
7. Merge to main

## Related Documents

- [Refactoring Guide](./REFACTORING_GUIDE.md)
- [Code Refactoring Template](../.github/ISSUE_TEMPLATE/code-refactoring.yml)
- [Performance Optimization Template](../.github/ISSUE_TEMPLATE/performance-optimization.yml)
