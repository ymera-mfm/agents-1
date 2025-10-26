# Security Scanning System

## 🔍 Overview

The AgentFlow security scanning system provides automated vulnerability detection and security best practices enforcement. It helps identify common security issues before they reach production.

## 🚀 Quick Start

### Run Security Scan

```bash
# Run comprehensive security scan
npm run security:scan

# View detailed report
cat security-scan-report.json
```

### Run Individual Security Checks

```bash
# Check for dependency vulnerabilities
npm audit

# Check for outdated packages
npm outdated

# Run security audit with specific severity level
npm run audit:security
```

## 📋 What Gets Scanned

### 1. Dependency Vulnerabilities
- Known vulnerabilities in npm packages
- Severity levels: Critical, High, Medium, Low
- Automatic fix suggestions

### 2. Sensitive Files
- Checks if sensitive files are in .gitignore
- Validates environment file security
- Ensures secrets are not committed

### 3. Hardcoded Secrets
- API keys and tokens
- Passwords and credentials
- Cloud provider keys (AWS, Google Cloud, Stripe)
- Bearer tokens and JWT secrets

### 4. Package Security
- Outdated packages
- Missing security scripts
- Package.json configuration

### 5. Security Best Practices
- HTTPS enforcement
- Security headers configuration
- Docker security
- nginx configuration

### 6. Client-Side Security (Browser)
- XSS vulnerabilities
- CSRF protection
- Content Security Policy
- Cookie security
- Input validation
- Authentication security
- Data exposure risks

## 📊 Security Report

The security scan generates a detailed JSON report with:

```json
{
  "scanDate": "2025-10-24T18:19:52.476Z",
  "summary": {
    "total": 1,
    "critical": 0,
    "high": 0,
    "medium": 1,
    "low": 0
  },
  "vulnerabilities": [],
  "warnings": [],
  "info": []
}
```

### Severity Levels

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| 🔴 Critical | Immediate security risk | Fix immediately |
| 🟠 High | Significant security risk | Fix within 7 days |
| 🟡 Medium | Moderate security risk | Fix within 30 days |
| 🟢 Low | Minor security concern | Address in next release |

## 🔧 Security Scanner Components

### 1. CLI Scanner (`scripts/security-scan.js`)

Node.js script that performs:
- File system scanning
- Dependency analysis
- Configuration validation
- Secret detection

**Usage:**
```bash
node scripts/security-scan.js
```

### 2. Browser Scanner (`src/utils/security-scanner.js`)

Client-side security checks:
- Runtime vulnerability detection
- DOM-based XSS checks
- Storage security validation
- Network security analysis

**Usage:**
```javascript
import { securityScanner } from './utils/security-scanner';

// Run full scan
const report = await securityScanner.runFullScan();

// Print to console
securityScanner.printReport(report);

// Export as markdown
const markdown = securityScanner.formatMarkdown(report);
```

### 3. Security Service Integration

The security service integrates both scanners:

```javascript
import { securityService } from './services/security';

// Run comprehensive scan
const report = await securityService.runComprehensiveScan();

// Print report
securityService.printSecurityReport(report);

// Export as markdown
const markdown = securityService.exportSecurityReportMarkdown(report);
```

## 🛡️ Security Checks in Detail

### XSS Detection

Checks for:
- Unsafe innerHTML usage
- Unsanitized user input
- Missing Content Security Policy
- Dangerous DOM manipulation

**Prevention:**
```javascript
// Bad
element.innerHTML = userInput;

// Good
element.textContent = userInput;

// Or use DOMPurify
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

### CSRF Protection

Validates:
- CSRF tokens in forms
- SameSite cookie attributes
- Anti-CSRF headers

**Implementation:**
```javascript
// Set SameSite cookie attribute
res.cookie('sessionId', session.id, {
  sameSite: 'strict',
  secure: true,
  httpOnly: true
});
```

### Sensitive Data Storage

Identifies:
- Credentials in localStorage
- Tokens in sessionStorage
- Unencrypted sensitive data

**Best Practice:**
```javascript
// Don't store sensitive data in localStorage
❌ localStorage.setItem('authToken', token);

// Use httpOnly cookies instead
✅ Set-Cookie: authToken=...; HttpOnly; Secure; SameSite=Strict
```

### HTTPS Enforcement

Verifies:
- HTTPS protocol usage
- Secure cookie flags
- HSTS header configuration

### Security Headers

Checks for:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Strict-Transport-Security
- Content-Security-Policy

## 🔒 Issue Template

Use the security vulnerability template to report security issues:

1. Go to GitHub Issues
2. Click "New Issue"
3. Select "🔒 Security Vulnerability"
4. Fill in all required fields
5. Submit (or email for critical issues)

Template includes:
- Vulnerability classification
- Severity assessment
- Technical details
- Proof of concept
- Proposed fixes
- Impact assessment
- Remediation steps

## 📝 Best Practices

### For Developers

1. **Run security scan before commits**
   ```bash
   npm run security:scan
   ```

2. **Fix critical and high issues immediately**

3. **Review security warnings regularly**

4. **Keep dependencies updated**
   ```bash
   npm update
   npm audit fix
   ```

5. **Never commit secrets**
   - Use environment variables
   - Add sensitive files to .gitignore
   - Use secrets management tools

### For DevOps

1. **Integrate into CI/CD pipeline**
   ```yaml
   - name: Security Scan
     run: npm run security:scan
   ```

2. **Set up automated alerts**

3. **Regular security audits**

4. **Monitor security advisories**

5. **Implement security gates**
   - Block PRs with critical vulnerabilities
   - Require security review for sensitive changes

## 🔍 Continuous Monitoring

### Automated Scanning

Add to your CI/CD pipeline:

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: npm ci
      - name: Run security scan
        run: npm run security:scan
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: security-report
          path: security-scan-report.json
```

### Regular Audits

Schedule regular security audits:
- **Weekly:** Dependency updates and scanning
- **Monthly:** Comprehensive security review
- **Quarterly:** Penetration testing
- **Annually:** Security architecture review

## 📚 Resources

### Internal Documentation
- [Security Best Practices](./SECURITY_BEST_PRACTICES.md)
- [Security Policy](../SECURITY.md)
- [Issue Template](.github/ISSUE_TEMPLATE/security-vulnerability.yml)

### External Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [npm Security Best Practices](https://docs.npmjs.com/packages-and-modules/securing-your-code)
- [Node.js Security Checklist](https://github.com/goldbergyoni/nodebestpractices#6-security-best-practices)

## 🆘 Getting Help

If you need help with security:

1. **For security vulnerabilities:** security@agentflow.com
2. **For questions:** Open a discussion on GitHub
3. **For bugs:** Create an issue using the bug template

## 📄 License

This security scanning system is part of AgentFlow and follows the same license.

---

**Last Updated:** 2025-10-24  
**Maintained By:** AgentFlow Security Team
