/**
 * Time-related constants
 * Centralizes time conversions and durations
 * @module constants/time
 */

/**
 * Time conversion constants in milliseconds
 */
export const TIME_MS = {
  /** One second in milliseconds */
  SECOND: 1000,

  /** One minute in milliseconds */
  MINUTE: 60 * 1000,

  /** One hour in milliseconds */
  HOUR: 60 * 60 * 1000,

  /** One day in milliseconds */
  DAY: 24 * 60 * 60 * 1000,

  /** One week in milliseconds */
  WEEK: 7 * 24 * 60 * 60 * 1000,

  /** One month (30 days) in milliseconds */
  MONTH: 30 * 24 * 60 * 60 * 1000,

  /** One year (365 days) in milliseconds */
  YEAR: 365 * 24 * 60 * 60 * 1000,
};

/**
 * Time conversion constants in seconds
 */
export const TIME_SECONDS = {
  /** One minute in seconds */
  MINUTE: 60,

  /** One hour in seconds */
  HOUR: 60 * 60,

  /** One day in seconds */
  DAY: 24 * 60 * 60,

  /** One week in seconds */
  WEEK: 7 * 24 * 60 * 60,

  /** One month (30 days) in seconds */
  MONTH: 30 * 24 * 60 * 60,

  /** One year (365 days) in seconds */
  YEAR: 365 * 24 * 60 * 60,
};

/**
 * Timeout and polling intervals
 */
export const INTERVALS = {
  /** Fast polling interval (ms) */
  FAST_POLL: 1000,

  /** Normal polling interval (ms) */
  NORMAL_POLL: 5000,

  /** Slow polling interval (ms) */
  SLOW_POLL: 30000,

  /** Health check interval (ms) */
  HEALTH_CHECK: 60000,

  /** Session refresh interval (ms) */
  SESSION_REFRESH: 5 * 60 * 1000,

  /** Token refresh interval (ms) */
  TOKEN_REFRESH: 14 * 60 * 1000, // 14 minutes (before 15 min expiry)
};

/**
 * Timeout durations
 */
export const TIMEOUTS = {
  /** Short timeout for quick operations (ms) */
  SHORT: 5000,

  /** Medium timeout for normal operations (ms) */
  MEDIUM: 15000,

  /** Long timeout for slow operations (ms) */
  LONG: 30000,

  /** Extra long timeout for very slow operations (ms) */
  EXTRA_LONG: 60000,

  /** API request timeout (ms) */
  API_REQUEST: 30000,

  /** File upload timeout (ms) */
  FILE_UPLOAD: 120000,
};

/**
 * Cache TTL (Time To Live) durations in milliseconds
 */
export const CACHE_TTL = {
  /** Very short cache duration (1 minute) */
  VERY_SHORT: 1 * 60 * 1000,

  /** Short cache duration (5 minutes) */
  SHORT: 5 * 60 * 1000,

  /** Medium cache duration (15 minutes) */
  MEDIUM: 15 * 60 * 1000,

  /** Long cache duration (1 hour) */
  LONG: 60 * 60 * 1000,

  /** Very long cache duration (24 hours) */
  VERY_LONG: 24 * 60 * 60 * 1000,

  /** User data cache (15 minutes) */
  USER_DATA: 15 * 60 * 1000,

  /** Static content cache (1 hour) */
  STATIC_CONTENT: 60 * 60 * 1000,

  /** API response cache (5 minutes) */
  API_RESPONSE: 5 * 60 * 1000,
};

/**
 * Session and token expiry times
 */
export const EXPIRY = {
  /** Short-lived token (15 minutes) */
  SHORT_TOKEN: 15 * 60 * 1000,

  /** Standard token (1 hour) */
  STANDARD_TOKEN: 60 * 60 * 1000,

  /** Long-lived token (24 hours) */
  LONG_TOKEN: 24 * 60 * 60 * 1000,

  /** Remember me token (30 days) */
  REMEMBER_ME: 30 * 24 * 60 * 60 * 1000,

  /** Session expiry (2 hours) */
  SESSION: 2 * 60 * 60 * 1000,

  /** OTP code expiry (5 minutes) */
  OTP: 5 * 60 * 1000,
};

