#!/usr/bin/env node

/**
 * Build Optimization Script
 * Analyzes and optimizes production builds
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Starting Build Optimization...\n');

// Step 1: Clean previous builds
console.log('🧹 Cleaning previous builds...');
try {
  execSync('rm -rf build', { stdio: 'inherit' });
  console.log('✓ Build directory cleaned\n');
} catch (error) {
  console.error('Failed to clean build directory:', error.message);
}

// Step 2: Build with production optimizations
console.log('🔨 Building with production optimizations...');
try {
  execSync('GENERATE_SOURCEMAP=false npm run build', {
    stdio: 'inherit',
    env: {
      ...process.env,
      NODE_ENV: 'production',
      GENERATE_SOURCEMAP: 'false',
      INLINE_RUNTIME_CHUNK: 'false',
    },
  });
  console.log('✓ Build completed\n');
} catch (error) {
  console.error('Build failed:', error.message);
  process.exit(1);
}

// Step 3: Analyze bundle sizes
console.log('📊 Analyzing bundle sizes...');
const buildDir = path.join(__dirname, '../build/static');

function getDirectorySize(dir) {
  let size = 0;
  try {
    const files = fs.readdirSync(dir);
    files.forEach((file) => {
      const filePath = path.join(dir, file);
      const stats = fs.statSync(filePath);
      if (stats.isDirectory()) {
        size += getDirectorySize(filePath);
      } else {
        size += stats.size;
      }
    });
  } catch (error) {
    // Directory doesn't exist
  }
  return size;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

const jsSize = getDirectorySize(path.join(buildDir, 'js'));
const cssSize = getDirectorySize(path.join(buildDir, 'css'));
const mediaSize = getDirectorySize(path.join(buildDir, 'media'));
const totalSize = jsSize + cssSize + mediaSize;

console.log('\n📦 Bundle Size Report:');
console.log(`   JavaScript: ${formatBytes(jsSize)}`);
console.log(`   CSS:        ${formatBytes(cssSize)}`);
console.log(`   Media:      ${formatBytes(mediaSize)}`);
console.log(`   Total:      ${formatBytes(totalSize)}`);

// Performance targets
const targets = {
  js: 300 * 1024, // 300KB
  css: 50 * 1024, // 50KB
  total: 500 * 1024, // 500KB
};

console.log('\n🎯 Performance Targets:');
console.log(`   JavaScript: ${formatBytes(targets.js)} ${jsSize <= targets.js ? '✓' : '⚠️'}`);
console.log(`   CSS:        ${formatBytes(targets.css)} ${cssSize <= targets.css ? '✓' : '⚠️'}`);
console.log(`   Total:      ${formatBytes(targets.total)} ${totalSize <= targets.total ? '✓' : '⚠️'}`);

// Step 4: List largest files
console.log('\n📁 Largest Files:');
const jsDir = path.join(buildDir, 'js');
try {
  const jsFiles = fs.readdirSync(jsDir);
  const fileSizes = jsFiles
    .map((file) => ({
      name: file,
      size: fs.statSync(path.join(jsDir, file)).size,
    }))
    .sort((a, b) => b.size - a.size)
    .slice(0, 10);

  fileSizes.forEach((file, index) => {
    console.log(`   ${index + 1}. ${file.name.padEnd(40)} ${formatBytes(file.size)}`);
  });
} catch (error) {
  console.log('   No JavaScript files found');
}

// Step 5: Generate optimization recommendations
console.log('\n💡 Optimization Recommendations:');
const recommendations = [];

if (jsSize > targets.js) {
  recommendations.push('- Implement code splitting for route-based chunks');
  recommendations.push('- Lazy load heavy libraries (Three.js, Framer Motion)');
  recommendations.push('- Use dynamic imports for conditional features');
}

if (totalSize > targets.total) {
  recommendations.push('- Enable Brotli/Gzip compression on server');
  recommendations.push('- Consider removing unused dependencies');
  recommendations.push('- Optimize third-party library imports');
}

// Check for common optimization opportunities
try {
  const packageJson = require('../package.json');
  const deps = Object.keys(packageJson.dependencies);

  if (deps.includes('moment')) {
    recommendations.push('- Replace moment.js with date-fns (smaller bundle)');
  }
  if (deps.includes('lodash') && !deps.includes('lodash-es')) {
    recommendations.push('- Use lodash-es instead of lodash for better tree shaking');
  }
} catch (error) {
  // Package.json not found
}

if (recommendations.length > 0) {
  recommendations.forEach((rec) => console.log(rec));
} else {
  console.log('   ✓ Build is well optimized!');
}

// Step 6: Calculate score
const jsScore = Math.min(100, Math.round((targets.js / jsSize) * 100));
const totalScore = Math.min(100, Math.round((targets.total / totalSize) * 100));
const finalScore = Math.round((jsScore + totalScore) / 2);

console.log('\n⭐ Optimization Score:');
console.log(`   JavaScript: ${jsScore}/100`);
console.log(`   Total Size: ${totalScore}/100`);
console.log(`   Final:      ${finalScore}/100`);

if (finalScore >= 90) {
  console.log('\n✅ Excellent! Build is highly optimized.');
} else if (finalScore >= 70) {
  console.log('\n✓ Good! Build meets most performance targets.');
} else if (finalScore >= 50) {
  console.log('\n⚠️  Fair. Some optimizations needed.');
} else {
  console.log('\n❌ Poor. Significant optimizations required.');
}

console.log('\n✓ Optimization analysis complete!\n');

// Exit with appropriate code
process.exit(finalScore >= 70 ? 0 : 1);
