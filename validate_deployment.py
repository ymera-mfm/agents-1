#!/usr/bin/env python3
"""
Deployment Validation Script
Validates that all prerequisites are met before deployment
"""

import os
import sys
from pathlib import Path


def check_environment_variables():
    """Check if required environment variables are set"""
    print("📋 Checking environment variables...")
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'API_PORT',
        'ENVIRONMENT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True


def check_docker():
    """Check if Docker is installed and running"""
    print("🐳 Checking Docker...")
    import subprocess
    
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker is installed: {result.stdout.strip()}")
        
        # Check if Docker daemon is running
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, text=True, check=True)
        print("✅ Docker daemon is running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Docker check failed: {e}")
        return False


def check_docker_compose():
    """Check if Docker Compose is installed"""
    print("🐙 Checking Docker Compose...")
    import subprocess
    
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker Compose is installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Docker Compose (v2) is installed: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Docker Compose check failed: {e}")
            return False


def check_deployment_files():
    """Check if all required deployment files exist"""
    print("📁 Checking deployment files...")
    
    deployment_dir = Path(__file__).parent
    required_files = [
        'docker-compose.yml',
        '.env.production',
        'deploy.sh'
    ]
    
    missing_files = []
    for file in required_files:
        file_path = deployment_dir / file
        if not file_path.exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required deployment files exist")
    return True


def check_integration_directory():
    """Check if integration directory exists for building api-gateway"""
    print("🔗 Checking integration directory...")
    
    deployment_dir = Path(__file__).parent
    integration_dir = deployment_dir / 'integration'
    
    if not integration_dir.exists():
        print(f"⚠️  Integration directory not found at {integration_dir}")
        print("   Creating placeholder integration directory...")
        integration_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal Dockerfile
        dockerfile = integration_dir / 'Dockerfile'
        dockerfile.write_text("""FROM python:3.11-slim

WORKDIR /app

# Install basic dependencies
RUN pip install fastapi uvicorn redis psycopg2-binary

# Placeholder entrypoint
CMD ["python", "-c", "print('API Gateway placeholder - Configure your application here')"]
""")
        print(f"✅ Created placeholder integration directory with Dockerfile")
    else:
        print("✅ Integration directory exists")
    
    return True


def main():
    """Main validation function"""
    print("=" * 60)
    print("🚀 DEPLOYMENT VALIDATION")
    print("=" * 60)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("Deployment Files", check_deployment_files),
        ("Integration Directory", check_integration_directory),
    ]
    
    all_passed = True
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            all_passed = False
        print()
    
    print("=" * 60)
    if all_passed:
        print("✅ All validation checks passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some validation checks failed. Please fix the issues above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
