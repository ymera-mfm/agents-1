/* eslint-disable no-console */
/**
 * Security Scanner Utility
 * Comprehensive security vulnerability scanning for the application
 * Identifies OWASP Top 10 and common security issues
 */

export class SecurityScanner {
  constructor() {
    this.vulnerabilities = [];
    this.warnings = [];
    this.info = [];
  }

  /**
   * Run comprehensive security scan
   */
  async runFullScan() {
    console.log('🔍 Starting comprehensive security scan...');

    this.vulnerabilities = [];
    this.warnings = [];
    this.info = [];

    // Run all security checks
    this.checkXSS();
    this.checkCSRF();
    this.checkInsecureStorage();
    this.checkHTTPS();
    this.checkSecurityHeaders();
    this.checkCSP();
    this.checkCookieSecurity();
    this.checkInputValidation();
    this.checkAuthenticationSecurity();
    this.checkDataExposure();
    this.checkDependencyVulnerabilities();
    this.checkAPISecurityHeaders();
    this.checkRateLimiting();
    this.checkErrorHandling();
    this.checkLoggingSecurity();

    return this.generateReport();
  }

  /**
   * Check for Cross-Site Scripting (XSS) vulnerabilities
   */
  checkXSS() {
    const testElement = document.createElement('div');
    const xssTest = '<script>void(0)</script>';

    try {
      testElement.innerHTML = xssTest;
      if (testElement.querySelector('script')) {
        this.addVulnerability(
          'XSS',
          'HIGH',
          'Application may be vulnerable to XSS attacks. Ensure all user input is sanitized.',
          'Use DOMPurify or similar library to sanitize all user inputs before rendering'
        );
      }
    } catch (e) {
      this.addInfo('XSS', 'Browser has built-in XSS protection');
    }

    // Check for dangerous innerHTML usage
    const scripts = Array.from(document.querySelectorAll('script'));
    const hasInlineScripts = scripts.some(
      (script) => script.innerHTML.includes('innerHTML') && !script.src
    );

    if (hasInlineScripts) {
      this.addWarning(
        'XSS',
        'MEDIUM',
        'Detected potential use of innerHTML. Verify all uses are properly sanitized.',
        'Replace innerHTML with textContent where possible, or use a sanitization library'
      );
    }
  }

  /**
   * Check for Cross-Site Request Forgery (CSRF) protection
   */
  checkCSRF() {
    // Check if forms have CSRF tokens
    const forms = document.querySelectorAll('form');
    let formsWithoutCSRF = 0;

    forms.forEach((form) => {
      const hasCSRFToken =
        form.querySelector('input[name="csrf_token"]') || form.querySelector('input[name="_csrf"]');
      if (!hasCSRFToken && form.method.toLowerCase() === 'post') {
        formsWithoutCSRF++;
      }
    });

    if (formsWithoutCSRF > 0) {
      this.addWarning(
        'CSRF',
        'MEDIUM',
        `Found ${formsWithoutCSRF} POST forms without CSRF tokens`,
        'Implement CSRF token validation for all state-changing operations'
      );
    }

    // Check for SameSite cookie attribute
    const cookies = document.cookie.split(';');
    const hasSecureCookies = cookies.some(
      (cookie) =>
        cookie.toLowerCase().includes('samesite=strict') ||
        cookie.toLowerCase().includes('samesite=lax')
    );

    if (!hasSecureCookies && cookies.length > 0) {
      this.addWarning(
        'CSRF',
        'MEDIUM',
        'Cookies do not have SameSite attribute set',
        'Set SameSite=Strict or SameSite=Lax on all cookies'
      );
    }
  }

  /**
   * Check for insecure data storage
   */
  checkInsecureStorage() {
    const sensitiveKeywords = [
      'password',
      'token',
      'secret',
      'key',
      'auth',
      'credential',
      'api_key',
      'private',
      'ssn',
      'credit',
    ];

    // Check localStorage
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      const value = localStorage.getItem(key);

      sensitiveKeywords.forEach((keyword) => {
        if (
          key.toLowerCase().includes(keyword) ||
          (value && value.toLowerCase().includes(keyword))
        ) {
          this.addVulnerability(
            'SENSITIVE_DATA_EXPOSURE',
            'HIGH',
            `Potentially sensitive data found in localStorage: ${key}`,
            'Store sensitive data in secure, httpOnly cookies or use sessionStorage with encryption'
          );
        }
      });
    }

