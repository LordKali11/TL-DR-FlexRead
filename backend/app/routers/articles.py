from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from ..models.api import ArticleListResponse, IngestResponse, ReadResponse
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
        
        summaries.append(ArticleSummary(
            id=a.id,
            headline=a.headline,
            lead=a.lead,
            section=a.section,
            date=a.date,
            author=a.author,
            url=a.url,
            image_url=a.image_url,
            word_count=a.preprocessing.word_count,
            reading_time_seconds=a.preprocessing.reading_time,
            article_length=a.preprocessing.article_length,
            tone=a.preprocessing.tone
        ))
        
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
    - main points
    - keywords
    - tone
    - article_length (tier)
    - reading time
    - word count
    """
    article = article_ingestion_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found")
    
    if not article.preprocessing or not article.preprocessing.main_points:
        article.preprocessing = preprocessor_service.process(article)
        
    return article

@router.get("/{article_id}/read", response_model=ReadResponse, summary="Read article in chosen FlexRead length")
def read_article_variant(
    article_id: str,
    mode: ReadingMode = Query(ReadingMode.SIXTY_SECONDS, description="Reading mode: 60s, bullet_points, inline_simplified, full"),
    user_id: Optional[str] = Query(None, description="Optional user ID for personalized reading speed and history tracking"),
    force_refresh: bool = Query(False, description="Bypass cache and regenerate with Gemini")
):
    """
    Delivers the article dynamically transformed into the chosen reading mode:
    - 60s: 60-second essentials for quick commuting
    - bullet_points: Structured executive takeaways
    - inline_simplified: Simplified paragraphs with inline explanations for social traffic
    - full: Original deep-dive article

    Guarantees standard output format: Title, summary, and actual content.
    Caches variants across lengths for sub-millisecond retrieval.
    """
    article = article_ingestion_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found")

    # Determine user-specific reading speed
    wpm = settings.DEFAULT_WPM
    if user_id:
        user = user_service.get_user(user_id)
        if user:
            wpm = user.preferences.reading_speed_wpm

    # Check cache first
    cached_variant = None
    if not force_refresh:
        cached_variant = cache_service.get_variant(article_id, mode, wpm=wpm)

    if cached_variant:
        variant = cached_variant
    else:
        # Generate with Gemini (or editorial heuristic fallback)
        variant = gemini_client_service.generate_variant(article, mode, wpm=wpm)
        # Store in cache
        cache_service.set_variant(article_id, mode, variant, wpm=wpm)

    # Compute time saved relative to original reading time
    original_time = article.preprocessing.reading_time if article.preprocessing else 180
    time_saved = max(0, original_time - variant.reading_time_seconds)

    # Automatically record read session if user_id provided
    if user_id:
        user_service.record_reading_history(
            user_id=user_id,
            article_id=article.id,
            headline=article.headline,
            mode_read=mode,
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

