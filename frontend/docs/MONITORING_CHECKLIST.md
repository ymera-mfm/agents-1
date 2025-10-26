# Monitoring Checklist

## Daily Monitoring Checklist

### Morning Check (Start of Business Day)
**Time:** Within first hour of business day  
**Responsibility:** On-call engineer

- [ ] Check error dashboard for overnight issues
  - Review Sentry for new errors
  - Check error trends vs. previous day
  - Identify any spike in error rates
  
- [ ] Review performance metrics
  - Check Core Web Vitals in GA
  - Review page load times
  - Monitor API response times
  - Check for performance degradation
  
- [ ] Check uptime status
  - Verify application is accessible
  - Check all critical pages loading
  - Monitor uptime percentage (target: 99.9%)
  
- [ ] Review user feedback/support tickets
  - Check new support tickets
  - Review user-reported issues
  - Prioritize urgent issues
  
- [ ] Verify all scheduled jobs completed
  - Check cron jobs logs (if applicable)
  - Verify data synchronization
  - Review backup completion

**Action Items from Morning Check:**
- _____________________
- _____________________

---

### Midday Check
**Time:** Around noon  
**Responsibility:** On-call engineer

- [ ] Monitor real-time traffic
  - Check concurrent users
  - Review traffic patterns
  - Identify any unusual spikes
  
- [ ] Check API response times
  - Monitor average response time
  - Check for slow endpoints
  - Review database query performance
  
- [ ] Review error logs
  - Check for new error patterns
  - Monitor error frequency
  - Verify error alerts working
  
- [ ] Monitor server resources
  - Check CPU usage
  - Monitor memory consumption
  - Review disk space
  - Check network bandwidth

**Action Items from Midday Check:**
- _____________________
- _____________________

---

### End of Day Check
**Time:** Before end of business day  
**Responsibility:** On-call engineer

- [ ] Review daily metrics summary
  - Total users today
  - Error count and rate
  - Performance metrics
  - API call volume
  
- [ ] Document any incidents
  - Create incident reports
  - Update incident log
  - Share with team if needed
  
- [ ] Plan fixes for next day
  - Prioritize issues
  - Create tickets for bugs
  - Schedule maintenance tasks
  
- [ ] Update status page if needed
  - Post any maintenance notices
  - Update incident status
  - Communicate with users

**Daily Summary:**
- Total Errors: _____
- Uptime: _____%
- Avg Response Time: _____ms
- Active Users: _____
- Critical Issues: _____

---

## Weekly Monitoring Review

### Weekly Metrics Review
**Time:** Monday morning  
**Responsibility:** Engineering lead + DevOps

- [ ] Analyze weekly trends
  - Compare with previous week
  - Identify patterns
  - Review growth metrics
  
- [ ] Review performance improvements
  - Check optimization impact
  - Measure performance gains
  - Identify areas for improvement
  
- [ ] Plan optimization tasks
  - Schedule performance work
  - Prioritize optimization
  - Assign tasks to team
  
- [ ] Update documentation
  - Update runbooks
  - Document new issues
  - Share learnings with team

### Weekly Tasks

- [ ] Dependency updates
  ```bash
  npm audit
  npm outdated
  npm update
  ```

- [ ] Security scan
  ```bash
  npm run audit:security
  ```

- [ ] Performance review
  ```bash
  npm run analyze
  lighthouse https://yourdomain.com
  ```

- [ ] Backup verification
  - Verify backups completed
  - Test backup restoration
  - Update backup schedule if needed

- [ ] Certificate expiration check
  ```bash
  openssl s_client -connect yourdomain.com:443 -servername yourdomain.com 2>/dev/null | openssl x509 -noout -dates
  ```

**Weekly Summary:**
- Total Uptime: _____%
- Total Errors: _____
- Avg Response Time: _____ms
- Total Users: _____
- Incidents: _____

---

## Monthly Monitoring Review

### Monthly Health Check
**Time:** First Monday of month  
**Responsibility:** Engineering team

- [ ] Full security audit
  - Review security logs
  - Check for vulnerabilities
  - Update security policies
  - Rotate credentials

- [ ] Performance optimization review
  - Analyze performance trends
  - Implement optimizations
  - Benchmark improvements
  - Set new targets

- [ ] User feedback analysis
  - Review support tickets
  - Analyze user surveys
  - Identify pain points
  - Plan improvements

- [ ] Infrastructure cost review
  - Review cloud costs
  - Optimize resource usage
  - Identify cost savings
  - Update budget forecasts

### Monthly Reporting

Generate monthly report including:

- [ ] Uptime statistics
- [ ] Error rates and trends
- [ ] Performance metrics
- [ ] User growth
- [ ] Feature adoption
- [ ] Incident summary
- [ ] Optimization wins
- [ ] Planned improvements

---

## Key Metrics Monitoring

### Application Health Metrics

| Metric | Target | Current | Status | Alert Threshold |
|--------|--------|---------|--------|-----------------|
| Uptime | 99.9% | _____% | [ ] OK [ ] Alert | <99.5% |
| Error Rate | <1% | _____% | [ ] OK [ ] Alert | >5% |
| Response Time | <2s | _____s | [ ] OK [ ] Alert | >5s |
| API Success | >99% | _____% | [ ] OK [ ] Alert | <95% |

