#!/usr/bin/env python3
"""
Quick test script for snippet functionality.
"""

import os
import sys
import tempfile
import json
import requests

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.snippets import extract_snippet
from backend.app.core.config import settings

def test_snippet_extraction():
    """Test snippet extraction with a sample file."""
    
    # Create a temporary test file
    test_content = """# Sample Python file
import os
import sys

def hello_world():
    print("Hello, World!")
    return "success"

class TestClass:
    def __init__(self):
        self.name = "test"
    
    def method1(self):
        return self.name
    
    def method2(self):
        # This is a comment
        value = 42
        return value * 2

if __name__ == "__main__":
    hello_world()
"""
    
    # Create temp directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override settings for test
        original_repos_dir = settings.repos_dir
        settings.repos_dir = temp_dir
        
        # Create repo directory and file
        repo_dir = os.path.join(temp_dir, "test-repo")
        os.makedirs(repo_dir, exist_ok=True)
        
        test_file = os.path.join(repo_dir, "sample.py")
        with open(test_file, "w") as f:
            f.write(test_content)
        
        # Test snippet extraction
        result = extract_snippet(
            repo_id="test-repo",
            rel_path="sample.py",
            start=5,  # hello_world function
            end=7,
            context_lines=3
        )
        
        # Restore original setting
        settings.repos_dir = original_repos_dir
        
        if result:
            window_start, window_end, code = result
            print("✅ Snippet extraction test passed!")
            print(f"Window: lines {window_start}-{window_end}")
            print("Code snippet:")
            print("=" * 40)
            print(code)
            print("=" * 40)
            return True
        else:
            print("❌ Snippet extraction test failed!")
            return False

def test_api_with_snippets():
    """Test the API endpoint to see if snippets are included."""
    
    # This assumes the API is running on localhost:8000
    url = "http://localhost:8000/query"
    
    payload = {
        "question": "How does authentication work?",
        "repo_ids": ["test-repo"],
        "k": 3
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API test passed!")
            print(f"Answer: {data.get('answer', 'No answer')}")
            print(f"Citations: {len(data.get('citations', []))}")
            print(f"Snippets: {len(data.get('snippets', []))}")
            
            # Show first snippet if available
            snippets = data.get('snippets', [])
            if snippets:
                snippet = snippets[0]
                print("\nFirst snippet:")
                print(f"Path: {snippet['path']}")
                print(f"Lines: {snippet['start']}-{snippet['end']} (window: {snippet['window_start']}-{snippet['window_end']})")
                print("Code:")
                print(snippet['code'][:200] + "..." if len(snippet['code']) > 200 else snippet['code'])
            
            return True
        else:
            print(f"❌ API test failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API test failed: {e}")
        print("Make sure the API server is running on localhost:8000")
        return False

if __name__ == "__main__":
    print("Testing snippet extraction functionality...\n")
    
    # Test 1: Direct snippet extraction
    print("Test 1: Direct snippet extraction")
    test1_passed = test_snippet_extraction()
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: API integration
    print("Test 2: API integration (requires running server)")
    test2_passed = test_api_with_snippets()
    
    print("\n" + "="*50)
    print("Summary:")
    print(f"Direct extraction: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"API integration: {'✅ PASS' if test2_passed else '❌ FAIL'}")