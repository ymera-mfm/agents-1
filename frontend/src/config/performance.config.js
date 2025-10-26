/**
 * Performance Configuration
 * Centralized configuration for performance optimization features
 */

export const PERFORMANCE_CONFIG = {
  // Performance monitoring
  monitoring: {
    enabled: process.env.REACT_APP_PERFORMANCE_MONITORING === 'true',
    sampleRate: parseFloat(process.env.REACT_APP_PERFORMANCE_SAMPLE_RATE) || 1.0,
    reportInterval: 30000, // 30 seconds
  },

  // Bundle optimization
  bundle: {
    // Lazy loading thresholds
    lazyLoadThreshold: 100 * 1024, // 100KB
    chunkSizeWarning: 200 * 1024, // 200KB
    maxChunkSize: 500 * 1024, // 500KB
  },

  // Image optimization
  images: {
    lazyLoad: true,
    placeholder: 'blur',
    formats: ['webp', 'jpg'],
    quality: 85,
    sizes: {
      thumbnail: 150,
      small: 300,
      medium: 600,
      large: 1200,
      xlarge: 1920,
    },
  },

  // Caching strategy
  cache: {
    // API response caching
    apiCache: {
      enabled: true,
      ttl: 5 * 60 * 1000, // 5 minutes
      maxSize: 100, // Max 100 items in memory
    },

    // Component caching
    componentCache: {
      enabled: true,
      strategy: 'LRU', // Least Recently Used
    },

    // Asset caching
    assetCache: {
      enabled: true,
      maxAge: 7 * 24 * 60 * 60, // 7 days in seconds
    },
  },

  // Rendering optimization
  rendering: {
    // Virtual scrolling
    virtualScroll: {
      enabled: true,
      itemThreshold: 50, // Enable for lists > 50 items
      overscan: 5, // Number of items to render outside viewport
    },

    // Debounce/Throttle settings
    debounce: {
      search: 300, // 300ms for search
      resize: 150, // 150ms for window resize
      scroll: 100, // 100ms for scroll events
    },
  },

  // Network optimization
  network: {
    // Request batching
    batching: {
      enabled: true,
      maxBatchSize: 10,
      batchInterval: 50, // 50ms
    },

    // Retry strategy
    retry: {
      enabled: true,
      maxAttempts: 3,
      backoff: 'exponential', // 'linear' or 'exponential'
      initialDelay: 1000, // 1 second
    },

    // Request timeout
    timeout: 30000, // 30 seconds
  },

  // Memory management
  memory: {
    // Memory leak detection
    leakDetection: {
      enabled: process.env.NODE_ENV === 'development',
      threshold: 50 * 1024 * 1024, // 50MB increase threshold
      checkInterval: 10000, // 10 seconds
    },

    // Garbage collection hints
    gcHints: {
      enabled: true,
      idleThreshold: 5000, // 5 seconds of idle time
    },
  },

  // Performance budgets
  budgets: {
    // Core Web Vitals targets
    webVitals: {
      LCP: 2500, // Largest Contentful Paint (ms)
      FID: 100, // First Input Delay (ms)
      CLS: 0.1, // Cumulative Layout Shift
      FCP: 1800, // First Contentful Paint (ms)
      TTFB: 600, // Time to First Byte (ms)
    },

    // Resource budgets
    resources: {
      totalSize: 500 * 1024, // 500KB total
      scriptSize: 300 * 1024, // 300KB scripts
      cssSize: 50 * 1024, // 50KB CSS
      imageSize: 150 * 1024, // 150KB images
    },

    // Timing budgets
    timing: {
      pageLoad: 3000, // 3 seconds
      timeToInteractive: 3500, // 3.5 seconds
      apiResponse: 1000, // 1 second
    },
  },

  // Feature flags for optimizations
  features: {
    codesplitting: true,
    lazyLoading: true,
    prefetching: true,
    preloading: false, // Can cause bandwidth waste
    serviceWorker: true,
    webWorkers: false, // Enable when needed
    compression: true,
    minification: true,
  },
};

// Get performance config with environment overrides
export function getPerformanceConfig() {
  return {
    ...PERFORMANCE_CONFIG,
    // Environment-specific overrides
    monitoring: {
      ...PERFORMANCE_CONFIG.monitoring,
      enabled: process.env.NODE_ENV === 'production' ? PERFORMANCE_CONFIG.monitoring.enabled : true,
    },
  };
}

export default PERFORMANCE_CONFIG;
