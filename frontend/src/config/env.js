// Environment Helper
// Provides access to environment variables without circular dependencies

export const env = {
  // Environment
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  version: process.env.REACT_APP_VERSION || '1.0.0',

  // API Configuration
  apiBaseUrl: process.env.REACT_APP_API_URL || 'http://localhost:3001',
  wsUrl: process.env.REACT_APP_WS_URL || 'ws://localhost:3001',
  apiTimeout: parseInt(process.env.REACT_APP_API_TIMEOUT) || 10000,

  // Feature Flags
  enable3DVisualization: process.env.REACT_APP_ENABLE_3D_VISUALIZATION === 'true',
  enableRealTimeCollaboration: process.env.REACT_APP_ENABLE_REAL_TIME_COLLABORATION === 'true',
  enableAdvancedAnalytics: process.env.REACT_APP_ENABLE_ADVANCED_ANALYTICS === 'true',
  enableAIAssistance: process.env.REACT_APP_ENABLE_AI_ASSISTANCE === 'true',
  enablePerformanceMonitoring: process.env.REACT_APP_ENABLE_PERFORMANCE_MONITORING === 'true',

  // Security
  enableCSP: process.env.REACT_APP_ENABLE_CSP === 'true',
  httpsOnly: process.env.REACT_APP_ENABLE_HTTPS_ONLY === 'true',
  sessionTimeout: parseInt(process.env.REACT_APP_SESSION_TIMEOUT) || 3600000,

  // Development
  debugMode: process.env.REACT_APP_DEBUG_MODE === 'true',
  mockApi: process.env.REACT_APP_MOCK_API === 'true',
  logLevel: process.env.REACT_APP_LOG_LEVEL || 'warn',

  // Analytics
  analyticsEnabled: process.env.REACT_APP_ANALYTICS_ENABLED === 'true',
  analyticsSampleRate: parseFloat(process.env.REACT_APP_ANALYTICS_SAMPLE_RATE) || 0.1,

  // UI
  primaryColor: '#3b82f6',

  // WebSocket
  wsReconnectAttempts: 5,
  wsReconnectDelay: 1000,
  wsHeartbeatInterval: 30000,
  wsMaxMessageSize: 1024 * 1024, // 1MB
};

export default env;
