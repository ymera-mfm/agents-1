@echo off
REM YMERA Database System V5.0.0 - Installation Script
REM This script installs all required dependencies

echo.
echo =========================================================
echo  YMERA DATABASE SYSTEM V5.0.0 - INSTALLATION
echo =========================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from python.org
    echo.
    pause
    exit /b 1
)

echo [1/4] Python detected:
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    echo.
    pause
    exit /b 1
)

echo [2/4] pip detected:
pip --version
echo.

REM Upgrade pip
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo [4/4] Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some dependencies
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

echo.
echo =========================================================
echo  INSTALLATION COMPLETE!
echo =========================================================
echo.
echo Next steps:
echo   1. Review START_HERE.md for quick start guide
echo   2. Configure .env file from .env.example
echo   3. Run: python quickstart.py
echo.
echo Optional:
echo   - Run example_setup.py for sample data
echo   - Run test_database.py to verify installation
echo   - Run example_api.py to start API server
echo.
pause
