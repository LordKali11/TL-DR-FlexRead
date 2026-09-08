from typing import List, Optional
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
