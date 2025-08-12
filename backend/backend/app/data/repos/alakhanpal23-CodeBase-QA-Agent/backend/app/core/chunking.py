"""
Code chunking utilities for processing source files.
"""

import os
import hashlib
from typing import List, Optional
from dataclasses import dataclass
import tiktoken

# File extensions to process
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.kt', '.go', '.rb', '.rs', '.php', '.cs',
    '.c', '.h', '.hpp', '.cc', '.cpp', '.m', '.mm', '.swift', '.sh', '.bash', '.zsh',
    '.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.env',
    '.md', '.rst', '.txt', '.html', '.css', '.scss', '.sql'
}

# Files to skip
SKIP_PATTERNS = {
    '.git', '.svn', '.hg', '__pycache__', '.pytest_cache', 'node_modules',
    '.venv', 'venv', '.env', 'dist', 'build', '.next', '.nuxt',
    'coverage', '.coverage', '.nyc_output', 'target', 'bin', 'obj'
}

# Maximum file size (1MB)
MAX_FILE_SIZE = 1024 * 1024


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    path: str
    content: str
    start_line: int
    end_line: int
    content_hash: str
    language: Optional[str] = None
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()


def should_skip_file(file_path: str, file_size: int) -> bool:
    """Check if a file should be skipped during processing."""
    # Check file size
    if file_size > MAX_FILE_SIZE:
        return True
    
    # Check if path contains skip patterns
    path_parts = file_path.lower().split(os.sep)
    for part in path_parts:
        if part in SKIP_PATTERNS:
            return True
        if part.startswith('.') and len(part) > 1:
            return True
    
    return False


def is_text_file(file_path: str, content_bytes: bytes) -> bool:
    """Check if a file is likely to be a text file."""
    # Check extension
    ext = os.path.splitext(file_path)[1].lower()
    if ext in TEXT_EXTENSIONS:
        return True
    
    # Check for binary content
    if b'\x00' in content_bytes[:1024]:  # Check first 1KB for null bytes
        return False
    
    # Check if mostly ASCII
    try:
        content_bytes.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False


def get_language_from_extension(file_path: str) -> Optional[str]:
    """Get programming language from file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.java': 'java',
        '.kt': 'kotlin',
        '.go': 'go',
        '.rb': 'ruby',
        '.rs': 'rust',
        '.php': 'php',
        '.cs': 'csharp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cc': 'cpp',
        '.cpp': 'cpp',
        '.m': 'objective-c',
        '.mm': 'objective-c',
        '.swift': 'swift',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.json': 'json',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.env': 'bash',
        '.md': 'markdown',
        '.rst': 'rst',
        '.txt': 'text',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sql': 'sql'
    }
    
    return language_map.get(ext)


def chunk_file(file_path: str, content: str, max_chunk_size: int = 1000) -> List[CodeChunk]:
    """Chunk a file into smaller pieces for embedding."""
    if not content.strip():
        return []
    
    lines = content.split('\n')
    chunks = []
    
    # Get language for syntax-aware chunking
    language = get_language_from_extension(file_path)
    
    # Use tiktoken for token counting
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback to character-based chunking
        encoding = None
    
    current_chunk = []
    current_size = 0
    start_line = 1
    
    for i, line in enumerate(lines, 1):
        line_size = len(encoding.encode(line)) if encoding else len(line)
        
        # If adding this line would exceed max size, create a chunk
        if current_chunk and current_size + line_size > max_chunk_size:
            chunk_content = '\n'.join(current_chunk)
            if chunk_content.strip():
                chunks.append(CodeChunk(
                    path=file_path,
                    content=chunk_content,
                    start_line=start_line,
                    end_line=i - 1,
                    content_hash="",  # Will be generated in __post_init__
                    language=language
                ))
            
            # Start new chunk
            current_chunk = [line]
            current_size = line_size
            start_line = i
        else:
            current_chunk.append(line)
            current_size += line_size
    
    # Add final chunk
    if current_chunk:
        chunk_content = '\n'.join(current_chunk)
        if chunk_content.strip():
            chunks.append(CodeChunk(
                path=file_path,
                content=chunk_content,
                start_line=start_line,
                end_line=len(lines),
                content_hash="",  # Will be generated in __post_init__
                language=language
            ))
    
    return chunks