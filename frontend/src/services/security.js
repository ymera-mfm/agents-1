import { config } from './config';
import { securityScanner } from '../utils/security-scanner';

// Security utilities and configurations
export class SecurityService {
  constructor() {
    this.initializeCSP();
    this.setupSecurityHeaders();
    this.initializeSessionManagement();
    this.scanner = securityScanner;
  }

  // Initialize Content Security Policy
  initializeCSP() {
    if (!config.security.enableCSP) {
      return;
    }

    const cspDirectives = {
      'default-src': ["'self'"],
      'script-src': [
        "'self'",
        "'unsafe-inline'", // Required for React development
        "'unsafe-eval'", // Required for development tools
        'https://cdn.jsdelivr.net',
        'https://unpkg.com',
      ],
      'style-src': [
        "'self'",
        "'unsafe-inline'", // Required for styled-components and CSS-in-JS
        'https://fonts.googleapis.com',
      ],
      'font-src': ["'self'", 'https://fonts.gstatic.com', 'data:'],
      'img-src': ["'self'", 'data:', 'blob:', 'https:'],
      'connect-src': [
        "'self'",
        config.api.baseUrl,
        config.api.wsUrl,
        'https://api.agentflow.com',
        'wss://ws.agentflow.com',
      ],
      'frame-src': ["'none'"],
      'object-src': ["'none'"],
      'base-uri': ["'self'"],
      'form-action': ["'self'"],
      'frame-ancestors': ["'none'"],
      'upgrade-insecure-requests': [],
    };

    // Build CSP string
    const cspString = Object.entries(cspDirectives)
      .map(([directive, sources]) => {
        if (sources.length === 0) {
          return directive;
        }
        return `${directive} ${sources.join(' ')}`;
      })
      .join('; ');

    // Apply CSP via meta tag (for client-side applications)
    const metaTag = document.createElement('meta');
    metaTag.httpEquiv = 'Content-Security-Policy';
    metaTag.content = cspString;
    document.head.appendChild(metaTag);
  }

  // Setup additional security headers (for server-side implementation)
  setupSecurityHeaders() {
    // These would typically be set on the server, but we can document them
    const securityHeaders = {
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'X-XSS-Protection': '1; mode=block',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
      'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
      'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    };

    // Store for reference and potential server configuration
    this.recommendedHeaders = securityHeaders;
  }

  // Initialize session management
  initializeSessionManagement() {
    this.sessionTimeout = config.security.sessionTimeout;
    this.lastActivity = Date.now();
    this.setupActivityTracking();
    this.setupSessionTimeout();
  }

  // Setup activity tracking
  setupActivityTracking() {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

    const updateActivity = () => {
      this.lastActivity = Date.now();
    };

    events.forEach((event) => {
      document.addEventListener(event, updateActivity, true);
    });
  }

  // Setup session timeout
  setupSessionTimeout() {
    setInterval(() => {
      const now = Date.now();
      const timeSinceLastActivity = now - this.lastActivity;

      if (timeSinceLastActivity > this.sessionTimeout) {
        this.handleSessionTimeout();
      }
    }, 60000); // Check every minute
  }

  // Handle session timeout
  handleSessionTimeout() {
    // Clear sensitive data
    localStorage.removeItem('authToken');
    sessionStorage.clear();

    // Redirect to login or show timeout modal
    window.dispatchEvent(new CustomEvent('sessionTimeout'));
  }

  // Sanitize user input
  sanitizeInput(input) {
    if (typeof input !== 'string') {
      return input;
    }

    return input
      .replace(/[<>]/g, '') // Remove potential HTML tags
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .replace(/vbscript:/gi, '') // Remove vbscript: protocol
      .replace(/data:/gi, '') // Remove data: protocol
      .replace(/on\w+\s*=/gi, '') // Remove event handlers (with whitespace handling)
      .trim();
  }

  // Validate and sanitize URL
  sanitizeUrl(url) {
    try {
      const urlObj = new URL(url);

      // Only allow http and https protocols
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        return null;
      }

      return urlObj.toString();
    } catch (error) {
      return null;
    }
  }

  // Generate secure random token
  generateSecureToken(length = 32) {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('');
  }

  // Hash sensitive data (for client-side hashing)
  async hashData(data) {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  }

  // Validate JWT token structure (basic client-side validation)
  validateJWTStructure(token) {
    if (!token || typeof token !== 'string') {
      return false;
    }

    const parts = token.split('.');
    if (parts.length !== 3) {
      return false;
    }

    try {
      // Validate that each part is valid base64
      parts.forEach((part) => {
        atob(part.replace(/-/g, '+').replace(/_/g, '/'));
      });
      return true;
    } catch (error) {
      return false;
    }
  }

