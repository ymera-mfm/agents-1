/**
 * Production Logger Wrapper
 * Removes console statements in production builds
 */

const isDevelopment = process.env.NODE_ENV === 'development';

export const logger = {
  log: (...args) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.log(...args);
    }
  },

  warn: (...args) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.warn(...args);
    }
  },

  error: (...args) => {
    // Always log errors, even in production
    // eslint-disable-next-line no-console
    console.error(...args);
  },

  info: (...args) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.info(...args);
    }
  },

  debug: (...args) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.debug(...args);
    }
  },

  table: (...args) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.table(...args);
    }
  },

  group: (...args) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.group(...args);
    }
  },

  groupEnd: () => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.groupEnd();
    }
  },

  time: (label) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.time(label);
    }
  },

  timeEnd: (label) => {
    if (isDevelopment) {
      // eslint-disable-next-line no-console
      console.timeEnd(label);
    }
  },
};

export default logger;
