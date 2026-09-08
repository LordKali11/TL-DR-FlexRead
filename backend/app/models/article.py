from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ReadingMode(str, Enum):
    SIXTY_SECONDS = "60s"
    BULLET_POINTS = "bullet_points"
    INLINE_SIMPLIFIED = "inline_simplified"
    FULL = "full"

class ToneCategory(str, Enum):
    ANALYTICAL = "analytical"
    INVESTIGATIVE = "investigative"
    OPINION_COMMENTARY = "opinion_commentary"
    REPORTAGE = "reportage"
    SOBER_BRIEFING = "sober_briefing"

class LengthTier(str, Enum):
    SHORT = "short"        # < 500 words
    MEDIUM = "medium"      # 500 - 1000 words
    LONG = "long"          # 1000 - 2500 words
    LONGFORM = "longform"  # > 2500 words

class ArticlePreprocessing(BaseModel):
    """
    Metadata computed during the preprocessing phase for every article:
    - main points
    - keywords
    - tone
    - article_length (tier)
    - reading time (seconds)
    - word count
    """
    main_points: List[str] = Field(
        default_factory=list,
        description="Core arguments, findings, and essential pillars of the article"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Extracted topical, semantic, and named entity keywords"
    )
    tone: ToneCategory = Field(
        default=ToneCategory.ANALYTICAL,
        description="Editorial tone detected in the article"
    )
    article_length: LengthTier = Field(
        default=LengthTier.MEDIUM,
        description="Categorized length tier based on word count"
    )
    reading_time: int = Field(
        default=0,
        description="Estimated reading time in seconds"
    )
    reading_time_minutes: float = Field(
        default=0.0,
        description="Estimated reading time in minutes"
    )
    word_count: int = Field(
        default=0,
        description="Total word count of original article"
    )

class FlexReadVariant(BaseModel):
    """
    Standard output structure for each reading mode:
    Output is a Title, summary and actual content.
    """
    mode: ReadingMode = Field(..., description="Reading mode variant")
    title: str = Field(..., description="Mode-adapted headline")
    summary: str = Field(..., description="Executive summary / lead paragraph")
    actual_content: str = Field(..., description="The transformed article content in markdown")
    word_count: int = Field(..., description="Word count of this variant")
    reading_time_seconds: int = Field(..., description="Reading time in seconds for this variant")
    cached: bool = Field(default=False, description="Whether this response was served from cache")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the variant was generated"
    )

class ArticleSummary(BaseModel):
    """Lightweight article model for listing and feed queries."""
    id: str
    headline: str
    lead: str
    section: Optional[str] = None
    date: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    word_count: int = 0
    reading_time_seconds: int = 0
    article_length: LengthTier = LengthTier.MEDIUM
    tone: ToneCategory = ToneCategory.ANALYTICAL
    available_modes: List[ReadingMode] = [
        ReadingMode.SIXTY_SECONDS,
        ReadingMode.BULLET_POINTS,
        ReadingMode.INLINE_SIMPLIFIED,
        ReadingMode.FULL
    ]

class Article(BaseModel):
    """Complete Article model including source text, preprocessing, and cached variants."""
    id: str
    source_path: str
    headline: str
    lead: str
    section: Optional[str] = "Allgemein"
    date: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    image_caption: Optional[str] = None
    raw_content: str
    language: str = "de"
    preprocessing: ArticlePreprocessing
    variants: Dict[str, FlexReadVariant] = Field(default_factory=dict)
