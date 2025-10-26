// Backend Integration Utilities
// Provides utilities and configurations for seamless backend integration

import { config } from '../config/config';
import { logger } from '../services/logger';
import api from '../services/api';

/**
 * Backend Integration Manager
 * Handles communication, data synchronization, and state management with backend services
 */
export const backendIntegration = {
  /**
   * API Configuration
   */
  config: {
    baseURL: config.api.baseUrl,
    wsURL: config.api.wsUrl,
    timeout: config.api.timeout,
    retryAttempts: config.api.retryAttempts,
    retryDelay: config.api.retryDelay,
  },

  /**
   * Connection Status
   */
  connectionStatus: {
    api: false,
    websocket: false,
    lastChecked: null,
  },

  /**
   * Check if backend is reachable
   */
  async checkHealth() {
    try {
      const response = await api.get('/health');
      this.connectionStatus.api = response.status === 'ok';
      this.connectionStatus.lastChecked = new Date().toISOString();
      logger.info('Backend health check successful', { status: response });
      return this.connectionStatus.api;
    } catch (error) {
      this.connectionStatus.api = false;
      this.connectionStatus.lastChecked = new Date().toISOString();
      logger.error('Backend health check failed', { error: error.message });
      return false;
    }
  },

  /**
   * Test API connectivity
   */
  async testConnection() {
    try {
      const response = await fetch(`${this.config.baseURL}/api/v1/system/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(5000),
      });

      if (response.ok) {
        const data = await response.json();
        logger.info('Backend connection test successful', { data });
        return { success: true, data };
      }

      return { success: false, error: 'Connection failed' };
    } catch (error) {
      logger.error('Backend connection test failed', { error: error.message });
      return { success: false, error: error.message };
    }
  },

  /**
   * Initialize backend connection
   */
  async initialize() {
    logger.info('Initializing backend integration...');

    try {
      // Test API connection
      const apiTest = await this.testConnection();
      if (!apiTest.success) {
        logger.warn('Backend API not reachable, using fallback mode');
      }

      // Check health endpoint
      await this.checkHealth();

      logger.info('Backend integration initialized', {
        apiConnected: this.connectionStatus.api,
      });

      return {
        success: true,
        apiConnected: this.connectionStatus.api,
      };
    } catch (error) {
      logger.error('Backend integration initialization failed', {
        error: error.message,
      });
      return {
        success: false,
        error: error.message,
      };
    }
  },

  /**
   * Get connection status
   */
  getStatus() {
    return {
      ...this.connectionStatus,
      config: {
        apiURL: this.config.baseURL,
        wsURL: this.config.wsURL,
      },
    };
  },

  /**
   * Validate backend requirements
   */
  async validateRequirements() {
    const requirements = {
      api: false,
      authentication: false,
      websocket: false,
      fileUpload: false,
      realtime: false,
    };

    try {
      // Check API endpoints
      const healthCheck = await this.checkHealth();
      requirements.api = healthCheck;

      // TODO: Add more validation as backend endpoints become available
      // - Authentication endpoint check
      // - WebSocket connection check
      // - File upload capability check
      // - Real-time features check

      logger.info('Backend requirements validated', { requirements });
      return requirements;
    } catch (error) {
      logger.error('Backend requirements validation failed', {
        error: error.message,
      });
      return requirements;
    }
  },

  /**
   * Backend API endpoints ready for integration
   */
  endpoints: {
    // Authentication
    auth: {
      login: '/api/v1/auth/login',
      logout: '/api/v1/auth/logout',
      register: '/api/v1/auth/register',
      refresh: '/api/v1/auth/refresh',
      verify: '/api/v1/auth/verify',
      resetPassword: '/api/v1/auth/reset-password',
      changePassword: '/api/v1/auth/change-password',
    },

    // Users
    users: {
      me: '/api/v1/users/me',
      list: '/api/v1/users',
      get: '/api/v1/users/:id',
      update: '/api/v1/users/:id',
      delete: '/api/v1/users/:id',
      avatar: '/api/v1/users/:id/avatar',
      preferences: '/api/v1/users/:id/preferences',
    },

    // Agents
    agents: {
      list: '/api/v1/agents',
      create: '/api/v1/agents',
      get: '/api/v1/agents/:id',
      update: '/api/v1/agents/:id',
      delete: '/api/v1/agents/:id',
      execute: '/api/v1/agents/:id/execute',
      stop: '/api/v1/agents/:id/stop',
      status: '/api/v1/agents/:id/status',
      logs: '/api/v1/agents/:id/logs',
      metrics: '/api/v1/agents/:id/metrics',
    },

    // Projects
    projects: {
      list: '/api/v1/projects',
      create: '/api/v1/projects',
      get: '/api/v1/projects/:id',
      update: '/api/v1/projects/:id',
      delete: '/api/v1/projects/:id',
      build: '/api/v1/projects/:id/build',
      deploy: '/api/v1/projects/:id/deploy',
      history: '/api/v1/projects/:id/history',
      files: '/api/v1/projects/:id/files',
    },

    // Chat
    chat: {
      conversations: '/api/v1/chat/conversations',
      messages: '/api/v1/chat/conversations/:id/messages',
      send: '/api/v1/chat/conversations/:id/send',
      history: '/api/v1/chat/conversations/:id/history',
    },

    // Files
    files: {
      upload: '/api/v1/files/upload',
      download: '/api/v1/files/:id/download',
      delete: '/api/v1/files/:id',
      list: '/api/v1/files',
      metadata: '/api/v1/files/:id/metadata',
    },

    // Analytics
    analytics: {
      dashboard: '/api/v1/analytics/dashboard',
      agents: '/api/v1/analytics/agents',
      projects: '/api/v1/analytics/projects',
      performance: '/api/v1/analytics/performance',
    },

    // Monitoring
    monitoring: {
      health: '/api/v1/monitoring/health',
      metrics: '/api/v1/monitoring/metrics',
      alerts: '/api/v1/monitoring/alerts',
      logs: '/api/v1/monitoring/logs',
      status: '/api/v1/monitoring/status',
    },

    // System
    system: {
      info: '/api/v1/system/info',
      config: '/api/v1/system/config',
      health: '/api/v1/system/health',
      version: '/api/v1/system/version',
    },
  },

  /**
   * WebSocket event types
   */
  wsEvents: {
    // Agent events
    agentCreated: 'agent:created',
    agentUpdated: 'agent:updated',
    agentDeleted: 'agent:deleted',
    agentStatusChanged: 'agent:status:changed',

    // Project events
    projectCreated: 'project:created',
    projectUpdated: 'project:updated',
    projectBuildStarted: 'project:build:started',
    projectBuildCompleted: 'project:build:completed',

    // Chat events
    messageReceived: 'chat:message:received',
    messageSent: 'chat:message:sent',
    userTyping: 'chat:user:typing',

    // System events
    systemAlert: 'system:alert',
    systemUpdate: 'system:update',
  },
};

/**
 * Export as default
 */
export default backendIntegration;
