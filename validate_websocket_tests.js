#!/usr/bin/env node
/**
 * Validation script for WebSocket load testing infrastructure
 * Checks that all components are properly configured
 */

const fs = require('fs');
const path = require('path');

console.log('='.repeat(60));
console.log('WebSocket Load Testing Infrastructure Validation');
console.log('='.repeat(60));
console.log('');

let allValid = true;
const errors = [];
const warnings = [];

// Check for required files
const requiredFiles = [
    'artillery_websocket.yml',
    'websocket_processor.js',
    'websocket_stress_test.js',
    'run_websocket_test.sh',
    'run_websocket_test.bat',
    'package.json',
    'WEBSOCKET_TESTING_GUIDE.md',
    'WEBSOCKET_TESTING_README.md'
];

console.log('Checking required files...');
for (const file of requiredFiles) {
    if (fs.existsSync(file)) {
        console.log(`  [OK] ${file}`);
    } else {
        console.log(`  [MISSING] ${file}`);
        errors.push(`Missing required file: ${file}`);
        allValid = false;
    }
}
console.log('');

// Check package.json
console.log('Validating package.json...');
try {
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    if (!pkg.dependencies || !pkg.dependencies.ws) {
        warnings.push('ws package not listed in dependencies');
    } else {
        console.log(`  ✓ ws dependency: ${pkg.dependencies.ws}`);
    }
    
    if (!pkg.scripts) {
        warnings.push('No npm scripts defined');
    } else {
        console.log(`  ✓ ${Object.keys(pkg.scripts).length} npm scripts defined`);
    }
} catch (e) {
    errors.push(`Failed to parse package.json: ${e.message}`);
    allValid = false;
}
console.log('');

// Check Node.js modules
console.log('Checking Node.js dependencies...');
try {
    require('ws');
    console.log('  ✓ ws module is available');
} catch (e) {
    errors.push('ws module not installed - run: npm install');
    allValid = false;
}
console.log('');

// Validate JavaScript files
console.log('Validating JavaScript files...');
const jsFiles = ['websocket_stress_test.js', 'websocket_processor.js'];
for (const file of jsFiles) {
    try {
        // Read and check for basic syntax without executing
        const content = fs.readFileSync(file, 'utf8');
        if (content.length > 0 && (content.includes('function') || content.includes('class')) && content.includes('module.exports')) {
            console.log(`  ✓ ${file} - structure valid`);
        } else {
            warnings.push(`${file} may have structural issues`);
        }
    } catch (e) {
        errors.push(`${file} has errors: ${e.message}`);
        allValid = false;
    }
}
console.log('');

// Check YAML file
console.log('Validating Artillery configuration...');
try {
    const yaml = fs.readFileSync('artillery_websocket.yml', 'utf8');
    if (yaml.includes('target:') && yaml.includes('scenarios:')) {
        console.log('  ✓ artillery_websocket.yml - basic structure valid');
    } else {
        warnings.push('artillery_websocket.yml may be malformed');
    }
    
    // Check for required sections
    const requiredSections = ['config', 'phases', 'scenarios', 'processor'];
    for (const section of requiredSections) {
        if (yaml.includes(section + ':')) {
            console.log(`  ✓ Contains ${section} section`);
        } else {
            warnings.push(`artillery_websocket.yml missing ${section} section`);
        }
    }
} catch (e) {
    errors.push(`Failed to read artillery_websocket.yml: ${e.message}`);
    allValid = false;
}
console.log('');

// Check script permissions (Unix only)
if (process.platform !== 'win32') {
    console.log('Checking script permissions...');
    try {
        const stats = fs.statSync('run_websocket_test.sh');
        const isExecutable = (stats.mode & 0o111) !== 0;
        if (isExecutable) {
            console.log('  ✓ run_websocket_test.sh is executable');
        } else {
            warnings.push('run_websocket_test.sh is not executable - run: chmod +x run_websocket_test.sh');
        }
    } catch (e) {
        warnings.push('Could not check script permissions');
    }
    console.log('');
}

// Summary
console.log('='.repeat(60));
console.log('Validation Summary');
console.log('='.repeat(60));

if (errors.length > 0) {
    console.log('\n[ERROR] The following issues were found:');
    errors.forEach(err => console.log(`  - ${err}`));
}

if (warnings.length > 0) {
    console.log('\n[WARNING] The following warnings were found:');
    warnings.forEach(warn => console.log(`  - ${warn}`));
}

if (allValid && errors.length === 0) {
    console.log('\n[SUCCESS] All checks passed!');
    console.log('\nYou can now run WebSocket load tests:');
    console.log('  ./run_websocket_test.sh quick');
    console.log('  node websocket_stress_test.js');
    console.log('\nMake sure you have a YMERA server running on ws://localhost:8000/ws');
    process.exit(0);
} else {
    console.log('\n[FAILED] Validation failed!');
    console.log('Please fix the errors above before running tests.');
    process.exit(1);
}
