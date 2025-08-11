"""
Query service for handling codebase queries.
"""

import time
from typing import List, Dict, Any, Optional
import structlog

from ..core.schemas import QueryRequest, QueryResponse, Citation, Snippet
from ..core.vector_store import VectorStoreManager
from .embedding import EmbeddingService
from .rag import RAGService
from .snippets import extract_snippet

logger = structlog.get_logger()


class QueryService:
    """Service for processing codebase queries."""
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.embedding_service = EmbeddingService()
        self.rag_service = RAGService()
    
    async def initialize(self):
        """Initialize the query service."""
        logger.info("Query service initialized")
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Query service cleaned up")
    
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Process a query and return an answer with citations."""
        start_time = time.time()
        
        try:
            # Check if repositories exist
            for repo_id in request.repo_ids:
                store = self.vector_store_manager.get_store(repo_id)
                if store.index.ntotal == 0:
                    latency_ms = int((time.time() - start_time) * 1000)
                    return QueryResponse(
                        answer=f"No indexed data found for repository '{repo_id}'. Please ingest the repository first.",
                        citations=[],
                        snippets=[],
                        latency_ms=latency_ms
                    )
            
            # Embed the question
            question_embedding = await self.embedding_service.embed_text(request.question)
            
            if not question_embedding:
                latency_ms = int((time.time() - start_time) * 1000)
                return QueryResponse(
                    answer="Failed to process the question. Please try again.",
                    citations=[],
                    snippets=[],
                    latency_ms=latency_ms
                )
            
            # Retrieve relevant chunks
            retrieved_chunks = self.vector_store_manager.search_multiple(
                question_embedding,
                request.repo_ids,
                request.k
            )
            
            if not retrieved_chunks:
                latency_ms = int((time.time() - start_time) * 1000)
                return QueryResponse(
                    answer="I couldn't find any relevant code to answer your question. Please try rephrasing or check if the repositories have been properly indexed.",
                    citations=[],
                    snippets=[],
                    latency_ms=latency_ms
                )
            
            # Generate answer using RAG
            answer, citations = await self.rag_service.generate_answer(
                request.question,
                retrieved_chunks
            )
            
            # Validate answer
            is_valid = await self.rag_service.validate_answer(answer, citations)
            
            # If answer lacks citations, try with more chunks
            if not is_valid and len(retrieved_chunks) < request.k + 2:
                logger.warning("Answer lacks citations, retrying with more chunks")
                more_chunks = self.vector_store_manager.search_multiple(
                    question_embedding,
                    request.repo_ids,
                    request.k + 2
                )
                if more_chunks:
                    answer, citations = await self.rag_service.generate_answer(
                        request.question,
                        more_chunks
                    )
            
            # Extract snippets from citations
            snippets = []
            for citation in citations:
                repo_id = request.repo_ids[0] if request.repo_ids else "unknown"
                
                snippet_data = extract_snippet(
                    repo_id=repo_id,
                    rel_path=citation.path,
                    start=citation.start,
                    end=citation.end
                )
                
                if snippet_data:
                    window_start, window_end, code = snippet_data
                    
                    # Add short preview to citation
                    preview_lines = code.splitlines()[:6]
                    citation.preview = "\n".join(preview_lines) if preview_lines else None
                    
                    # Create snippet
                    snippet = Snippet(
                        path=citation.path,
                        start=citation.start,
                        end=citation.end,
                        window_start=window_start,
                        window_end=window_end,
                        code=code
                    )
                    snippets.append(snippet)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return QueryResponse(
                answer=answer,
                citations=citations,
                snippets=snippets,
                latency_ms=latency_ms,
                mode="mock" if hasattr(self.rag_service, 'use_mock') and self.rag_service.use_mock else "gpt4"
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Query failed after {latency_ms}ms: {e}")
            return QueryResponse(
                answer=f"An error occurred while processing your query: {str(e)}",
                citations=[],
                snippets=[],
                latency_ms=latency_ms
            )
    
    async def search_only(self, request: QueryRequest) -> List[Citation]:
        """Search for relevant chunks without generating an answer."""
        # Check if repositories exist
        for repo_id in request.repo_ids:
            store = self.vector_store_manager.get_store(repo_id)
            if store.index.ntotal == 0:
                return []
        
        # Embed the question
        question_embedding = await self.embedding_service.embed_text(request.question)
        
        if not question_embedding:
            return []
        
        # Retrieve relevant chunks
        retrieved_chunks = self.vector_store_manager.search_multiple(
            question_embedding,
            request.repo_ids,
            request.k
        )
        
        return retrieved_chunks
    
    async def get_similar_chunks(self, text: str, repo_ids: List[str], k: int = 5) -> List[Citation]:
        """Find chunks similar to the given text."""
        # Embed the text
        text_embedding = await self.embedding_service.embed_text(text)
        
        if not text_embedding:
            return []
        
        # Search for similar chunks
        return self.vector_store_manager.search_multiple(text_embedding, repo_ids, k)
    
    async def get_chunk_content(self, repo_id: str, chunk_id: str) -> Optional[str]:
        """Get the content of a specific chunk."""
        try:
            store = self.vector_store_manager.get_store(repo_id)
            return store.get_chunk_content(chunk_id)
        except Exception as e:
            logger.error(f"Failed to get chunk content: {e}")
            return None
    
    async def get_query_stats(self) -> Dict[str, Any]:
        """Get statistics about query performance."""
        return {
            "embedding_stats": await self.embedding_service.get_embedding_stats(),
            "rag_stats": await self.rag_service.get_rag_stats()
        }
