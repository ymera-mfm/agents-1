# Performance Optimization Guide

## Overview

This guide provides comprehensive information about the performance optimization system implemented in the AgentFlow application. It includes templates, utilities, and best practices for maintaining and improving application performance.

## Table of Contents

1. [Performance Template](#performance-template)
2. [Performance Configuration](#performance-configuration)
3. [Performance Monitoring](#performance-monitoring)
4. [Optimization Techniques](#optimization-techniques)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Performance Template

The performance optimization template is available at `.github/ISSUE_TEMPLATE/performance-optimization.yml`. Use this template when creating performance-related issues to ensure all necessary information is captured.

### Template Sections

- **Performance Issue Description**: What needs optimization
- **Current Metrics**: Real performance measurements
- **Target Metrics**: Performance goals
- **Bottleneck Analysis**: Identified performance issues with evidence
- **Affected Components**: Files and modules requiring optimization
- **Optimization Strategies**: Planned optimization approaches
- **Benchmarking Plan**: How improvements will be measured
- **Testing Requirements**: Validation tests
- **Rollback Plan**: Safety measures

---

## Performance Configuration

Performance settings are centralized in `src/config/performance.config.js`.

### Key Configuration Areas

#### Monitoring
```javascript
monitoring: {
  enabled: true,
  sampleRate: 1.0,
  reportInterval: 30000, // 30 seconds
}
```

#### Bundle Optimization
```javascript
bundle: {
  lazyLoadThreshold: 100 * 1024, // 100KB
  chunkSizeWarning: 200 * 1024, // 200KB
  maxChunkSize: 500 * 1024, // 500KB
}
```

#### Image Optimization
```javascript
images: {
  lazyLoad: true,
  quality: 85,
  formats: ['webp', 'jpg'],
}
```

#### Caching Strategy
```javascript
cache: {
  apiCache: { enabled: true, ttl: 5 * 60 * 1000 },
  componentCache: { enabled: true },
  assetCache: { enabled: true, maxAge: 7 * 24 * 60 * 60 },
}
```

---

## Performance Monitoring

### Performance Monitor

The `performanceMonitor` utility tracks various performance metrics:

```javascript
import { performanceMonitor, measureRender, measureAsync } from '@/utils/performance';

// Measure component render
measureRender('MyComponent', () => {
  // Component render logic
});

// Measure async operations
await measureAsync('fetchData', async () => {
  return await api.getData();
});
```

### Metrics Tracked

- **Long tasks**: Operations taking >50ms
- **Layout shifts**: Unexpected layout changes
- **Resource timing**: Asset load times
- **Memory usage**: Heap size and potential leaks
- **Component renders**: Render duration and count

### Getting Metrics

```javascript
// Get current metrics
const metrics = performanceMonitor.getMetrics();
console.log(metrics);

// Get Web Vitals
const vitals = performanceMonitor.getWebVitals();
console.log(vitals);
```

---

## Optimization Techniques

### 1. Bundle Optimization

#### Code Splitting
```javascript
// Use React.lazy for route-based splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));

// Wrap in Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Dashboard />
</Suspense>
```

#### Bundle Analysis
```javascript
import { bundleAnalyzer } from '@/utils/performance';

// Analyze and get recommendations
const analysis = bundleAnalyzer.generateReport();
```

### 2. Image Optimization

```javascript
import { imageOptimizer } from '@/utils/performance';

// Get optimized image URL
const optimizedUrl = imageOptimizer.getOptimizedUrl(
  '/images/hero.jpg',
  { size: 'large', format: 'webp' }
);

// Generate responsive srcSet
const srcSet = imageOptimizer.generateSrcSet('/images/hero.jpg');

// Lazy load images
imageOptimizer.lazyLoad(imageElement);
```

### 3. React Optimizations

#### Debouncing
```javascript
import { useDebounce } from '@/utils/performance';

function SearchComponent() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);

  useEffect(() => {
    // This only runs after user stops typing
    performSearch(debouncedSearch);
  }, [debouncedSearch]);
}
```

#### Throttling
```javascript
import { useThrottle } from '@/utils/performance';

function ScrollComponent() {
  const [scrollY, setScrollY] = useState(0);
  const throttledScrollY = useThrottle(scrollY, 100);

  // Use throttledScrollY for expensive operations
}
```

#### Lazy Loading with Retry
```javascript
import { lazyWithRetry } from '@/utils/performance';

const HeavyComponent = lazy(() => 
  lazyWithRetry(() => import('./HeavyComponent'))
);
```

#### Render Performance
```javascript
import { useRenderTime } from '@/utils/performance';

function MyComponent() {
  const { renderTime, renderCount } = useRenderTime('MyComponent');
  
  // Logs warnings for slow renders (>16ms)
  return <div>...</div>;
}
```

#### Intersection Observer
```javascript
import { useIntersectionObserver } from '@/utils/performance';

function LazySection() {
  const ref = useRef();
  const [isVisible, setIsVisible] = useState(false);

  useIntersectionObserver(
    ref,
    { threshold: 0.1 },
    () => setIsVisible(true)
  );

  return (
    <div ref={ref}>
      {isVisible && <HeavyContent />}
    </div>
  );
}
```

### 4. Caching Strategies

The application uses the existing `cacheService` from `src/services/cache.js`:

```javascript
import { cacheService } from '@/services/cache';

// Cache API responses
cacheService.set('user-data', userData, 5 * 60 * 1000); // 5 minutes

// Retrieve from cache
const cachedData = cacheService.get('user-data');

// Use enhanced caching with namespaces
cacheService.setEnhanced('agents', agentsData, 10 * 60 * 1000, 'api');
const agents = cacheService.getEnhanced('agents', 'api');
```

---

## Best Practices

### Component Optimization

1. **Use React.memo for Pure Components**
   ```javascript
   const MyComponent = React.memo(({ data }) => {
     return <div>{data}</div>;
   });
   ```

2. **Use useMemo for Expensive Computations**
   ```javascript
   const expensiveResult = useMemo(() => {
     return computeExpensiveValue(data);
   }, [data]);
   ```

3. **Use useCallback for Function Props**
   ```javascript
   const handleClick = useCallback(() => {
     doSomething(id);
   }, [id]);
   ```

### Loading Optimization

1. **Lazy Load Routes**
   - Split code by route
   - Use Suspense for loading states

2. **Lazy Load Images**
   - Use `imageOptimizer.lazyLoad()`
   - Implement proper placeholders

3. **Defer Non-Critical Resources**
   - Load analytics after page load
   - Use `useIdleCallback` for low-priority tasks

### Network Optimization

1. **Implement Caching**
   - Use `cacheService` for API responses
   - Set appropriate TTL values

2. **Batch Requests**
   - Combine multiple API calls when possible
   - Use GraphQL for precise data fetching

3. **Optimize Payload Size**
   - Minimize response data
   - Use compression (gzip/brotli)

### Bundle Size Optimization

1. **Audit Dependencies**
   ```bash
   npm run analyze
   ```

2. **Remove Unused Code**
   - Use tree shaking
   - Remove unused dependencies

3. **Use Smaller Alternatives**
   - Choose lightweight libraries
   - Use native APIs when possible

---

## Performance Budgets

The system enforces performance budgets defined in `performance.config.js`:

### Core Web Vitals Targets
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1
- **FCP** (First Contentful Paint): < 1.8s
- **TTFB** (Time to First Byte): < 600ms

### Resource Budgets
- **Total Size**: < 500KB
- **Script Size**: < 300KB
- **CSS Size**: < 50KB
- **Image Size**: < 150KB per image

### Timing Budgets
- **Page Load**: < 3s
- **Time to Interactive**: < 3.5s
- **API Response**: < 1s

---

## Monitoring in Production

### Enable Performance Monitoring

Set environment variables:
```bash
REACT_APP_PERFORMANCE_MONITORING=true
REACT_APP_PERFORMANCE_SAMPLE_RATE=0.1  # Sample 10% of users
```

### View Performance Reports

```javascript
// In development console
performanceMonitor.generateReport();

// Get metrics programmatically
const metrics = performanceMonitor.getMetrics();
```

---

## Troubleshooting

### High Bundle Size

1. Run bundle analyzer:
   ```bash
   npm run analyze
   ```

2. Check for:
   - Duplicate dependencies
   - Large libraries not code-split
   - Unused code

### Slow Renders

1. Use React DevTools Profiler
2. Check for:
   - Missing `React.memo`
   - Missing dependency arrays
   - Unnecessary re-renders

3. Use `useRenderTime` hook to identify slow components

### Memory Leaks

1. Enable memory leak detection in development
2. Check for:
   - Event listeners not cleaned up
   - Subscriptions not cancelled
   - Large objects in closure

### Poor Web Vitals Scores

1. Run Lighthouse audit:
   ```bash
   npm run performance:test
   ```

2. Address issues in order of priority:
   - Critical: LCP, FID
   - Important: CLS, FCP
   - Nice-to-have: Other metrics

---

## Testing Performance

### Run Performance Tests

```bash
# Lighthouse performance audit
npm run performance:test

# Bundle analysis
npm run analyze

# E2E performance tests
npm run test:e2e
```

### Write Performance Tests

```javascript
// e2e/performance/custom.spec.js
import { test, expect } from '@playwright/test';

test('should load page quickly', async ({ page }) => {
  const startTime = Date.now();
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  const loadTime = Date.now() - startTime;
  
  expect(loadTime).toBeLessThan(3000);
});
```

---

## Additional Resources

- [Web.dev Performance Guide](https://web.dev/performance/)
- [React Performance Optimization](https://react.dev/learn/render-and-commit)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [Lighthouse Documentation](https://developer.chrome.com/docs/lighthouse/)

---

## Continuous Improvement

1. **Regular Audits**: Run performance audits quarterly
2. **Monitor Trends**: Track metrics over time
3. **User Feedback**: Listen to user experience reports
4. **Stay Updated**: Keep dependencies current
5. **Learn**: Follow performance best practices

For questions or suggestions, please create an issue using the performance optimization template.
