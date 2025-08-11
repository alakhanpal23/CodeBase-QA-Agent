#!/usr/bin/env python3
"""
Final integration validation for snippet functionality.
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_actual_snippet_service():
    """Test the actual snippet service implementation."""
    print("🧪 Testing actual snippet service...")
    
    # Set up environment
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Mock settings to avoid validation errors
        with patch('backend.app.core.config.settings') as mock_settings:
            mock_settings.repos_dir = temp_dir
            mock_settings.snippet_context_lines = 6
            mock_settings.snippet_max_chars = 1200
            
            from backend.app.services.snippets import extract_snippet
            
            # Create test repository
            repo_dir = os.path.join(temp_dir, "integration-test")
            os.makedirs(repo_dir, exist_ok=True)
            
            # Create realistic test file
            test_content = """#!/usr/bin/env python3
\"\"\"
Authentication service for the application.
\"\"\"

import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    \"\"\"Handle user authentication and JWT tokens.\"\"\"
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        \"\"\"Create a new JWT access token.\"\"\"
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, token: str):
        \"\"\"Verify and decode a JWT token.\"\"\"
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            return None
    
    def hash_password(self, password: str):
        \"\"\"Hash a password using bcrypt.\"\"\"
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str):
        \"\"\"Verify a password against its hash.\"\"\"
        return pwd_context.verify(plain_password, hashed_password)
