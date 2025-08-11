"""
Snippet extraction service for retrieving code with surrounding context.
"""

import os
from typing import Optional, Tuple
import structlog

from ..core.config import settings

logger = structlog.get_logger()


def extract_snippet(
    repo_id: str,
    rel_path: str,
    start: int,
    end: int,
    context_lines: int = None
) -> Optional[Tuple[int, int, str]]:
    """
    Extract a code snippet with surrounding context.
    
    Args:
        repo_id: Repository identifier
        rel_path: Relative path to the file
        start: Start line number (1-indexed)
        end: End line number (1-indexed)
        context_lines: Number of context lines before/after (default from settings)
    
    Returns:
        Tuple of (window_start, window_end, code) or None if extraction fails
    """
    if context_lines is None:
        context_lines = settings.snippet_context_lines
    
    try:
        # Construct full file path
        file_path = os.path.join(settings.repos_dir, repo_id, rel_path)
        
        # Security check: ensure path is within repo directory
        repo_dir = os.path.join(settings.repos_dir, repo_id)
        if not _is_safe_path(file_path, repo_dir):
            logger.warning(f"Unsafe path detected: {file_path}")
            return None
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            except Exception as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                return None
        
        if not lines:
            return None
        
        total_lines = len(lines)
        
        # Convert to 0-indexed
        start_idx = max(0, start - 1)
        end_idx = min(total_lines, end)
        
        # Calculate window with context
        window_start = max(1, start - context_lines)
        window_end = min(total_lines, end + context_lines)
        
        # Extract lines (convert back to 0-indexed for slicing)
        window_start_idx = window_start - 1
        window_end_idx = window_end
        
        snippet_lines = lines[window_start_idx:window_end_idx]
        
        # Join lines and ensure we don't exceed max chars
        code = ''.join(snippet_lines)
        
        if len(code) > settings.snippet_max_chars:
            # Truncate while trying to preserve line boundaries
            truncated = code[:settings.snippet_max_chars]
            last_newline = truncated.rfind('\n')
            if last_newline > settings.snippet_max_chars * 0.8:  # If we can save most content
                code = truncated[:last_newline + 1]
            else:
                code = truncated + '\n... (truncated)'
        
        return window_start, window_end, code
        
    except Exception as e:
        logger.error(f"Failed to extract snippet from {rel_path}: {e}")
        return None


def _is_safe_path(file_path: str, base_dir: str) -> bool:
    """
    Check if the file path is safe (no directory traversal).
    
    Args:
        file_path: The file path to check
        base_dir: The base directory that should contain the file
    
    Returns:
        True if the path is safe, False otherwise
    """
    try:
        # Resolve both paths to absolute paths
        abs_file_path = os.path.abspath(file_path)
        abs_base_dir = os.path.abspath(base_dir)
        
        # Check if the file path starts with the base directory
        return abs_file_path.startswith(abs_base_dir + os.sep) or abs_file_path == abs_base_dir
        
    except Exception:
        return False


def get_file_language(file_path: str) -> str:
    """
    Determine the programming language from file extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Language identifier or 'text' if unknown
    """
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
    
    return language_map.get(ext, 'text')