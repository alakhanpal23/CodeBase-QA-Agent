"""
Tests for RAG formatting and citation generation.
"""

import pytest
from pathlib import Path

# Add the backend directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.rag import RAGService
from app.core.schemas import Citation


class TestRAGService:
    """Test cases for RAG service."""
    
    @pytest.fixture
    def rag_service(self):
        """Create a RAG service instance for testing."""
        return RAGService()
    
    def test_system_prompt(self, rag_service):
        """Test that system prompt contains required elements."""
        prompt = rag_service._get_system_prompt()
        
        # Check for key elements
        assert "precise codebase assistant" in prompt.lower()
        assert "citations" in prompt.lower()
        assert "file paths" in prompt.lower()
        assert "line ranges" in prompt.lower()
        assert "not confident" in prompt.lower()
    
    def test_build_rag_prompt(self, rag_service):
        """Test building RAG prompt with retrieved chunks."""
        question = "Where is authentication implemented?"
        retrieved_chunks = [
            {
                "path": "src/auth/jwt.py",
                "start_line": 10,
                "end_line": 25,
                "content": "def authenticate_user(token):\n    # JWT validation logic\n    pass"
            },
            {
                "path": "src/auth/middleware.py",
                "start_line": 5,
                "end_line": 15,
                "content": "def auth_middleware(request):\n    # Auth middleware\n    pass"
            }
        ]
        
        prompt = rag_service._build_rag_prompt(question, retrieved_chunks)
        
        # Check that question is included
        assert question in prompt
        
        # Check that chunks are included
        assert "src/auth/jwt.py:10-25" in prompt
        assert "src/auth/middleware.py:5-15" in prompt
        assert "def authenticate_user" in prompt
        assert "def auth_middleware" in prompt
        
        # Check that instructions are included
        assert "Explain in 2-5 sentences" in prompt
        assert "List citations as: path:start-end" in prompt
    
    def test_extract_citations(self, rag_service):
        """Test extracting citations from generated answer."""
        answer = "Authentication is implemented in src/auth/jwt.py:10-25 and src/auth/middleware.py:5-15."
        retrieved_chunks = [
            {
                "path": "src/auth/jwt.py",
                "start_line": 10,
                "end_line": 25,
                "content": "def authenticate_user(token):\n    # JWT validation logic\n    pass",
                "score": 0.9
            },
            {
                "path": "src/auth/middleware.py",
                "start_line": 5,
                "end_line": 15,
                "content": "def auth_middleware(request):\n    # Auth middleware\n    pass",
                "score": 0.8
            }
        ]
        
        citations = rag_service._extract_citations(answer, retrieved_chunks)
        
        assert len(citations) == 2
        
        # Check first citation
        assert citations[0].path == "src/auth/jwt.py"
        assert citations[0].start == 10
        assert citations[0].end == 25
        assert citations[0].score == 0.9
        
        # Check second citation
        assert citations[1].path == "src/auth/middleware.py"
        assert citations[1].start == 5
        assert citations[1].end == 15
        assert citations[1].score == 0.8
    
    def test_extract_citations_no_patterns(self, rag_service):
        """Test citation extraction when no patterns are found."""
        answer = "Authentication is implemented in the auth module."
        retrieved_chunks = [
            {
                "path": "src/auth/jwt.py",
                "start_line": 10,
                "end_line": 25,
                "content": "def authenticate_user(token):\n    # JWT validation logic\n    pass",
                "score": 0.9
            }
        ]
        
        citations = rag_service._extract_citations(answer, retrieved_chunks)
        
        # Should create citations from retrieved chunks even without patterns
        assert len(citations) == 1
        assert citations[0].path == "src/auth/jwt.py"
        assert citations[0].start == 10
        assert citations[0].end == 25
    
    def test_clean_answer(self, rag_service):
        """Test cleaning up answer text."""
        answer = "Authentication is implemented [1] in the auth module [2]."
        cleaned = rag_service._clean_answer(answer)
        
        assert "[1]" not in cleaned
        assert "[2]" not in cleaned
        assert "Authentication is implemented in the auth module." in cleaned
    
    def test_validate_answer_with_citations(self, rag_service):
        """Test answer validation with proper citations."""
        answer = "Authentication is implemented in src/auth/jwt.py:10-25."
        citations = [
            Citation(
                path="src/auth/jwt.py",
                start=10,
                end=25,
                score=0.9,
                content="def authenticate_user(token): pass"
            )
        ]
        
        is_valid = rag_service.validate_answer(answer, citations)
        assert is_valid
    
    def test_validate_answer_uncertain(self, rag_service):
        """Test answer validation when uncertain."""
        answer = "I'm not sure about the authentication implementation."
        citations = [
            Citation(
                path="src/auth/jwt.py",
                start=10,
                end=25,
                score=0.5,
                content="def authenticate_user(token): pass"
            )
        ]
        
        is_valid = rag_service.validate_answer(answer, citations)
        assert is_valid
    
    def test_validate_answer_invalid(self, rag_service):
        """Test answer validation for invalid answers."""
        # Empty answer
        is_valid = rag_service.validate_answer("", [])
        assert not is_valid
        
        # No citations
        is_valid = rag_service.validate_answer("Authentication is implemented.", [])
        assert not is_valid
        
        # Answer without citations or uncertainty
        citations = [
            Citation(
                path="src/auth/jwt.py",
                start=10,
                end=25,
                score=0.9,
                content="def authenticate_user(token): pass"
            )
        ]
        is_valid = rag_service.validate_answer("Authentication is implemented.", citations)
        assert not is_valid


