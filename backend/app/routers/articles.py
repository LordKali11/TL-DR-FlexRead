from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from ..models.api import ArticleListResponse, IngestResponse, ReadResponse, TransformRawTextRequest, TransformRawTextResponse
from ..models.article import Article, ArticleSummary, ReadingMode
from ..services.article_ingestion import article_ingestion_service
from ..services.preprocessor import preprocessor_service
from ..services.gemini_client import gemini_client_service
from ..services.cache_service import cache_service
from ..services.user_service import user_service
from ..services.preprocessing_service import preprocessing_service
from ..config import settings

router = APIRouter(prefix="/api/articles", tags=["Articles & FlexRead"])

@router.post("/ingest", response_model=IngestResponse, summary="Ingest articles from input folders")
def trigger_ingestion(force_reload: bool = False):
    """
    Pulls articles from input folders (e.g., input/days and input/longform).
    Loads both JSON and MD documents, standardizes IDs, and populates index.
    """
    found, indexed, errors = article_ingestion_service.ingest_all(force_reload=force_reload)
    return IngestResponse(
        status="success",
        articles_found=found,
        articles_indexed=indexed,
        errors=errors
    )

@router.get("", response_model=ArticleListResponse, summary="List ingested articles")
def list_articles(
    section: Optional[str] = Query(None, description="Filter by section (e.g. Wirtschaft, Schweiz)"),
    search: Optional[str] = Query(None, description="Search term in headline or lead"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Returns paginated articles list with preprocessing summary."""
    articles, total = article_ingestion_service.list_articles(
        section=section,
        search_query=search,
        offset=offset,
        limit=limit
    )
    
    summaries = []
    for a in articles:
        if not a.preprocessing or not a.preprocessing.word_count:
            a.preprocessing = preprocessor_service.process(a)
        
        summaries.append(a.to_summary())
        
    return ArticleListResponse(
        total=total,
        count=len(summaries),
        offset=offset,
        limit=limit,
        articles=summaries
    )

@router.get("/{article_id}", response_model=Article, summary="Get full article with preprocessing metadata")
def get_article_detail(article_id: str):
    """
    Retrieves complete article along with its preprocessing attributes:
    - main points (summary_bullets_en)
    - keywords (tags)
    - tone
    - article_length (tier)
    - reading time
    - word count
    """
    article = article_ingestion_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found")
    
    if not article.preprocessing or not article.preprocessing.main_points or not article.summary_bullets_en:
        article.preprocessing = preprocessor_service.process(article)
        article.summary_bullets_en = list(article.preprocessing.main_points)
        
    return article

@router.get("/{article_id}/summary", summary="Get article summary in standard NZZ JSON format")
def get_article_summary_nzz(article_id: str):
    """
    Returns the article and its preprocessed summary matching the exact JSON format
    of input/days/2026-08-25/articles.
    """
    article = article_ingestion_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found")
    
    if not article.preprocessing or not article.preprocessing.main_points or not article.summary_bullets_en:
        article.preprocessing = preprocessor_service.process(article)
        article.summary_bullets_en = list(article.preprocessing.main_points)
        
    return article.to_nzz_json()


@router.get("/{article_id}/read", response_model=ReadResponse, summary="Read article in chosen FlexRead length")
def read_article_variant(
    article_id: str,
    mode: Optional[ReadingMode] = Query(None, description="Reading mode: 60s, bullet_points, inline_simplified, full, 5min, 10min, 15min"),
    target_time_minutes: Optional[str] = Query(None, description="Target reading time: 5, 10, 15, full, or custom minutes"),
    user_id: Optional[str] = Query(None, description="Optional user ID for personalized reading speed and history tracking"),
    force_refresh: bool = Query(False, description="Bypass cache and regenerate with Gemini")
):
    """
    Delivers the article dynamically transformed into the chosen reading mode:
    - 60s: 60-second essentials for quick commuting
    - bullet_points: Structured executive takeaways
    - inline_simplified: Simplified paragraphs with inline explanations for social traffic
    - 5min: 5-minute executive briefing with structured bullets (~1,000 to 1,250 words)
    - 10min: 10-minute balanced narrative with data metrics and context (~2,000 to 2,500 words)
    - 15min: 15-minute full deep-dive analysis preserving quotes & perspectives (~3,000 to 3,750 words)
    - full: Original deep-dive article

    Guarantees standard output format: Title, summary, and actual content.
    Caches variants across lengths for sub-millisecond retrieval.
    """
    article = article_ingestion_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found")

    # Resolve reading mode
    resolved_mode = mode
    if target_time_minutes:
        try:
            resolved_mode = ReadingMode(target_time_minutes)
        except ValueError:
            pass
    if not resolved_mode:
        resolved_mode = ReadingMode.SIXTY_SECONDS

    # Determine user-specific reading speed
    wpm = settings.DEFAULT_WPM
    if user_id:
        user = user_service.get_user(user_id)
        if user:
            wpm = user.preferences.reading_speed_wpm

    # Check cache first
    cached_variant = None
    if not force_refresh:
        cached_variant = cache_service.get_variant(article_id, resolved_mode, wpm=wpm)

    if cached_variant:
        variant = cached_variant
    else:
        # Generate with Gemini (or editorial heuristic fallback)
        variant = gemini_client_service.generate_variant(article, resolved_mode, wpm=wpm)
        # Store in cache
        cache_service.set_variant(article_id, resolved_mode, variant, wpm=wpm)

    # Compute time saved relative to original reading time
    original_time = article.preprocessing.reading_time if article.preprocessing else 180
    time_saved = max(0, original_time - variant.reading_time_seconds)

    # Automatically record read session if user_id provided
    if user_id:
        user_service.record_reading_history(
            user_id=user_id,
            article_id=article.id,
            headline=article.headline,
            mode_read=resolved_mode,
            time_spent_seconds=variant.reading_time_seconds,
            completion_rate=1.0
        )

    return ReadResponse(
        article_id=article.id,
        original_headline=article.headline,
        original_lead=article.lead,
        original_word_count=article.preprocessing.word_count if article.preprocessing else 0,
        original_reading_time_seconds=original_time,
        mode=variant.mode,
        title=variant.title,
        summary=variant.summary,
        actual_content=variant.actual_content,
        estimated_reading_time_minutes=variant.estimated_reading_time_minutes,
        variant_word_count=variant.word_count,
        variant_reading_time_seconds=variant.reading_time_seconds,
        time_saved_seconds=time_saved,
        cached=variant.cached,
        reading_speed_wpm=wpm
    )

@router.post("/{article_id}/preprocess", summary="Preprocess article from MongoDB and populate Redis")
def preprocess_article_from_mongo(
    article_id: str,
    warm_variants: bool = Query(True, description="Pre-generate and warm all FlexRead modes into Redis cache")
):
    """
    Ingests an article document from MongoDB, applies the full editorial pre-processing logic
    (main points, keywords, tone, length tier, reading time, word count),
    updates the MongoDB document, and populates Redis as the ultra-fast cache layer.
    """
    try:
        result = preprocessing_service.process_article_from_mongo(
            article_id=article_id,
            warm_variants=warm_variants
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Preprocessing failed: {e}")

@router.post("/preprocess/batch", summary="Batch preprocess unprocessed articles from MongoDB into Redis")
def batch_preprocess_from_mongo(
    limit: int = Query(50, ge=1, le=200, description="Max number of unprocessed articles to process"),
    warm_variants: bool = Query(False, description="Pre-warm reading mode variants in Redis")
):
    """
    Finds articles in MongoDB missing preprocessing metadata, applies preprocessing logic,
    updates MongoDB documents, and populates Redis.
    """
    result = preprocessing_service.process_unprocessed_from_mongo(
        limit=limit,
        warm_variants=warm_variants
    )
    return result


@router.post("/transform", response_model=TransformRawTextResponse, summary="Transform raw article text into target time budget")
def transform_raw_text(
    payload: TransformRawTextRequest,
    user_id: Optional[str] = Query(None, description="Optional user ID for personalized reading speed")
):
    """
    Transforms arbitrary raw text into a target reading budget:
    - 5-Minute Mode (5 minutes / 5min): ~1,000 to 1,250 words
    - 10-Minute Mode (10 minutes / 10min): ~2,000 to 2,500 words
    - 15-Minute Mode (15 minutes / 15min): ~3,000 to 3,750 words
    - Full Mode / Full Article (full): Returns original text unaltered, estimated reading time at 200 wpm.
    """
    wpm = settings.DEFAULT_WPM
    if user_id:
        user = user_service.get_user(user_id)
        if user:
            wpm = user.preferences.reading_speed_wpm

    result = gemini_client_service.transform_raw_text(
        raw_text=payload.raw_text,
        target_time_minutes=payload.target_time_minutes,
        wpm=wpm
    )
    return TransformRawTextResponse(**result)

