"""
Tests for GPT-4 compatibility and mode switching.
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.rag import RAGService
from backend.app.services.query import QueryService
from backend.app.core.schemas import QueryRequest, Citation
from backend.app.core.config import settings


class TestGPT4Compatibility:
    """Test GPT-4 mode compatibility with snippet functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_repos_dir = settings.repos_dir
        settings.repos_dir = self.temp_dir
        
        # Create test repository
        self.repo_dir = os.path.join(self.temp_dir, "gpt4-test-repo")
        os.makedirs(os.path.join(self.repo_dir, "app"), exist_ok=True)
        
        # Create sample code files
        self.create_test_files()
    
    def teardown_method(self):
        """Cleanup test environment."""
        settings.repos_dir = self.original_repos_dir
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_files(self):
        """Create test files for GPT-4 testing."""
        # Authentication service
        auth_service = """import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        \"\"\"Create JWT access token.\"\"\"
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, token: str):
        \"\"\"Verify JWT token.\"\"\"
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            return None
    
    def hash_password(self, password: str):
        \"\"\"Hash password using bcrypt.\"\"\"
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str):
        \"\"\"Verify password against hash.\"\"\"
        return pwd_context.verify(plain_password, hashed_password)
"""
        
        # Database models
        models_content = """from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    \"\"\"User model for authentication and authorization.\"\"\"
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        \"\"\"Convert user to dictionary.\"\"\"
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Session(Base):
    \"\"\"User session model.\"\"\"
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        \"\"\"Check if session is expired.\"\"\"
        return datetime.utcnow() > self.expires_at
"""
        
        # API routes
        routes_content = """from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from .models import User
from .auth_service import AuthService
from .database import get_db

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService("your-secret-key")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    \"\"\"Get current authenticated user.\"\"\"
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.post("/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    \"\"\"Authenticate user and return access token.\"\"\"
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not auth_service.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_user)):
    \"\"\"Get current user information.\"\"\"
    return current_user.to_dict()

@router.get("/users", response_model=List[dict])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    \"\"\"Get list of users (admin only).\"\"\"
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = db.query(User).offset(skip).limit(limit).all()
    return [user.to_dict() for user in users]
"""
        
        # Write files
        with open(os.path.join(self.repo_dir, "app", "auth_service.py"), "w") as f:
            f.write(auth_service)
        
        with open(os.path.join(self.repo_dir, "app", "models.py"), "w") as f:
            f.write(models_content)
        
        with open(os.path.join(self.repo_dir, "app", "routes.py"), "w") as f:
            f.write(routes_content)
    
    @patch('backend.app.services.rag.openai.AsyncOpenAI')
    def test_gpt4_mode_with_snippets(self, mock_openai):
        """Test GPT-4 mode with snippet extraction."""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        # Simulate GPT-4 response with citations
        mock_message.content = """JWT authentication is implemented in the AuthService class. The create_access_token method in app/auth_service.py:13-22 handles token creation, while verify_token in app/auth_service.py:24-30 handles token verification. The login endpoint in app/routes.py:45-60 uses these methods for user authentication."""
        
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Test RAG service in GPT-4 mode
        rag_service = RAGService()
        rag_service.use_mock = False  # Enable GPT-4 mode
        
        # Mock retrieved chunks
        retrieved_chunks = [
            {
                "path": "app/auth_service.py",
                "start_line": 13,
                "end_line": 22,
                "score": 0.9,
                "content": "def create_access_token(self, data: dict, expires_delta: timedelta = None):\n    \"\"\"Create JWT access token.\"\"\"\n    to_encode = data.copy()",
                "content_hash": "hash1"
            },
            {
                "path": "app/routes.py",
                "start_line": 45,
                "end_line": 60,
                "score": 0.85,
                "content": "@router.post(\"/login\")\nasync def login(username: str, password: str, db: Session = Depends(get_db)):",
                "content_hash": "hash2"
            }
        ]
        
        # Test answer generation
        import asyncio
        
        async def run_test():
            answer, citations = await rag_service.generate_answer(
                "How does JWT authentication work?",
                retrieved_chunks
            )
            
            assert answer is not None
            assert len(citations) > 0
            assert any("auth_service.py" in c.path for c in citations)
            return answer, citations
        
        answer, citations = asyncio.run(run_test())
        
        # Verify citations can be used for snippet extraction
        from backend.app.services.snippets import extract_snippet
        
        for citation in citations:
            snippet_result = extract_snippet(
                "gpt4-test-repo",
                citation.path,
                citation.start,
                citation.end
            )
            
            if snippet_result:  # File exists and is readable
                window_start, window_end, code = snippet_result
                assert window_start <= citation.start
                assert window_end >= citation.end
                assert len(code) > 0
    
    def test_mock_to_gpt4_mode_switching(self):
        """Test switching from mock to GPT-4 mode."""
        rag_service = RAGService()
        
        # Start in mock mode
        assert rag_service.use_mock is True
        
        # Simulate quota error that triggers mock mode
        with patch.object(rag_service.client.chat.completions, 'create', 
                         side_effect=Exception("insufficient_quota")):
            
            retrieved_chunks = [{
                "path": "app/auth_service.py",
                "start_line": 10,
                "end_line": 15,
                "score": 0.8,
                "content": "def create_access_token(self):"
            }]
            
            import asyncio
            
            async def run_test():
                answer, citations = await rag_service.generate_answer(
                    "How does authentication work?",
                    retrieved_chunks
                )
                return answer, citations
            
            answer, citations = asyncio.run(run_test())
            
            # Should fall back to mock mode
            assert rag_service.use_mock is True
            assert answer is not None
            assert len(citations) > 0
    
    @patch('backend.app.services.rag.openai.AsyncOpenAI')
    def test_gpt4_citation_extraction(self, mock_openai):
        """Test citation extraction from GPT-4 responses."""
        # Mock OpenAI with response containing citation patterns
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        # Response with explicit citation patterns
        mock_message.content = """Authentication is handled by the create_access_token function in app/auth_service.py:13-22. The login endpoint in app/routes.py:45-60 validates credentials and returns tokens."""
        
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        rag_service = RAGService()
        rag_service.use_mock = False
        
        retrieved_chunks = [
            {
                "path": "app/auth_service.py",
                "start_line": 13,
                "end_line": 22,
                "score": 0.9,
                "content": "def create_access_token(self, data: dict):",
                "content_hash": "hash1"
            },
            {
                "path": "app/routes.py", 
                "start_line": 45,
                "end_line": 60,
                "score": 0.85,
                "content": "@router.post('/login')",
                "content_hash": "hash2"
            }
        ]
        
        import asyncio
        
        async def run_test():
            answer, citations = await rag_service.generate_answer(
                "How does authentication work?",
                retrieved_chunks
            )
            
            # Should extract citations from the response
            assert len(citations) >= 2
            
            # Check citation details
            auth_citation = next((c for c in citations if "auth_service.py" in c.path), None)
            routes_citation = next((c for c in citations if "routes.py" in c.path), None)
            
            assert auth_citation is not None
            assert routes_citation is not None
            
            assert auth_citation.start == 13
            assert auth_citation.end == 22
            assert routes_citation.start == 45
            assert routes_citation.end == 60
            
            return citations
        
        citations = asyncio.run(run_test())
        
        # Test that these citations work with snippet extraction
        for citation in citations:
            snippet_result = extract_snippet(
                "gpt4-test-repo",
                citation.path,
                citation.start,
                citation.end,
                context_lines=3
            )
            
            if snippet_result:
                window_start, window_end, code = snippet_result
                assert "def " in code or "async def" in code or "@router" in code
    
    def test_gpt4_answer_validation(self):
        """Test answer validation for GPT-4 responses."""
        rag_service = RAGService()
        
        # Test valid answer with citations
        valid_answer = "Authentication is handled in app/auth_service.py:13-22 and app/routes.py:45-60"
        valid_citations = [
            Citation(path="app/auth_service.py", start=13, end=22, score=0.9),
            Citation(path="app/routes.py", start=45, end=60, score=0.85)
        ]
        
        import asyncio
        
        async def test_valid():
            is_valid = await rag_service.validate_answer(valid_answer, valid_citations)
            assert is_valid is True
        
        asyncio.run(test_valid())
        
        # Test invalid answer without citations
        invalid_answer = "I don't know how authentication works"
        empty_citations = []
        
        async def test_invalid():
            is_valid = await rag_service.validate_answer(invalid_answer, empty_citations)
            assert is_valid is False
        
        asyncio.run(test_invalid())
        
        # Test uncertain answer (should be valid)
        uncertain_answer = "I'm not sure about the authentication implementation"
        
        async def test_uncertain():
            is_valid = await rag_service.validate_answer(uncertain_answer, empty_citations)
            assert is_valid is True  # Uncertainty is acceptable
        
        asyncio.run(test_uncertain())