/**
 * Retry and backoff delays
 */
export const RETRY = {
  /** Initial retry delay (ms) */
  INITIAL_DELAY: 1000,

  /** Maximum retry delay (ms) */
  MAX_DELAY: 30000,

  /** Retry backoff multiplier */
  BACKOFF_MULTIPLIER: 2,

  /** Maximum number of retries */
  MAX_ATTEMPTS: 3,
};

/**
 * Date format patterns
 */
export const DATE_FORMATS = {
  /** Short date (MM/DD/YYYY) */
  SHORT: 'MM/dd/yyyy',

  /** Medium date (MMM DD, YYYY) */
  MEDIUM: 'MMM dd, yyyy',

  /** Long date (MMMM DD, YYYY) */
  LONG: 'MMMM dd, yyyy',

  /** Full date with time (MMMM DD, YYYY HH:MM:SS) */
  FULL: 'MMMM dd, yyyy HH:mm:ss',

  /** ISO format (YYYY-MM-DD) */
  ISO: 'yyyy-MM-dd',

  /** Time only (HH:MM:SS) */
  TIME: 'HH:mm:ss',

  /** Short time (HH:MM) */
  TIME_SHORT: 'HH:mm',

  /** DateTime (YYYY-MM-DD HH:MM) */
  DATETIME: 'yyyy-MM-dd HH:mm',
};

/**
 * Relative time thresholds (in milliseconds)
 */
export const RELATIVE_TIME_THRESHOLDS = {
  /** Show "just now" for times within this threshold */
  JUST_NOW: 60 * 1000, // 1 minute

  /** Show minutes for times within this threshold */
  MINUTES: 60 * 60 * 1000, // 1 hour

  /** Show hours for times within this threshold */
  HOURS: 24 * 60 * 60 * 1000, // 1 day

  /** Show days for times within this threshold */
  DAYS: 7 * 24 * 60 * 60 * 1000, // 1 week

  /** Show weeks for times within this threshold */
  WEEKS: 30 * 24 * 60 * 60 * 1000, // ~1 month
};

/**
 * Helper functions for time calculations
 */
export const TimeHelpers = {
  /**
   * Converts milliseconds to seconds
   * @param {number} ms - Milliseconds
   * @returns {number} Seconds
   */
  msToSeconds: (ms) => Math.floor(ms / 1000),

  /**
   * Converts seconds to milliseconds
   * @param {number} seconds - Seconds
   * @returns {number} Milliseconds
   */
  secondsToMs: (seconds) => seconds * 1000,

  /**
   * Checks if a timestamp is expired
   * @param {number} timestamp - Timestamp in milliseconds
   * @param {number} ttl - Time to live in milliseconds
   * @returns {boolean} True if expired
   */
  isExpired: (timestamp, ttl) => Date.now() > timestamp + ttl,

  /**
   * Gets expiry timestamp
   * @param {number} ttl - Time to live in milliseconds
   * @returns {number} Expiry timestamp
   */
  getExpiryTime: (ttl) => Date.now() + ttl,

  /**
   * Gets time remaining until expiry
   * @param {number} expiryTime - Expiry timestamp in milliseconds
   * @returns {number} Milliseconds remaining (0 if expired)
   */
  getTimeRemaining: (expiryTime) => Math.max(0, expiryTime - Date.now()),
};

const TIME_CONSTANTS = {
  TIME_MS,
  TIME_SECONDS,
  INTERVALS,
  TIMEOUTS,
  CACHE_TTL,
  EXPIRY,
  RETRY,
  DATE_FORMATS,
  RELATIVE_TIME_THRESHOLDS,
  TimeHelpers,
};

export default TIME_CONSTANTS;
