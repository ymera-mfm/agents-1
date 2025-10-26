# Security Policy

## 🔒 Security Overview

AgentFlow takes security seriously. This document outlines our security policies, vulnerability reporting procedures, and security best practices.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability in AgentFlow, please send an email to security@agentflow.com.

We take all security vulnerabilities seriously and will respond as quickly as possible.

### What to Include

Please include:
- **Description of the vulnerability:** Clear explanation of the security issue
- **Steps to reproduce:** Detailed steps to demonstrate the vulnerability
- **Potential impact:** Assessment of the security impact
- **Suggested fix (if any):** Proposed remediation steps
- **Your contact information:** For follow-up questions

### Response Timeline

- **Acknowledgment:** Within 48 hours of report
- **Initial Assessment:** Within 7 days
- **Status Updates:** Every 7 days until resolved
- **Resolution:** Based on severity (Critical: 1-3 days, High: 7-14 days, Medium: 30 days)

## 🔍 Security Scanning

### Automated Security Scans

We have implemented automated security scanning tools:

```bash
# Run comprehensive security scan
npm run security:scan

# Run dependency vulnerability check
npm audit

# Check for outdated packages
npm outdated
```

### Security Scan Features

Our security scanner checks for:

- ✅ Cross-Site Scripting (XSS) vulnerabilities
- ✅ Cross-Site Request Forgery (CSRF) protection
- ✅ Insecure data storage
- ✅ HTTPS enforcement
- ✅ Security headers configuration
- ✅ Content Security Policy (CSP)
- ✅ Cookie security
- ✅ Input validation
- ✅ Authentication security
- ✅ Data exposure risks
- ✅ Hardcoded secrets
- ✅ Dependency vulnerabilities
- ✅ Configuration security

## 🛡️ Security Measures Implemented

### 1. HTTPS Enforcement

- All production traffic uses HTTPS
- HTTP requests are automatically redirected to HTTPS
- Strict-Transport-Security header enabled

### 2. Security Headers

```nginx
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: no-referrer-when-downgrade
Content-Security-Policy: default-src 'self'
```

### 3. Content Security Policy (CSP)

- Restricts resource loading to trusted sources
- Prevents inline script execution in production
- Mitigates XSS attacks

### 4. Authentication & Authorization

- JWT-based authentication
- Secure session management
- Session timeout after inactivity
- Secure cookie attributes (HttpOnly, Secure, SameSite)

### 5. Input Validation & Sanitization

- All user inputs are validated
- XSS protection through DOMPurify
- SQL injection prevention through parameterized queries
- CSRF token validation

### 6. Data Protection

- Sensitive data encrypted at rest
- Secure data transmission over HTTPS
- No sensitive data in localStorage
- Password hashing with bcrypt

### 7. Error Handling

- Generic error messages in production
- Detailed logging server-side only
- No stack traces exposed to users

### 8. Rate Limiting

- API endpoint rate limiting
- Protection against brute force attacks
- DDoS mitigation

### 9. Dependency Management

- Regular dependency updates
- Automated vulnerability scanning
- No known vulnerabilities in production

### 10. Docker Security

- Non-root user in containers
- Minimal base images
- Security scanning of Docker images

## 📋 Security Checklist

Before deploying to production, ensure:

- [ ] All dependencies are up to date
- [ ] No critical or high vulnerabilities in npm audit
- [ ] HTTPS is enabled and enforced
- [ ] Security headers are configured
- [ ] CSP is properly set
- [ ] Authentication is working correctly
- [ ] Sensitive data is encrypted
- [ ] Error messages don't expose sensitive information
- [ ] Rate limiting is enabled
- [ ] Logging is properly configured
- [ ] Security scan passes (npm run security:scan)

## 🔐 Security Best Practices

For developers working on AgentFlow:

1. **Never commit secrets** - Use environment variables
2. **Validate all inputs** - Never trust user input
3. **Use HTTPS everywhere** - No exceptions
4. **Implement least privilege** - Grant minimal required permissions
5. **Keep dependencies updated** - Regular npm updates
6. **Review code for security** - Security-first mindset
7. **Log security events** - Monitor for suspicious activity
8. **Test security regularly** - Automated and manual testing

See [Security Best Practices Guide](docs/SECURITY_BEST_PRACTICES.md) for detailed guidelines.

## 📚 Security Resources

### Internal Documentation

- **Production Security Configuration:** `docs/PRODUCTION_SECURITY_CONFIG.md` - Comprehensive production deployment guide
- **Production Readiness Checklist:** `docs/PRODUCTION_READINESS_CHECKLIST.md` - Pre-deployment verification
- **Operations Runbook:** `docs/OPERATIONS_RUNBOOK.md` - Operational procedures and troubleshooting
- **Security Template:** `.github/ISSUE_TEMPLATE/security-vulnerability.yml`
- **Security Scanner:** `scripts/security-scan.js`
- **Environment Validator:** `scripts/validate-env.js`
- **Best Practices:** `docs/SECURITY_BEST_PRACTICES.md`
- **Security Service:** `src/services/security.js`
- **Security Utils:** `src/utils/security-scanner.js`

### Quick Commands

```bash
# Validate production environment configuration
npm run validate:env:prod

# Run comprehensive security scan
npm run security:scan

# Verify deployment
npm run deploy:verify:prod

# Run all pre-deployment checks
npm run predeploy
```

### External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## 🔒 Vulnerability Disclosure Policy

### Responsible Disclosure

We follow responsible disclosure practices:

1. **Private Reporting:** Report vulnerabilities privately first
2. **Coordinated Disclosure:** Work with us on fix timeline
3. **Public Disclosure:** After fix is deployed (90-day window)
4. **Credit:** Security researchers are credited (if desired)

### Bug Bounty

Currently, we do not offer a formal bug bounty program, but we greatly appreciate security research and will acknowledge all responsible disclosures.

## 📞 Contact

- **Security Email:** security@agentflow.com
- **General Support:** support@agentflow.com
- **Website:** https://agentflow.com

---

**Last Updated:** 2025-10-25  
**Version:** 1.1  
**Classification:** Public

## 🚀 Production Deployment

For production deployment guidance, see:
- **[Production Security Configuration](docs/PRODUCTION_SECURITY_CONFIG.md)** - Complete deployment guide
- **[Production Readiness Checklist](docs/PRODUCTION_READINESS_CHECKLIST.md)** - Pre-deployment verification
- **[Operations Runbook](docs/OPERATIONS_RUNBOOK.md)** - Operational procedures

