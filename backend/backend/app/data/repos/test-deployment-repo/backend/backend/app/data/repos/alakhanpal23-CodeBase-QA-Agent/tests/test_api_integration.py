"""
Integration tests for API endpoints with snippet functionality.
"""

import os
import sys
import tempfile
import json
import asyncio
from unittest.mock import patch, MagicMock
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings


class TestAPIIntegration:
    """Test API integration with snippet functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.client = TestClient(app)
        self.temp_dir = tempfile.mkdtemp()
        self.original_repos_dir = settings.repos_dir
        settings.repos_dir = self.temp_dir
        
        # Create test repository structure
        self.repo_dir = os.path.join(self.temp_dir, "api-test-repo")
        os.makedirs(os.path.join(self.repo_dir, "src"), exist_ok=True)
        
        # Create sample files
        self.create_sample_files()
    
    def teardown_method(self):
        """Cleanup test environment."""
        settings.repos_dir = self.original_repos_dir
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_sample_files(self):
        """Create sample files for testing."""
        # Main application file
        main_content = """from fastapi import FastAPI, HTTPException
from .auth import authenticate_user
from .models import User

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/login")
async def login(username: str, password: str):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": user.generate_token()}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = User.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()
"""
        
        # Auth module
        auth_content = """import bcrypt
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def authenticate_user(username: str, password: str):
    # Mock authentication logic
    from .models import User
    user = User.get_by_username(username)
    if user and verify_password(password, user.password_hash):
        return user
    return None
"""
        
        # Models
        models_content = """from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    is_active: bool = True
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        # Mock database lookup
        if user_id == 1:
            return cls(1, "testuser", "test@example.com", "hashed_password")
        return None
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        # Mock database lookup
        if username == "testuser":
            return cls(1, "testuser", "test@example.com", "hashed_password")
        return None
    
    def generate_token(self) -> str:
        from .auth import create_jwt_token
        return create_jwt_token(self.id)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active
        }
