# System Issue Scanner

## Overview

The **System Issue Scanner** is an automated tool that comprehensively analyzes your codebase to identify common issues across multiple categories including code quality, security, testing, build configuration, and documentation.

## Features

### 🔍 Comprehensive Scanning

The scanner checks for:

- **Code Quality**: Linting errors, code formatting, complexity
- **Security**: Vulnerability scanning, configuration issues, exposed secrets
- **Testing**: Test coverage, test configuration
- **Build**: Build script configuration, dependency issues
- **Configuration**: Missing essential files, configuration problems
- **Documentation**: README completeness, missing sections

### 📊 Detailed Reporting

- Issues categorized by severity (Critical, High, Medium, Low, Info)
- Actionable fixes for each issue
- Prioritized recommendations
- JSON output for automation
- Console-friendly formatting

### 🤖 Automation Ready

- GitHub Actions workflow integration
- Automatic issue creation
- PR comments with scan results
- Scheduled daily scans
- Manual trigger support

## Installation

The scanner is already included in this repository. No additional installation needed.

## Usage

### Manual Execution

Run the scanner manually from the command line:

```bash
# Run the scanner
node scripts/system-issue-scanner.js

# Output will be displayed in console and saved to system-issue-report.json
```

### Via npm Script

Add to your `package.json`:

```json
{
  "scripts": {
    "scan:system": "node scripts/system-issue-scanner.js"
  }
}
```

Then run:

```bash
npm run scan:system
```

### GitHub Actions Integration

The scanner automatically runs:

1. **Daily at 2 AM UTC** - Scheduled scan
2. **On push to main** - After merging changes
3. **On pull requests** - Before merging
4. **Manual trigger** - Via GitHub Actions UI

#### Manual Trigger

1. Go to **Actions** tab in GitHub
2. Select **System Issue Scanner** workflow
3. Click **Run workflow**
4. Choose whether to create an issue with results
5. Click **Run workflow** button

## Output Format

### Console Output

```
================================================================================
📊 SYSTEM ISSUE SCAN REPORT
================================================================================

Scan completed at: 2024-10-24T19:00:00.000Z

📈 SUMMARY
────────────────────────────────────────────────────────────────────────────────
Total Issues Found: 5
  🔴 Critical: 0
  🟠 High:     2
  🟡 Medium:   2
  🔵 Low:      1
  ⚪ Info:     0

🟠 HIGH ISSUES (2)
────────────────────────────────────────────────────────────────────────────────

1. [CODE_QUALITY] 15 linting error(s) found
   Multiple linting violations detected
   💡 Fix: Run "npm run lint:fix" to automatically fix issues

2. [SECURITY] Environment files not properly ignored
   .env file not in .gitignore may expose secrets
   💡 Fix: Add ".env" to .gitignore

...
```

### JSON Output (`system-issue-report.json`)

```json
{
  "timestamp": "2024-10-24T19:00:00.000Z",
  "summary": {
    "totalIssues": 5,
    "criticalCount": 0,
    "highCount": 2,
    "mediumCount": 2,
    "lowCount": 1,
    "infoCount": 0
  },
  "issues": {
    "critical": [],
    "high": [
      {
        "severity": "high",
        "category": "CODE_QUALITY",
        "title": "15 linting error(s) found",
        "description": "Multiple linting violations detected",
        "fix": "Run \"npm run lint:fix\" to automatically fix issues",
        "timestamp": "2024-10-24T19:00:00.000Z"
      }
    ],
    "medium": [...],
    "low": [...],
    "info": [...]
  },
  "recommendations": [
    {
      "priority": "HIGH",
      "action": "Fix high severity issues soon",
      "description": "High severity issues should be resolved in the next sprint"
    }
  ]
}
```

## Issue Severity Levels

### 🔴 Critical

**Requires immediate action** - System-breaking issues or critical security vulnerabilities

Examples:
- Critical security vulnerabilities (CVEs with CVSS >= 9.0)
- Missing essential configuration files (package.json)
- Exposed secrets in version control

### 🟠 High

**Should be addressed soon** - Significant issues that impact security or functionality

Examples:
- High severity security vulnerabilities
- Multiple linting errors
- Configuration exposing sensitive data
- Missing .gitignore entries for secrets

### 🟡 Medium

**Plan for resolution** - Issues that should be scheduled for fixing

Examples:
- Moderate security vulnerabilities
- Low test coverage (<70%)
- Code formatting issues
- Missing documentation sections

### 🔵 Low

**Address when convenient** - Minor issues and improvements

Examples:
- Low severity vulnerabilities
- Code style inconsistencies
- Minor documentation gaps
- Informational warnings

### ⚪ Info

**Informational only** - Not issues, but useful information

Examples:
- Successful checks
- System status
- Recommendations
- Best practice suggestions

## Scanner Checks

### 1. Linting Check

Runs ESLint to detect code quality issues:
- Syntax errors
- Code style violations
- Best practice violations
- Potential bugs

**Fix**: `npm run lint:fix`

### 2. Dependency Vulnerabilities

Runs npm audit to check for known vulnerabilities:
- Critical vulnerabilities
- High severity issues
- Moderate issues
- Low priority issues

**Fix**: `npm audit fix`

### 3. Security Configuration

Checks for security best practices:
- `.env` in `.gitignore`
- Secrets in example files
- Configuration exposure

**Fix**: Manual review and configuration updates

### 4. Test Coverage

Analyzes test suite configuration and coverage:
- Test script existence
- Coverage percentages
- Coverage thresholds

**Fix**: Add tests, improve coverage

### 5. Build Configuration

Verifies build setup:
- Build script existence
- Build tool configuration
- Production readiness

**Fix**: Configure build scripts properly

