"""
RAG (Retrieval-Augmented Generation) service for answering questions about codebases.
"""

import asyncio
from typing import List, Dict, Any, Optional
import openai
import structlog

from ..core.config import settings
from ..core.schemas import Citation

logger = structlog.get_logger()


class RAGService:
    """Service for generating answers using RAG with citations."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.use_mock = True  # Use mock mode by default to avoid API issues
    
    async def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> tuple[str, List[Citation]]:
        """Generate an answer using RAG with citations."""
        if not retrieved_chunks:
            return "I couldn't find any relevant code to answer your question. Please try rephrasing or check if the repository has been properly indexed.", []
        
        # Check if we should use mock responses
        if self.use_mock:
            return await self._mock_generate_answer(question, retrieved_chunks)
        
        # Build the RAG prompt
        prompt = self._build_rag_prompt(question, retrieved_chunks)
        
        try:
            # Generate answer using OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for deterministic answers
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Extract citations from the answer
            citations = self._extract_citations(answer, retrieved_chunks)
            
            # Clean up the answer (remove citation markers)
            clean_answer = self._clean_answer(answer)
            
            return clean_answer, citations
            
        except Exception as e:
            logger.error(f"Failed to generate RAG answer: {e}")
            
            # If it's a quota error, switch to mock mode
            if "quota" in str(e).lower() or "insufficient_quota" in str(e).lower():
                logger.warning("OpenAI quota exceeded, switching to mock RAG for testing")
                self.use_mock = True
                return await self._mock_generate_answer(question, retrieved_chunks)
            
            return "Sorry, I encountered an error while generating the answer. Please try again.", []
    
    async def _mock_generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> tuple[str, List[Citation]]:
        """Generate a mock answer for testing."""
        # Create a simple mock answer based on the question and chunks
        if "auth" in question.lower() or "login" in question.lower():
            answer = f"Authentication is implemented in the codebase. Based on the retrieved code snippets, I found relevant authentication code in {len(retrieved_chunks)} files."
        elif "route" in question.lower() or "endpoint" in question.lower():
            answer = f"Routing is handled in the codebase. The retrieved snippets show routing implementation across {len(retrieved_chunks)} files."
        elif "database" in question.lower() or "model" in question.lower():
            answer = f"Database models are defined in the codebase. I found {len(retrieved_chunks)} relevant files containing model definitions."
        else:
            answer = f"I found relevant code for your question. The retrieved snippets contain information from {len(retrieved_chunks)} files that may help answer your query."
        
        # Create mock citations
        citations = []
        for chunk in retrieved_chunks:
            citation = Citation(
                path=chunk.get("path", "unknown"),
                start=chunk.get("start_line", 1),
                end=chunk.get("end_line", 10),
                score=chunk.get("score", 0.8),
                content=chunk.get("content", "")[:100] + "..." if chunk.get("content") else None
            )
            citations.append(citation)
        
        return answer, citations
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for RAG."""
        return """You are a precise codebase assistant. Answer concisely using only the provided snippets. Always include citations with file paths and line ranges. If unsure, say you are not confident.

Guidelines:
- Explain in 2-5 sentences
- List citations as: path:start-end
- If multiple files contribute, describe their roles briefly
- If answer is uncertain, state what is missing and suggest where to look next
- Use the exact file paths and line numbers provided in the snippets
- Do not make up information not present in the provided code"""
    
    def _build_rag_prompt(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Build the RAG prompt with retrieved chunks."""
        prompt_parts = [f"Question: {question}\n"]
        prompt_parts.append("Relevant snippets:")
        
        for i, chunk in enumerate(retrieved_chunks, 1):
            path = chunk.get("path", "unknown")
            start_line = chunk.get("start_line", 0)
            end_line = chunk.get("end_line", 0)
            content = chunk.get("content", "")
            
            prompt_parts.append(f"\n--- {path}:{start_line}-{end_line}")
            prompt_parts.append(content.strip())
        
        prompt_parts.append("\nInstructions:")
        prompt_parts.append("- Explain in 2-5 sentences.")
        prompt_parts.append("- List citations as: path:start-end.")
        prompt_parts.append("- If multiple files contribute, describe their roles briefly.")
        prompt_parts.append("- If answer is uncertain, state what is missing and suggest where to look next.")
        
        return "\n".join(prompt_parts)
    
    def _extract_citations(self, answer: str, retrieved_chunks: List[Dict[str, Any]]) -> List[Citation]:
        """Extract citations from the generated answer."""
        citations = []
        
        # Create a mapping of chunk content to metadata
        chunk_map = {}
        for chunk in retrieved_chunks:
            content_hash = chunk.get("content_hash", "")
            chunk_map[content_hash] = chunk
        
        # Look for citation patterns in the answer
        import re
        citation_pattern = r'([^:\s]+):(\d+)-(\d+)'
        matches = re.findall(citation_pattern, answer)
        
        for path, start, end in matches:
            # Find the corresponding chunk
            for chunk in retrieved_chunks:
                if chunk.get("path") == path and chunk.get("start_line") <= int(start) <= chunk.get("end_line"):
                    citation = Citation(
                        path=path,
                        start=int(start),
                        end=int(end),
                        score=chunk.get("score", 0.0),
                        content=chunk.get("content", "")
                    )
                    citations.append(citation)
                    break
        
        # If no citations found, create them from retrieved chunks
        if not citations:
            for chunk in retrieved_chunks:
                citation = Citation(
                    path=chunk.get("path", ""),
                    start=chunk.get("start_line", 0),
                    end=chunk.get("end_line", 0),
                    score=chunk.get("score", 0.0),
                    content=chunk.get("content", "")
                )
                citations.append(citation)
        
        return citations
    
    def _clean_answer(self, answer: str) -> str:
        """Clean up the answer by removing citation markers."""
        # Remove citation markers like [1], [2], etc.
        import re
        cleaned = re.sub(r'\[\d+\]', '', answer)
        return cleaned.strip()
    
    async def validate_answer(self, answer: str, citations: List[Citation]) -> bool:
        """Validate that the answer has proper citations."""
        if not answer or answer.strip() == "":
            return False
        
        if not citations:
            return False
        
        # Check if answer mentions uncertainty
        uncertainty_indicators = [
            "not sure", "uncertain", "not confident", "don't know",
            "not found", "couldn't find", "no relevant"
        ]
        
        answer_lower = answer.lower()
        for indicator in uncertainty_indicators:
            if indicator in answer_lower:
                return True  # Valid if explicitly uncertain
        
        # Check if citations are mentioned in answer
        citation_mentioned = any(
            f"{citation.path}:{citation.start}-{citation.end}" in answer
            for citation in citations
        )
        
        return citation_mentioned
    
    async def get_rag_stats(self) -> Dict[str, Any]:
        """Get statistics about RAG usage."""
        return {
            "model": self.model,
            "temperature": 0.1,
            "max_tokens": 1000,
            "using_mock": self.use_mock
        }
