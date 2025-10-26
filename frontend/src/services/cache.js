import { CONFIG, config } from '../config/config';
import { safeGetJSON, safeSetJSON } from '../utils/storage-utils';
import { TIME_MS } from '../constants/time';

// Enhanced cache service with multiple storage strategies
class CacheService {
  constructor() {
    this.cache = new Map(); // Legacy cache for backward compatibility
    this.memoryCache = new Map();
    this.defaultTTL = CONFIG.CACHE_TTL;
    this.cacheStats = { hits: 0, misses: 0 };
    this.loadCacheStats();
  }

  // Load cache statistics from localStorage
  loadCacheStats() {
    this.cacheStats = safeGetJSON(localStorage, 'cacheStats', { hits: 0, misses: 0 });
  }

  // Save cache statistics to localStorage
  saveCacheStats() {
    safeSetJSON(localStorage, 'cacheStats', this.cacheStats);
  }

  // Generate cache key with namespace
  generateKey(key, namespace = 'default') {
    return `${namespace}:${key}`;
  }

  // Get cache strategy for a given key
  getCacheStrategy(key) {
    const strategies = config?.cache?.strategies || {
      agents: 'memory',
      projects: 'memory',
      analytics: 'sessionStorage',
      user: 'localStorage',
    };

    // Check if key matches any specific strategy
    for (const [pattern, strategy] of Object.entries(strategies)) {
      if (key.includes(pattern)) {
        return strategy;
      }
    }

    return 'memory'; // Default strategy
  }

