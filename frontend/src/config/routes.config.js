// Routes Configuration
// Comprehensive configuration for frontend routes, API endpoints, and navigation

import env from './env';

export const routesConfig = {
  // Frontend Routes
  frontend: {
    // Public Routes (no authentication required)
    public: [
      {
        path: '/',
        name: 'Login',
        component: 'LoginPage',
        exact: true,
        title: 'Login - AgentFlow',
        description: 'Sign in to your AgentFlow account',
      },
      {
        path: '/login',
        name: 'Login',
        component: 'LoginPage',
        exact: true,
        title: 'Login - AgentFlow',
        description: 'Sign in to your AgentFlow account',
      },
    ],

    // Protected Routes (authentication required)
    protected: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: 'DashboardPage',
        icon: 'layout-dashboard',
        title: 'Dashboard - AgentFlow',
        description: 'System overview and metrics',
        permissions: ['view_dashboard'],
        showInNav: true,
      },
      {
        path: '/agents',
        name: 'Agents',
        component: 'AgentsPage',
        icon: 'bot',
        title: 'Agents - AgentFlow',
        description: 'Manage AI agents',
        permissions: ['view_agents', 'manage_agents'],
        showInNav: true,
      },
      {
        path: '/projects',
        name: 'Projects',
        component: 'ProjectsPage',
        icon: 'folder',
        title: 'Projects - AgentFlow',
        description: 'Project management',
        permissions: ['view_projects', 'manage_projects'],
        showInNav: true,
      },
      {
        path: '/projects/history',
        name: 'Project History',
        component: 'ProjectHistoryPage',
        icon: 'history',
        title: 'Project History - AgentFlow',
        description: 'View project activity history',
        permissions: ['view_projects'],
        showInNav: false,
      },
      {
        path: '/collaboration',
        name: 'Collaboration',
        component: 'CollaborationPage',
        icon: 'users',
        title: 'Collaboration - AgentFlow',
        description: 'Team collaboration workspace',
        permissions: ['view_collaboration'],
        showInNav: true,
      },
      {
        path: '/analytics',
        name: 'Analytics',
        component: 'AnalyticsPage',
        icon: 'bar-chart',
        title: 'Analytics - AgentFlow',
        description: 'Advanced analytics and insights',
        permissions: ['view_analytics'],
        showInNav: true,
      },
      {
        path: '/resources',
        name: 'Resources',
        component: 'ResourcesPage',
        icon: 'hard-drive',
        title: 'Resources - AgentFlow',
        description: 'Resource management',
        permissions: ['view_resources', 'manage_resources'],
        showInNav: true,
      },
      {
        path: '/monitoring',
        name: 'Monitoring',
        component: 'MonitoringPage',
        icon: 'activity',
        title: 'Monitoring - AgentFlow',
        description: 'Real-time system monitoring',
        permissions: ['view_monitoring'],
        showInNav: true,
      },
      {
        path: '/command',
        name: 'Command Center',
        component: 'CommandPage',
        icon: 'terminal',
        title: 'Command Center - AgentFlow',
        description: 'Admin command interface',
        permissions: ['admin'],
        showInNav: true,
        requiredRole: 'admin',
      },
      {
        path: '/settings',
        name: 'Settings',
        component: 'SettingsPage',
        icon: 'settings',
        title: 'Settings - AgentFlow',
        description: 'User preferences',
        permissions: ['view_settings'],
        showInNav: true,
      },
      {
        path: '/profile',
        name: 'Profile',
        component: 'ProfilePage',
        icon: 'user',
        title: 'Profile - AgentFlow',
        description: 'User profile management',
        permissions: ['view_profile'],
        showInNav: false,
      },
    ],

    // Error Routes
    error: [
      {
        path: '/404',
        name: 'Not Found',
        component: 'NotFoundPage',
        title: '404 - Page Not Found',
      },
      {
        path: '/403',
        name: 'Forbidden',
        component: 'ForbiddenPage',
        title: '403 - Access Denied',
      },
      {
        path: '/500',
        name: 'Server Error',
        component: 'ServerErrorPage',
        title: '500 - Server Error',
      },
    ],

    // Default redirect
    defaultRoute: '/dashboard',
    fallbackRoute: '/404',
  },

  // API Routes
  api: {
    baseUrl: env.apiBaseUrl,
    version: 'v1',
    timeout: env.apiTimeout,

    // Authentication endpoints
    auth: {
      login: '/api/v1/auth/login',
      logout: '/api/v1/auth/logout',
      register: '/api/v1/auth/register',
      refresh: '/api/v1/auth/refresh',
      verify: '/api/v1/auth/verify',
      resetPassword: '/api/v1/auth/reset-password',
      changePassword: '/api/v1/auth/change-password',
    },

    // User endpoints
    users: {
      me: '/api/v1/users/me',
      list: '/api/v1/users',
      get: '/api/v1/users/:id',
      update: '/api/v1/users/:id',
      delete: '/api/v1/users/:id',
      avatar: '/api/v1/users/:id/avatar',
      preferences: '/api/v1/users/:id/preferences',
    },

    // Agent endpoints
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

    // Project endpoints
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

    // Chat endpoints
    chat: {
      conversations: '/api/v1/chat/conversations',
      messages: '/api/v1/chat/conversations/:id/messages',
      send: '/api/v1/chat/conversations/:id/send',
      history: '/api/v1/chat/conversations/:id/history',
      participants: '/api/v1/chat/conversations/:id/participants',
      typing: '/api/v1/chat/conversations/:id/typing',
    },

    // File endpoints
    files: {
      upload: '/api/v1/files/upload',
      download: '/api/v1/files/:id/download',
      delete: '/api/v1/files/:id',
      list: '/api/v1/files',
      metadata: '/api/v1/files/:id/metadata',
      preview: '/api/v1/files/:id/preview',
    },

    // Analytics endpoints
    analytics: {
      dashboard: '/api/v1/analytics/dashboard',
      agents: '/api/v1/analytics/agents',
      projects: '/api/v1/analytics/projects',
      performance: '/api/v1/analytics/performance',
      usage: '/api/v1/analytics/usage',
      trends: '/api/v1/analytics/trends',
    },

    // Learning endpoints
    learning: {
      models: '/api/v1/learning/models',
      train: '/api/v1/learning/train',
      predict: '/api/v1/learning/predict',
      evaluate: '/api/v1/learning/evaluate',
      datasets: '/api/v1/learning/datasets',
    },

    // Resource endpoints
    resources: {
      list: '/api/v1/resources',
      allocate: '/api/v1/resources/allocate',
      deallocate: '/api/v1/resources/deallocate',
      usage: '/api/v1/resources/usage',
      limits: '/api/v1/resources/limits',
    },

    // Monitoring endpoints
    monitoring: {
      health: '/api/v1/monitoring/health',
      metrics: '/api/v1/monitoring/metrics',
      alerts: '/api/v1/monitoring/alerts',
      logs: '/api/v1/monitoring/logs',
      status: '/api/v1/monitoring/status',
    },

    // System endpoints
    system: {
      info: '/api/v1/system/info',
      config: '/api/v1/system/config',
      health: '/api/v1/system/health',
      version: '/api/v1/system/version',
    },
  },

  // WebSocket Routes
  websocket: {
    url: env.wsUrl,
    reconnect: true,
    reconnectAttempts: env.wsReconnectAttempts,
    reconnectDelay: env.wsReconnectDelay,

    channels: {
      agents: 'agents',
      projects: 'projects',
      chat: 'chat',
      notifications: 'notifications',
      monitoring: 'monitoring',
      system: 'system',
    },

    events: {
      // Agent events
      agentCreated: 'agent:created',
      agentUpdated: 'agent:updated',
      agentDeleted: 'agent:deleted',
      agentStatusChanged: 'agent:status:changed',
      agentExecutionStarted: 'agent:execution:started',
      agentExecutionCompleted: 'agent:execution:completed',
      agentExecutionFailed: 'agent:execution:failed',

      // Project events
      projectCreated: 'project:created',
      projectUpdated: 'project:updated',
      projectDeleted: 'project:deleted',
      projectBuildStarted: 'project:build:started',
      projectBuildCompleted: 'project:build:completed',
      projectBuildFailed: 'project:build:failed',

      // Chat events
      messageReceived: 'chat:message:received',
      messageSent: 'chat:message:sent',
      userTyping: 'chat:user:typing',
      userJoined: 'chat:user:joined',
      userLeft: 'chat:user:left',

      // System events
      systemAlert: 'system:alert',
      systemUpdate: 'system:update',
      systemHealthChanged: 'system:health:changed',
    },
  },

  // Route Middleware Configuration
  middleware: {
    authentication: {
      enabled: true,
      excludePaths: ['/', '/login', '/register'],
      redirectTo: '/login',
    },
    authorization: {
      enabled: true,
      checkPermissions: true,
      onUnauthorized: 'redirect', // 'redirect', 'error', 'hide'
      redirectTo: '/403',
    },
    analytics: {
      enabled: env.analyticsEnabled,
      trackPageViews: true,
      trackEvents: true,
    },
    logging: {
      enabled: true,
      logLevel: env.logLevel,
      includeUserInfo: env.isProduction,
    },
    rateLimit: {
      enabled: env.isProduction,
      maxRequests: 100,
      windowMs: 60000, // 1 minute
    },
  },

  // Navigation Configuration
  navigation: {
    showBreadcrumbs: true,
    showBackButton: true,
    animation: 'fade', // 'fade', 'slide', 'none'
    persistScroll: true,
    prefetch: env.isProduction,
  },

  // Route Guards
  guards: {
    authenticated: (user) => !!user,
    admin: (user) => user?.role === 'admin',
    hasPermission: (user, permission) => user?.permissions?.includes(permission),
    hasRole: (user, role) => user?.role === role,
  },
};

// Helper functions
export const getRoute = (name, params = {}) => {
  const allRoutes = [
    ...routesConfig.frontend.public,
    ...routesConfig.frontend.protected,
  ];
  
  const route = allRoutes.find(r => r.name === name);
  if (!route) {
    return null;
  }

  let path = route.path;
  Object.keys(params).forEach(key => {
    path = path.replace(`:${key}`, params[key]);
  });

  return path;
};

export const getApiEndpoint = (category, endpoint, params = {}) => {
  const categoryEndpoints = routesConfig.api[category];
  if (!categoryEndpoints) {
    return null;
  }

  let url = categoryEndpoints[endpoint];
  if (!url) {
    return null;
  }

  Object.keys(params).forEach(key => {
    url = url.replace(`:${key}`, params[key]);
  });

  return `${routesConfig.api.baseUrl}${url}`;
};

export const getNavigationRoutes = () => {
  return routesConfig.frontend.protected.filter(route => route.showInNav);
};

export const isPublicRoute = (path) => {
  return routesConfig.frontend.public.some(route => route.path === path);
};

export const isProtectedRoute = (path) => {
  return routesConfig.frontend.protected.some(route => route.path === path);
};

export default routesConfig;
