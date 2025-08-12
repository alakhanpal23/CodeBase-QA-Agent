# 🚀 Quick Start Guide

## One-Command Startup

```bash
./start_system.sh
```

This will:
- ✅ Start the backend server on port 8000
- ✅ Start the frontend server on port 3001/3002
- ✅ Create all necessary directories
- ✅ Set up environment variables

## Manual Startup

### 1. Start Backend
```bash
cd backend
export OPENAI_API_KEY="dummy-key-for-testing"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend (new terminal)
```bash
cd frontend
npm run dev
```

## Access Points

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Admin Dashboard**: http://localhost:3001/admin

## Test the System

```bash
# Basic functionality test
python test_deployment.py

# Comprehensive test suite
python run_all_tests.py
```

## Test Repositories

Add these repositories to test the system:

```
https://github.com/tiangolo/fastapi
https://github.com/pallets/flask
https://github.com/alakhanpal23/CodeBase-QA-Agent
```

## Example Questions

- "How does routing work in this framework?"
- "Show me the authentication implementation"
- "What are the main API endpoints?"
- "How is error handling implemented?"

## Troubleshooting

**Port conflicts:**
```bash
lsof -ti:8000 | xargs kill -9
lsof -ti:3001 | xargs kill -9
```

**Missing dependencies:**
```bash
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

**Permission issues:**
```bash
chmod +x start_system.sh
chmod +x run_all_tests.py
chmod +x test_deployment.py
```

## Production Deployment

```bash
# With OpenAI API key
export OPENAI_API_KEY="your-real-openai-key"
./deploy.sh production

# Without OpenAI (uses mock embeddings)
./deploy.sh production
```

🎉 **Your CodeBase QA Agent is ready!**