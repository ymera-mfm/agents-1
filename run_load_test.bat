@echo off
REM Quick Load Test Runner for YMERA API (Windows)
REM This script starts the API server and runs various load tests

setlocal enabledelayedexpansion

echo =====================================
echo YMERA API Load Testing Runner
echo =====================================
echo.

REM Configuration
if "%API_HOST%"=="" set API_HOST=http://localhost:8000
if "%API_PORT%"=="" set API_PORT=8000

:check_api
echo Checking if API is running...
curl -s "%API_HOST%/api/v1/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo API is running OK
    goto menu
) else (
    echo API is NOT running
    goto start_api
)

:start_api
echo Starting API server on port %API_PORT%...
start /B python main.py > nul 2>&1
timeout /t 5 /nobreak > nul
echo API server started
goto check_api

:menu
echo.
echo Select load test type:
echo 1^) Quick Test ^(10 users, 10 seconds^)
echo 2^) Light Test ^(50 users, 1 minute^)
echo 3^) Medium Test ^(100 users, 2 minutes^)
echo 4^) Heavy Test ^(500 users, 5 minutes^)
echo 5^) Stress Test ^(1000 users, 10 minutes^)
echo 6^) Simple Endpoint Validation
echo 7^) Web UI Mode
echo 8^) Custom Test
echo 9^) Exit
echo.
set /p choice=Enter your choice [1-9]: 

if "%choice%"=="1" goto quick
if "%choice%"=="2" goto light
if "%choice%"=="3" goto medium
if "%choice%"=="4" goto heavy
if "%choice%"=="5" goto stress
if "%choice%"=="6" goto validate
if "%choice%"=="7" goto webui
if "%choice%"=="8" goto custom
if "%choice%"=="9" goto exit
echo Invalid choice. Please select 1-9
goto menu

:quick
call :run_test 10 2 10s quick
goto menu

:light
call :run_test 50 5 1m light
goto menu

:medium
call :run_test 100 10 2m medium
goto menu

:heavy
call :run_test 500 50 5m heavy
goto menu

:stress
call :run_test 1000 100 10m stress
goto menu

:validate
echo.
echo Running Simple Endpoint Validation
echo =====================================
python test_api_simple.py
goto menu

:webui
echo.
echo Starting Locust Web UI
echo =====================================
echo Open http://localhost:8089 in your browser
echo Press Ctrl+C to stop
locust -f locust_api_load_test.py --host=%API_HOST%
goto menu

:custom
echo.
set /p users=Number of users: 
set /p spawn_rate=Spawn rate (users/sec): 
set /p run_time=Run time (e.g., 10s, 1m, 5m): 
call :run_test %users% %spawn_rate% %run_time% custom
goto menu

:run_test
set users=%1
set spawn_rate=%2
set run_time=%3
set test_name=%4
set timestamp=%date:~-4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%

echo.
echo Running %test_name% Test
echo Users: %users%, Spawn Rate: %spawn_rate%, Duration: %run_time%
echo =====================================

locust -f locust_api_load_test.py ^
    --host=%API_HOST% ^
    --users=%users% ^
    --spawn-rate=%spawn_rate% ^
    --run-time=%run_time% ^
    --headless ^
    --html=load_test_%test_name%_%timestamp%.html ^
    --csv=load_test_%test_name%_%timestamp%

echo.
echo Test completed!
echo Reports generated in current directory
goto :eof

:exit
echo Stopping API server...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq main.py" >nul 2>&1
echo Exiting...
exit /b 0
