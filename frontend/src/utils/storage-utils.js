/**
 * Storage utility functions for safe localStorage/sessionStorage operations
 * Centralizes error handling and provides consistent interface
 * @module utils/storage-utils
 */

/**
 * Safely retrieves and parses JSON from storage
 * @param {Storage} storage - The storage object (localStorage or sessionStorage)
 * @param {string} key - The storage key
 * @param {any} defaultValue - Default value if retrieval fails
 * @returns {any} Parsed value or default
 * @example
 * const userData = safeGetJSON(localStorage, 'user', { name: 'Guest' });
 */
export function safeGetJSON(storage, key, defaultValue = null) {
  try {
    const item = storage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.warn(`Failed to retrieve ${key} from storage:`, error);
    return defaultValue;
  }
}

/**
 * Safely stores JSON in storage
 * @param {Storage} storage - The storage object (localStorage or sessionStorage)
 * @param {string} key - The storage key
 * @param {any} value - Value to store
 * @returns {boolean} Success status
 * @example
 * const success = safeSetJSON(localStorage, 'user', { name: 'John' });
 */
export function safeSetJSON(storage, key, value) {
  try {
    storage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.warn(`Failed to store ${key} in storage:`, error);
    return false;
  }
}

/**
 * Safely retrieves a string from storage
 * @param {Storage} storage - The storage object
 * @param {string} key - The storage key
 * @param {string} defaultValue - Default value if retrieval fails
 * @returns {string} Retrieved value or default
 */
export function safeGetString(storage, key, defaultValue = '') {
  try {
    return storage.getItem(key) || defaultValue;
  } catch (error) {
    console.warn(`Failed to retrieve ${key} from storage:`, error);
    return defaultValue;
  }
}

/**
 * Safely stores a string in storage
 * @param {Storage} storage - The storage object
 * @param {string} key - The storage key
 * @param {string} value - Value to store
 * @returns {boolean} Success status
 */
export function safeSetString(storage, key, value) {
  try {
    storage.setItem(key, value);
    return true;
  } catch (error) {
    console.warn(`Failed to store ${key} in storage:`, error);
    return false;
  }
}

/**
 * Safely removes an item from storage
 * @param {Storage} storage - The storage object
 * @param {string} key - The storage key
 * @returns {boolean} Success status
 */
export function safeRemove(storage, key) {
  try {
    storage.removeItem(key);
    return true;
  } catch (error) {
    console.warn(`Failed to remove ${key} from storage:`, error);
    return false;
  }
}

/**
 * Safely clears all items from storage
 * @param {Storage} storage - The storage object
 * @returns {boolean} Success status
 */
export function safeClear(storage) {
  try {
    storage.clear();
    return true;
  } catch (error) {
    console.warn('Failed to clear storage:', error);
    return false;
  }
}

/**
 * Checks if a key exists in storage
 * @param {Storage} storage - The storage object
 * @param {string} key - The storage key
 * @returns {boolean} True if key exists
 */
export function hasKey(storage, key) {
  try {
    return storage.getItem(key) !== null;
  } catch (error) {
    console.warn(`Failed to check ${key} in storage:`, error);
    return false;
  }
}

/**
 * Gets all keys from storage
 * @param {Storage} storage - The storage object
 * @returns {string[]} Array of storage keys
 */
export function getAllKeys(storage) {
  try {
    return Object.keys(storage);
  } catch (error) {
    console.warn('Failed to get storage keys:', error);
    return [];
  }
}

/**
 * Gets storage size in bytes (approximate)
 * @param {Storage} storage - The storage object
 * @returns {number} Approximate size in bytes
 */
export function getStorageSize(storage) {
  try {
    let size = 0;
    for (const key in storage) {
      if (storage.hasOwnProperty(key)) {
        size += key.length + (storage.getItem(key)?.length || 0);
      }
    }
    return size;
  } catch (error) {
    console.warn('Failed to calculate storage size:', error);
    return 0;
  }
}

/**
 * Storage wrapper with namespace support
 */
export class NamespacedStorage {
  /**
   * Creates a namespaced storage instance
   * @param {Storage} storage - The underlying storage
   * @param {string} namespace - Namespace prefix
   */
  constructor(storage, namespace = 'app') {
    this.storage = storage;
    this.namespace = namespace;
  }

  /**
   * Generates namespaced key
   * @param {string} key - Original key
   * @returns {string} Namespaced key
   */
  getNamespacedKey(key) {
    return `${this.namespace}:${key}`;
  }

  /**
   * Sets a JSON value
   * @param {string} key - Storage key
   * @param {any} value - Value to store
   * @returns {boolean} Success status
   */
  setJSON(key, value) {
    return safeSetJSON(this.storage, this.getNamespacedKey(key), value);
  }

  /**
   * Gets a JSON value
   * @param {string} key - Storage key
   * @param {any} defaultValue - Default value
   * @returns {any} Retrieved value or default
   */
  getJSON(key, defaultValue = null) {
    return safeGetJSON(this.storage, this.getNamespacedKey(key), defaultValue);
  }

  /**
   * Sets a string value
   * @param {string} key - Storage key
   * @param {string} value - Value to store
   * @returns {boolean} Success status
   */
  setString(key, value) {
    return safeSetString(this.storage, this.getNamespacedKey(key), value);
  }

  /**
   * Gets a string value
   * @param {string} key - Storage key
   * @param {string} defaultValue - Default value
   * @returns {string} Retrieved value or default
   */
  getString(key, defaultValue = '') {
    return safeGetString(this.storage, this.getNamespacedKey(key), defaultValue);
  }

  /**
   * Removes a key
   * @param {string} key - Storage key
   * @returns {boolean} Success status
   */
  remove(key) {
    return safeRemove(this.storage, this.getNamespacedKey(key));
  }

  /**
   * Checks if key exists
   * @param {string} key - Storage key
   * @returns {boolean} True if exists
   */
  has(key) {
    return hasKey(this.storage, this.getNamespacedKey(key));
  }

  /**
   * Clears all namespaced keys
   * @returns {number} Number of keys cleared
   */
  clearNamespace() {
    try {
      const keys = getAllKeys(this.storage);
      const prefix = `${this.namespace}:`;
      let cleared = 0;

      keys.forEach((key) => {
        if (key.startsWith(prefix)) {
          this.storage.removeItem(key);
          cleared++;
        }
      });

      return cleared;
    } catch (error) {
      console.warn(`Failed to clear namespace ${this.namespace}:`, error);
      return 0;
    }
  }
}

// Export default instances
export const appLocalStorage = new NamespacedStorage(localStorage, 'app');
export const appSessionStorage = new NamespacedStorage(sessionStorage, 'app');
