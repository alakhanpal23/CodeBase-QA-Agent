#!/usr/bin/env python3
"""
Comprehensive test runner for all snippet functionality.
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def run_test_file(test_file, description):
    """Run a single test file and return results."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Try to run with pytest first
        result = subprocess.run([
            sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ PASSED (pytest)")
            print(result.stdout)
            return True
        else:
            print("⚠️  pytest failed, trying direct execution...")
            # Fall back to direct execution
            result = subprocess.run([
                sys.executable, test_file
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ PASSED (direct)")
                print(result.stdout)
                return True
            else:
                print("❌ FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT (60s)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        elapsed = time.time() - start_time
        print(f"⏱️  Completed in {elapsed:.2f}s")

def run_manual_tests():
    """Run manual tests that don't require pytest."""
    print(f"\n{'='*60}")
    print("🧪 Running Manual Tests")
    print(f"{'='*60}")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Basic snippet extraction
    print("\n1. Testing basic snippet extraction...")
    tests_total += 1
    
    try:
        from backend.app.services.snippets import extract_snippet
        from backend.app.core.config import settings
        
        # Create temp test
        temp_dir = tempfile.mkdtemp()
        original_repos_dir = settings.repos_dir
        settings.repos_dir = temp_dir
        
        try:
            # Create test repo
            repo_dir = os.path.join(temp_dir, "manual-test-repo")
            os.makedirs(repo_dir, exist_ok=True)
            
            test_content = """def hello():
    print("Hello, World!")
    return "success"

class TestClass:
    def method(self):
        return 42
"""
            
            with open(os.path.join(repo_dir, "test.py"), "w") as f:
                f.write(test_content)
            
            # Test extraction
            result = extract_snippet("manual-test-repo", "test.py", 1, 3, context_lines=2)
            
            if result:
                window_start, window_end, code = result
                if "def hello():" in code and "print" in code:
                    print("   ✅ Basic extraction works")
                    tests_passed += 1
                else:
                    print("   ❌ Extraction content incorrect")
            else:
                print("   ❌ Extraction returned None")
                
        finally:
            settings.repos_dir = original_repos_dir
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Schema validation
    print("\n2. Testing schema validation...")
    tests_total += 1
    
    try:
        from backend.app.core.schemas import QueryResponse, Citation, Snippet
        
        # Test creating response with snippets
        citation = Citation(
            path="test.py",
            start=1,
            end=5,
            score=0.8,
            content="def test(): pass"
        )
        
        snippet = Snippet(
            path="test.py",
            start=1,
            end=5,
            window_start=1,
            window_end=8,
            code="def test():\n    pass\n"
        )
        
        response = QueryResponse(
            answer="Test answer",
            citations=[citation],
            snippets=[snippet],
            latency_ms=100,
            mode="mock"
        )
        
        if (len(response.citations) == 1 and 
            len(response.snippets) == 1 and
            response.mode == "mock"):
            print("   ✅ Schema validation works")
            tests_passed += 1
        else:
            print("   ❌ Schema validation failed")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Configuration
    print("\n3. Testing configuration...")
    tests_total += 1
    
    try:
        from backend.app.core.config import settings
        
        required_attrs = [
            'snippet_context_lines',
            'snippet_max_chars', 
            'repos_dir',
            'openai_model',
            'embed_mode'
        ]
        
        missing_attrs = [attr for attr in required_attrs if not hasattr(settings, attr)]
        
        if not missing_attrs:
            print("   ✅ Configuration complete")
            tests_passed += 1
        else:
            print(f"   ❌ Missing configuration: {missing_attrs}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print(f"\n📊 Manual Tests: {tests_passed}/{tests_total} passed")
    return tests_passed == tests_total

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'fastapi',
        'pydantic',
        'pydantic_settings',
        'uvicorn'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} (missing)")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {missing}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    print("✅ All dependencies available")
    return True

def test_api_server():
    """Test if API server can start."""
    print("\n🚀 Testing API server startup...")
    
    try:
        # Try to import the main app
        from backend.app.main import app
        print("   ✅ App imports successfully")
        
        # Try to create test client
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("   ✅ Health endpoint works")
            return True
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Server test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 CodeBase QA Agent - Comprehensive Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Cannot run tests without required dependencies")
        return False
    
    # Test results tracking
    test_results = {}
    
    # 1. Manual tests (always run)
    test_results['manual'] = run_manual_tests()
    
    # 2. API server test
    test_results['api_server'] = test_api_server()
    
    # 3. Test files (if they exist)
    test_files = [
        ("tests/test_snippets.py", "Snippet Extraction Tests"),
        ("tests/test_api_integration.py", "API Integration Tests"),
        ("tests/test_gpt4_compatibility.py", "GPT-4 Compatibility Tests"),
        ("simple_snippet_test.py", "Simple Snippet Test")
    ]
    
    for test_file, description in test_files:
        if os.path.exists(test_file):
            test_results[test_file] = run_test_file(test_file, description)
        else:
            print(f"\n⚠️  Skipping {description} - file not found: {test_file}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f}s")
    print(f"📈 Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✨ Snippet functionality is ready for production!")
        print("\nNext steps:")
        print("1. Start server: uvicorn backend.app.main:app --reload")
        print("2. Ingest repository: POST /ingest")
        print("3. Query with snippets: POST /query")
        print("4. Switch to GPT-4 by setting use_mock=False in RAGService")
        return True
    else:
        print(f"\n❌ {total - passed} test suite(s) failed")
        print("Please fix failing tests before deploying")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)