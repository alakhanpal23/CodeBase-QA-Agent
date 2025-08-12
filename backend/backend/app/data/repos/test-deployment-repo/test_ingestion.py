#!/usr/bin/env python3
"""
Test script to verify ingestion functionality.
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print("❌ Backend health check failed")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

def test_repos_endpoint():
    """Test repos endpoint."""
    try:
        response = requests.get(f"{API_BASE}/repos")
        print(f"Repos endpoint: {response.status_code}")
        if response.status_code == 200:
            repos = response.json()
            print(f"✅ Found {len(repos)} repositories")
            return True
        else:
            print(f"❌ Repos endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Repos endpoint error: {e}")
        return False

def test_ingestion():
    """Test repository ingestion."""
    try:
        # Test with a small public repository
        payload = {
            "source": "github",
            "url": "https://github.com/octocat/Hello-World",
            "repo_id": "hello-world-test",
            "include_globs": ["**/*.md", "**/*.txt"],
            "exclude_globs": [".git/**"]
        }
        
        print("Testing ingestion...")
        response = requests.post(
            f"{API_BASE}/ingest",
            json=payload,
            timeout=60
        )
        
        print(f"Ingestion response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ingestion successful!")
            print(f"   Files processed: {result.get('files_processed', 0)}")
            print(f"   Chunks stored: {result.get('chunks_stored', 0)}")
            print(f"   Time taken: {result.get('elapsed_time', 0):.2f}s")
            return True
        else:
            print(f"❌ Ingestion failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing CodeBase QA Agent Backend")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health),
        ("Repos Endpoint", test_repos_endpoint),
        ("Repository Ingestion", test_ingestion),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        print("-" * 20)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The backend is working correctly.")
        print("\n✨ You can now:")
        print("1. Visit http://localhost:3001 to use the frontend")
        print("2. Add repositories via the UI")
        print("3. Query your codebase with natural language")
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()