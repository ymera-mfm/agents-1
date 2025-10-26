#!/usr/bin/env node

/**
 * Environment Variables Validation Script
 * Validates that all required environment variables are configured
 * for the specified environment (development, staging, production)
 */

const fs = require('fs');
const path = require('path');

// Color codes for output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

// Required environment variables by category
const requiredVariables = {
  core: [
    'NODE_ENV',
    'REACT_APP_VERSION',
  ],
  api: [
    'REACT_APP_API_URL',
    'REACT_APP_WS_URL',
    'REACT_APP_API_TIMEOUT',
  ],
  security: [
    'REACT_APP_ENABLE_CSP',
    'REACT_APP_ENABLE_HTTPS_ONLY',
    'REACT_APP_SESSION_TIMEOUT',
  ],
  features: [
    'REACT_APP_ENABLE_3D_VISUALIZATION',
    'REACT_APP_ENABLE_REAL_TIME_COLLABORATION',
    'REACT_APP_ENABLE_ADVANCED_ANALYTICS',
    'REACT_APP_ENABLE_AI_ASSISTANCE',
    'REACT_APP_ENABLE_PERFORMANCE_MONITORING',
  ],
  performance: [
    'REACT_APP_MAX_AGENTS',
    'REACT_APP_MAX_PROJECTS',
    'REACT_APP_CACHE_TIMEOUT',
    'REACT_APP_VIRTUAL_SCROLL_THRESHOLD',
  ],
  analytics: [
    'REACT_APP_ANALYTICS_ENABLED',
    'REACT_APP_ANALYTICS_SAMPLE_RATE',
    'REACT_APP_ERROR_REPORTING_ENABLED',
  ],
  build: [
    'GENERATE_SOURCEMAP',
    'INLINE_RUNTIME_CHUNK',
  ],
};

// Production-specific required variables
const productionRequired = [
  'REACT_APP_SENTRY_DSN',
  'REACT_APP_ANALYTICS_ID',
];

// Validation rules
const validationRules = {
  'NODE_ENV': (value) => ['development', 'staging', 'production'].includes(value),
  'REACT_APP_API_URL': (value) => value.startsWith('http://') || value.startsWith('https://'),
  'REACT_APP_WS_URL': (value) => value.startsWith('ws://') || value.startsWith('wss://'),
  'REACT_APP_API_TIMEOUT': (value) => !isNaN(parseInt(value)) && parseInt(value) > 0,
  'REACT_APP_SESSION_TIMEOUT': (value) => !isNaN(parseInt(value)) && parseInt(value) > 0,
  'REACT_APP_MAX_AGENTS': (value) => !isNaN(parseInt(value)) && parseInt(value) > 0,
  'REACT_APP_MAX_PROJECTS': (value) => !isNaN(parseInt(value)) && parseInt(value) > 0,
  'REACT_APP_CACHE_TIMEOUT': (value) => !isNaN(parseInt(value)) && parseInt(value) > 0,
  'REACT_APP_VIRTUAL_SCROLL_THRESHOLD': (value) => !isNaN(parseInt(value)) && parseInt(value) > 0,
  'REACT_APP_ANALYTICS_SAMPLE_RATE': (value) => {
    const rate = parseFloat(value);
    return !isNaN(rate) && rate >= 0 && rate <= 1;
  },
  'REACT_APP_ENABLE_CSP': (value) => value === 'true' || value === 'false',
  'REACT_APP_ENABLE_HTTPS_ONLY': (value) => value === 'true' || value === 'false',
  'REACT_APP_ANALYTICS_ENABLED': (value) => value === 'true' || value === 'false',
  'REACT_APP_ERROR_REPORTING_ENABLED': (value) => value === 'true' || value === 'false',
  'GENERATE_SOURCEMAP': (value) => value === 'true' || value === 'false',
  'INLINE_RUNTIME_CHUNK': (value) => value === 'true' || value === 'false',
};

