# Security Best Practices Guide

## 🔒 Security Overview

This document outlines security best practices for the AgentFlow application, including vulnerability prevention, secure coding guidelines, and security testing procedures.

## 📋 Table of Contents

1. [OWASP Top 10 Prevention](#owasp-top-10-prevention)
2. [Secure Coding Guidelines](#secure-coding-guidelines)
3. [Authentication & Authorization](#authentication--authorization)
4. [Data Protection](#data-protection)
5. [Security Testing](#security-testing)
6. [Incident Response](#incident-response)

## OWASP Top 10 Prevention

### 1. Broken Access Control

**Prevention:**
- Implement proper authentication and authorization checks
- Deny by default - require explicit permission for all resources
- Use role-based access control (RBAC)
- Validate permissions on the server side
- Disable directory listing

**Implementation:**
```javascript
// Good: Check permissions before accessing resource
async function getResource(userId, resourceId) {
  const user = await getUserById(userId);
  const resource = await getResourceById(resourceId);
  
  if (!user.hasPermission(resource)) {
    throw new ForbiddenError('Access denied');
  }
  
  return resource;
}
```

### 2. Cryptographic Failures

**Prevention:**
- Use HTTPS for all communications
- Never store passwords in plain text - use bcrypt or similar
- Use strong encryption algorithms (AES-256, RSA-2048+)
- Implement proper key management
- Don't roll your own crypto

**Implementation:**
```javascript
// Good: Use Web Crypto API for client-side hashing
async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}
```

### 3. Injection (SQL, XSS, etc.)

**Prevention:**
- Use parameterized queries or ORMs
- Validate and sanitize all user inputs
- Use Content Security Policy (CSP)
- Escape output when rendering user data
- Use allowlists instead of blocklists

**Implementation:**
```javascript
// Bad: SQL Injection vulnerable
const query = `SELECT * FROM users WHERE id = ${userId}`;

// Good: Use parameterized queries
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);

// Bad: XSS vulnerable
element.innerHTML = userInput;

// Good: Use textContent or sanitize
element.textContent = userInput;
// OR
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

### 4. Insecure Design

**Prevention:**
- Perform threat modeling during design phase
- Use secure design patterns
- Implement defense in depth
- Separate duties and privileges
- Limit resource consumption

### 5. Security Misconfiguration

**Prevention:**
- Remove unnecessary features and frameworks
- Keep all systems and dependencies updated
- Use security headers
- Implement proper error handling (don't expose stack traces)
- Disable default accounts and passwords

**Security Headers:**
```nginx
# nginx.conf
add_header X-Frame-Options "DENY";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'";
```

### 6. Vulnerable and Outdated Components

**Prevention:**
- Regularly update dependencies
- Remove unused dependencies
- Use npm audit or similar tools
- Monitor security advisories
- Use software composition analysis (SCA) tools

**Commands:**
```bash
# Check for vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix

# Update outdated packages
npm update

# Check for outdated packages
npm outdated
```

### 7. Identification and Authentication Failures

**Prevention:**
- Implement multi-factor authentication (MFA)
- Use strong password policies
- Implement account lockout mechanisms
- Secure session management
- Never store credentials in code

**Implementation:**
```javascript
// Good: Secure session management
const sessionConfig = {
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true,      // HTTPS only
    httpOnly: true,    // Prevent JavaScript access
    sameSite: 'strict', // CSRF protection
    maxAge: 3600000    // 1 hour
  }
};
```

### 8. Software and Data Integrity Failures

**Prevention:**
- Use digital signatures for software updates
- Implement CI/CD pipeline security
- Use dependency lock files (package-lock.json)
- Verify third-party libraries
- Implement integrity checks

### 9. Security Logging and Monitoring Failures

**Prevention:**
- Log all authentication events
- Log access control failures
- Implement centralized logging
- Set up alerts for suspicious activity
- Protect log files from tampering

**Implementation:**
```javascript
// Good: Comprehensive logging
logger.info('User login attempt', {
  userId: user.id,
  ip: req.ip,
  userAgent: req.headers['user-agent'],
  timestamp: new Date().toISOString()
});

// Log security events
logger.warn('Failed login attempt', {
  username: username,
  ip: req.ip,
  timestamp: new Date().toISOString()
});
```

### 10. Server-Side Request Forgery (SSRF)

**Prevention:**
- Validate and sanitize all URLs
- Use allowlists for allowed domains
- Disable HTTP redirects
- Don't send raw responses to clients
- Use network segmentation

**Implementation:**
```javascript
// Good: Validate URL before making request
function isAllowedUrl(url) {
  const allowedDomains = ['api.example.com', 'trusted-api.com'];
  try {
    const urlObj = new URL(url);
    return allowedDomains.includes(urlObj.hostname);
  } catch (error) {
    return false;
  }
}

async function fetchData(url) {
  if (!isAllowedUrl(url)) {
    throw new Error('Invalid URL');
  }
  return fetch(url);
}
```

## Secure Coding Guidelines

### Input Validation

**Always validate and sanitize user input:**

```javascript
import { z } from 'zod';

// Define validation schema
const userSchema = z.object({
  username: z.string().min(3).max(50).regex(/^[a-zA-Z0-9_]+$/),
  email: z.string().email(),
  age: z.number().int().min(18).max(120)
});

// Validate input
function validateUser(data) {
  try {
    return userSchema.parse(data);
  } catch (error) {
    throw new ValidationError('Invalid user data', error.errors);
  }
}
```

### Output Encoding

**Encode output based on context:**

```javascript
// HTML context
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// JavaScript context
function escapeJs(str) {
  return str
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r');
}

// URL context
function escapeUrl(str) {
  return encodeURIComponent(str);
}
```

### Error Handling

**Never expose sensitive information in errors:**

```javascript
// Bad: Exposes internal details
catch (error) {
  res.status(500).json({ error: error.stack });
}

// Good: Generic error message
catch (error) {
  logger.error('Database error', { error, userId: req.user.id });
  res.status(500).json({ 
    error: 'An error occurred. Please try again later.' 
  });
}
```

### Secrets Management

**Never hardcode secrets:**

```javascript
// Bad: Hardcoded secret
const apiKey = 'sk_live_abc123xyz789';

// Good: Use environment variables
const apiKey = process.env.API_KEY;

// Good: Use secrets management service
const apiKey = await secretsManager.getSecret('api-key');
```

## Authentication & Authorization

### Token-Based Authentication

**Use JWT with proper configuration:**

```javascript
import jwt from 'jsonwebtoken';

// Generate token
function generateToken(user) {
  return jwt.sign(
    { 
      userId: user.id,
      role: user.role 
    },
    process.env.JWT_SECRET,
    { 
      expiresIn: '1h',
      issuer: 'agentflow',
      audience: 'agentflow-api'
    }
  );
}

// Verify token
function verifyToken(token) {
  try {
    return jwt.verify(token, process.env.JWT_SECRET, {
      issuer: 'agentflow',
      audience: 'agentflow-api'
    });
  } catch (error) {
    throw new UnauthorizedError('Invalid token');
  }
}
```

### Authorization Middleware

```javascript
function authorize(requiredRole) {
  return async (req, res, next) => {
    const user = req.user;
    
    if (!user) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    
    if (user.role !== requiredRole) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    
    next();
  };
}

// Usage
app.get('/admin/users', authorize('admin'), getUsers);
```

## Data Protection

### Encryption at Rest

```javascript
import crypto from 'crypto';

const algorithm = 'aes-256-gcm';
const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');

function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(algorithm, key, iv);
  
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  const authTag = cipher.getAuthTag();
  
  return {
    encrypted,
    iv: iv.toString('hex'),
    authTag: authTag.toString('hex')
  };
}

function decrypt(encrypted, iv, authTag) {
  const decipher = crypto.createDecipheriv(
    algorithm,
    key,
    Buffer.from(iv, 'hex')
  );
  
  decipher.setAuthTag(Buffer.from(authTag, 'hex'));
  
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
}
```

### Secure Data Transmission

```javascript
// Always use HTTPS in production
if (process.env.NODE_ENV === 'production' && req.protocol !== 'https') {
  return res.redirect(`https://${req.hostname}${req.url}`);
}

// Set secure cookie options
res.cookie('sessionId', session.id, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  maxAge: 3600000
});
```

## Security Testing

### Automated Security Scanning

```bash
# Run security scan
npm run security:scan

# Run npm audit
npm audit

# Run dependency check
npm outdated
```

### Manual Security Testing

**Test for common vulnerabilities:**

1. **XSS Testing:**
   - Try injecting `<script>alert('XSS')</script>` in all input fields
   - Test with various encoding techniques

2. **SQL Injection Testing:**
   - Try `' OR '1'='1` in input fields
   - Test with various SQL injection payloads

3. **CSRF Testing:**
   - Verify CSRF tokens on all forms
   - Test cross-origin requests

4. **Authentication Testing:**
   - Test with invalid credentials
   - Test session timeout
   - Test concurrent sessions

### Security Test Checklist

- [ ] All user inputs are validated and sanitized
- [ ] Authentication and authorization work correctly
- [ ] Sensitive data is encrypted
- [ ] HTTPS is enforced in production
- [ ] Security headers are set
- [ ] CSRF protection is implemented
- [ ] Rate limiting is in place
- [ ] Error messages don't expose sensitive information
- [ ] Logs don't contain sensitive data
- [ ] Dependencies are up to date
- [ ] No hardcoded secrets in code

## Incident Response

### Security Incident Workflow

1. **Detection:** Identify the security incident
2. **Assessment:** Determine the scope and impact
3. **Containment:** Limit the damage
4. **Eradication:** Remove the threat
5. **Recovery:** Restore normal operations
6. **Lessons Learned:** Document and improve

### Incident Response Checklist

- [ ] Isolate affected systems
- [ ] Preserve evidence
- [ ] Notify security team
- [ ] Assess impact
- [ ] Contain the incident
- [ ] Remove the threat
- [ ] Restore from backups if needed
- [ ] Monitor for recurrence
- [ ] Document the incident
- [ ] Update security measures
- [ ] Notify affected users if required
- [ ] Conduct post-incident review

## Security Resources

### Tools

- **OWASP ZAP:** Web application security scanner
- **Burp Suite:** Security testing toolkit
- **npm audit:** Dependency vulnerability scanner
- **Snyk:** Continuous security monitoring
- **SonarQube:** Code quality and security analysis

### References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [MDN Web Security](https://developer.mozilla.org/en-US/docs/Web/Security)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Contact

For security concerns, contact: security@agentflow.com
