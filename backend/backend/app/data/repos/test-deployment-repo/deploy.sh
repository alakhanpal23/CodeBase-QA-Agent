#!/bin/bash

# CodeBase QA Agent Deployment Script
# Usage: ./deploy.sh [development|production]

set -e

ENVIRONMENT=${1:-development}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Deploying CodeBase QA Agent in $ENVIRONMENT mode..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Node.js is installed (for local development)
    if [[ "$ENVIRONMENT" == "development" ]] && ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. Some development features may not work."
    fi
    
    # Check if Python is installed (for local development)
    if [[ "$ENVIRONMENT" == "development" ]] && ! command -v python3 &> /dev/null; then
        print_warning "Python 3 is not installed. Some development features may not work."
    fi
    
    print_success "Prerequisites check completed"
}

# Setup environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    # Backend environment
    if [[ ! -f "$SCRIPT_DIR/backend/.env" ]]; then
        print_status "Creating backend .env file from template..."
        cp "$SCRIPT_DIR/backend/.env.example" "$SCRIPT_DIR/backend/.env"
        print_warning "Please edit backend/.env with your actual configuration values"
    fi
    
    # Frontend environment
    if [[ "$ENVIRONMENT" == "production" ]]; then
        if [[ ! -f "$SCRIPT_DIR/frontend/.env.production.local" ]]; then
            print_status "Creating frontend production environment file..."
            cp "$SCRIPT_DIR/frontend/.env.production" "$SCRIPT_DIR/frontend/.env.production.local"
            print_warning "Please edit frontend/.env.production.local with your production API URL"
        fi
    else
        if [[ ! -f "$SCRIPT_DIR/frontend/.env.local" ]]; then
            print_status "Creating frontend development environment file..."
            cp "$SCRIPT_DIR/frontend/.env.local.example" "$SCRIPT_DIR/frontend/.env.local"
        fi
    fi
    
    print_success "Environment files setup completed"
}

# Development deployment
deploy_development() {
    print_status "Starting development deployment..."
    
    # Install backend dependencies
    print_status "Installing backend dependencies..."
    cd "$SCRIPT_DIR/backend"
    if [[ -f "requirements.txt" ]]; then
        pip3 install -r requirements.txt
    fi
    
    # Install frontend dependencies
    print_status "Installing frontend dependencies..."
    cd "$SCRIPT_DIR/frontend"
    if [[ -f "package.json" ]]; then
        npm install
    fi
    
    # Create data directories
    mkdir -p "$SCRIPT_DIR/backend/app/data/indexes"
    mkdir -p "$SCRIPT_DIR/backend/app/data/temp"
    mkdir -p "$SCRIPT_DIR/backend/app/data/repos"
    
    print_success "Development environment setup completed"
    print_status "To start the services:"
    print_status "  Backend: cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    print_status "  Frontend: cd frontend && npm run dev"
}\n\n# Production deployment\ndeploy_production() {\n    print_status \"Starting production deployment...\"\n    \n    # Build and start services with Docker Compose\n    print_status \"Building and starting services...\"\n    cd \"$SCRIPT_DIR\"\n    \n    # Set environment variables for Docker Compose\n    export ENVIRONMENT=production\n    export OPENAI_API_KEY=${OPENAI_API_KEY:-dummy-key-for-testing}\n    export EMBED_MODE=${EMBED_MODE:-auto}\n    \n    # Build and start services\n    docker-compose down --remove-orphans\n    docker-compose build --no-cache\n    docker-compose up -d\n    \n    # Wait for services to be ready\n    print_status \"Waiting for services to be ready...\"\n    sleep 30\n    \n    # Health check\n    if curl -f http://localhost:8000/health > /dev/null 2>&1; then\n        print_success \"Backend is healthy\"\n    else\n        print_error \"Backend health check failed\"\n        docker-compose logs backend\n        exit 1\n    fi\n    \n    if curl -f http://localhost:3000 > /dev/null 2>&1; then\n        print_success \"Frontend is healthy\"\n    else\n        print_error \"Frontend health check failed\"\n        docker-compose logs frontend\n        exit 1\n    fi\n    \n    print_success \"Production deployment completed successfully!\"\n    print_status \"Services are running at:\"\n    print_status \"  Frontend: http://localhost:3000\"\n    print_status \"  Backend API: http://localhost:8000\"\n    print_status \"  API Documentation: http://localhost:8000/docs\"\n}\n\n# Run tests\nrun_tests() {\n    print_status \"Running deployment tests...\"\n    \n    cd \"$SCRIPT_DIR\"\n    \n    # Wait a bit for services to be fully ready\n    sleep 10\n    \n    # Run the test script\n    if [[ -f \"test_deployment.py\" ]]; then\n        python3 test_deployment.py\n        if [[ $? -eq 0 ]]; then\n            print_success \"All tests passed!\"\n        else\n            print_error \"Some tests failed. Check the output above.\"\n            exit 1\n        fi\n    else\n        print_warning \"Test script not found. Skipping tests.\"\n    fi\n}\n\n# Main deployment logic\nmain() {\n    print_status \"CodeBase QA Agent Deployment\"\n    print_status \"Environment: $ENVIRONMENT\"\n    print_status \"Script directory: $SCRIPT_DIR\"\n    \n    check_prerequisites\n    setup_environment\n    \n    if [[ \"$ENVIRONMENT\" == \"production\" ]]; then\n        deploy_production\n    else\n        deploy_development\n    fi\n    \n    # Ask if user wants to run tests\n    if [[ \"$ENVIRONMENT\" == \"production\" ]]; then\n        read -p \"Do you want to run deployment tests? (y/n): \" -n 1 -r\n        echo\n        if [[ $REPLY =~ ^[Yy]$ ]]; then\n            run_tests\n        fi\n    fi\n    \n    print_success \"Deployment completed successfully!\"\n}\n\n# Run main function\nmain \"$@\"