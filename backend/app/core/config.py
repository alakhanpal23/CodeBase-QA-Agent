"""
Configuration management using Pydantic settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Embedding Configuration
    embed_mode: str = "auto"  # Options: openai | local | mock | auto
    embed_model: str = "all-MiniLM-L6-v2"
    embed_batch_size: int = 64
    embedding_dimension: int = 1536
    
    # Production Configuration
    environment: str = "development"  # development | production
    enable_analytics: bool = True
    max_concurrent_requests: int = 10
    
    # Storage Configuration
    index_dir: str = "backend/app/data/indexes"
    meta_db_uri: str = "sqlite:///backend/app/data/meta.sqlite"
    temp_dir: str = "backend/app/data/temp"
    
    # Chunking Configuration
    max_chunk_tokens: int = 300  # Reduced for speed
    chunk_overlap_tokens: int = 50   # Reduced for speed
    max_file_size_bytes: int = 262144  # 250KB - smaller files
    max_files_per_repo: int = 100      # Limit files for demo
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Snippet Configuration
    snippet_context_lines: int = 6          # lines of context before/after a hit
    snippet_max_chars: int = 1200           # hard cap to avoid huge payloads
    repos_dir: str = "backend/app/data/repos"  # base dir where repos are stored
    
    # Security
    max_repo_size_mb: int = 50   # Smaller repos for speed
    rate_limit_per_minute: int = 60
    
    # Performance
    query_timeout_seconds: int = 5
    ingestion_timeout_seconds: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def ensure_directories():
    """Ensure all required directories exist."""
    os.makedirs(settings.index_dir, exist_ok=True)
    os.makedirs(settings.temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.meta_db_uri.replace("sqlite:///", "")), exist_ok=True)
