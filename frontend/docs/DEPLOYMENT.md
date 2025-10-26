# AgentFlow Deployment Guide

This guide covers various deployment options for the AgentFlow application, from development to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Deployment](#cloud-deployment)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Node.js**: 18.x or higher
- **npm**: 8.x or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: Minimum 1GB free space
- **Network**: Internet connection for dependencies

### Development Tools

- **Git**: For version control
- **Docker**: For containerized deployment (optional)
- **Docker Compose**: For multi-container setups (optional)

## Environment Configuration

### Environment Variables

Create appropriate `.env` files based on your deployment environment:

#### Development (`.env`)
```bash
NODE_ENV=development
REACT_APP_VERSION=1.0.0
REACT_APP_API_URL=http://localhost:3001
REACT_APP_WS_URL=ws://localhost:3001
REACT_APP_DEBUG_MODE=true
REACT_APP_MOCK_API=true
```

#### Production (`.env.production`)
```bash
NODE_ENV=production
REACT_APP_VERSION=1.0.0
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_WS_URL=wss://ws.yourdomain.com
REACT_APP_DEBUG_MODE=false
REACT_APP_MOCK_API=false
REACT_APP_ANALYTICS_ENABLED=true
REACT_APP_ERROR_REPORTING_ENABLED=true
```

### Security Configuration

Ensure the following security settings are configured:

- **HTTPS**: Always use HTTPS in production
- **CSP**: Content Security Policy headers
- **CORS**: Proper Cross-Origin Resource Sharing configuration
- **Authentication**: Secure authentication mechanisms

## Development Deployment

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd agentflow-enhanced
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

4. **Access the application**:
   - Open http://localhost:3000 in your browser
   - The application will automatically reload on code changes

### Development with Docker

1. **Start development environment**:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **View logs**:
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f
   ```

3. **Stop development environment**:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

## Production Deployment

### Manual Production Build

1. **Install production dependencies**:
   ```bash
   npm ci --only=production
   ```

2. **Build the application**:
   ```bash
   npm run build
   ```

3. **Serve the built application**:
   ```bash
   npm run serve
   ```

### Enhanced Production Build

Use the custom build script for optimized production builds:

```bash
node scripts/build.js
```

This script provides:
- Optimized bundle analysis
- Security header injection
- Server configuration files
- Deployment scripts

### Web Server Configuration

#### Apache Configuration

Copy the generated `.htaccess` file to your web root, or add to your Apache virtual host:

```apache
<VirtualHost *:443>
    ServerName yourdomain.com
    DocumentRoot /var/www/agentflow/build
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
    
    # Security Headers
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    
    # SPA Routing
    RewriteEngine On
    RewriteBase /
    RewriteRule ^index\\.html$ - [L]
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule . /index.html [L]
</VirtualHost>
```

#### Nginx Configuration

Use the generated `nginx.conf` or configure manually:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    root /var/www/agentflow/build;
    index index.html;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Static asset caching
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Docker Deployment

### Production Docker Deployment

1. **Build and start services**:
   ```bash
   docker-compose up -d
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f agentflow-frontend
   ```

3. **Scale services** (if needed):
   ```bash
   docker-compose up -d --scale agentflow-frontend=3
   ```

4. **Update deployment**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

### Docker Swarm Deployment

For high-availability deployments:

1. **Initialize swarm**:
   ```bash
   docker swarm init
   ```

2. **Deploy stack**:
   ```bash
   docker stack deploy -c docker-compose.yml agentflow
   ```

3. **Scale services**:
   ```bash
   docker service scale agentflow_agentflow-frontend=3
   ```

## Cloud Deployment

### AWS Deployment

#### S3 + CloudFront

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Upload to S3**:
   ```bash
   aws s3 sync build/ s3://your-bucket-name --delete
   ```

3. **Configure CloudFront** for SPA routing and caching

#### ECS Deployment

1. **Push Docker image to ECR**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t agentflow .
   docker tag agentflow:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/agentflow:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/agentflow:latest
   ```

2. **Create ECS task definition and service**

### Google Cloud Platform

#### App Engine

1. **Create `app.yaml`**:
   ```yaml
   runtime: nodejs18
   
   handlers:
   - url: /static
     static_dir: build/static
   
   - url: /(.*\\.(json|ico|js))$
     static_files: build/\\1
     upload: build/.*\\.(json|ico|js)$
   
   - url: .*
     static_files: build/index.html
     upload: build/index.html
   ```

2. **Deploy**:
   ```bash
   gcloud app deploy
   ```

### Vercel Deployment

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Deploy**:
   ```bash
   vercel --prod
   ```

### Netlify Deployment

1. **Create `_redirects` file in public folder**:
   ```
   /*    /index.html   200
   ```

2. **Deploy via Git integration or CLI**:
   ```bash
   npm install -g netlify-cli
   netlify deploy --prod --dir=build
   ```

## Monitoring and Maintenance

### Phase 3: Production Deployment & Monitoring

#### Error Tracking & Performance Monitoring

The application includes comprehensive monitoring infrastructure for production environments.

**Sentry Error Tracking:**
- Automatic error capture and reporting
- Performance tracing with configurable sample rates
- Privacy-focused data filtering
- Environment-specific configuration

**Google Analytics:**
- Page view tracking
- Event tracking
- User timing metrics
- Exception tracking

**Web Vitals Monitoring:**
- Core Web Vitals collection (CLS, FID, FCP, LCP, TTFB)
- API endpoint reporting
- Real-time performance metrics

**Configuration:**
```bash
# .env.production
REACT_APP_SENTRY_DSN=your_sentry_dsn
REACT_APP_SENTRY_TRACES_SAMPLE_RATE=0.1
REACT_APP_ANALYTICS_ID=your_analytics_id
REACT_APP_ANALYTICS_ENABLED=true
REACT_APP_PERFORMANCE_MONITORING=true
```

#### Deployment Verification

**Pre-Deployment Checklist:**
See `/docs/PRE_DEPLOYMENT_CHECKLIST.md` for comprehensive checklist including:
- Environment configuration
- Security verification
- Code quality checks
- Infrastructure readiness

**Smoke Tests:**
```bash
# Run smoke tests after deployment
npm run test:smoke:prod
```

**Deployment Verification:**
```bash
# Verify deployment health
npm run deploy:verify:prod
```

#### Monitoring & Alerts

**Alert Configuration:**
Alert thresholds are defined in `/src/config/alerts.config.js`:
- Critical errors: >10/min - Page team immediately
- High error rate: >5% - Slack notification
- Slow response time: >5s - Email alert
- Application downtime: >60s - Page team immediately

**Performance Targets:**
- First Contentful Paint: <1.5s
- Largest Contentful Paint: <2.5s
- Time to Interactive: <3.5s
- Cumulative Layout Shift: <0.1
- First Input Delay: <100ms

**Monitoring Dashboards:**
- Sentry: Error tracking and performance
- Google Analytics: User behavior and traffic
- Custom metrics: Web Vitals and API performance

#### Operations

**Daily Monitoring:**
See `/docs/MONITORING_CHECKLIST.md` for:
- Morning health checks
- Midday monitoring
- End-of-day summaries

**Operations Runbook:**
See `/docs/OPERATIONS_RUNBOOK.md` for:
- Common issues and solutions
- Emergency procedures
- Maintenance tasks
- Contact information

**User Acceptance Testing:**
See `/docs/UAT_GUIDE.md` for:
- UAT session guides
- Test scenarios
- Sign-off procedures

#### Rollback Procedures

**Quick Rollback:**
```bash
# Vercel
vercel rollback

# Netlify
netlify rollback

# Git-based
git revert HEAD
git push origin main
```

**When to Rollback:**
- Application completely down
- Critical security vulnerability
- Error rate >10%
- Data loss occurring
- Authentication broken for all users

See `/docs/OPERATIONS_RUNBOOK.md#rollback-procedure` for detailed steps.

#### First Week Post-Deployment

**Hour 0-1:** Monitor every 5 minutes
- Application uptime
- Error rates
- Login success rate
- Critical paths

**Hours 1-24:** Check every hour
- Error dashboard
- Performance metrics
- User feedback
- Support tickets

**Days 2-7:** Check twice daily
- Daily metrics
- Error trends
- Performance trends
- Feature adoption

**Success Metrics:**
- Uptime > 99.9%
- Error rate < 1%
- Response time < 2s
- User satisfaction > 4/5
- No critical bugs

### Health Checks

The application includes several health check endpoints:

- **Application Health**: `/health`
- **Build Information**: `/build-info.json`
- **Performance Metrics**: Available through monitoring dashboard

### Monitoring Setup

#### Prometheus + Grafana

1. **Start monitoring stack**:
   ```bash
   docker-compose up -d prometheus grafana
   ```

2. **Access Grafana**: http://localhost:3000
   - Username: admin
   - Password: admin123 (change in production)

3. **Import dashboards** from `monitoring/grafana/dashboards/`

#### Application Monitoring

The application includes built-in monitoring features:

- **Performance Monitoring**: Real-time performance metrics
- **Error Tracking**: Automatic error reporting
- **User Analytics**: Usage tracking and analytics
- **Cache Monitoring**: Cache hit rates and performance

### Log Management

#### Log Locations

- **Application Logs**: Available through browser console and logging service
- **Web Server Logs**: `/var/log/nginx/` or `/var/log/apache2/`
- **Container Logs**: `docker logs <container-name>`

#### Log Aggregation

For production environments, consider:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd** for log collection
- **Cloud logging services** (AWS CloudWatch, GCP Cloud Logging)

### Backup and Recovery

#### Application Data

- **Configuration Files**: Backup `.env` and configuration files
- **SSL Certificates**: Backup SSL certificates and keys
- **Custom Assets**: Backup any custom assets or configurations

#### Database Backup (if applicable)

```bash
# Redis backup
docker exec agentflow-redis redis-cli BGSAVE

# Copy backup file
docker cp agentflow-redis:/data/dump.rdb ./backup/
```

## Troubleshooting

### Common Issues

#### Build Failures

1. **Clear npm cache**:
   ```bash
   npm cache clean --force
   ```

2. **Delete node_modules and reinstall**:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Check Node.js version**:
   ```bash
   node --version
   npm --version
   ```

#### Runtime Errors

1. **Check browser console** for JavaScript errors
2. **Verify environment variables** are correctly set
3. **Check network connectivity** to API endpoints
4. **Review application logs** for detailed error information

#### Performance Issues

1. **Analyze bundle size**:
   ```bash
   npm run analyze
   ```

2. **Check memory usage** in browser DevTools
3. **Monitor network requests** for slow API calls
4. **Review performance metrics** in monitoring dashboard

#### Docker Issues

1. **Check container logs**:
   ```bash
   docker logs agentflow-frontend
   ```

2. **Verify container health**:
   ```bash
   docker ps
   docker inspect agentflow-frontend
   ```

3. **Rebuild containers**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Support and Maintenance

#### Regular Maintenance Tasks

1. **Update dependencies** regularly:
   ```bash
   npm audit
   npm update
   ```

2. **Monitor security vulnerabilities**:
   ```bash
   npm audit fix
   ```

3. **Review and rotate SSL certificates**

4. **Monitor application performance** and optimize as needed

5. **Backup critical data** and configurations

#### Getting Help

- **Documentation**: Check this deployment guide and application documentation
- **Logs**: Review application and server logs for error details
- **Monitoring**: Use monitoring dashboards to identify issues
- **Community**: Check GitHub issues and community forums

For additional support, please refer to the project documentation or contact the development team.
