@echo off
REM YMERA System Startup Script for Windows

echo ==========================================
echo Starting YMERA Multi-Agent AI System
echo ==========================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo WARNING: Please edit .env with your configuration
)

REM Start Docker services
echo Starting Docker services...
docker-compose up -d postgres redis nats

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 10 /nobreak

REM Check service health
echo Checking service health...
docker-compose ps

echo.
echo ==========================================
echo Starting YMERA API Server...
echo ==========================================
echo.
echo API: http://localhost:8000
echo Docs: http://localhost:8000/api/v1/docs
echo.
echo Press Ctrl+C to stop
echo.

python main.py
