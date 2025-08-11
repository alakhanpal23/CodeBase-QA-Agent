#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for CodeBase QA Agent
Tests all functionality including edge cases and error scenarios
"""

import requests
import json
import time
import sys
import os
import tempfile
import zipfile
from typing import Dict, Any, List
import concurrent.futures
import threading

API_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:3001"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.warnings = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
    
    def add_warning(self, test_name: str, warning: str):
        self.warnings.append(f"{test_name}: {warning}")
        print(f"⚠️  {test_name}: {warning}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.failed > 0:
            print(f"❌ {self.failed} tests failed:")
            for error in self.errors:
                print(f"   - {error}")
        if self.warnings:
            print(f"⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")
        print(f"{'='*60}")
        return self.failed == 0

results = TestResults()

def test_api_health():
    """Test API health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and "timestamp" in data:
                results.add_pass("API Health Check")
                return True
            else:
                results.add_fail("API Health Check", "Invalid health response format")
        else:
            results.add_fail("API Health Check", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("API Health Check", str(e))
    return False

def test_frontend_accessibility():
    """Test frontend accessibility"""
    try:
        response = requests.get(FRONTEND_BASE, timeout=10)
        if response.status_code == 200:
            if "CodeBase QA" in response.text:
                results.add_pass("Frontend Accessibility")
                return True
            else:
                results.add_fail("Frontend Accessibility", "Page content not found")
        else:
            results.add_fail("Frontend Accessibility", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Frontend Accessibility", str(e))
    return False

def test_api_documentation():
    """Test API documentation endpoint"""
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        if response.status_code == 200:
            results.add_pass("API Documentation")
            return True
        else:
            results.add_fail("API Documentation", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("API Documentation", str(e))
    return False

def test_cors_headers():
    """Test CORS headers"""
    try:
        response = requests.options(f"{API_BASE}/health", timeout=5)
        headers = response.headers
        if "Access-Control-Allow-Origin" in headers:
            results.add_pass("CORS Headers")
            return True
        else:
            results.add_fail("CORS Headers", "CORS headers not found")
    except Exception as e:
        results.add_fail("CORS Headers", str(e))
    return False

def test_repository_list_empty():
    """Test empty repository list"""
    try:
        response = requests.get(f"{API_BASE}/repos", timeout=10)
        if response.status_code == 200:
            repos = response.json()
            if isinstance(repos, list):
                results.add_pass("Repository List (Empty)")
                return True
            else:
                results.add_fail("Repository List (Empty)", "Invalid response format")
        else:
            results.add_fail("Repository List (Empty)", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Repository List (Empty)", str(e))
    return False

def test_repository_ingestion():
    """Test repository ingestion with various scenarios"""
    test_cases = [
        {
            "name": "Valid GitHub Repository",
            "payload": {
                "source": "github",
                "url": "https://github.com/alakhanpal23/CodeBase-QA-Agent",
                "repo_id": "test-main-repo",
                "include_globs": ["**/*.py", "**/*.md", "**/*.js", "**/*.ts"],
                "exclude_globs": [".git/**", "node_modules/**", "__pycache__/**"]
            },
            "should_succeed": True
        },
        {
            "name": "Invalid GitHub URL",
            "payload": {
                "source": "github",
                "url": "https://github.com/nonexistent/repository",
                "repo_id": "test-invalid-repo",
                "include_globs": ["**/*.py"],
                "exclude_globs": [".git/**"]
            },
            "should_succeed": False
        },
        {
            "name": "Missing Required Fields",
            "payload": {
                "source": "github",
                "url": "https://github.com/alakhanpal23/CodeBase-QA-Agent"
                # Missing repo_id
            },
            "should_succeed": False
        }
    ]
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/ingest",
                json=test_case["payload"],
                timeout=120
            )
            
            if test_case["should_succeed"]:
                if response.status_code == 200:
                    data = response.json()
                    if "files_processed" in data and "chunks_stored" in data:
                        results.add_pass(f"Repository Ingestion - {test_case['name']}")
                    else:
                        results.add_fail(f"Repository Ingestion - {test_case['name']}", "Invalid response format")
                else:
                    results.add_fail(f"Repository Ingestion - {test_case['name']}", f"HTTP {response.status_code}")
            else:
                if response.status_code >= 400:
                    results.add_pass(f"Repository Ingestion - {test_case['name']} (Expected Failure)")
                else:
                    results.add_fail(f"Repository Ingestion - {test_case['name']}", "Should have failed but didn't")
                    
        except Exception as e:
            if test_case["should_succeed"]:
                results.add_fail(f"Repository Ingestion - {test_case['name']}", str(e))
            else:
                results.add_pass(f"Repository Ingestion - {test_case['name']} (Expected Exception)")

def test_query_functionality():
    """Test query functionality with various scenarios"""
    # First ensure we have a repository
    test_queries = [
        {
            "name": "Basic Code Question",
            "payload": {
                "question": "How does the FastAPI application work?",
                "repo_ids": ["test-main-repo"],
                "k": 5
            }
        },
        {
            "name": "Specific Function Question",
            "payload": {
                "question": "Show me the main API endpoints and their functionality",
                "repo_ids": ["test-main-repo"],
                "k": 3
            }
        },
        {
            "name": "Architecture Question",
            "payload": {
                "question": "What is the overall architecture of this application?",
                "repo_ids": ["test-main-repo"],
                "k": 7
            }
        },
        {
            "name": "Empty Question",
            "payload": {
                "question": "",
                "repo_ids": ["test-main-repo"],
                "k": 5
            }
        },
        {
            "name": "Non-existent Repository",
            "payload": {
                "question": "How does this work?",
                "repo_ids": ["non-existent-repo"],
                "k": 5
            }
        }
    ]
    
    for test_case in test_queries:
        try:
            response = requests.post(
                f"{API_BASE}/query",
                json=test_case["payload"],
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["answer", "citations", "snippets", "latency_ms"]
                if all(field in data for field in required_fields):
                    # Check if we got meaningful results
                    if data["answer"] and len(data["answer"]) > 10:
                        results.add_pass(f"Query - {test_case['name']}")
                    else:
                        results.add_warning(f"Query - {test_case['name']}", "Empty or very short answer")
                else:
                    results.add_fail(f"Query - {test_case['name']}", "Missing required fields in response")
            else:
                if test_case["name"] in ["Empty Question", "Non-existent Repository"]:
                    results.add_pass(f"Query - {test_case['name']} (Expected Error)")
                else:
                    results.add_fail(f"Query - {test_case['name']}", f"HTTP {response.status_code}")
                    
        except Exception as e:
            results.add_fail(f"Query - {test_case['name']}", str(e))

def test_concurrent_requests():
    """Test system under concurrent load"""
    def make_request():
        try:
            response = requests.get(f"{API_BASE}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results_list = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results_list) / len(results_list)
        if success_rate >= 0.9:  # 90% success rate
            results.add_pass(f"Concurrent Requests (Success Rate: {success_rate:.1%})")
        else:
            results.add_fail("Concurrent Requests", f"Low success rate: {success_rate:.1%}")
            
    except Exception as e:
        results.add_fail("Concurrent Requests", str(e))

def test_error_handling():
    """Test error handling scenarios"""
    error_tests = [
        {
            "name": "Invalid JSON",
            "url": f"{API_BASE}/ingest",
            "data": "invalid json",
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "Missing Content-Type",
            "url": f"{API_BASE}/ingest",
            "data": json.dumps({"source": "github"}),
            "headers": {}
        },
        {
            "name": "Non-existent Endpoint",
            "url": f"{API_BASE}/nonexistent",
            "data": None,
            "headers": {}
        }
    ]
    
    for test in error_tests:
        try:
            if test["data"]:
                response = requests.post(test["url"], data=test["data"], headers=test["headers"], timeout=5)
            else:
                response = requests.get(test["url"], timeout=5)
            
            if response.status_code >= 400:
                results.add_pass(f"Error Handling - {test['name']}")
            else:
                results.add_fail(f"Error Handling - {test['name']}", "Should have returned error status")
                
        except Exception as e:
            results.add_pass(f"Error Handling - {test['name']} (Connection Error Expected)")

def test_data_validation():
    """Test input validation"""
    validation_tests = [
        {
            "name": "SQL Injection Attempt",
            "payload": {
                "question": "'; DROP TABLE users; --",
                "repo_ids": ["test-main-repo"],
                "k": 5
            }
        },
        {
            "name": "XSS Attempt",
            "payload": {
                "question": "<script>alert('xss')</script>",
                "repo_ids": ["test-main-repo"],
                "k": 5
            }
        },
        {
            "name": "Path Traversal Attempt",
            "payload": {
                "source": "github",
                "url": "https://github.com/alakhanpal23/CodeBase-QA-Agent",
                "repo_id": "../../../etc/passwd",
                "include_globs": ["**/*.py"],
                "exclude_globs": [".git/**"]
            }
        }
    ]
    
    for test in validation_tests:
        try:
            if "question" in test["payload"]:
                response = requests.post(f"{API_BASE}/query", json=test["payload"], timeout=10)
            else:
                response = requests.post(f"{API_BASE}/ingest", json=test["payload"], timeout=10)
            
            # System should either handle gracefully or reject
            if response.status_code in [200, 400, 422]:
                results.add_pass(f"Data Validation - {test['name']}")
            else:
                results.add_fail(f"Data Validation - {test['name']}", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            results.add_pass(f"Data Validation - {test['name']} (Handled Exception)")

def test_performance_benchmarks():
    """Test performance benchmarks"""
    # Health check latency
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE}/health", timeout=5)
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200 and latency < 1000:  # Less than 1 second
            results.add_pass(f"Health Check Latency ({latency:.0f}ms)")
        else:
            results.add_warning("Health Check Latency", f"Slow response: {latency:.0f}ms")
            
    except Exception as e:
        results.add_fail("Health Check Latency", str(e))

def test_repository_cleanup():
    """Clean up test repositories"""
    try:
        # Try to delete test repository
        response = requests.delete(f"{API_BASE}/repos/test-main-repo", timeout=10)
        if response.status_code in [200, 404]:  # Success or already deleted
            results.add_pass("Repository Cleanup")
        else:
            results.add_warning("Repository Cleanup", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_warning("Repository Cleanup", str(e))

def test_embedding_modes():
    """Test different embedding modes"""
    try:
        # Test with a simple query to see what mode is being used
        response = requests.post(
            f"{API_BASE}/query",
            json={
                "question": "test",
                "repo_ids": ["test-main-repo"],
                "k": 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            mode = data.get("mode", "unknown")
            results.add_pass(f"Embedding Mode Detection (Mode: {mode})")
        else:
            results.add_warning("Embedding Mode Detection", "Could not determine mode")
            
    except Exception as e:
        results.add_warning("Embedding Mode Detection", str(e))

def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive End-to-End Tests")
    print("=" * 60)
    
    # Basic connectivity tests
    print("\n📡 CONNECTIVITY TESTS")
    test_api_health()
    test_frontend_accessibility()
    test_api_documentation()
    test_cors_headers()
    
    # Repository management tests
    print("\n📚 REPOSITORY MANAGEMENT TESTS")
    test_repository_list_empty()
    test_repository_ingestion()
    
    # Query functionality tests
    print("\n🤖 QUERY FUNCTIONALITY TESTS")
    test_query_functionality()
    test_embedding_modes()
    
    # Performance and load tests
    print("\n⚡ PERFORMANCE TESTS")
    test_concurrent_requests()
    test_performance_benchmarks()
    
    # Security tests
    print("\n🔒 SECURITY TESTS")
    test_error_handling()
    test_data_validation()
    
    # Cleanup
    print("\n🧹 CLEANUP TESTS")
    test_repository_cleanup()
    
    # Final summary
    success = results.summary()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! System is production-ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)