// Production-specific validation rules
const productionRules = {
  'REACT_APP_ENABLE_HTTPS_ONLY': (value) => value === 'true',
  'REACT_APP_ENABLE_CSP': (value) => value === 'true',
  'REACT_APP_DEBUG_MODE': (value) => value !== 'true',
  'REACT_APP_MOCK_API': (value) => value !== 'true',
  'GENERATE_SOURCEMAP': (value) => value !== 'true',
  'REACT_APP_API_URL': (value) => value.startsWith('https://'),
  'REACT_APP_WS_URL': (value) => value.startsWith('wss://'),
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function loadEnvFile(envPath) {
  if (!fs.existsSync(envPath)) {
    return null;
  }

  const envContent = fs.readFileSync(envPath, 'utf-8');
  const envVars = {};

  envContent.split('\n').forEach((line) => {
    const trimmedLine = line.trim();
    if (trimmedLine && !trimmedLine.startsWith('#')) {
      const [key, ...valueParts] = trimmedLine.split('=');
      if (key && valueParts.length > 0) {
        envVars[key.trim()] = valueParts.join('=').trim();
      }
    }
  });

  return envVars;
}

function validateEnvironment(env, envVars) {
  log(`\n${'='.repeat(80)}`, 'cyan');
  log(`🔍 Validating ${env.toUpperCase()} Environment Variables`, 'cyan');
  log('='.repeat(80), 'cyan');

  const issues = {
    missing: [],
    invalid: [],
    warnings: [],
  };

  let totalChecked = 0;
  let totalPassed = 0;

  // Check each category
  Object.entries(requiredVariables).forEach(([category, variables]) => {
    log(`\n📦 ${category.toUpperCase()} Configuration:`, 'blue');

    variables.forEach((variable) => {
      totalChecked++;
      const value = envVars[variable];

      if (value === undefined) {
        issues.missing.push(variable);
        log(`  ❌ ${variable}: MISSING`, 'red');
      } else if (validationRules[variable] && !validationRules[variable](value)) {
        issues.invalid.push({ variable, value });
        log(`  ❌ ${variable}: INVALID VALUE ("${value}")`, 'red');
      } else {
        totalPassed++;
        log(`  ✅ ${variable}: ${value}`, 'green');
      }
    });
  });

  // Check production-specific variables
  if (env === 'production') {
    log('\n🔒 Production-Specific Configuration:', 'blue');

    productionRequired.forEach((variable) => {
      totalChecked++;
      const value = envVars[variable];

      if (value === undefined) {
        issues.missing.push(variable);
        log(`  ❌ ${variable}: MISSING (Required for production)`, 'red');
      } else if (value === 'your_sentry_dsn' || value === 'your_analytics_id') {
        issues.warnings.push(`${variable} has placeholder value`);
        log(`  ⚠️  ${variable}: PLACEHOLDER VALUE DETECTED`, 'yellow');
      } else {
        totalPassed++;
        log(`  ✅ ${variable}: Configured`, 'green');
      }
    });

    // Additional production validation
    log('\n🔐 Production Security Checks:', 'blue');
    Object.entries(productionRules).forEach(([variable, rule]) => {
      totalChecked++;
      const value = envVars[variable];

      if (value && !rule(value)) {
        issues.warnings.push(`${variable} should be configured for production security`);
        log(`  ⚠️  ${variable}: ${value} (Should be production-safe)`, 'yellow');
      } else if (value) {
        totalPassed++;
        log(`  ✅ ${variable}: Production-ready`, 'green');
      }
    });
  }

  // Summary
  log('\n' + '='.repeat(80), 'cyan');
  log('📊 Validation Summary:', 'cyan');
  log('='.repeat(80), 'cyan');

  const passRate = ((totalPassed / totalChecked) * 100).toFixed(1);
  log(`\nTotal Variables Checked: ${totalChecked}`);
  log(`Passed: ${totalPassed}`, 'green');
  log(`Failed: ${totalChecked - totalPassed}`, totalPassed === totalChecked ? 'green' : 'red');
  log(`Pass Rate: ${passRate}%`, totalPassed === totalChecked ? 'green' : 'yellow');

  if (issues.missing.length > 0) {
    log(`\n❌ Missing Variables (${issues.missing.length}):`, 'red');
    issues.missing.forEach((variable) => {
      log(`   - ${variable}`, 'red');
    });
  }

  if (issues.invalid.length > 0) {
    log(`\n❌ Invalid Values (${issues.invalid.length}):`, 'red');
    issues.invalid.forEach(({ variable, value }) => {
      log(`   - ${variable}: "${value}"`, 'red');
    });
  }

  if (issues.warnings.length > 0) {
    log(`\n⚠️  Warnings (${issues.warnings.length}):`, 'yellow');
    issues.warnings.forEach((warning) => {
      log(`   - ${warning}`, 'yellow');
    });
  }

  // Return validation result
  const isValid = issues.missing.length === 0 && issues.invalid.length === 0;

  if (isValid) {
    log('\n✅ Environment validation PASSED!', 'green');
  } else {
    log('\n❌ Environment validation FAILED!', 'red');
    log('\n💡 Please fix the issues above before deploying.', 'yellow');
  }

  log('='.repeat(80) + '\n', 'cyan');

  return isValid;
}

function main() {
  const args = process.argv.slice(2);
  const environment = args[0] || 'production';

  const validEnvironments = ['development', 'staging', 'production'];
  if (!validEnvironments.includes(environment)) {
    log(`\n❌ Invalid environment: ${environment}`, 'red');
    log(`Valid environments: ${validEnvironments.join(', ')}`, 'yellow');
    log('\nUsage: node validate-env.js [environment]', 'cyan');
    log('Example: node validate-env.js production\n', 'cyan');
    process.exit(1);
  }

  const envFileName = environment === 'development' ? '.env' : `.env.${environment}`;
  const envPath = path.join(__dirname, '..', envFileName);

  log(`\n📁 Loading environment file: ${envFileName}`, 'blue');

  const envVars = loadEnvFile(envPath);

  if (!envVars) {
    log(`\n❌ Environment file not found: ${envPath}`, 'red');
    log('💡 Create the file and configure the required variables.\n', 'yellow');
    process.exit(1);
  }

  log(`✅ Loaded ${Object.keys(envVars).length} variables from ${envFileName}`, 'green');

  const isValid = validateEnvironment(environment, envVars);

  process.exit(isValid ? 0 : 1);
}

// Run the script
if (require.main === module) {
  main();
}

module.exports = { validateEnvironment, loadEnvFile };
