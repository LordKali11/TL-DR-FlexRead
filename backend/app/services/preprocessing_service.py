import logging
from typing import Any, Dict, List, Optional
from ..db.mongodb import mongodb_service, MongoDBService
from ..models.article import Article, ArticlePreprocessing, FlexReadVariant, ReadingMode
from .preprocessor import ArticlePreprocessor, preprocessor_service
from .cache_service import cache_service, CacheService
from .gemini_client import gemini_client

logger = logging.getLogger(__name__)

class PreprocessingService:
    """
    Dedicated Pre-processing Service for NZZ FlexRead.
    Pipeline:
      1. Ingests raw article data from MongoDB (primary persistent database).
      2. Applies editorial pre-processing logic (main points, keywords, tone, length tier, reading time, word count).
      3. Persists pre-processed metadata back into MongoDB (system of record).
      4. Populates Redis with preprocessed summaries and pre-warmed reading mode variants
         (60s, bullet_points, inline_simplified, full) to serve as the ultra-fast cache layer.
    """
    def __init__(
        self,
        db_service: Optional[MongoDBService] = None,
        preprocessor: Optional[ArticlePreprocessor] = None,
        cache: Optional[CacheService] = None
    ):
        self.db = db_service or mongodb_service
        self.preprocessor = preprocessor or preprocessor_service
        self.cache = cache or cache_service

    def process_article_from_mongo(
        self,
        article_id: str,
        wpm: int = 220,
        warm_variants: bool = True
    ) -> Dict[str, Any]:
        """
        Ingests a single article from MongoDB, applies pre-processing logic,
        updates MongoDB, and populates Redis.
        """
        # 1. Ingest from MongoDB
        doc = self.db.get_article(article_id)
        if not doc:
            raise ValueError(f"Article with id '{article_id}' not found in MongoDB")

        # Convert to Article domain model
        raw_content = doc.get("raw_content") or doc.get("body_text", "")
        if not raw_content and isinstance(doc.get("body"), list):
            parts = []
            for item in doc.get("body", []):
                if isinstance(item, dict) and item.get("text"):
                    parts.append(item["text"])
            raw_content = "\n\n".join(parts)

        authors = doc.get("authors")
        if isinstance(authors, list) and authors:
            author = ", ".join(authors)
        else:
            author = doc.get("author_line") or doc.get("author")

        article = Article(
            id=doc["id"],
            source_path=doc.get("source_path", ""),
            headline=doc.get("headline", "Untitled"),
            lead=doc.get("lead", ""),
            section=doc.get("section", "General"),
            raw_content=raw_content,
            date=doc.get("date") or doc.get("published_at"),
            author=author,
            preprocessing=ArticlePreprocessing()
        )

        # 2. Apply Pre-processing Logic
        prep_result = self.preprocessor.process(article, wpm=wpm)
        article.preprocessing = prep_result
        article.word_count = prep_result.word_count
        article.reading_time_seconds = prep_result.reading_time
        article.reading_time_minutes = prep_result.reading_time_minutes
        article.article_length = prep_result.article_length
        article.tone = prep_result.tone

        # 3. Persist Pre-processing Results back into MongoDB
        prep_dict = prep_result.model_dump()
        self.db.update_article_preprocessing(article.id, prep_dict)

        # Also update root-level convenience fields in MongoDB
        col = self.db.get_collection("articles")
        col.update_one(
            {"id": article.id},
            {
                "$set": {
                    "word_count": article.word_count,
                    "reading_time_seconds": article.reading_time_seconds,
                    "reading_time_minutes": article.reading_time_minutes,
                    "article_length": article.article_length.value,
                    "tone": article.tone.value
                }
            }
        )

        # 4. Populate Redis Ultra-Fast Cache Layer
        updated_doc = self.db.get_article(article.id)
        self.cache.cache_preprocessed_article(updated_doc)

        cached_modes = []
        if warm_variants:
            # Pre-compute and store all reading modes in Redis for instant delivery
            modes = [
                ReadingMode.SIXTY_SECONDS,
                ReadingMode.BULLET_POINTS,
                ReadingMode.INLINE_SIMPLIFIED,
                ReadingMode.FULL
            ]
            for mode in modes:
                variant = gemini_client.transform_article(article, mode, wpm)
                self.cache.set_variant(article.id, mode, variant, wpm)
                cached_modes.append(mode.value)

        logger.info(
            f"Preprocessed article '{article.id}' from MongoDB. "
            f"Words: {article.word_count}, Tone: {article.tone.value}. "
            f"Populated Redis with {len(cached_modes)} modes."
        )

        return {
            "article_id": article.id,
            "headline": article.headline,
            "preprocessing": prep_dict,
            "word_count": article.word_count,
            "reading_time_seconds": article.reading_time_seconds,
            "reading_time_minutes": article.reading_time_minutes,
            "article_length": article.article_length.value,
            "tone": article.tone.value,
            "redis_cache_populated": True,
            "warmed_modes": cached_modes
        }

    def process_unprocessed_from_mongo(
        self,
        limit: int = 50,
        wpm: int = 220,
        warm_variants: bool = False
    ) -> Dict[str, Any]:
        """
        Scans MongoDB for articles without pre-processing data,
        runs pre-processing, and populates Redis.
        """
        unprocessed_docs = self.db.get_unprocessed_articles(limit=limit)
        processed_count = 0
        article_ids = []

        for doc in unprocessed_docs:
            art_id = doc.get("id")
            if art_id:
                try:
                    self.process_article_from_mongo(art_id, wpm=wpm, warm_variants=warm_variants)
                    processed_count += 1
                    article_ids.append(art_id)
                except Exception as e:
                    logger.error(f"Failed to preprocess article '{art_id}' from MongoDB: {e}")

        return {
            "total_unprocessed_found": len(unprocessed_docs),
            "successfully_processed": processed_count,
            "processed_article_ids": article_ids,
            "redis_cache_populated": True
        }

    def process_all_from_mongo(
        self,
        section: Optional[str] = None,
        limit: int = 500,
        wpm: int = 220,
        warm_variants: bool = False
    ) -> Dict[str, Any]:
        """
        Ingests all matching articles from MongoDB, computes pre-processing,
        and refreshes the Redis cache.
        """
        articles = self.db.list_articles(section=section, limit=limit)
        processed_count = 0
        article_ids = []

        for doc in articles:
            art_id = doc.get("id")
            if art_id:
                try:
                    self.process_article_from_mongo(art_id, wpm=wpm, warm_variants=warm_variants)
                    processed_count += 1
                    article_ids.append(art_id)
                except Exception as e:
                    logger.error(f"Error processing {art_id} from MongoDB: {e}")

        return {
            "articles_retrieved_from_mongo": len(articles),
            "successfully_processed": processed_count,
            "processed_article_ids": article_ids,
            "redis_cache_populated": True
        }

preprocessing_service = PreprocessingService()
