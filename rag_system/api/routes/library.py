"""Library info API routes."""

from fastapi import APIRouter, Depends

from ...rag_engine import RAGEngine
from ..deps import get_rag_engine

router = APIRouter()


@router.get("/api/library")
async def get_library_info(rag_engine: RAGEngine = Depends(get_rag_engine)):
    """Get library information and statistics."""
    stats = rag_engine.stats()
    return {
        "status": "ok",
        **stats
    }
