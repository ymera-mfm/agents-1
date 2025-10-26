#!/usr/bin/env python3
"""
YMERA Platform - Complete Production Deployment Script
Version: 4.0.0
Applies ALL fixes and validates the system
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# ===============================================================================
# CONFIGURATION
# ===============================================================================

BACKEND_ROOT = Path("backend")
API_GATEWAY_DIR = BACKEND_ROOT / "app" / "API_GATEWAY_CORE_ROUTES"
UTILS_DIR = BACKEND_ROOT / "app" / "utils"
BACKUP_DIR = Path("backups") / f"backup_{int(time.time())}"

# ===============================================================================
# COLORED OUTPUT
# ===============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg.center(80)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def print_step(step: int, total: int, msg: str):
    print(f"\n{Colors.BOLD}[{step}/{total}] {msg}{Colors.END}")

# ===============================================================================
# FILE CONTENT TEMPLATES
# ===============================================================================

DATABASE_PY_CONTENT = '''"""
YMERA Enterprise - Database Wrapper Module
Production-Ready Database Connection Management - v4.0
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
import structlog

logger = structlog.get_logger("ymera.database")
Base = declarative_base()

class DatabaseConfig:
    """Database configuration with environment-based settings"""
    
    def __init__(self):
        try:
            from app.CORE_CONFIGURATION.config_settings import get_settings
            settings = get_settings()
            self.database_url = settings.DATABASE_URL
            self.echo = settings.DATABASE_ECHO
            self.pool_size = settings.DATABASE_POOL_SIZE
            self.max_overflow = settings.DATABASE_MAX_OVERFLOW
        except ImportError:
            import os
            self.database_url = os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://postgres:postgres@localhost:5432/ymera"
            )
            self.echo = os.getenv("DATABASE_ECHO", "False").lower() == "true"
            self.pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
            self.max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

class DatabaseManager:
    """Centralized database manager for all API routes"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
        self.logger = logger.bind(component="database_manager")
    
    async def initialize(self) -> None:
        """Initialize database engine and session factory"""
        if self._initialized:
            self.logger.warning("Database already initialized")
            return
        
        try:
            self._engine = create_async_engine(
                self.config.database_url,
                echo=self.config.echo,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            
            self._initialized = True
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize database", error=str(e))
            raise RuntimeError(f"Database initialization failed: {e}") from e
    
    async def dispose(self) -> None:
        """Dispose of database engine and cleanup resources"""
        if self._engine:
            await self._engine.dispose()
            self._initialized = False
            self.logger.info("Database disposed successfully")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
        if not self._initialized:
            await self.initialize()
        
        if not self._session_factory:
            raise RuntimeError("Database session factory not initialized")
        
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            self.logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            if not self._initialized:
                return False
            
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True
                
        except Exception as e:
            self.logger.error("Database health check failed", error=str(e))
            return False

_db_manager = DatabaseManager()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting database session"""
    async with _db_manager.get_session() as session:
        yield session

async def init_database() -> None:
    """Initialize database on application startup"""
    await _db_manager.initialize()

async def close_database() -> None:
    """Close database on application shutdown"""
    await _db_manager.dispose()

