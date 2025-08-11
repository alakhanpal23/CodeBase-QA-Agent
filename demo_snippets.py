#!/usr/bin/env python3
"""
Demo script showing the enhanced query API with snippets.
"""

import json
import requests
import time

def demo_query_with_snippets():
    """Demo the enhanced query API with snippet functionality."""
    
    base_url = "http://localhost:8000"
    
    print("🚀 CodeBase QA Agent - Enhanced with Snippets Demo")
    print("=" * 60)
    
    # Check if server is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Server is not running. Start it with:")
            print("   uvicorn backend.app.main:app --reload")
            return
        print("✅ Server is running")
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Start it with:")
        print("   uvicorn backend.app.main:app --reload")
        return
    
    # Sample queries to demonstrate
    sample_queries = [
        {
            "question": "How does authentication work?",
            "repo_ids": ["fastapi-demo"],
            "k": 3
        },
        {
            "question": "Where are the database models defined?",
            "repo_ids": ["fastapi-demo"],
            "k": 4
        },
        {
            "question": "How are API routes structured?",
            "repo_ids": ["fastapi-demo"],
            "k": 5
        }
    ]
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\n📝 Query {i}: {query['question']}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/query", json=query, timeout=30)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Query completed in {elapsed:.2f}s")
                print(f"📊 Mode: {data.get('mode', 'unknown')}")
                print(f"⚡ Server latency: {data.get('latency_ms', 0)}ms")
                
                # Show answer
                print(f"\n💬 Answer:")
                print(data.get('answer', 'No answer provided'))
                
                # Show citations
                citations = data.get('citations', [])
                print(f"\n📚 Citations ({len(citations)}):")
                for j, citation in enumerate(citations, 1):
                    print(f"  {j}. {citation['path']}:{citation['start']}-{citation['end']} (score: {citation['score']:.2f})")
                    if citation.get('preview'):
                        preview = citation['preview'][:100] + "..." if len(citation['preview']) > 100 else citation['preview']
                        print(f"     Preview: {preview.replace(chr(10), ' ')}")
                
                # Show snippets (NEW FEATURE)
                snippets = data.get('snippets', [])
                print(f"\n🔍 Code Snippets ({len(snippets)}):")
                for j, snippet in enumerate(snippets, 1):
                    print(f"  {j}. {snippet['path']} (lines {snippet['window_start']}-{snippet['window_end']})")
                    
                    # Show first few lines of code
                    code_lines = snippet['code'].splitlines()
                    preview_lines = code_lines[:8]  # Show first 8 lines
                    
                    print("     Code:")
                    for line_num, line in enumerate(preview_lines, snippet['window_start']):
                        # Highlight the original match lines
                        marker = ">>>" if snippet['start'] <= line_num <= snippet['end'] else "   "
                        print(f"     {marker} {line_num:3d}: {line}")
                    
                    if len(code_lines) > 8:
                        print(f"     ... ({len(code_lines) - 8} more lines)")
                    print()
                
            else:
                print(f"❌ Query failed with status {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        if i < len(sample_queries):
            print("\n" + "="*60)
    
    print("\n🎉 Demo completed!")
    print("\nKey improvements with snippets:")
    print("• Users can see actual code without opening files")
    print("• Context lines help understand the code better")
    print("• Works in both mock and GPT-4 modes")
    print("• Reduces 'black box' feeling of AI responses")

def demo_api_structure():
    """Show the new API response structure."""
    
    print("\n📋 New API Response Structure")
    print("=" * 40)
    
    example_response = {
        "answer": "Authentication is handled by JWT tokens...",
        "citations": [
            {
                "path": "app/auth/jwt.py",
                "start": 42,
                "end": 67,
                "score": 0.83,
                "content": "def refresh_token(user_id): ...",
                "url": None,
                "preview": "def refresh_token(user_id):\n    # Generate new JWT token\n    ..."
            }
        ],
        "snippets": [
            {
                "path": "app/auth/jwt.py",
                "start": 42,
                "end": 67,
                "window_start": 39,
                "window_end": 70,
                "code": "# JWT token utilities\n\ndef refresh_token(user_id):\n    # Generate new JWT token\n    token = create_jwt(user_id)\n    return token\n\n# Helper functions"
            }
        ],
        "latency_ms": 245,
        "mode": "mock",
        "confidence": None
    }
    
    print(json.dumps(example_response, indent=2))

if __name__ == "__main__":
    demo_query_with_snippets()
    demo_api_structure()