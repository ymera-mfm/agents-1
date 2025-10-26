#!/bin/bash
# YMERA Platform - Automated Setup Script
# This script automates the entire setup process
# Usage: ./automated_setup.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run as root"
    exit 1
fi

print_header "YMERA PLATFORM - AUTOMATED SETUP"

# Step 1: Backup existing files
print_info "Step 1/10: Creating backups..."
if [ -d "backend/app/CORE_ENGINE" ]; then
    cp -r backend/app/CORE_ENGINE backend/app/CORE_ENGINE.backup.$(date +%Y%m%d_%H%M%S)
    print_success "Backup created"
else
    mkdir -p backend/app/CORE_ENGINE
    print_info "Created CORE_ENGINE directory"
fi

if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    print_success ".env backed up"
fi

# Step 2: Check Python version
print_info "Step 2/10: Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    print_success "Python $python_version detected"
else
    print_error "Python 3.9+ required, found $python_version"
    exit 1
fi

# Step 3: Install dependencies
print_info "Step 3/10: Installing Python dependencies..."
pip3 install -q --upgrade pip
pip3 install -q asyncio structlog aioredis typing-extensions python-dotenv cryptography pydantic
print_success "Dependencies installed"

# Step 4: Create directory structure
print_info "Step 4/10: Creating directory structure..."
mkdir -p backend/app/CORE_ENGINE
mkdir -p backend/app/CORE_CONFIGURATION
mkdir -p tests
mkdir -p scripts
mkdir -p keys
mkdir -p logs
mkdir -p data
chmod 700 keys
print_success "Directory structure created"

# Step 5: Update .gitignore
print_info "Step 5/10: Updating .gitignore..."
cat >> .gitignore << 'EOF'

# YMERA Security - Never commit these files
.env
.env.*
!.env.template
*.key
*.pem
keys/
secrets/
1.txt
*.backup

# Sensitive configuration
**/config_local.py
**/secrets.py

# Logs and data
logs/
data/
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
EOF
print_success ".gitignore updated"

# Step 6: Generate secure keys
print_info "Step 6/10: Generating secure keys..."
if [ ! -f ".env" ]; then
    print_info "Creating .env file with secure keys..."
    
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    cat > .env << EOF
# YMERA Platform Configuration
# Generated: $(date)

# Application
APP_NAME=YMERA Enterprise Platform
APP_VERSION=4.0.0
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=${SECRET_KEY}

# Security
JWT_SECRET_KEY=${JWT_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Database
DATABASE_URL=postgresql+asyncpg://ymera_user:ymera_password@localhost:5432/ymera_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=20

# Learning Engine
LEARNING_CYCLE_INTERVAL=60
KNOWLEDGE_SYNC_INTERVAL=300
PATTERN_DISCOVERY_INTERVAL=900
MEMORY_CONSOLIDATION_INTERVAL=3600

# Add your API keys below:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# PINECONE_API_KEY=...
EOF
    
    chmod 600 .env
    print_success "Secure .env file created"
else
    print_warning ".env file already exists, skipping"
fi

# Step 7: Check for exposed credentials
print_info "Step 7/10: Checking for exposed credentials..."
if [ -f "1.txt" ]; then
    print_warning "Found potentially exposed credential file: 1.txt"
    read -p "Do you want to delete it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm 1.txt
        print_success "Removed 1.txt"
    else
        print_warning "⚠️  WARNING: 1.txt contains exposed credentials!"
    fi
fi

# Step 8: Verify file structure
print_info "Step 8/10: Verifying file structure..."

required_files=(
    "backend/app/CORE_ENGINE/__init__.py"
    "backend/app/CORE_ENGINE/utils.py"
    "backend/app/CORE_ENGINE/core_engine.py"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Missing: $file"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = true ]; then
    print_success "All required files present"
else
    print_warning "Some files are missing - please copy from artifacts"
fi

# Step 9: Run tests
print_info "Step 9/10: Running validation tests..."

# Test imports
if python3 -c "from backend.app.CORE_ENGINE import CoreEngine, utils" 2>/dev/null; then
    print_success "Import test passed"
else
    print_warning "Import test failed - check file contents"
fi

# Step 10: Create helper scripts
print_info "Step 10/10: Creating helper scripts..."

# Create startup script
cat > scripts/start.sh << 'EOF'
#!/bin/bash
echo "Starting YMERA Platform..."
source .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF
chmod +x scripts/start.sh

# Create test script
cat > scripts/run_tests.sh << 'EOF'
#!/bin/bash
echo "Running YMERA tests..."
python3 tests/test_utils.py
python3 tests/test_core_engine.py
python3 tests/test_integration.py
EOF
chmod +x scripts/run_tests.sh

# Create health check script
cat > scripts/health_check.sh << 'EOF'
#!/bin/bash
echo "Checking YMERA health..."
curl -f http://localhost:8000/health || echo "Service not running"
EOF
chmod +x scripts/health_check.sh

print_success "Helper scripts created"

# Final summary
print_header "SETUP COMPLETE!"

echo -e "${GREEN}✅ Setup completed successfully!${NC}\n"

echo "📋 Next Steps:"
echo "1. Review and update .env file with your API keys"
echo "2. Copy artifact contents to the following files:"
echo "   - backend/app/CORE_ENGINE/__init__.py (from artifact: core_engine_init)"
echo "   - backend/app/CORE_ENGINE/utils.py (from artifact: core_engine_utils)"
echo "   - backend/app/CORE_ENGINE/core_engine.py (from artifact: core_engine_complete)"
echo ""
echo "3. Run validation:"
echo "   ./scripts/run_tests.sh"
echo ""
echo "4. Start the platform:"
echo "   ./scripts/start.sh"
echo ""
echo "5. Check health:"
echo "   ./scripts/health_check.sh"
echo ""

print_warning "IMPORTANT: Before deploying to production:"
echo "   1. Revoke all exposed credentials from 1.txt"
echo "   2. Update .env with production credentials"
echo "   3. Run security audit: python scripts/audit_credentials.py"
echo "   4. Run pre-deployment checks"
echo ""

echo -e "${BLUE}📚 Documentation available in deployment guide artifact${NC}"
echo -e "${GREEN}Happy building! 🚀${NC}\n"

# Save setup log
log_file="setup_$(date +%Y%m%d_%H%M%S).log"
echo "Setup completed at $(date)" > "$log_file"
echo "Python version: $python_version" >> "$log_file"
echo "Setup script version: 1.0" >> "$log_file"
print_info "Setup log saved to: $log_file"