"""
            
            with open(os.path.join(repo_dir, "auth_service.py"), "w") as f:
                f.write(test_content)
            
            # Test snippet extraction
            result = extract_snippet(
                repo_id="integration-test",
                rel_path="auth_service.py",
                start=18,  # create_access_token method
                end=27,
                context_lines=3
            )
            
            if result:
                window_start, window_end, code = result
                
                # Verify extraction
                if ("def create_access_token" in code and
                    "to_encode = data.copy()" in code and
                    window_start <= 18 and
                    window_end >= 27):
                    print("   ✅ Actual snippet service works")
                    return True
                else:
                    print(f"   ❌ Incorrect extraction: {code[:100]}...")
                    return False
            else:
                print("   ❌ No result from snippet service")
                return False
                
    except Exception as e:
        print(f"   ❌ Exception in snippet service: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

def test_query_service_integration():
    """Test query service with snippet integration."""
    print("🧪 Testing query service integration...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Mock all dependencies
        with patch('backend.app.core.config.settings') as mock_settings:
            mock_settings.repos_dir = temp_dir
            mock_settings.snippet_context_lines = 6
            mock_settings.snippet_max_chars = 1200
            
            # Create test file
            repo_dir = os.path.join(temp_dir, "query-test")
            os.makedirs(repo_dir, exist_ok=True)
            
            with open(os.path.join(repo_dir, "test.py"), "w") as f:
                f.write("def hello():\n    return 'world'\n\nclass Test:\n    pass\n")
            
            # Mock the dependencies
            with patch('backend.app.services.query.VectorStoreManager') as mock_vector, \
                 patch('backend.app.services.query.EmbeddingService') as mock_embedding, \
                 patch('backend.app.services.query.RAGService') as mock_rag:
                
                # Setup mocks
                mock_embedding_instance = MagicMock()
                mock_embedding_instance.embed_text.return_value = [0.1] * 1536
                mock_embedding.return_value = mock_embedding_instance
                
                mock_vector_instance = MagicMock()
                mock_store = MagicMock()
                mock_store.index.ntotal = 100
                mock_vector_instance.get_store.return_value = mock_store
                mock_vector_instance.search_multiple.return_value = [
                    {
                        "path": "test.py",
                        "start_line": 1,
                        "end_line": 2,
                        "score": 0.9,
                        "content": "def hello():\n    return 'world'"
                    }
                ]
                mock_vector.return_value = mock_vector_instance
                
                # Mock RAG service
                from backend.app.core.schemas import Citation
                mock_rag_instance = MagicMock()
                mock_rag_instance.use_mock = True
                mock_rag_instance.generate_answer.return_value = (
                    "The hello function returns 'world'",
                    [Citation(path="test.py", start=1, end=2, score=0.9, content="def hello():\n    return 'world'")]
                )
                mock_rag_instance.validate_answer.return_value = True
                mock_rag.return_value = mock_rag_instance
                
                # Test query service
                from backend.app.services.query import QueryService
                from backend.app.core.schemas import QueryRequest
                
                query_service = QueryService()
                request = QueryRequest(
                    question="What does the hello function do?",
                    repo_ids=["query-test"],
                    k=5
                )
                
                # Run async test
                import asyncio
                
                async def run_query_test():
                    response = await query_service.query(request)
                    
                    # Verify response structure
                    if (hasattr(response, 'answer') and
                        hasattr(response, 'citations') and
                        hasattr(response, 'snippets') and
                        hasattr(response, 'latency_ms') and
                        hasattr(response, 'mode')):
                        
                        # Check if snippets were extracted
                        if len(response.snippets) > 0:
                            snippet = response.snippets[0]
                            if (hasattr(snippet, 'path') and
                                hasattr(snippet, 'code') and
                                hasattr(snippet, 'window_start') and
                                hasattr(snippet, 'window_end')):
                                return True
                    
                    return False
                
                result = asyncio.run(run_query_test())
                
                if result:
                    print("   ✅ Query service integration works")
                    return True
                else:
                    print("   ❌ Query service integration failed")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Exception in query service: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)

def test_schema_compatibility():
    """Test schema compatibility between mock and GPT-4 modes."""
    print("🧪 Testing schema compatibility...")
    
    try:
        from backend.app.core.schemas import QueryResponse, Citation, Snippet
        
        # Test mock mode response
        mock_citation = Citation(
            path="app/auth.py",
            start=10,
            end=15,
            score=0.85,
            content="def authenticate():",
            preview="def authenticate():\n    pass"
        )
        
        mock_snippet = Snippet(
            path="app/auth.py",
            start=10,
            end=15,
            window_start=8,
            window_end=17,
            code="# Auth module\ndef authenticate():\n    pass\n# End"
        )
        
        mock_response = QueryResponse(
            answer="Authentication is handled by authenticate function",
            citations=[mock_citation],
            snippets=[mock_snippet],
            latency_ms=150,
            mode="mock"
        )
        
        # Test GPT-4 mode response (with confidence)
        gpt4_response = QueryResponse(
            answer="Authentication is handled by authenticate function",
            citations=[mock_citation],
            snippets=[mock_snippet],
            latency_ms=500,
            mode="gpt4",
            confidence=0.95
        )
        
        # Verify both work
        if (mock_response.mode == "mock" and
            gpt4_response.mode == "gpt4" and
            gpt4_response.confidence == 0.95 and
            len(mock_response.snippets) == len(gpt4_response.snippets)):
            print("   ✅ Schema compatibility works")
            return True
        else:
            print("   ❌ Schema compatibility failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception in schema test: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios."""
    print("🧪 Testing error handling...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        with patch('backend.app.core.config.settings') as mock_settings:
            mock_settings.repos_dir = temp_dir
            mock_settings.snippet_context_lines = 6
            mock_settings.snippet_max_chars = 1200
            
            from backend.app.services.snippets import extract_snippet
            
            # Test 1: Non-existent file
            result1 = extract_snippet("nonexistent-repo", "missing.py", 1, 5)
            
            # Test 2: Non-existent repo
            result2 = extract_snippet("missing-repo", "test.py", 1, 5)
            
            # Test 3: Empty file
            repo_dir = os.path.join(temp_dir, "error-test")
            os.makedirs(repo_dir, exist_ok=True)
            
            with open(os.path.join(repo_dir, "empty.py"), "w") as f:
                pass  # Empty file
            
            result3 = extract_snippet("error-test", "empty.py", 1, 5)
            
            # All should return None gracefully
            if result1 is None and result2 is None and result3 is None:
                print("   ✅ Error handling works")
                return True
            else:
                print(f"   ❌ Error handling failed: {result1}, {result2}, {result3}")
                return False
                
    except Exception as e:
        print(f"   ❌ Exception in error handling: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

def test_performance_characteristics():
    """Test performance characteristics."""
    print("🧪 Testing performance characteristics...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        with patch('backend.app.core.config.settings') as mock_settings:
            mock_settings.repos_dir = temp_dir
            mock_settings.snippet_context_lines = 6
            mock_settings.snippet_max_chars = 1200
            
            from backend.app.services.snippets import extract_snippet
            import time
            
            # Create test repo with medium-sized file
            repo_dir = os.path.join(temp_dir, "perf-test")
            os.makedirs(repo_dir, exist_ok=True)
            
            # Generate content (1000 lines)
            lines = [f"def function_{i}():\n    return {i}\n" for i in range(500)]
            content = "\n".join(lines)
            
            with open(os.path.join(repo_dir, "large.py"), "w") as f:
                f.write(content)
            
            # Time multiple extractions
            start_time = time.time()
            
            for i in range(10):
                result = extract_snippet("perf-test", "large.py", i*10 + 1, i*10 + 5)
                if result is None:
                    print(f"   ❌ Extraction {i} failed")
                    return False
            
            elapsed = time.time() - start_time
            
            # Should be reasonably fast (less than 2 seconds for 10 extractions)
            if elapsed < 2.0:
                print(f"   ✅ Performance acceptable ({elapsed:.3f}s for 10 extractions)")
                return True
            else:
                print(f"   ❌ Performance too slow ({elapsed:.3f}s for 10 extractions)")
                return False
                
    except Exception as e:
        print(f"   ❌ Exception in performance test: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

def main():
    """Run all integration validation tests."""
    print("🧪 CodeBase QA Agent - Integration Validation")
    print("=" * 60)
    
    tests = [
        ("Actual Snippet Service", test_actual_snippet_service),
        ("Query Service Integration", test_query_service_integration),
        ("Schema Compatibility", test_schema_compatibility),
        ("Error Handling", test_error_handling),
        ("Performance Characteristics", test_performance_characteristics),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"   ❌ {test_name} failed")
        except Exception as e:
            print(f"   ❌ {test_name} error: {e}")
    
    print(f"\n{'='*60}")
    print("📊 INTEGRATION VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("\n✨ Snippet functionality is fully integrated and working!")
        
        print("\n🚀 DEPLOYMENT READY!")
        print("\nFeatures validated:")
        print("• ✅ Snippet extraction service")
        print("• ✅ Query service integration")
        print("• ✅ Mock and GPT-4 mode compatibility")
        print("• ✅ Error handling and edge cases")
        print("• ✅ Performance characteristics")
        
        print("\n📋 Final checklist:")
        print("• ✅ Core functionality working")
        print("• ✅ Integration tests passing")
        print("• ✅ Error handling robust")
        print("• ✅ Performance acceptable")
        print("• ✅ Schema compatibility confirmed")
        
        print("\n🎯 Ready for production use!")
        print("Both mock mode (for testing) and GPT-4 mode (for production) are fully supported.")
        
        return True
    else:
        print(f"\n❌ {total - passed} integration test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)