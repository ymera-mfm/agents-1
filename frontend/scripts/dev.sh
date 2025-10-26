#!/bin/bash

# Development server startup script
echo "🚀 Starting AgentFlow development server..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📦 Installing dependencies..."
  npm install
fi

# Start the development server
echo "🌐 Starting development server on port 3000..."
BROWSER=none npm start
