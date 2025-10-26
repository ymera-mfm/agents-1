// Configuration Validation Test
// This file tests that all configuration modules are properly defined and accessible

import {
  config,
  agentsConfig,
  routesConfig,
  learningConfig,
  enginesConfig,
  chatConfig,
  fileConfig,
  validateSystemConfig,
  getConfigSummary,
} from '../../config';

describe('System Configuration', () => {
  describe('Main Configuration', () => {
    it('should export main config', () => {
      expect(config).toBeDefined();
      expect(config.isDevelopment).toBeDefined();
      expect(config.isProduction).toBeDefined();
      expect(config.api).toBeDefined();
      expect(config.features).toBeDefined();
    });

    it('should have valid API configuration', () => {
      expect(config.api.baseUrl).toBeDefined();
      expect(config.api.wsUrl).toBeDefined();
      expect(config.api.timeout).toBeGreaterThan(0);
    });
  });

  describe('Agents Configuration', () => {
    it('should export agents config', () => {
      expect(agentsConfig).toBeDefined();
      expect(agentsConfig.types).toBeDefined();
    });

    it('should have defined agent types', () => {
      expect(Object.keys(agentsConfig.types).length).toBeGreaterThan(0);
      expect(agentsConfig.types.coder).toBeDefined();
      expect(agentsConfig.types.analyst).toBeDefined();
      expect(agentsConfig.types.security).toBeDefined();
    });

    it('should have lifecycle configuration', () => {
      expect(agentsConfig.lifecycle).toBeDefined();
      expect(agentsConfig.lifecycle.initialization).toBeDefined();
      expect(agentsConfig.lifecycle.execution).toBeDefined();
      expect(agentsConfig.lifecycle.termination).toBeDefined();
    });
  });

  describe('Routes Configuration', () => {
    it('should export routes config', () => {
      expect(routesConfig).toBeDefined();
      expect(routesConfig.frontend).toBeDefined();
      expect(routesConfig.api).toBeDefined();
    });

    it('should have frontend routes', () => {
      expect(routesConfig.frontend.public).toBeInstanceOf(Array);
      expect(routesConfig.frontend.protected).toBeInstanceOf(Array);
      expect(routesConfig.frontend.protected.length).toBeGreaterThan(0);
    });

    it('should have API endpoints', () => {
      expect(routesConfig.api.auth).toBeDefined();
      expect(routesConfig.api.agents).toBeDefined();
      expect(routesConfig.api.projects).toBeDefined();
      expect(routesConfig.api.chat).toBeDefined();
      expect(routesConfig.api.files).toBeDefined();
    });
  });

  describe('Learning Configuration', () => {
    it('should export learning config', () => {
      expect(learningConfig).toBeDefined();
      expect(learningConfig.models).toBeDefined();
    });

    it('should have ML models defined', () => {
      expect(Object.keys(learningConfig.models).length).toBeGreaterThan(0);
      expect(learningConfig.models.agentPerformance).toBeDefined();
      expect(learningConfig.models.taskClassification).toBeDefined();
    });

    it('should have training configuration', () => {
      expect(learningConfig.training).toBeDefined();
      expect(learningConfig.inference).toBeDefined();
    });
  });

  describe('Engines Configuration', () => {
    it('should export engines config', () => {
      expect(enginesConfig).toBeDefined();
      expect(enginesConfig.engines).toBeDefined();
    });

    it('should have processing engines defined', () => {
      expect(Object.keys(enginesConfig.engines).length).toBeGreaterThan(0);
      expect(enginesConfig.engines.code).toBeDefined();
      expect(enginesConfig.engines.build).toBeDefined();
      expect(enginesConfig.engines.test).toBeDefined();
    });

    it('should have queue configuration', () => {
      expect(enginesConfig.queue).toBeDefined();
      expect(enginesConfig.workers).toBeDefined();
    });
  });

  describe('Chat Configuration', () => {
    it('should export chat config', () => {
      expect(chatConfig).toBeDefined();
      expect(chatConfig.system).toBeDefined();
    });

    it('should have conversation types defined', () => {
      expect(chatConfig.conversations.types).toBeDefined();
      expect(chatConfig.conversations.types.direct).toBeDefined();
      expect(chatConfig.conversations.types.group).toBeDefined();
      expect(chatConfig.conversations.types.agent).toBeDefined();
    });

    it('should have message configuration', () => {
      expect(chatConfig.messages).toBeDefined();
      expect(chatConfig.messages.maxLength).toBeGreaterThan(0);
    });
  });

  describe('File Configuration', () => {
    it('should export file config', () => {
      expect(fileConfig).toBeDefined();
      expect(fileConfig.storage).toBeDefined();
    });

    it('should have upload configuration', () => {
      expect(fileConfig.upload).toBeDefined();
      expect(fileConfig.upload.limits).toBeDefined();
      expect(fileConfig.upload.allowedTypes).toBeDefined();
    });

    it('should have storage providers defined', () => {
      expect(fileConfig.storage.local).toBeDefined();
      expect(fileConfig.storage.s3).toBeDefined();
    });
  });

  describe('System Validation', () => {
    it('should have validation function', () => {
      expect(validateSystemConfig).toBeDefined();
      expect(typeof validateSystemConfig).toBe('function');
    });

    it('should validate configurations', () => {
      const isValid = validateSystemConfig();
      expect(typeof isValid).toBe('boolean');
    });

    it('should provide config summary', () => {
      const summary = getConfigSummary();
      expect(summary).toBeDefined();
      expect(summary.environment).toBeDefined();
      expect(summary.version).toBeDefined();
      expect(summary.agentTypes).toBeGreaterThan(0);
      expect(summary.engines).toBeGreaterThan(0);
    });
  });
});
