/**
 * Memoization Utilities
 * Optimizes expensive computations through caching
 */

/**
 * Simple memoization function for pure functions
 */
export function memoize(fn, options = {}) {
  const {
    maxSize = 100,
    ttl = 5 * 60 * 1000, // 5 minutes default
    keyResolver = (...args) => JSON.stringify(args),
  } = options;

  const cache = new Map();
  const timestamps = new Map();

  return function memoized(...args) {
    const key = keyResolver(...args);
    const now = Date.now();

    // Check if cached and not expired
    if (cache.has(key)) {
      const timestamp = timestamps.get(key);
      if (now - timestamp < ttl) {
        return cache.get(key);
      }
      // Expired, remove from cache
      cache.delete(key);
      timestamps.delete(key);
    }

    // Compute result
    const result = fn.apply(this, args);

    // Add to cache
    cache.set(key, result);
    timestamps.set(key, now);

    // Enforce max size (LRU)
    if (cache.size > maxSize) {
      // Remove oldest entry
      const oldestKey = cache.keys().next().value;
      cache.delete(oldestKey);
      timestamps.delete(oldestKey);
    }

    return result;
  };
}

/**
 * Memoization for async functions
 */
export function memoizeAsync(fn, options = {}) {
  const {
    maxSize = 100,
    ttl = 5 * 60 * 1000,
    keyResolver = (...args) => JSON.stringify(args),
  } = options;

  const cache = new Map();
  const timestamps = new Map();
  const pending = new Map();

  return async function memoizedAsync(...args) {
    const key = keyResolver(...args);
    const now = Date.now();

    // Check if cached and not expired
    if (cache.has(key)) {
      const timestamp = timestamps.get(key);
      if (now - timestamp < ttl) {
        return cache.get(key);
      }
      // Expired, remove from cache
      cache.delete(key);
      timestamps.delete(key);
    }

    // Check if request is already pending
    if (pending.has(key)) {
      return pending.get(key);
    }

    // Create promise and cache it
    const promise = (async () => {
      try {
        const result = await fn.apply(this, args);

        // Cache result
        cache.set(key, result);
        timestamps.set(key, now);

        // Enforce max size (LRU)
        if (cache.size > maxSize) {
          const oldestKey = cache.keys().next().value;
          cache.delete(oldestKey);
          timestamps.delete(oldestKey);
        }

        return result;
      } finally {
        // Remove from pending
        pending.delete(key);
      }
    })();

    pending.set(key, promise);
    return promise;
  };
}

/**
 * Memoization with WeakMap for object keys
 */
export function memoizeWeak(fn) {
  const cache = new WeakMap();

  return function memoizedWeak(obj, ...args) {
    if (!cache.has(obj)) {
      cache.set(obj, fn.call(this, obj, ...args));
    }
    return cache.get(obj);
  };
}

/**
 * Create a memoized selector (for Redux/state)
 */
export function createMemoizedSelector(selector, options = {}) {
  const { equalityCheck = (a, b) => a === b } = options;

  let lastArgs = null;
  let lastResult = null;

  return function memoizedSelector(...args) {
    // Check if args have changed
    if (
      lastArgs !== null &&
      lastArgs.length === args.length &&
      lastArgs.every((arg, index) => equalityCheck(arg, args[index]))
    ) {
      return lastResult;
    }

    // Compute new result
    lastArgs = args;
    lastResult = selector(...args);
    return lastResult;
  };
}

/**
 * Batch execution of similar operations
 */
export class BatchExecutor {
  constructor(executeFn, options = {}) {
    this.executeFn = executeFn;
    this.batchSize = options.batchSize || 10;
    this.delay = options.delay || 50;
    this.pending = [];
    this.timer = null;
  }

  add(item) {
    return new Promise((resolve, reject) => {
      this.pending.push({ item, resolve, reject });

      if (this.pending.length >= this.batchSize) {
        this.flush();
      } else if (!this.timer) {
        this.timer = setTimeout(() => this.flush(), this.delay);
      }
    });
  }

  async flush() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    if (this.pending.length === 0) {
      return;
    }

    const batch = this.pending;
    this.pending = [];

    try {
      const items = batch.map((b) => b.item);
      const results = await this.executeFn(items);

      batch.forEach((b, index) => {
        b.resolve(results[index]);
      });
    } catch (error) {
      batch.forEach((b) => {
        b.reject(error);
      });
    }
  }
}

/**
 * Debounce utility
 */
export function debounce(fn, delay = 300) {
  let timeoutId;

  return function debounced(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

/**
 * Throttle utility
 */
export function throttle(fn, limit = 300) {
  let inThrottle;

  return function throttled(...args) {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

/**
 * Once utility - executes function only once
 */
export function once(fn) {
  let called = false;
  let result;

  return function onced(...args) {
    if (!called) {
      called = true;
      result = fn.apply(this, args);
    }
    return result;
  };
}

const memoizationUtils = {
  memoize,
  memoizeAsync,
  memoizeWeak,
  createMemoizedSelector,
  BatchExecutor,
  debounce,
  throttle,
  once,
};

export default memoizationUtils;
