# 🧪 Testing Guide - CodeBase QA Agent

## Overview

This document provides comprehensive testing instructions for the CodeBase QA Agent. Our testing suite ensures production readiness through multiple layers of validation.

## 🏗️ Test Architecture

### Test Suites

1. **Comprehensive API Tests** (`tests/test_comprehensive.py`)
   - End-to-end API functionality
   - Security testing (SQL injection, XSS, path traversal)
   - Error handling validation
   - Data validation testing
   - Repository management testing

2. **Performance Tests** (`tests/test_performance.py`)
   - Load testing with concurrent users
   - Sustained load testing
   - Memory leak detection
   - Response time benchmarking
   - Error recovery testing

3. **Frontend E2E Tests** (`tests/test_frontend_e2e.py`)
   - User interface testing with Selenium
   - Responsive design validation
   - Accessibility compliance
   - Form validation testing
   - Navigation flow testing

4. **Basic Deployment Tests** (`test_deployment.py`)
   - Smoke tests for deployment verification
   - Basic functionality validation
   - Quick health checks

## 🚀 Quick Start

### Prerequisites

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# For frontend tests (optional)
# Install Chrome and ChromeDriver
```

### Run All Tests

```bash
# Master test runner (recommended)
python run_all_tests.py

# Individual test suites
python tests/test_comprehensive.py
python tests/test_performance.py
python tests/test_frontend_e2e.py
python test_deployment.py
```

## 📋 Test Categories

### 🔒 Security Tests

**SQL Injection Protection**
```python
# Tests malicious SQL in query parameters
payload = {"question": "'; DROP TABLE users; --"}
```

**XSS Prevention**
```python
# Tests script injection attempts
payload = {"question": "<script>alert('xss')</script>"}
```

**Path Traversal Protection**
```python
# Tests directory traversal attempts
payload = {"repo_id": "../../../etc/passwd"}
```

### ⚡ Performance Tests

**Concurrent Load Testing**
- Light Load: 5 concurrent users, 10 requests each
- Medium Load: 10 concurrent users, 10 requests each
- Heavy Load: 20 concurrent users, 5 requests each

**Sustained Load Testing**
- Duration: 60 seconds
- Rate: 2 requests/second
- Monitors: Response time stability

**Memory Leak Detection**
- Runs 5 batches of 50 requests
- Monitors response time trends
- Alerts on >500ms degradation

### 🌐 Frontend Tests

**Responsive Design**
- Desktop: 1920x1080
- Tablet: 768x1024
- Mobile: 375x667

**Accessibility**
- Alt text validation
- Heading hierarchy
- Form label compliance
- Keyboard navigation

**User Flows**
- Homepage navigation
- Repository addition
- Chat interface interaction
- Error state handling

## 📊 Test Reports

### Automated Reporting

Tests generate comprehensive reports in `test_reports/`:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_duration": 120.5,
  "summary": {
    "total_suites": 4,
    "passed_suites": 4,
    "failed_suites": 0,
    "required_passed": 3,
    "required_total": 3
  }
}
```

### Success Criteria

**Production Ready Requirements:**
- ✅ All required test suites pass
- ✅ Security tests pass 100%
- ✅ Performance tests meet SLA:
  - Response time < 2s (95th percentile)
  - Success rate > 95%
  - Memory stable over time
- ✅ Frontend accessibility compliance
- ✅ Error handling graceful

## 🎯 Test Scenarios

### Repository Management
```bash
# Valid repository ingestion
POST /ingest
{
  "source": "github",
  "url": "https://github.com/user/repo",
  "repo_id": "test-repo"
}

# Invalid repository handling
POST /ingest
{
  "source": "github",
  "url": "https://github.com/nonexistent/repo"
}
```

### Query Testing
```bash
# Successful query
POST /query
{
  "question": "How does authentication work?",
  "repo_ids": ["test-repo"],
  "k": 5
}

# Edge cases
- Empty question
- Non-existent repository
- Very long questions
- Special characters
```

### Error Scenarios
```bash
# Network timeouts
# Invalid JSON payloads
# Missing required fields
# Malformed requests
# Rate limit exceeded
```

## 🔧 Debugging Tests

### Common Issues

**Backend Not Running**
```bash
# Start backend first
cd backend
export OPENAI_API_KEY="dummy-key-for-testing"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Not Accessible**
```bash
# Start frontend
cd frontend
npm run dev
```

**Selenium WebDriver Issues**
```bash
# Install ChromeDriver
# On macOS: brew install chromedriver
# On Ubuntu: apt-get install chromium-chromedriver
```

### Test Environment Variables

```bash
# API endpoints
API_BASE="http://localhost:8000"
FRONTEND_BASE="http://localhost:3001"

# Test configuration
TEST_TIMEOUT=300  # 5 minutes per suite
CONCURRENT_USERS=20
LOAD_TEST_DURATION=60
```

## 📈 Performance Benchmarks

### Expected Performance

**API Response Times:**
- Health check: < 100ms
- Repository list: < 500ms
- Query processing: < 2000ms
- Repository ingestion: < 60s

**Concurrent Load:**
- 20 concurrent users: > 90% success rate
- Response time degradation: < 50%
- Memory usage: Stable over time

**Frontend Performance:**
- Page load: < 3s
- Navigation: < 1s
- Form submission: < 5s

## 🚨 Monitoring & Alerts

### Health Checks

```bash
# Continuous monitoring
while true; do
  curl -f http://localhost:8000/health || echo "ALERT: Backend down"
  sleep 30
done
```

### Performance Monitoring

```bash
# Response time monitoring
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health
```

### Log Analysis

```bash
# Backend logs
tail -f backend/logs/app.log | grep ERROR

# Frontend logs
# Check browser console for errors
```

## 🎉 Production Readiness Checklist

### Before Deployment
- [ ] All required tests pass
- [ ] Performance benchmarks met
- [ ] Security tests pass
- [ ] Error handling validated
- [ ] Load testing completed
- [ ] Frontend accessibility verified

### After Deployment
- [ ] Health checks operational
- [ ] Monitoring dashboards active
- [ ] Error tracking configured
- [ ] Performance metrics baseline
- [ ] Backup procedures tested

## 📞 Support

### Test Failures

1. **Check Prerequisites**: Ensure all services are running
2. **Review Logs**: Check test output for specific errors
3. **Environment**: Verify environment variables
4. **Dependencies**: Confirm all packages installed
5. **Network**: Check connectivity between services

### Performance Issues

1. **Resource Usage**: Monitor CPU/memory during tests
2. **Database**: Check database performance
3. **Network**: Verify network latency
4. **Concurrency**: Adjust concurrent user limits
5. **Timeouts**: Increase timeout values if needed

---

**Happy Testing! 🧪✨**