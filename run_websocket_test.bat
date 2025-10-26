@echo off
REM WebSocket Load Testing Runner Script for YMERA (Windows)

echo ==========================================
echo YMERA WebSocket Load Testing
echo ==========================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js is not installed
    exit /b 1
)

REM Check if dependencies are installed
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
    echo.
)

REM Default values
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=quick

if not defined WS_URL set WS_URL=ws://localhost:8000/ws

echo Test Type: %TEST_TYPE%
echo Target URL: %WS_URL%
echo.

if "%TEST_TYPE%"=="quick" (
    echo Running quick WebSocket stress test (100 connections, 10 messages)
    set CONNECTIONS=100
    set MESSAGES=10
    node websocket_stress_test.js
) else if "%TEST_TYPE%"=="medium" (
    echo Running medium WebSocket stress test (500 connections, 20 messages)
    set CONNECTIONS=500
    set MESSAGES=20
    node websocket_stress_test.js
) else if "%TEST_TYPE%"=="heavy" (
    echo Running heavy WebSocket stress test (1000 connections, 50 messages)
    set CONNECTIONS=1000
    set MESSAGES=50
    node websocket_stress_test.js
) else if "%TEST_TYPE%"=="artillery-quick" (
    echo Running quick Artillery test (localhost)
    npx artillery run -e localhost artillery_websocket.yml
) else if "%TEST_TYPE%"=="artillery-staging" (
    echo Running full Artillery test (staging)
    npx artillery run -e staging artillery_websocket.yml
) else (
    echo Unknown test type: %TEST_TYPE%
    echo.
    echo Usage: %0 [TEST_TYPE]
    echo.
    echo Available test types:
    echo   quick              - Quick stress test (100 connections, 10 messages)
    echo   medium             - Medium stress test (500 connections, 20 messages)
    echo   heavy              - Heavy stress test (1000 connections, 50 messages)
    echo   artillery-quick    - Quick Artillery test (localhost)
    echo   artillery-staging  - Full Artillery test (staging)
    echo.
    echo Environment variables:
    echo   WS_URL             - WebSocket URL (default: ws://localhost:8000/ws)
    echo   CONNECTIONS        - Number of connections (for stress tests)
    echo   MESSAGES           - Messages per connection (for stress tests)
    exit /b 1
)

echo.
echo Test completed!
