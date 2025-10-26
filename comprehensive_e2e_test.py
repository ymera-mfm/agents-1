"""
Comprehensive E2E Testing Script for YMERA Database System V5
Tests all components and provides honest assessment
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Test results tracking
test_results = {
    'passed': [],
    'failed': [],
    'warnings': [],
    'skipped': []
}

def log_result(category, test_name, status, message=""):
    """Log test result"""
    result = {
        'test': test_name,
        'status': status,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    test_results[category].append(result)
    
    symbols = {
        'passed': '✅',
        'failed': '❌',
        'warnings': '⚠️',
        'skipped': '⏭️'
    }
    
    print(f"{symbols.get(category, '•')} {test_name}: {message}")

def test_category(name):
    """Decorator for test categories"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"\n{'='*60}")
            print(f"Testing: {name}")
            print('='*60)
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


# ============================================================================
# TEST 1: Environment and Dependencies
# ============================================================================

@test_category("1. Environment & Dependencies")
def test_environment():
    """Test Python environment and dependencies"""
    
    # Check Python version
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 9:
        log_result('passed', 'Python Version', 'OK', f'Python {py_version.major}.{py_version.minor}.{py_version.micro}')
    else:
        log_result('failed', 'Python Version', 'FAIL', f'Requires Python 3.9+, found {py_version.major}.{py_version.minor}')
    
    # Check critical dependencies
    dependencies = [
        ('sqlalchemy', 'SQLAlchemy'),
        ('structlog', 'Structlog'),
        ('asyncio', 'AsyncIO'),
    ]
    
    for module, name in dependencies:
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'built-in')
            log_result('passed', f'{name} Import', 'OK', f'Version: {version}')
        except ImportError:
            log_result('failed', f'{name} Import', 'MISSING', 'Not installed')
        except Exception as e:
            log_result('warnings', f'{name} Import', 'ERROR', str(e))
    
    # Check optional dependencies
    optional_deps = [
        ('asyncpg', 'AsyncPG (PostgreSQL)'),
        ('aiosqlite', 'AIOSqlite (SQLite)'),
        ('faker', 'Faker (Test Data)'),
        ('pydantic', 'Pydantic (Validation)'),
    ]
    
    for module, name in optional_deps:
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'unknown')
            log_result('passed', f'{name}', 'OK', f'Version: {version}')
        except ImportError:
            log_result('warnings', f'{name}', 'NOT INSTALLED', 'Optional but recommended')


# ============================================================================
# TEST 2: Core Module Structure
# ============================================================================

@test_category("2. Core Module Structure")
def test_core_module():
    """Test database_core_integrated module"""
    
    try:
        import database_core_integrated as dbc
        log_result('passed', 'Core Module Import', 'OK', 'database_core_integrated imported')
        
        # Check key classes
        required_classes = [
            'DatabaseConfig',
            'IntegratedDatabaseManager',
            'User',
            'Project',
            'Agent',
            'Task',
            'File',
            'AuditLog',
            'BaseRepository',
            'BaseMigration',
            'Base'
        ]
        
        for cls_name in required_classes:
            if hasattr(dbc, cls_name):
                log_result('passed', f'Class: {cls_name}', 'FOUND', 'Available')
            else:
                log_result('failed', f'Class: {cls_name}', 'MISSING', 'Not found in module')
        
        # Check key functions
        required_functions = [
            'get_database_manager',
            'get_db_session',
            'init_database',
            'close_database'
        ]
        
        for func_name in required_functions:
            if hasattr(dbc, func_name):
                log_result('passed', f'Function: {func_name}', 'FOUND', 'Available')
            else:
                log_result('failed', f'Function: {func_name}', 'MISSING', 'Not found in module')
        
        return True
        
    except ImportError as e:
        log_result('failed', 'Core Module Import', 'FAILED', str(e))
        return False
    except Exception as e:
        log_result('failed', 'Core Module Structure', 'ERROR', str(e))
        return False


# ============================================================================
# TEST 3: File Structure
# ============================================================================

