"""
Snippet extraction service for retrieving code with surrounding context.
"""

import os
from typing import Optional, Tuple, List
from ..core.config import settings

_TEXT_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".go", ".rb", ".rs", ".php", ".cs",
    ".c", ".h", ".hpp", ".cc", ".cpp", ".m", ".mm", ".swift", ".sh", ".bash", ".zsh",
    ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".env",
    ".md", ".rst", ".txt", ".html", ".css", ".scss", ".sql"
}


def _is_probably_text(path: str, first_bytes: bytes) -> bool:
    """Check if a file is likely to be text-based."""
    if b"\x00" in first_bytes:
        return False
    ext = os.path.splitext(path)[1].lower()
    if ext in _TEXT_EXTS:
        return True
    # Fallback: treat small ASCII-ish chunks as text
    asciiish = sum(1 for b in first_bytes if 9 <= b <= 126 or b in (10, 13))
    return asciiish / max(1, len(first_bytes)) > 0.85


def _safe_repo_path(repo_id: str, rel_path: str) -> str:
    """Safely construct repository file path preventing path traversal."""
    root = os.path.abspath(os.path.join(settings.repos_dir, repo_id))
    candidate = os.path.abspath(os.path.join(root, rel_path))
    if not candidate.startswith(root + os.sep) and candidate != root:
        raise ValueError("Path traversal detected")
    return candidate


def extract_snippet(
    repo_id: str,
    rel_path: str,
    start: int,
    end: int,
    context_lines: int = None,
    max_chars: int = None,
) -> Optional[Tuple[int, int, str]]:
    """
    Extract code snippet with surrounding context.
    
    Args:
        repo_id: Repository identifier
        rel_path: Relative path to file within repository
        start: Start line number (1-based inclusive)
        end: End line number (1-based inclusive)
        context_lines: Lines of context before/after
        max_chars: Maximum characters to return
    
    Returns:
        Tuple of (window_start, window_end, code) or None if file not readable/text
    """
    context_lines = context_lines or settings.snippet_context_lines
    max_chars = max_chars or settings.snippet_max_chars

    abspath = _safe_repo_path(repo_id, rel_path)
    if not os.path.exists(abspath) or not os.path.isfile(abspath):
        return None

    try:
        # Check if file is text
        with open(abspath, "rb") as f:
            head = f.read(2048)
            if not _is_probably_text(rel_path, head):
                return None
        
        # Read file lines
        with open(abspath, "r", encoding="utf-8", errors="replace") as f:
            lines: List[str] = f.readlines()
    except Exception:
        return None

    n = len(lines)
    if n == 0:
        return None

    # Calculate context window
    window_start = max(1, start - context_lines)
    window_end = min(n, end + context_lines)

    # Extract lines (convert to 0-based indexing)
    block = "".join(lines[window_start-1:window_end])
    
    # Trim to max chars if needed
    if len(block) > max_chars:
        # Try to keep the center around the original [start,end]
        keep = max_chars
        head_keep = keep // 2
        tail_keep = keep - head_keep
        block = block[:head_keep] + "\n...\n" + block[-tail_keep:]

    return (window_start, window_end, block)