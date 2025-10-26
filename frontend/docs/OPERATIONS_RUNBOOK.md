# Operations Runbook

## Table of Contents
1. [Common Issues & Solutions](#common-issues--solutions)
2. [Monitoring & Alerts](#monitoring--alerts)
3. [Maintenance Tasks](#maintenance-tasks)
4. [Emergency Procedures](#emergency-procedures)
5. [Contact Information](#contact-information)

## Common Issues & Solutions

### Issue 1: High Error Rate
**Symptoms:** Error rate > 5% in Sentry dashboard

**Investigation Steps:**
1. Check Sentry dashboard for error patterns
2. Review recent deployments (last 24 hours)
3. Check API health endpoint
4. Review server logs
5. Check for common error messages

**Resolution:**
- If deployment-related: Initiate rollback procedure
- If API-related: Contact backend team immediately
- If client-side bug: Deploy hotfix following expedited process
- Document issue in incident log

**Commands:**
```bash
# Check application health
curl -I https://yourdomain.com/health

# View recent errors in Sentry (use Sentry dashboard)
# Check deployment status
vercel ls
```

### Issue 2: Slow Performance
**Symptoms:** Page load time > 5 seconds, Core Web Vitals failing

**Investigation Steps:**
1. Check CDN status (CloudFlare/CloudFront)
2. Review bundle size with webpack analyzer
3. Check API response times
4. Monitor server resources
5. Review performance metrics in GA

**Resolution:**
- Clear CDN cache if stale content
- Optimize heavy components
- Add caching where appropriate
- Review and optimize images
- Check for memory leaks

**Commands:**
```bash
# Clear CloudFront cache
aws cloudfront create-invalidation --distribution-id DIST_ID --paths "/*"

# Analyze bundle size
npm run analyze

# Run Lighthouse performance test
lighthouse https://yourdomain.com --output=html
```

### Issue 3: Authentication Failures
**Symptoms:** Users unable to login, 401/403 errors

**Investigation Steps:**
1. Check auth API status
2. Review token configuration
3. Verify JWT token expiration settings
4. Check cookie/localStorage functionality
5. Verify CORS settings
6. Review session timeout configuration

**Resolution:**
- Verify API endpoints are responding
- Check auth service status with backend team
- Review environment variables
- Verify SSL certificates
- Check for browser-specific issues

**Commands:**
```bash
# Test auth endpoint
curl -X POST https://api.yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Check CORS headers
curl -I -H "Origin: https://yourdomain.com" https://api.yourdomain.com
```

### Issue 4: 404 Errors / Routing Issues
**Symptoms:** Direct URL access returns 404

**Investigation Steps:**
1. Check server configuration (nginx/Apache)
2. Verify SPA routing is configured
3. Check .htaccess or nginx.conf
4. Review build output
5. Verify deployment completed successfully

**Resolution:**
- Ensure server is configured for SPA routing
- Update nginx.conf or .htaccess
- Redeploy if necessary
- Clear CDN cache

**Nginx Configuration:**
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### Issue 5: Build Failures
**Symptoms:** Deployment fails during build

**Investigation Steps:**
1. Check build logs
2. Verify dependencies installed
3. Check environment variables
4. Review recent code changes
5. Check Node.js version compatibility

**Resolution:**
```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Verify Node version
node --version  # Should be 18.x or higher

# Run build locally
npm run build
```

### Issue 6: Memory Leaks / High Memory Usage
**Symptoms:** Application becomes slow over time, browser tab crashes

**Investigation Steps:**
1. Use Chrome DevTools Memory profiler
2. Check for event listener leaks
3. Review component lifecycle
4. Check for unclosed subscriptions
5. Review 3D visualization cleanup

**Resolution:**
- Fix memory leaks in components
- Ensure proper cleanup in useEffect
- Dispose Three.js objects properly
- Implement proper unsubscribe patterns

## Monitoring & Alerts

### Key Metrics to Monitor

#### Application Health
- **Uptime:** Target 99.9%
- **Response Time:** Target <2s
- **Error Rate:** Target <1%
- **API Success Rate:** Target >99%

#### Performance Metrics
- **First Contentful Paint (FCP):** Target <1.5s
- **Largest Contentful Paint (LCP):** Target <2.5s
- **Time to Interactive (TTI):** Target <3.5s
- **Cumulative Layout Shift (CLS):** Target <0.1
- **First Input Delay (FID):** Target <100ms

#### Business Metrics
- Daily active users
- Session duration
- Bounce rate
- Conversion rate
- Feature usage statistics

### Alert Thresholds

| Alert Type | Threshold | Action | Priority |
|-----------|-----------|--------|----------|
| Application Down | 60s | Page team immediately | Critical |
| High Error Rate | >5% | Send Slack notification | High |
| Slow Response | >5s | Send email alert | Medium |
| Memory Usage | >90% | Send Slack notification | High |
| API Failures | >10/min | Page team immediately | Critical |

### Monitoring Dashboards

**Sentry Dashboard:**
- URL: https://sentry.io/organizations/your-org/
- Check for: Error trends, stack traces, affected users

**Google Analytics:**
- URL: https://analytics.google.com/
- Check for: Traffic, user behavior, conversions

**Custom Performance Dashboard:**
- Monitor Web Vitals in real-time
- Track API response times
- View error rates and trends

## Maintenance Tasks

### Daily Tasks
- [ ] Review error logs in Sentry
- [ ] Check performance metrics in GA
- [ ] Monitor uptime status
- [ ] Review user feedback/support tickets
- [ ] Verify scheduled jobs completed (if any)
- [ ] Check monitoring alerts

**Daily Check Script:**
```bash
#!/bin/bash
# daily-check.sh

echo "=== Daily Health Check ==="
echo "Date: $(date)"

# Check application health
echo "Checking application health..."
curl -f https://yourdomain.com/health || echo "⚠️ Health check failed"

# Check SSL expiration
echo "Checking SSL certificate..."
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com 2>/dev/null | openssl x509 -noout -dates

echo "=== Check complete ==="
```

### Weekly Tasks
- [ ] Review weekly metrics summary
- [ ] Analyze performance trends
- [ ] Plan optimization tasks
- [ ] Update dependencies (check for security updates)
- [ ] Review and close resolved support tickets
- [ ] Backup critical configurations
- [ ] Review monitoring alerts and adjust thresholds

**Weekly Maintenance Script:**
```bash
# Check for security updates
npm audit

# Update non-breaking dependencies
npm update

# Run security scan
npm run audit:security
```

### Monthly Tasks
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] User feedback analysis
- [ ] Infrastructure cost review
- [ ] Review and update documentation
- [ ] Rotate API keys/secrets
- [ ] Review SSL certificate expiration
- [ ] Load testing

## Emergency Procedures

### Severity Levels

**Critical (P1):**
- Application completely down
- Data loss occurring
- Security breach
- Payment system broken

**High (P2):**
- Major feature broken
- Error rate >10%
- Performance degraded >50%
- Authentication issues

**Medium (P3):**
- Non-critical feature broken
- Minor performance issues
- UI bugs affecting multiple users

**Low (P4):**
- Minor UI issues
- Edge case bugs
- Non-urgent improvements

### Incident Response Process

1. **Identify & Classify**
   - Determine severity level
   - Document initial symptoms
   - Notify appropriate team members

2. **Communicate**
   - Update status page
   - Notify affected users (if P1/P2)
   - Create incident channel (Slack)

3. **Investigate**
   - Gather logs and metrics
   - Identify root cause
   - Document findings

4. **Resolve**
   - Implement fix or rollback
   - Verify resolution
   - Monitor for recurrence

5. **Post-Mortem**
   - Document incident
   - Identify preventive measures
   - Update runbook

### Rollback Procedure

**When to Rollback:**
- Application completely down
- Critical security vulnerability exposed
- Data loss occurring
- Error rate >10%
- Authentication broken for all users

**Rollback Steps:**

1. **Assess Impact**
   ```bash
   # Check current error rate
   # Review Sentry dashboard
   # Confirm rollback decision with team
   ```

2. **Execute Rollback**
   ```bash
   # Vercel
   vercel rollback
   
   # Netlify
   netlify rollback
   
   # Git-based
   git revert HEAD
   git push origin main
   
   # AWS S3
   aws s3 sync s3://backup-bucket/ s3://production-bucket/ --delete
   aws cloudfront create-invalidation --distribution-id PROD_ID --paths "/*"
   ```

3. **Verify**
   ```bash
   # Check application health
   curl -f https://yourdomain.com/health
   
   # Run smoke tests
   npm run test:e2e -- --grep @smoke
   ```

4. **Communicate**
   - Update team in incident channel
   - Update status page
   - Notify stakeholders

5. **Post-Rollback**
   - Document reason for rollback
   - Plan fix for next deployment
   - Update runbook if needed

## Contact Information

### On-Call Rotation
- **Primary:** [Name] - [Phone] - [Email]
- **Secondary:** [Name] - [Phone] - [Email]
- **Manager:** [Name] - [Phone] - [Email]

### Escalation Path
1. On-call engineer (respond within 15 min)
2. Tech lead (escalate after 30 min)
3. Engineering manager (escalate after 1 hour)

### External Services Support
- **Hosting (Vercel/Netlify):** [Support URL]
- **Sentry:** support@sentry.io
- **CDN Provider:** [Support contact]
- **DNS Provider:** [Support contact]

### Internal Resources
- **Documentation:** [Wiki URL]
- **Slack Channels:**
  - #alerts - Automated alerts
  - #incidents - Incident discussion
  - #engineering - General engineering
- **Ticket System:** [URL]
- **Status Page:** [URL]

---

**Last Updated:** [Date]  
**Maintained By:** DevOps Team  
**Next Review:** [Date + 3 months]
