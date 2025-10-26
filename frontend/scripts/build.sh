#!/bin/bash

# Build script for production deployment
# This script optimizes the build process and includes security checks

echo "🚀 Starting production build..."

# Check Node version
REQUIRED_NODE_VERSION=18
CURRENT_NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)

if [ "$CURRENT_NODE_VERSION" -lt "$REQUIRED_NODE_VERSION" ]; then
  echo "❌ Error: Node.js version $REQUIRED_NODE_VERSION or higher is required"
  exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf dist/

# Install dependencies with clean install
echo "📦 Installing dependencies..."
npm ci --production=false

# Run security audit
echo "🔒 Running security audit..."
npm audit --audit-level=moderate || {
  echo "⚠️  Security vulnerabilities detected. Please review."
  read -p "Continue anyway? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
}

# Run linter
echo "🔍 Running linter..."
npm run lint || {
  echo "❌ Linting failed. Please fix errors before building."
  exit 1
}

# Run tests
echo "🧪 Running tests..."
npm run test:coverage || {
  echo "❌ Tests failed. Please fix errors before building."
  exit 1
}

# Build for production
echo "🏗️  Building for production..."
NODE_ENV=production npm run build || {
  echo "❌ Build failed."
  exit 1
}

# Optimize images and assets
echo "🖼️  Optimizing assets..."
if [ -d "build/static/media" ]; then
  find build/static/media -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" | while read img; do
    if command -v optipng &> /dev/null; then
      optipng -o7 "$img" 2>/dev/null || true
    fi
  done
fi

# Generate build report
echo "📊 Generating build report..."
BUILD_SIZE=$(du -sh build/ | cut -f1)
JS_SIZE=$(du -sh build/static/js/ | cut -f1)
CSS_SIZE=$(du -sh build/static/css/ | cut -f1)

echo "
✅ Build completed successfully!

📦 Build Statistics:
  - Total size: $BUILD_SIZE
  - JavaScript: $JS_SIZE
  - CSS: $CSS_SIZE
  - Build directory: $(pwd)/build

🚀 Ready for deployment!
"

# Optional: Run bundle analyzer
if [ "$1" == "--analyze" ]; then
  echo "📈 Running bundle analyzer..."
  npm run analyze:bundle
fi

exit 0
