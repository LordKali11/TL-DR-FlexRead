import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from ..config import settings
from ..db.mongodb import mongodb_service, MongoDBService
from ..models.article import Article, ArticlePreprocessing, LengthTier, ToneCategory
from .preprocessor import preprocessor_service
from .cache_service import cache_service

logger = logging.getLogger(__name__)

class ArticleIngestionService:
    """
    Article Ingestion Service for NZZ FlexRead.
    Sources raw articles directly from the remote MongoDB database collections ('articles')
    as the primary single source of truth.
    Local disk folder scanning has been disabled and deprecated.
    """
    def __init__(self, input_dir: Optional[Path] = None, db_service: Optional[MongoDBService] = None):
        self.input_dir = input_dir or settings.INPUT_DIR
        self.db = db_service or mongodb_service
        self._articles_cache: Dict[str, Article] = {}

    @staticmethod
    def extract_id_from_path(file_path: Path) -> str:
        """Extracts and normalizes article identifier from filename."""
        match = re.search(r"ld\.?(\d+)", file_path.stem)
        if match:
            return f"ld{match.group(1)}"
        return file_path.stem.replace(".", "").lower()

    @staticmethod
    def normalize_id(raw_id: Any) -> str:
        """Standardizes article IDs into clean 'ld...' format."""
        clean = str(raw_id).replace(".", "").lower()
        if not clean.startswith("ld"):
            clean = f"ld{clean}"
        return clean

    def doc_to_article(self, doc: Dict[str, Any]) -> Optional[Article]:
        """
        Converts a raw MongoDB article document into the standard Article domain model.
        Extracts content from body_text, body elements, or raw_content,
        and computes editorial preprocessing metrics if not already present.
        """
        try:
            raw_id = doc.get("id") or doc.get("nzz_id") or doc.get("document_id") or doc.get("_id") or "unknown"
            clean_id = self.normalize_id(raw_id)

            headline = doc.get("headline") or doc.get("seo_title") or doc.get("social_title") or doc.get("title") or "Untitled"
            lead = doc.get("lead") or ""
            section = doc.get("section") or "General"
            date = doc.get("published_at") or doc.get("date")

            # Authors
            authors = doc.get("authors")
            if isinstance(authors, list) and authors:
                author = ", ".join(authors)
            else:
                author = doc.get("author_line") or doc.get("author")

            # Teaser image
            teaser_image = doc.get("teaser_image")
            image_url = doc.get("image_url")
            image_caption = doc.get("image_caption")
            if isinstance(teaser_image, dict):
                image_url = teaser_image.get("url") or image_url
                image_caption = teaser_image.get("caption") or image_caption

            # Extract raw content: prefer body_text, then raw_content, then reconstruct from body array
            raw_content = doc.get("body_text") or doc.get("raw_content") or ""
            if not raw_content and isinstance(doc.get("body"), list):
                parts = []
                for item in doc.get("body"):
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get("type")
                    text = item.get("text", "").strip()
                    if not text:
                        continue
                    if item_type == "paragraph":
                        parts.append(text)
                    elif item_type == "heading":
                        parts.append(f"## {text}")
                    elif item_type == "quote":
                        parts.append(f"> {text}")
                raw_content = "\n\n".join(parts)

            # Preprocessing metrics
            existing_prep = doc.get("preprocessing")
            if isinstance(existing_prep, dict) and existing_prep.get("main_points"):
                preprocessing = ArticlePreprocessing(**existing_prep)
            else:
                # Seed with existing bullets/tags if available
                initial_points = doc.get("summary_bullets_en") or []
                initial_keywords = doc.get("tags") or []
                temp_article = Article(
                    id=clean_id,
                    source_path=doc.get("source_path", ""),
                    headline=headline,
                    lead=lead,
                    section=section,
                    date=date,
                    author=author,
                    url=doc.get("url"),
                    image_url=image_url,
                    image_caption=image_caption,
                    raw_content=raw_content,
                    language=doc.get("language", "en"),
                    preprocessing=ArticlePreprocessing(
                        main_points=initial_points,
                        keywords=initial_keywords
                    )
                )
                preprocessing = preprocessor_service.process(temp_article)

            article = Article(
                nzz_id=doc.get("nzz_id") or (f"ld.{clean_id[2:]}" if clean_id.startswith("ld") else f"ld.{clean_id}"),
                document_id=doc.get("document_id") if doc.get("document_id") is not None else clean_id,
                url=doc.get("url"),
                language=doc.get("language", "en"),
                machine_translated_from_de=doc.get("machine_translated_from_de", True),
                section=section,
                ressort_path=doc.get("ressort_path") or (section.lower().replace(" ", "-") if section else ""),
                genre_flag=doc.get("genre_flag") or "",
                layout=doc.get("layout") or "regular",
                published_at=doc.get("published_at") or date,
                last_updated=doc.get("last_updated") or doc.get("published_at") or date,
                headline=headline,
                lead=lead,
                author_line=doc.get("author_line") or author,
                authors=doc.get("authors") if isinstance(doc.get("authors"), list) else ([author] if author else []),
                reading_time_seconds=preprocessing.reading_time,
                word_count=preprocessing.word_count,
                character_count=doc.get("character_count") or len(raw_content or ""),
                seo_title=doc.get("seo_title") or headline,
                social_title=doc.get("social_title") or headline,
                print_title=doc.get("print_title") or headline,
                print_subtitle=doc.get("print_subtitle") or lead,
                summary_bullets_en=doc.get("summary_bullets_en") or list(preprocessing.main_points),
                key_questions_de=doc.get("key_questions_de") or [],
                tags=doc.get("tags") or list(preprocessing.keywords),
                sections_tag=doc.get("sections_tag") or section,
                teaser_image=teaser_image,
                original_de=doc.get("original_de") or {"headline": headline, "lead": lead, "kicker": None},
                body=doc.get("body") or [],
                body_text=doc.get("body_text") or raw_content,
                id=clean_id,
                source_path=doc.get("source_path", ""),
                date=date,
                author=author,
                image_url=image_url,
                image_caption=image_caption,
                raw_content=raw_content,
                reading_time_minutes=preprocessing.reading_time_minutes,
                article_length=preprocessing.article_length,
                tone=preprocessing.tone,
                preprocessing=preprocessing
            )
            return article
        except Exception as e:
            logger.error(f"Error parsing MongoDB document into Article model: {e}")
            return None

    def ingest_from_mongodb(self, limit: Optional[int] = None) -> Tuple[int, int, List[str]]:
        """
        Primary ingestion method:
        Pulls raw articles directly from the remote MongoDB database collection ('articles').
        Standardizes models, ensures preprocessing metrics, updates MongoDB if needed,
        and populates the ultra-fast cache layer.
        """
        logger.info("Ingesting articles directly from remote MongoDB collection 'articles'...")
        col = self.db.get_collection("articles")
        
        cursor = col.find()
        if limit:
            cursor = cursor.limit(limit)

        articles_found = 0
        articles_indexed = 0
        errors: List[str] = []

        for doc in cursor:
            articles_found += 1
            article = self.doc_to_article(doc)
            if not article:
                errors.append(f"Failed to parse MongoDB doc with _id={doc.get('_id')}")
                continue

            # Store in local fast memory cache
            self._articles_cache[article.id] = article

            # Cache preprocessed metadata into cache service (Redis or memory)
            try:
                cache_service.cache_preprocessed_article(article.model_dump())
            except Exception as e:
                logger.debug(f"Cache population notice: {e}")

            # If document did not have preprocessing persisted, update MongoDB
            if not doc.get("preprocessing"):
                try:
                    self.db.update_article_preprocessing(
                        article.id,
                        article.preprocessing.model_dump()
                    )
                except Exception as e:
                    logger.debug(f"Notice updating preprocessing in MongoDB for {article.id}: {e}")

            articles_indexed += 1

        logger.info(
            f"Successfully synced {articles_indexed}/{articles_found} articles "
            f"directly from MongoDB database '{self.db.db_name}'."
        )
        return articles_found, articles_indexed, errors

    def ingest_all(self, force_reload: bool = False) -> Tuple[int, int, List[str]]:
        """
        Public ingestion interface called during startup and via /api/articles/ingest.
        Directly queries the remote MongoDB database. If empty, seeds from input directory.
        """
        if self._articles_cache and not force_reload:
            return len(self._articles_cache), len(self._articles_cache), []
        found, indexed, errors = self.ingest_from_mongodb()
        if indexed == 0 and self.input_dir and self.input_dir.exists():
            f_disk, i_disk, e_disk = self.ingest_from_disk()
            return f_disk, i_disk, errors + e_disk
        return found, indexed, errors

    def get_article(self, article_id: str) -> Optional[Article]:
        """
        Retrieves an article by ID:
        1. Fast in-memory cache
        2. Remote MongoDB primary database
        """
        clean_id = self.normalize_id(article_id)
        if clean_id in self._articles_cache:
            return self._articles_cache[clean_id]

        # Query remote MongoDB directly
        doc = self.db.get_article(clean_id)
        if doc:
            article = self.doc_to_article(doc)
            if article:
                self._articles_cache[clean_id] = article
                return article

        # If cache was never populated, perform initial sync from MongoDB
        if not self._articles_cache:
            self.ingest_from_mongodb()
            return self._articles_cache.get(clean_id)

        return None

    def list_articles(
        self,
        section: Optional[str] = None,
        search_query: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[Article], int]:
        """
        Lists articles with optional filtering and pagination.
        Sourced from in-memory cache populated from MongoDB.
        """
        if not self._articles_cache:
            self.ingest_from_mongodb()

        articles = list(self._articles_cache.values())

        if section:
            sec_lower = section.lower()
            articles = [
                a for a in articles 
                if a.section and sec_lower in a.section.lower()
            ]

        if search_query:
            q = search_query.lower()
            articles = [
                a for a in articles
                if q in a.headline.lower()
                or (a.lead and q in a.lead.lower())
                or q in a.raw_content.lower()
            ]

        total = len(articles)
        paginated = articles[offset : offset + limit]
        return paginated, total

    def ingest_from_disk(self) -> Tuple[int, int, List[str]]:
        """
        Scans local disk folders in self.input_dir (e.g. days and longform subdirectories).
        Parses JSON and MD files, seeds them into MongoDB, and populates the local cache.
        """
        target_dirs: List[Path] = []
        if self.input_dir and self.input_dir.exists():
            for sub in ("days", "longform"):
                d = self.input_dir / sub
                if d.exists():
                    target_dirs.append(d)
            if not target_dirs:
                target_dirs.append(self.input_dir)

        articles_found = 0
        articles_indexed = 0
        errors: List[str] = []

        import json
        for directory in target_dirs:
            for jf in sorted(directory.glob("*.json")):
                articles_found += 1
                try:
                    with open(jf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    clean_id = self.extract_id_from_path(jf)
                    data["id"] = clean_id
                    data["source_path"] = str(jf)
                    
                    if not data.get("body_text") and not data.get("raw_content"):
                        md_sibling = jf.with_suffix(".md")
                        if md_sibling.exists():
                            with open(md_sibling, "r", encoding="utf-8") as mf:
                                data["raw_content"] = mf.read().strip()

                    article = self.doc_to_article(data)
                    if article:
                        self._articles_cache[article.id] = article
                        try:
                            self.db.save_article(article.model_dump())
                        except Exception as save_err:
                            logger.debug(f"Notice saving seeded article to MongoDB: {save_err}")
                        articles_indexed += 1
                    else:
                        errors.append(f"Failed to parse {jf.name}")
                except Exception as e:
                    errors.append(f"Error reading {jf.name}: {e}")

        logger.info(f"Disk ingestion seeded {articles_indexed}/{articles_found} articles into cache and MongoDB.")
        return articles_found, articles_indexed, errors

# Global singleton instance
article_ingestion_service = ArticleIngestionService()
