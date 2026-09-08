from fastapi import APIRouter, HTTPException, status
from ..models.api import CreateUserRequest, UpdatePreferencesRequest, LogReadHistoryRequest
from ..models.user import UserProfile, UserStats
from ..services.user_service import user_service
from ..services.article_ingestion import article_ingestion_service

router = APIRouter(prefix="/api/users", tags=["User Management"])

@router.post("", response_model=UserProfile, status_code=status.HTTP_201_CREATED, summary="Create user profile")
def create_user(req: CreateUserRequest):
    """Creates a new user profile with reading preferences."""
    profile = user_service.create_user(req)
    return profile

@router.get("/{user_id}", response_model=UserProfile, summary="Get user profile")
def get_user(user_id: str):
    """Retrieves user profile and preferences."""
    profile = user_service.get_user(user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return profile

@router.put("/{user_id}/preferences", response_model=UserProfile, summary="Update reading preferences")
def update_preferences(user_id: str, req: UpdatePreferencesRequest):
    """
    Updates user reading preferences:
    - reading_speed_wpm
    - preferred_mode (60s, bullet_points, inline_simplified, full)
    - topic_interests
    - commute_time_budget_minutes
    """
    profile = user_service.update_preferences(user_id, req)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return profile

@router.post("/{user_id}/history", summary="Log read session")
def log_reading_history(user_id: str, req: LogReadHistoryRequest):
    """Records that a user read an article in a specific length/mode."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    
    article = article_ingestion_service.get_article(req.article_id)
    headline = article.headline if article else "Artikel"

    success = user_service.record_reading_history(
        user_id=user_id,
        article_id=req.article_id,
        headline=headline,
        mode_read=req.mode_read,
        time_spent_seconds=req.time_spent_seconds,
        completion_rate=req.completion_rate
    )
    return {"status": "recorded", "article_id": req.article_id}

@router.get("/{user_id}/stats", response_model=UserStats, summary="Get user reading analytics")
def get_user_stats(user_id: str):
    """
    Calculates reading stats:
    - Articles read
    - Total reading time
    - Favorite reading mode
    - Time saved through FlexRead compressed formats
    """
    stats = user_service.get_user_stats(user_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return stats
