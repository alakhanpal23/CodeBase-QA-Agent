"""
Vector store management for storing and retrieving code embeddings.
"""

import os
import pickle
import numpy as np
import faiss
import structlog
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import settings
from .chunking import CodeChunk

logger = structlog.get_logger()


class VectorStore:
    """FAISS-based vector store for a single repository."""
    
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.dimension = 384  # sentence-transformers dimension
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.chunks: List[CodeChunk] = []
        self.metadata: Dict[str, Any] = {}
        
        # File paths
        self.store_dir = os.path.join(settings.index_dir, repo_id)
        self.index_path = os.path.join(self.store_dir, "index.faiss")
        self.chunks_path = os.path.join(self.store_dir, "chunks.pkl")
        self.metadata_path = os.path.join(self.store_dir, "metadata.pkl")
        
        # Create directory
        os.makedirs(self.store_dir, exist_ok=True)
        
        # Load existing data
        self._load()
    
    def _load(self):
        """Load existing index and chunks."""
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                logger.info(f"Loaded FAISS index for {self.repo_id} with {self.index.ntotal} vectors")
            
            if os.path.exists(self.chunks_path):
                with open(self.chunks_path, 'rb') as f:
                    self.chunks = pickle.load(f)
                logger.info(f"Loaded {len(self.chunks)} chunks for {self.repo_id}")
            
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
        
        except Exception as e:
            logger.warning(f"Failed to load existing data for {self.repo_id}: {e}")
            self._reset()
    
    def _reset(self):
        """Reset the vector store."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks = []
        self.metadata = {}
    
    def _save(self):
        """Save index and chunks to disk."""
        try:
            faiss.write_index(self.index, self.index_path)
            
            with open(self.chunks_path, 'wb') as f:
                pickle.dump(self.chunks, f)
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
                
        except Exception as e:
            logger.error(f"Failed to save vector store for {self.repo_id}: {e}")
            raise
    
    def add_chunks(self, chunks: List[CodeChunk], embeddings: List[List[float]]) -> int:
        """Add chunks with their embeddings to the store."""
        if not chunks or not embeddings:
            return 0
        
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Add chunks
        self.chunks.extend(chunks)
        
        # Update metadata
        self.metadata.update({
            "last_updated": np.datetime64('now').item().timestamp(),
            "total_chunks": len(self.chunks)
        })
        
        # Save to disk
        self._save()
        
        logger.info(f"Added {len(chunks)} chunks to {self.repo_id}")
        return len(chunks)
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks."""
        if self.index.ntotal == 0:
            return []
        
        # Convert to numpy array and normalize
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(query_array, k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    "path": chunk.path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "content": chunk.content,
                    "score": float(score),
                    "content_hash": chunk.content_hash
                })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about this vector store."""
        # Count unique files
        unique_files = set()
        for chunk in self.chunks:
            unique_files.add(chunk.path)
        
        return {
            "repo_id": self.repo_id,
            "chunk_count": len(self.chunks),
            "file_count": len(unique_files),
            "index_size": self.index.ntotal,
            "last_updated": self.metadata.get("last_updated", 0)
        }
    
    def delete(self):
        """Delete the vector store."""
        try:
            import shutil
            if os.path.exists(self.store_dir):
                shutil.rmtree(self.store_dir)
            logger.info(f"Deleted vector store for {self.repo_id}")
        except Exception as e:
            logger.error(f"Failed to delete vector store for {self.repo_id}: {e}")


class VectorStoreManager:
    """Manager for multiple vector stores."""
    
    def __init__(self):
        self.stores: Dict[str, VectorStore] = {}
        os.makedirs(settings.index_dir, exist_ok=True)
    
    def get_store(self, repo_id: str) -> VectorStore:
        """Get or create a vector store for a repository."""
        if repo_id not in self.stores:
            self.stores[repo_id] = VectorStore(repo_id)
        return self.stores[repo_id]
    
    def delete_repo(self, repo_id: str):
        """Delete a repository's vector store."""
        if repo_id in self.stores:
            self.stores[repo_id].delete()
            del self.stores[repo_id]
        else:
            # Try to delete from disk even if not in memory
            store = VectorStore(repo_id)
            store.delete()
    
    def list_repositories(self) -> List[str]:
        """List all repository IDs."""
        repo_ids = []
        
        # Check disk for existing repositories
        if os.path.exists(settings.index_dir):
            for item in os.listdir(settings.index_dir):
                item_path = os.path.join(settings.index_dir, item)
                if os.path.isdir(item_path):
                    repo_ids.append(item)
        
        # Add any in-memory repositories
        for repo_id in self.stores.keys():
            if repo_id not in repo_ids:
                repo_ids.append(repo_id)
        
        return sorted(repo_ids)
    
    def search_multiple(self, repo_ids: List[str], query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search across multiple repositories."""
        all_results = []
        
        for repo_id in repo_ids:
            try:
                store = self.get_store(repo_id)
                results = store.search(query_embedding, k)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Failed to search repository {repo_id}: {e}")
        
        # Sort by score and return top k
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:k]
    
    def close_all(self):
        """Close all vector stores."""
        self.stores.clear()
        logger.info("Closed all vector stores")