from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator

class ReadingMode(str, Enum):
    SIXTY_SECONDS = "60s"
    BULLET_POINTS = "bullet_points"
    INLINE_SIMPLIFIED = "inline_simplified"
    FULL = "full"
    FIVE_MINUTES = "5min"
    TEN_MINUTES = "10min"
    FIFTEEN_MINUTES = "15min"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_clean = value.lower().strip()
            aliases = {
                "5": cls.FIVE_MINUTES,
                "5m": cls.FIVE_MINUTES,
                "5min": cls.FIVE_MINUTES,
                "5-minute": cls.FIVE_MINUTES,
                "5_minute": cls.FIVE_MINUTES,
                "five_minutes": cls.FIVE_MINUTES,
                "10": cls.TEN_MINUTES,
                "10m": cls.TEN_MINUTES,
                "10min": cls.TEN_MINUTES,
                "10-minute": cls.TEN_MINUTES,
                "10_minute": cls.TEN_MINUTES,
                "ten_minutes": cls.TEN_MINUTES,
                "15": cls.FIFTEEN_MINUTES,
                "15m": cls.FIFTEEN_MINUTES,
                "15min": cls.FIFTEEN_MINUTES,
                "15-minute": cls.FIFTEEN_MINUTES,
                "15_minute": cls.FIFTEEN_MINUTES,
                "15 minutes": cls.FIFTEEN_MINUTES,
                "15-minutes": cls.FIFTEEN_MINUTES,
                "15_minutes": cls.FIFTEEN_MINUTES,
                "fifteen_minutes": cls.FIFTEEN_MINUTES,
                "fifteen minutes": cls.FIFTEEN_MINUTES,
                "5 minutes": cls.FIVE_MINUTES,
                "5-minutes": cls.FIVE_MINUTES,
                "5_minutes": cls.FIVE_MINUTES,
                "10 minutes": cls.TEN_MINUTES,
                "10-minutes": cls.TEN_MINUTES,
                "10_minutes": cls.TEN_MINUTES,
                "full": cls.FULL,
                "full article": cls.FULL,
                "full-article": cls.FULL,
                "full_article": cls.FULL,
                "original": cls.FULL,
            }
            if val_clean in aliases:
                return aliases[val_clean]
        return super()._missing_(value)

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
    Output is a Title, summary, actual content, estimated reading time, and word count.
    """
    mode: ReadingMode = Field(..., description="Reading mode variant")
    title: str = Field(..., description="Mode-adapted headline")
    summary: str = Field(..., description="Executive summary / lead paragraph")
    actual_content: str = Field(..., description="The transformed article content in markdown")
    estimated_reading_time_minutes: int = Field(
        default=0,
        description="Estimated reading time in minutes tailored to the target budget"
    )
    word_count: int = Field(..., description="Word count of this variant")
    reading_time_seconds: int = Field(default=0, description="Reading time in seconds for this variant")
    cached: bool = Field(default=False, description="Whether this response was served from cache")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the variant was generated"
    )

    @model_validator(mode="after")
    def populate_estimated_reading_time(self):
        if not self.estimated_reading_time_minutes:
            if self.mode == ReadingMode.FIVE_MINUTES:
                self.estimated_reading_time_minutes = 5
            elif self.mode == ReadingMode.TEN_MINUTES:
                self.estimated_reading_time_minutes = 10
            elif self.mode == ReadingMode.FIFTEEN_MINUTES:
                self.estimated_reading_time_minutes = 15
            elif self.mode == ReadingMode.SIXTY_SECONDS:
                self.estimated_reading_time_minutes = 1
            elif self.mode == ReadingMode.FULL:
                self.estimated_reading_time_minutes = max(1, round(self.word_count / 200))
            elif self.reading_time_seconds > 0:
                self.estimated_reading_time_minutes = max(1, round(self.reading_time_seconds / 60))
            else:
                self.estimated_reading_time_minutes = 1
        return self

class ArticleSummary(BaseModel):
    """Lightweight article model for listing and feed queries matching NZZ schema."""
    id: str
    nzz_id: Optional[str] = None
    document_id: Optional[Any] = None
    headline: str
    lead: str
    section: Optional[str] = None
    date: Optional[str] = None
    published_at: Optional[str] = None
    author: Optional[str] = None
    author_line: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    image_url: Optional[str] = None
    teaser_image: Optional[Dict[str, Any]] = None
    word_count: int = 0
    reading_time_seconds: int = 0
    summary_bullets_en: List[str] = Field(
        default_factory=list,
        description="Summary bullets matching NZZ schema"
    )
    tags: List[str] = Field(default_factory=list)
    article_length: LengthTier = LengthTier.MEDIUM
    tone: ToneCategory = ToneCategory.ANALYTICAL
    available_modes: List[ReadingMode] = [
        ReadingMode.SIXTY_SECONDS,
        ReadingMode.BULLET_POINTS,
        ReadingMode.INLINE_SIMPLIFIED,
        ReadingMode.FULL,
        ReadingMode.FIVE_MINUTES,
        ReadingMode.TEN_MINUTES,
        ReadingMode.FIFTEEN_MINUTES
    ]

class Article(BaseModel):
    """
    Complete Article model matching the exact NZZ schema of input/days/2026-08-25/articles/*.json
    along with FlexRead preprocessing, caching, and variants.
    """
    # 30 Standard NZZ Schema Fields
    nzz_id: Optional[str] = None
    document_id: Optional[Any] = None
    url: Optional[str] = None
    language: str = "en"
    machine_translated_from_de: bool = True
    section: Optional[str] = "General"
    ressort_path: Optional[str] = None
    genre_flag: Optional[str] = None
    layout: Optional[str] = "regular"
    published_at: Optional[str] = None
    last_updated: Optional[str] = None
    headline: str
    lead: str = ""
    author_line: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    reading_time_seconds: int = 0
    word_count: int = 0
    character_count: Optional[int] = None
    seo_title: Optional[str] = None
    social_title: Optional[str] = None
    print_title: Optional[str] = None
    print_subtitle: Optional[str] = None
    summary_bullets_en: List[str] = Field(
        default_factory=list,
        description="Executive summary bullets matching NZZ schema"
    )
    key_questions_de: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    sections_tag: Optional[str] = None
    teaser_image: Optional[Dict[str, Any]] = None
    original_de: Optional[Dict[str, Any]] = None
    body: List[Dict[str, Any]] = Field(default_factory=list)
    body_text: str = ""

    # FlexRead Extensions & Legacy Compatibility
    id: str = ""
    source_path: str = ""
    date: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    image_caption: Optional[str] = None
    raw_content: str = ""
    preprocessing: ArticlePreprocessing = Field(default_factory=ArticlePreprocessing)
    reading_time_minutes: float = 0.0
    article_length: LengthTier = LengthTier.MEDIUM
    tone: ToneCategory = ToneCategory.ANALYTICAL
    variants: Dict[str, FlexReadVariant] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_fields(self) -> "Article":
        # Synchronize ID fields
        if not self.id and self.nzz_id:
            self.id = self.nzz_id.replace(".", "").lower()
        elif not self.nzz_id and self.id:
            clean = self.id.replace(".", "").lower()
            if clean.startswith("ld"):
                self.nzz_id = f"ld.{clean[2:]}"
            else:
                self.nzz_id = f"ld.{clean}"

        # Synchronize document_id
        if self.document_id is None and self.nzz_id:
            digits = "".join(filter(str.isdigit, self.nzz_id))
            if digits:
                self.document_id = int(digits)

        # Synchronize content fields
        if not self.raw_content and self.body_text:
            self.raw_content = self.body_text
        elif not self.body_text and self.raw_content:
            self.body_text = self.raw_content

        # Synchronize date / published_at
        if not self.date and self.published_at:
            self.date = self.published_at
        elif not self.published_at and self.date:
            self.published_at = self.date

        # Synchronize author fields
        if not self.author and self.author_line:
            self.author = self.author_line
        elif not self.author_line and self.author:
            self.author_line = self.author
        if not self.authors and self.author:
            self.authors = [self.author]

        # Synchronize summary bullets (NZZ schema) and preprocessing main points
        if not self.summary_bullets_en and self.preprocessing and self.preprocessing.main_points:
            self.summary_bullets_en = list(self.preprocessing.main_points)
        elif self.summary_bullets_en and self.preprocessing and not self.preprocessing.main_points:
            self.preprocessing.main_points = list(self.summary_bullets_en)

        # Synchronize tags and preprocessing keywords
        if not self.tags and self.preprocessing and self.preprocessing.keywords:
            self.tags = list(self.preprocessing.keywords)
        elif self.tags and self.preprocessing and not self.preprocessing.keywords:
            self.preprocessing.keywords = list(self.tags)

        # Synchronize teaser_image / image_url
        if self.teaser_image and isinstance(self.teaser_image, dict) and not self.image_url:
            self.image_url = self.teaser_image.get("url")
        elif not self.teaser_image and self.image_url:
            self.teaser_image = {
                "url": self.image_url,
                "caption": self.image_caption or self.lead or "",
                "credit": "",
                "width": 1024,
                "height": 768
            }

        # Synchronize reading times and counts
        if self.reading_time_seconds and not self.reading_time_minutes:
            self.reading_time_minutes = round(self.reading_time_seconds / 60.0, 1)
        elif self.reading_time_minutes and not self.reading_time_seconds:
            self.reading_time_seconds = int(self.reading_time_minutes * 60)

        if not self.character_count:
            self.character_count = len(self.body_text or self.raw_content or "")

        return self

    def to_summary(self) -> ArticleSummary:
        return ArticleSummary(
            id=self.id,
            nzz_id=self.nzz_id,
            document_id=self.document_id,
            headline=self.headline,
            lead=self.lead,
            section=self.section,
            date=self.published_at or self.date,
            published_at=self.published_at or self.date,
            author=self.author_line or self.author,
            author_line=self.author_line or self.author,
            authors=self.authors,
            url=self.url,
            image_url=self.image_url or (self.teaser_image.get("url") if self.teaser_image else None),
            teaser_image=self.teaser_image,
            word_count=self.word_count or (self.preprocessing.word_count if self.preprocessing else 0),
            reading_time_seconds=self.reading_time_seconds or (self.preprocessing.reading_time if self.preprocessing else 0),
            summary_bullets_en=self.summary_bullets_en or (self.preprocessing.main_points if self.preprocessing else []),
            tags=self.tags or (self.preprocessing.keywords if self.preprocessing else []),
            article_length=self.article_length or (self.preprocessing.article_length if self.preprocessing else LengthTier.MEDIUM),
            tone=self.tone or (self.preprocessing.tone if self.preprocessing else ToneCategory.ANALYTICAL)
        )

    def to_nzz_json(self) -> Dict[str, Any]:
        """
        Produces an exact JSON dictionary matching the schema of input/days/2026-08-25/articles/*.json.
        The summary output is populated in 'summary_bullets_en'.
        """
        summary_bullets = self.summary_bullets_en or (self.preprocessing.main_points if self.preprocessing else [])
        keywords = self.tags or (self.preprocessing.keywords if self.preprocessing else [])
        reading_seconds = self.reading_time_seconds or (self.preprocessing.reading_time if self.preprocessing else 0)
        w_count = self.word_count or (self.preprocessing.word_count if self.preprocessing else 0)
        char_count = self.character_count or len(self.body_text or self.raw_content or "")

        body_items = self.body
        if not body_items:
            text = self.body_text or self.raw_content or ""
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            body_items = [{"type": "paragraph", "text": p} for p in paragraphs if not p.startswith("## ")]

        return {
            "nzz_id": self.nzz_id or (f"ld.{self.id[2:]}" if self.id.startswith("ld") else f"ld.{self.id}"),
            "document_id": self.document_id if self.document_id is not None else (int("".join(filter(str.isdigit, self.id))) if any(c.isdigit() for c in self.id) else self.id),
            "url": self.url or "",
            "language": self.language or "en",
            "machine_translated_from_de": self.machine_translated_from_de,
            "section": self.section or "",
            "ressort_path": self.ressort_path or (self.section.lower().replace(" ", "-") if self.section else ""),
            "genre_flag": self.genre_flag or "",
            "layout": self.layout or "regular",
            "published_at": self.published_at or self.date or "",
            "last_updated": self.last_updated or self.published_at or self.date or "",
            "headline": self.headline,
            "lead": self.lead or "",
            "author_line": self.author_line or self.author or "",
            "authors": self.authors or ([self.author] if self.author else []),
            "reading_time_seconds": reading_seconds,
            "word_count": w_count,
            "character_count": char_count,
            "seo_title": self.seo_title or self.headline,
            "social_title": self.social_title or self.headline,
            "print_title": self.print_title or self.headline,
            "print_subtitle": self.print_subtitle or self.lead or "",
            "summary_bullets_en": summary_bullets,
            "key_questions_de": self.key_questions_de or [],
            "tags": keywords,
            "sections_tag": self.sections_tag or self.section or "",
            "teaser_image": self.teaser_image or ({
                "url": self.image_url,
                "caption": self.image_caption or self.lead or "",
                "credit": "",
                "width": 1024,
                "height": 768
            } if self.image_url else None),
            "original_de": self.original_de or {
                "headline": self.headline,
                "lead": self.lead,
                "kicker": None
            },
            "body": body_items,
            "body_text": self.body_text or self.raw_content or "",
            # Essential compatibility fields for frontend & FlexRead pipeline
            "id": self.id,
            "article_id": self.id,
            "reading_time_minutes": self.reading_time_minutes or round(reading_seconds / 60.0, 1),
            "article_length": self.article_length.value if hasattr(self.article_length, "value") else str(self.article_length),
            "tone": self.tone.value if hasattr(self.tone, "value") else str(self.tone),
            "preprocessing": self.preprocessing.model_dump() if self.preprocessing else {}
        }


