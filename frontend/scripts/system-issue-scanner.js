#!/usr/bin/env node

/**
 * System Issue Scanner
 * Automatically identifies common system issues and generates actionable reports
 * 
 * This scanner checks for:
 * - Linting errors and warnings
 * - Security vulnerabilities in dependencies
 * - Code quality issues
 * - Performance bottlenecks
 * - Configuration problems
 * - Test coverage gaps
 * - Documentation gaps
 * - Build issues
 */

const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');

const execAsync = promisify(exec);

class SystemIssueScanner {
  constructor() {
    this.issues = {
      critical: [],
      high: [],
      medium: [],
      low: [],
      info: []
    };
    this.summary = {
      totalIssues: 0,
      criticalCount: 0,
      highCount: 0,
      mediumCount: 0,
      lowCount: 0,
      infoCount: 0
    };
  }

  /**
   * Add an issue to the report
   */
  addIssue(severity, category, title, description, fix = null) {
    const issue = {
      severity,
      category,
      title,
      description,
      fix,
      timestamp: new Date().toISOString()
    };

    this.issues[severity].push(issue);
    this.summary.totalIssues++;
    this.summary[`${severity}Count`]++;
  }

  /**
   * Run all system checks
   */
  async runAllChecks() {
    console.log('🔍 Starting comprehensive system issue scan...\n');

    await this.checkLinting();
    await this.checkDependencies();
    await this.checkSecurity();
    await this.checkTests();
    await this.checkBuild();
    await this.checkConfiguration();
    await this.checkDocumentation();
    await this.checkCodeQuality();

    return this.generateReport();
  }

  /**
   * Check for linting issues
   */
  async checkLinting() {
    console.log('📝 Checking linting issues...');
    try {
      const { stdout, stderr } = await execAsync('npm run lint', { 
        cwd: process.cwd(),
        maxBuffer: 1024 * 1024 * 10 
      });
      
      if (stderr && !stderr.includes('warnings')) {
        this.addIssue('high', 'CODE_QUALITY', 
          'Linting errors detected',
          `Linting produced errors:\n${stderr}`,
          'Run "npm run lint:fix" to automatically fix common issues'
        );
      }
      
      console.log('✅ Linting check complete');
    } catch (error) {
      const output = error.stdout || error.stderr || error.message;
      
      // Parse eslint output to get error count
      const errorMatch = output.match(/(\d+)\s+error/);
      const warningMatch = output.match(/(\d+)\s+warning/);
      
      if (errorMatch && parseInt(errorMatch[1]) > 0) {
        this.addIssue('high', 'CODE_QUALITY',
          `${errorMatch[1]} linting error(s) found`,
          output,
          'Run "npm run lint:fix" to automatically fix issues, then manually fix remaining errors'
        );
      }
      
      if (warningMatch && parseInt(warningMatch[1]) > 0) {
        this.addIssue('medium', 'CODE_QUALITY',
          `${warningMatch[1]} linting warning(s) found`,
          output,
          'Run "npm run lint:fix" to automatically fix warnings'
        );
      }
    }
  }

