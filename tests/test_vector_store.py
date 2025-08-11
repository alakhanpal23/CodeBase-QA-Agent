"""
Tests for vector store functionality.
"""

import pytest
import tempfile
import os
import numpy as np
from pathlib import Path

# Add the backend directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.vector_store import VectorStore, VectorStoreManager
from app.core.chunking import CodeChunk


class TestVectorStore:
    """Test cases for VectorStore class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def vector_store(self, temp_dir, monkeypatch):
        """Create a VectorStore instance for testing."""
        # Mock the settings to use temp directory
        monkeypatch.setattr("app.core.config.settings.index_dir", temp_dir)
        
        store = VectorStore("test/repo")
        yield store
        store.close()
    
    def test_vector_store_initialization(self, vector_store):
        """Test vector store initialization."""
        assert vector_store.repo_id == "test/repo"
        assert vector_store.index is not None
        assert vector_store.metadata_db is not None
    
    def test_add_chunks(self, vector_store):
        """Test adding chunks to the vector store."""
        # Create test chunks
        chunks = [
            CodeChunk("def test1(): pass", "test1.py", 1, 1, "python"),
            CodeChunk("def test2(): pass", "test2.py", 1, 1, "python"),
        ]
        
        # Create test embeddings
        embeddings = [
            [0.1, 0.2, 0.3] * 512,  # 1536 dimensions
            [0.4, 0.5, 0.6] * 512,
        ]
        
        # Add chunks
        stored_count = vector_store.add_chunks(chunks, embeddings)
        
        assert stored_count == 2
        assert vector_store.index.ntotal == 2
    
    def test_search(self, vector_store):
        """Test searching in the vector store."""
        # Add test data
        chunks = [
            CodeChunk("def test1(): pass", "test1.py", 1, 1, "python"),
            CodeChunk("def test2(): pass", "test2.py", 1, 1, "python"),
        ]
        
        embeddings = [
            [0.1, 0.2, 0.3] * 512,
            [0.4, 0.5, 0.6] * 512,
        ]
        
        vector_store.add_chunks(chunks, embeddings)
        
        # Search
        query_embedding = [0.1, 0.2, 0.3] * 512
        results = vector_store.search(query_embedding, k=2)
        
        assert len(results) == 2
        assert all("score" in result for result in results)
        assert all("path" in result for result in results)
    
    def test_search_empty_index(self, vector_store):
        """Test searching in an empty index."""
        query_embedding = [0.1, 0.2, 0.3] * 512
        results = vector_store.search(query_embedding, k=5)
        
        assert len(results) == 0
    
    def test_get_stats(self, vector_store):
        """Test getting vector store statistics."""
        # Add some test data
        chunks = [
            CodeChunk("def test1(): pass", "test1.py", 1, 1, "python"),
            CodeChunk("def test2(): pass", "test2.py", 1, 1, "python"),
        ]
        
        embeddings = [
            [0.1, 0.2, 0.3] * 512,
            [0.4, 0.5, 0.6] * 512,
        ]
        
        vector_store.add_chunks(chunks, embeddings)
        
        # Get stats
        stats = vector_store.get_stats()
        
        assert stats["total_chunks"] == 2
        assert stats["unique_files"] == 2
        assert "python" in stats["languages"]
        assert stats["languages"]["python"] == 2
        assert stats["faiss_ntotal"] == 2
    
    def test_delete_repo(self, vector_store):
        """Test deleting repository data."""
        # Add some data first
        chunks = [CodeChunk("test content", "test.py", 1, 1, "python")]
        embeddings = [[0.1, 0.2, 0.3] * 512]
        vector_store.add_chunks(chunks, embeddings)
        
        # Delete
        vector_store.delete_repo()
        
        # Check that files are deleted
        assert not os.path.exists(vector_store.index_path)
        assert not os.path.exists(vector_store.metadata_path)


class TestVectorStoreManager:
    """Test cases for VectorStoreManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def manager(self, temp_dir, monkeypatch):
        """Create a VectorStoreManager instance for testing."""
        # Mock the settings to use temp directory
        monkeypatch.setattr("app.core.config.settings.index_dir", temp_dir)
        
        manager = VectorStoreManager()
        yield manager
        manager.close_all()
    
    def test_get_store(self, manager):
        """Test getting a vector store."""
        store1 = manager.get_store("test/repo1")
        store2 = manager.get_store("test/repo2")
        store3 = manager.get_store("test/repo1")  # Should return same instance
        
        assert store1.repo_id == "test/repo1"
        assert store2.repo_id == "test/repo2"
        assert store1 is store3  # Same instance
    
    def test_search_multiple(self, manager):
        """Test searching across multiple repositories."""
        # Add data to multiple stores
        store1 = manager.get_store("test/repo1")
        store2 = manager.get_store("test/repo2")
        
        chunks1 = [CodeChunk("content1", "test1.py", 1, 1, "python")]
        chunks2 = [CodeChunk("content2", "test2.py", 1, 1, "python")]
        
        embeddings1 = [[0.1, 0.2, 0.3] * 512]
        embeddings2 = [[0.4, 0.5, 0.6] * 512]
        
        store1.add_chunks(chunks1, embeddings1)
        store2.add_chunks(chunks2, embeddings2)
        
        # Search across both repositories
        query_embedding = [0.1, 0.2, 0.3] * 512
        results = manager.search_multiple(
            query_embedding,
            ["test/repo1", "test/repo2"],
            k=5
        )
        
        assert len(results) == 2
        assert any("test1.py" in result["path"] for result in results)
        assert any("test2.py" in result["path"] for result in results)
    
    def test_get_all_stats(self, manager):
        """Test getting statistics for all repositories."""
        # Add data to multiple stores
        store1 = manager.get_store("test/repo1")
        store2 = manager.get_store("test/repo2")
        
        chunks1 = [CodeChunk("content1", "test1.py", 1, 1, "python")]
        chunks2 = [CodeChunk("content2", "test2.py", 1, 1, "python")]
        
        embeddings1 = [[0.1, 0.2, 0.3] * 512]
        embeddings2 = [[0.4, 0.5, 0.6] * 512]
        
        store1.add_chunks(chunks1, embeddings1)
        store2.add_chunks(chunks2, embeddings2)
        
        # Get all stats
        stats = manager.get_all_stats()
        
        assert stats["total_repos"] == 2
        assert stats["total_chunks"] == 2
        assert stats["total_files"] == 2
        assert "test/repo1" in stats["repos"]
        assert "test/repo2" in stats["repos"]
    
    def test_delete_repo(self, manager):
        """Test deleting a repository."""
        # Add data
        store = manager.get_store("test/repo")
        chunks = [CodeChunk("content", "test.py", 1, 1, "python")]
        embeddings = [[0.1, 0.2, 0.3] * 512]
        store.add_chunks(chunks, embeddings)
        
        # Delete
        manager.delete_repo("test/repo")
        
        # Check that store is removed
        assert "test/repo" not in manager.stores
    
    def test_close_all(self, manager):
        """Test closing all vector stores."""
        # Add some stores
        manager.get_store("test/repo1")
        manager.get_store("test/repo2")
        
        assert len(manager.stores) == 2
        
        # Close all
        manager.close_all()
        
        assert len(manager.stores) == 0


