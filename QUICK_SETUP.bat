@echo off
REM YMERA Database System V5 - Quick Setup Script for Windows
REM Installs dependencies and performs initial setup

echo.
echo ============================================================
echo YMERA DATABASE SYSTEM V5 - QUICK SETUP
echo ============================================================
echo.

echo Step 1: Installing Python dependencies...
echo.
pip install sqlalchemy[asyncio]>=2.0.0
pip install asyncpg>=0.29.0
pip install aiosqlite>=0.19.0
pip install structlog>=23.0.0
pip install pydantic>=2.0.0
pip install faker>=20.0.0
pip install psutil>=5.9.0
pip install python-dotenv>=1.0.0

echo.
echo Step 2: Verifying installations...
echo.
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
python -c "import structlog; print('Structlog: OK')"
python -c "import faker; print('Faker: OK')"
python -c "import pydantic; print('Pydantic: OK')"

echo.
echo Step 3: Setting up database (SQLite for quick start)...
echo.
set DATABASE_URL=sqlite+aiosqlite:///./ymera_enterprise.db

echo.
echo Step 4: Running comprehensive tests...
echo.
python comprehensive_e2e_test.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Setup completed successfully
    echo ============================================================
    echo.
    echo Next steps:
    echo   1. Run migrations: python database\migration_manager.py migrate
    echo   2. Run tests: python test_database.py
    echo   3. Check health: python scripts\database_monitor.py health
    echo   4. Read: PRODUCTION_READINESS_ASSESSMENT.md
    echo.
) else (
    echo.
    echo ============================================================
    echo SETUP FAILED - Please check errors above
    echo ============================================================
    echo.
    echo Troubleshooting:
    echo   1. Ensure Python 3.9+ is installed
    echo   2. Check internet connection for pip
    echo   3. Read: PRODUCTION_READINESS_ASSESSMENT.md
    echo.
)

pause
