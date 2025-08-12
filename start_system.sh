#!/bin/bash

# CodeBase QA Agent - Complete System Startup Script

echo "🚀 Starting CodeBase QA Agent System"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    print_error "Please run this script from the CodeBase-QA-Agent root directory"
    exit 1
fi

# Kill any existing processes on our ports
print_status "Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true
lsof -ti:3002 | xargs kill -9 2>/dev/null || true

# Create data directories
print_status "Creating data directories..."
mkdir -p backend/app/data/indexes
mkdir -p backend/app/data/temp
mkdir -p backend/app/data/repos

# Set environment variables
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-for-testing}"
print_status "Using OpenAI API Key: ${OPENAI_API_KEY:0:10}..."

# Start backend
print_status "Starting backend server..."
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
print_status "Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend is running on http://localhost:8000"
else
    print_warning "Backend may still be starting up..."
fi

# Start frontend
print_status "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
print_status "Waiting for frontend to initialize..."
sleep 10

# Check if frontend is running
if curl -f http://localhost:3001 > /dev/null 2>&1; then
    print_success "Frontend is running on http://localhost:3001"
elif curl -f http://localhost:3002 > /dev/null 2>&1; then
    print_success "Frontend is running on http://localhost:3002"
else
    print_warning "Frontend may still be starting up..."
fi

print_success "System startup complete!"
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://localhost:3001 (or 3002)"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Admin Dashboard: http://localhost:3001/admin"
echo ""
echo "🧪 Run tests:"
echo "   python test_deployment.py"
echo "   python run_all_tests.py"
echo ""
echo "🛑 To stop the system:"
echo "   Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"

# Keep script running and handle Ctrl+C
trap 'print_status "Shutting down..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Wait for processes
wait