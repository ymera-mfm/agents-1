/**
 * Performance Monitor
 * Tracks and reports performance metrics for the application
 */

import { PERFORMANCE_CONFIG } from '../../config/performance.config';

class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.observers = [];
    this.isMonitoring = PERFORMANCE_CONFIG.monitoring.enabled;

    if (this.isMonitoring) {
      this.initializeObservers();
      this.startMonitoring();
    }
  }

  /**
   * Initialize performance observers
   */
  initializeObservers() {
    // Observe long tasks
    if ('PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric('long-task', {
              duration: entry.duration,
              startTime: entry.startTime,
              name: entry.name,
            });
          }
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (e) {
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.warn('Long task observer not supported:', e);
        }
      }

      // Observe layout shifts
      try {
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              this.recordMetric('layout-shift', {
                value: entry.value,
                startTime: entry.startTime,
              });
            }
          }
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(clsObserver);
      } catch (e) {
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.warn('Layout shift observer not supported:', e);
        }
      }

      // Observe resource timing
      try {
        const resourceObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordResourceMetric(entry);
          }
        });
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.push(resourceObserver);
      } catch (e) {
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.warn('Resource observer not supported:', e);
        }
      }
    }
  }

  /**
   * Start monitoring performance
   */
  startMonitoring() {
    // Report metrics periodically
    this.reportInterval = setInterval(() => {
      this.reportMetrics();
    }, PERFORMANCE_CONFIG.monitoring.reportInterval);

    // Monitor memory usage
    if (performance.memory) {
      this.memoryInterval = setInterval(() => {
        this.recordMemoryMetrics();
      }, 10000); // Every 10 seconds
    }
  }

  /**
   * Record a performance metric
   */
  recordMetric(name, data) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }

    this.metrics.get(name).push({
      ...data,
      timestamp: Date.now(),
    });

    // Keep only recent metrics (last 100)
    const metrics = this.metrics.get(name);
    if (metrics.length > 100) {
      metrics.shift();
    }
  }

  /**
   * Record resource timing metric
   */
  recordResourceMetric(entry) {
    const metric = {
      name: entry.name,
      type: entry.initiatorType,
      size: entry.transferSize,
      duration: entry.duration,
      startTime: entry.startTime,
    };

    this.recordMetric('resource', metric);

    // Check against budgets
    this.checkResourceBudget(metric);
  }

  /**
   * Record memory metrics
   */
  recordMemoryMetrics() {
    if (!performance.memory) {
      return;
    }

    const memory = {
      usedJSHeapSize: performance.memory.usedJSHeapSize,
      totalJSHeapSize: performance.memory.totalJSHeapSize,
      jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
      timestamp: Date.now(),
    };

    this.recordMetric('memory', memory);

    // Check for potential memory leaks
    this.checkMemoryLeak(memory);
  }

  /**
   * Check resource against performance budget
   */
  checkResourceBudget(metric) {
    const budgets = PERFORMANCE_CONFIG.budgets.resources;

    if (process.env.NODE_ENV === 'development') {
      if (metric.type === 'script' && metric.size > budgets.scriptSize) {
        // eslint-disable-next-line no-console
        console.warn(`Script size exceeds budget: ${metric.name} (${metric.size} bytes)`);
      }

      if (metric.type === 'css' && metric.size > budgets.cssSize) {
        // eslint-disable-next-line no-console
        console.warn(`CSS size exceeds budget: ${metric.name} (${metric.size} bytes)`);
      }

      if ((metric.type === 'img' || metric.type === 'image') && metric.size > budgets.imageSize) {
        // eslint-disable-next-line no-console
        console.warn(`Image size exceeds budget: ${metric.name} (${metric.size} bytes)`);
      }
    }
  }

  /**
   * Check for potential memory leaks
   */
  checkMemoryLeak(currentMemory) {
    const memoryMetrics = this.metrics.get('memory');
    if (!memoryMetrics || memoryMetrics.length < 2) {
      return;
    }

    const previousMemory = memoryMetrics[memoryMetrics.length - 2];
    const increase = currentMemory.usedJSHeapSize - previousMemory.usedJSHeapSize;

    if (increase > PERFORMANCE_CONFIG.memory.leakDetection.threshold) {
      if (process.env.NODE_ENV === 'development') {
        // eslint-disable-next-line no-console
        console.warn(
          `Potential memory leak detected: ${(increase / 1024 / 1024).toFixed(2)}MB increase`,
          {
            previous: (previousMemory.usedJSHeapSize / 1024 / 1024).toFixed(2) + 'MB',
            current: (currentMemory.usedJSHeapSize / 1024 / 1024).toFixed(2) + 'MB',
          }
        );
      }
    }
  }

  /**
   * Measure component render time
   */
  measureRender(componentName, callback) {
    if (!this.isMonitoring) {
      return callback();
    }

    const startTime = performance.now();
    const result = callback();
    const duration = performance.now() - startTime;

    this.recordMetric('render', {
      component: componentName,
      duration,
    });

    // Warn about slow renders
    if (duration > 16 && process.env.NODE_ENV === 'development') {
      // More than one frame (60fps)
      // eslint-disable-next-line no-console
      console.warn(`Slow render detected: ${componentName} took ${duration.toFixed(2)}ms`);
    }

    return result;
  }

  /**
   * Measure async operation
   */
  async measureAsync(operationName, asyncFn) {
    if (!this.isMonitoring) {
      return asyncFn();
    }

    const startTime = performance.now();
    try {
      const result = await asyncFn();
      const duration = performance.now() - startTime;

      this.recordMetric('async-operation', {
        name: operationName,
        duration,
        status: 'success',
      });

      return result;
    } catch (error) {
      const duration = performance.now() - startTime;

      this.recordMetric('async-operation', {
        name: operationName,
        duration,
        status: 'error',
        error: error.message,
      });

      throw error;
    }
  }

  /**
   * Get performance metrics summary
   */
  getMetrics() {
    const summary = {};

    for (const [name, metrics] of this.metrics) {
      if (metrics.length === 0) {
        continue;
      }

      summary[name] = {
        count: metrics.length,
        latest: metrics[metrics.length - 1],
      };

      // Calculate averages for numeric metrics
      if (name === 'render' || name === 'async-operation') {
        const durations = metrics.map((m) => m.duration);
        summary[name].average = durations.reduce((a, b) => a + b, 0) / durations.length;
        summary[name].max = Math.max(...durations);
        summary[name].min = Math.min(...durations);
      }
    }

    return summary;
  }

  /**
   * Report metrics (override this to send to analytics)
   */
  reportMetrics() {
    const metrics = this.getMetrics();

    // In development, log to console
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.log('Performance Metrics:', metrics);
    }

    // In production, send to analytics
    if (process.env.NODE_ENV === 'production' && window.gtag) {
      // Example: Send to Google Analytics
      Object.entries(metrics).forEach(([name, data]) => {
        if (data.average) {
          window.gtag('event', 'performance', {
            event_category: name,
            value: Math.round(data.average),
          });
        }
      });
    }
  }

  /**
   * Get Core Web Vitals
   */
  getWebVitals() {
    const vitals = {};

    // Get paint timings
    const paintEntries = performance.getEntriesByType('paint');
    paintEntries.forEach((entry) => {
      vitals[entry.name] = entry.startTime;
    });

    // Get navigation timing
    const navigationTiming = performance.getEntriesByType('navigation')[0];
    if (navigationTiming) {
      vitals.domContentLoaded =
        navigationTiming.domContentLoadedEventEnd - navigationTiming.domContentLoadedEventStart;
      vitals.loadComplete = navigationTiming.loadEventEnd - navigationTiming.loadEventStart;
    }

    return vitals;
  }

  /**
   * Clear metrics
   */
  clearMetrics() {
    this.metrics.clear();
  }

  /**
   * Stop monitoring
   */
  stopMonitoring() {
    if (this.reportInterval) {
      clearInterval(this.reportInterval);
    }

    if (this.memoryInterval) {
      clearInterval(this.memoryInterval);
    }

    this.observers.forEach((observer) => observer.disconnect());
    this.observers = [];
  }

  /**
   * Mark a custom performance marker
   */
  mark(name) {
    if ('performance' in window && 'mark' in performance) {
      performance.mark(name);
    }
  }

  /**
   * Measure between two markers
   */
  measure(name, startMark, endMark) {
    if ('performance' in window && 'measure' in performance) {
      try {
        performance.measure(name, startMark, endMark);
        const measure = performance.getEntriesByName(name, 'measure')[0];
        if (measure) {
          this.recordMetric('measure', {
            name,
            duration: measure.duration,
          });
        }
      } catch (e) {
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.warn('Performance measure failed:', e);
        }
      }
    }
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Export convenience functions
export const measureRender = (name, callback) => performanceMonitor.measureRender(name, callback);
export const measureAsync = (name, asyncFn) => performanceMonitor.measureAsync(name, asyncFn);
export const mark = (name) => performanceMonitor.mark(name);
export const measure = (name, start, end) => performanceMonitor.measure(name, start, end);

export default performanceMonitor;