class TestCitationModel:
    """Test cases for Citation model."""
    
    def test_citation_creation(self):
        """Test creating a Citation."""
        citation = Citation(
            path="src/auth/jwt.py",
            start=10,
            end=25,
            score=0.9,
            content="def authenticate_user(token): pass"
        )
        
        assert citation.path == "src/auth/jwt.py"
        assert citation.start == 10
        assert citation.end == 25
        assert citation.score == 0.9
        assert citation.content == "def authenticate_user(token): pass"
    
    def test_citation_without_content(self):
        """Test creating a Citation without content."""
        citation = Citation(
            path="src/auth/jwt.py",
            start=10,
            end=25,
            score=0.9
        )
        
        assert citation.path == "src/auth/jwt.py"
        assert citation.start == 10
        assert citation.end == 25
        assert citation.score == 0.9
        assert citation.content is None


class TestRAGIntegration:
    """Integration tests for RAG functionality."""
    
    @pytest.fixture
    def rag_service(self):
        """Create a RAG service instance for testing."""
        return RAGService()
    
    def test_full_rag_workflow(self, rag_service):
        """Test a complete RAG workflow."""
        question = "Where is user authentication implemented?"
        retrieved_chunks = [
            {
                "path": "src/auth/jwt.py",
                "start_line": 10,
                "end_line": 25,
                "content": "def authenticate_user(token):\n    # JWT validation logic\n    return user",
                "score": 0.9
            },
            {
                "path": "src/auth/middleware.py",
                "start_line": 5,
                "end_line": 15,
                "content": "def auth_middleware(request):\n    # Auth middleware\n    return request",
                "score": 0.8
            }
        ]
        
        # Build prompt
        prompt = rag_service._build_rag_prompt(question, retrieved_chunks)
        
        # Check prompt structure
        assert question in prompt
        assert "src/auth/jwt.py:10-25" in prompt
        assert "src/auth/middleware.py:5-15" in prompt
        assert "def authenticate_user" in prompt
        assert "def auth_middleware" in prompt
        
        # Simulate answer with citations
        answer = "User authentication is implemented in src/auth/jwt.py:10-25 for JWT validation and src/auth/middleware.py:5-15 for request middleware."
        
        # Extract citations
        citations = rag_service._extract_citations(answer, retrieved_chunks)
        
        assert len(citations) == 2
        assert citations[0].path == "src/auth/jwt.py"
        assert citations[1].path == "src/auth/middleware.py"
        
        # Validate answer
        is_valid = rag_service.validate_answer(answer, citations)
        assert is_valid
        
        # Clean answer
        cleaned = rag_service._clean_answer(answer)
        assert "src/auth/jwt.py:10-25" in cleaned
        assert "src/auth/middleware.py:5-15" in cleaned


if __name__ == "__main__":
    pytest.main([__file__])
