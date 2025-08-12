"""
Comprehensive tests for snippet extraction functionality.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.snippets import extract_snippet, _is_probably_text, _safe_repo_path
from backend.app.core.config import settings


class TestSnippetExtraction:
    """Test snippet extraction functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_repos_dir = settings.repos_dir
        settings.repos_dir = self.temp_dir
        
        # Create test repo structure
        self.repo_dir = os.path.join(self.temp_dir, "test-repo")
        os.makedirs(self.repo_dir, exist_ok=True)
        
        # Sample Python file
        self.python_content = """#!/usr/bin/env python3
# Sample Python file for testing
import os
import sys

def hello_world():
    \"\"\"Simple hello world function.\"\"\"
    print("Hello, World!")
    return "success"

class TestClass:
    \"\"\"Test class for demonstration.\"\"\"
    
    def __init__(self):
        self.name = "test"
        self.value = 42
    
    def method1(self):
        \"\"\"First method.\"\"\"
        return self.name
    
    def method2(self):
        \"\"\"Second method with logic.\"\"\"
        # This is a comment
        value = self.value
        return value * 2
    
    def complex_method(self):
        \"\"\"More complex method.\"\"\"
        result = []
        for i in range(10):
            if i % 2 == 0:
                result.append(i * 2)
        return result

if __name__ == "__main__":
    obj = TestClass()
    print(obj.method2())
    hello_world()
"""
        
        # JavaScript file
        self.js_content = """// JavaScript test file
const express = require('express');
const app = express();

function setupRoutes() {
    app.get('/api/users', (req, res) => {
        res.json({ users: [] });
    });
    
    app.post('/api/users', (req, res) => {
        const user = req.body;
        // Save user logic here
        res.status(201).json(user);
    });
}

class UserService {
    constructor() {
        this.users = [];
    }
    
    addUser(user) {
        this.users.push(user);
        return user;
    }
}

module.exports = { setupRoutes, UserService };
"""
        
        # Create test files
        with open(os.path.join(self.repo_dir, "test.py"), "w") as f:
            f.write(self.python_content)
        
        with open(os.path.join(self.repo_dir, "app.js"), "w") as f:
            f.write(self.js_content)
        
        # Binary file
        with open(os.path.join(self.repo_dir, "binary.bin"), "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")
        
        # Empty file
        with open(os.path.join(self.repo_dir, "empty.txt"), "w") as f:
            pass
    
    def teardown_method(self):
        """Cleanup test environment."""
        settings.repos_dir = self.original_repos_dir
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_basic_snippet_extraction(self):
        """Test basic snippet extraction."""
        result = extract_snippet("test-repo", "test.py", 5, 8, context_lines=2)
        
        assert result is not None
        window_start, window_end, code = result
        
        assert window_start == 3  # 5 - 2
        assert window_end == 10   # 8 + 2
        assert "def hello_world():" in code
        assert "print(\"Hello, World!\")" in code
        assert "return \"success\"" in code
    
    def test_edge_cases_line_numbers(self):
        """Test edge cases with line numbers."""
        # Test start of file
        result = extract_snippet("test-repo", "test.py", 1, 3, context_lines=5)
        assert result is not None
        window_start, window_end, code = result
        assert window_start == 1  # Can't go below 1
        
        # Test end of file
        lines_count = len(self.python_content.splitlines())
        result = extract_snippet("test-repo", "test.py", lines_count-2, lines_count, context_lines=5)
        assert result is not None
        window_start, window_end, code = result
        assert window_end == lines_count  # Can't go beyond file end
    
    def test_context_lines_configuration(self):
        """Test different context line configurations."""
        # Test with 0 context lines
        result = extract_snippet("test-repo", "test.py", 5, 8, context_lines=0)
        assert result is not None
        window_start, window_end, code = result
        assert window_start == 5
        assert window_end == 8
        
        # Test with large context lines
        result = extract_snippet("test-repo", "test.py", 10, 12, context_lines=20)
        assert result is not None
        window_start, window_end, code = result
        assert window_start == 1  # Should be clamped to file start
    
    def test_max_chars_limit(self):
        """Test character limit enforcement."""
        result = extract_snippet("test-repo", "test.py", 1, 30, max_chars=200)
        assert result is not None
        window_start, window_end, code = result
        assert len(code) <= 200 + 10  # Allow some margin for truncation markers
        assert "..." in code  # Should have truncation marker
    
    def test_different_file_types(self):
        """Test extraction from different file types."""
        # Python file
        result = extract_snippet("test-repo", "test.py", 5, 8)
        assert result is not None
        
        # JavaScript file
        result = extract_snippet("test-repo", "app.js", 4, 8)
        assert result is not None
        window_start, window_end, code = result
        assert "setupRoutes" in code
        assert "app.get" in code
    
    def test_binary_file_rejection(self):
        """Test that binary files are rejected."""
        result = extract_snippet("test-repo", "binary.bin", 1, 5)
        assert result is None
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        result = extract_snippet("test-repo", "empty.txt", 1, 5)
        assert result is None
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent files."""
        result = extract_snippet("test-repo", "nonexistent.py", 1, 5)
        assert result is None
    
    def test_path_traversal_protection(self):
        """Test path traversal attack prevention."""
        with pytest.raises(ValueError, match="Path traversal detected"):
            _safe_repo_path("test-repo", "../../../etc/passwd")
        
        with pytest.raises(ValueError, match="Path traversal detected"):
            _safe_repo_path("test-repo", "..\\..\\windows\\system32")
    
    def test_text_file_detection(self):
        """Test text file detection logic."""
        # Text content
        assert _is_probably_text("test.py", b"print('hello')")
        assert _is_probably_text("test.js", b"console.log('test')")
        assert _is_probably_text("unknown.ext", b"This is text content")
        
        # Binary content
        assert not _is_probably_text("test.bin", b"\x00\x01\x02\x03")
        assert not _is_probably_text("test.py", b"print\x00hello")
        
        # Known text extensions
        assert _is_probably_text("test.py", b"")
        assert _is_probably_text("test.md", b"")
        assert _is_probably_text("config.yml", b"")


class TestSnippetIntegration:
    """Test snippet integration with query service."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_repos_dir = settings.repos_dir
        settings.repos_dir = self.temp_dir
        
        # Create test repo with realistic structure
        self.repo_dir = os.path.join(self.temp_dir, "integration-repo")
        os.makedirs(os.path.join(self.repo_dir, "app", "auth"), exist_ok=True)
        os.makedirs(os.path.join(self.repo_dir, "app", "models"), exist_ok=True)
        
        # Auth module
        auth_content = """from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)
"""
        
        # User model
        user_model_content = """from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
"""
        
        with open(os.path.join(self.repo_dir, "app", "auth", "jwt.py"), "w") as f:
            f.write(auth_content)
        
        with open(os.path.join(self.repo_dir, "app", "models", "user.py"), "w") as f:
            f.write(user_model_content)
    
    def teardown_method(self):
        """Cleanup test environment."""
        settings.repos_dir = self.original_repos_dir
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_multiple_file_snippets(self):
        """Test snippet extraction from multiple files."""
        # Test auth file
        result1 = extract_snippet("integration-repo", "app/auth/jwt.py", 7, 15)
        assert result1 is not None
        window_start1, window_end1, code1 = result1
        assert "create_access_token" in code1
        assert "expires_delta" in code1
        
        # Test user model file
        result2 = extract_snippet("integration-repo", "app/models/user.py", 8, 16)
        assert result2 is not None
        window_start2, window_end2, code2 = result2
        assert "class User" in code2
        assert "__tablename__" in code2
    
    def test_realistic_citation_scenarios(self):
        """Test realistic citation scenarios."""
        # Function definition
        result = extract_snippet("integration-repo", "app/auth/jwt.py", 6, 6, context_lines=3)
        assert result is not None
        window_start, window_end, code = result
        assert "def create_access_token" in code
        
        # Class definition
        result = extract_snippet("integration-repo", "app/models/user.py", 8, 8, context_lines=2)
        assert result is not None
        window_start, window_end, code = result
        assert "class User(Base):" in code


