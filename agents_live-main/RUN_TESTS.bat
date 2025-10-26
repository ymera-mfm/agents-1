@echo off
REM YMERA Database System V5.0.0 - Test Runner
REM This script runs the comprehensive test suite

echo.
echo =========================================================
echo  YMERA DATABASE SYSTEM V5.0.0 - TEST SUITE
echo =========================================================
echo.

REM Set Python path
set PYTHONPATH=%~dp0..

echo Running comprehensive test suite...
echo.

python test_database.py

if errorlevel 1 (
    echo.
    echo =========================================================
    echo  TESTS FAILED - Please review errors above
    echo =========================================================
    echo.
) else (
    echo.
    echo =========================================================
    echo  ALL TESTS PASSED!
    echo =========================================================
    echo.
)

pause
