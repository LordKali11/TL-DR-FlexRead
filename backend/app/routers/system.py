from fastapi import APIRouter
from ..models.api import CacheStatsResponse
from ..services.cache_service import cache_service
from ..db.mongodb import mongodb_service
from ..config import settings

router = APIRouter(tags=["System & Cache"])

@router.get("/health", summary="Health Check")
def health_check():
    """System status and environment overview including MongoDB and Redis health."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_active": bool(settings.GEMINI_API_KEY or settings.USE_VERTEX_AI),
        "primary_database": "mongodb",
        "mongodb_status": mongodb_service.ping(),
        "cache_layer": "redis",
        "redis_status": cache_service.ping()
    }

@router.get("/api/cache/stats", response_model=CacheStatsResponse, summary="Get cache statistics")
def get_cache_statistics():
    """Retrieves cache hit/miss statistics and stored variant count."""
    return cache_service.get_stats()

@router.post("/api/cache/clear", summary="Clear cache")
def clear_cache():
    """Invalidates all cached article variants in Redis."""
    cache_service.clear()
    return {"status": "cleared"}
