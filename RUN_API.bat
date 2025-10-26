@echo off
REM YMERA Database System V5.0.0 - API Server
REM This script starts the FastAPI example server

echo.
echo =========================================================
echo  YMERA DATABASE SYSTEM V5.0.0 - API SERVER
echo =========================================================
echo.

REM Set Python path
set PYTHONPATH=%~dp0..

echo Starting FastAPI server...
echo.
echo Server will be available at:
echo   - http://localhost:8000
echo   - API Documentation: http://localhost:8000/api/docs
echo   - Alternative Docs: http://localhost:8000/api/redoc
echo.
echo Press Ctrl+C to stop the server
echo.
echo =========================================================
echo.

python example_api.py

pause
