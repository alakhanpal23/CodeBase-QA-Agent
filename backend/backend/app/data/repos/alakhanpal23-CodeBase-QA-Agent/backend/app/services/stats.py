"""
Statistics service for tracking system metrics.
"""

import structlog
from typing import Dict, Any, List
from ..core.schemas import StatsResponse, Repository
from ..core.vector_store import VectorStoreManager

logger = structlog.get_logger()


class StatsService:
    """Service for collecting and providing system statistics."""
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
    
    async def initialize(self):
        """Initialize the stats service."""
        logger.info("Stats service initialized")
    
    async def get_stats(self) -> StatsResponse:
        """Get comprehensive system statistics."""
        try:
            repositories = await self.get_repositories()
            
            total_files = sum(repo.file_count for repo in repositories)
            total_chunks = sum(repo.chunk_count for repo in repositories)
            
            return StatsResponse(
                repositories=repositories,
                total_repositories=len(repositories),
                total_files=total_files,
                total_chunks=total_chunks
            )
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return StatsResponse(
                repositories=[],
                total_repositories=0,
                total_files=0,
                total_chunks=0
            )
    
    async def get_repositories(self) -> List[Repository]:
        """Get list of all repositories with their statistics."""
        repositories = []
        
        try:
            # Get all repository IDs from vector store manager
            repo_ids = self.vector_store_manager.list_repositories()
            
            for repo_id in repo_ids:
                try:
                    vector_store = self.vector_store_manager.get_store(repo_id)
                    stats = vector_store.get_stats()
                    
                    repository = Repository(
                        repo_id=repo_id,
                        name=repo_id.replace("-", " ").title(),  # Simple name formatting
                        file_count=stats.get("file_count", 0),
                        chunk_count=stats.get("chunk_count", 0)
                    )
                    repositories.append(repository)
                    
                except Exception as e:
                    logger.warning(f"Failed to get stats for repository {repo_id}: {e}")
                    # Add repository with zero stats
                    repository = Repository(
                        repo_id=repo_id,
                        name=repo_id.replace("-", " ").title(),
                        file_count=0,
                        chunk_count=0
                    )
                    repositories.append(repository)
            
        except Exception as e:
            logger.error(f"Failed to list repositories: {e}")
        
        return repositories