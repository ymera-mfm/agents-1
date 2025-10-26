// Central Configuration Index
// This file exports all configuration modules for easy access throughout the application

/* eslint-disable no-unused-vars */
import mainConfig, { CONFIG, validateConfig } from './config';
import agentsConfigModule, { getAgentTypeConfig, getAvailableAgentTypes } from './agents.config';
import routesConfigModule, { getRoute, getApiEndpoint, getNavigationRoutes } from './routes.config';
import learningConfigModule, { getModelConfig, getEnabledModels, isModelReady } from './learning.config';
import enginesConfigModule, { getEngineConfig, getEnabledEngines, getEngineByType } from './engines.config';
import chatConfigModule, { getConversationType, canUserPerformAction, isMessageAllowed } from './chat.config';
import fileConfigModule, { isFileTypeAllowed, getMaxFileSizeForType, canUploadFile } from './file.config';
import performanceConfigModule from './performance.config';
import alertsConfigModule from './alerts.config';
import constantsModule from './constants';
/* eslint-enable no-unused-vars */

// Export named imports
export { default as config, CONFIG, validateConfig } from './config';
export { default as agentsConfig, getAgentTypeConfig, getAvailableAgentTypes } from './agents.config';
export { default as routesConfig, getRoute, getApiEndpoint, getNavigationRoutes } from './routes.config';
export { default as learningConfig, getModelConfig, getEnabledModels, isModelReady } from './learning.config';
export { default as enginesConfig, getEngineConfig, getEnabledEngines, getEngineByType } from './engines.config';
export { default as chatConfig, getConversationType, canUserPerformAction, isMessageAllowed } from './chat.config';
export { default as fileConfig, isFileTypeAllowed, getMaxFileSizeForType, canUploadFile } from './file.config';
export { default as performanceConfig } from './performance.config';
export { default as alertsConfig } from './alerts.config';
export { default as constants } from './constants';
export * from './helpers';

// Re-export commonly used values for convenience
export const {
  isDevelopment,
  isProduction,
  version,
  api,
  features,
  performance,
  analytics,
  security,
  development,
} = mainConfig;

// System-wide configuration validator
export const validateSystemConfig = () => {
  const validations = {
    config: validateConfig(),
    // Add more validators as needed
  };

  const allValid = Object.values(validations).every(v => v === true);
  
  if (!allValid) {
    console.error('System configuration validation failed:', validations);
  }

  return allValid;
};

// Get all configuration modules
export const getAllConfigs = () => ({
  config: mainConfig,
  agentsConfig: agentsConfigModule,
  routesConfig: routesConfigModule,
  learningConfig: learningConfigModule,
  enginesConfig: enginesConfigModule,
  chatConfig: chatConfigModule,
  fileConfig: fileConfigModule,
  performanceConfig: performanceConfigModule,
  alertsConfig: alertsConfigModule,
  constants: constantsModule,
});

// Configuration summary for debugging
export const getConfigSummary = () => ({
  environment: mainConfig.isDevelopment ? 'development' : 'production',
  version: mainConfig.version,
  features: mainConfig.features,
  apiBaseUrl: mainConfig.api.baseUrl,
  wsUrl: mainConfig.api.wsUrl,
  agentTypes: Object.keys(agentsConfigModule.types).length,
  mlModels: Object.keys(learningConfigModule.models).length,
  engines: Object.keys(enginesConfigModule.engines).length,
  conversationTypes: Object.keys(chatConfigModule.conversations.types).length,
});

// Default export
const allConfigs = {
  config: mainConfig,
  agentsConfig: agentsConfigModule,
  routesConfig: routesConfigModule,
  learningConfig: learningConfigModule,
  enginesConfig: enginesConfigModule,
  chatConfig: chatConfigModule,
  fileConfig: fileConfigModule,
  performanceConfig: performanceConfigModule,
  alertsConfig: alertsConfigModule,
  constants: constantsModule,
};

export default allConfigs;
