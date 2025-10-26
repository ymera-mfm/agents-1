#!/bin/bash
# YMERA Platform - System Startup Script
# This script starts the complete YMERA multi-agent AI system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$BLUE" "=========================================="
    print_message "$BLUE" "$1"
    print_message "$BLUE" "=========================================="
    echo ""
}

print_success() {
    print_message "$GREEN" "✓ $1"
}

print_error() {
    print_message "$RED" "✗ $1"
}

print_warning() {
    print_message "$YELLOW" "⚠ $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local all_good=true
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python 3 installed: $PYTHON_VERSION"
    else
        print_error "Python 3 is not installed. Please install Python 3.11 or higher."
        all_good=false
    fi
    
    # Check Docker
    if command_exists docker; then
        print_success "Docker is installed"
    else
        print_warning "Docker is not installed. Docker-based startup will not work."
    fi
    
    # Check Docker Compose
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        print_success "Docker Compose is available"
    else
        print_warning "Docker Compose is not available. Docker-based startup will not work."
    fi
    
    # Check PostgreSQL client (optional)
    if command_exists psql; then
        print_success "PostgreSQL client is installed"
    else
        print_warning "PostgreSQL client is not installed. Database connection testing will be limited."
    fi
    
    if [ "$all_good" = false ]; then
        print_error "Some required prerequisites are missing. Please install them and try again."
        exit 1
    fi
    
    echo ""
}

# Setup environment
setup_environment() {
    print_header "Setting Up Environment"
    
    # Check if .env exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
            print_warning "Please edit .env file with your configuration before starting the system."
            print_message "$YELLOW" "Required changes:"
            print_message "$YELLOW" "  - Set DATABASE_URL to your PostgreSQL connection string"
            print_message "$YELLOW" "  - Set REDIS_URL to your Redis connection string"
            print_message "$YELLOW" "  - Set JWT_SECRET_KEY to a secure random string"
            echo ""
            read -p "Press Enter to continue after editing .env, or Ctrl+C to exit..."
        else
            print_error ".env.example not found. Please create a .env file manually."
            exit 1
        fi
    else
        print_success ".env file exists"
    fi
    
    echo ""
}

# Install Python dependencies
install_dependencies() {
    print_header "Installing Python Dependencies"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_message "$YELLOW" "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_message "$YELLOW" "Activating virtual environment..."
    source venv/bin/activate
    
    # Install/upgrade pip
    print_message "$YELLOW" "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install dependencies
    print_message "$YELLOW" "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
    
    echo ""
}

# Start infrastructure services with Docker Compose
start_infrastructure() {
    print_header "Starting Infrastructure Services"
    
    if command_exists docker-compose; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not available"
        return 1
    fi
    
    print_message "$YELLOW" "Starting PostgreSQL, Redis, and other services..."
    $COMPOSE_CMD up -d postgres redis
    
    print_message "$YELLOW" "Waiting for services to be healthy..."
    sleep 5
    
    # Check if services are running
    if $COMPOSE_CMD ps | grep -q "postgres.*Up"; then
        print_success "PostgreSQL is running"
    else
        print_warning "PostgreSQL may not be running properly"
    fi
    
    if $COMPOSE_CMD ps | grep -q "redis.*Up"; then
        print_success "Redis is running"
    else
        print_warning "Redis may not be running properly"
    fi
    
    echo ""
}

# Initialize database
initialize_database() {
    print_header "Initializing Database"
    
    # Activate virtual environment if not already activated
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
    print_message "$YELLOW" "Running database migrations..."
    
    # Check if alembic is configured
    if [ -f "alembic.ini" ]; then
        # Run migrations
        if python3 -m alembic upgrade head 2>/dev/null; then
            print_success "Database migrations completed"
        else
            print_warning "Database migrations may have failed. Trying alternative initialization..."
            # Try alternative initialization script if it exists
            if [ -f "001_initial_schema.py" ]; then
                python3 001_initial_schema.py
                print_success "Database initialized using schema script"
            fi
        fi
    else
        print_warning "Alembic not configured. Checking for SQL schema files..."
        # Try to initialize with SQL schema
        if [ -f "database_schema.sql" ]; then
            print_message "$YELLOW" "SQL schema found. Manual initialization may be required."
            print_message "$YELLOW" "Run: psql -h localhost -U ymera_user -d ymera < database_schema.sql"
        fi
    fi
    
    echo ""
}

# Start the application
start_application() {
    print_header "Starting YMERA Application"
    
    # Activate virtual environment if not already activated
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
    print_message "$YELLOW" "Starting the main application..."
    print_message "$BLUE" "Application will be available at: http://localhost:8000"
    print_message "$BLUE" "Health check: http://localhost:8000/health"
    print_message "$BLUE" "Metrics: http://localhost:8000/metrics"
    print_message "$BLUE" "API Docs: http://localhost:8000/docs"
    echo ""
    print_message "$YELLOW" "Press Ctrl+C to stop the application"
    echo ""
    
    # Start the application
    python3 main.py
}

# Start all services with Docker Compose
start_full_docker() {
    print_header "Starting Full System with Docker Compose"
    
    if command_exists docker-compose; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not available"
        exit 1
    fi
    
    print_message "$YELLOW" "Starting all services..."
    $COMPOSE_CMD up -d
    
    print_message "$YELLOW" "Waiting for services to be healthy..."
    sleep 10
    
    print_success "Services started"
    print_message "$BLUE" "Use '$COMPOSE_CMD ps' to check service status"
    print_message "$BLUE" "Use '$COMPOSE_CMD logs -f' to view logs"
    print_message "$BLUE" "Use '$COMPOSE_CMD down' to stop all services"
    
    echo ""
}

# Main menu
show_menu() {
    print_header "YMERA Platform - Startup Script"
    echo "Choose startup mode:"
    echo ""
    echo "  1) Full Local Development (Infrastructure + Application)"
    echo "  2) Application Only (requires external PostgreSQL & Redis)"
    echo "  3) Docker Compose Full Stack"
    echo "  4) Infrastructure Only (PostgreSQL, Redis, etc.)"
    echo "  5) Exit"
    echo ""
}

# Main script
main() {
    # Check prerequisites first
    check_prerequisites
    
    # Show menu
    while true; do
        show_menu
        read -p "Enter your choice [1-5]: " choice
        
        case $choice in
            1)
                setup_environment
                install_dependencies
                start_infrastructure
                initialize_database
                start_application
                break
                ;;
            2)
                setup_environment
                install_dependencies
                print_warning "Make sure PostgreSQL and Redis are running and configured in .env"
                read -p "Press Enter to continue..."
                initialize_database
                start_application
                break
                ;;
            3)
                setup_environment
                start_full_docker
                print_success "Full stack started with Docker Compose"
                print_message "$BLUE" "Application URL: http://localhost:8000"
                break
                ;;
            4)
                start_infrastructure
                print_success "Infrastructure services started"
                break
                ;;
            5)
                print_message "$GREEN" "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1-5."
                ;;
        esac
    done
}

# Run main function
main
