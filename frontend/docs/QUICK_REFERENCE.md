# AgentFlow Frontend - Quick Reference Guide

## 🚀 Quick Start

### Development
```bash
# Install dependencies
npm install

# Start development server
npm start

# Open http://localhost:3000
```

### Production Build
```bash
# Build for production
npm run build:prod

# Serve production build locally
npm run serve
```

## 📋 Common Commands

### Development
| Command | Description |
|---------|-------------|
| `npm start` | Start dev server (port 3000) |
| `npm test` | Run tests in watch mode |
| `npm run lint` | Check code quality |
| `npm run format` | Format all files |
| `npm run validate` | Validate system configuration |

### Production
| Command | Description |
|---------|-------------|
| `npm run build` | Standard production build |
| `npm run build:prod` | Optimized production build |
| `npm run serve` | Serve production build |
| `npm run analyze` | Analyze bundle size |

### Quality Assurance
| Command | Description |
|---------|-------------|
| `npm run test:coverage` | Run tests with coverage |
| `npm run lint:fix` | Auto-fix linting issues |
| `npm run format:check` | Check code formatting |
| `npm run audit:security` | Security vulnerability check |

### Docker
| Command | Description |
|---------|-------------|
| `npm run docker:build` | Build production Docker image |
| `npm run docker:run` | Run production container |
| `npm run docker:compose:up` | Start with docker-compose |
| `npm run docker:compose:dev` | Start dev environment |

### Deployment
| Command | Description |
|---------|-------------|
| `npm run deploy:vercel` | Deploy to Vercel |
| `npm run deploy:netlify` | Deploy to Netlify |
| `npm run deploy:docker` | Deploy with Docker |

## 🔧 Configuration Files

### Environment Variables
- `.env` - Development environment
- `.env.production` - Production environment
- `.env.example` - Template for new environments

**Required Variables:**
```bash
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_WS_URL=wss://ws.yourdomain.com
```

### Build Configuration
- `package.json` - Dependencies and scripts
- `jsconfig.json` - Path aliases and JS config
- `tailwind.config.js` - Tailwind CSS customization
- `postcss.config.js` - PostCSS plugins

### Code Quality
- `.eslintrc.json` - ESLint rules
- `.prettierrc` - Prettier formatting rules
- `jest.config.js` - Jest testing configuration

## 📁 Project Structure

```
agentflow-enhanced/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   │   ├── Dashboard   # Main dashboard
│   │   ├── Login       # Authentication
│   │   ├── Projects    # Project management
│   │   ├── Monitoring  # System monitoring
│   │   ├── Profile     # User profile
│   │   └── Settings    # User settings
│   ├── services/       # API and external services
│   ├── utils/          # Utility functions
│   ├── hooks/          # Custom React hooks
│   ├── context/        # React context providers
│   └── styles/         # Global styles
├── public/             # Static assets
├── scripts/            # Build and deployment scripts
└── config/             # Configuration files
```

## 🎨 Key Features

### Pages Implemented
- ✅ **Dashboard** - Real-time agent monitoring
- ✅ **Login/Auth** - User authentication
- ✅ **Projects** - Project creation and management
- ✅ **Project Builder** - Live project building with 3D visualization
- ✅ **Monitoring** - System health and performance
- ✅ **Profile** - User profile management
- ✅ **Settings** - Application settings
- ✅ **Command Center** - Admin panel
- ✅ **History** - Project and activity history

### Core Features
- 🎨 **Consistent Dark Theme** - Across all pages
- 📱 **Responsive Design** - Mobile, tablet, desktop
- 🌐 **Real-time Updates** - WebSocket integration
- 💬 **Chat System** - Interactive agent communication
- 📁 **File Management** - Upload/download capabilities
- 📊 **Analytics** - Real-time metrics and charts
- 🔐 **Authentication** - Secure user management
- 🎭 **3D Visualization** - Three.js agent representation

## 🔌 API Integration

### Environment Setup
Update your `.env` file with your API endpoints:

```bash
# API Configuration
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_WS_URL=wss://ws.yourdomain.com
REACT_APP_API_TIMEOUT=10000
```

### WebSocket Connection
The app automatically connects to WebSocket for real-time updates:
- Project build status
- Chat messages
- System notifications
- Agent status updates

## 🐳 Docker Deployment

### Development
```bash
# Build and run development container
docker-compose -f docker-compose.dev.yml up

# Access at http://localhost:3000
```

### Production
```bash
# Build production image
docker build -t agentflow:latest .

# Run production container
docker run -p 80:80 agentflow:latest

# Or use docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🚀 Deployment Platforms

### Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
npm run deploy:vercel
```

### Netlify
```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
npm run deploy:netlify
```

### AWS S3
```bash
# Configure AWS credentials first
aws configure

# Deploy
npm run deploy:aws:s3
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- ComponentName.test.js
```

### Coverage Requirements
- Branches: 70%
- Functions: 70%
- Lines: 70%
- Statements: 70%

## 🔒 Security

### Security Headers
All deployments include:
- Content-Security-Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

### Environment Variables
Never commit sensitive data:
- Use `.env` files (gitignored)
- Set environment variables in deployment platform
- Use secrets management for production

## 📊 Performance

### Optimization Features
- Code splitting
- Lazy loading
- Image optimization
- Bundle minification
- Compression (gzip)
- Caching strategies
- Service workers (PWA)

### Performance Monitoring
```bash
# Run Lighthouse audit
npm run performance:test

# Analyze bundle size
npm run analyze
```

## 🐛 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Kill process on port 3000 (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Node modules issues:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

**Build errors:**
```bash
# Clear cache and rebuild
npm run clean
npm run build
```

## 📚 Documentation

- `README.md` - Main documentation
- `DEPLOYMENT.md` - Deployment guide
- `CONTRIBUTING.md` - How to contribute
- `SECURITY.md` - Security policies
- `CHANGELOG.md` - Version history

## 🆘 Support

### Resources
- Documentation: Check `/docs` directory
- Issues: GitHub Issues
- Security: security@agentflow.com

### Logs
```bash
# View Docker logs
docker-compose logs -f

# Export application logs
npm run logs:export
```

## ✅ Pre-Deployment Checklist

- [ ] Update environment variables
- [ ] Run `npm run validate` to check configuration
- [ ] Run `npm run test:coverage` to ensure tests pass
- [ ] Run `npm run lint` to check code quality
- [ ] Run `npm run build:prod` to verify build
- [ ] Update API URLs in `.env.production`
- [ ] Test deployment on staging environment
- [ ] Configure SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

## 🎯 Performance Targets

- Lighthouse Performance: >90
- Lighthouse Accessibility: >90
- Lighthouse Best Practices: >90
- Lighthouse SEO: >90
- First Contentful Paint: <1.5s
- Time to Interactive: <3.5s
- Bundle Size: <500KB (gzipped)

## 📝 Notes

- Node.js 18+ required
- NPM 8+ required
- Modern browsers only (no IE support)
- Uses React 18 features (Concurrent Mode, Suspense)
- Tailwind CSS for styling
- Zustand for state management
- React Query for data fetching

---

**Last Updated:** October 16, 2025  
**Version:** 1.0.0  
**Status:** Production Ready ✅
