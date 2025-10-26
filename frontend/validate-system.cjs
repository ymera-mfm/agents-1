#!/usr/bin/env node

/**
 * System Validation Script
 * Validates all configuration files and system readiness for production
 */

const fs = require('fs');
const path = require('path');

class SystemValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.success = [];
    this.rootDir = process.cwd();
  }

  log(message, type = 'info') {
    const icons = {
      info: 'ℹ️',
      success: '✅',
      warning: '⚠️',
      error: '❌'
    };
    console.log(`${icons[type]} ${message}`);
  }

  // Check if file exists
  fileExists(filePath) {
    const fullPath = path.join(this.rootDir, filePath);
    const exists = fs.existsSync(fullPath);
    
    if (exists) {
      this.success.push(`Found: ${filePath}`);
    } else {
      this.errors.push(`Missing: ${filePath}`);
    }
    
    return exists;
  }

  // Check directory exists
  dirExists(dirPath) {
    const fullPath = path.join(this.rootDir, dirPath);
    const exists = fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory();
    
    if (exists) {
      this.success.push(`Found directory: ${dirPath}`);
    } else {
      this.errors.push(`Missing directory: ${dirPath}`);
    }
    
    return exists;
  }

  // Validate package.json
  validatePackageJson() {
    this.log('Validating package.json...', 'info');
    
    if (!this.fileExists('package.json')) {
      return false;
    }

    try {
      const pkg = JSON.parse(fs.readFileSync(path.join(this.rootDir, 'package.json'), 'utf8'));
      
      // Check required fields
      const requiredFields = ['name', 'version', 'dependencies', 'scripts'];
      requiredFields.forEach(field => {
        if (!pkg[field]) {
          this.errors.push(`package.json missing required field: ${field}`);
        }
      });

      // Check required dependencies
      const requiredDeps = ['react', 'react-dom', 'react-router-dom'];
      requiredDeps.forEach(dep => {
        if (!pkg.dependencies || !pkg.dependencies[dep]) {
          this.errors.push(`Missing required dependency: ${dep}`);
        }
      });

      // Check required scripts
      const requiredScripts = ['start', 'build', 'test', 'lint'];
      requiredScripts.forEach(script => {
        if (!pkg.scripts || !pkg.scripts[script]) {
          this.warnings.push(`Missing recommended script: ${script}`);
        }
      });

      this.log('package.json validation complete', 'success');
      return true;
    } catch (error) {
      this.errors.push(`Invalid package.json: ${error.message}`);
      return false;
    }
  }

  // Validate configuration files
  validateConfigFiles() {
    this.log('Validating configuration files...', 'info');
    
    const configFiles = [
      'jsconfig.json',
      'tailwind.config.js',
      'postcss.config.js',
      '.eslintrc.json',
      '.prettierrc',
      '.gitignore',
      '.env.example'
    ];

    configFiles.forEach(file => this.fileExists(file));
  }

  // Validate build files
  validateBuildFiles() {
    this.log('Validating build files...', 'info');
    
    const buildFiles = [
      'Dockerfile',
      'Dockerfile.dev',
      'docker-compose.yml',
      'docker-compose.dev.yml',
      'docker-compose.prod.yml'
    ];

    buildFiles.forEach(file => this.fileExists(file));
  }

  // Validate deployment files
  validateDeploymentFiles() {
    this.log('Validating deployment files...', 'info');
    
    const deployFiles = [
      'vercel.json',
      'netlify.toml',
      'nginx/nginx.conf'
    ];

    deployFiles.forEach(file => this.fileExists(file));
  }

  // Validate source structure
  validateSourceStructure() {
    this.log('Validating source structure...', 'info');
    
    const requiredDirs = [
      'src',
      'src/components',
      'src/pages',
      'src/services',
      'src/utils',
      'src/hooks',
      'public'
    ];

    requiredDirs.forEach(dir => this.dirExists(dir));

    const srcFiles = ['src/index.js', 'src/App.js'];
    srcFiles.forEach(file => this.fileExists(file));
  }

  // Validate testing setup
  validateTestingSetup() {
    this.log('Validating testing setup...', 'info');
    
    this.fileExists('jest.config.js');
    this.dirExists('__mocks__');
    this.fileExists('__mocks__/fileMock.js');
    this.fileExists('__mocks__/styleMock.js');
  }

  // Validate CI/CD
  validateCICD() {
    this.log('Validating CI/CD configuration...', 'info');
    
    this.dirExists('.github/workflows');
    this.fileExists('.github/workflows/ci-cd.yml');
  }

  // Validate documentation
  validateDocumentation() {
    this.log('Validating documentation...', 'info');
    
    const docs = [
      'README.md',
      'CHANGELOG.md',
      'CONTRIBUTING.md',
      'SECURITY.md'
    ];

    docs.forEach(doc => this.fileExists(doc));
  }

  // Check node version
  checkNodeVersion() {
    this.log('Checking Node.js version...', 'info');
    
    const version = process.version;
    const major = parseInt(version.slice(1).split('.')[0]);
    
    if (major >= 18) {
      this.success.push(`Node.js version ${version} is compatible`);
      this.log(`Node.js ${version} ✓`, 'success');
    } else {
      this.errors.push(`Node.js version ${version} is too old. Requires >=18.0.0`);
      this.log(`Node.js version too old`, 'error');
    }
  }

  // Print summary
  printSummary() {
    console.log('\n' + '='.repeat(60));
    console.log('VALIDATION SUMMARY');
    console.log('='.repeat(60) + '\n');

    if (this.success.length > 0) {
      this.log(`✅ Success: ${this.success.length} checks passed`, 'success');
    }

    if (this.warnings.length > 0) {
      this.log(`⚠️  Warnings: ${this.warnings.length}`, 'warning');
      this.warnings.forEach(warning => console.log(`   - ${warning}`));
    }

    if (this.errors.length > 0) {
      this.log(`❌ Errors: ${this.errors.length}`, 'error');
      this.errors.forEach(error => console.log(`   - ${error}`));
    }

    console.log('\n' + '='.repeat(60));

    if (this.errors.length === 0) {
      this.log('🎉 System is ready for production!', 'success');
      console.log('='.repeat(60) + '\n');
      return 0;
    } else {
      this.log('❌ System has errors that need to be fixed', 'error');
      console.log('='.repeat(60) + '\n');
      return 1;
    }
  }

  // Run all validations
  async run() {
    console.log('\n🔍 Starting system validation...\n');

    this.checkNodeVersion();
    this.validatePackageJson();
    this.validateConfigFiles();
    this.validateBuildFiles();
    this.validateDeploymentFiles();
    this.validateSourceStructure();
    this.validateTestingSetup();
    this.validateCICD();
    this.validateDocumentation();

    return this.printSummary();
  }
}

// Run validation if called directly
if (require.main === module) {
  const validator = new SystemValidator();
  validator.run().then(exitCode => process.exit(exitCode));
}

module.exports = SystemValidator;
