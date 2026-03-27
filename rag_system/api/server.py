"""HTTP server with FastAPI."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..rag_engine import RAGEngine
from ..config import get_settings
from ..exceptions import RAGError
from ..exceptions.handlers import handle_exception
from ..monitoring import get_health_checker, create_basic_health_checks
from ..monitoring.logging_config import get_logger
from .security import SecurityMiddleware
from .deps import get_rag_engine, get_security, get_api_key, get_client_id
from .routes import upload_router, files_router, history_router, library_router

logger = get_logger("api.server")


class QueryRequest(BaseModel):
    """Query request model."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=3, ge=1, le=20, description="Number of results")


class QueryResponse(BaseModel):
    """Query response model."""
    query: str
    answer_lines: list[str]
    hits: list[dict]
    metadata: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    checks: dict
    timestamp: float


class StatsResponse(BaseModel):
    """System stats response model."""
    library_dir: str
    documents: int
    chunks: int
    supported_formats: list[str]
    embedding_backend: str
    reranker_backend: str
    retrieval_strategy: str
    rerank_strategy: str


# Global state moved to deps.py


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up RAG server")
    settings = get_settings()
    
    # Initialize RAG engine
    rag = get_rag_engine()
    
    # Setup health checks
    health_checker = get_health_checker()
    checks = create_basic_health_checks(
        rag,
        rag.embedding_backend,
        rag.reranker_backend,
    )
    for name, check_fn in checks.items():
        health_checker.register_check(name, check_fn)
    health_checker.start_monitoring()
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG server")
    health_checker.stop_monitoring()
    
    # Close async resources
    if hasattr(rag.embedding_backend, 'close'):
        await rag.embedding_backend.close()
    if hasattr(rag.reranker_backend, 'close'):
        await rag.reranker_backend.close()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="RAG System API",
        description="Production-ready Retrieval-Augmented Generation API",
        version="2.0.0",
        lifespan=lifespan,
    )
    
    # CORS middleware
    if settings.server.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.server.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Exception handler
    @app.exception_handler(RAGError)
    async def rag_error_handler(request: Request, exc: RAGError):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )
    
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        response = handle_exception(exc, {"path": str(request.url)})
        return JSONResponse(
            status_code=500,
            content=response,
        )
    
    # Routes
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        health_checker = get_health_checker()
        return health_checker.get_status()
    
    @app.get("/api/stats", response_model=StatsResponse)
    async def get_stats(
        api_key: Optional[str] = Depends(get_api_key),
        client_id: str = Depends(get_client_id),
    ):
        """Get system statistics."""
        security = get_security()
        security.validate_request(api_key, client_id)
        
        rag = get_rag_engine()
        stats = rag.stats()
        return StatsResponse(**stats)
    
    @app.post("/api/query", response_model=QueryResponse)
    async def query(
        request: QueryRequest,
        api_key: Optional[str] = Depends(get_api_key),
        client_id: str = Depends(get_client_id),
    ):
        """Execute RAG query."""
        security = get_security()
        security.validate_request(api_key, client_id)
        
        # Validate inputs
        query_text = security.validate_query(request.query)
        top_k = security.validate_top_k(request.top_k)
        
        # Execute query
        rag = get_rag_engine()
        response = await rag.answer_async(query=query_text, top_k=top_k)
        
        return QueryResponse(
            query=response.query,
            answer_lines=response.answer_lines,
            hits=[
                {
                    "score": round(hit.score, 4),
                    "retrieve_score": round(hit.retrieve_score, 4),
                    "rerank_score": round(hit.rerank_score, 4),
                    "lexical_score": round(hit.lexical_score, 4),
                    "title_score": round(hit.title_score, 4),
                    "llm_score": round(hit.llm_score, 4),
                    "source": hit.chunk.source,
                    "title": hit.chunk.title,
                    "text": hit.chunk.text,
                    "chunk_id": hit.chunk.chunk_id,
                    "metadata": hit.metadata,
                }
                for hit in response.hits
            ],
            metadata=response.metadata,
        )
    
    @app.post("/api/ask", response_model=QueryResponse)
    async def ask(
        request: QueryRequest,
        api_key: Optional[str] = Depends(get_api_key),
        client_id: str = Depends(get_client_id),
    ):
        """Execute RAG query (alias for /api/query)."""
        security = get_security()
        security.validate_request(api_key, client_id)
        
        # Validate inputs
        query_text = security.validate_query(request.query)
        top_k = security.validate_top_k(request.top_k)
        
        # Execute query
        rag = get_rag_engine()
        response = await rag.answer_async(query=query_text, top_k=top_k)
        
        return QueryResponse(
            query=response.query,
            answer_lines=response.answer_lines,
            hits=[
                {
                    "score": round(hit.score, 4),
                    "retrieve_score": round(hit.retrieve_score, 4),
                    "rerank_score": round(hit.rerank_score, 4),
                    "lexical_score": round(hit.lexical_score, 4),
                    "title_score": round(hit.title_score, 4),
                    "llm_score": round(hit.llm_score, 4),
                    "source": hit.chunk.source,
                    "title": hit.chunk.title,
                    "text": hit.chunk.text,
                    "chunk_id": hit.chunk.chunk_id,
                    "metadata": hit.metadata,
                }
                for hit in response.hits
            ],
            metadata=response.metadata,
        )
    
    @app.get("/api/search")
    async def search(
        q: str = Query(..., min_length=1, max_length=1000),
        top_k: int = Query(default=3, ge=1, le=20),
        api_key: Optional[str] = Depends(get_api_key),
        client_id: str = Depends(get_client_id),
    ):
        """Search documents."""
        security = get_security()
        security.validate_request(api_key, client_id)
        
        # Validate inputs
        query_text = security.validate_query(q)
        top_k = security.validate_top_k(top_k)
        
        # Execute search
        rag = get_rag_engine()
        hits = await rag.search_async(query=query_text, top_k=top_k)
        
        return {
            "query": query_text,
            "hits": [
                {
                    "score": float(round(hit.score, 4)),
                    "retrieve_score": float(round(hit.retrieve_score, 4)),
                    "rerank_score": float(round(hit.rerank_score, 4)),
                    "lexical_score": float(round(hit.lexical_score, 4)),
                    "title_score": float(round(hit.title_score, 4)),
                    "llm_score": float(round(hit.llm_score, 4)),
                    "source": hit.chunk.source,
                    "title": hit.chunk.title,
                    "text": hit.chunk.text,
                    "chunk_id": hit.chunk.chunk_id,
                }
                for hit in hits
            ],
            "total": len(hits),
        }
    
    @app.post("/api/reload")
    async def reload_library(
        api_key: Optional[str] = Depends(get_api_key),
        client_id: str = Depends(get_client_id),
    ):
        """Reload document library."""
        security = get_security()
        security.validate_request(api_key, client_id)
        
        rag = get_rag_engine()
        await rag.reload_async()
        
        return {"status": "ok", "message": "Library reloaded", **rag.stats()}
    
    # Include additional routers
    app.include_router(upload_router)
    app.include_router(files_router)
    app.include_router(history_router)
    app.include_router(library_router)
    
    return app


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the server."""
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "rag_system.api.server:create_app",
        host=host or settings.server.host,
        port=port or settings.server.port,
        workers=settings.server.workers,
        reload=settings.debug,
        factory=True,
    )
