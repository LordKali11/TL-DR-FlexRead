from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field
from .article import Article, ArticleSummary, FlexReadVariant, ReadingMode, LengthTier, ToneCategory
from .user import UserPreferences, UserProfile, UserStats

class IngestResponse(BaseModel):
    status: str
    articles_found: int
    articles_indexed: int
    errors: List[str] = Field(default_factory=list)

class ArticleListResponse(BaseModel):
    total: int
    count: int
    offset: int
    limit: int
    articles: List[ArticleSummary]

class ReadResponse(BaseModel):
    article_id: str
    original_headline: str
    original_lead: str
    original_word_count: int
    original_reading_time_seconds: int
    mode: ReadingMode
    title: str
    summary: str
    actual_content: str
    estimated_reading_time_minutes: int = 0
    variant_word_count: int
    variant_reading_time_seconds: int
    time_saved_seconds: int
    cached: bool
    reading_speed_wpm: int

class CreateUserRequest(BaseModel):
    username: str
    email: Optional[str] = None
    reading_speed_wpm: Optional[int] = 220
    preferred_mode: Optional[ReadingMode] = ReadingMode.SIXTY_SECONDS
    topic_interests: Optional[List[str]] = None
    commute_time_budget_minutes: Optional[int] = 5

class UpdatePreferencesRequest(BaseModel):
    reading_speed_wpm: Optional[int] = None
    preferred_mode: Optional[ReadingMode] = None
    topic_interests: Optional[List[str]] = None
    commute_time_budget_minutes: Optional[int] = None

class LogReadHistoryRequest(BaseModel):
    article_id: str
    mode_read: ReadingMode
    time_spent_seconds: int
    completion_rate: float = 1.0

class RecommendedArticle(BaseModel):
    article: ArticleSummary
    recommended_mode: ReadingMode
    estimated_reading_time_minutes: float
    relevance_reason: str

class PersonalizedFeedResponse(BaseModel):
    user_id: str
    commute_time_budget_minutes: int
    reading_speed_wpm: int
    recommended_articles: List[RecommendedArticle]

class CacheStatsResponse(BaseModel):
    backend: str
    total_entries: int
    cached_variants: int
    hits: int
    misses: int

class TransformRawTextRequest(BaseModel):
    raw_text: str = Field(..., description="The full original article content.")
    target_time_minutes: Union[int, str] = Field(..., description="The user's available reading budget (5, 10, 15, or full).")

class TransformRawTextResponse(BaseModel):
    title: str = Field(..., description="Adapted headline fitting the selected mode")
    summary: str = Field(..., description="1-2 sentence executive briefing")
    actual_content: str = Field(..., description="Markdown-formatted text body for the target mode or full text")
    estimated_reading_time_minutes: int = Field(..., description="Target reading time in minutes or computed for full mode")
    word_count: int = Field(..., description="Word count of actual_content")