class TestEndToEndGPT4Integration:
    """End-to-end tests for GPT-4 integration with snippets."""
    
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
    
    @patch('backend.app.services.rag.openai.AsyncOpenAI')
    @patch('backend.app.services.query.VectorStoreManager')
    @patch('backend.app.services.query.EmbeddingService')
    def test_full_query_pipeline_gpt4(self, mock_embedding, mock_vector, mock_openai):
        """Test full query pipeline with GPT-4 and snippets."""
        # Create test repository
        repo_dir = os.path.join(self.temp_dir, "e2e-repo")
        os.makedirs(repo_dir, exist_ok=True)
        
        test_content = """def authenticate_user(username: str, password: str):
    \"\"\"Authenticate user with username and password.\"\"\"
    user = get_user_by_username(username)
    if user and verify_password(password, user.password_hash):
        return user
    return None

def create_jwt_token(user_id: int):
    \"\"\"Create JWT token for authenticated user.\"\"\"
    payload = {'user_id': user_id, 'exp': datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
"""
        
        with open(os.path.join(repo_dir, "auth.py"), "w") as f:
            f.write(test_content)
        
        # Mock services
        mock_embedding_instance = MagicMock()
        mock_embedding_instance.embed_text.return_value = [0.1] * 1536
        mock_embedding.return_value = mock_embedding_instance
        
        mock_vector_instance = MagicMock()
        mock_store = MagicMock()
        mock_store.index.ntotal = 100
        mock_vector_instance.get_store.return_value = mock_store
        mock_vector_instance.search_multiple.return_value = [
            {
                "path": "auth.py",
                "start_line": 1,
                "end_line": 7,
                "score": 0.9,
                "content": "def authenticate_user(username: str, password: str):\n    \"\"\"Authenticate user with username and password.\"\"\""
            },
            {
                "path": "auth.py",
                "start_line": 9,
                "end_line": 12,
                "score": 0.85,
                "content": "def create_jwt_token(user_id: int):\n    \"\"\"Create JWT token for authenticated user.\"\"\""
            }
        ]
        mock_vector.return_value = mock_vector_instance
        
        # Mock OpenAI
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Authentication is handled by authenticate_user in auth.py:1-7 and JWT tokens are created by create_jwt_token in auth.py:9-12."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # Test full pipeline
        from backend.app.services.query import QueryService
        from backend.app.core.schemas import QueryRequest
        
        query_service = QueryService()
        query_service.rag_service.use_mock = False  # Enable GPT-4 mode
        
        request = QueryRequest(
            question="How does authentication work?",
            repo_ids=["e2e-repo"],
            k=5
        )
        
        import asyncio
        
        async def run_e2e_test():
            response = await query_service.query(request)
            
            # Verify response structure
            assert response.answer is not None
            assert len(response.citations) > 0
            assert len(response.snippets) > 0  # Should have snippets from real files
            assert response.mode == "gpt4"
            assert response.latency_ms > 0
            
            # Verify snippet content
            for snippet in response.snippets:
                assert snippet.path == "auth.py"
                assert snippet.window_start <= snippet.start
                assert snippet.window_end >= snippet.end
                assert "def " in snippet.code
                assert len(snippet.code) > 0
            
            return response
        
        response = asyncio.run(run_e2e_test())
        
        # Additional verification
        assert "authenticate" in response.answer.lower()
        assert any("auth.py" in citation.path for citation in response.citations)