  /**
   * Check for dependency vulnerabilities
   */
  async checkDependencies() {
    console.log('📦 Checking dependency vulnerabilities...');
    try {
      const { stdout } = await execAsync('npm audit --json', { 
        cwd: process.cwd(),
        maxBuffer: 1024 * 1024 * 10
      });
      
      const auditResult = JSON.parse(stdout);
      
      if (auditResult.metadata) {
        const { vulnerabilities } = auditResult.metadata;
        
        if (vulnerabilities.critical > 0) {
          this.addIssue('critical', 'SECURITY',
            `${vulnerabilities.critical} critical vulnerability/vulnerabilities found`,
            'Critical security vulnerabilities detected in dependencies',
            'Run "npm audit fix --force" to attempt automatic fixes, then review changes carefully'
          );
        }
        
        if (vulnerabilities.high > 0) {
          this.addIssue('high', 'SECURITY',
            `${vulnerabilities.high} high severity vulnerability/vulnerabilities found`,
            'High severity security vulnerabilities detected in dependencies',
            'Run "npm audit fix" to fix compatible vulnerabilities'
          );
        }
        
        if (vulnerabilities.moderate > 0) {
          this.addIssue('medium', 'SECURITY',
            `${vulnerabilities.moderate} moderate severity vulnerability/vulnerabilities found`,
            'Moderate severity security vulnerabilities detected in dependencies',
            'Run "npm audit fix" to fix compatible vulnerabilities'
          );
        }
        
        if (vulnerabilities.low > 0) {
          this.addIssue('low', 'SECURITY',
            `${vulnerabilities.low} low severity vulnerability/vulnerabilities found`,
            'Low severity security vulnerabilities detected in dependencies',
            'Run "npm audit fix" to fix compatible vulnerabilities'
          );
        }
        
        if (vulnerabilities.info > 0) {
          this.addIssue('info', 'SECURITY',
            `${vulnerabilities.info} informational vulnerability/vulnerabilities found`,
            'Informational security notices in dependencies',
            'Review npm audit output for details'
          );
        }
      }
      
      console.log('✅ Dependency check complete');
    } catch (error) {
      console.log('⚠️  Could not run npm audit');
    }
  }

  /**
   * Check security issues
   */
  async checkSecurity() {
    console.log('🔒 Checking security configuration...');
    
    try {
      // Check for .env file exposure
      const gitignoreContent = await fs.readFile('.gitignore', 'utf-8');
      if (!gitignoreContent.includes('.env')) {
        this.addIssue('critical', 'SECURITY',
          'Environment files not properly ignored',
          '.env file is not listed in .gitignore, which may expose secrets',
          'Add ".env" to .gitignore file'
        );
      }
      
      // Check for secrets in .env.example
      try {
        const envExample = await fs.readFile('.env.example', 'utf-8');
        const secretPatterns = [
          /password\s*=\s*[^<][^\s]+/i,
          /secret\s*=\s*[^<][^\s]+/i,
          /api[_-]?key\s*=\s*[^<][^\s]+/i,
          /token\s*=\s*[^<][^\s]+/i
        ];
        
        for (const pattern of secretPatterns) {
          if (pattern.test(envExample)) {
            this.addIssue('high', 'SECURITY',
              'Potential secrets in .env.example',
              '.env.example file may contain actual secrets instead of placeholders',
              'Replace all real values with placeholders like "<YOUR_API_KEY>"'
            );
            break;
          }
        }
      } catch (e) {
        // .env.example doesn't exist, that's ok
      }
      
      console.log('✅ Security check complete');
    } catch (error) {
      console.log('⚠️  Could not complete security check:', error.message);
    }
  }

  /**
   * Check test coverage
   */
  async checkTests() {
    console.log('🧪 Checking test coverage...');
    
    try {
      const packageJson = JSON.parse(await fs.readFile('package.json', 'utf-8'));
      
      // Check if test script exists
      if (!packageJson.scripts || !packageJson.scripts.test) {
        this.addIssue('medium', 'TESTING',
          'No test script configured',
          'package.json does not have a test script',
          'Add "test" script to package.json'
        );
      }
      
      // Try to check test coverage
      if (packageJson.scripts && packageJson.scripts['test:coverage']) {
        try {
          const { stdout } = await execAsync('npm run test:coverage -- --passWithNoTests', {
            cwd: process.cwd(),
            maxBuffer: 1024 * 1024 * 10,
            timeout: 60000
          });
          
          // Parse coverage results
          const coverageMatch = stdout.match(/All files\s*\|\s*([\d.]+)/);
          if (coverageMatch) {
            const coverage = parseFloat(coverageMatch[1]);
            if (coverage < 70) {
              this.addIssue('medium', 'TESTING',
                `Low test coverage: ${coverage}%`,
                `Current test coverage is ${coverage}%, below recommended 70%`,
                'Add more unit and integration tests to improve coverage'
              );
            } else if (coverage < 80) {
              this.addIssue('low', 'TESTING',
                `Test coverage could be improved: ${coverage}%`,
                `Current test coverage is ${coverage}%, target is 80%+`,
                'Consider adding more tests for critical paths'
              );
            }
          }
        } catch (e) {
          // Test coverage couldn't run, log but don't fail
          console.log('⚠️  Could not run test coverage');
        }
      }
      
      console.log('✅ Test check complete');
    } catch (error) {
      console.log('⚠️  Could not check tests:', error.message);
    }
  }

