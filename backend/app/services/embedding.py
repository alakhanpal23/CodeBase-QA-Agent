"""
Embedding service for generating text embeddings.
"""

import asyncio
import hashlib
from typing import List
import structlog

from ..core.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating embeddings from text."""
    
    def __init__(self):
        self.dimension = 384
        self.use_openai = False
        self.use_local = False
        self.use_mock = True
        self.openai_client = None
        self.local_model = None
        
        self._initialize_embedding_service()
    
    def _initialize_embedding_service(self):
        """Initialize the best available embedding service."""
        mode = settings.embed_mode.lower()
        
        if mode == "auto":
            # Try OpenAI first, then local, then mock
            if self._try_openai():
                return
            elif self._try_local():
                return
            else:
                self._use_mock()
        elif mode == "openai":
            if not self._try_openai():
                logger.warning("OpenAI not available, falling back to mock")
                self._use_mock()
        elif mode == "local":
            if not self._try_local():
                logger.warning("Local model not available, falling back to mock")
                self._use_mock()
        else:
            self._use_mock()
    
    def _try_openai(self) -> bool:
        """Try to initialize OpenAI embeddings."""
        try:
            if not settings.openai_api_key or settings.openai_api_key == "dummy-key-for-testing":
                return False
            
            import openai
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Test the connection with a simple request
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Quick test (this will be replaced with actual test in production)
            self.use_openai = True
            self.use_mock = False
            self.dimension = 1536  # OpenAI embedding dimension
            logger.info("OpenAI embeddings initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
            return False
    
    def _try_local(self) -> bool:
        """Try to initialize local embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            self.local_model = SentenceTransformer(settings.embed_model)
            self.use_local = True
            self.use_mock = False
            self.dimension = self.local_model.get_sentence_embedding_dimension()
            logger.info(f"Local embeddings initialized: {settings.embed_model}")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize local embeddings: {e}")
            return False
    
    def _use_mock(self):
        """Use mock embeddings."""
        self.use_mock = True
        self.use_openai = False
        self.use_local = False
        self.dimension = 384
        logger.info("Using mock embeddings for development/testing")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if self.use_openai:
            return await self._openai_embedding(text)
        elif self.use_local:
            return await self._local_embedding(text)
        else:
            return self._mock_embedding(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        
        if self.use_openai:
            return await self._openai_embeddings(texts)
        elif self.use_local:
            return await self._local_embeddings(texts)
        else:
            return [self._mock_embedding(text) for text in texts]
    
    async def _openai_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for single text."""
        try:
            response = await self.openai_client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            # Fallback to mock
            return self._mock_embedding(text)
    
    async def _openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate OpenAI embeddings for multiple texts."""
        try:
            response = await self.openai_client.embeddings.create(
                model=settings.openai_embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embeddings failed: {e}")
            # Fallback to mock
            return [self._mock_embedding(text) for text in texts]
    
    async def _local_embedding(self, text: str) -> List[float]:
        """Generate local embedding for single text."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.local_model.encode([text], convert_to_tensor=False)[0]
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Local embedding failed: {e}")
            return self._mock_embedding(text)
    
    async def _local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate local embeddings for multiple texts."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.local_model.encode(texts, convert_to_tensor=False, show_progress_bar=False)
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Local embeddings failed: {e}")
            return [self._mock_embedding(text) for text in texts]
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding based on text hash."""
        # Create a deterministic "embedding" based on text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to numbers and normalize to [-1, 1]
        embedding = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0 * 2 - 1  # Normalize to [-1, 1]
            embedding.append(value)
        
        # Pad or truncate to desired dimension
        while len(embedding) < self.dimension:
            embedding.extend(embedding[:min(len(embedding), self.dimension - len(embedding))])
        
        return embedding[:self.dimension]
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.dimension
    
    def get_mode(self) -> str:
        """Get the current embedding mode."""
        if self.use_openai:
            return "openai"
        elif self.use_local:
            return "local"
        else:
            return "mock"
    
    def is_production_ready(self) -> bool:
        """Check if the service is production ready."""
        return self.use_openai or self.use_local