__all__ = [
    "Base",
    "DatabaseManager",
    "DatabaseConfig",
    "get_db_session",
    "init_database",
    "close_database",
    "_db_manager",
]
'''

INIT_PY_CONTENT = '''"""
YMERA Enterprise - API Gateway Core Routes Module
Production-Ready Module Initialization - v4.0.0
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from . import database
    
    from .ymera_api_gateway import (
        APIGateway,
        GatewayConfig,
        APIRequest,
        APIResponse,
        GatewayStats,
        LoadBalancer,
        RateLimitManager,
        router as gateway_router
    )
    
    from .ymera_auth_routes import router as auth_router
    from .ymera_agent_routes import router as agent_router
    from .ymera_file_routes import router as file_router
    from .project_routes import router as project_router
    from .websocket_routes import router as websocket_router
    
except ImportError as e:
    import logging
    logging.error(f"CRITICAL: Failed to import API Gateway components: {e}")
    raise ImportError(
        f"Failed to initialize API Gateway Core Routes. "
        f"Missing dependency: {e}"
    ) from e

__version__ = "4.0.0"
__author__ = "YMERA Enterprise Team"
__status__ = "Production"

__all__ = [
    "database",
    "APIGateway",
    "GatewayConfig",
    "APIRequest",
    "APIResponse",
    "GatewayStats",
    "LoadBalancer",
    "RateLimitManager",
    "gateway_router",
    "auth_router",
    "agent_router",
    "file_router",
    "project_router",
    "websocket_router",
    "__version__",
]

def verify_imports() -> Dict[str, Any]:
    """Verify all critical imports are working"""
    import_status = {
        "database": False,
        "api_gateway": False,
        "auth_routes": False,
        "agent_routes": False,
        "file_routes": False,
        "project_routes": False,
        "websocket_routes": False,
    }
    
    try:
        import_status["database"] = hasattr(database, 'get_db_session')
        import_status["api_gateway"] = APIGateway is not None
        import_status["auth_routes"] = auth_router is not None
        import_status["agent_routes"] = agent_router is not None
        import_status["file_routes"] = file_router is not None
        import_status["project_routes"] = project_router is not None
        import_status["websocket_routes"] = websocket_router is not None
    except Exception as e:
        import logging
        logging.error(f"Import verification failed: {e}")
    
    return import_status

_import_status = verify_imports()
_failed_imports = [k for k, v in _import_status.items() if not v]

if _failed_imports:
    import logging
    logging.warning(
        f"API Gateway initialized with missing components: {', '.join(_failed_imports)}"
    )
else:
    import logging
    logging.info("API Gateway Core Routes initialized successfully")
'''

# ===============================================================================
# DEPLOYMENT CLASS
# ===============================================================================

class ProductionDeployment:
    """Complete production deployment orchestration"""
    
    def __init__(self):
        self.fixes_applied = []
        self.warnings = []
        self.errors = []
    
    def create_backup(self) -> bool:
        """Create backup of existing files"""
        print_step(1, 10, "Creating Backup")
        
        try:
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            
            # Backup API Gateway directory
            if API_GATEWAY_DIR.exists():
                backup_path = BACKUP_DIR / "API_GATEWAY_CORE_ROUTES"
                shutil.copytree(API_GATEWAY_DIR, backup_path)
                print_success(f"Backup created: {backup_path}")
            
            self.fixes_applied.append("Backup created")
            return True
            
        except Exception as e:
            print_error(f"Backup failed: {e}")
            self.errors.append(f"Backup: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create required directory structure"""
        print_step(2, 10, "Creating Directory Structure")
        
        try:
            directories = [
                API_GATEWAY_DIR,
                UTILS_DIR,
                BACKEND_ROOT / "app" / "models",
                BACKEND_ROOT / "app" / "SECURITY",
                BACKEND_ROOT / "app" / "CORE_CONFIGURATION",
                BACKEND_ROOT / "app" / "DATABASE_CORE",
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                print_success(f"Created: {directory}")
            
            self.fixes_applied.append("Directory structure created")
            return True
            
        except Exception as e:
            print_error(f"Directory creation failed: {e}")
            self.errors.append(f"Directories: {e}")
            return False
    
    def fix_database_module(self) -> bool:
        """Create/update database.py module"""
        print_step(3, 10, "Fixing Database Module")
        
        try:
            db_file = API_GATEWAY_DIR / "database.py"
            db_file.write_text(DATABASE_PY_CONTENT)
            print_success("database.py created/updated")
            
            self.fixes_applied.append("Database module fixed")
            return True
            
        except Exception as e:
            print_error(f"Database module fix failed: {e}")
            self.errors.append(f"Database module: {e}")
            return False
    
    def fix_init_file(self) -> bool:
        """Create/update __init__.py"""
        print_step(4, 10, "Fixing __init__.py")
        
        try:
            init_file = API_GATEWAY_DIR / "__init__.py"
            init_file.write_text(INIT_PY_CONTENT)
            print_success("__init__.py created/updated")
            
            self.fixes_applied.append("__init__.py fixed")
            return True
            
        except Exception as e:
            print_error(f"__init__.py fix failed: {e}")
            self.errors.append(f"__init__.py: {e}")
            return False
    
    def fix_gateway_routing_encoding(self) -> bool:
        """Fix encoding issues in gateway_routing.py"""
        print_step(5, 10, "Fixing Gateway Routing Encoding")
        
        try:
            gateway_file = API_GATEWAY_DIR / "gateway_routing.py"
            
            if not gateway_file.exists():
                print_warning("gateway_routing.py not found, skipping")
                return True
            
            content = gateway_file.read_text(encoding='utf-8', errors='ignore')
            
            # Replace smart quotes with standard quotes
            replacements = {
                '"': '"',
                '"': '"',
                ''': "'",
                ''': "'",
                '–': '-',
                '—': '-',
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            gateway_file.write_text(content, encoding='utf-8')
            print_success("Encoding issues fixed in gateway_routing.py")
            
            self.fixes_applied.append("Gateway routing encoding fixed")
            return True
            
        except Exception as e:
            print_error(f"Gateway routing fix failed: {e}")
            self.errors.append(f"Gateway routing: {e}")
            return False
    
    def create_utility_files(self) -> bool:
        """Create utility files"""
        print_step(6, 10, "Creating Utility Files")
        
        try:
            # Create __init__.py for utils
            utils_init = UTILS_DIR / "__init__.py"
            utils_init.write_text('"""YMERA Utilities"""')
            
            print_success("Utility files created")
            self.fixes_applied.append("Utility files created")
            return True
            
        except Exception as e:
            print_error(f"Utility creation failed: {e}")
            self.errors.append(f"Utilities: {e}")
            return False
    
    def verify_syntax(self) -> bool:
        """Verify Python syntax"""
        print_step(7, 10, "Verifying Python Syntax")
        
        try:
            files_to_check = [
                API_GATEWAY_DIR / "__init__.py",
                API_GATEWAY_DIR / "database.py",
            ]
            
            all_valid = True
            for file_path in files_to_check:
                if not file_path.exists():
                    continue
                
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(file_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print_success(f"Syntax valid: {file_path.name}")
                else:
                    print_error(f"Syntax error in {file_path.name}")
                    all_valid = False
            
            if all_valid:
                self.fixes_applied.append("Syntax verification passed")
            
            return all_valid
            
        except Exception as e:
            print_error(f"Syntax verification failed: {e}")
            self.errors.append(f"Syntax: {e}")
            return False
    
    def verify_imports(self) -> bool:
        """Verify imports work"""
        print_step(8, 10, "Verifying Imports")
        
        test_script = f"""
import sys
sys.path.insert(0, '{BACKEND_ROOT}')

try:
    from app.API_GATEWAY_CORE_ROUTES import database
    print('✅ Database wrapper imported')
    
    from app.API_GATEWAY_CORE_ROUTES import verify_imports
    status = verify_imports()
    print(f'✅ Import verification: {{status}}')
    
    sys.exit(0)
except ImportError as e:
    print(f'❌ Import failed: {{e}}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
        
        try:
            result = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            
            if result.returncode == 0:
                print_success("Import verification passed")
                self.fixes_applied.append("Import verification passed")
                return True
            else:
                print_error(f"Import verification failed:\n{result.stderr}")
                self.errors.append("Import verification failed")
                return False
                
        except Exception as e:
            print_error(f"Import verification failed: {e}")
            self.errors.append(f"Import verification: {e}")
            return False
    
    def create_env_template(self) -> bool:
        """Create .env template file"""
        print_step(9, 10, "Creating Environment Template")
        
        env_content = """# YMERA Platform - Environment Configuration
# Copy this file to .env and update with your values

# ===============================================================================
# DATABASE CONFIGURATION
# ===============================================================================
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ymera
DATABASE_ECHO=False
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# ===============================================================================
# REDIS CONFIGURATION
# ===============================================================================
REDIS_URL=redis://localhost:6379/0

# ===============================================================================
# API GATEWAY CONFIGURATION
# ===============================================================================
GATEWAY_ENABLED=True
MAX_CONCURRENT_REQUESTS=1000
REQUEST_TIMEOUT=30
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# ===============================================================================
# JWT CONFIGURATION
# ===============================================================================
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===============================================================================
# FILE STORAGE CONFIGURATION
# ===============================================================================
FILE_STORAGE_PATH=/var/ymera/files
TEMP_STORAGE_PATH=/var/ymera/temp
MAX_FILE_SIZE=104857600
MAX_FILES_PER_USER=1000
VIRUS_SCAN_ENABLED=False

# ===============================================================================
# SECURITY CONFIGURATION
# ===============================================================================
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
SECRET_KEY=your-secret-key-change-in-production
CORS_ENABLED=True

# ===============================================================================
# LOGGING CONFIGURATION
# ===============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/ymera/app.log

# ===============================================================================
# SERVICE ENDPOINTS (for load balancing)
# ===============================================================================
AUTH_SERVICE_URL=http://localhost:8001
AGENT_SERVICE_URL=http://localhost:8002
FILE_SERVICE_URL=http://localhost:8003
"""
        
        try:
            env_file = BACKEND_ROOT / ".env.example"
            env_file.write_text(env_content)
            print_success(".env.example created")
            
            self.fixes_applied.append("Environment template created")
            return True
            
        except Exception as e:
            print_error(f"Environment template creation failed: {e}")
            self.errors.append(f"Environment template: {e}")
            return False
    
    def generate_deployment_report(self) -> bool:
        """Generate deployment report"""
        print_step(10, 10, "Generating Deployment Report")
        
        report = f"""
# YMERA Platform - Deployment Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## ✅ Fixes Applied ({len(self.fixes_applied)})
"""
        
        for i, fix in enumerate(self.fixes_applied, 1):
            report += f"{i}. {fix}\n"
        
        if self.warnings:
            report += f"\n## ⚠️ Warnings ({len(self.warnings)})\n"
            for i, warning in enumerate(self.warnings, 1):
                report += f"{i}. {warning}\n"
        
        if self.errors:
            report += f"\n## ❌ Errors ({len(self.errors)})\n"
            for i, error in enumerate(self.errors, 1):
                report += f"{i}. {error}\n"
        
        report += """
## 📋 Next Steps

1. **Review Changes**
   - Check the backup directory for previous versions
   - Review all modified files

2. **Configure Environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your configuration
   ```

3. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run Database Migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

5. **Start Services**
   ```bash
   # Development
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Production
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

6. **Verify Deployment**
   - Test health endpoint: http://localhost:8000/health
   - Test API documentation: http://localhost:8000/docs
   - Run integration tests

7. **Monitor**
   - Check application logs
   - Monitor error rates
   - Watch resource usage

## 🔒 Security Checklist

- [ ] Update all secret keys in .env
- [ ] Configure HTTPS/TLS certificates
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable virus scanning (if needed)
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Enable monitoring/alerting

## 📚 Documentation

- API Documentation: /docs
- Health Check: /health
- Gateway Stats: /gateway/stats
- File Upload: /api/v1/files/upload
- WebSocket: /ws/{connection_type}/{user_id}

## 🆘 Troubleshooting

### Import Errors
If you see import errors, ensure:
- All dependencies are installed
- Python path is correct
- __init__.py files exist in all packages

### Database Connection Issues
- Verify DATABASE_URL is correct
- Ensure database server is running
- Check network connectivity
- Verify credentials

### File Upload Issues
- Check file storage paths exist
- Verify permissions on storage directories
- Check MAX_FILE_SIZE settings
- Review file validation logs

### WebSocket Issues
- Verify WebSocket URL format
- Check CORS settings
- Review connection logs
- Test with wscat or similar tool

## 📞 Support

For issues, check:
- Application logs: /var/log/ymera/
- Error tracking dashboard
- System metrics
- Database logs
"""
        
        try:
            report_file = BACKEND_ROOT / "DEPLOYMENT_REPORT.md"
            report_file.write_text(report)
            print_success(f"Deployment report created: {report_file}")
            
            # Also print summary
            print_header("DEPLOYMENT SUMMARY")
            print_success(f"✅ Fixes Applied: {len(self.fixes_applied)}")
            if self.warnings:
                print_warning(f"⚠️  Warnings: {len(self.warnings)}")
            if self.errors:
                print_error(f"❌ Errors: {len(self.errors)}")
            
            return True
            
        except Exception as e:
            print_error(f"Report generation failed: {e}")
            return False
    
    def run_deployment(self) -> bool:
        """Run complete deployment"""
        print_header("YMERA PRODUCTION DEPLOYMENT v4.0.0")
        print_info("Starting automated deployment process...")
        
        steps = [
            self.create_backup,
            self.create_directories,
            self.fix_database_module,
            self.fix_init_file,
            self.fix_gateway_routing_encoding,
            self.create_utility_files,
            self.verify_syntax,
            self.verify_imports,
            self.create_env_template,
            self.generate_deployment_report,
        ]
        
        success = True
        for step in steps:
            if not step():
                success = False
                print_error(f"Step failed: {step.__name__}")
                
                response = input("\nContinue with remaining steps? (y/n): ")
                if response.lower() != 'y':
                    break
        
        print_header("DEPLOYMENT COMPLETE")
        
        if success and not self.errors:
            print_success("🎉 Deployment completed successfully!")
            print_info(f"\n📁 Backup location: {BACKUP_DIR}")
            print_info(f"📄 Deployment report: {BACKEND_ROOT / 'DEPLOYMENT_REPORT.md'}")
            print_info("\n👉 Next: Review the deployment report and follow the next steps")
            return True
        else:
            print_error("⚠️  Deployment completed with issues")
            print_info(f"\n📁 Backup location: {BACKUP_DIR}")
            print_info("👉 Review errors above and the deployment report")
            return False

# ===============================================================================
# MAIN ENTRY POINT
# ===============================================================================

def main():
    """Main entry point"""
    
    # Check if running from correct directory
    if not BACKEND_ROOT.exists():
        print_error("Error: backend directory not found!")
        print_info("Please run this script from the project root directory")
        sys.exit(1)
    
    # Confirm deployment
    print_header("YMERA PRODUCTION DEPLOYMENT")
    print_warning("This script will modify your codebase.")
    print_info(f"Backup will be created in: {BACKUP_DIR}")
    
    response = input("\nContinue with deployment? (yes/no): ")
    if response.lower() != 'yes':
        print_info("Deployment cancelled")
        sys.exit(0)
    
    # Run deployment
    deployment = ProductionDeployment()
    success = deployment.run_deployment()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
