"""
Ingestion service for processing GitHub repositories and ZIP files.
"""

import os
import tempfile
import zipfile
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import git
import structlog
from fastapi import UploadFile

from ..core.config import settings
from ..core.schemas import IngestRequest, IngestResponse
from ..core.chunking import chunk_file, should_skip_file, is_text_file
from ..core.vector_store import VectorStoreManager
from .embedding import EmbeddingService

logger = structlog.get_logger()


class IngestionService:
    """Service for ingesting repositories and building vector indexes."""
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.embedding_service = EmbeddingService()
    
    async def initialize(self):
        """Initialize the ingestion service."""
        # Ensure directories exist
        os.makedirs(settings.index_dir, exist_ok=True)
        os.makedirs(settings.temp_dir, exist_ok=True)
        logger.info("Ingestion service initialized")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.vector_store_manager.close_all()
        logger.info("Ingestion service cleaned up")
    
    async def ingest_repository(self, request: IngestRequest) -> IngestResponse:
        """Ingest a GitHub repository."""
        start_time = time.time()
        
        try:
            if request.source == "github":
                result = await self._ingest_github_repo(request)
            elif request.source == "zip":
                raise ValueError("Use ingest_zip_file for ZIP uploads")
            else:
                raise ValueError(f"Unsupported source type: {request.source}")
            
            elapsed_time = time.time() - start_time
            result.elapsed_time = elapsed_time
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Ingestion failed after {elapsed_time:.2f}s: {e}")
            raise
    
    async def ingest_zip_file(self, file: UploadFile, request: IngestRequest) -> IngestResponse:
        """Ingest a ZIP file containing repository code."""
        start_time = time.time()
        
        try:
            if request.source != "zip":
                raise ValueError("Source must be 'zip' for ZIP file ingestion")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save uploaded file
                zip_path = os.path.join(temp_dir, "upload.zip")
                with open(zip_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                
                # Extract ZIP file
                extract_path = os.path.join(temp_dir, "extracted")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Process extracted files
                result = await self._process_files(extract_path, request)
                
                elapsed_time = time.time() - start_time
                result.elapsed_time = elapsed_time
                return result
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"ZIP ingestion failed after {elapsed_time:.2f}s: {e}")
            raise
    
    async def _ingest_github_repo(self, request: IngestRequest) -> IngestResponse:
        """Ingest a GitHub repository by cloning it."""
        if not request.url:
            raise ValueError("GitHub URL is required for GitHub ingestion")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "repo")
            
            try:
                # Clone repository
                logger.info(f"Cloning repository: {request.url}")
                repo = git.Repo.clone_from(
                    request.url,
                    repo_path,
                    branch=request.branch or "main",
                    depth=1  # Shallow clone for speed
                )
                
                commit_sha = repo.head.commit.hexsha
                logger.info(f"Cloned repository, commit: {commit_sha}")
                
                # Process files
                result = await self._process_files(repo_path, request)
                result.commit_sha = commit_sha
                
                return result
                
            except Exception as e:
                logger.error(f"Failed to clone repository {request.url}: {e}")
                raise
    
    async def _process_files(
        self,
        root_path: str,
        request: IngestRequest
    ) -> IngestResponse:
        """Process files in a directory and build the index."""
        # Get vector store for this repository
        vector_store = self.vector_store_manager.get_store(request.repo_id)
        
        # Find all files
        all_files = self._find_files(root_path, request.include_globs, request.exclude_globs)
        
        files_processed = 0
        chunks_stored = 0
        
        # Process files in batches
        batch_size = 10  # Process 10 files at a time
        for i in range(0, len(all_files), batch_size):
            batch_files = all_files[i:i + batch_size]
            
            batch_chunks = []
            batch_texts = []
            
            for file_path in batch_files:
                try:
                    file_chunks = await self._process_single_file(file_path, root_path)
                    if file_chunks:
                        batch_chunks.extend(file_chunks)
                        batch_texts.extend([chunk.content for chunk in file_chunks])
                        files_processed += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue
            
            # Compute embeddings for batch
            if batch_chunks:
                embeddings = await self.embedding_service.embed_texts(batch_texts)
                
                # Add to vector store
                stored_count = vector_store.add_chunks(batch_chunks, embeddings)
                chunks_stored += stored_count
        
        logger.info(
            f"Ingestion completed for {request.repo_id}",
            files_processed=files_processed,
            chunks_stored=chunks_stored
        )
        
        return IngestResponse(
            repo_id=request.repo_id,
            files_processed=files_processed,
            chunks_stored=chunks_stored,
            elapsed_time=0.0,  # This will be set by the calling method
            status="success"
        )
    
    def _find_files(
        self,
        root_path: str,
        include_globs: List[str],
        exclude_globs: List[str]
    ) -> List[str]:
        """Find files matching include/exclude patterns."""
        from pathspec import PathSpec
        from pathspec.patterns import GitWildMatchPattern
        
        # Build pathspec for include/exclude patterns
        include_spec = PathSpec.from_lines(GitWildMatchPattern, include_globs)
        exclude_spec = PathSpec.from_lines(GitWildMatchPattern, exclude_globs)
        
        files = []
        root_path_obj = Path(root_path)
        
        for file_path in root_path_obj.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Convert to relative path for pattern matching
            rel_path = str(file_path.relative_to(root_path))
            
            # Check if file should be included
            if not include_spec.match_file(rel_path):
                continue
            
            # Check if file should be excluded
            if exclude_spec.match_file(rel_path):
                continue
            
            # Check file size
            file_size = file_path.stat().st_size
            if should_skip_file(rel_path, file_size):
                continue
            
            files.append(str(file_path))
        
        logger.info(f"Found {len(files)} files to process")
        return files
    
    async def _process_single_file(self, file_path: str, root_path: str) -> List:
        """Process a single file and return chunks."""
        from ..core.chunking import CodeChunk
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return []
        
        # Check if it's a text file
        if not is_text_file(file_path, content_bytes):
            return []
        
        # Decode content
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode file {file_path} as UTF-8")
            return []
        
        # Normalize content
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Get relative path
        rel_path = os.path.relpath(file_path, root_path)
        
        # Chunk the file
        chunks = chunk_file(rel_path, content)
        
        return chunks
    
    async def delete_repository(self, repo_id: str):
        """Delete a repository from the index."""
        self.vector_store_manager.delete_repo(repo_id)
        logger.info(f"Deleted repository {repo_id}")
    
    async def get_repository_stats(self, repo_id: str) -> Dict[str, Any]:
        """Get statistics for a specific repository."""
        try:
            vector_store = self.vector_store_manager.get_store(repo_id)
            return vector_store.get_stats()
        except Exception as e:
            logger.error(f"Failed to get stats for {repo_id}: {e}")
            return {}
