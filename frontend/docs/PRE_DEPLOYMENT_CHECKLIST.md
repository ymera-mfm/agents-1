# Pre-Deployment Checklist

## Environment Configuration

### Required Environment Variables
- [ ] `REACT_APP_API_URL` - Production API endpoint
- [ ] `REACT_APP_WS_URL` - WebSocket endpoint
- [ ] `REACT_APP_ENV` - Set to 'production'
- [ ] `REACT_APP_VERSION` - Current version number
- [ ] `REACT_APP_SENTRY_DSN` - Sentry error tracking DSN
- [ ] `REACT_APP_ANALYTICS_ID` - Google Analytics tracking ID
- [ ] `REACT_APP_SENTRY_TRACES_SAMPLE_RATE` - Performance monitoring sample rate

### Infrastructure Checklist
- [ ] All environment variables configured in `.env.production`
- [ ] API endpoints verified and accessible
- [ ] SSL certificates validated and not expiring soon
- [ ] CDN configured (CloudFlare/CloudFront if applicable)
- [ ] Backup and rollback plan documented
- [ ] Team notified of deployment schedule
- [ ] Database backups completed (if applicable)
- [ ] DNS records updated and propagated
- [ ] Monitoring tools configured (Sentry, Analytics)
- [ ] Error tracking enabled and tested

### Security Checklist
- [ ] Security headers configured (CSP, X-Frame-Options, etc.)
- [ ] HTTPS enforced
- [ ] API keys rotated if needed
- [ ] Authentication endpoints secured
- [ ] CORS policies configured correctly
- [ ] Rate limiting enabled on API
- [ ] No secrets in client-side code
- [ ] Security audit passed

### Code Quality Checklist
- [ ] All tests passing (`npm test`)
- [ ] E2E tests passing (`npm run test:e2e`)
- [ ] No linting errors (`npm run lint`)
- [ ] Code formatted (`npm run format:check`)
- [ ] Bundle size acceptable (<500KB gzipped)
- [ ] No security vulnerabilities (`npm audit`)
- [ ] Performance targets met
- [ ] Accessibility standards met

## Build Verification

### Build Process
```bash
# Run full test suite
npm test -- --watchAll=false --coverage

# Run E2E tests
npm run test:e2e

# Lint code
npm run lint

# Build production bundle
npm run build

# Analyze bundle size
npm run analyze
```

### Build Success Criteria
- [ ] Build completes without errors
- [ ] Bundle size within acceptable limits
- [ ] All assets generated correctly
- [ ] Source maps created (or excluded for production)
- [ ] Service worker generated
- [ ] Manifest file present

## Deployment Steps

### 1. Pre-Deployment
```bash
# Create deployment tag
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# Final verification
npm run validate
```

### 2. Deployment Commands

#### Vercel
```bash
vercel --prod
```

#### Netlify
```bash
netlify deploy --prod --dir=build
```

#### AWS S3 + CloudFront
```bash
aws s3 sync build/ s3://your-production-bucket --delete
aws cloudfront create-invalidation --distribution-id PROD_ID --paths "/*"
```

#### Custom Server
```bash
scp -r build/* user@production-server:/var/www/html/
```

### 3. Post-Deployment Verification

#### Immediate Checks (Within 5 minutes)
- [ ] Application loads at production URL
- [ ] Homepage renders correctly
- [ ] Login page accessible
- [ ] No JavaScript errors in console
- [ ] All static assets loading
- [ ] SSL certificate valid
- [ ] Navbar and logo present
- [ ] Dark theme applied correctly

#### Health Checks
```bash
# Verify application is live
curl -I https://yourdomain.com

# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Test critical endpoints
curl https://yourdomain.com/api/health
```

#### Smoke Tests
- [ ] User can access homepage
- [ ] User can login successfully
- [ ] Dashboard displays after login
- [ ] Navigation works
- [ ] User can logout
- [ ] Mobile view responsive

## Monitoring Setup

### Error Tracking (Sentry)
- [ ] Sentry project created
- [ ] DSN configured in environment
- [ ] Error notifications set up
- [ ] Team members added to project
- [ ] Alert rules configured

### Analytics (Google Analytics)
- [ ] GA property created
- [ ] Tracking ID configured
- [ ] Goals and events configured
- [ ] Team access granted
- [ ] Dashboard created

### Performance Monitoring
- [ ] Web Vitals tracking enabled
- [ ] Performance budgets configured
- [ ] Lighthouse CI set up (optional)
- [ ] Monitoring dashboard accessible

## Rollback Plan

### Quick Rollback Triggers
- Application completely down
- Critical security vulnerability
- Data loss occurring
- Authentication broken for all users
- Error rate > 10%

### Rollback Procedure
```bash
# Vercel/Netlify - rollback in dashboard or CLI
vercel rollback

# Git-based rollback
git revert HEAD
git push origin main

# AWS CloudFront + S3
aws s3 sync s3://backup-bucket/ s3://production-bucket/ --delete
aws cloudfront create-invalidation --distribution-id PROD_ID --paths "/*"
```

## Sign-Off

### Deployment Approval
- [ ] Technical lead approval
- [ ] Product manager approval
- [ ] QA sign-off
- [ ] Security review completed
- [ ] Documentation updated

### Post-Deployment
- [ ] Deployment notification sent to team
- [ ] Status page updated
- [ ] Monitoring alerts verified
- [ ] First 24-hour monitoring planned
- [ ] Retrospective scheduled

---

**Approved by:** _______________  
**Date:** _______________  
**Deployment Time:** _______________  
**Deployed Version:** v1.0.0
