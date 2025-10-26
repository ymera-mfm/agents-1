#!/usr/bin/env python3
"""
Test script to verify the deployment preparation structure
"""

import os
import sys
from pathlib import Path


def test_deployment_structure():
    """Test that all required deployment files exist"""
    print("🧪 Testing deployment structure...")
    
    deployment_dir = Path(__file__).parent / 'enhanced_workspace' / 'deployment'
    
    required_files = {
        'docker-compose.yml': 'Docker Compose configuration',
        '.env.production': 'Production environment variables',
        'deploy.sh': 'Deployment script',
        'validate_deployment.py': 'Deployment validation script',
        'health_check.py': 'Health check script',
        'init_database.py': 'Database initialization script',
        'README.md': 'Documentation',
    }
    
    required_dirs = {
        'integration': 'API Gateway build context',
    }
    
    all_passed = True
    
    # Check files
    for filename, description in required_files.items():
        filepath = deployment_dir / filename
        if filepath.exists():
            print(f"✅ {filename} exists ({description})")
        else:
            print(f"❌ {filename} missing ({description})")
            all_passed = False
    
    # Check directories
    for dirname, description in required_dirs.items():
        dirpath = deployment_dir / dirname
        if dirpath.exists() and dirpath.is_dir():
            print(f"✅ {dirname}/ exists ({description})")
        else:
            print(f"❌ {dirname}/ missing ({description})")
            all_passed = False
    
    # Check integration/Dockerfile
    integration_dockerfile = deployment_dir / 'integration' / 'Dockerfile'
    if integration_dockerfile.exists():
        print(f"✅ integration/Dockerfile exists")
    else:
        print(f"❌ integration/Dockerfile missing")
        all_passed = False
    
    assert all_passed


def test_docker_compose_content():
    """Test docker-compose.yml content"""
    print("\n🧪 Testing docker-compose.yml content...")
    
    deployment_dir = Path(__file__).parent / 'enhanced_workspace' / 'deployment'
    docker_compose_file = deployment_dir / 'docker-compose.yml'
    
    if not docker_compose_file.exists():
        print("❌ docker-compose.yml not found")
        return False
    
    content = docker_compose_file.read_text()
    
    required_elements = [
        "version: '3.8'",
        "api-gateway:",
        "build: ./integration/",
        "8000:8000",
        "redis:",
        "image: redis:alpine",
        "6379:6379",
        "postgres:",
        "image: postgres:13",
        "POSTGRES_DB: enhanced_platform",
        "POSTGRES_USER: admin",
        "POSTGRES_PASSWORD: secure_password",
        "5432:5432",
        "volumes:",
        "postgres_data:",
    ]
    
    all_passed = True
    for element in required_elements:
        if element in content:
            print(f"✅ Contains: {element}")
        else:
            print(f"❌ Missing: {element}")
            all_passed = False
    
    return all_passed


def test_env_production_content():
    """Test .env.production content"""
    print("\n🧪 Testing .env.production content...")
    
    deployment_dir = Path(__file__).parent / 'enhanced_workspace' / 'deployment'
    env_file = deployment_dir / '.env.production'
    
    if not env_file.exists():
        print("❌ .env.production not found")
        return False
    
    content = env_file.read_text()
    
    required_vars = [
        "DATABASE_URL=postgresql://admin:secure_password@postgres:5432/enhanced_platform",
        "REDIS_URL=redis://redis:6379/0",
        "API_PORT=8000",
        "LOG_LEVEL=INFO",
        "ENVIRONMENT=production",
        "ENABLE_ALL_AGENTS=true",
        "ENABLE_ALL_ENGINES=true",
        "ENABLE_MONITORING=true",
        "ENABLE_LOGGING=true",
    ]
    
    all_passed = True
    for var in required_vars:
        if var in content:
            print(f"✅ Contains: {var}")
        else:
            print(f"❌ Missing: {var}")
            all_passed = False
    
    return all_passed


def test_deploy_script_content():
    """Test deploy.sh content"""
    print("\n🧪 Testing deploy.sh content...")
    
    deployment_dir = Path(__file__).parent / 'enhanced_workspace' / 'deployment'
    deploy_script = deployment_dir / 'deploy.sh'
    
    if not deploy_script.exists():
        print("❌ deploy.sh not found")
        return False
    
    content = deploy_script.read_text()
    
    required_elements = [
        "#!/bin/bash",
        "python deployment/validate_deployment.py",
        "docker-compose up -d --build",
        "python deployment/health_check.py",
        "python deployment/init_database.py",
    ]
    
    all_passed = True
    for element in required_elements:
        if element in content:
            print(f"✅ Contains: {element}")
        else:
            print(f"❌ Missing: {element}")
            all_passed = False
    
    # Check if executable
    if os.access(deploy_script, os.X_OK):
        print("✅ Script is executable")
    else:
        print("❌ Script is not executable")
        all_passed = False
    
    return all_passed


def test_python_scripts():
    """Test Python scripts are executable and have shebang"""
    print("\n🧪 Testing Python scripts...")
    
    deployment_dir = Path(__file__).parent / 'enhanced_workspace' / 'deployment'
    
    scripts = [
        'validate_deployment.py',
        'health_check.py',
        'init_database.py',
    ]
    
    all_passed = True
    for script in scripts:
        script_path = deployment_dir / script
        
        if not script_path.exists():
            print(f"❌ {script} not found")
            all_passed = False
            continue
        
        # Check shebang
        content = script_path.read_text()
        if content.startswith('#!/usr/bin/env python3'):
            print(f"✅ {script} has correct shebang")
        else:
            print(f"❌ {script} missing shebang")
            all_passed = False
        
        # Check if executable
        if os.access(script_path, os.X_OK):
            print(f"✅ {script} is executable")
        else:
            print(f"❌ {script} is not executable")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 DEPLOYMENT PREPARATION TESTS")
    print("=" * 60)
    print()
    
    tests = [
        ("Deployment Structure", test_deployment_structure),
        ("Docker Compose Content", test_docker_compose_content),
        ("Environment Variables Content", test_env_production_content),
        ("Deploy Script Content", test_deploy_script_content),
        ("Python Scripts", test_python_scripts),
    ]
    
    all_passed = True
    for name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {name} test failed with error: {e}")
            all_passed = False
        print()
    
    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