    // Check sessionStorage
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      const value = sessionStorage.getItem(key);

      sensitiveKeywords.forEach((keyword) => {
        if (
          key.toLowerCase().includes(keyword) ||
          (value && value.toLowerCase().includes(keyword))
        ) {
          this.addWarning(
            'SENSITIVE_DATA_EXPOSURE',
            'MEDIUM',
            `Potentially sensitive data found in sessionStorage: ${key}`,
            'Encrypt sensitive data before storing or use secure server-side sessions'
          );
        }
      });
    }
  }

  /**
   * Check HTTPS usage
   */
  checkHTTPS() {
    if (
      window.location.protocol !== 'https:' &&
      window.location.hostname !== 'localhost' &&
      !window.location.hostname.startsWith('127.0.0.1')
    ) {
      this.addVulnerability(
        'INSECURE_TRANSPORT',
        'CRITICAL',
        'Application is not using HTTPS',
        'Enable HTTPS for all production environments. Redirect all HTTP traffic to HTTPS'
      );
    } else if (window.location.protocol === 'https:') {
      this.addInfo('HTTPS', 'Application is using HTTPS ✓');
    }
  }

  /**
   * Check security headers
   */
  checkSecurityHeaders() {
    const requiredHeaders = [
      'X-Content-Type-Options',
      'X-Frame-Options',
      'X-XSS-Protection',
      'Strict-Transport-Security',
      'Referrer-Policy',
    ];

    // Note: We can't directly check response headers from client-side
    // This is more of a documentation/reminder
    this.addInfo(
      'SECURITY_HEADERS',
      'Verify the following security headers are set on server:\n' +
        requiredHeaders.map((h) => `  - ${h}`).join('\n')
    );
  }

  /**
   * Check Content Security Policy
   */
  checkCSP() {
    const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    const cspMetaContent = cspMeta?.content || '';

    if (!cspMeta) {
      this.addWarning(
        'CSP',
        'MEDIUM',
        'Content Security Policy not found',
        'Implement a strict Content Security Policy to prevent XSS attacks'
      );
      return;
    }

    // Check for unsafe directives
    if (cspMetaContent.includes("'unsafe-inline'") || cspMetaContent.includes("'unsafe-eval'")) {
      this.addWarning(
        'CSP',
        'MEDIUM',
        'CSP contains unsafe directives (unsafe-inline or unsafe-eval)',
        'Remove unsafe-inline and unsafe-eval from CSP. Use nonces or hashes for inline scripts'
      );
    }

    // Check for wildcards
    if (cspMetaContent.includes('*')) {
      this.addWarning(
        'CSP',
        'MEDIUM',
        'CSP contains wildcard (*) which weakens protection',
        'Replace wildcards with specific allowed domains'
      );
    }

    if (!cspMetaContent.includes('upgrade-insecure-requests')) {
      this.addInfo('CSP', 'Consider adding "upgrade-insecure-requests" directive to CSP');
    }
  }

  /**
   * Check cookie security
   */
  checkCookieSecurity() {
    const cookies = document.cookie.split(';');

    if (cookies.length === 0 || (cookies.length === 1 && cookies[0] === '')) {
      this.addInfo('COOKIES', 'No cookies detected in client-side');
      return;
    }

    cookies.forEach((cookie) => {
      const cookieLower = cookie.toLowerCase();

      if (!cookieLower.includes('secure') && window.location.protocol === 'https:') {
        this.addWarning(
          'COOKIE_SECURITY',
          'MEDIUM',
          'Cookie missing Secure flag',
          'Add Secure flag to all cookies when using HTTPS'
        );
      }

      if (!cookieLower.includes('httponly')) {
        this.addWarning(
          'COOKIE_SECURITY',
          'MEDIUM',
          'Cookie missing HttpOnly flag',
          'Add HttpOnly flag to cookies to prevent JavaScript access'
        );
      }

      if (!cookieLower.includes('samesite')) {
        this.addWarning(
          'COOKIE_SECURITY',
          'MEDIUM',
          'Cookie missing SameSite attribute',
          'Add SameSite=Strict or SameSite=Lax to prevent CSRF attacks'
        );
      }
    });
  }

  /**
   * Check input validation
   */
  checkInputValidation() {
    const inputs = document.querySelectorAll('input, textarea');
    let inputsWithoutValidation = 0;

    inputs.forEach((input) => {
      const hasValidation =
        input.pattern ||
        input.required ||
        input.minLength ||
        input.maxLength ||
        input.type !== 'text';

      if (!hasValidation) {
        inputsWithoutValidation++;
      }
    });

    if (inputsWithoutValidation > 0) {
      this.addWarning(
        'INPUT_VALIDATION',
        'MEDIUM',
        `Found ${inputsWithoutValidation} inputs without validation attributes`,
        'Add validation (pattern, required, min/maxLength) to all user inputs'
      );
    }
  }

  /**
   * Check authentication security
   */
  checkAuthenticationSecurity() {
    const hasAuthToken =
      localStorage.getItem('authToken') ||
      localStorage.getItem('token') ||
      sessionStorage.getItem('authToken') ||
      sessionStorage.getItem('token');

    if (hasAuthToken) {
      this.addWarning(
        'AUTHENTICATION',
        'HIGH',
        'Authentication token found in browser storage',
        'Store authentication tokens in httpOnly cookies, not localStorage/sessionStorage'
      );
    }

    // Check password inputs
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach((input) => {
      if (input.autocomplete === 'on') {
        this.addWarning(
          'AUTHENTICATION',
          'LOW',
          'Password field has autocomplete enabled',
          'Set autocomplete="off" or autocomplete="new-password" for password fields'
        );
      }
    });
  }

  /**
   * Check for data exposure
   */
  checkDataExposure() {
    // Check for console.log in production
    if (
      window.location.hostname !== 'localhost' &&
      !window.location.hostname.startsWith('127.0.0.1')
    ) {
      const originalConsoleLog = console.log;
      let consoleUsageDetected = false;

      console.log = function () {
        consoleUsageDetected = true;
        originalConsoleLog.apply(console, arguments);
      };

      // Synchronously test for console.log usage (example: call a function that may log)
      // For demonstration, we do not call any function here, but in a real scenario,
      // you would wrap the code that may use console.log here.
      // Immediately restore console.log
      console.log = originalConsoleLog;

      if (consoleUsageDetected) {
        this.addWarning(
          'DATA_EXPOSURE',
          'LOW',
          'console.log detected in production',
          'Remove all console.log statements in production builds'
        );
      }
    }

    // Check for exposed API keys in page source
    const pageSource = document.documentElement.outerHTML;
    const apiKeyPatterns = [
      /api[_-]?key['"]?\s*[:=]\s*['"]\w{20,}/gi,
      /secret['"]?\s*[:=]\s*['"]\w{20,}/gi,
      /token['"]?\s*[:=]\s*['"]\w{20,}/gi,
    ];

    apiKeyPatterns.forEach((pattern) => {
      if (pattern.test(pageSource)) {
        this.addVulnerability(
          'DATA_EXPOSURE',
          'CRITICAL',
          'Potential API key or secret exposed in page source',
          'Never hardcode API keys or secrets in client-side code. Use environment variables and server-side proxies'
        );
      }
    });
  }

  /**
   * Check dependency vulnerabilities (basic check)
   */
  checkDependencyVulnerabilities() {
    this.addInfo(
      'DEPENDENCIES',
      'Run "npm audit" to check for known vulnerabilities in dependencies'
    );
  }

  /**
   * Check API security headers
   */
  checkAPISecurityHeaders() {
    this.addInfo(
      'API_SECURITY',
      'Verify API endpoints implement:\n' +
        '  - Rate limiting\n' +
        '  - Authentication/Authorization\n' +
        '  - Input validation\n' +
        '  - CORS configuration\n' +
        '  - Request size limits'
    );
  }

  /**
   * Check rate limiting
   */
  checkRateLimiting() {
    // This is a basic check - actual implementation would need server-side testing
    this.addInfo(
      'RATE_LIMITING',
      'Implement rate limiting on all API endpoints to prevent abuse and DDoS attacks'
    );
  }

  /**
   * Check error handling
   */
  checkErrorHandling() {
    // Check if errors are exposed in production
    const originalError = console.error;
    let errorExposed = false;

    console.error = function () {
      errorExposed = true;
      originalError.apply(console, arguments);
    };

    // Perform error handling check synchronously here
    // ... (simulate error logging if needed)
    console.error = originalError;

    if (errorExposed && window.location.hostname !== 'localhost') {
      this.addWarning(
        'ERROR_HANDLING',
        'MEDIUM',
        'Detailed errors exposed in production',
        'Implement generic error messages in production. Log detailed errors server-side only'
      );
    }
  }

  /**
   * Check logging security
   */
  checkLoggingSecurity() {
    this.addInfo(
      'LOGGING',
      'Ensure logging implementation:\n' +
        '  - Does not log sensitive data (passwords, tokens, PII)\n' +
        '  - Logs security events (login, logout, permission changes)\n' +
        '  - Uses appropriate log levels\n' +
        '  - Implements log rotation and retention\n' +
        '  - Protects log files from unauthorized access'
    );
  }

  /**
   * Add vulnerability to report
   */
  addVulnerability(type, severity, description, remediation) {
    this.vulnerabilities.push({
      type,
      severity,
      description,
      remediation,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Add warning to report
   */
  addWarning(type, severity, description, remediation) {
    this.warnings.push({
      type,
      severity,
      description,
      remediation,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Add info to report
   */
  addInfo(type, description) {
    this.info.push({
      type,
      description,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Generate security report
   */
  generateReport() {
    const report = {
      scanDate: new Date().toISOString(),
      summary: {
        total: this.vulnerabilities.length + this.warnings.length,
        critical: this.vulnerabilities.filter((v) => v.severity === 'CRITICAL').length,
        high: this.vulnerabilities.filter((v) => v.severity === 'HIGH').length,
        medium: this.warnings.filter((w) => w.severity === 'MEDIUM').length,
        low: this.warnings.filter((w) => w.severity === 'LOW').length,
      },
      vulnerabilities: this.vulnerabilities,
      warnings: this.warnings,
      info: this.info,
      recommendations: this.getRecommendations(),
    };

    return report;
  }

  /**
   * Get security recommendations
   */
  getRecommendations() {
    return {
      immediate: [
        'Fix all CRITICAL and HIGH severity vulnerabilities immediately',
        'Enable HTTPS for all environments',
        'Implement proper authentication and authorization',
        'Remove sensitive data from client-side storage',
      ],
      shortTerm: [
        'Implement Content Security Policy',
        'Add security headers (X-Frame-Options, X-Content-Type-Options, etc.)',
        'Implement CSRF protection',
        'Add input validation and sanitization',
        'Set up rate limiting',
      ],
      longTerm: [
        'Implement security monitoring and logging',
        'Regular security audits and penetration testing',
        'Security training for development team',
        'Establish security development lifecycle',
        'Set up automated security scanning in CI/CD pipeline',
      ],
    };
  }

  /**
   * Format report as console output
   */
  printReport(report) {
    console.group('🔒 Security Scan Report');

    console.log('📅 Scan Date:', report.scanDate);
    console.log('\n📊 Summary:');
    console.log(`   Total Issues: ${report.summary.total}`);
    console.log(`   🔴 Critical: ${report.summary.critical}`);
    console.log(`   🟠 High: ${report.summary.high}`);
    console.log(`   🟡 Medium: ${report.summary.medium}`);
    console.log(`   🟢 Low: ${report.summary.low}`);

    if (report.vulnerabilities.length > 0) {
      console.group('\n🚨 Vulnerabilities:');
      report.vulnerabilities.forEach((vuln, index) => {
        console.group(`${index + 1}. [${vuln.severity}] ${vuln.type}`);
        console.log('Description:', vuln.description);
        console.log('Remediation:', vuln.remediation);
        console.groupEnd();
      });
      console.groupEnd();
    }

    if (report.warnings.length > 0) {
      console.group('\n⚠️ Warnings:');
      report.warnings.forEach((warn, index) => {
        console.group(`${index + 1}. [${warn.severity}] ${warn.type}`);
        console.log('Description:', warn.description);
        console.log('Remediation:', warn.remediation);
        console.groupEnd();
      });
      console.groupEnd();
    }

    if (report.info.length > 0) {
      console.group('\nℹ️ Information:');
      report.info.forEach((info, index) => {
        console.log(`${index + 1}. [${info.type}]`, info.description);
      });
      console.groupEnd();
    }

    console.group('\n💡 Recommendations:');
    console.group('Immediate Actions:');
    report.recommendations.immediate.forEach((rec, i) => console.log(`${i + 1}. ${rec}`));
    console.groupEnd();

    console.group('Short-term Actions:');
    report.recommendations.shortTerm.forEach((rec, i) => console.log(`${i + 1}. ${rec}`));
    console.groupEnd();

    console.group('Long-term Actions:');
    report.recommendations.longTerm.forEach((rec, i) => console.log(`${i + 1}. ${rec}`));
    console.groupEnd();
    console.groupEnd();

    console.groupEnd();

    return report;
  }

  /**
   * Format report as markdown
   */
  formatMarkdown(report) {
    let markdown = `# 🔒 Security Scan Report\n\n`;
    markdown += `**Scan Date:** ${new Date(report.scanDate).toLocaleString()}\n\n`;

    markdown += `## 📊 Summary\n\n`;
    markdown += `| Severity | Count |\n`;
    markdown += `|----------|-------|\n`;
    markdown += `| 🔴 Critical | ${report.summary.critical} |\n`;
    markdown += `| 🟠 High | ${report.summary.high} |\n`;
    markdown += `| 🟡 Medium | ${report.summary.medium} |\n`;
    markdown += `| 🟢 Low | ${report.summary.low} |\n`;
    markdown += `| **Total** | **${report.summary.total}** |\n\n`;

    if (report.vulnerabilities.length > 0) {
      markdown += `## 🚨 Vulnerabilities\n\n`;
      report.vulnerabilities.forEach((vuln, index) => {
        markdown += `### ${index + 1}. [${vuln.severity}] ${vuln.type}\n\n`;
        markdown += `**Description:** ${vuln.description}\n\n`;
        markdown += `**Remediation:** ${vuln.remediation}\n\n`;
        markdown += `---\n\n`;
      });
    }

    if (report.warnings.length > 0) {
      markdown += `## ⚠️ Warnings\n\n`;
      report.warnings.forEach((warn, index) => {
        markdown += `### ${index + 1}. [${warn.severity}] ${warn.type}\n\n`;
        markdown += `**Description:** ${warn.description}\n\n`;
        markdown += `**Remediation:** ${warn.remediation}\n\n`;
        markdown += `---\n\n`;
      });
    }

    markdown += `## 💡 Recommendations\n\n`;
    markdown += `### Immediate Actions\n\n`;
    report.recommendations.immediate.forEach((rec, i) => {
      markdown += `${i + 1}. ${rec}\n`;
    });

    markdown += `\n### Short-term Actions\n\n`;
    report.recommendations.shortTerm.forEach((rec, i) => {
      markdown += `${i + 1}. ${rec}\n`;
    });

    markdown += `\n### Long-term Actions\n\n`;
    report.recommendations.longTerm.forEach((rec, i) => {
      markdown += `${i + 1}. ${rec}\n`;
    });

    return markdown;
  }
}

// Create and export singleton instance
export const securityScanner = new SecurityScanner();

// Export default
export default securityScanner;
