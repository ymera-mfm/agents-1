/**
 * Performance Utilities Index
 * Central export for all performance optimization utilities
 */

export {
  default as performanceMonitor,
  measureRender,
  measureAsync,
  mark,
  measure,
} from './monitor';
export { default as bundleAnalyzer } from './bundleAnalyzer';
export { default as imageOptimizer } from './imageOptimizer';
export {
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
} from './reactOptimizations';

// Re-export performance config
export { PERFORMANCE_CONFIG, getPerformanceConfig } from '../../config/performance.config';
