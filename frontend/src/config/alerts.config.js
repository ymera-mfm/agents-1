/**
 * Alert Configuration
 * Defines thresholds and actions for monitoring alerts
 */

export const alerts = {
  criticalErrors: {
    threshold: 10, // errors per minute
    action: 'page_team_immediately',
    severity: 'critical',
    description: 'Critical error rate exceeded threshold',
  },
  highErrorRate: {
    threshold: 5, // percent
    action: 'send_slack_notification',
    severity: 'high',
    description: 'Error rate is above acceptable threshold',
  },
  slowResponseTime: {
    threshold: 5000, // milliseconds
    action: 'send_email_alert',
    severity: 'medium',
    description: 'API response time exceeds acceptable limit',
  },
  downtime: {
    threshold: 60, // seconds
    action: 'page_team_immediately',
    severity: 'critical',
    description: 'Application downtime detected',
  },
  highMemoryUsage: {
    threshold: 90, // percent
    action: 'send_slack_notification',
    severity: 'high',
    description: 'Memory usage is critically high',
  },
  slowPageLoad: {
    threshold: 3000, // milliseconds
    action: 'send_email_alert',
    severity: 'medium',
    description: 'Page load time exceeds target',
  },
};

export const performanceTargets = {
  // Core Web Vitals
  firstContentfulPaint: 1500, // ms
  largestContentfulPaint: 2500, // ms
  timeToInteractive: 3500, // ms
  cumulativeLayoutShift: 0.1, // score
  firstInputDelay: 100, // ms

  // Application metrics
  apiResponseTime: 2000, // ms
  pageLoadTime: 3000, // ms
  uptime: 99.9, // percent
  errorRate: 1, // percent
};

export const monitoringEndpoints = {
  healthCheck: '/health',
  metrics: '/api/metrics',
  vitals: '/api/analytics/vitals',
  errors: '/api/errors',
};

const alertsConfig = {
  alerts,
  performanceTargets,
  monitoringEndpoints,
};

export default alertsConfig;
