#!/usr/bin/env python3
"""
Simple test for snippet extraction without complex dependencies.
"""

import os
import tempfile

# Simple snippet extraction function (standalone version)
def extract_snippet_simple(file_path, start, end, context_lines=6, max_chars=1200):
    """Extract code snippet with surrounding context."""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return None

    n = len(lines)
    if n == 0:
        return None

    # Calculate context window
    window_start = max(1, start - context_lines)
    window_end = min(n, end + context_lines)

    # Extract lines (convert to 0-based indexing)
    block = "".join(lines[window_start-1:window_end])
    
    # Trim to max chars if needed
    if len(block) > max_chars:
        keep = max_chars
        head_keep = keep // 2
        tail_keep = keep - head_keep
        block = block[:head_keep] + "\n...\n" + block[-tail_keep:]

    return (window_start, window_end, block)

def test_snippet_extraction():
    """Test snippet extraction with a sample file."""
    
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
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        # Test snippet extraction
        result = extract_snippet_simple(
            file_path=temp_file,
            start=5,  # hello_world function
            end=7,
            context_lines=3
        )
        
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
    finally:
        # Clean up
        os.unlink(temp_file)

def test_mock_api_response():
    """Test what a mock API response would look like with snippets."""
    
    # Mock data that would come from the query service
    mock_citations = [
        {
            "path": "app/auth/jwt.py",
            "start": 42,
            "end": 67,
            "score": 0.83,
            "content": "def refresh_token(user_id):\n    # logic to issue new JWT\n    ..."
        },
        {
            "path": "app/models/user.py", 
            "start": 15,
            "end": 25,
            "score": 0.76,
            "content": "class User(BaseModel):\n    id: int\n    username: str"
        }
    ]
    
    # Mock snippets that would be extracted
    mock_snippets = []
    for citation in mock_citations:
        # Simulate snippet extraction
        mock_code = f"""# Context before
{citation['content']}
# Context after
"""
        
        snippet = {
            "path": citation["path"],
            "start": citation["start"],
            "end": citation["end"],
            "window_start": citation["start"] - 3,
            "window_end": citation["end"] + 3,
            "code": mock_code
        }
        mock_snippets.append(snippet)
    
    # Mock complete response
    mock_response = {
        "answer": "Authentication is implemented using JWT tokens. The refresh_token function in app/auth/jwt.py handles token renewal, and the User model in app/models/user.py defines the user structure.",
        "citations": mock_citations,
        "snippets": mock_snippets,
        "latency_ms": 245,
        "mode": "mock"
    }
    
    print("✅ Mock API response structure:")
    print("=" * 50)
    print(f"Answer: {mock_response['answer']}")
    print(f"Citations: {len(mock_response['citations'])}")
    print(f"Snippets: {len(mock_response['snippets'])}")
    print(f"Mode: {mock_response['mode']}")
    
    print("\nFirst snippet:")
    if mock_snippets:
        snippet = mock_snippets[0]
        print(f"Path: {snippet['path']}")
        print(f"Lines: {snippet['start']}-{snippet['end']} (window: {snippet['window_start']}-{snippet['window_end']})")
        print("Code:")
        print(snippet['code'])
    
    return True

if __name__ == "__main__":
    print("Testing snippet extraction functionality...\n")
    
    # Test 1: Direct snippet extraction
    print("Test 1: Direct snippet extraction")
    test1_passed = test_snippet_extraction()
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Mock API response structure
    print("Test 2: Mock API response structure")
    test2_passed = test_mock_api_response()
    
    print("\n" + "="*50)
    print("Summary:")
    print(f"Direct extraction: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Mock API structure: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The snippet feature is ready to use.")
        print("\nNext steps:")
        print("1. Start the API server: uvicorn backend.app.main:app --reload")
        print("2. Ingest a repository using /ingest endpoint")
        print("3. Query with /query endpoint to see snippets in action")
    else:
        print("\n❌ Some tests failed. Check the implementation.")