#!/usr/bin/env node

/**
 * Security Scan Script
 * Runs automated security checks and generates a report
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class SecurityScannerCLI {
  constructor() {
    this.vulnerabilities = [];
    this.warnings = [];
    this.info = [];
  }

  async runScan() {
    console.log('🔍 Starting Security Scan...\n');

    // Run npm audit
    this.runNpmAudit();

    // Check for sensitive files
    this.checkSensitiveFiles();

    // Check for hardcoded secrets
    this.checkHardcodedSecrets();

    // Check package.json security
    this.checkPackageJsonSecurity();

    // Check environment files
    this.checkEnvironmentFiles();

    // Check for security best practices
    this.checkSecurityBestPractices();

    // Generate report
    this.generateReport();
  }

  runNpmAudit() {
    console.log('📦 Running npm audit...');
    try {
      const result = execSync('npm audit --json', { encoding: 'utf-8' });
      const auditData = JSON.parse(result);
      
      if (auditData.metadata.vulnerabilities.total > 0) {
        const meta = auditData.metadata.vulnerabilities;
        this.addWarning(
          'DEPENDENCIES',
          'HIGH',
          `Found ${meta.total} vulnerabilities: ${meta.critical} critical, ${meta.high} high, ${meta.moderate} moderate, ${meta.low} low`,
          'Run "npm audit fix" to fix vulnerabilities'
        );
      } else {
        this.addInfo('DEPENDENCIES', 'No known vulnerabilities found in dependencies ✓');
      }
    } catch (error) {
      // npm audit returns non-zero exit code when vulnerabilities are found
      if (error.stdout) {
        try {
          const auditData = JSON.parse(error.stdout);
          const meta = auditData.metadata.vulnerabilities;
          this.addWarning(
            'DEPENDENCIES',
            'HIGH',
            `Found ${meta.total} vulnerabilities: ${meta.critical} critical, ${meta.high} high, ${meta.moderate} moderate, ${meta.low} low`,
            'Run "npm audit fix" to fix vulnerabilities'
          );
        } catch (parseError) {
          this.addWarning('DEPENDENCIES', 'MEDIUM', 'Failed to parse npm audit results', 'Review npm audit output manually');
        }
      }
    }
    console.log('✓ npm audit completed\n');
  }

  checkSensitiveFiles() {
    console.log('🔐 Checking for sensitive files...');
    
    const sensitiveFiles = [
      '.env',
      '.env.local',
      '.env.production',
      'config/secrets.js',
      'config/keys.js',
      'private.key',
      'certificate.pem'
    ];

    const gitignorePath = path.join(process.cwd(), '.gitignore');
    let gitignoreContent = '';

    if (fs.existsSync(gitignorePath)) {
      gitignoreContent = fs.readFileSync(gitignorePath, 'utf-8');
    }

    sensitiveFiles.forEach(file => {
      const filePath = path.join(process.cwd(), file);
      if (fs.existsSync(filePath)) {
        if (!gitignoreContent.includes(file)) {
          this.addVulnerability(
            'SENSITIVE_FILES',
            'CRITICAL',
            `Sensitive file "${file}" is not in .gitignore`,
            `Add "${file}" to .gitignore to prevent committing sensitive data`
          );
        } else {
          this.addInfo('SENSITIVE_FILES', `"${file}" is properly ignored ✓`);
        }
      }
    });

    console.log('✓ Sensitive files check completed\n');
  }

  checkHardcodedSecrets() {
    console.log('🔑 Checking for hardcoded secrets...');

    const filesToCheck = this.getJavaScriptFiles();
    const secretPatterns = [
      { pattern: /api[_-]?key\s*[:=]\s*["'][a-zA-Z0-9]{20,}["']/gi, type: 'API Key' },
      { pattern: /secret\s*[:=]\s*["'][a-zA-Z0-9]{20,}["']/gi, type: 'Secret' },
      { pattern: /password\s*[:=]\s*["'][^"']+["']/gi, type: 'Password' },
      { pattern: /token\s*[:=]\s*["'][a-zA-Z0-9]{20,}["']/gi, type: 'Token' },
      { pattern: /bearer\s+[a-zA-Z0-9\-._~+/]+=*/gi, type: 'Bearer Token' },
      { pattern: /sk_live_[a-zA-Z0-9]{24,}/gi, type: 'Stripe Secret Key' },
      { pattern: /pk_live_[a-zA-Z0-9]{24,}/gi, type: 'Stripe Public Key' },
      { pattern: /AIza[0-9A-Za-z\\-_]{35}/gi, type: 'Google API Key' },
      { pattern: /AKIA[0-9A-Z]{16}/gi, type: 'AWS Access Key' }
    ];

    let secretsFound = 0;

    filesToCheck.forEach(file => {
      // Skip node_modules, build directories, and test files
      const pathParts = file.split(path.sep);
      const baseName = path.basename(file);
      if (
        pathParts.includes('node_modules') ||
        pathParts.includes('build') ||
        pathParts.includes('dist') ||
        pathParts.includes('__tests__') ||
        baseName.includes('.test.') ||
        baseName.includes('.spec.')
      ) {
        return;
      }

      const content = fs.readFileSync(file, 'utf-8');
      
      secretPatterns.forEach(({ pattern, type }) => {
        const matches = content.match(pattern);
        if (matches) {
          secretsFound += matches.length;
          this.addVulnerability(
            'HARDCODED_SECRETS',
            'CRITICAL',
            `Potential ${type} found in ${file}`,
            'Remove hardcoded secrets and use environment variables instead'
          );
        }
      });
    });

    if (secretsFound === 0) {
      this.addInfo('HARDCODED_SECRETS', 'No obvious hardcoded secrets found ✓');
    }

    console.log('✓ Hardcoded secrets check completed\n');
  }

  checkPackageJsonSecurity() {
    console.log('📋 Checking package.json security...');

    const packageJsonPath = path.join(process.cwd(), 'package.json');
    if (!fs.existsSync(packageJsonPath)) {
      this.addWarning('PACKAGE_JSON', 'MEDIUM', 'package.json not found', 'Ensure package.json exists');
      return;
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));

    // Check for security-related scripts
    if (!packageJson.scripts || !packageJson.scripts['audit:security']) {
      this.addInfo('PACKAGE_JSON', 'Consider adding "audit:security" script to package.json');
    }

    // Check for outdated packages
    try {
      const outdated = execSync('npm outdated --json', { encoding: 'utf-8' });
      if (outdated) {
        const outdatedPackages = JSON.parse(outdated);
        const count = Object.keys(outdatedPackages).length;
        if (count > 0) {
          this.addWarning(
            'PACKAGE_JSON',
            'MEDIUM',
            `Found ${count} outdated packages`,
            'Run "npm update" to update packages'
          );
        }
      }
    } catch (error) {
      // npm outdated returns non-zero exit code when outdated packages exist
      if (error.stdout) {
        try {
          const outdatedPackages = JSON.parse(error.stdout);
          const count = Object.keys(outdatedPackages).length;
          if (count > 0) {
            this.addWarning(
              'PACKAGE_JSON',
              'MEDIUM',
              `Found ${count} outdated packages`,
              'Run "npm update" to update packages'
            );
          }
        } catch (parseError) {
          // Ignore parse errors
        }
      }
    }

    console.log('✓ package.json check completed\n');
  }

  checkEnvironmentFiles() {
    console.log('🌍 Checking environment configuration...');

    const envExamplePath = path.join(process.cwd(), '.env.example');
    const envPath = path.join(process.cwd(), '.env');

    if (!fs.existsSync(envExamplePath)) {
      this.addWarning(
        'ENVIRONMENT',
        'LOW',
        '.env.example file not found',
        'Create .env.example with template environment variables'
      );
    }

    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf-8');
      
      // Check for actual secrets in .env (basic check)
      const lines = envContent.split('\n');
      lines.forEach((line, index) => {
        if (line.includes('=') && !line.startsWith('#')) {
          const [key, value] = line.split('=');
          if (value && value.length > 20 && !value.includes('your-') && !value.includes('example')) {
            // This might be a real secret
            this.addInfo('ENVIRONMENT', `Environment variable "${key.trim()}" appears to contain actual data`);
          }
        }
      });
    }

    console.log('✓ Environment configuration check completed\n');
  }

  checkSecurityBestPractices() {
    console.log('🛡️ Checking security best practices...');

    // Check for HTTPS enforcement
    const nginxPath = path.join(process.cwd(), 'nginx.conf');
    if (fs.existsSync(nginxPath)) {
      const nginxContent = fs.readFileSync(nginxPath, 'utf-8');
      if (!nginxContent.includes('ssl') && !nginxContent.includes('https')) {
        this.addWarning(
          'HTTPS',
          'HIGH',
          'nginx.conf does not appear to enforce HTTPS',
          'Configure SSL/TLS in nginx.conf'
        );
      } else {
        this.addInfo('HTTPS', 'HTTPS configuration found in nginx.conf ✓');
      }
    }

    // Check for security headers in nginx
    if (fs.existsSync(nginxPath)) {
      const nginxContent = fs.readFileSync(nginxPath, 'utf-8');
      const securityHeaders = [
        'X-Frame-Options',
        'X-Content-Type-Options',
        'X-XSS-Protection',
        'Strict-Transport-Security'
      ];

      securityHeaders.forEach(header => {
        if (!nginxContent.includes(header)) {
          this.addWarning(
            'SECURITY_HEADERS',
            'MEDIUM',
            `Security header "${header}" not found in nginx.conf`,
            `Add "${header}" header to nginx.conf`
          );
        }
      });
    }

    // Check for Docker security
    const dockerfilePath = path.join(process.cwd(), 'Dockerfile');
    if (fs.existsSync(dockerfilePath)) {
      const dockerContent = fs.readFileSync(dockerfilePath, 'utf-8');
      
      if (dockerContent.includes('USER root') || !dockerContent.includes('USER ')) {
        this.addWarning(
          'DOCKER',
          'MEDIUM',
          'Dockerfile may be running as root user',
          'Add "USER" directive to run container as non-root user'
        );
      } else {
        this.addInfo('DOCKER', 'Dockerfile uses non-root user ✓');
      }
    }

    console.log('✓ Security best practices check completed\n');
  }

  getJavaScriptFiles() {
    const files = [];
    const srcPath = path.join(process.cwd(), 'src');

    if (!fs.existsSync(srcPath)) {
      return files;
    }

    const walk = (dir) => {
      const items = fs.readdirSync(dir);
      items.forEach(item => {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
          walk(fullPath);
        } else if (item.endsWith('.js') || item.endsWith('.jsx') || item.endsWith('.ts') || item.endsWith('.tsx')) {
          files.push(fullPath);
        }
      });
    };

    walk(srcPath);
    return files;
  }

  addVulnerability(type, severity, description, remediation) {
    this.vulnerabilities.push({ type, severity, description, remediation });
  }

  addWarning(type, severity, description, remediation) {
    this.warnings.push({ type, severity, description, remediation });
  }

  addInfo(type, description) {
    this.info.push({ type, description });
  }

  generateReport() {
    console.log('\n' + '='.repeat(80));
    console.log('🔒 SECURITY SCAN REPORT');
    console.log('='.repeat(80) + '\n');

    const total = this.vulnerabilities.length + this.warnings.length;
    const critical = this.vulnerabilities.filter(v => v.severity === 'CRITICAL').length;
    const high = this.vulnerabilities.filter(v => v.severity === 'HIGH').length + 
                 this.warnings.filter(w => w.severity === 'HIGH').length;
    const medium = this.warnings.filter(w => w.severity === 'MEDIUM').length;
    const low = this.warnings.filter(w => w.severity === 'LOW').length;

    console.log('📊 SUMMARY');
    console.log(`   Total Issues: ${total}`);
    console.log(`   🔴 Critical: ${critical}`);
    console.log(`   🟠 High: ${high}`);
    console.log(`   🟡 Medium: ${medium}`);
    console.log(`   🟢 Low: ${low}\n`);

    if (this.vulnerabilities.length > 0) {
      console.log('🚨 VULNERABILITIES\n');
      this.vulnerabilities.forEach((vuln, index) => {
        console.log(`${index + 1}. [${vuln.severity}] ${vuln.type}`);
        console.log(`   Description: ${vuln.description}`);
        console.log(`   Remediation: ${vuln.remediation}\n`);
      });
    }

    if (this.warnings.length > 0) {
      console.log('⚠️  WARNINGS\n');
      this.warnings.forEach((warn, index) => {
        console.log(`${index + 1}. [${warn.severity}] ${warn.type}`);
        console.log(`   Description: ${warn.description}`);
        console.log(`   Remediation: ${warn.remediation}\n`);
      });
    }

    if (this.info.length > 0) {
      console.log('ℹ️  INFORMATION\n');
      this.info.forEach((info, index) => {
        console.log(`${index + 1}. [${info.type}] ${info.description}`);
      });
      console.log('');
    }

    // Save report to file
    this.saveReportToFile();

    console.log('='.repeat(80));
    
    // Exit with error code if critical or high vulnerabilities found
    if (critical > 0 || high > 0) {
      console.log('\n❌ Security scan found critical or high severity issues!');
      process.exit(1);
    } else {
      console.log('\n✅ Security scan completed successfully!');
      process.exit(0);
    }
  }

  saveReportToFile() {
    const report = {
      scanDate: new Date().toISOString(),
      summary: {
        total: this.vulnerabilities.length + this.warnings.length,
        critical: this.vulnerabilities.filter(v => v.severity === 'CRITICAL').length,
        high: this.vulnerabilities.filter(v => v.severity === 'HIGH').length + 
              this.warnings.filter(w => w.severity === 'HIGH').length,
        medium: this.warnings.filter(w => w.severity === 'MEDIUM').length,
        low: this.warnings.filter(w => w.severity === 'LOW').length
      },
      vulnerabilities: this.vulnerabilities,
      warnings: this.warnings,
      info: this.info
    };

    const reportPath = path.join(process.cwd(), 'security-scan-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`📄 Report saved to: ${reportPath}\n`);
  }
}

// Run scanner
const scanner = new SecurityScannerCLI();
scanner.runScan().catch(error => {
  console.error('❌ Error running security scan:', error);
  process.exit(1);
});
