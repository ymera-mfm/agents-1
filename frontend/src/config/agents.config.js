// Agent System Configuration
// Comprehensive configuration for AI agents, their capabilities, lifecycle, and management

import env from './env';

export const agentsConfig = {
  // Agent Types and Capabilities
  types: {
    coder: {
      id: 'coder',
      name: 'Code Agent',
      description: 'Specialized in writing and reviewing code',
      capabilities: ['code_generation', 'code_review', 'refactoring', 'testing'],
      defaultModel: 'gpt-4',
      maxConcurrentTasks: 5,
      priority: 'high',
      color: '#3b82f6',
      icon: 'code',
    },
    analyst: {
      id: 'analyst',
      name: 'Analytics Agent',
      description: 'Analyzes data and provides insights',
      capabilities: ['data_analysis', 'reporting', 'visualization', 'predictions'],
      defaultModel: 'gpt-4',
      maxConcurrentTasks: 3,
      priority: 'medium',
      color: '#10b981',
      icon: 'chart',
    },
    security: {
      id: 'security',
      name: 'Security Agent',
      description: 'Monitors and ensures system security',
      capabilities: ['vulnerability_scan', 'threat_detection', 'compliance_check', 'audit'],
      defaultModel: 'gpt-4',
      maxConcurrentTasks: 10,
      priority: 'critical',
      color: '#ef4444',
      icon: 'shield',
    },
    designer: {
      id: 'designer',
      name: 'Design Agent',
      description: 'Creates and optimizes UI/UX designs',
      capabilities: ['ui_design', 'ux_optimization', 'prototyping', 'accessibility'],
      defaultModel: 'gpt-4',
      maxConcurrentTasks: 3,
      priority: 'medium',
      color: '#f59e0b',
      icon: 'palette',
    },
    tester: {
      id: 'tester',
      name: 'Testing Agent',
      description: 'Automated testing and quality assurance',
      capabilities: ['unit_testing', 'integration_testing', 'e2e_testing', 'performance_testing'],
      defaultModel: 'gpt-3.5-turbo',
      maxConcurrentTasks: 8,
      priority: 'high',
      color: '#8b5cf6',
      icon: 'test-tube',
    },
    devops: {
      id: 'devops',
      name: 'DevOps Agent',
      description: 'Manages deployment and infrastructure',
      capabilities: ['deployment', 'monitoring', 'scaling', 'ci_cd'],
      defaultModel: 'gpt-4',
      maxConcurrentTasks: 5,
      priority: 'high',
      color: '#06b6d4',
      icon: 'server',
    },
  },

  // Agent Lifecycle Configuration
  lifecycle: {
    initialization: {
      timeout: 30000, // 30 seconds
      retryAttempts: 3,
      healthCheckInterval: 10000, // 10 seconds
    },
    execution: {
      maxExecutionTime: 300000, // 5 minutes
      heartbeatInterval: 5000, // 5 seconds
      progressUpdateInterval: 1000, // 1 second
    },
    termination: {
      gracefulShutdownTimeout: 10000, // 10 seconds
      forceKillTimeout: 5000, // 5 seconds
      cleanupTimeout: 3000, // 3 seconds
    },
  },

  // Agent Orchestration
  orchestration: {
    maxConcurrentAgents: 20,
    queueSize: 100,
    priorityLevels: ['critical', 'high', 'medium', 'low'],
    schedulingStrategy: 'priority', // 'priority', 'fifo', 'round-robin'
    loadBalancing: true,
    autoScaling: {
      enabled: env.isProduction,
      minAgents: 2,
      maxAgents: 20,
      scaleUpThreshold: 0.8, // 80% capacity
      scaleDownThreshold: 0.3, // 30% capacity
      cooldownPeriod: 60000, // 1 minute
    },
  },

  // Agent Communication
  communication: {
    protocol: 'websocket',
    messageFormat: 'json',
    compression: true,
    encryption: env.httpsOnly,
    channels: {
      command: 'agent:command',
      status: 'agent:status',
      result: 'agent:result',
      error: 'agent:error',
      heartbeat: 'agent:heartbeat',
    },
    timeout: 30000, // 30 seconds
    retryPolicy: {
      maxRetries: 3,
      backoffMultiplier: 2,
      maxBackoff: 10000,
    },
  },

  // Agent Monitoring
  monitoring: {
    enabled: true,
    metrics: [
      'execution_time',
      'success_rate',
      'error_rate',
      'throughput',
      'resource_usage',
      'queue_depth',
    ],
    alerts: {
      highErrorRate: {
        threshold: 0.1, // 10% error rate
        window: 300000, // 5 minutes
        action: 'notify',
      },
      slowExecution: {
        threshold: 60000, // 1 minute
        action: 'investigate',
      },
      queueBacklog: {
        threshold: 50, // 50 tasks
        action: 'scale_up',
      },
    },
    logging: {
      level: env.logLevel,
      destinations: ['console', 'file', 'remote'],
      includeStackTrace: true,
      maxLogSize: 10485760, // 10MB
    },
  },

  // Agent Resource Limits
  resources: {
    memory: {
      min: 128, // MB
      max: 2048, // MB
      default: 512, // MB
    },
    cpu: {
      min: 0.1, // cores
      max: 2, // cores
      default: 0.5, // cores
    },
    disk: {
      max: 5120, // MB (5GB)
      cleanup: true,
    },
    network: {
      maxConcurrentConnections: 10,
      maxBandwidth: 10485760, // 10MB/s
    },
  },

  // Agent Security
  security: {
    authentication: {
      enabled: true,
      method: 'jwt',
      tokenExpiry: 3600000, // 1 hour
    },
    authorization: {
      enabled: true,
      roleBasedAccess: true,
      permissionModel: 'capability-based',
    },
    sandboxing: {
      enabled: env.isProduction,
      isolateFileSystem: true,
      isolateNetwork: false,
      allowedDomains: [env.apiBaseUrl],
    },
    encryption: {
      enabled: env.httpsOnly,
      algorithm: 'AES-256-GCM',
      keyRotation: true,
      keyRotationInterval: 86400000, // 24 hours
    },
  },

  // Agent Collaboration
  collaboration: {
    enabled: env.enableRealTimeCollaboration,
    maxCollaborators: 5,
    sharedContext: true,
    conflictResolution: 'last-write-wins', // 'last-write-wins', 'merge', 'manual'
    synchronization: {
      method: 'operational-transform',
      interval: 1000, // 1 second
    },
  },

  // Agent Training & Learning
  training: {
    enabled: false, // Disabled in frontend, handled by backend
    feedbackCollection: true,
    modelUpdates: {
      frequency: 'weekly',
      method: 'incremental',
    },
    performanceBaseline: {
      successRate: 0.9, // 90%
      averageExecutionTime: 30000, // 30 seconds
    },
  },

  // Agent API Endpoints
  endpoints: {
    list: '/api/agents',
    create: '/api/agents',
    get: '/api/agents/:id',
    update: '/api/agents/:id',
    delete: '/api/agents/:id',
    execute: '/api/agents/:id/execute',
    status: '/api/agents/:id/status',
    logs: '/api/agents/:id/logs',
    metrics: '/api/agents/:id/metrics',
  },

  // Agent UI Configuration
  ui: {
    defaultView: '3d', // '3d', 'grid', 'list'
    showMetrics: true,
    showLogs: env.isDevelopment,
    autoRefresh: true,
    refreshInterval: 5000, // 5 seconds
    animations: {
      enabled: true,
      duration: 300,
    },
    colors: {
      idle: '#64748b',
      running: '#3b82f6',
      success: '#10b981',
      error: '#ef4444',
      warning: '#f59e0b',
    },
  },

  // Development & Debug
  development: {
    mockAgents: env.mockApi,
    verboseLogging: env.debugMode,
    simulateDelays: false,
    errorSimulation: false,
  },
};

// Agent validation function
export const validateAgentConfig = (agentType) => {
  if (!agentsConfig.types[agentType]) {
    throw new Error(`Invalid agent type: ${agentType}`);
  }
  return true;
};

// Get agent type configuration
export const getAgentTypeConfig = (agentType) => {
  return agentsConfig.types[agentType] || null;
};

// Get all available agent types
export const getAvailableAgentTypes = () => {
  return Object.keys(agentsConfig.types);
};

export default agentsConfig;
