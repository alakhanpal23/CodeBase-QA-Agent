#!/usr/bin/env python3
"""
Quick Performance Test - Fast validation of core functionality
"""

import requests
import time
import sys

API_BASE = "http://localhost:8000"

def quick_test():
    """Run quick performance tests"""
    print("⚡ Quick Performance Test")
    print("=" * 30)
    
    tests_passed = 0
    total_tests = 4
    
    # 1. Health check
    print("🔍 Health check...", end=" ")
    start = time.time()
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        duration = (time.time() - start) * 1000
        if response.status_code == 200:
            print(f"✅ {duration:.0f}ms")
            tests_passed += 1
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ {e}")
    
    # 2. Repository list
    print("📚 Repository list...", end=" ")
    start = time.time()
    try:
        response = requests.get(f"{API_BASE}/repos", timeout=3)
        duration = (time.time() - start) * 1000
        if response.status_code == 200:
            repos = response.json()
            print(f"✅ {len(repos)} repos, {duration:.0f}ms")
            tests_passed += 1
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ {e}")
    
    # 3. Quick query (if repos exist)
    print("🤖 Quick query...", end=" ")
    start = time.time()
    try:
        payload = {
            "question": "How does this work?",
            "repo_ids": ["test-deployment-repo"],
            "k": 2  # Only 2 chunks for speed
        }
        response = requests.post(f"{API_BASE}/query", json=payload, timeout=5)
        duration = (time.time() - start) * 1000
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {len(data.get('citations', []))} citations, {duration:.0f}ms")
            tests_passed += 1
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ {e}")
    
    # 4. Stats endpoint
    print("📊 System stats...", end=" ")
    start = time.time()
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=2)
        duration = (time.time() - start) * 1000
        if response.status_code == 200:
            print(f"✅ {duration:.0f}ms")
            tests_passed += 1
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ {e}")
    
    # Summary
    print("=" * 30)
    print(f"🎯 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🚀 System is fast and responsive!")
        return 0
    else:
        print("⚠️  Some performance issues detected")
        return 1

if __name__ == "__main__":
    exit_code = quick_test()
    sys.exit(exit_code)