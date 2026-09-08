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

        # Convert to Article domain model using Ingestion Service (populating all 30 NZZ schema attributes)
        try:
            from .article_ingestion import article_ingestion_service
            article = article_ingestion_service.doc_to_article(doc)
        except Exception:
            article = None

        if not article:
            # Fallback initialization ensuring all NZZ keys are present
            raw_id = doc.get("id") or doc.get("nzz_id") or doc.get("_id") or article_id
            clean_id = str(raw_id).replace(".", "").lower()
            raw_content = doc.get("body_text") or doc.get("raw_content") or ""
            if not raw_content and isinstance(doc.get("body"), list):
                parts = [item.get("text", "") for item in doc.get("body", []) if isinstance(item, dict) and item.get("text")]
                raw_content = "\n\n".join(parts)

            author = doc.get("author_line") or doc.get("author") or ""
            article = Article(
                nzz_id=doc.get("nzz_id") or (f"ld.{clean_id[2:]}" if clean_id.startswith("ld") else f"ld.{clean_id}"),
                document_id=doc.get("document_id") if doc.get("document_id") is not None else clean_id,
                url=doc.get("url"),
                language=doc.get("language", "en"),
                machine_translated_from_de=doc.get("machine_translated_from_de", True),
                section=doc.get("section", "General"),
                ressort_path=doc.get("ressort_path"),
                genre_flag=doc.get("genre_flag", ""),
                layout=doc.get("layout", "regular"),
                published_at=doc.get("published_at") or doc.get("date"),
                last_updated=doc.get("last_updated") or doc.get("published_at") or doc.get("date"),
                headline=doc.get("headline", "Untitled"),
                lead=doc.get("lead", ""),
                author_line=author,
                authors=doc.get("authors") if isinstance(doc.get("authors"), list) else ([author] if author else []),
                character_count=doc.get("character_count") or len(raw_content),
                seo_title=doc.get("seo_title") or doc.get("headline", "Untitled"),
                social_title=doc.get("social_title") or doc.get("headline", "Untitled"),
                print_title=doc.get("print_title") or doc.get("headline", "Untitled"),
                print_subtitle=doc.get("print_subtitle") or doc.get("lead", ""),
                summary_bullets_en=doc.get("summary_bullets_en") or [],
                key_questions_de=doc.get("key_questions_de") or [],
                tags=doc.get("tags") or [],
                sections_tag=doc.get("sections_tag") or doc.get("section", "General"),
                teaser_image=doc.get("teaser_image"),
                original_de=doc.get("original_de") or {"headline": doc.get("headline", ""), "lead": doc.get("lead", ""), "kicker": None},
                body=doc.get("body") or [],
                body_text=doc.get("body_text") or raw_content,
                id=clean_id,
                source_path=doc.get("source_path", ""),
                date=doc.get("date") or doc.get("published_at"),
                author=author,
                raw_content=raw_content,
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

        # Summary bullets in exact NZZ format:
        article.summary_bullets_en = list(prep_result.main_points)
        if not article.tags:
            article.tags = list(prep_result.keywords)

        # 3. Persist Pre-processing Results back into MongoDB
        prep_dict = prep_result.model_dump()
        self.db.update_article_preprocessing(article.id, prep_dict)

        # Update root-level NZZ fields in MongoDB (summary_bullets_en, word_count, etc.)
        col = self.db.get_collection("articles")
        col.update_one(
            {
                "$or": [
                    {"id": article.id},
                    {"nzz_id": article.nzz_id},
                    {"_id": article.nzz_id},
                    {"_id": article.id}
                ]
            },
            {
                "$set": {
                    "summary_bullets_en": article.summary_bullets_en,
                    "word_count": article.word_count,
                    "reading_time_seconds": article.reading_time_seconds,
                    "reading_time_minutes": article.reading_time_minutes,
                    "article_length": article.article_length.value,
                    "tone": article.tone.value,
                    "tags": article.tags,
                    "preprocessing": prep_dict
                }
            }
        )

        # 4. Populate Redis Ultra-Fast Cache Layer
        cached_modes = []
        if warm_variants:
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

        # Generate output dictionary matching input/days/2026-08-25/articles/*.json schema
        nzz_response = article.to_nzz_json()
        nzz_response["redis_cache_populated"] = True
        nzz_response["warmed_modes"] = cached_modes

        self.cache.cache_preprocessed_article(nzz_response)

        logger.info(
            f"Preprocessed article '{article.id}' from MongoDB. "
            f"Summary bullets: {len(article.summary_bullets_en)}, Words: {article.word_count}, "
            f"Tone: {article.tone.value}. Populated Redis with {len(cached_modes)} modes."
        )

        return nzz_response

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
