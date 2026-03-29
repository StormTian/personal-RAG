"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Response
from rag_system.monitoring.prometheus_exporter import get_prometheus_exporter, CONTENT_TYPE_LATEST

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format.
    """
    exporter = get_prometheus_exporter()
    return Response(
        content=exporter.get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )
