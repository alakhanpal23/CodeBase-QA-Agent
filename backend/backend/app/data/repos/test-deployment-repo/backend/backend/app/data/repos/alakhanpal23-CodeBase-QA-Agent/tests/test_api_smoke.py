"""
Smoke tests for API endpoints.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Add the backend directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.main import app


class TestAPISmoke:
    """Smoke tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "timestamp" in data
    
    def test_stats_endpoint(self, client):
        """Test stats endpoint."""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_repos" in data
        assert "total_files" in data
        assert "total_chunks" in data
        assert "index_size_mb" in data
        
        # Check data types
        assert isinstance(data["total_repos"], int)
        assert isinstance(data["total_files"], int)
        assert isinstance(data["total_chunks"], int)
        assert isinstance(data["index_size_mb"], (int, float))
    
    def test_ingest_endpoint_invalid_request(self, client):
        """Test ingest endpoint with invalid request."""
        # Missing required fields
        response = client.post("/ingest", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_ingest_endpoint_valid_request(self, client):
        """Test ingest endpoint with valid request structure."""
        request_data = {
            "source": "github",
            "url": "https://github.com/test/repo",
            "repo_id": "test/repo",
            "branch": "main",
            "include_globs": ["**/*.py"],
            "exclude_globs": [".git/**"]
        }
        
        response = client.post("/ingest", json=request_data)
        
        # Should fail because we can't actually clone the repo in tests
        # But the request structure should be valid
        assert response.status_code in [500, 422]  # Either validation error or processing error
    
    def test_query_endpoint_invalid_request(self, client):
        """Test query endpoint with invalid request."""
        # Missing required fields
        response = client.post("/query", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_query_endpoint_valid_request(self, client):
        """Test query endpoint with valid request structure."""
        params = {
            "question": "Where is authentication implemented?",
            "repo_ids": ["test/repo"],
            "k": 6
        }
        
        response = client.post("/query", json=params)
        
        # Should fail because no indexed data exists
        # But the request structure should be valid
        assert response.status_code in [500, 422]  # Either validation error or processing error
    
    def test_api_documentation(self, client):
        """Test that API documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestAPISchemas:
    """Test API request/response schemas."""
    
    def test_ingest_request_schema(self):
        """Test IngestRequest schema validation."""
        from app.core.schemas import IngestRequest
        
        # Valid request
        request = IngestRequest(
            source="github",
            url="https://github.com/test/repo",
            repo_id="test/repo",
            branch="main",
            include_globs=["**/*.py"],
            exclude_globs=[".git/**"]
        )
        
        assert request.source == "github"
        assert request.url == "https://github.com/test/repo"
        assert request.repo_id == "test/repo"
        assert request.branch == "main"
        assert request.include_globs == ["**/*.py"]
        assert request.exclude_globs == [".git/**"]
    
    def test_query_request_schema(self):
        """Test QueryRequest schema validation."""
        from app.core.schemas import QueryRequest
        
        # Valid request
        request = QueryRequest(
            question="Where is authentication implemented?",
            repo_ids=["test/repo"],
            k=6
        )
        
        assert request.question == "Where is authentication implemented?"
        assert request.repo_ids == ["test/repo"]
        assert request.k == 6
    
    def test_citation_schema(self):
        """Test Citation schema validation."""
        from app.core.schemas import Citation
        
        # Valid citation
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


class TestAPIErrorHandling:
    """Test API error handling."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_404_endpoint(self, client):
        """Test 404 handling."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_ingest_error_handling(self, client):
        """Test ingest error handling."""
        # Invalid source type
        request_data = {
            "source": "invalid",
            "repo_id": "test/repo"
        }
        
        response = client.post("/ingest", json=request_data)
        assert response.status_code == 422
    
    def test_query_error_handling(self, client):
        """Test query error handling."""
        # Invalid k value
        params = {
            "question": "test",
            "repo_ids": ["test/repo"],
            "k": -1  # Invalid
        }
        
        response = client.post("/query", json=params)
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