### Performance Metrics (Core Web Vitals)

| Metric | Target | Current | Status | Notes |
|--------|--------|---------|--------|-------|
| FCP | <1.5s | _____s | [ ] Good [ ] Needs Work | |
| LCP | <2.5s | _____s | [ ] Good [ ] Needs Work | |
| TTI | <3.5s | _____s | [ ] Good [ ] Needs Work | |
| CLS | <0.1 | _____ | [ ] Good [ ] Needs Work | |
| FID | <100ms | _____ms | [ ] Good [ ] Needs Work | |

### Business Metrics

| Metric | This Week | Last Week | Change | Notes |
|--------|-----------|-----------|--------|-------|
| Daily Active Users | _____ | _____ | _____% | |
| Session Duration | _____min | _____min | _____% | |
| Bounce Rate | _____% | _____% | _____% | |
| Conversion Rate | _____% | _____% | _____% | |
| Feature Usage | _____ | _____ | _____% | |

---

## Incident Response Monitoring

### Active Incidents

| Incident ID | Severity | Status | Started | Description | Assigned To |
|-------------|----------|--------|---------|-------------|-------------|
| INC-001 | [ ] P1 [ ] P2 [ ] P3 [ ] P4 | [ ] Open [ ] Investigating [ ] Resolved | | | |
| INC-002 | [ ] P1 [ ] P2 [ ] P3 [ ] P4 | [ ] Open [ ] Investigating [ ] Resolved | | | |

### Incident Metrics

- **Total Incidents This Month:** _____
- **Average Resolution Time:** _____
- **P1 Incidents:** _____
- **P2 Incidents:** _____
- **Recurring Issues:** _____

---

## Monitoring Tools Checklist

### Tools Status

- [ ] Sentry
  - Status: [ ] Operational [ ] Degraded [ ] Down
  - Last Check: _____
  - Alerts Working: [ ] Yes [ ] No
  
- [ ] Google Analytics
  - Status: [ ] Operational [ ] Degraded [ ] Down
  - Last Check: _____
  - Data Flowing: [ ] Yes [ ] No
  
- [ ] Uptime Monitor
  - Status: [ ] Operational [ ] Degraded [ ] Down
  - Last Check: _____
  - Alerts Working: [ ] Yes [ ] No
  
- [ ] Performance Monitor
  - Status: [ ] Operational [ ] Degraded [ ] Down
  - Last Check: _____
  - Metrics Collected: [ ] Yes [ ] No

### Alert Channels

- [ ] Email alerts configured and tested
- [ ] Slack notifications working
- [ ] PagerDuty integration active (if applicable)
- [ ] SMS alerts configured (for critical)

---

## Post-Deployment Monitoring

### First Hour After Deployment
**Monitor every 5 minutes:**

- [ ] Application uptime
- [ ] Error rates
- [ ] User login success rate
- [ ] API response times
- [ ] Critical user flows working

**Checklist:**
- [ ] :00 - Check deployed successfully
- [ ] :05 - Verify no error spikes
- [ ] :10 - Test critical paths
- [ ] :15 - Monitor error dashboard
- [ ] :20 - Check performance metrics
- [ ] :30 - Review user sessions
- [ ] :45 - Verify all features working
- [ ] :60 - Final hour-1 check

### First 4-24 Hours (First Day)
**Check every hour:**

- [ ] Error dashboard review
- [ ] Performance metrics check
- [ ] User feedback channels
- [ ] Support ticket monitoring
- [ ] Server resource usage

### Days 2-7 (First Week)
**Check twice daily:**

- [ ] Daily metrics review (morning & evening)
- [ ] Error trend analysis
- [ ] Performance trend analysis
- [ ] User growth tracking
- [ ] Feature adoption monitoring

### Success Metrics for First Week

**Targets to Hit:**

- [ ] Uptime > 99.9%
- [ ] Error rate < 1%
- [ ] Average response time < 2s
- [ ] User satisfaction score > 4/5
- [ ] No critical bugs reported
- [ ] All critical paths functional
- [ ] Mobile usage working smoothly
- [ ] No security incidents
- [ ] Performance targets met
- [ ] User feedback positive

---

## Monitoring Dashboard Links

### Quick Access Links

- **Sentry Dashboard:** https://sentry.io/organizations/[your-org]/issues/
- **Google Analytics:** https://analytics.google.com/
- **Uptime Monitor:** [Your uptime monitor URL]
- **Application:** https://yourdomain.com
- **Staging:** https://staging.yourdomain.com
- **API Health:** https://api.yourdomain.com/health

### Documentation

- **Runbook:** `/docs/OPERATIONS_RUNBOOK.md`
- **Deployment Guide:** `/DEPLOYMENT.md`
- **Emergency Contacts:** `/docs/OPERATIONS_RUNBOOK.md#contact-information`

---

**Last Updated:** [Date]  
**Updated By:** [Name]  
**Next Review:** [Date]
