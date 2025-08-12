"""
Tests for code chunking functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add the backend directory to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.chunking import chunk_file, is_text_file, should_skip_file, CodeChunk


class TestChunking:
    """Test cases for code chunking."""
    
    def test_chunk_python_file(self):
        """Test chunking a Python file."""
        python_code = '''
def hello_world():
    """Simple hello world function."""
    print("Hello, World!")
    return True

class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
'''
        
        chunks = chunk_file("test.py", python_code)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
        assert all(chunk.language == "python" for chunk in chunks)
        assert all(chunk.path == "test.py" for chunk in chunks)
    
    def test_chunk_javascript_file(self):
        """Test chunking a JavaScript file."""
        js_code = '''
function greet(name) {
    return `Hello, ${name}!`;
}

class User {
    constructor(name, email) {
        this.name = name;
        this.email = email;
    }
    
    getInfo() {
        return `${this.name} (${this.email})`;
    }
}
'''
        
        chunks = chunk_file("test.js", js_code)
        
        assert len(chunks) > 0
        assert all(chunk.language == "javascript" for chunk in chunks)
        assert all(chunk.path == "test.js" for chunk in chunks)
    
    def test_chunk_empty_file(self):
        """Test chunking an empty file."""
        chunks = chunk_file("empty.py", "")
        assert len(chunks) == 0
    
    def test_chunk_small_file(self):
        """Test chunking a very small file."""
        small_code = "print('hello')"
        chunks = chunk_file("small.py", small_code)
        
        assert len(chunks) > 0
        assert chunks[0].content.strip() == "print('hello')"
    
    def test_chunk_large_file(self):
        """Test chunking a large file with many lines."""
        large_code = "\n".join([f"line_{i} = {i}" for i in range(1000)])
        chunks = chunk_file("large.py", large_code)
        
        assert len(chunks) > 1  # Should be split into multiple chunks
        assert all(len(chunk.content.split('\n')) <= 50 for chunk in chunks)  # Rough chunk size check
    
    def test_chunk_metadata(self):
        """Test that chunk metadata is correct."""
        code = '''
def test_function():
    pass
'''
        chunks = chunk_file("test.py", code)
        
        for chunk in chunks:
            assert chunk.start_line > 0
            assert chunk.end_line >= chunk.start_line
            assert chunk.content_hash is not None
            assert len(chunk.content_hash) > 0
    
    def test_language_detection(self):
        """Test language detection from file extensions."""
        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.ts", "typescript"),
            ("test.jsx", "javascript"),
            ("test.tsx", "typescript"),
            ("test.java", "java"),
            ("test.cpp", "cpp"),
            ("test.go", "go"),
            ("test.rs", "rust"),
            ("test.unknown", "unknown"),
        ]
        
        for filename, expected_lang in test_cases:
            chunks = chunk_file(filename, "test content")
            if chunks:
                assert chunks[0].language == expected_lang


class TestFileFiltering:
    """Test cases for file filtering."""
    
    def test_is_text_file(self):
        """Test text file detection."""
        # Test text files
        assert is_text_file("test.py", b"print('hello')")
        assert is_text_file("test.js", b"console.log('hello')")
        assert is_text_file("test.txt", b"plain text")
        assert is_text_file("test.json", b'{"key": "value"}')
        
        # Test binary files
        assert not is_text_file("test.exe", b"\x00\x01\x02\x03")
        assert not is_text_file("test.png", b"\x89PNG\r\n\x1a\n")
        assert not is_text_file("test.jpg", b"\xff\xd8\xff")
    
    def test_should_skip_file(self):
        """Test file skipping logic."""
        # Test files that should be skipped
        assert should_skip_file(".git/config", 100)
        assert should_skip_file("node_modules/package.json", 100)
        assert should_skip_file("dist/bundle.js", 100)
        assert should_skip_file("build/output.o", 100)
        assert should_skip_file("test.exe", 100)
        assert should_skip_file("large_file.py", 1024 * 1024)  # 1MB file
        
        # Test files that should not be skipped
        assert not should_skip_file("src/main.py", 100)
        assert not should_skip_file("app.js", 100)
        assert not should_skip_file("README.md", 100)
        assert not should_skip_file("config.json", 100)


class TestCodeChunk:
    """Test cases for CodeChunk class."""
    
    def test_chunk_creation(self):
        """Test creating a CodeChunk."""
        chunk = CodeChunk(
            content="def test(): pass",
            path="test.py",
            start_line=1,
            end_line=1,
            language="python",
            chunk_type="function"
        )
        
        assert chunk.content == "def test(): pass"
        assert chunk.path == "test.py"
        assert chunk.start_line == 1
        assert chunk.end_line == 1
        assert chunk.language == "python"
        assert chunk.chunk_type == "function"
        assert chunk.content_hash is not None
    
    def test_chunk_hash_consistency(self):
        """Test that chunk hash is consistent for same content."""
        chunk1 = CodeChunk("test content", "test.py", 1, 1, "python")
        chunk2 = CodeChunk("test content", "test.py", 1, 1, "python")
        
        assert chunk1.content_hash == chunk2.content_hash
    
    def test_chunk_hash_uniqueness(self):
        """Test that different content produces different hashes."""
        chunk1 = CodeChunk("content 1", "test.py", 1, 1, "python")
        chunk2 = CodeChunk("content 2", "test.py", 1, 1, "python")
        
        assert chunk1.content_hash != chunk2.content_hash
    
    def test_chunk_to_dict(self):
        """Test converting chunk to dictionary."""
        chunk = CodeChunk(
            content="test content",
            path="test.py",
            start_line=1,
            end_line=5,
            language="python",
            chunk_type="function"
        )
        
        chunk_dict = chunk.to_dict()
        
        assert chunk_dict["content"] == "test content"
        assert chunk_dict["path"] == "test.py"
        assert chunk_dict["start_line"] == 1
        assert chunk_dict["end_line"] == 5
        assert chunk_dict["language"] == "python"
        assert chunk_dict["chunk_type"] == "function"
        assert chunk_dict["content_hash"] == chunk.content_hash


if __name__ == "__main__":
    pytest.main([__file__])