  // Legacy method for backward compatibility
  set(key, data, ttl = this.defaultTTL) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });

    // Also use enhanced caching
    this.setEnhanced(key, data, ttl);
  }

  // Legacy method for backward compatibility
  get(key) {
    const item = this.cache.get(key);
    if (item) {
      if (Date.now() - item.timestamp > item.ttl) {
        this.cache.delete(key);
        return null;
      }
      return item.data;
    }

    // Try enhanced caching
    return this.getEnhanced(key);
  }

  // Enhanced set method
  setEnhanced(key, value, ttl = this.defaultTTL, namespace = 'default') {
    const cacheKey = this.generateKey(key, namespace);
    const strategy = this.getCacheStrategy(key);
    const expiresAt = Date.now() + ttl;

    const cacheItem = {
      value,
      expiresAt,
      createdAt: Date.now(),
      accessCount: 0,
    };

    try {
      switch (strategy) {
        case 'memory':
          this.setMemoryCache(cacheKey, cacheItem);
          break;
        case 'localStorage':
          this.setLocalStorage(cacheKey, cacheItem);
          break;
        case 'sessionStorage':
          this.setSessionStorage(cacheKey, cacheItem);
          break;
        default:
          this.setMemoryCache(cacheKey, cacheItem);
      }
    } catch (error) {
      console.warn(`Failed to set cache item ${cacheKey}:`, error);
    }
  }

  // Enhanced get method
  getEnhanced(key, namespace = 'default') {
    const cacheKey = this.generateKey(key, namespace);
    const strategy = this.getCacheStrategy(key);

    let cacheItem = null;

    try {
      switch (strategy) {
        case 'memory':
          cacheItem = this.getMemoryCache(cacheKey);
          break;
        case 'localStorage':
          cacheItem = this.getLocalStorage(cacheKey);
          break;
        case 'sessionStorage':
          cacheItem = this.getSessionStorage(cacheKey);
          break;
        default:
          cacheItem = this.getMemoryCache(cacheKey);
      }

      if (cacheItem) {
        // Check if item has expired
        if (Date.now() > cacheItem.expiresAt) {
          this.deleteEnhanced(key, namespace);
          this.cacheStats.misses++;
          this.saveCacheStats();
          return null;
        }

        // Update access count
        cacheItem.accessCount++;
        this.setEnhanced(key, cacheItem.value, cacheItem.expiresAt - Date.now(), namespace);

        this.cacheStats.hits++;
        this.saveCacheStats();
        return cacheItem.value;
      }

      this.cacheStats.misses++;
      this.saveCacheStats();
      return null;
    } catch (error) {
      console.warn(`Failed to get cache item ${cacheKey}:`, error);
      this.cacheStats.misses++;
      this.saveCacheStats();
      return null;
    }
  }

  // Memory cache operations
  setMemoryCache(key, item) {
    const maxSize = config?.cache?.maxSize || 100;

    // Implement LRU eviction if cache is full
    if (this.memoryCache.size >= maxSize) {
      const firstKey = this.memoryCache.keys().next().value;
      this.memoryCache.delete(firstKey);
    }

    this.memoryCache.set(key, item);
  }

  getMemoryCache(key) {
    return this.memoryCache.get(key);
  }

  // localStorage operations
  setLocalStorage(key, item) {
    const success = safeSetJSON(localStorage, key, item);
    if (!success) {
      // Handle quota exceeded - clear expired items and retry
      this.clearExpiredLocalStorage();
      safeSetJSON(localStorage, key, item);
    }
  }

  getLocalStorage(key) {
    return safeGetJSON(localStorage, key, null);
  }

  // sessionStorage operations
  setSessionStorage(key, item) {
    const success = safeSetJSON(sessionStorage, key, item);
    if (!success) {
      // Handle quota exceeded - clear expired items and retry
      this.clearExpiredSessionStorage();
      safeSetJSON(sessionStorage, key, item);
    }
  }

  getSessionStorage(key) {
    return safeGetJSON(sessionStorage, key, null);
  }

  // Clear expired items from localStorage
  clearExpiredLocalStorage() {
    const now = Date.now();
    const keysToRemove = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.includes(':')) {
        try {
          const item = JSON.parse(localStorage.getItem(key));
          if (item && item.expiresAt && now > item.expiresAt) {
            keysToRemove.push(key);
          }
        } catch (error) {
          keysToRemove.push(key);
        }
      }
    }

    keysToRemove.forEach((key) => localStorage.removeItem(key));
  }

  // Clear expired items from sessionStorage
  clearExpiredSessionStorage() {
    const now = Date.now();
    const keysToRemove = [];

    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.includes(':')) {
        try {
          const item = JSON.parse(sessionStorage.getItem(key));
          if (item && item.expiresAt && now > item.expiresAt) {
            keysToRemove.push(key);
          }
        } catch (error) {
          keysToRemove.push(key);
        }
      }
    }

    keysToRemove.forEach((key) => sessionStorage.removeItem(key));
  }

  // Enhanced delete method
  deleteEnhanced(key, namespace = 'default') {
    const cacheKey = this.generateKey(key, namespace);
    const strategy = this.getCacheStrategy(key);

    try {
      switch (strategy) {
        case 'memory':
          this.memoryCache.delete(cacheKey);
          break;
        case 'localStorage':
          localStorage.removeItem(cacheKey);
          break;
        case 'sessionStorage':
          sessionStorage.removeItem(cacheKey);
          break;
        default:
          this.memoryCache.delete(cacheKey);
      }
    } catch (error) {
      console.warn(`Failed to delete cache item ${cacheKey}:`, error);
    }
  }

  // Legacy delete method
  delete(key) {
    this.cache.delete(key);
    this.deleteEnhanced(key);
  }

  // Legacy clear method
  clear() {
    this.cache.clear();
    this.clearEnhanced();
  }

  // Enhanced clear method
  clearEnhanced(namespace = null) {
    if (namespace) {
      // Clear specific namespace
      const prefix = `${namespace}:`;

      // Clear memory cache
      for (const key of this.memoryCache.keys()) {
        if (key.startsWith(prefix)) {
          this.memoryCache.delete(key);
        }
      }

      // Clear localStorage
      const localKeysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(prefix)) {
          localKeysToRemove.push(key);
        }
      }
      localKeysToRemove.forEach((key) => localStorage.removeItem(key));

      // Clear sessionStorage
      const sessionKeysToRemove = [];
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key && key.startsWith(prefix)) {
          sessionKeysToRemove.push(key);
        }
      }
      sessionKeysToRemove.forEach((key) => sessionStorage.removeItem(key));
    } else {
      // Clear all caches
      this.memoryCache.clear();
      this.cache.clear();
    }

    // Reset cache stats
    this.cacheStats = { hits: 0, misses: 0 };
    this.saveCacheStats();
  }

  // Get cache statistics
  getStats() {
    const hitRate =
      this.cacheStats.hits + this.cacheStats.misses > 0
        ? (this.cacheStats.hits / (this.cacheStats.hits + this.cacheStats.misses)) * 100
        : 0;

    return {
      ...this.cacheStats,
      hitRate: Math.round(hitRate * 100) / 100,
      memorySize: this.memoryCache.size,
      legacySize: this.cache.size,
    };
  }

  // Cleanup expired items periodically
  startCleanupInterval() {
    setInterval(() => {
      this.clearExpiredLocalStorage();
      this.clearExpiredSessionStorage();

      // Clear expired memory cache items
      const now = Date.now();
      for (const [key, item] of this.memoryCache) {
        if (item.expiresAt && now > item.expiresAt) {
          this.memoryCache.delete(key);
        }
      }
    }, TIME_MS.MINUTE); // Run every minute
  }
}

// Create singleton instance
export const cacheService = new CacheService();

// Start cleanup interval
cacheService.startCleanupInterval();
