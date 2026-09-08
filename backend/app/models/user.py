from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .article import ReadingMode

class ReadingHistoryItem(BaseModel):
    article_id: str
    headline: str = ""
    mode_read: ReadingMode = ReadingMode.SIXTY_SECONDS
    read_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completion_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    time_spent_seconds: int = Field(default=60, ge=0)

class UserPreferences(BaseModel):
    reading_speed_wpm: int = Field(
        default=220,
        ge=80,
        le=800,
        description="Reading speed in words per minute (used to customize reading times)"
    )
    preferred_mode: ReadingMode = Field(
        default=ReadingMode.SIXTY_SECONDS,
        description="Default reading mode for quick commuting / social traffic"
    )
    topic_interests: List[str] = Field(
        default_factory=lambda: ["Business", "Economy", "Technology", "Global Politics", "International"],
        description="List of preferred NZZ sections/topics"
    )
    commute_time_budget_minutes: int = Field(
        default=5,
        ge=1,
        le=120,
        description="Default available time window for reading sessions"
    )

class UserProfile(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    reading_history: List[ReadingHistoryItem] = Field(default_factory=list)
    bookmarked_articles: List[str] = Field(default_factory=list)

class UserStats(BaseModel):
    user_id: str
    articles_read_count: int = 0
    total_reading_time_minutes: float = 0.0
    favorite_mode: ReadingMode = ReadingMode.SIXTY_SECONDS
    top_sections: List[str] = Field(default_factory=list)
    time_saved_minutes: float = 0.0
    mode_breakdown: Dict[str, int] = Field(default_factory=dict)
