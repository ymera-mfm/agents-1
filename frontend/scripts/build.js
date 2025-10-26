#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Production build script with optimizations
class ProductionBuilder {
  constructor() {
    this.buildDir = path.join(process.cwd(), 'build');
    this.startTime = Date.now();
  }

  log(message) {
    console.log(`[BUILD] ${message}`);
  }

  error(message) {
    console.error(`[ERROR] ${message}`);
  }

  // Clean previous build
  cleanBuild() {
    this.log('Cleaning previous build...');
    if (fs.existsSync(this.buildDir)) {
      fs.rmSync(this.buildDir, { recursive: true, force: true });
    }
  }

  // Set production environment
  setProductionEnv() {
    this.log('Setting production environment...');
    process.env.NODE_ENV = 'production';
    process.env.GENERATE_SOURCEMAP = 'false';
    process.env.INLINE_RUNTIME_CHUNK = 'false';
  }

  // Run React build
  runReactBuild() {
    this.log('Building React application...');
    try {
      execSync('npm run build', { stdio: 'inherit' });
      this.log('React build completed successfully');
    } catch (error) {
      this.error('React build failed');
      throw error;
    }
  }

  // Analyze bundle size
  analyzeBundleSize() {
    this.log('Analyzing bundle size...');
    try {
      // Generate bundle analysis
      execSync('npx webpack-bundle-analyzer build/static/js/*.js --mode static --report build/bundle-report.html --no-open', { stdio: 'inherit' });
      this.log('Bundle analysis completed - report saved to build/bundle-report.html');
    } catch (error) {
      this.log('Bundle analysis skipped (optional)');
    }
  }

  // Optimize build
  optimizeBuild() {
    this.log('Optimizing build...');
    
    // Create optimized index.html with security headers
    const indexPath = path.join(this.buildDir, 'index.html');
    if (fs.existsSync(indexPath)) {
      let indexContent = fs.readFileSync(indexPath, 'utf8');
      
      // Add security headers meta tags
      const securityHeaders = `
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="X-XSS-Protection" content="1; mode=block">
    <meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
    <meta http-equiv="Permissions-Policy" content="geolocation=(), microphone=(), camera=()">`;
      
      indexContent = indexContent.replace('<head>', `<head>${securityHeaders}`);
      fs.writeFileSync(indexPath, indexContent);
      this.log('Security headers added to index.html');
    }

    // Create .htaccess for Apache servers
    const htaccessContent = `
# Security Headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"

# HTTPS Redirect
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>

# Cache Control
<IfModule mod_expires.c>
    ExpiresActive on
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
    ExpiresByType image/webp "access plus 1 year"
    ExpiresByType font/woff "access plus 1 year"
    ExpiresByType font/woff2 "access plus 1 year"
</IfModule>

# SPA Routing
RewriteEngine On
RewriteBase /
RewriteRule ^index\\.html$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]
`;

    fs.writeFileSync(path.join(this.buildDir, '.htaccess'), htaccessContent);
    this.log('Apache .htaccess file created');

    // Create nginx.conf for Nginx servers
    const nginxContent = `
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration (add your SSL certificate paths)
    # ssl_certificate /path/to/certificate.crt;
    # ssl_certificate_key /path/to/private.key;
    
    root /var/www/agentflow/build;
    index index.html;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()";
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Cache control
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy (if needed)
    location /api/ {
        proxy_pass http://your-api-server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
`;

    fs.writeFileSync(path.join(this.buildDir, 'nginx.conf'), nginxContent);
    this.log('Nginx configuration file created');
  }

  // Generate build info
  generateBuildInfo() {
    this.log('Generating build information...');
    
    const buildInfo = {
      buildTime: new Date().toISOString(),
      buildDuration: Date.now() - this.startTime,
      nodeVersion: process.version,
      environment: 'production',
      version: require('../package.json').version,
      commit: this.getGitCommit(),
      branch: this.getGitBranch()
    };

    fs.writeFileSync(
      path.join(this.buildDir, 'build-info.json'),
      JSON.stringify(buildInfo, null, 2)
    );

    this.log(`Build completed in ${buildInfo.buildDuration}ms`);
    return buildInfo;
  }

  // Get git commit hash
  getGitCommit() {
    try {
      return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
    } catch {
      return 'unknown';
    }
  }

  // Get git branch
  getGitBranch() {
    try {
      return execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
    } catch {
      return 'unknown';
    }
  }

  // Create deployment package
  createDeploymentPackage() {
    this.log('Creating deployment package...');
    
    const deploymentFiles = [
      'build/',
      'package.json',
      'package-lock.json',
      '.env.production',
      'README.md'
    ];

    // Create deployment script
    const deployScript = `#!/bin/bash
# Deployment script for AgentFlow

echo "Starting AgentFlow deployment..."

# Install dependencies
npm ci --only=production

# Copy build files
cp -r build/* /var/www/agentflow/

# Restart web server (adjust for your setup)
# sudo systemctl restart nginx
# sudo systemctl restart apache2

echo "Deployment completed successfully!"
`;

    const deployScriptPath = path.join(this.buildDir, 'deploy.sh');
    // Create the file with the desired mode and then explicitly set the final mode to guarantee it despite umask
    fs.writeFileSync(deployScriptPath, deployScript, { mode: 0o755 });
    fs.chmodSync(deployScriptPath, 0o755);
    
    this.log('Deployment script created');
  }

  // Run complete build process
  async build() {
    try {
      this.log('Starting production build process...');
      
      this.cleanBuild();
      this.setProductionEnv();
      this.runReactBuild();
      this.optimizeBuild();
      this.analyzeBundleSize();
      this.createDeploymentPackage();
      const buildInfo = this.generateBuildInfo();
      
      this.log('✅ Production build completed successfully!');
      this.log(`📦 Build output: ${this.buildDir}`);
      this.log(`⏱️  Build time: ${buildInfo.buildDuration}ms`);
      this.log(`🔍 Bundle analysis: ${path.join(this.buildDir, 'bundle-report.html')}`);
      
      return buildInfo;
    } catch (error) {
      this.error('❌ Production build failed!');
      this.error(error.message);
      process.exit(1);
    }
  }
}

// Run build if called directly
if (require.main === module) {
  const builder = new ProductionBuilder();
  builder.build();
}

module.exports = ProductionBuilder;
