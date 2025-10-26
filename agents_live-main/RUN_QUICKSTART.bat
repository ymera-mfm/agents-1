@echo off
REM YMERA Database System V5.0.0 - Quick Start
REM This script runs the quick start verification

echo.
echo =========================================================
echo  YMERA DATABASE SYSTEM V5.0.0 - QUICK START
echo =========================================================
echo.

REM Set Python path
set PYTHONPATH=%~dp0..

echo Running quick start verification...
echo.

python quickstart.py

if errorlevel 1 (
    echo.
    echo =========================================================
    echo  QUICK START FAILED - Please review errors above
    echo =========================================================
    echo.
    echo Troubleshooting:
    echo   1. Ensure dependencies are installed: run INSTALL.bat
    echo   2. Check Python version: python --version
    echo   3. Review START_HERE.md for help
    echo.
) else (
    echo.
    echo =========================================================
    echo  SUCCESS! Your database system is working!
    echo =========================================================
    echo.
    echo Next steps:
    echo   1. Review START_HERE.md for detailed guide
    echo   2. Run example_setup.py for sample data
    echo   3. Read README.md for complete documentation
    echo.
)

pause
