#!/bin/bash

# Deployment script for production
echo "🚀 Deploying AgentFlow to production..."

# Load environment variables
if [ -f .env.production ]; then
  export $(cat .env.production | grep -v '^#' | xargs)
fi

# Build the application
echo "🏗️  Building application..."
npm run build:prod

# Check if build was successful
if [ ! -d "build" ]; then
  echo "❌ Build failed"
  exit 1
fi

# Deploy based on platform
case "$1" in
  "aws")
    echo "☁️  Deploying to AWS S3..."
    npm run deploy:aws:s3
    ;;
  "vercel")
    echo "▲ Deploying to Vercel..."
    npm run deploy:vercel
    ;;
  "netlify")
    echo "🌐 Deploying to Netlify..."
    npm run deploy:netlify
    ;;
  "docker")
    echo "🐳 Deploying with Docker..."
    npm run deploy:docker
    ;;
  *)
    echo "❌ Unknown deployment platform: $1"
    echo "Usage: ./deploy.sh [aws|vercel|netlify|docker]"
    exit 1
    ;;
esac

echo "✅ Deployment completed successfully!"