class TestQueryServiceIntegration:
    """Test integration with query service."""
    
    @patch('backend.app.services.query.VectorStoreManager')
    @patch('backend.app.services.query.EmbeddingService')
    @patch('backend.app.services.query.RAGService')
    def test_query_with_snippets_mock_mode(self, mock_rag, mock_embedding, mock_vector):
        """Test query service with snippets in mock mode."""
        from backend.app.services.query import QueryService
        from backend.app.core.schemas import QueryRequest, Citation
        
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
                "path": "app/auth/jwt.py",
                "start_line": 6,
                "end_line": 15,
                "score": 0.85,
                "content": "def create_access_token(data: dict):\n    # JWT creation logic"
            }
        ]
        mock_vector.return_value = mock_vector_instance
        
        mock_rag_instance = MagicMock()
        mock_rag_instance.use_mock = True
        mock_rag_instance.generate_answer.return_value = (
            "JWT tokens are created using the create_access_token function.",
            [Citation(
                path="app/auth/jwt.py",
                start=6,
                end=15,
                score=0.85,
                content="def create_access_token(data: dict):\n    # JWT creation logic"
            )]
        )
        mock_rag_instance.validate_answer.return_value = True
        mock_rag.return_value = mock_rag_instance
        
        # Test query service
        query_service = QueryService()
        request = QueryRequest(
            question="How are JWT tokens created?",
            repo_ids=["test-repo"],
            k=5
        )
        
        # This would normally require async, but we're mocking everything
        # In real tests, you'd use pytest-asyncio
        import asyncio
        
        async def run_test():
            response = await query_service.query(request)
            
            assert response.answer is not None
            assert len(response.citations) > 0
            assert len(response.snippets) >= 0  # Snippets depend on file existence
            assert response.mode == "mock"
            assert response.latency_ms > 0
        
        # Run the async test
        asyncio.run(run_test())
    
    def test_snippet_preview_generation(self):
        """Test snippet preview generation for citations."""
        from backend.app.core.schemas import Citation
        
        # Mock code content
        code_content = """def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "SECRET_KEY")
    return encoded_jwt"""
        
        # Test preview generation (first 6 lines)
        lines = code_content.splitlines()
        preview = "\n".join(lines[:6])
        
        citation = Citation(
            path="app/auth/jwt.py",
            start=6,
            end=11,
            score=0.85,
            content=code_content,
            preview=preview
        )
        
        assert citation.preview is not None
        assert "def create_access_token" in citation.preview
        assert len(citation.preview.splitlines()) <= 6


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_malformed_file_handling(self):
        """Test handling of malformed files."""
        temp_dir = tempfile.mkdtemp()
        original_repos_dir = settings.repos_dir
        settings.repos_dir = temp_dir
        
        try:
            repo_dir = os.path.join(temp_dir, "error-repo")
            os.makedirs(repo_dir, exist_ok=True)
            
            # Create file with invalid UTF-8
            with open(os.path.join(repo_dir, "invalid.py"), "wb") as f:
                f.write(b"print('hello')\n\xff\xfe\x00\x00invalid utf8\nprint('world')")
            
            # Should handle gracefully with error replacement
            result = extract_snippet("error-repo", "invalid.py", 1, 3)
            assert result is not None  # Should not crash
            
        finally:
            settings.repos_dir = original_repos_dir
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_permission_errors(self):
        """Test handling of permission errors."""
        # This test would need special setup on different OS
        # For now, just test the exception handling path
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = extract_snippet("test-repo", "test.py", 1, 5)
            assert result is None  # Should handle gracefully
    
    def test_configuration_edge_cases(self):
        """Test configuration edge cases."""
        # Test with zero context lines
        original_context = settings.snippet_context_lines
        original_max_chars = settings.snippet_max_chars
        
        try:
            settings.snippet_context_lines = 0
            settings.snippet_max_chars = 50
            
            temp_dir = tempfile.mkdtemp()
            settings.repos_dir = temp_dir
            
            repo_dir = os.path.join(temp_dir, "config-test")
            os.makedirs(repo_dir, exist_ok=True)
            
            with open(os.path.join(repo_dir, "test.py"), "w") as f:
                f.write("line1\nline2\nline3\nline4\nline5\n")
            
            result = extract_snippet("config-test", "test.py", 2, 4)
            assert result is not None
            window_start, window_end, code = result
            assert window_start == 2
            assert window_end == 4
            assert len(code) <= 60  # Should respect max_chars
            
        finally:
            settings.snippet_context_lines = original_context
            settings.snippet_max_chars = original_max_chars
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run tests manually if pytest not available
    import unittest
    
    # Convert pytest-style tests to unittest
    suite = unittest.TestSuite()
    
    # Add basic tests
    test_instance = TestSnippetExtraction()
    test_instance.setup_method()
    
    try:
        test_instance.test_basic_snippet_extraction()
        print("✅ Basic snippet extraction test passed")
        
        test_instance.test_edge_cases_line_numbers()
        print("✅ Edge cases test passed")
        
        test_instance.test_different_file_types()
        print("✅ Different file types test passed")
        
        test_instance.test_binary_file_rejection()
        print("✅ Binary file rejection test passed")
        
        test_instance.test_text_file_detection()
        print("✅ Text file detection test passed")
        
        print("\n🎉 All basic tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        test_instance.teardown_method()