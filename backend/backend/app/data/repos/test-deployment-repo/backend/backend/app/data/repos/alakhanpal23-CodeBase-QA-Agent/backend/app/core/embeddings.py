"""
Resilient embedding service with multiple modes and automatic fallback.
"""

import os
import time
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional
import structlog

from .config import settings

logger = structlog.get_logger()

# Get embedding mode from settings
EMBED_MODE = settings.embed_mode.lower()


class Embedder:
    """Resilient embedding service with multiple modes."""
    
    def __init__(self):
        self.mode = EMBED_MODE
        self._local_model = None
        self._openai_client = None
        
        # Set embedding dimension based on mode
        if self.mode == "local":
            self.embedding_dimension = 384  # Local model dimension
        elif self.mode == "mock":
            self.embedding_dimension = 384  # Mock mode dimension
        else:
            self.embedding_dimension = settings.embedding_dimension  # OpenAI dimension
        
        logger.info(f"Initializing embedder in {self.mode} mode with dimension {self.embedding_dimension}")
        
        if self.mode == "local":
            self._init_local_model()
        elif self.mode == "openai":
            self._init_openai_client()
        elif self.mode == "mock":
            logger.info("Using mock embeddings for testing")
        else:
            logger.warning(f"Unknown embed mode: {self.mode}, falling back to mock")
            self.mode = "mock"
            self.embedding_dimension = 384
    
    def _init_local_model(self):
        """Initialize local sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading local sentence transformer model...")
            self._local_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Local model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load local model: {e}, falling back to mock")
            self.mode = "mock"
    
    def _init_openai_client(self):
        """Initialize OpenAI client."""
        try:
            import openai
            api_key = settings.openai_api_key
            if not api_key:
                logger.error("No OpenAI API key found, falling back to mock")
                self.mode = "mock"
                return
            
            self._openai_client = openai.AsyncOpenAI(api_key=api_key)
            self._openai_model = settings.openai_embedding_model
            logger.info(f"OpenAI client initialized with model: {self._openai_model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}, falling back to mock")
            self.mode = "mock"
    
    def _mock_vec(self, text: str, dim: int = 384) -> List[float]:
        """Generate deterministic mock embedding."""
        # Use text hash as seed for consistent embeddings
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = np.random.default_rng(seed)
        v = rng.normal(size=dim)
        v = v / np.linalg.norm(v)  # Normalize
        return v.astype(np.float32).tolist()
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using the configured mode."""
        if not texts:
            return []
        
        logger.debug(f"Embedding {len(texts)} texts in {self.mode} mode")
        
        if self.mode == "mock":
            return [self._mock_vec(t, self.embedding_dimension) for t in texts]
        
        if self.mode == "local":
            return await self._embed_local(texts)
        
        if self.mode == "openai":
            return await self._embed_openai(texts)
        
        # Fallback to mock
        logger.warning(f"Unknown mode {self.mode}, using mock embeddings")
        return [self._mock_vec(t, self.embedding_dimension) for t in texts]
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text."""
        embeddings = await self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    async def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Embed using local sentence transformer."""
        try:
            start_time = time.time()
            embeddings = self._local_model.encode(texts, normalize_embeddings=True)
            elapsed = time.time() - start_time
            
            logger.debug(f"Local embedding completed in {elapsed:.2f}s")
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Local embedding failed: {e}, falling back to mock")
            return [self._mock_vec(t, self.embedding_dimension) for t in texts]
    
    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Embed using OpenAI API with fallback."""
        try:
            start_time = time.time()
            response = await self._openai_client.embeddings.create(
                input=texts,
                model=self._openai_model
            )
            embeddings = [embedding.embedding for embedding in response.data]
            elapsed = time.time() - start_time
            
            logger.debug(f"OpenAI embedding completed in {elapsed:.2f}s")
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}, falling back to mock")
            # If it's a quota error, switch to mock mode permanently
            if "quota" in str(e).lower() or "insufficient_quota" in str(e).lower():
                logger.warning("OpenAI quota exceeded, switching to mock mode")
                self.mode = "mock"
            
            return [self._mock_vec(t, self.embedding_dimension) for t in texts]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics."""
        return {
            "mode": self.mode,
            "dimension": self.embedding_dimension,
            "local_model_loaded": self._local_model is not None,
            "openai_client_loaded": self._openai_client is not None
        }


# Global embedder instance
_embedder = None


def get_embedder() -> Embedder:
    """Get the global embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convenience function to embed texts."""
    embedder = get_embedder()
    return await embedder.embed_texts(texts)


async def embed_text(text: str) -> List[float]:
    """Convenience function to embed a single text."""
    embedder = get_embedder()
    return await embedder.embed_text(text)
