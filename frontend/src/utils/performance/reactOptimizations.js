/**
 * React Performance Utilities
 * Helper functions for optimizing React components
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { PERFORMANCE_CONFIG } from '../../config/performance.config';

/**
 * Debounce hook
 * Delays the execution of a function until after a specified delay
 */
export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Throttle hook
 * Limits the rate at which a function can fire
 */
export function useThrottle(value, limit = 300) {
  const [throttledValue, setThrottledValue] = useState(value);
  const lastRan = useRef(Date.now());

  useEffect(() => {
    const handler = setTimeout(
      () => {
        if (Date.now() - lastRan.current >= limit) {
          setThrottledValue(value);
          lastRan.current = Date.now();
        }
      },
      limit - (Date.now() - lastRan.current)
    );

    return () => {
      clearTimeout(handler);
    };
  }, [value, limit]);

  return throttledValue;
}

/**
 * Lazy component loader with retry
 */
export function lazyWithRetry(componentImport, retries = 3) {
  return new Promise((resolve, reject) => {
    const attemptLoad = (retriesLeft) => {
      componentImport()
        .then(resolve)
        .catch((error) => {
          if (retriesLeft === 0) {
            reject(error);
            return;
          }

          // Wait before retrying (exponential backoff)
          const delay = Math.pow(2, retries - retriesLeft) * 1000;
          setTimeout(() => {
            if (process.env.NODE_ENV === 'development') {
              // eslint-disable-next-line no-console
              console.log(`Retrying component load... (${retriesLeft} attempts left)`);
            }
            attemptLoad(retriesLeft - 1);
          }, delay);
        });
    };

    attemptLoad(retries);
  });
}

/**
 * Hook for detecting slow renders
 */
export function useRenderTime(componentName) {
  const renderTimeRef = useRef(0);
  const renderCountRef = useRef(0);

  useEffect(() => {
    renderCountRef.current += 1;
    const startTime = performance.now();

    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      renderTimeRef.current = renderTime;

      if (renderTime > 16) {
        // More than one frame at 60fps
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.warn(
            `[Performance] Slow render detected in ${componentName}:`,
            `${renderTime.toFixed(2)}ms (render #${renderCountRef.current})`
          );
        }
      }
    };
  });

  return {
    renderTime: renderTimeRef.current,
    renderCount: renderCountRef.current,
  };
}

/**
 * Hook for intersection observer (lazy loading)
 */
export function useIntersectionObserver(elementRef, options = {}, onIntersect) {
  const { threshold = 0, root = null, rootMargin = '0px', freezeOnceVisible = false } = options;

  useEffect(() => {
    const element = elementRef.current;
    if (!element) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        const isIntersecting = entry.isIntersecting;

        if (isIntersecting && onIntersect) {
          onIntersect(entry);
        }

        if (isIntersecting && freezeOnceVisible) {
          observer.unobserve(element);
        }
      },
      { threshold, root, rootMargin }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [elementRef, threshold, root, rootMargin, freezeOnceVisible, onIntersect]);
}

/**
 * Hook for window resize with debounce
 */
export function useWindowSize(debounceDelay = PERFORMANCE_CONFIG.rendering.debounce.resize) {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });

  useEffect(() => {
    let timeoutId;

    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        setWindowSize({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }, debounceDelay);
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(timeoutId);
    };
  }, [debounceDelay]);

  return windowSize;
}

/**
 * Hook for idle callback
 */
export function useIdleCallback(callback, options = {}) {
  const { timeout = 1000 } = options;
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if ('requestIdleCallback' in window) {
      const handle = window.requestIdleCallback(
        () => {
          callbackRef.current();
        },
        { timeout }
      );

      return () => {
        window.cancelIdleCallback(handle);
      };
    } else {
      // Fallback for browsers without requestIdleCallback
      const timer = setTimeout(() => {
        callbackRef.current();
      }, timeout);

      return () => {
        clearTimeout(timer);
      };
    }
  }, [timeout]);
}

/**
 * Memoized event handler creator
 */
export function useEventCallback(fn) {
  const ref = useRef(fn);

  useEffect(() => {
    ref.current = fn;
  });

  return useCallback((...args) => {
    return ref.current?.(...args);
  }, []);
}

/**
 * Hook for preventing unnecessary re-renders
 */
export function useDeepCompareMemo(factory, deps) {
  const ref = useRef(deps);
  const signalRef = useRef(0);

  if (!deepEqual(deps, ref.current)) {
    ref.current = deps;
    signalRef.current += 1;
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  return useMemo(factory, [signalRef.current]);
}

/**
 * Deep equality check
 */
function deepEqual(obj1, obj2) {
  if (obj1 === obj2) {
    return true;
  }
  if (obj1 === null || obj2 === null) {
    return false;
  }
  if (typeof obj1 !== 'object' || typeof obj2 !== 'object') {
    return false;
  }

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) {
    return false;
  }

  for (const key of keys1) {
    if (!keys2.includes(key) || !deepEqual(obj1[key], obj2[key])) {
      return false;
    }
  }

  return true;
}

/**
 * Hook for component mount/unmount tracking
 */
export function useComponentLifecycle(componentName) {
  const mountTimeRef = useRef(Date.now());

  useEffect(() => {
    const mountTime = Date.now();
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.log(`[Lifecycle] ${componentName} mounted`);
    }

    return () => {
      const lifetime = Date.now() - mountTime;
      if (process.env.NODE_ENV === 'development') {
        // eslint-disable-next-line no-console
        console.log(`[Lifecycle] ${componentName} unmounted after ${lifetime}ms`);
      }
    };
  }, [componentName]);

  return mountTimeRef.current;
}

/**
 * Hook for async data with loading state
 */
export function useAsync(asyncFunction, immediate = true) {
  const [status, setStatus] = useState('idle');
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const execute = useCallback(
    async (...args) => {
      setStatus('pending');
      setData(null);
      setError(null);

      try {
        const response = await asyncFunction(...args);
        setData(response);
        setStatus('success');
        return response;
      } catch (error) {
        setError(error);
        setStatus('error');
        throw error;
      }
    },
    [asyncFunction]
  );

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { execute, status, data, error, loading: status === 'pending' };
}

/**
 * Create a memoized selector
 */
export function createMemoizedSelector(selector) {
  const cache = new WeakMap();

  return (state) => {
    if (cache.has(state)) {
      return cache.get(state);
    }

    const result = selector(state);
    cache.set(state, result);
    return result;
  };
}

const performanceUtils = {
  useDebounce,
  useThrottle,
  lazyWithRetry,
  useRenderTime,
  useIntersectionObserver,
  useWindowSize,
  useIdleCallback,
  useEventCallback,
  useDeepCompareMemo,
  useComponentLifecycle,
  useAsync,
  createMemoizedSelector,
};

export default performanceUtils;
