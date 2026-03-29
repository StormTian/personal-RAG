"""Health check API routes."""

from fastapi import APIRouter
from datetime import datetime

from rag_system.monitoring.health import get_health_checker, HealthStatus

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns overall system health status and individual component checks.
    """
    checker = get_health_checker()
    status = checker.get_status()
    
    return {
        "status": status["status"],
        "timestamp": datetime.utcnow().isoformat(),
        "checks": status["checks"],
    }


@router.get("/ready")
async def readiness_check():
    """Readiness probe endpoint.
    
    Returns whether the service is ready to accept traffic.
    """
    checker = get_health_checker()
    status = checker.get_status()
    
    is_ready = status["status"] in [HealthStatus.HEALTHY.value, HealthStatus.DEGRADED.value]
    
    return {
        "ready": is_ready,
        "status": status["status"],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/live")
async def liveness_check():
    """Liveness probe endpoint.
    
    Simple check that the service is alive.
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
