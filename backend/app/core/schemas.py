"""
Pydantic schemas for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class IngestRequest(BaseModel):
    """Request model for repository ingestion."""
    source: str = Field(..., description="Source type: 'github' or 'zip'")
    url: Optional[str] = Field(None, description="GitHub repository URL")
    branch: Optional[str] = Field("main", description="GitHub branch to clone")
    repo_id: str = Field(..., description="Repository identifier (e.g., 'org/repo')")
    include_globs: List[str] = Field(
        default=["**/*.py", "**/*.ts", "**/*.js"],
        description="File patterns to include"
    )
    exclude_globs: List[str] = Field(
        default=[".git/**", "node_modules/**", "dist/**", "build/**", ".venv/**"],
        description="File patterns to exclude"
    )


class IngestResponse(BaseModel):
    """Response model for repository ingestion."""
    repo_id: str
    files_processed: int
    chunks_stored: int
    commit_sha: Optional[str] = None
    elapsed_time: float = Field(..., description="Processing time in seconds")
    status: str = "success"


class Citation(BaseModel):
    """Citation model for code references."""
    path: str = Field(..., description="File path")
    start: int = Field(..., description="Start line number")
    end: int = Field(..., description="End line number")
    score: float = Field(..., description="Relevance score")
    content: Optional[str] = Field(None, description="Code excerpt")
    url: Optional[str] = Field(None, description="Optional deep link")
    preview: Optional[str] = Field(None, description="Short preview for list views")


class Snippet(BaseModel):
    """Code snippet with surrounding context."""
    path: str = Field(..., description="File path")
    start: int = Field(..., description="Original match start line")
    end: int = Field(..., description="Original match end line")
    window_start: int = Field(..., description="Context window start line")
    window_end: int = Field(..., description="Context window end line")
    code: str = Field(..., description="Code with surrounding context")


class QueryRequest(BaseModel):
    """Request model for codebase queries."""
    question: str = Field(..., description="Natural language question about the codebase")
    repo_ids: List[str] = Field(..., description="Repository IDs to search in")
    k: int = Field(default=6, description="Number of chunks to retrieve")


class QueryResponse(BaseModel):
    """Response model for codebase queries."""
    answer: str = Field(..., description="Generated answer with citations")
    citations: List[Citation] = Field(..., description="List of code citations")
    snippets: List[Snippet] = Field(..., description="Code snippets with context")
    latency_ms: int = Field(..., description="Query latency in milliseconds")
    mode: Optional[str] = Field(None, description="Query mode (mock/gpt4)")
    confidence: Optional[float] = Field(None, description="Answer confidence score")


class HealthResponse(BaseModel):
    """Response model for health check."""
    ok: bool = Field(..., description="Service health status")
    timestamp: float = Field(..., description="Current timestamp")


class Repository(BaseModel):
    """Repository model."""
    repo_id: str
    name: str
    file_count: int
    chunk_count: int


class StatsResponse(BaseModel):
    """Response model for service statistics."""
    repositories: List[Repository]
    total_repositories: int
    total_files: int
    total_chunks: int


class ChunkMetadata(BaseModel):
    """Metadata for a code chunk."""
    repo_id: str
    commit_sha: Optional[str]
    path: str
    language: str
    start_line: int
    end_line: int
    content_hash: str
    embedding_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RepositoryInfo(BaseModel):
    """Information about a repository."""
    repo_id: str
    commit_sha: Optional[str]
    files_count: int
    chunks_count: int
    last_updated: datetime
    size_mb: float



