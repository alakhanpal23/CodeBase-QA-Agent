"""
Embedding service using the resilient embedder with multiple modes.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
import structlog

from ..core.embeddings import get_embedder, embed_texts, embed_text

logger = structlog.get_logger()


class EmbeddingService:
    """Service for computing embeddings using the resilient embedder."""
    
    def __init__(self):
        self.embedder = get_embedder()
        self.batch_size = 64  # Default batch size
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using the configured embedder."""
        if not texts:
            return []
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = await embed_texts(batch)
            embeddings.extend(batch_embeddings)
            
            # Small delay between batches for rate limiting
            if i + self.batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return embeddings
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        return await embed_text(text)
    
    async def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding has the correct dimension."""
        return len(embedding) == self.embedder.embedding_dimension
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about embedding usage."""
        embedder_stats = self.embedder.get_stats()
        return {
            **embedder_stats,
            "batch_size": self.batch_size
        }