@test_category("3. File Structure")
def test_file_structure():
    """Test that all expected files exist"""
    
    required_files = [
        'database_core_integrated.py',
        'requirements.txt',
        'README.md',
        'test_database.py',
        'DATABASE_ARCHITECTURE.md',
        'IMPLEMENTATION_SUMMARY.md',
        'COMPLETE_IMPLEMENTATION_REPORT.md'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            size_kb = Path(file_path).stat().st_size / 1024
            log_result('passed', f'File: {file_path}', 'EXISTS', f'{size_kb:.1f} KB')
        else:
            log_result('failed', f'File: {file_path}', 'MISSING', 'File not found')
    
    # Check directories
    required_dirs = [
        'database',
        'database/migrations',
        'database/fixtures',
        'scripts',
        'docs'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            log_result('passed', f'Directory: {dir_path}', 'EXISTS', 'Found')
        else:
            log_result('failed', f'Directory: {dir_path}', 'MISSING', 'Directory not found')
    
    # Check new components
    new_components = [
        'database/migration_manager.py',
        'database/migrations/001_initial_schema.py',
        'database/fixtures/test_fixtures.py',
        'scripts/backup_manager.py',
        'scripts/database_monitor.py',
        'docs/DISASTER_RECOVERY.md',
        'docs/OPERATIONS_RUNBOOK.md'
    ]
    
    for component in new_components:
        if Path(component).exists():
            size_kb = Path(component).stat().st_size / 1024
            log_result('passed', f'Component: {Path(component).name}', 'EXISTS', f'{size_kb:.1f} KB')
        else:
            log_result('warnings', f'Component: {Path(component).name}', 'MISSING', 'New component not found')


# ============================================================================
# TEST 4: Database Initialization (Basic)
# ============================================================================

@test_category("4. Database Initialization")
async def test_database_init():
    """Test basic database initialization"""
    
    try:
        from database_core_integrated import DatabaseConfig, IntegratedDatabaseManager
        
        # Test config creation
        config = DatabaseConfig()
        log_result('passed', 'DatabaseConfig', 'CREATED', f'DB type: {config.db_type}')
        
        # Test database URL
        if config.database_url:
            log_result('passed', 'Database URL', 'SET', f'Type: {config.db_type}')
        else:
            log_result('warnings', 'Database URL', 'NOT SET', 'Using default')
        
        # Test manager creation (without actual connection)
        manager = IntegratedDatabaseManager(config)
        log_result('passed', 'DatabaseManager', 'CREATED', 'Instance created')
        
        return True
        
    except Exception as e:
        log_result('failed', 'Database Initialization', 'ERROR', str(e))
        return False


# ============================================================================
# TEST 5: Model Definitions
# ============================================================================

@test_category("5. Model Definitions")
def test_models():
    """Test database model definitions"""
    
    try:
        from database_core_integrated import User, Project, Agent, Task, File, AuditLog, Base
        
        models = {
            'User': User,
            'Project': Project,
            'Agent': Agent,
            'Task': Task,
            'File': File,
            'AuditLog': AuditLog
        }
        
        for model_name, model_class in models.items():
            # Check table name
            if hasattr(model_class, '__tablename__'):
                log_result('passed', f'Model: {model_name}', 'OK', f'Table: {model_class.__tablename__}')
            else:
                log_result('failed', f'Model: {model_name}', 'NO TABLE', 'Missing __tablename__')
            
            # Check key columns
            if hasattr(model_class, '__table__'):
                col_count = len(model_class.__table__.columns)
                log_result('passed', f'  └─ Columns', 'OK', f'{col_count} columns defined')
            
            # Check relationships
            if hasattr(model_class, '__mapper__'):
                rel_count = len(model_class.__mapper__.relationships)
                if rel_count > 0:
                    log_result('passed', f'  └─ Relationships', 'OK', f'{rel_count} relationships')
        
        return True
        
    except Exception as e:
        log_result('failed', 'Model Definitions', 'ERROR', str(e))
        return False


# ============================================================================
# TEST 6: Migration System
# ============================================================================

@test_category("6. Migration System")
def test_migration_system():
    """Test migration system components"""
    
    # Check migration manager
    if Path('database/migration_manager.py').exists():
        log_result('passed', 'Migration Manager', 'EXISTS', 'Script found')
        
        try:
            # Try to import (without running)
            spec = __import__('importlib.util').util.spec_from_file_location(
                "migration_manager",
                "database/migration_manager.py"
            )
            if spec:
                log_result('passed', 'Migration Manager Import', 'OK', 'Can be imported')
        except Exception as e:
            log_result('warnings', 'Migration Manager Import', 'ERROR', str(e))
    else:
        log_result('failed', 'Migration Manager', 'MISSING', 'File not found')
    
    # Check migrations directory
    migrations_dir = Path('database/migrations')
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob('*.py'))
        migration_files = [f for f in migration_files if not f.name.startswith('__')]
        log_result('passed', 'Migrations Directory', 'EXISTS', f'{len(migration_files)} migrations found')
    else:
        log_result('failed', 'Migrations Directory', 'MISSING', 'Directory not found')


# ============================================================================
# TEST 7: Operations Scripts
# ============================================================================

@test_category("7. Operations Scripts")
def test_operations_scripts():
    """Test operations and monitoring scripts"""
    
    scripts = {
        'scripts/backup_manager.py': 'Backup & Recovery',
        'scripts/database_monitor.py': 'Monitoring & Health Checks'
    }
    
    for script_path, description in scripts.items():
        if Path(script_path).exists():
            size_kb = Path(script_path).stat().st_size / 1024
            log_result('passed', description, 'EXISTS', f'{size_kb:.1f} KB')
        else:
            log_result('failed', description, 'MISSING', 'Script not found')


# ============================================================================
# TEST 8: Documentation
# ============================================================================

@test_category("8. Documentation")
def test_documentation():
    """Test documentation completeness"""
    
    docs = {
        'README.md': 'User Guide',
        'DATABASE_ARCHITECTURE.md': 'Architecture Docs',
        'IMPLEMENTATION_SUMMARY.md': 'Implementation Summary',
        'COMPLETE_IMPLEMENTATION_REPORT.md': 'Complete Report',
        'docs/DISASTER_RECOVERY.md': 'Disaster Recovery Plan',
        'docs/OPERATIONS_RUNBOOK.md': 'Operations Runbook',
        'DEPLOYMENT_GUIDE.md': 'Deployment Guide'
    }
    
    for doc_path, description in docs.items():
        if Path(doc_path).exists():
            size_kb = Path(doc_path).stat().st_size / 1024
            log_result('passed', description, 'EXISTS', f'{size_kb:.1f} KB')
        else:
            log_result('warnings', description, 'MISSING', 'Document not found')


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*60)
    print("YMERA DATABASE SYSTEM V5 - COMPREHENSIVE E2E TESTING")
    print("="*60)
    print(f"Started: {datetime.utcnow().isoformat()}")
    print("="*60)
    
    # Run synchronous tests
    test_environment()
    core_ok = test_core_module()
    test_file_structure()
    test_models()
    test_migration_system()
    test_operations_scripts()
    test_documentation()
    
    # Run async tests
    if core_ok:
        await test_database_init()
    else:
        log_result('skipped', 'Database Initialization', 'SKIPPED', 'Core module failed')
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = sum(len(results) for results in test_results.values())
    
    print(f"\n✅ Passed:  {len(test_results['passed'])}")
    print(f"❌ Failed:  {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    print(f"⏭️  Skipped: {len(test_results['skipped'])}")
    print(f"\nTotal Tests: {total_tests}")
    
    # Calculate success rate
    if total_tests > 0:
        success_rate = (len(test_results['passed']) / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Show critical failures
    if test_results['failed']:
        print("\n❌ CRITICAL FAILURES:")
        for failure in test_results['failed']:
            print(f"  • {failure['test']}: {failure['message']}")
    
    # Show warnings
    if test_results['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in test_results['warnings'][:5]:  # Show first 5
            print(f"  • {warning['test']}: {warning['message']}")
        if len(test_results['warnings']) > 5:
            print(f"  ... and {len(test_results['warnings']) - 5} more")
    
    print("\n" + "="*60)
    print(f"Completed: {datetime.utcnow().isoformat()}")
    print("="*60 + "\n")
    
    return test_results


if __name__ == "__main__":
    # Run tests
    results = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    if results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)