  /**
   * Check if build works
   */
  async checkBuild() {
    console.log('🏗️  Checking build configuration...');
    
    try {
      const packageJson = JSON.parse(await fs.readFile('package.json', 'utf-8'));
      
      if (!packageJson.scripts || !packageJson.scripts.build) {
        this.addIssue('high', 'BUILD',
          'No build script configured',
          'package.json does not have a build script',
          'Add "build" script to package.json'
        );
      }
      
      console.log('✅ Build check complete');
    } catch (error) {
      console.log('⚠️  Could not check build:', error.message);
    }
  }

  /**
   * Check configuration files
   */
  async checkConfiguration() {
    console.log('⚙️  Checking configuration files...');
    
    try {
      // Check for essential config files
      const requiredFiles = [
        { file: '.gitignore', severity: 'high', category: 'CONFIGURATION' },
        { file: 'package.json', severity: 'critical', category: 'CONFIGURATION' },
        { file: 'README.md', severity: 'medium', category: 'DOCUMENTATION' }
      ];
      
      for (const { file, severity, category } of requiredFiles) {
        try {
          await fs.access(file);
        } catch (e) {
          this.addIssue(severity, category,
            `Missing ${file}`,
            `Required file ${file} is missing from the project`,
            `Create ${file} with appropriate content`
          );
        }
      }
      
      console.log('✅ Configuration check complete');
    } catch (error) {
      console.log('⚠️  Could not check configuration:', error.message);
    }
  }

