import { config } from '../config/config';
import { safeGetJSON, safeSetJSON, safeGetString, safeSetString } from '../utils/storage-utils';
import { TIME_MS } from '../constants/time';

// Enhanced logging service with multiple levels and outputs
class Logger {
  constructor() {
    this.logLevel = this.getLogLevel();
    this.logBuffer = [];
    this.maxBufferSize = 1000;
    this.flushInterval = 30 * TIME_MS.SECOND; // 30 seconds

    this.initializeLogger();
  }

  // Get log level from configuration
  getLogLevel() {
    const levels = {
      error: 0,
      warn: 1,
      info: 2,
      debug: 3,
    };

    return levels[config.development.logLevel] || levels.warn;
  }

  // Initialize logger with periodic flushing
  initializeLogger() {
    // Flush logs periodically
    setInterval(() => {
      this.flushLogs();
    }, this.flushInterval);

    // Flush logs before page unload
    window.addEventListener('beforeunload', () => {
      this.flushLogs();
    });

    // Capture unhandled errors
    window.addEventListener('error', (event) => {
      this.error('Unhandled error:', {
        message: event.error?.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
      });
    });

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Unhandled promise rejection:', {
        reason: event.reason,
        promise: event.promise,
      });
    });
  }

  // Create log entry
  createLogEntry(level, message, data = {}) {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      data,
      url: window.location.href,
      userAgent: navigator.userAgent,
      sessionId: this.getSessionId(),
      userId: this.getUserId(),
      buildVersion: config.version,
    };
  }

  // Get session ID
  getSessionId() {
    let sessionId = safeGetString(sessionStorage, 'sessionId');
    if (!sessionId) {
      // Use crypto.randomUUID() for cryptographically secure session IDs
      if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        sessionId = crypto.randomUUID();
      } else {
        // Fallback for older browsers (still better than Math.random)
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        sessionId = Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('');
      }
      safeSetString(sessionStorage, 'sessionId', sessionId);
    }
    return sessionId;
  }

  // Get user ID
  getUserId() {
    const user = safeGetJSON(localStorage, 'user', {});
    return user.id || 'anonymous';
  }

  // Add log to buffer
  addToBuffer(logEntry) {
    this.logBuffer.push(logEntry);

    // Prevent buffer overflow
    if (this.logBuffer.length > this.maxBufferSize) {
      this.logBuffer = this.logBuffer.slice(-this.maxBufferSize);
    }
  }

  // Error level logging
  error(message, data = {}) {
    if (this.logLevel >= 0) {
      const logEntry = this.createLogEntry('error', message, data);

      // Always log errors to console
      console.error(`[${logEntry.timestamp}] ERROR:`, message, data);

      this.addToBuffer(logEntry);

      // Immediately flush critical errors
      if (config.isProduction) {
        this.flushLogs();
      }
    }
  }

  // Warning level logging
  warn(message, data = {}) {
    if (this.logLevel >= 1) {
      const logEntry = this.createLogEntry('warn', message, data);

      console.warn(`[${logEntry.timestamp}] WARN:`, message, data);
      this.addToBuffer(logEntry);
    }
  }

  // Info level logging
  info(message, data = {}) {
    if (this.logLevel >= 2) {
      const logEntry = this.createLogEntry('info', message, data);

      /* eslint-disable-next-line no-console */
      console.info(`[${logEntry.timestamp}] INFO:`, message, data);
      this.addToBuffer(logEntry);
    }
  }

  // Debug level logging
  debug(message, data = {}) {
    if (this.logLevel >= 3) {
      const logEntry = this.createLogEntry('debug', message, data);

      /* eslint-disable-next-line no-console */
      console.debug(`[${logEntry.timestamp}] DEBUG:`, message, data);
      this.addToBuffer(logEntry);
    }
  }

  // Performance logging
  performance(operation, duration, data = {}) {
    const logEntry = this.createLogEntry('performance', `${operation} completed`, {
      operation,
      duration,
      ...data,
    });

    if (config.development.showPerformanceMetrics && process.env.NODE_ENV === 'development') {
      /* eslint-disable-next-line no-console */
      console.log(`[${logEntry.timestamp}] PERF: ${operation} - ${duration}ms`, data);
    }

    this.addToBuffer(logEntry);
  }

  // User action logging
  userAction(action, data = {}) {
    const logEntry = this.createLogEntry('user_action', action, data);

    if (this.logLevel >= 2 && process.env.NODE_ENV === 'development') {
      /* eslint-disable-next-line no-console */
      console.log(`[${logEntry.timestamp}] USER: ${action}`, data);
    }

    this.addToBuffer(logEntry);
  }

  // API call logging
  apiCall(method, url, status, duration, data = {}) {
    const logEntry = this.createLogEntry('api_call', `${method} ${url}`, {
      method,
      url,
      status,
      duration,
      ...data,
    });

    if (this.logLevel >= 2 && process.env.NODE_ENV === 'development') {
      /* eslint-disable-next-line no-console */
      console.log(
        `[${logEntry.timestamp}] API: ${method} ${url} - ${status} (${duration}ms)`,
        data
      );
    }

    this.addToBuffer(logEntry);
  }

  // Security event logging
  security(event, data = {}) {
    const logEntry = this.createLogEntry('security', event, data);

    console.warn(`[${logEntry.timestamp}] SECURITY: ${event}`, data);
    this.addToBuffer(logEntry);

    // Immediately flush security events
    this.flushLogs();
  }

  // Flush logs to remote endpoint
  async flushLogs() {
    if (this.logBuffer.length === 0 || !config.analytics.enabled) {
      return;
    }

    const logsToFlush = [...this.logBuffer];
    this.logBuffer = [];

    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logs: logsToFlush,
          metadata: {
            flushTime: new Date().toISOString(),
            logCount: logsToFlush.length,
          },
        }),
      });
    } catch (error) {
      // If flushing fails, add logs back to buffer
      this.logBuffer = [...logsToFlush, ...this.logBuffer];

      // Store logs locally as fallback
      this.storeLogsLocally(logsToFlush);

      console.warn('Failed to flush logs to server:', error);
    }
  }

  // Store logs locally as fallback
  storeLogsLocally(logs) {
    const storedLogs = safeGetJSON(localStorage, 'pendingLogs', []);
    const allLogs = [...storedLogs, ...logs];

    // Keep only recent logs to prevent storage overflow
    const recentLogs = allLogs.slice(-500);
    safeSetJSON(localStorage, 'pendingLogs', recentLogs);
  }

  // Get stored logs
  getStoredLogs() {
    return safeGetJSON(localStorage, 'pendingLogs', []);
  }

  // Clear stored logs
  clearStoredLogs() {
    localStorage.removeItem('pendingLogs');
  }

  // Get current log buffer
  getLogBuffer() {
    return [...this.logBuffer];
  }

  // Set log level dynamically
  setLogLevel(level) {
    const levels = {
      error: 0,
      warn: 1,
      info: 2,
      debug: 3,
    };

    if (levels.hasOwnProperty(level)) {
      this.logLevel = levels[level];
      this.info(`Log level changed to: ${level}`);
    }
  }

  // Create performance timer
  createTimer(operation) {
    const startTime = performance.now();

    return {
      end: (data = {}) => {
        const duration = performance.now() - startTime;
        this.performance(operation, Math.round(duration), data);
        return duration;
      },
    };
  }

  // Log component lifecycle events
  componentLifecycle(component, event, data = {}) {
    if (this.logLevel >= 3) {
      this.debug(`Component ${component} - ${event}`, data);
    }
  }

  // Log state changes
  stateChange(component, oldState, newState) {
    if (this.logLevel >= 3) {
      this.debug(`State change in ${component}`, {
        oldState,
        newState,
        changes: this.getStateChanges(oldState, newState),
      });
    }
  }

  // Get state changes
  getStateChanges(oldState, newState) {
    const changes = {};

    for (const key in newState) {
      if (oldState[key] !== newState[key]) {
        changes[key] = {
          from: oldState[key],
          to: newState[key],
        };
      }
    }

    return changes;
  }

  // Export logs for debugging
  exportLogs() {
    const allLogs = [...this.getStoredLogs(), ...this.logBuffer];
    const blob = new Blob([JSON.stringify(allLogs, null, 2)], {
      type: 'application/json',
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agentflow-logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// Create singleton instance
export const logger = new Logger();

// Convenience methods for direct import
export const log = {
  error: (message, data) => logger.error(message, data),
  warn: (message, data) => logger.warn(message, data),
  info: (message, data) => logger.info(message, data),
  debug: (message, data) => logger.debug(message, data),
  performance: (operation, duration, data) => logger.performance(operation, duration, data),
  userAction: (action, data) => logger.userAction(action, data),
  apiCall: (method, url, status, duration, data) =>
    logger.apiCall(method, url, status, duration, data),
  security: (event, data) => logger.security(event, data),
  timer: (operation) => logger.createTimer(operation),
};

export default logger;
