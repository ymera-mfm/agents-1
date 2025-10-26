#!/bin/bash

# YMERA System Startup Script

set -e

echo "=========================================="
echo "Starting YMERA Multi-Agent AI System"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d postgres redis nats

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo "Checking service health..."
docker-compose ps

# Run database migrations (if any)
echo "Running database setup..."
# alembic upgrade head  # Uncomment when migrations are added

# Start the application
echo ""
echo "=========================================="
echo "Starting YMERA API Server..."
echo "=========================================="
echo ""
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/api/v1/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py