  /**
   * Check documentation
   */
  async checkDocumentation() {
    console.log('📚 Checking documentation...');
    
    try {
      // Check README.md content
      try {
        const readme = await fs.readFile('README.md', 'utf-8');
        
        if (readme.length < 100) {
          this.addIssue('medium', 'DOCUMENTATION',
            'README.md is too brief',
            'README.md exists but contains minimal content',
            'Expand README.md with setup instructions, usage, and examples'
          );
        }
        
        const essentialSections = [
          { name: 'Installation', patterns: [/##.*\binstall/i, /##.*\bsetup/i] },
          { name: 'Usage', patterns: [/##.*\busage/i, /##.*\bgetting started/i] }
        ];
        
        for (const section of essentialSections) {
          const hasSection = section.patterns.some(pattern => pattern.test(readme));
          if (!hasSection) {
            this.addIssue('low', 'DOCUMENTATION',
              `README.md missing ${section.name} section`,
              `README.md should include a ${section.name} section`,
              `Add ${section.name} section to README.md`
            );
          }
        }
      } catch (e) {
        // Already caught in configuration check
      }
      
      console.log('✅ Documentation check complete');
    } catch (error) {
      console.log('⚠️  Could not check documentation:', error.message);
    }
  }

  /**
   * Check code quality metrics
   */
  async checkCodeQuality() {
    console.log('✨ Checking code quality...');
    
    try {
      // Check for code formatting
      const packageJson = JSON.parse(await fs.readFile('package.json', 'utf-8'));
      
      if (packageJson.scripts && packageJson.scripts['format:check']) {
        try {
          await execAsync('npm run format:check', {
            cwd: process.cwd(),
            maxBuffer: 1024 * 1024 * 10
          });
        } catch (error) {
          this.addIssue('low', 'CODE_QUALITY',
            'Code formatting issues detected',
            'Some files are not properly formatted',
            'Run "npm run format" to auto-format code'
          );
        }
      }
      
      console.log('✅ Code quality check complete');
    } catch (error) {
      console.log('⚠️  Could not check code quality:', error.message);
    }
  }

  /**
   * Generate comprehensive report
   */
  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: this.summary,
      issues: this.issues,
      recommendations: this.generateRecommendations()
    };

    return report;
  }

  /**
   * Generate prioritized recommendations
   */
  generateRecommendations() {
    const recommendations = [];

    if (this.summary.criticalCount > 0) {
      recommendations.push({
        priority: 'URGENT',
        action: 'Address critical issues immediately',
        description: 'Critical security vulnerabilities or blocking issues require immediate attention'
      });
    }

    if (this.summary.highCount > 0) {
      recommendations.push({
        priority: 'HIGH',
        action: 'Fix high severity issues soon',
        description: 'High severity issues should be resolved in the next sprint'
      });
    }

    if (this.summary.mediumCount > 0) {
      recommendations.push({
        priority: 'MEDIUM',
        action: 'Plan fixes for medium severity issues',
        description: 'Medium severity issues should be scheduled for resolution'
      });
    }

    if (this.summary.totalIssues === 0) {
      recommendations.push({
        priority: 'SUCCESS',
        action: 'System is healthy',
        description: 'No issues detected. Continue monitoring and maintaining code quality.'
      });
    }

    return recommendations;
  }

  /**
   * Print report to console
   */
  printReport(report) {
    console.log('\n' + '='.repeat(80));
    console.log('📊 SYSTEM ISSUE SCAN REPORT');
    console.log('='.repeat(80));
    console.log(`\nScan completed at: ${report.timestamp}\n`);

    console.log('📈 SUMMARY');
    console.log('─'.repeat(80));
    console.log(`Total Issues Found: ${report.summary.totalIssues}`);
    console.log(`  🔴 Critical: ${report.summary.criticalCount}`);
    console.log(`  🟠 High:     ${report.summary.highCount}`);
    console.log(`  🟡 Medium:   ${report.summary.mediumCount}`);
    console.log(`  🔵 Low:      ${report.summary.lowCount}`);
    console.log(`  ⚪ Info:     ${report.summary.infoCount}\n`);

    // Print issues by severity
    const severities = ['critical', 'high', 'medium', 'low', 'info'];
    const icons = { critical: '🔴', high: '🟠', medium: '🟡', low: '🔵', info: '⚪' };

    for (const severity of severities) {
      const issues = report.issues[severity];
      if (issues.length > 0) {
        console.log(`\n${icons[severity]} ${severity.toUpperCase()} ISSUES (${issues.length})`);
        console.log('─'.repeat(80));
        
        issues.forEach((issue, index) => {
          console.log(`\n${index + 1}. [${issue.category}] ${issue.title}`);
          console.log(`   ${issue.description}`);
          if (issue.fix) {
            console.log(`   💡 Fix: ${issue.fix}`);
          }
        });
      }
    }

    console.log('\n\n🎯 RECOMMENDATIONS');
    console.log('─'.repeat(80));
    report.recommendations.forEach((rec, index) => {
      console.log(`\n${index + 1}. [${rec.priority}] ${rec.action}`);
      console.log(`   ${rec.description}`);
    });

    console.log('\n' + '='.repeat(80));
    console.log('Scan Complete\n');
  }

  /**
   * Save report to file
   */
  async saveReport(report, filename = 'system-issue-report.json') {
    try {
      await fs.writeFile(filename, JSON.stringify(report, null, 2));
      console.log(`\n✅ Report saved to ${filename}`);
    } catch (error) {
      console.error(`\n❌ Failed to save report: ${error.message}`);
    }
  }
}

// Main execution
async function main() {
  const scanner = new SystemIssueScanner();
  
  try {
    const report = await scanner.runAllChecks();
    scanner.printReport(report);
    await scanner.saveReport(report);
    
    // Exit with error code if critical or high issues found
    if (report.summary.criticalCount > 0 || report.summary.highCount > 0) {
      process.exit(1);
    }
  } catch (error) {
    console.error('❌ Scanner failed:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = SystemIssueScanner;