class TestConfigurationAndSettings:
    """Test configuration handling for GPT-4 mode."""
    
    def test_openai_configuration(self):
        """Test OpenAI configuration settings."""
        from backend.app.core.config import settings
        
        # Verify required settings exist
        assert hasattr(settings, 'openai_api_key')
        assert hasattr(settings, 'openai_model')
        assert hasattr(settings, 'openai_embedding_model')
        
        # Verify default values
        assert settings.openai_model == "gpt-4"
        assert settings.openai_embedding_model == "text-embedding-3-small"
    
    def test_snippet_configuration_with_gpt4(self):
        """Test snippet configuration works with GPT-4 mode."""
        from backend.app.core.config import settings
        
        # Verify snippet settings
        assert hasattr(settings, 'snippet_context_lines')
        assert hasattr(settings, 'snippet_max_chars')
        assert hasattr(settings, 'repos_dir')
        
        # Test configuration values
        assert settings.snippet_context_lines == 6
        assert settings.snippet_max_chars == 1200
        assert isinstance(settings.repos_dir, str)
    
    def test_rag_service_configuration(self):
        """Test RAG service configuration for GPT-4."""
        rag_service = RAGService()
        
        # Verify GPT-4 settings
        assert rag_service.model == "gpt-4"
        assert hasattr(rag_service, 'use_mock')
        assert hasattr(rag_service, 'client')
        
        # Test stats
        import asyncio
        
        async def test_stats():
            stats = await rag_service.get_rag_stats()
            assert 'model' in stats
            assert 'using_mock' in stats
            assert stats['model'] == "gpt-4"
        
        asyncio.run(test_stats())


if __name__ == "__main__":
    # Run basic GPT-4 compatibility tests
    test_instance = TestGPT4Compatibility()
    test_instance.setup_method()
    
    try:
        test_instance.test_mock_to_gpt4_mode_switching()
        print("✅ Mock to GPT-4 mode switching test passed")
        
        print("\n🎉 GPT-4 compatibility tests passed!")
        print("Note: Full GPT-4 tests require API key and network access")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test_instance.teardown_method()