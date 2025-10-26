// Engines Configuration
// Comprehensive configuration for processing engines, workers, and queue management

import env from './env';

export const enginesConfig = {
  // Processing Engines
  engines: {
    code: {
      id: 'code-engine',
      name: 'Code Processing Engine',
      description: 'Handles code generation, analysis, and transformation',
      type: 'code',
      enabled: true,
      priority: 'high',
      workers: {
        min: 2,
        max: 10,
        default: 4,
      },
      capabilities: [
        'code_generation',
        'code_review',
        'refactoring',
        'linting',
        'formatting',
        'compilation',
      ],
      languages: ['javascript', 'typescript', 'python', 'java', 'go', 'rust'],
      maxConcurrentTasks: 20,
      timeout: 300000, // 5 minutes
      resources: {
        memory: 1024, // MB
        cpu: 1, // cores
      },
    },
    build: {
      id: 'build-engine',
      name: 'Build Engine',
      description: 'Manages project building and compilation',
      type: 'build',
      enabled: true,
      priority: 'high',
      workers: {
        min: 1,
        max: 5,
        default: 2,
      },
      capabilities: [
        'compilation',
        'bundling',
        'minification',
        'optimization',
        'asset_processing',
      ],
      buildTools: ['webpack', 'vite', 'rollup', 'esbuild', 'parcel'],
      maxConcurrentTasks: 10,
      timeout: 600000, // 10 minutes
      resources: {
        memory: 2048, // MB
        cpu: 2, // cores
      },
    },
    test: {
      id: 'test-engine',
      name: 'Testing Engine',
      description: 'Executes automated tests and quality checks',
      type: 'test',
      enabled: true,
      priority: 'medium',
      workers: {
        min: 1,
        max: 8,
        default: 3,
      },
      capabilities: [
        'unit_testing',
        'integration_testing',
        'e2e_testing',
        'performance_testing',
        'security_testing',
        'coverage_analysis',
      ],
      frameworks: ['jest', 'playwright', 'cypress', 'mocha', 'vitest'],
      maxConcurrentTasks: 15,
      timeout: 900000, // 15 minutes
      resources: {
        memory: 1536, // MB
        cpu: 1.5, // cores
      },
    },
    deploy: {
      id: 'deploy-engine',
      name: 'Deployment Engine',
      description: 'Handles application deployment and updates',
      type: 'deploy',
      enabled: true,
      priority: 'critical',
      workers: {
        min: 1,
        max: 3,
        default: 1,
      },
      capabilities: [
        'containerization',
        'orchestration',
        'rollout',
        'rollback',
        'health_checks',
      ],
      platforms: ['docker', 'kubernetes', 'vercel', 'netlify', 'aws'],
      maxConcurrentTasks: 5,
      timeout: 1200000, // 20 minutes
      resources: {
        memory: 2048, // MB
        cpu: 2, // cores
      },
    },
    analytics: {
      id: 'analytics-engine',
      name: 'Analytics Engine',
      description: 'Processes and analyzes system data',
      type: 'analytics',
      enabled: env.enableAdvancedAnalytics,
      priority: 'low',
      workers: {
        min: 1,
        max: 4,
        default: 2,
      },
      capabilities: [
        'data_processing',
        'aggregation',
        'visualization',
        'reporting',
        'predictions',
      ],
      maxConcurrentTasks: 20,
      timeout: 180000, // 3 minutes
      resources: {
        memory: 1024, // MB
        cpu: 1, // cores
      },
    },
    ml: {
      id: 'ml-engine',
      name: 'Machine Learning Engine',
      description: 'Handles ML model training and inference',
      type: 'ml',
      enabled: env.enableAIAssistance,
      priority: 'medium',
      workers: {
        min: 0,
        max: 2,
        default: 1,
      },
      capabilities: [
        'training',
        'inference',
        'evaluation',
        'feature_engineering',
      ],
      frameworks: ['tensorflow', 'pytorch', 'scikit-learn'],
      maxConcurrentTasks: 5,
      timeout: 3600000, // 1 hour
      resources: {
        memory: 4096, // MB
        cpu: 2, // cores
        gpu: false,
      },
    },
  },

  // Queue Management
  queue: {
    type: 'priority', // 'priority', 'fifo', 'lifo'
    maxSize: 1000,
    persistence: env.isProduction,
    storage: 'redis', // 'memory', 'redis', 'database'
    
    priorities: {
      critical: 4,
      high: 3,
      medium: 2,
      low: 1,
    },

    retry: {
      enabled: true,
      maxAttempts: 3,
      backoffStrategy: 'exponential', // 'fixed', 'exponential'
      initialDelay: 1000, // 1 second
      maxDelay: 60000, // 1 minute
      backoffMultiplier: 2,
    },

    deadLetter: {
      enabled: env.isProduction,
      maxRetries: 3,
      storage: 'database',
      alertOnDead: true,
    },

    monitoring: {
      enabled: true,
      metrics: [
        'queue_depth',
        'processing_rate',
        'wait_time',
        'completion_rate',
        'error_rate',
      ],
      alerts: {
        queueBacklog: {
          threshold: 100,
          action: 'scale_workers',
        },
        highErrorRate: {
          threshold: 0.1, // 10%
          action: 'notify_admin',
        },
        longWaitTime: {
          threshold: 60000, // 1 minute
          action: 'increase_priority',
        },
      },
    },
  },

  // Worker Configuration
  workers: {
    autoScaling: {
      enabled: env.isProduction,
      strategy: 'cpu_based', // 'cpu_based', 'queue_based', 'hybrid'
      scaleUpThreshold: 0.8, // 80% utilization
      scaleDownThreshold: 0.3, // 30% utilization
      cooldownPeriod: 60000, // 1 minute
      maxWorkers: 50,
      minWorkers: 5,
    },

    healthChecks: {
      enabled: true,
      interval: 10000, // 10 seconds
      timeout: 5000, // 5 seconds
      maxFailures: 3,
      restartOnFailure: true,
    },

    lifecycle: {
      gracefulShutdown: true,
      shutdownTimeout: 30000, // 30 seconds
      completePendingTasks: true,
      signalHandling: true,
    },

    resources: {
      limitMemory: env.isProduction,
      limitCPU: env.isProduction,
      monitoring: {
        enabled: true,
        alertOnHighUsage: true,
        killOnOOM: true,
      },
    },

    isolation: {
      enabled: env.isProduction,
      sandboxing: true,
      networkIsolation: false,
      fileSystemIsolation: true,
    },
  },

  // Task Management
  tasks: {
    scheduling: {
      strategy: 'priority', // 'priority', 'round-robin', 'least-loaded'
      batchProcessing: false,
      parallelExecution: true,
    },

    timeout: {
      enabled: true,
      default: 300000, // 5 minutes
      max: 3600000, // 1 hour
      gracePeriod: 10000, // 10 seconds
    },

    tracking: {
      enabled: true,
      persistState: env.isProduction,
      stateStorage: 'database',
      includeMetrics: true,
      includeTimeline: true,
    },

    results: {
      storage: 'database', // 'memory', 'database', 's3'
      retention: 604800000, // 7 days
      compression: true,
      encryption: env.httpsOnly,
    },

    notifications: {
      enabled: true,
      channels: ['websocket', 'webhook'],
      events: [
        'task_started',
        'task_completed',
        'task_failed',
        'task_timeout',
      ],
    },
  },

  // Pipeline Configuration
  pipelines: {
    enabled: true,
    
    definitions: {
      cicd: {
        name: 'CI/CD Pipeline',
        stages: ['build', 'test', 'deploy'],
        parallel: false,
        continueOnError: false,
      },
      dataProcessing: {
        name: 'Data Processing Pipeline',
        stages: ['extract', 'transform', 'load', 'analyze'],
        parallel: true,
        continueOnError: true,
      },
      mlTraining: {
        name: 'ML Training Pipeline',
        stages: ['prepare_data', 'train', 'evaluate', 'deploy'],
        parallel: false,
        continueOnError: false,
      },
    },

    execution: {
      maxConcurrentPipelines: 10,
      queuePipelines: true,
      retryFailedStages: true,
    },

    monitoring: {
      enabled: true,
      visualize: true,
      trackMetrics: true,
      alertOnFailure: true,
    },
  },

  // Resource Management
  resources: {
    allocation: {
      strategy: 'fair', // 'fair', 'priority-based', 'first-come-first-served'
      reservations: true,
      overcommit: false,
    },

    limits: {
      global: {
        maxMemory: 16384, // MB (16GB)
        maxCPU: 8, // cores
        maxDisk: 102400, // MB (100GB)
      },
      perEngine: {
        maxMemory: 4096, // MB
        maxCPU: 2, // cores
        maxDisk: 20480, // MB (20GB)
      },
      perTask: {
        maxMemory: 2048, // MB
        maxCPU: 1, // cores
        maxDisk: 5120, // MB (5GB)
      },
    },

    monitoring: {
      enabled: true,
      interval: 5000, // 5 seconds
      alertThresholds: {
        memory: 0.9, // 90%
        cpu: 0.9, // 90%
        disk: 0.8, // 80%
      },
    },
  },

  // Integration
  integration: {
    api: {
      enabled: true,
      endpoints: {
        submit: '/api/v1/engines/submit',
        status: '/api/v1/engines/status/:taskId',
        cancel: '/api/v1/engines/cancel/:taskId',
        results: '/api/v1/engines/results/:taskId',
        logs: '/api/v1/engines/logs/:taskId',
      },
    },

    websocket: {
      enabled: true,
      events: [
        'engine:started',
        'engine:completed',
        'engine:failed',
        'engine:progress',
        'worker:scaled',
        'queue:backlog',
      ],
    },

    hooks: {
      enabled: true,
      beforeExecution: [],
      afterExecution: [],
      onSuccess: [],
      onFailure: [],
    },
  },

  // Monitoring & Observability
  monitoring: {
    enabled: true,
    
    metrics: [
      'task_throughput',
      'task_latency',
      'success_rate',
      'error_rate',
      'queue_depth',
      'worker_utilization',
      'resource_usage',
    ],

    logging: {
      enabled: true,
      level: env.logLevel,
      structured: true,
      includeContext: true,
    },

    tracing: {
      enabled: env.isProduction,
      samplingRate: 0.1, // 10%
      includeHeaders: true,
    },

    alerts: {
      enabled: true,
      channels: ['email', 'slack', 'webhook'],
      severity: ['critical', 'high', 'medium', 'low'],
    },
  },

  // Development & Testing
  development: {
    mockEngines: env.mockApi,
    verboseLogging: env.debugMode,
    simulateDelays: false,
    simulateFailures: false,
    dryRun: false,
  },
};

// Helper functions
export const getEngineConfig = (engineId) => {
  return Object.values(enginesConfig.engines).find(e => e.id === engineId);
};

export const getEnabledEngines = () => {
  return Object.values(enginesConfig.engines).filter(e => e.enabled);
};

export const getEngineByType = (type) => {
  return Object.values(enginesConfig.engines).filter(e => e.type === type);
};

export default enginesConfig;
