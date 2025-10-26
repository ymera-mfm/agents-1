// Enhanced Configuration Management
export const config = {
  // Environment
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  version: process.env.REACT_APP_VERSION || '1.0.0',

  // API Configuration
  api: {
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:3001',
    wsUrl: process.env.REACT_APP_WS_URL || 'ws://localhost:3001',
    timeout: parseInt(process.env.REACT_APP_API_TIMEOUT) || 10000,
    retryAttempts: 3,
    retryDelay: 1000,
  },

  // Feature Flags
  features: {
    threeDVisualization: process.env.REACT_APP_ENABLE_3D_VISUALIZATION === 'true',
    realTimeCollaboration: process.env.REACT_APP_ENABLE_REAL_TIME_COLLABORATION === 'true',
    advancedAnalytics: process.env.REACT_APP_ENABLE_ADVANCED_ANALYTICS === 'true',
    aiAssistance: process.env.REACT_APP_ENABLE_AI_ASSISTANCE === 'true',
    performanceMonitoring: process.env.REACT_APP_ENABLE_PERFORMANCE_MONITORING === 'true',
  },

  // Performance Configuration
  performance: {
    maxAgents: parseInt(process.env.REACT_APP_MAX_AGENTS) || 50,
    maxProjects: parseInt(process.env.REACT_APP_MAX_PROJECTS) || 100,
    cacheTimeout: parseInt(process.env.REACT_APP_CACHE_TIMEOUT) || 300000,
    virtualScrollThreshold: parseInt(process.env.REACT_APP_VIRTUAL_SCROLL_THRESHOLD) || 50,
    debounceDelay: 300,
    throttleDelay: 100,
  },

  // Analytics Configuration
  analytics: {
    enabled: process.env.REACT_APP_ANALYTICS_ENABLED === 'true',
    sampleRate: parseFloat(process.env.REACT_APP_ANALYTICS_SAMPLE_RATE) || 0.1,
    errorReporting: process.env.REACT_APP_ERROR_REPORTING_ENABLED === 'true',
    endpoints: {
      performance: '/api/analytics/performance',
      errors: '/api/analytics/errors',
      usage: '/api/analytics/usage',
      events: '/api/analytics/events',
    },
  },

  // Security Configuration
  security: {
    enableCSP: process.env.REACT_APP_ENABLE_CSP === 'true',
    httpsOnly: process.env.REACT_APP_ENABLE_HTTPS_ONLY === 'true',
    sessionTimeout: parseInt(process.env.REACT_APP_SESSION_TIMEOUT) || 3600000,
    maxLoginAttempts: 5,
    lockoutDuration: 900000, // 15 minutes
  },

  // Development Configuration
  development: {
    debugMode: process.env.REACT_APP_DEBUG_MODE === 'true',
    mockApi: process.env.REACT_APP_MOCK_API === 'true',
    logLevel: process.env.REACT_APP_LOG_LEVEL || 'warn',
    showPerformanceMetrics: process.env.NODE_ENV === 'development',
  },

  // UI Configuration
  ui: {
    theme: {
      primary: '#3b82f6',
      secondary: '#64748b',
      accent: '#f59e0b',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#06b6d4',
    },
    animations: {
      duration: {
        fast: 150,
        normal: 300,
        slow: 500,
      },
      easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
    breakpoints: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
  },

  // WebSocket Configuration
  websocket: {
    reconnectAttempts: 5,
    reconnectDelay: 1000,
    heartbeatInterval: 30000,
    maxMessageSize: 1024 * 1024, // 1MB
  },

  // Cache Configuration
  cache: {
    defaultTTL: 300000, // 5 minutes
    maxSize: 100, // Maximum number of cached items
    strategies: {
      agents: 'memory',
      projects: 'memory',
      analytics: 'sessionStorage',
      user: 'localStorage',
    },
  },

  // Error Handling Configuration
  errorHandling: {
    maxRetries: 3,
    retryDelay: 1000,
    showUserFriendlyMessages: true,
    logErrors: true,
    reportErrors: process.env.NODE_ENV === 'production',
  },

  // Build Configuration
  build: {
    generateSourceMap: process.env.GENERATE_SOURCEMAP === 'true',
    inlineRuntimeChunk: process.env.INLINE_RUNTIME_CHUNK === 'true',
    optimization: process.env.NODE_ENV === 'production',
  },
};

// Legacy CONFIG export for backward compatibility
export const CONFIG = {
  API_BASE_URL: config.api.baseUrl,
  WS_URL: config.api.wsUrl,
  RETRY_ATTEMPTS: config.api.retryAttempts,
  RETRY_DELAY: config.api.retryDelay,
  CACHE_TTL: config.cache.defaultTTL,
  REQUEST_TIMEOUT: config.api.timeout,
};

// Configuration validation
export const validateConfig = () => {
  const errors = [];

  // Validate required environment variables
  if (!config.api.baseUrl) {
    errors.push('REACT_APP_API_URL is required');
  }

  if (!config.api.wsUrl) {
    errors.push('REACT_APP_WS_URL is required');
  }

  // Validate numeric values
  if (isNaN(config.performance.maxAgents) || config.performance.maxAgents <= 0) {
    errors.push('REACT_APP_MAX_AGENTS must be a positive number');
  }

  if (isNaN(config.performance.maxProjects) || config.performance.maxProjects <= 0) {
    errors.push('REACT_APP_MAX_PROJECTS must be a positive number');
  }

  // Validate analytics sample rate
  if (config.analytics.sampleRate < 0 || config.analytics.sampleRate > 1) {
    errors.push('REACT_APP_ANALYTICS_SAMPLE_RATE must be between 0 and 1');
  }

  if (errors.length > 0) {
    console.error('Configuration validation errors:', errors);
    if (config.isProduction) {
      throw new Error(`Configuration validation failed: ${errors.join(', ')}`);
    }
  }

  return errors.length === 0;
};

// Initialize configuration validation
validateConfig();

// Export all configuration modules
export { default as agentsConfig } from './agents.config';
export { default as routesConfig } from './routes.config';
export { default as learningConfig } from './learning.config';
export { default as enginesConfig } from './engines.config';
export { default as chatConfig } from './chat.config';
export { default as fileConfig } from './file.config';
export { default as performanceConfig } from './performance.config';
export { default as alertsConfig } from './alerts.config';

export default config;
