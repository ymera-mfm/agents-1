import { useState, useEffect, useCallback, useRef } from 'react';
import { config } from '../config/config';

export const usePerformanceMonitor = () => {
  const [metrics, setMetrics] = useState({
    fps: 0,
    memory: { used: 0, total: 0 },
    renderTime: 0,
    networkLatency: 0,
    errorCount: 0,
    bundleSize: 0,
    cacheHitRate: 0,
    apiResponseTime: 0,
  });

  const [isMonitoring, setIsMonitoring] = useState(false);
  const frameCount = useRef(0);
  const lastTime = useRef(performance.now());
  const metricsRef = useRef(metrics);
  const observerRef = useRef(null);

  // Update metrics reference
  useEffect(() => {
    metricsRef.current = metrics;
  }, [metrics]);

  // Performance observer for advanced metrics
  const initializePerformanceObserver = useCallback(() => {
    if (!window.PerformanceObserver) {
      return;
    }

    try {
      observerRef.current = new PerformanceObserver((list) => {
        const entries = list.getEntries();

        entries.forEach((entry) => {
          switch (entry.entryType) {
            case 'measure':
              if (entry.name.includes('React')) {
                setMetrics((prev) => ({
                  ...prev,
                  renderTime: entry.duration,
                }));
              }
              break;
            case 'navigation':
              setMetrics((prev) => ({
                ...prev,
                networkLatency: entry.responseStart - entry.requestStart,
              }));
              break;
            case 'resource':
              if (entry.name.includes('api')) {
                setMetrics((prev) => ({
                  ...prev,
                  apiResponseTime: entry.duration,
                }));
              }
              break;
            default:
              break;
          }
        });
      });

      observerRef.current.observe({
        entryTypes: ['measure', 'navigation', 'resource', 'paint'],
      });
    } catch (error) {
      console.warn('Performance Observer not supported:', error);
    }
  }, []);

  // Enhanced performance measurement
  const measurePerformance = useCallback((currentTime) => {
    frameCount.current++;

    // Update FPS every second
    if (currentTime - lastTime.current >= 1000) {
      const fps = Math.round((frameCount.current * 1000) / (currentTime - lastTime.current));

      setMetrics((prev) => ({
        ...prev,
        fps,
      }));

      frameCount.current = 0;
      lastTime.current = currentTime;

      // Memory usage (Chrome only)
      if (performance.memory) {
        setMetrics((prev) => ({
          ...prev,
          memory: {
            used: Math.round(performance.memory.usedJSHeapSize / 1048576),
            total: Math.round(performance.memory.totalJSHeapSize / 1048576),
          },
        }));
      }

      // Bundle size analysis
      analyzeBundleSize();

      // Cache hit rate monitoring
      monitorCacheHitRate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Bundle size analysis
  const analyzeBundleSize = useCallback(() => {
    try {
      const entries = performance.getEntriesByType('resource');
      let totalSize = 0;

      entries.forEach((entry) => {
        if (entry.name.includes('.js') || entry.name.includes('.css')) {
          totalSize += entry.transferSize || 0;
        }
      });

      setMetrics((prev) => ({
        ...prev,
        bundleSize: Math.round(totalSize / 1024), // KB
      }));
    } catch (error) {
      console.warn('Bundle size analysis failed:', error);
    }
  }, []);

  // Cache hit rate monitoring
  const monitorCacheHitRate = useCallback(() => {
    const cacheStats = JSON.parse(localStorage.getItem('cacheStats') || '{"hits": 0, "misses": 0}');
    const total = cacheStats.hits + cacheStats.misses;
    const hitRate = total > 0 ? (cacheStats.hits / total) * 100 : 0;

    setMetrics((prev) => ({
      ...prev,
      cacheHitRate: Math.round(hitRate * 100) / 100,
    }));
  }, []);

  // Error tracking
  const trackError = useCallback((error) => {
    setMetrics((prev) => ({
      ...prev,
      errorCount: prev.errorCount + 1,
    }));

    // Report to analytics if enabled
    if (config.analytics.enabled && config.analytics.errorReporting) {
      fetch(config.analytics.endpoints.errors, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: error.message,
          stack: error.stack,
          timestamp: new Date().toISOString(),
          url: window.location.href,
          userAgent: navigator.userAgent,
          metrics: metricsRef.current,
        }),
      }).catch(() => {
        // Silently fail if analytics endpoint is not available
      });
    }
  }, []);

  // Get performance score
  const getPerformanceScore = useCallback(() => {
    const weights = {
      fps: 0.3,
      memory: 0.2,
      renderTime: 0.2,
      apiResponseTime: 0.15,
      cacheHitRate: 0.1,
      errorCount: 0.05,
    };

    let score = 100;

    // Deduct points based on metrics
    if (metrics.fps < 60) {
      score -= (60 - metrics.fps) * weights.fps;
    }
    if (metrics.memory.used > 50) {
      score -= (metrics.memory.used - 50) * weights.memory;
    }
    if (metrics.renderTime > 16) {
      score -= (metrics.renderTime - 16) * weights.renderTime;
    }
    if (metrics.apiResponseTime > 1000) {
      score -= ((metrics.apiResponseTime - 1000) / 10) * weights.apiResponseTime;
    }
    if (metrics.cacheHitRate < 80) {
      score -= (80 - metrics.cacheHitRate) * weights.cacheHitRate;
    }
    score -= metrics.errorCount * 10 * weights.errorCount;

    return Math.max(0, Math.min(100, Math.round(score)));
  }, [metrics]);

  // Start monitoring
  const startMonitoring = useCallback(() => {
    if (!config.features.performanceMonitoring) {
      return;
    }

    setIsMonitoring(true);
    initializePerformanceObserver();

    let animationFrameId;
    const performanceLoop = (currentTime) => {
      measurePerformance(currentTime);
      if (isMonitoring) {
        animationFrameId = requestAnimationFrame(performanceLoop);
      }
    };

    animationFrameId = requestAnimationFrame(performanceLoop);

    return () => {
      cancelAnimationFrame(animationFrameId);
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [isMonitoring, initializePerformanceObserver, measurePerformance]);

  // Initialize monitoring
  useEffect(() => {
    const cleanup = startMonitoring();

    return () => {
      cleanup?.();
      setIsMonitoring(false);
    };
  }, [startMonitoring]);

  // Global error handler
  useEffect(() => {
    const handleError = (event) => {
      trackError(event.error || new Error(event.message));
    };

    const handleUnhandledRejection = (event) => {
      trackError(new Error(event.reason));
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, [trackError]);

  return {
    ...metrics,
    performanceScore: getPerformanceScore(),
    trackError,
    isMonitoring,
  };
};

// Component performance wrapper
export const withPerformanceMonitor = (Component, componentName) => {
  return (props) => {
    const startTime = useRef(performance.now());

    useEffect(() => {
      const endTime = performance.now();
      const renderTime = endTime - startTime.current;

      // Log slow renders
      if (renderTime > 16) {
        // 60fps threshold
        console.warn(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`);
      }
    });

    return <Component {...props} />;
  };
};
