// Learning System Configuration
// Comprehensive configuration for machine learning, training, and inference

import env from './env';

export const learningConfig = {
  // ML Models Configuration
  models: {
    agentPerformance: {
      id: 'agent-performance',
      name: 'Agent Performance Predictor',
      type: 'regression',
      framework: 'tensorflow',
      version: '1.0.0',
      endpoint: '/api/v1/learning/models/agent-performance',
      features: [
        'execution_time',
        'success_rate',
        'resource_usage',
        'task_complexity',
        'historical_performance',
      ],
      target: 'predicted_performance',
      accuracy: 0.87,
      lastTrained: null,
      enabled: env.enableAIAssistance,
    },
    taskClassification: {
      id: 'task-classification',
      name: 'Task Classifier',
      type: 'classification',
      framework: 'tensorflow',
      version: '1.0.0',
      endpoint: '/api/v1/learning/models/task-classification',
      features: [
        'task_description',
        'task_type',
        'priority',
        'complexity',
      ],
      classes: ['code', 'design', 'test', 'deploy', 'analyze'],
      accuracy: 0.92,
      lastTrained: null,
      enabled: env.enableAIAssistance,
    },
    anomalyDetection: {
      id: 'anomaly-detection',
      name: 'System Anomaly Detector',
      type: 'anomaly_detection',
      framework: 'scikit-learn',
      version: '1.0.0',
      endpoint: '/api/v1/learning/models/anomaly-detection',
      features: [
        'cpu_usage',
        'memory_usage',
        'error_rate',
        'response_time',
        'request_rate',
      ],
      threshold: 0.95,
      lastTrained: null,
      enabled: env.enablePerformanceMonitoring,
    },
    resourceOptimization: {
      id: 'resource-optimization',
      name: 'Resource Optimizer',
      type: 'optimization',
      framework: 'tensorflow',
      version: '1.0.0',
      endpoint: '/api/v1/learning/models/resource-optimization',
      features: [
        'current_load',
        'available_resources',
        'task_queue',
        'priority_distribution',
      ],
      objective: 'minimize_cost_maximize_performance',
      lastTrained: null,
      enabled: true,
    },
  },

  // Training Configuration
  training: {
    enabled: false, // Training handled by backend
    automatic: {
      enabled: env.isProduction,
      schedule: 'weekly', // 'daily', 'weekly', 'monthly'
      minDataPoints: 1000,
      triggerThreshold: 0.1, // 10% accuracy drop triggers retraining
    },
    manual: {
      enabled: true,
      requireApproval: env.isProduction,
      notifyOnCompletion: true,
    },
    validation: {
      splitRatio: 0.2, // 80% train, 20% validation
      crossValidation: true,
      folds: 5,
      metrics: ['accuracy', 'precision', 'recall', 'f1_score'],
    },
    hyperparameters: {
      learningRate: 0.001,
      batchSize: 32,
      epochs: 100,
      earlyStoppingPatience: 10,
      optimizer: 'adam',
    },
    resources: {
      maxMemory: 4096, // MB
      maxCPU: 2, // cores
      useGPU: false,
      timeout: 3600000, // 1 hour
    },
  },

  // Inference Configuration
  inference: {
    enabled: env.enableAIAssistance,
    mode: 'realtime', // 'realtime', 'batch'
    caching: {
      enabled: true,
      ttl: 300000, // 5 minutes
      maxSize: 1000,
    },
    batching: {
      enabled: false,
      maxBatchSize: 32,
      maxWaitTime: 1000, // 1 second
    },
    fallback: {
      enabled: true,
      strategy: 'use_default', // 'use_default', 'skip', 'error'
      defaultPredictions: {
        agentPerformance: 0.8,
        taskClassification: 'code',
        anomalyDetection: false,
      },
    },
    monitoring: {
      logPredictions: env.isDevelopment,
      trackLatency: true,
      trackAccuracy: true,
    },
  },

  // Data Collection
  dataCollection: {
    enabled: env.analyticsEnabled,
    sources: [
      'agent_executions',
      'project_builds',
      'user_interactions',
      'system_metrics',
    ],
    storage: {
      type: 'database', // 'database', 's3', 'local'
      retention: 2592000000, // 30 days
      compression: true,
    },
    preprocessing: {
      enabled: true,
      normalize: true,
      removeOutliers: true,
      handleMissing: 'mean', // 'mean', 'median', 'drop'
    },
    privacy: {
      anonymize: env.isProduction,
      excludePersonalData: true,
      encryption: env.httpsOnly,
    },
  },

  // Feature Engineering
  featureEngineering: {
    enabled: true,
    automatic: {
      enabled: true,
      methods: [
        'polynomial_features',
        'interaction_features',
        'temporal_features',
      ],
    },
    custom: {
      enabled: true,
      features: [
        {
          name: 'agent_efficiency',
          formula: 'success_rate / execution_time',
        },
        {
          name: 'resource_utilization',
          formula: '(cpu_usage + memory_usage) / 2',
        },
        {
          name: 'task_urgency',
          formula: 'priority * (1 / time_remaining)',
        },
      ],
    },
  },

  // Model Evaluation
  evaluation: {
    enabled: true,
    metrics: {
      classification: [
        'accuracy',
        'precision',
        'recall',
        'f1_score',
        'confusion_matrix',
        'roc_auc',
      ],
      regression: [
        'mse',
        'rmse',
        'mae',
        'r2_score',
      ],
      anomalyDetection: [
        'precision',
        'recall',
        'f1_score',
        'false_positive_rate',
      ],
    },
    thresholds: {
      minAccuracy: 0.8,
      minPrecision: 0.85,
      minRecall: 0.85,
      maxFalsePositiveRate: 0.05,
    },
    reporting: {
      generateReport: true,
      includeVisualizations: true,
      notifyStakeholders: env.isProduction,
    },
  },

  // Model Management
  management: {
    versioning: {
      enabled: true,
      strategy: 'semantic', // 'semantic', 'timestamp'
      keepVersions: 5,
    },
    deployment: {
      strategy: 'blue-green', // 'blue-green', 'canary', 'rolling'
      rollback: {
        enabled: true,
        automatic: true,
        conditions: ['accuracy_drop', 'error_spike'],
      },
      approval: {
        required: env.isProduction,
        approvers: ['admin', 'ml_engineer'],
      },
    },
    monitoring: {
      enabled: true,
      metrics: [
        'prediction_latency',
        'throughput',
        'accuracy_drift',
        'data_drift',
      ],
      alerts: {
        accuracyDrop: {
          threshold: 0.1, // 10% drop
          action: 'notify_and_rollback',
        },
        highLatency: {
          threshold: 1000, // 1 second
          action: 'notify',
        },
        dataDrift: {
          threshold: 0.2, // 20% drift
          action: 'trigger_retraining',
        },
      },
    },
  },

  // AutoML Configuration
  automl: {
    enabled: false, // Disabled for now
    searchSpace: {
      algorithms: ['random_forest', 'gradient_boosting', 'neural_network'],
      hyperparameters: {
        learningRate: [0.001, 0.01, 0.1],
        maxDepth: [3, 5, 7, 10],
        numEstimators: [50, 100, 200],
      },
    },
    search: {
      method: 'random_search', // 'grid_search', 'random_search', 'bayesian'
      maxTrials: 50,
      timeout: 7200000, // 2 hours
    },
    evaluation: {
      metric: 'accuracy',
      crossValidation: true,
      folds: 5,
    },
  },

  // Explainability & Interpretability
  explainability: {
    enabled: env.isDevelopment,
    methods: [
      'feature_importance',
      'shap_values',
      'lime',
    ],
    visualization: {
      enabled: true,
      interactive: env.isDevelopment,
    },
    reporting: {
      generateExplanations: env.isDevelopment,
      includeInUI: env.isDevelopment,
    },
  },

  // Integration with other systems
  integration: {
    agents: {
      useModelPredictions: true,
      confidenceThreshold: 0.7,
      fallbackBehavior: 'manual_assignment',
    },
    monitoring: {
      detectAnomalies: true,
      alertOnAnomalies: true,
      autoRemediate: false,
    },
    analytics: {
      enhanceDashboards: true,
      providePredictions: true,
      showTrends: true,
    },
  },

  // API Configuration
  api: {
    endpoints: {
      predict: '/api/v1/learning/predict',
      train: '/api/v1/learning/train',
      evaluate: '/api/v1/learning/evaluate',
      models: '/api/v1/learning/models',
      datasets: '/api/v1/learning/datasets',
    },
    authentication: {
      required: true,
      method: 'jwt',
    },
    rateLimit: {
      enabled: env.isProduction,
      maxRequests: 100,
      windowMs: 60000, // 1 minute
    },
  },

  // Development & Debugging
  development: {
    mockPredictions: env.mockApi,
    verboseLogging: env.debugMode,
    showModelDetails: env.isDevelopment,
    enablePlayground: env.isDevelopment,
  },
};

// Helper functions
export const getModelConfig = (modelId) => {
  return Object.values(learningConfig.models).find(m => m.id === modelId);
};

export const getEnabledModels = () => {
  return Object.values(learningConfig.models).filter(m => m.enabled);
};

export const isModelReady = (modelId) => {
  const model = getModelConfig(modelId);
  return model && model.enabled && model.lastTrained !== null;
};

export default learningConfig;
