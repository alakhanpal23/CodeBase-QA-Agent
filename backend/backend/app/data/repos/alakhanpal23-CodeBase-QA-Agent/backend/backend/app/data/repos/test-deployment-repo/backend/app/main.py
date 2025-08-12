"""
Main FastAPI application for the Codebase QA Agent.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from typing import List, Optional

from .core.config import settings
from .core.schemas import (
    IngestRequest, IngestResponse, QueryRequest, QueryResponse,
    HealthResponse, StatsResponse
)
from .services.ingestion import IngestionService
from .services.query import QueryService
from .services.stats import StatsService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Codebase QA Agent",
    description="A service that ingests GitHub repositories and answers questions about codebases using RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ingestion_service = IngestionService()
query_service = QueryService()
stats_service = StatsService()


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Codebase QA Agent")
    await ingestion_service.initialize()
    await query_service.initialize()
    await stats_service.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Codebase QA Agent")
    await ingestion_service.cleanup()
    await query_service.cleanup()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(ok=True, timestamp=time.time())


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get service statistics."""
    try:
        stats = await stats_service.get_stats()
        return stats
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@app.post("/ingest", response_model=IngestResponse)
async def ingest_repository(request: IngestRequest):
    """Ingest a GitHub repository or ZIP file."""
    try:
        logger.info("Starting ingestion", repo_id=request.repo_id, source=request.source)
        
        result = await ingestion_service.ingest_repository(request)
        
        logger.info(
            "Ingestion completed",
            repo_id=request.repo_id,
            files_processed=result.files_processed,
            chunks_stored=result.chunks_stored,
            elapsed_time=result.elapsed_time
        )
        
        return result
    except Exception as e:
        logger.error("Ingestion failed", repo_id=request.repo_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/ingest/zip")
async def ingest_zip_file(
    file: UploadFile = File(...),
    repo_id: str = Form(...),
    include_globs: Optional[str] = Form("**/*.py,**/*.ts,**/*.js"),
    exclude_globs: Optional[str] = Form(".git/**,node_modules/**,dist/**,build/**,.venv/**")
):
    """Ingest a ZIP file containing repository code."""
    try:
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Parse glob patterns
        include_patterns = [p.strip() for p in include_globs.split(',') if p.strip()]
        exclude_patterns = [p.strip() for p in exclude_globs.split(',') if p.strip()]
        
        request = IngestRequest(
            source="zip",
            repo_id=repo_id,
            include_globs=include_patterns,
            exclude_globs=exclude_patterns
        )
        
        logger.info("Starting ZIP ingestion", repo_id=repo_id, filename=file.filename)
        
        result = await ingestion_service.ingest_zip_file(file, request)
        
        logger.info(
            "ZIP ingestion completed",
            repo_id=repo_id,
            files_processed=result.files_processed,
            chunks_stored=result.chunks_stored,
            elapsed_time=result.elapsed_time
        )
        
        return result
    except Exception as e:
        logger.error("ZIP ingestion failed", repo_id=repo_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"ZIP ingestion failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest):
    """Query the codebase with a natural language question."""
    try:
        logger.info("Processing query", question=request.question, repo_ids=request.repo_ids)
        
        result = await query_service.query(request)
        
        logger.info(
            "Query completed",
            question=request.question,
            latency_ms=result.latency_ms,
            citations_count=len(result.citations)
        )
        
        return result
    except Exception as e:
        logger.error("Query failed", question=request.question, error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
