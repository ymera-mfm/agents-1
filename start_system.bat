@echo off
REM YMERA Platform - System Startup Script (Windows)
REM This script starts the complete YMERA multi-agent AI system

setlocal enabledelayedexpansion

REM Colors using Windows color command (limited support)
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "NC=[0m"

echo.
echo ==========================================
echo YMERA Platform - Startup Script
echo ==========================================
echo.

:MENU
echo Choose startup mode:
echo.
echo   1) Full Local Development (Infrastructure + Application)
echo   2) Application Only (requires external PostgreSQL ^& Redis)
echo   3) Docker Compose Full Stack
echo   4) Infrastructure Only (PostgreSQL, Redis, etc.)
echo   5) Exit
echo.

set /p choice="Enter your choice [1-5]: "

if "%choice%"=="1" goto FULL_LOCAL
if "%choice%"=="2" goto APP_ONLY
if "%choice%"=="3" goto DOCKER_FULL
if "%choice%"=="4" goto INFRASTRUCTURE
if "%choice%"=="5" goto EXIT
goto INVALID_CHOICE

:FULL_LOCAL
echo.
echo ==========================================
echo Starting Full Local Development
echo ==========================================
echo.
call :CHECK_PREREQUISITES
call :SETUP_ENVIRONMENT
call :INSTALL_DEPENDENCIES
call :START_INFRASTRUCTURE
call :INITIALIZE_DATABASE
call :START_APPLICATION
goto END

:APP_ONLY
echo.
echo ==========================================
echo Starting Application Only
echo ==========================================
echo.
call :CHECK_PREREQUISITES
call :SETUP_ENVIRONMENT
call :INSTALL_DEPENDENCIES
echo.
echo %YELLOW%WARNING: Make sure PostgreSQL and Redis are running and configured in .env%NC%
pause
call :INITIALIZE_DATABASE
call :START_APPLICATION
goto END

:DOCKER_FULL
echo.
echo ==========================================
echo Starting Full Stack with Docker Compose
echo ==========================================
echo.
call :CHECK_DOCKER
call :SETUP_ENVIRONMENT
call :START_FULL_DOCKER
goto END

:INFRASTRUCTURE
echo.
echo ==========================================
echo Starting Infrastructure Services
echo ==========================================
echo.
call :CHECK_DOCKER
call :START_INFRASTRUCTURE
goto END

:CHECK_PREREQUISITES
echo.
echo Checking Prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%[PASS] Python installed: !PYTHON_VERSION!%NC%
) else (
    echo %RED%[FAIL] Python is not installed. Please install Python 3.11 or higher.%NC%
    pause
    exit /b 1
)

REM Check pip
pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%[PASS] pip is installed%NC%
) else (
    echo %RED%[FAIL] pip is not installed.%NC%
    pause
    exit /b 1
)

echo.
exit /b 0

:CHECK_DOCKER
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%[PASS] Docker is installed%NC%
) else (
    echo %RED%[FAIL] Docker is not installed.%NC%
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%[PASS] Docker Compose is installed%NC%
) else (
    echo %RED%[FAIL] Docker Compose is not installed.%NC%
    pause
    exit /b 1
)
exit /b 0

:SETUP_ENVIRONMENT
echo.
echo Setting Up Environment...
echo.

if not exist .env (
    echo %YELLOW%[WARN] .env file not found. Creating from .env.example...%NC%
    if exist .env.example (
        copy .env.example .env >nul
        echo %GREEN%[PASS] Created .env file from .env.example%NC%
        echo.
        echo %YELLOW%IMPORTANT: Please edit .env file with your configuration:%NC%
        echo   - Set DATABASE_URL to your PostgreSQL connection string
        echo   - Set REDIS_URL to your Redis connection string
        echo   - Set JWT_SECRET_KEY to a secure random string
        echo.
        pause
    ) else (
        echo %RED%[FAIL] .env.example not found. Please create a .env file manually.%NC%
        pause
        exit /b 1
    )
) else (
    echo %GREEN%[PASS] .env file exists%NC%
)

echo.
exit /b 0

:INSTALL_DEPENDENCIES
echo.
echo Installing Python Dependencies...
echo.

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo %GREEN%[PASS] Virtual environment created%NC%
) else (
    echo %GREEN%[PASS] Virtual environment already exists%NC%
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
echo %GREEN%[PASS] Dependencies installed%NC%

echo.
exit /b 0

:START_INFRASTRUCTURE
echo.
echo Starting Infrastructure Services...
echo.

docker-compose up -d postgres redis
if %errorlevel% equ 0 (
    echo %GREEN%[PASS] Infrastructure services started%NC%
    echo Waiting for services to be healthy...
    timeout /t 5 /nobreak >nul
) else (
    echo %RED%[FAIL] Failed to start infrastructure services%NC%
    pause
    exit /b 1
)

echo.
exit /b 0

:INITIALIZE_DATABASE
echo.
echo Initializing Database...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if alembic is configured
if exist alembic.ini (
    echo Running database migrations...
    python -m alembic upgrade head 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%[PASS] Database migrations completed%NC%
    ) else (
        echo %YELLOW%[WARN] Migrations may have failed. Trying alternative...%NC%
        if exist 001_initial_schema.py (
            python 001_initial_schema.py
            echo %GREEN%[PASS] Database initialized using schema script%NC%
        )
    )
) else (
    echo %YELLOW%[WARN] Alembic not configured. Manual database setup may be required.%NC%
)

echo.
exit /b 0

:START_APPLICATION
echo.
echo ==========================================
echo Starting YMERA Application
echo ==========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Application will be available at:
echo   - Main API: http://localhost:8000
echo   - Health Check: http://localhost:8000/health
echo   - Metrics: http://localhost:8000/metrics
echo   - API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the application
echo.

REM Start the application
python main.py
exit /b 0

:START_FULL_DOCKER
echo.
echo Starting all services with Docker Compose...
echo.

docker-compose up -d
if %errorlevel% equ 0 (
    echo %GREEN%[PASS] All services started%NC%
    echo.
    echo Use 'docker-compose ps' to check service status
    echo Use 'docker-compose logs -f' to view logs
    echo Use 'docker-compose down' to stop all services
    echo.
    echo Application URL: http://localhost:8000
) else (
    echo %RED%[FAIL] Failed to start services%NC%
    pause
    exit /b 1
)
exit /b 0

:INVALID_CHOICE
echo %RED%Invalid choice. Please enter 1-5.%NC%
goto MENU

:EXIT
echo.
echo Goodbye!
exit /b 0

:END
echo.
pause
