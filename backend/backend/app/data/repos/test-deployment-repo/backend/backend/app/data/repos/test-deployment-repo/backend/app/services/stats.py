"""
Statistics service for monitoring system performance and usage.
"""

import os
import time
import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from ..core.config import settings

logger = structlog.get_logger()


class StatsService:
    """Service for collecting and providing system statistics."""
    
    def __init__(self):
        self.query_latencies = []  # Simple in-memory storage for demo
        self.last_ingest_time = None
    
    async def initialize(self):
        """Initialize the stats service."""
        logger.info("Stats service initialized")
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Stats service cleaned up")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        try:
            # Compute stats directly from database
            db_stats = self._get_database_stats()
            
            # Calculate index size
            index_size_mb = self._calculate_index_size()
            
            # Get average query latency
            avg_latency = self._calculate_avg_latency()
            
            stats = {
                "total_repos": db_stats.get("total_repos", 0),
                "total_files": db_stats.get("total_files", 0),
                "total_chunks": db_stats.get("total_chunks", 0),
                "index_size_mb": index_size_mb,
                "last_ingest_time": db_stats.get("last_ingest_time"),
                "avg_query_latency_ms": avg_latency,
                "repositories": db_stats.get("repositories", {}),
                "system_info": await self._get_system_info()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_repos": 0,
                "total_files": 0,
                "total_chunks": 0,
                "index_size_mb": 0,
                "last_ingest_time": None,
                "avg_query_latency_ms": None,
                "error": str(e)
            }
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Get statistics directly from the database."""
        stats = {
            "total_repos": 0,
            "total_files": 0,
            "total_chunks": 0,
            "repositories": {}
        }
        
        try:
            # Scan for all metadata databases
            if not os.path.exists(settings.index_dir):
                return stats
            
            for filename in os.listdir(settings.index_dir):
                if filename.endswith('_metadata.db'):
                    # Extract repo_id from filename
                    repo_id = filename[:-13].replace('_', '/')  # Remove '_metadata.db'
                    
                    db_path = os.path.join(settings.index_dir, filename)
                    repo_stats = self._get_repo_stats_from_db(db_path, repo_id)
                    
                    if repo_stats:
                        stats["total_repos"] += 1
                        stats["total_files"] += repo_stats.get("unique_files", 0)
                        stats["total_chunks"] += repo_stats.get("total_chunks", 0)
                        stats["repositories"][repo_id] = repo_stats
                        
                        # Track last ingest time
                        repo_last_ingest = repo_stats.get("last_ingest_time")
                        if repo_last_ingest:
                            if not stats.get("last_ingest_time") or repo_last_ingest > stats["last_ingest_time"]:
                                stats["last_ingest_time"] = repo_last_ingest
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
        
        return stats
    
    def _get_repo_stats_from_db(self, db_path: str, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific repository from its database."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if chunks table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'")
            if not cursor.fetchone():
                conn.close()
                return None
            
            # Get basic stats
            cursor.execute('SELECT COUNT(*) FROM chunks')
            total_chunks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT path) FROM chunks')
            unique_files = cursor.fetchone()[0]
            
            # Get languages
            cursor.execute('SELECT language, COUNT(*) FROM chunks GROUP BY language')
            languages = dict(cursor.fetchall())
            
            # Get last ingest time
            cursor.execute('SELECT MAX(created_at) FROM chunks')
            last_ingest = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_chunks": total_chunks,
                "unique_files": unique_files,
                "languages": languages,
                "last_ingest_time": last_ingest
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for {repo_id}: {e}")
            return None
    
    def _calculate_index_size(self) -> float:
        """Calculate total size of all index files."""
        total_size = 0
        
        try:
            if os.path.exists(settings.index_dir):
                for filename in os.listdir(settings.index_dir):
                    file_path = os.path.join(settings.index_dir, filename)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            logger.error(f"Failed to calculate index size: {e}")
            return 0.0
    
    def _calculate_avg_latency(self) -> Optional[float]:
        """Calculate average query latency."""
        if not self.query_latencies:
            return None
        
        return sum(self.query_latencies) / len(self.query_latencies)
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            import psutil
            
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "uptime": time.time() - psutil.boot_time()
            }
        except ImportError:
            return {
                "note": "psutil not available for detailed system info"
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}
    
    def record_query_latency(self, latency_ms: float):
        """Record a query latency for statistics."""
        self.query_latencies.append(latency_ms)
        
        # Keep only last 1000 queries to prevent memory issues
        if len(self.query_latencies) > 1000:
            self.query_latencies = self.query_latencies[-1000:]
    
    def record_ingest_time(self):
        """Record the time of last ingestion."""
        self.last_ingest_time = datetime.utcnow()
    
    async def get_repository_stats(self, repo_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific repository."""
        try:
            # Find the database file for this repo
            db_filename = f"{repo_id.replace('/', '_')}_metadata.db"
            db_path = os.path.join(settings.index_dir, db_filename)
            
            if not os.path.exists(db_path):
                return {
                    "repo_id": repo_id,
                    "error": "Repository not found"
                }
            
            stats = self._get_repo_stats_from_db(db_path, repo_id)
            if stats:
                stats["repo_id"] = repo_id
                stats["index_exists"] = os.path.exists(os.path.join(settings.index_dir, f"{repo_id.replace('/', '_')}.faiss"))
                stats["metadata_exists"] = os.path.exists(db_path)
                return stats
            else:
                return {
                    "repo_id": repo_id,
                    "error": "Failed to read repository stats"
                }
            
        except Exception as e:
            logger.error(f"Failed to get repository stats for {repo_id}: {e}")
            return {
                "repo_id": repo_id,
                "error": str(e)
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance-related metrics."""
        return {
            "query_latencies": {
                "count": len(self.query_latencies),
                "average": self._calculate_avg_latency(),
                "min": min(self.query_latencies) if self.query_latencies else None,
                "max": max(self.query_latencies) if self.query_latencies else None
            },
            "last_ingest": self.last_ingest_time,
            "index_size_mb": self._calculate_index_size()
        }
