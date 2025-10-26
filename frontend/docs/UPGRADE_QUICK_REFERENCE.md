# 🚀 System Upgrade Quick Reference

**For quick access to upgrade commands and procedures**

---

## 📊 Current System Status

### Versions Summary
- **Node.js Runtime**: 20.19.5 ✅
- **Docker Node.js**: 18-alpine ⚠️ (Update to 20-alpine)
- **React**: 18.3.1 (Latest: 19.2.0 - HOLD until stable)
- **npm**: 10.8.2 ✅

### Upgrade Priority Matrix

| Priority | Package | Current | Target | Risk |
|----------|---------|---------|--------|------|
| 🔴 HIGH | Node Docker Image | 18-alpine | 20-alpine | LOW |
| 🔴 HIGH | ESLint | 8.57.1 | 9.38.0 | MEDIUM |
| 🟡 MEDIUM | Tailwind CSS | 3.4.18 | 4.1.16 | HIGH |
| 🟡 MEDIUM | React Router | 6.30.1 | 7.9.4 | HIGH |
| 🟡 MEDIUM | Three.js | 0.158.0 | 0.180.0 | HIGH |
| 🟢 LOW | Date-fns | 2.30.0 | 4.1.0 | MEDIUM |
| 🟢 LOW | Minor updates | Various | Latest | LOW |
| ⏸️ HOLD | React | 18.3.1 | 19.2.0 | HIGH |

---

## ⚡ Quick Commands

### Pre-Upgrade Checks
```bash
# Check current versions
node --version
npm --version
npm list --depth=0

# Check outdated packages
npm outdated

# Security audit
npm audit

# Run baseline tests
npm test
npm run build
npm run test:e2e

# Check bundle size
npm run analyze
```

### Phase 1: Low-Risk Updates (Execute First)
```bash
# Update Docker base image
# Edit Dockerfile: FROM node:18-alpine -> FROM node:20-alpine
docker build -t agentflow:test .

# Minor package updates
npm update axios lucide-react clsx postcss autoprefixer prettier @heroicons/react

# Verify
npm test && npm run build
```

### Phase 2: Medium-Risk Updates
```bash
# ESLint 9 upgrade
npm install --save-dev eslint@9 @eslint/js @eslint/eslintrc
# Then migrate .eslintrc.json to eslint.config.js

# Date-fns 4
npm install date-fns@4

# Tailwind Merge
npm install tailwind-merge@3

# Test after each
npm test && npm run lint && npm run build
```

### Phase 3: High-Risk Updates (Careful!)
```bash
# Tailwind CSS 4
npm install tailwindcss@4
# Review and update tailwind.config.js
npm run build

# React Router 7
npm install react-router-dom@7
# Update route configurations
npm test

# Three.js ecosystem (in order)
npm install three@0.180.0
npm install @types/three@0.180.0
npm install @react-three/fiber@9
npm install @react-three/drei@10
# Test 3D components extensively
```

### Rollback Commands
```bash
# Revert last commit
git revert HEAD
git push

# Restore packages
git checkout HEAD~1 -- package.json package-lock.json
npm install

# Docker rollback
docker tag agentflow:current agentflow:rollback
docker-compose down && docker-compose up -d
```

---

## 🧪 Testing Commands

### Unit & Integration Tests
```bash
npm test                          # Run all tests
npm run test:coverage            # With coverage report
npm test -- --watchAll=false     # Single run
```

### E2E Tests
```bash
npm run test:e2e                 # Run Playwright tests
npm run test:e2e:headed         # With browser visible
npm run test:e2e:debug          # Debug mode
```

### Build & Performance
```bash
npm run build                    # Production build
npm run build:prod              # Optimized build
npm run analyze                 # Bundle analysis
npm run performance:test        # Lighthouse test
```

### Linting & Formatting
```bash
npm run lint                     # Check linting
npm run lint:fix                # Auto-fix issues
npm run format:check            # Check formatting
npm run format                  # Auto-format
```

---

## 📋 Phase Execution Checklist

### Before Starting Any Phase
```bash
✅ git checkout -b upgrade/phase-X
✅ Document baseline metrics
✅ Backup configuration files
✅ npm test (all passing)
✅ npm run build (successful)
```

### After Each Package Update
```bash
✅ npm test
✅ npm run build
✅ Check console for errors
✅ Visual check in browser
✅ git commit -m "upgrade: package-name vX.X.X -> vY.Y.Y"
```

### End of Each Phase
```bash
✅ npm run test:coverage
✅ npm run test:e2e
✅ npm run lint
✅ npm audit
✅ git push origin upgrade/phase-X
✅ Create pull request
✅ Deploy to staging
✅ Monitor for 24 hours
```

---

## 🔍 Debugging Upgrade Issues

### Build Failures
```bash
# Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build

# Check for peer dependency issues
npm ls

# Verbose build output
npm run build -- --verbose
```

### Test Failures
```bash
# Run tests in isolation
npm test -- --testNamePattern="specific test"

# Update snapshots if needed
npm test -- -u

# Debug mode
node --inspect-brk node_modules/.bin/react-scripts test --runInBand
```

### Linting Issues
```bash
# Check specific files
npx eslint src/path/to/file.js

# Fix auto-fixable issues
npm run lint:fix

# Check ESLint config
npx eslint --print-config src/App.jsx
```

### Type Errors (if using TypeScript types)
```bash
# Check types without @types/react-dom upgrade issues
npm install @types/react@18 @types/react-dom@18

# Clear type cache
rm -rf node_modules/.cache
```

---

## 📊 Metrics to Track

### Before Upgrade
```bash
# Build time
time npm run build

# Bundle sizes
npm run build && ls -lh build/static/js/

# Test count
npm test -- --passWithNoTests --verbose

# Dependencies count
npm list --depth=0 | wc -l
```

### After Upgrade
```bash
# Compare build time (should be similar ±10%)
# Compare bundle size (should not increase >10%)
# Verify all tests still pass
# Check dependency count (should not increase significantly)
```

---

## 🚨 Emergency Procedures

### Critical Production Issue
```bash
# 1. Immediate rollback
git revert HEAD --no-edit
git push origin main

# 2. Redeploy previous version
npm run deploy:production

# 3. Verify rollback
curl -f https://yourdomain.com/health
npm run health:check

# 4. Post-mortem
# - Document what went wrong
# - Update rollback procedures
# - Plan fix strategy
```

### Staging Issues
```bash
# 1. Don't panic - it's staging
# 2. Investigate logs
docker-compose logs -f

# 3. Try fix forward first
# - Identify issue
# - Apply fix
# - Test again

# 4. If can't fix quickly, rollback staging
git reset --hard HEAD~1
npm install
npm run build
```

---

## 📝 Documentation Updates

### After Each Phase
```bash
# Update CHANGELOG.md
- Add entries for upgraded packages
- Note any breaking changes
- Document fixes applied

# Update SYSTEM_UPGRADE_STRATEGY.md
- Mark phase as complete
- Add lessons learned
- Update recommendations

# Update UPGRADE_CHECKLIST.md
- Check off completed items
- Add notes on issues encountered
```

---

## 🔗 Quick Links

- **Full Strategy**: [SYSTEM_UPGRADE_STRATEGY.md](./SYSTEM_UPGRADE_STRATEGY.md)
- **Detailed Checklist**: [UPGRADE_CHECKLIST.md](./UPGRADE_CHECKLIST.md)
- **npm outdated**: `npm outdated`
- **Security Audit**: `npm audit`
- **Package Registry**: https://www.npmjs.com/

---

## 💡 Pro Tips

### Upgrade Best Practices
1. **One major change at a time** - Don't mix multiple major upgrades
2. **Test immediately** - Run tests after each package update
3. **Commit frequently** - Small commits make rollback easier
4. **Read changelogs** - Always review breaking changes first
5. **Update related packages together** - E.g., Three.js ecosystem
6. **Monitor staging** - Watch metrics for 24h before production

### Common Pitfalls to Avoid
- ❌ Upgrading React before ecosystem is ready
- ❌ Skipping tests to "save time"
- ❌ Not checking peer dependencies
- ❌ Ignoring deprecation warnings
- ❌ Upgrading in production directly
- ❌ Not having rollback plan ready

### Time-Savers
```bash
# Alias common commands
alias upgrade-check="npm outdated && npm audit"
alias upgrade-test="npm test && npm run build && npm run lint"
alias upgrade-verify="npm run test:coverage && npm run test:e2e"

# Use them
upgrade-check  # Before starting
upgrade-test   # After each change
upgrade-verify # Before pushing
```

---

## 📞 When to Ask for Help

### Get Help If:
- ❗ Build fails and you can't identify why
- ❗ More than 30% of tests start failing
- ❗ Critical dependency conflicts
- ❗ Performance degrades significantly (>20%)
- ❗ Security vulnerabilities introduced
- ❗ Breaking changes unclear from documentation

### Before Asking:
1. ✅ Check error messages carefully
2. ✅ Search package changelog/issues
3. ✅ Try rollback to verify it's upgrade-related
4. ✅ Document what you've tried
5. ✅ Prepare minimal reproduction if possible

---

## 🎯 Success Indicators

You know the upgrade is successful when:

✅ All tests pass (100%)  
✅ Build completes without warnings  
✅ Bundle size acceptable (<10% increase)  
✅ No console errors in browser  
✅ All pages render correctly  
✅ Performance metrics maintained  
✅ Security audit clean  
✅ Team can work with new versions  
✅ Documentation updated  
✅ Staging stable for 24+ hours  

---

**Quick Reference Version**: 1.0.0  
**Last Updated**: 2025-10-25  
**Use with**: SYSTEM_UPGRADE_STRATEGY.md & UPGRADE_CHECKLIST.md

---

*This is a quick reference only. Always consult the full documentation for comprehensive guidance.*
