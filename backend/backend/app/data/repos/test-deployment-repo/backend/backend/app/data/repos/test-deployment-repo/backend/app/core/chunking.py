"""
Code chunking utilities with syntax-aware chunking using tree-sitter.
"""

import os
import hashlib
import tiktoken
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import structlog

logger = structlog.get_logger()

# Try to import tree-sitter, fallback gracefully if not available
try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.warning("tree-sitter not available, using fallback chunking")

from .config import settings


class CodeChunk:
    """Represents a chunk of code with metadata."""
    
    def __init__(
        self,
        content: str,
        path: str,
        start_line: int,
        end_line: int,
        language: str,
        chunk_type: str = "unknown"
    ):
        self.content = content
        self.path = path
        self.start_line = start_line
        self.end_line = end_line
        self.language = language
        self.chunk_type = chunk_type
        self.content_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash of chunk content."""
        return hashlib.md5(self.content.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "content": self.content,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "chunk_type": self.chunk_type,
            "content_hash": self.content_hash
        }


class TreeSitterChunker:
    """Syntax-aware chunking using tree-sitter."""
    
    def __init__(self):
        self.parsers = {}
        self._initialize_parsers()
    
    def _initialize_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        if not TREE_SITTER_AVAILABLE:
            return
        
        try:
            # Initialize parsers for supported languages
            languages = {
                'python': 'tree_sitter_python',
                'javascript': 'tree_sitter_javascript',
                'typescript': 'tree_sitter_typescript'
            }
            
            for lang, module in languages.items():
                try:
                    # This is a simplified approach - in production you'd build the language library
                    parser = Parser()
                    # Note: This would need proper tree-sitter language library setup
                    # For now, we'll use the fallback chunker
                    self.parsers[lang] = parser
                except Exception as e:
                    logger.warning(f"Failed to initialize parser for {lang}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter parsers: {e}")
    
    def chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk a file using tree-sitter if available, otherwise fallback."""
        if not TREE_SITTER_AVAILABLE:
            return self._fallback_chunk_file(file_path, content)
        
        language = self._detect_language(file_path)
        if language not in self.parsers:
            return self._fallback_chunk_file(file_path, content)
        
        try:
            return self._tree_sitter_chunk(file_path, content, language)
        except Exception as e:
            logger.warning(f"Tree-sitter chunking failed for {file_path}, using fallback: {e}")
            return self._fallback_chunk_file(file_path, content)
    
    def _tree_sitter_chunk(self, file_path: str, content: str, language: str) -> List[CodeChunk]:
        """Chunk using tree-sitter (placeholder implementation)."""
        # This is a placeholder - in a full implementation, you would:
        # 1. Parse the code with tree-sitter
        # 2. Extract function/class definitions
        # 3. Create chunks for each function/class
        # 4. Handle nested structures appropriately
        
        # For now, return fallback chunking
        return self._fallback_chunk_file(file_path, content)
    
    def _fallback_chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        """Fallback chunking using line-based windows."""
        language = self._detect_language(file_path)
        lines = content.split('\n')
        
        # Calculate chunk size in lines (approximate)
        encoding = tiktoken.get_encoding("cl100k_base")
        avg_tokens_per_line = 10  # Rough estimate
        lines_per_chunk = max(1, settings.max_chunk_tokens // avg_tokens_per_line)
        overlap_lines = max(1, settings.chunk_overlap_tokens // avg_tokens_per_line)
        
        chunks = []
        
        for i in range(0, len(lines), lines_per_chunk - overlap_lines):
            end_line = min(i + lines_per_chunk, len(lines))
            chunk_lines = lines[i:end_line]
            chunk_content = '\n'.join(chunk_lines)
            
            # Skip empty chunks
            if not chunk_content.strip():
                continue
            
            chunk = CodeChunk(
                content=chunk_content,
                path=file_path,
                start_line=i + 1,  # 1-indexed
                end_line=end_line,
                language=language,
                chunk_type="line_window"
            )
            chunks.append(chunk)
        
        return chunks
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        return language_map.get(ext, 'unknown')


def chunk_file(file_path: str, content: str) -> List[CodeChunk]:
    """Main function to chunk a file."""
    chunker = TreeSitterChunker()
    return chunker.chunk_file(file_path, content)


def is_text_file(file_path: str, content: bytes) -> bool:
    """Check if a file is text-based."""
    # Check file extension
    text_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
        '.go', '.rs', '.php', '.rb', '.cs', '.swift', '.kt', '.scala', '.md',
        '.txt', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.sql',
        '.html', '.css', '.scss', '.sass', '.less', '.xml', '.svg'
    }
    
    ext = Path(file_path).suffix.lower()
    if ext in text_extensions:
        return True
    
    # Check if content is text (simple heuristic)
    try:
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False


def should_skip_file(file_path: str, file_size: int) -> bool:
    """Determine if a file should be skipped during ingestion."""
    # Skip files that are too large
    if file_size > settings.max_file_size_bytes:
        return True
    
    # Skip binary files and common build artifacts
    skip_patterns = {
        '.git', '.svn', '.hg', '.bzr',
        'node_modules', 'vendor', 'dist', 'build', 'target',
        '.venv', 'venv', 'env', '__pycache__',
        '.DS_Store', 'Thumbs.db',
        '.exe', '.dll', '.so', '.dylib', '.a', '.o',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx'
    }
    
    file_path_lower = file_path.lower()
    for pattern in skip_patterns:
        if pattern in file_path_lower:
            return True
    
    return False