class TestVectorStoreIntegration:
    """Integration tests for vector store functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def manager(self, temp_dir, monkeypatch):
        """Create a VectorStoreManager instance for testing."""
        monkeypatch.setattr("app.core.config.settings.index_dir", temp_dir)
        
        manager = VectorStoreManager()
        yield manager
        manager.close_all()
    
    def test_full_workflow(self, manager):
        """Test a complete workflow: add chunks, search, get stats."""
        # Create test data
        chunks = [
            CodeChunk("def authenticate(): pass", "auth.py", 1, 1, "python"),
            CodeChunk("def validate_token(): pass", "auth.py", 2, 2, "python"),
            CodeChunk("def login(): pass", "auth.py", 3, 3, "python"),
        ]
        
        # Create embeddings (simulating similarity)
        embeddings = [
            [0.1, 0.2, 0.3] * 512,  # auth-related
            [0.1, 0.2, 0.3] * 512,  # auth-related
            [0.1, 0.2, 0.3] * 512,  # auth-related
        ]
        
        # Add to store
        store = manager.get_store("test/auth-repo")
        stored_count = store.add_chunks(chunks, embeddings)
        
        assert stored_count == 3
        
        # Search for auth-related content
        query_embedding = [0.1, 0.2, 0.3] * 512
        results = store.search(query_embedding, k=3)
        
        assert len(results) == 3
        assert all("auth.py" in result["path"] for result in results)
        
        # Get stats
        stats = store.get_stats()
        assert stats["total_chunks"] == 3
        assert stats["unique_files"] == 1
        assert stats["languages"]["python"] == 3


if __name__ == "__main__":
    pytest.main([__file__])
