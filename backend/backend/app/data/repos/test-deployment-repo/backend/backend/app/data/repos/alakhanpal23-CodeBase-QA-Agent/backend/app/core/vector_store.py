"""
Vector store implementation using FAISS for indexing and retrieval.
"""

import os
import pickle
import json
import numpy as np
import faiss
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import structlog

from .config import settings
from .chunking import CodeChunk

logger = structlog.get_logger()


class VectorStore:
    """FAISS-based vector store with metadata management."""
    
    def __init__(self, repo_id: str, embedding_dimension: int = None):
        self.repo_id = repo_id
        self.index_path = os.path.join(settings.index_dir, f"{repo_id.replace('/', '_')}.faiss")
        self.metadata_path = os.path.join(settings.index_dir, f"{repo_id.replace('/', '_')}_metadata.db")
        self.meta_path = os.path.join(settings.index_dir, f"{repo_id.replace('/', '_')}.meta.json")
        self.index = None
        self.metadata_db = None
        self.embedding_dimension = embedding_dimension or settings.embedding_dimension
        self._initialize()
    
    def _initialize(self):
        """Initialize FAISS index and metadata database."""
        # Initialize metadata database
        self._init_metadata_db()
        
        # Initialize or load FAISS index
        if os.path.exists(self.index_path):
            self._load_index()
        else:
            self._create_index()
    
    def _init_metadata_db(self):
        """Initialize SQLite database for metadata."""
        self.metadata_db = sqlite3.connect(self.metadata_path)
        cursor = self.metadata_db.cursor()
        
        # Enable WAL mode for better performance
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                embedding_id TEXT PRIMARY KEY,
                repo_id TEXT NOT NULL,
                commit_sha TEXT,
                path TEXT NOT NULL,
                language TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                chunk_type TEXT NOT NULL,
                faiss_row INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_repo_id ON chunks(repo_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_path ON chunks(path)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_faiss_row ON chunks(faiss_row)
        ''')
        
        self.metadata_db.commit()
    
    def _save_meta(self):
        """Save metadata about the index."""
        meta = {
            "embedding_dimension": self.embedding_dimension,
            "repo_id": self.repo_id,
            "created_at": str(np.datetime64('now'))
        }
        with open(self.meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
    
    def _load_meta(self) -> Optional[Dict[str, Any]]:
        """Load metadata about the index."""
        if os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load meta for {self.repo_id}: {e}")
        return None
    
    def _create_index(self):
        """Create a new FAISS index."""
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        self._save_meta()
        logger.info(f"Created new FAISS index for {self.repo_id} with dimension {self.embedding_dimension}")
    
    def _load_index(self):
        """Load existing FAISS index."""
        try:
            # Check embedding dimension consistency
            meta = self._load_meta()
            if meta and meta.get("embedding_dimension") != self.embedding_dimension:
                raise ValueError(
                    f"Embedding dimension mismatch for {self.repo_id}: "
                    f"index={meta.get('embedding_dimension')} current={self.embedding_dimension}. "
                    f"Ingest again with the same embedding mode, or set EMBED_MODE to match."
                )
            
            self.index = faiss.read_index(self.index_path)
            logger.info(f"Loaded existing FAISS index for {self.repo_id} with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to load index for {self.repo_id}: {e}")
            self._create_index()
    
    def _save_index(self):
        """Save FAISS index to disk."""
        try:
            faiss.write_index(self.index, self.index_path)
            self._save_meta()
            logger.info(f"Saved FAISS index for {self.repo_id}")
        except Exception as e:
            logger.error(f"Failed to save index for {self.repo_id}: {e}")
    
    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        return (vectors / norms).astype(np.float32)
    
    def add_chunks(self, chunks: List[CodeChunk], embeddings: List[List[float]]) -> int:
        """Add chunks and their embeddings to the index."""
        if not chunks or not embeddings:
            return 0
        
        # Convert embeddings to numpy array and normalize
        embeddings_array = np.array(embeddings, dtype=np.float32)
        embeddings_array = self._normalize_vectors(embeddings_array)
        
        # Get current index size for faiss_row assignment
        base_row = self.index.ntotal
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store metadata
        cursor = self.metadata_db.cursor()
        for i, chunk in enumerate(chunks):
            embedding_id = f"{chunk.content_hash}_{i}"
            faiss_row = base_row + i
            
            cursor.execute('''
                INSERT OR REPLACE INTO chunks 
                (embedding_id, repo_id, path, language, start_line, end_line, 
                 content_hash, chunk_type, faiss_row)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                embedding_id,
                self.repo_id,
                chunk.path,
                chunk.language,
                chunk.start_line,
                chunk.end_line,
                chunk.content_hash,
                chunk.chunk_type,
                faiss_row
            ))
        
        self.metadata_db.commit()
        self._save_index()
        
        logger.info(f"Added {len(chunks)} chunks to {self.repo_id}")
        return len(chunks)
    
    def search(self, query_embedding: List[float], k: int = 6) -> List[Dict[str, Any]]:
        """Search for similar chunks."""
        if self.index.ntotal == 0:
            return []
        
        # Normalize query vector
        query_array = np.array([query_embedding], dtype=np.float32)
        query_array = self._normalize_vectors(query_array)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_array, min(k, self.index.ntotal))
        
        # Retrieve metadata for results
        results = []
        cursor = self.metadata_db.cursor()
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
            
            # Get metadata by faiss_row
            cursor.execute('''
                SELECT embedding_id, repo_id, path, language, start_line, end_line,
                       content_hash, chunk_type
                FROM chunks
                WHERE faiss_row = ?
            ''', (int(idx),))
            
            row = cursor.fetchone()
            if row:
                results.append({
                    "embedding_id": row[0],
                    "repo_id": row[1],
                    "path": row[2],
                    "language": row[3],
                    "start_line": row[4],
                    "end_line": row[5],
                    "content_hash": row[6],
                    "chunk_type": row[7],
                    "score": float(score)
                })
        
        return results
    
    def get_chunk_content(self, embedding_id: str) -> Optional[str]:
        """Get chunk content by embedding ID."""
        cursor = self.metadata_db.cursor()
        cursor.execute('''
            SELECT path, start_line, end_line
            FROM chunks
            WHERE embedding_id = ?
        ''', (embedding_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # This is a simplified approach - in production you'd store the content
        # or have a way to reconstruct it from the file
        return f"Content from {row[0]}:{row[1]}-{row[2]}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        cursor = self.metadata_db.cursor()
        
        # Total chunks
        cursor.execute('SELECT COUNT(*) FROM chunks')
        total_chunks = cursor.fetchone()[0]
        
        # Unique files
        cursor.execute('SELECT COUNT(DISTINCT path) FROM chunks')
        unique_files = cursor.fetchone()[0]
        
        # Languages
        cursor.execute('SELECT language, COUNT(*) FROM chunks GROUP BY language')
        languages = dict(cursor.fetchall())
        
        # Index size
        index_size_mb = os.path.getsize(self.index_path) / (1024 * 1024) if os.path.exists(self.index_path) else 0
        
        return {
            "total_chunks": total_chunks,
            "unique_files": unique_files,
            "languages": languages,
            "index_size_mb": index_size_mb,
            "faiss_ntotal": self.index.ntotal if self.index else 0
        }
    
    def delete_repo(self):
        """Delete all data for this repository."""
        try:
            # Close database connection
            if self.metadata_db:
                self.metadata_db.close()
            
            # Remove files
            if os.path.exists(self.index_path):
                os.remove(self.index_path)
            if os.path.exists(self.metadata_path):
                os.remove(self.metadata_path)
            if os.path.exists(self.meta_path):
                os.remove(self.meta_path)
            
            logger.info(f"Deleted all data for repository {self.repo_id}")
        except Exception as e:
            logger.error(f"Failed to delete data for {self.repo_id}: {e}")
    
    def close(self):
        """Close database connection."""
        if self.metadata_db:
            self.metadata_db.close()


class VectorStoreManager:
    """Manages multiple vector stores for different repositories."""
    
    def __init__(self):
        self.stores: Dict[str, VectorStore] = {}
        self._scan_existing_stores()
    
    def _scan_existing_stores(self):
        """Scan for existing stores on disk and load them."""
        try:
            if not os.path.exists(settings.index_dir):
                return
            
            for filename in os.listdir(settings.index_dir):
                if filename.endswith('.faiss'):
                    # Extract repo_id from filename (e.g., "fastapi_fastapi.faiss" -> "fastapi/fastapi")
                    repo_id = filename[:-5].replace('_', '/')
                    if repo_id not in self.stores:
                        try:
                            # Try to load the meta file to get the embedding dimension
                            meta_path = os.path.join(settings.index_dir, f"{repo_id.replace('/', '_')}.meta.json")
                            embedding_dimension = None
                            if os.path.exists(meta_path):
                                try:
                                    with open(meta_path, 'r') as f:
                                        meta = json.load(f)
                                        embedding_dimension = meta.get("embedding_dimension")
                                except Exception as e:
                                    logger.warning(f"Failed to load meta for {repo_id}: {e}")
                            
                            self.stores[repo_id] = VectorStore(repo_id, embedding_dimension)
                            logger.info(f"Loaded existing store for {repo_id}")
                        except Exception as e:
                            logger.error(f"Failed to load store for {repo_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to scan existing stores: {e}")
    
    def get_store(self, repo_id: str) -> VectorStore:
        """Get or create vector store for a repository."""
        if repo_id not in self.stores:
            # Get embedding dimension from the embedder
            from ..core.embeddings import get_embedder
            embedder = get_embedder()
            embedding_dimension = embedder.embedding_dimension
            self.stores[repo_id] = VectorStore(repo_id, embedding_dimension)
        return self.stores[repo_id]
    
    def search_multiple(self, query_embedding: List[float], repo_ids: List[str], k: int = 6) -> List[Dict[str, Any]]:
        """Search across multiple repositories."""
        all_results = []
        
        for repo_id in repo_ids:
            try:
                store = self.get_store(repo_id)
                results = store.search(query_embedding, k)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Failed to search in {repo_id}: {e}")
        
        # Sort by score and return top k
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:k]
    
    def delete_repo(self, repo_id: str):
        """Delete a repository from all stores."""
        if repo_id in self.stores:
            self.stores[repo_id].delete_repo()
            del self.stores[repo_id]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all repositories."""
        stats = {
            "total_repos": len(self.stores),
            "total_chunks": 0,
            "total_files": 0,
            "index_size_mb": 0,
            "repos": {}
        }
        
        for repo_id, store in self.stores.items():
            try:
                repo_stats = store.get_stats()
                stats["total_chunks"] += repo_stats["total_chunks"]
                stats["total_files"] += repo_stats["unique_files"]
                stats["index_size_mb"] += repo_stats["index_size_mb"]
                stats["repos"][repo_id] = repo_stats
            except Exception as e:
                logger.error(f"Failed to get stats for {repo_id}: {e}")
        
        return stats
    
    def close_all(self):
        """Close all vector stores."""
        for store in self.stores.values():
            store.close()
        self.stores.clear()