  // Rate limiting for API calls
  createRateLimiter(maxRequests = 100, windowMs = 60000) {
    const requests = new Map();

    return (identifier) => {
      const now = Date.now();
      const windowStart = now - windowMs;

      // Clean old requests
      for (const [key, timestamps] of requests.entries()) {
        const validTimestamps = timestamps.filter((ts) => ts > windowStart);
        if (validTimestamps.length === 0) {
          requests.delete(key);
        } else {
          requests.set(key, validTimestamps);
        }
      }

      // Check current identifier
      const userRequests = requests.get(identifier) || [];
      const recentRequests = userRequests.filter((ts) => ts > windowStart);

      if (recentRequests.length >= maxRequests) {
        return false; // Rate limit exceeded
      }

      // Add current request
      recentRequests.push(now);
      requests.set(identifier, recentRequests);

      return true; // Request allowed
    };
  }

  // Secure local storage wrapper
  secureStorage = {
    setItem: (key, value) => {
      try {
        const encrypted = this.encryptData(JSON.stringify(value));
        localStorage.setItem(key, encrypted);
      } catch (error) {
        console.warn('Failed to set secure storage item:', error);
      }
    },

    getItem: (key) => {
      try {
        const encrypted = localStorage.getItem(key);
        if (!encrypted) {
          return null;
        }

        const decrypted = this.decryptData(encrypted);
        return JSON.parse(decrypted);
      } catch (error) {
        console.warn('Failed to get secure storage item:', error);
        return null;
      }
    },

    removeItem: (key) => {
      localStorage.removeItem(key);
    },
  };

  // Simple encryption for client-side data (not cryptographically secure)
  encryptData(data) {
    // This is a simple obfuscation, not real encryption
    // For real encryption, use Web Crypto API with proper key management
    return btoa(data);
  }

  // Simple decryption for client-side data
  decryptData(encryptedData) {
    try {
      return atob(encryptedData);
    } catch (error) {
      throw new Error('Failed to decrypt data');
    }
  }

  // Check for common security vulnerabilities
  performSecurityCheck() {
    const issues = [];

    // Check for HTTPS in production
    if (config.isProduction && window.location.protocol !== 'https:') {
      issues.push('Application should use HTTPS in production');
    }

    // Check for secure cookies
    if (document.cookie && !document.cookie.includes('Secure')) {
      issues.push('Cookies should have Secure flag in production');
    }

    // Check for CSP
    const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    if (!cspMeta) {
      issues.push('Content Security Policy not found');
    }

    // Check for sensitive data in localStorage
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      const value = localStorage.getItem(key);

      if (value && (value.includes('password') || value.includes('token'))) {
        issues.push(`Potentially sensitive data found in localStorage: ${key}`);
      }
    }

    return issues;
  }

  // Run comprehensive security scan
  async runComprehensiveScan() {
    const report = await this.scanner.runFullScan();
    return report;
  }

  // Print security scan report to console
  printSecurityReport(report) {
    return this.scanner.printReport(report);
  }

  // Export security report as markdown
  exportSecurityReportMarkdown(report) {
    return this.scanner.formatMarkdown(report);
  }

  // Get security recommendations
  getSecurityRecommendations() {
    return {
      headers: this.recommendedHeaders,
      csp: 'Implement Content Security Policy',
      https: 'Use HTTPS in production',
      cookies: 'Set Secure and HttpOnly flags on cookies',
      cors: 'Configure CORS properly',
      authentication: 'Implement proper authentication and authorization',
      inputValidation: 'Validate and sanitize all user inputs',
      errorHandling: 'Avoid exposing sensitive information in error messages',
      logging: 'Implement security logging and monitoring',
      updates: 'Keep dependencies updated and scan for vulnerabilities',
    };
  }
}

// Create singleton instance
export const securityService = new SecurityService();

// Security middleware for API calls
export const securityMiddleware = {
  // Add security headers to requests
  addSecurityHeaders: (config) => {
    return {
      ...config,
      headers: {
        ...config.headers,
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache',
        Pragma: 'no-cache',
      },
    };
  },

  // Validate response for security issues
  validateResponse: (response) => {
    // Check for potential security issues in response
    const securityHeaders = ['x-content-type-options', 'x-frame-options', 'x-xss-protection'];

    const missingHeaders = securityHeaders.filter((header) => !response.headers.get(header));

    if (missingHeaders.length > 0) {
      console.warn('Missing security headers:', missingHeaders);
    }

    return response;
  },
};

export default securityService;