### 6. Configuration Files

Checks for essential files:
- `.gitignore`
- `package.json`
- `README.md`
- Other required configs

**Fix**: Create missing files

### 7. Documentation

Analyzes documentation quality:
- README.md existence and content
- Essential sections (Installation, Usage)
- Documentation completeness

**Fix**: Improve documentation

### 8. Code Quality Metrics

Checks additional quality metrics:
- Code formatting (Prettier)
- Code complexity
- Code duplication

**Fix**: Run formatters, refactor complex code

## GitHub Actions Workflow

### Workflow Features

- **Automatic Scheduling**: Runs daily at 2 AM UTC
- **PR Integration**: Comments on PRs with scan results
- **Issue Creation**: Automatically creates GitHub issues for problems
- **Artifact Upload**: Saves JSON report for 30 days
- **Failure Handling**: Fails build if critical/high issues found

### Workflow Configuration

Location: `.github/workflows/system-issue-scan.yml`

#### Trigger Events

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:      # Manual trigger
  push:
    branches: [main]      # On push to main
  pull_request:
    branches: [main]      # On PR to main
```

#### Permissions

```yaml
permissions:
  contents: read       # Read repository
  issues: write        # Create issues
  pull-requests: write # Comment on PRs
```

### PR Comments

When running on pull requests, the scanner automatically comments with results:

```
## 🟠 System Issue Scan Results

High severity issues found. Please review.

Summary:
- Total Issues: 3
- 🔴 Critical: 0
- 🟠 High: 2
- 🟡 Medium: 1
- 🔵 Low: 0

📊 View detailed report

---
Automated scan by System Issue Scanner
```

### Automatic Issue Creation

For scheduled or manual runs, creates a GitHub issue using the `system-issue-automated.yml` template with:
- Complete issue categorization
- Prioritized action items
- Links to detailed reports
- Suggested fixes

## Integration with Development Workflow

### Pre-commit Checks

Add to your pre-commit hook:

```bash
#!/bin/bash
npm run scan:system
if [ $? -ne 0 ]; then
  echo "System scan found issues. Fix before committing."
  exit 1
fi
```

### CI/CD Pipeline

Integrate into your CI/CD:

```yaml
- name: System Issue Scan
  run: npm run scan:system
  continue-on-error: true  # Don't block deployment
```

### Local Development

Run before submitting PRs:

```bash
npm run scan:system
# Review issues
# Fix critical and high severity issues
# Commit fixes
```

## Best Practices

### 1. Regular Scanning

- Run scanner before committing code
- Review automated scan results daily
- Address critical/high issues immediately

### 2. Triage Process

1. Review scan results
2. Prioritize by severity
3. Assign to team members
4. Track in project management tool
5. Verify fixes with re-scan

### 3. Continuous Improvement

- Maintain zero critical issues
- Keep high severity issues < 5
- Aim for 80%+ test coverage
- Keep dependencies updated

### 4. Team Workflow

- Daily: Review automated scan issues
- Weekly: Team review of medium issues
- Sprint: Plan fixes for low priority items
- Monthly: Audit scanner configuration

## Troubleshooting

### Scanner Fails to Run

**Problem**: Scanner exits with error

**Solutions**:
1. Check Node.js version (requires 18+)
2. Ensure dependencies installed: `npm install`
3. Verify script has execute permissions
4. Check for syntax errors in scanner script

### No Output Generated

**Problem**: Scanner runs but produces no output

**Solutions**:
1. Check console for error messages
2. Verify npm scripts exist
3. Ensure proper permissions to write files
4. Check if running in correct directory

### False Positives

**Problem**: Scanner reports issues that aren't real problems

**Solutions**:
1. Review the specific check causing false positive
2. Update scanner configuration if needed
3. Add exceptions for known false positives
4. Report false positives for scanner improvement

### GitHub Actions Failures

**Problem**: Workflow fails in GitHub Actions

**Solutions**:
1. Check workflow permissions
2. Verify secrets are configured
3. Review workflow logs for specific errors
4. Ensure repository settings allow workflows

## Customization

### Adding Custom Checks

Add new checks to `scripts/system-issue-scanner.js`:

```javascript
async checkCustomThing() {
  console.log('🔍 Checking custom thing...');
  
  // Your check logic here
  if (problemDetected) {
    this.addIssue('high', 'CUSTOM',
      'Problem detected',
      'Description of the problem',
      'How to fix it'
    );
  }
  
  console.log('✅ Custom check complete');
}
```

Then add to `runAllChecks()`:

```javascript
async runAllChecks() {
  // ... existing checks ...
  await this.checkCustomThing();
  // ...
}
```

### Modifying Severity Thresholds

Edit severity logic in specific check methods:

```javascript
if (coverage < 60) {  // Changed from 70
  this.addIssue('high', 'TESTING',  // Changed from 'medium'
    // ...
  );
}
```

### Adjusting Workflow Schedule

Edit `.github/workflows/system-issue-scan.yml`:

```yaml
schedule:
  - cron: '0 8 * * 1'  # Monday at 8 AM instead of daily
```

## Related Documentation

- [System Analysis Template](.github/ISSUE_TEMPLATE/system-analysis.yml) - Manual system analysis
- [Automated Issue Template](.github/ISSUE_TEMPLATE/system-issue-automated.yml) - Template for automated reports
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute
- [Security Policy](../SECURITY.md) - Security guidelines

## Support

For issues or questions:

1. Check this documentation
2. Review existing GitHub issues
3. Create a new issue with `[system-scanner]` prefix
4. Contact the development team

## License

This tool is part of the project and follows the same license.

---

**Last Updated**: 2024-10-24
**Version**: 1.0.0
**Maintainer**: Development Team
