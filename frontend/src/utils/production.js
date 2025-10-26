// config/production.js
export const productionConfig = {
  // Performance optimizations
  performance: {
    maxAgents: 50,
    maxProjects: 100,
    cacheTimeout: 300000, // 5 minutes
    virtualScrollThreshold: 50,
  },

  // Error handling
  errorHandling: {
    maxRetries: 3,
    timeout: 10000,
    reportErrors: true,
    logLevel: 'warn',
  },

  // Analytics
  analytics: {
    enabled: true,
    sampleRate: 0.1,
    endpoints: {
      performance: '/api/analytics/performance',
      errors: '/api/analytics/errors',
      usage: '/api/analytics/usage',
    },
  },

  // Feature flags
  features: {
    threeDVisualization: true,
    realTimeCollaboration: true,
    advancedAnalytics: true,
    aiAssistance: true,
  },
};

// services/errorTracking.js
export class ErrorTrackingService {
  static init() {
    if (process.env.NODE_ENV === 'production') {
      // Initialize error tracking service
      window.addEventListener('error', this.handleError);
      window.addEventListener('unhandledrejection', this.handlePromiseRejection);
    }
  }

  static handleError(event) {
    const errorInfo = {
      message: event.error?.message,
      stack: event.error?.stack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    // Send to analytics service
    this.reportError(errorInfo);
  }

  static handlePromiseRejection(event) {
    this.handleError({
      error: event.reason,
      message: event.reason?.message || 'Unhandled Promise Rejection',
    });
  }

  static reportError(errorInfo) {
    fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorInfo),
    }).catch(() => {
      // Fallback error logging
      console.error('Error reporting failed:', errorInfo);
    });
  }
}
