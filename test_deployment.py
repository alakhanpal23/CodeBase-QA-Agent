#!/usr/bin/env python3
"""
Comprehensive deployment test script for CodeBase QA Agent.
"""

import requests
import json
import time
import sys
from typing import Dict, Any

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_repos_list():
    """Test repositories list endpoint."""
    print("\n🔍 Testing repositories list...")
    try:
        response = requests.get(f"{API_BASE}/repos", timeout=10)
        if response.status_code == 200:
            repos = response.json()
            print(f"✅ Repositories list: {len(repos)} repos found")
            return repos
        else:
            print(f"❌ Repositories list failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Repositories list error: {e}")
        return []

def test_ingest_repo():
    """Test repository ingestion."""
    print("\n🔍 Testing repository ingestion...")
    
    payload = {
        "source": "github",
        "url": "https://github.com/alakhanpal23/CodeBase-QA-Agent",
        "repo_id": "test-deployment-repo",
        "include_globs": ["**/*.py", "**/*.md", "**/*.js", "**/*.ts"],
        "exclude_globs": [".git/**", "node_modules/**", "__pycache__/**"]
    }
    
    try:
        print("📥 Starting ingestion (this may take a while)...")
        response = requests.post(
            f"{API_BASE}/ingest",
            json=payload,
            timeout=120  # 2 minutes timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ingestion successful:")
            print(f"   - Files processed: {data.get('files_processed', 0)}")
            print(f"   - Chunks stored: {data.get('chunks_stored', 0)}")
            print(f"   - Time taken: {data.get('elapsed_time', 0):.2f}s")
            return data
        else:
            print(f"❌ Ingestion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        return None

def test_query():
    """Test querying the codebase."""
    print("\n🔍 Testing codebase query...")
    
    payload = {
        "question": "How does the FastAPI application work? Show me the main endpoints.",
        "repo_ids": ["test-deployment-repo"],
        "k": 5
    }
    
    try:
        print("🤔 Sending query...")
        response = requests.post(
            f"{API_BASE}/query",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query successful:")
            print(f"   - Answer length: {len(data.get('answer', ''))}")
            print(f"   - Citations: {len(data.get('citations', []))}")
            print(f"   - Snippets: {len(data.get('snippets', []))}")
            print(f"   - Latency: {data.get('latency_ms', 0)}ms")
            print(f"   - Mode: {data.get('mode', 'unknown')}")
            
            # Show first part of answer
            answer = data.get('answer', '')
            if answer:
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"   - Answer preview: {preview}")
            
            return data
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None

def test_delete_repo():
    """Test repository deletion."""
    print("\n🔍 Testing repository deletion...")
    
    try:
        response = requests.delete(f"{API_BASE}/repos/test-deployment-repo", timeout=30)
        
        if response.status_code == 200:
            print("✅ Repository deleted successfully")
            return True
        else:
            print(f"❌ Deletion failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Deletion error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting CodeBase QA Agent Deployment Tests")
    print("=" * 50)
    
    # Test sequence
    tests_passed = 0
    total_tests = 5
    
    # 1. Health check
    if test_health():
        tests_passed += 1
    
    # 2. List repositories
    repos = test_repos_list()
    if repos is not None:
        tests_passed += 1
    
    # 3. Ingest repository
    ingest_result = test_ingest_repo()
    if ingest_result:
        tests_passed += 1
        
        # 4. Query repository
        query_result = test_query()
        if query_result:
            tests_passed += 1
        
        # 5. Delete repository
        if test_delete_repo():
            tests_passed += 1
    else:
        print("⏭️  Skipping query and deletion tests due to ingestion failure")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! System is ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)