"""
        
        # Write files
        with open(os.path.join(self.repo_dir, "src", "main.py"), "w") as f:
            f.write(main_content)
        
        with open(os.path.join(self.repo_dir, "src", "auth.py"), "w") as f:
            f.write(auth_content)
        
        with open(os.path.join(self.repo_dir, "src", "models.py"), "w") as f:
            f.write(models_content)
    
    def test_health_endpoint(self):
        """Test health endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "timestamp" in data
    
    @patch('backend.app.services.query.QueryService')
    def test_query_endpoint_with_snippets(self, mock_query_service):
        """Test query endpoint returns snippets."""
        # Mock query service response
        mock_service_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.answer = "Authentication is handled by the authenticate_user function in auth.py"
        mock_response.citations = [
            MagicMock(
                path="src/auth.py",
                start=20,
                end=25,
                score=0.85,
                content="def authenticate_user(username: str, password: str):",
                preview="def authenticate_user(username: str, password: str):\n    # Mock authentication logic"
            )
        ]
        mock_response.snippets = [
            MagicMock(
                path="src/auth.py",
                start=20,
                end=25,
                window_start=18,
                window_end=27,
                code="def create_jwt_token(user_id: int) -> str:\n    payload = {\n        'user_id': user_id,\n        'exp': datetime.utcnow() + timedelta(hours=24)\n    }\n    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')\n\ndef authenticate_user(username: str, password: str):\n    # Mock authentication logic"
            )
        ]
        mock_response.latency_ms = 150
        mock_response.mode = "mock"
        
        mock_service_instance.query.return_value = mock_response
        mock_query_service.return_value = mock_service_instance
        
        # Test query request
        query_data = {
            "question": "How does authentication work?",
            "repo_ids": ["api-test-repo"],
            "k": 5
        }
        
        response = self.client.post("/query", json=query_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert "snippets" in data
        assert "latency_ms" in data
        assert "mode" in data
        
        # Verify snippets structure
        snippets = data["snippets"]
        assert len(snippets) > 0
        
        snippet = snippets[0]
        assert "path" in snippet
        assert "start" in snippet
        assert "end" in snippet
        assert "window_start" in snippet
        assert "window_end" in snippet
        assert "code" in snippet
    
    def test_query_endpoint_validation(self):
        """Test query endpoint input validation."""
        # Missing required fields
        response = self.client.post("/query", json={})
        assert response.status_code == 422
        
        # Invalid data types
        response = self.client.post("/query", json={
            "question": 123,  # Should be string
            "repo_ids": "not-a-list",  # Should be list
            "k": "not-a-number"  # Should be int
        })
        assert response.status_code == 422
        
        # Valid request structure
        response = self.client.post("/query", json={
            "question": "How does authentication work?",
            "repo_ids": ["test-repo"],
            "k": 5
        })
        # Should not fail due to validation (might fail due to missing data)
        assert response.status_code in [200, 500]  # 500 if no data ingested
    
    @patch('backend.app.services.ingestion.IngestionService')
    def test_ingest_endpoint(self, mock_ingestion_service):
        """Test ingestion endpoint."""
        mock_service_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.repo_id = "test-repo"
        mock_response.files_processed = 10
        mock_response.chunks_stored = 50
        mock_response.elapsed_time = 2.5
        mock_response.status = "success"
        
        mock_service_instance.ingest_repository.return_value = mock_response
        mock_ingestion_service.return_value = mock_service_instance
        
        ingest_data = {
            "source": "github",
            "url": "https://github.com/test/repo",
            "repo_id": "test-repo",
            "include_globs": ["**/*.py"],
            "exclude_globs": [".git/**"]
        }
        
        response = self.client.post("/ingest", json=ingest_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["repo_id"] == "test-repo"
        assert data["files_processed"] == 10
        assert data["chunks_stored"] == 50
        assert data["status"] == "success"


class TestSnippetAPIBehavior:
    """Test specific snippet behavior in API responses."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_repos_dir = settings.repos_dir
        settings.repos_dir = self.temp_dir
    
    def teardown_method(self):
        """Cleanup test environment."""
        settings.repos_dir = self.original_repos_dir
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_snippet_response_structure(self):
        """Test that snippet responses have correct structure."""
        from backend.app.core.schemas import QueryResponse, Citation, Snippet
        
        # Create test response
        citation = Citation(
            path="test.py",
            start=10,
            end=15,
            score=0.8,
            content="def test_function():\n    pass",
            preview="def test_function():\n    pass"
        )
        
        snippet = Snippet(
            path="test.py",
            start=10,
            end=15,
            window_start=8,
            window_end=17,
            code="# Test file\n\ndef test_function():\n    pass\n\n# End of function"
        )
        
        response = QueryResponse(
            answer="Test function is defined in test.py",
            citations=[citation],
            snippets=[snippet],
            latency_ms=100,
            mode="mock"
        )
        
        # Verify structure
        assert len(response.citations) == 1
        assert len(response.snippets) == 1
        assert response.citations[0].preview is not None
        assert response.snippets[0].window_start < response.snippets[0].start
        assert response.snippets[0].window_end > response.snippets[0].end
    
    def test_empty_snippets_handling(self):
        """Test handling when no snippets can be extracted."""
        from backend.app.core.schemas import QueryResponse, Citation
        
        # Response with citations but no snippets (e.g., files not found)
        citation = Citation(
            path="nonexistent.py",
            start=10,
            end=15,
            score=0.8,
            content="def test_function():\n    pass"
        )
        
        response = QueryResponse(
            answer="Function found but file not accessible",
            citations=[citation],
            snippets=[],  # Empty snippets
            latency_ms=100,
            mode="mock"
        )
        
        # Should handle gracefully
        assert len(response.citations) == 1
        assert len(response.snippets) == 0
        assert response.answer is not None
    
    def test_large_snippet_handling(self):
        """Test handling of large code snippets."""
        from backend.app.services.snippets import extract_snippet
        
        # Create large file
        repo_dir = os.path.join(self.temp_dir, "large-repo")
        os.makedirs(repo_dir, exist_ok=True)
        
        # Generate large content
        large_content = "\n".join([f"# Line {i}: " + "x" * 100 for i in range(1000)])
        
        with open(os.path.join(repo_dir, "large.py"), "w") as f:
            f.write(large_content)
        
        # Extract snippet with small max_chars
        result = extract_snippet("large-repo", "large.py", 500, 510, max_chars=500)
        
        assert result is not None
        window_start, window_end, code = result
        assert len(code) <= 520  # Should be truncated with some margin for markers
        assert "..." in code  # Should have truncation marker


class TestMockVsGPT4Compatibility:
    """Test compatibility between mock and GPT-4 modes."""
    
    def test_response_schema_compatibility(self):
        """Test that both modes return compatible response schemas."""
        from backend.app.core.schemas import QueryResponse, Citation, Snippet
        
        # Mock mode response
        mock_response = QueryResponse(
            answer="Mock answer with citations",
            citations=[Citation(path="test.py", start=1, end=5, score=0.8)],
            snippets=[Snippet(path="test.py", start=1, end=5, window_start=1, window_end=8, code="mock code")],
            latency_ms=100,
            mode="mock"
        )
        
        # GPT-4 mode response (simulated)
        gpt4_response = QueryResponse(
            answer="GPT-4 answer with citations",
            citations=[Citation(path="test.py", start=1, end=5, score=0.8)],
            snippets=[Snippet(path="test.py", start=1, end=5, window_start=1, window_end=8, code="gpt4 code")],
            latency_ms=500,
            mode="gpt4",
            confidence=0.95
        )
        
        # Both should have same structure
        assert type(mock_response.citations) == type(gpt4_response.citations)
        assert type(mock_response.snippets) == type(gpt4_response.snippets)
        assert hasattr(mock_response, 'mode')
        assert hasattr(gpt4_response, 'mode')
        assert hasattr(gpt4_response, 'confidence')  # GPT-4 can have confidence
    
    @patch('backend.app.services.rag.RAGService')
    def test_mode_switching(self, mock_rag_service):
        """Test switching between mock and GPT-4 modes."""
        from backend.app.services.query import QueryService
        from backend.app.core.schemas import QueryRequest
        
        # Test mock mode
        mock_rag_instance = MagicMock()
        mock_rag_instance.use_mock = True
        mock_rag_instance.generate_answer.return_value = ("Mock answer", [])
        mock_rag_instance.validate_answer.return_value = True
        mock_rag_service.return_value = mock_rag_instance
        
        query_service = QueryService()
        assert hasattr(query_service.rag_service, 'use_mock')
        
        # Test GPT-4 mode (simulated)
        mock_rag_instance.use_mock = False
        assert not query_service.rag_service.use_mock


class TestPerformanceAndScaling:
    """Test performance characteristics of snippet extraction."""
    
    def test_snippet_extraction_performance(self):
        """Test performance of snippet extraction."""
        import time
        from backend.app.services.snippets import extract_snippet
        
        temp_dir = tempfile.mkdtemp()
        original_repos_dir = settings.repos_dir
        settings.repos_dir = temp_dir
        
        try:
            # Create test repo
            repo_dir = os.path.join(temp_dir, "perf-repo")
            os.makedirs(repo_dir, exist_ok=True)
            
            # Create medium-sized file
            content = "\n".join([f"def function_{i}():\n    return {i}\n" for i in range(1000)])
            
            with open(os.path.join(repo_dir, "functions.py"), "w") as f:
                f.write(content)
            
            # Time multiple extractions
            start_time = time.time()
            
            for i in range(10):
                result = extract_snippet("perf-repo", "functions.py", i*10 + 1, i*10 + 5)
                assert result is not None
            
            elapsed = time.time() - start_time
            
            # Should be reasonably fast (less than 1 second for 10 extractions)
            assert elapsed < 1.0
            
        finally:
            settings.repos_dir = original_repos_dir
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_concurrent_snippet_extraction(self):
        """Test concurrent snippet extraction."""
        import concurrent.futures
        from backend.app.services.snippets import extract_snippet
        
        temp_dir = tempfile.mkdtemp()
        original_repos_dir = settings.repos_dir
        settings.repos_dir = temp_dir
        
        try:
            # Create test repo
            repo_dir = os.path.join(temp_dir, "concurrent-repo")
            os.makedirs(repo_dir, exist_ok=True)
            
            # Create multiple files
            for i in range(5):
                content = f"# File {i}\n" + "\n".join([f"def func_{j}(): return {j}" for j in range(100)])
                with open(os.path.join(repo_dir, f"file_{i}.py"), "w") as f:
                    f.write(content)
            
            # Test concurrent extraction
            def extract_worker(file_num):
                return extract_snippet("concurrent-repo", f"file_{file_num}.py", 10, 15)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(extract_worker, i) for i in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All extractions should succeed
            assert all(result is not None for result in results)
            
        finally:
            settings.repos_dir = original_repos_dir
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run basic tests manually
    test_instance = TestAPIIntegration()
    test_instance.setup_method()
    
    try:
        test_instance.test_health_endpoint()
        print("✅ Health endpoint test passed")
        
        test_instance.test_query_endpoint_validation()
        print("✅ Query validation test passed")
        
        print("\n🎉 Basic API tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test_instance.teardown_method()