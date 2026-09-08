import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..config import settings
from ..models.article import Article, ArticlePreprocessing, LengthTier, ToneCategory

logger = logging.getLogger(__name__)

class ArticleIngestionService:
    """
    Ingests articles from input folders (e.g. input/days/ and input/longform/).
    Parses both .json and .md files, extracting content, structure, and metadata.
    """
    def __init__(self, input_dir: Optional[Path] = None):
        self.input_dir = input_dir or settings.INPUT_DIR
        self._articles_cache: Dict[str, Article] = {}

    def get_input_directories(self) -> List[Path]:
        """Returns list of article directories to scan."""
        dirs = []
        days_dir = self.input_dir / "days"
        if days_dir.exists():
            for day_folder in days_dir.iterdir():
                if day_folder.is_dir():
                    articles_sub = day_folder / "articles"
                    if articles_sub.exists():
                        dirs.append(articles_sub)
                    else:
                        dirs.append(day_folder)
        
        longform_dir = self.input_dir / "longform"
        if longform_dir.exists():
            articles_sub = longform_dir / "articles"
            if articles_sub.exists():
                dirs.append(articles_sub)
            else:
                dirs.append(longform_dir)
        
        return dirs

    @staticmethod
    def extract_id_from_path(file_path: Path) -> str:
        """Extracts unique article ID from filename (e.g. ld10020939)."""
        stem = file_path.stem
        match = re.search(r"ld[0-9]+", stem, re.IGNORECASE)
        if match:
            return match.group(0).lower()
        return stem

    def parse_json_article(self, file_path: Path) -> Optional[Article]:
        """Parses an NZZ JSON article file into an Article domain model."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            raw_id = str(data.get("nzz_id") or data.get("document_id") or self.extract_id_from_path(file_path))
            clean_id = raw_id.replace(".", "").lower()
            if not clean_id.startswith("ld"):
                clean_id = f"ld{clean_id}"
            
            headline = data.get("headline") or data.get("seo_title") or "Ohne Titel"
            lead = data.get("lead") or ""
            section = data.get("section") or "Wirtschaft"
            date = data.get("published_at")
            
            # Author
            authors = data.get("authors", [])
            author = ", ".join(authors) if authors else data.get("author_line")
            
            # Image
            teaser_image = data.get("teaser_image", {})
            image_url = teaser_image.get("url") if isinstance(teaser_image, dict) else None
            image_caption = teaser_image.get("caption") if isinstance(teaser_image, dict) else None
            
            # Body reconstruction
            body_elements = data.get("body", [])
            body_parts = []
            for item in body_elements:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                if item_type == "paragraph":
                    text = item.get("text", "").strip()
                    if text:
                        body_parts.append(text)
                elif item_type == "heading":
                    text = item.get("text", "").strip()
                    if text:
                        body_parts.append(f"## {text}")
                elif item_type == "quote":
                    text = item.get("text", "").strip()
                    if text:
                        body_parts.append(f"> {text}")
            
            raw_content = "\n\n".join(body_parts)
            
            # If body was empty in JSON, try adjacent .md file
            if not raw_content.strip():
                md_path = file_path.with_suffix(".md")
                if md_path.exists():
                    raw_content = self.read_md_body(md_path)
            
            # Initial placeholder preprocessing (refined by preprocessor service)
            word_count = data.get("word_count") or len(raw_content.split())
            reading_time = data.get("reading_time_seconds") or max(30, int(word_count / (220 / 60)))
            
            preprocessing = ArticlePreprocessing(
                main_points=data.get("summary_bullets_en") or [],
                keywords=data.get("tags") or [],
                tone=ToneCategory.ANALYTICAL,
                article_length=LengthTier.MEDIUM,
                reading_time=reading_time,
                reading_time_minutes=round(reading_time / 60.0, 1),
                word_count=word_count
            )
            
            return Article(
                id=clean_id,
                source_path=str(file_path),
                headline=headline,
                lead=lead,
                section=section,
                date=date,
                author=author,
                url=data.get("url"),
                image_url=image_url,
                image_caption=image_caption,
                raw_content=raw_content,
                language=data.get("language", "de"),
                preprocessing=preprocessing
            )
        except Exception as e:
            logger.error(f"Error parsing JSON article {file_path}: {e}")
            return None

    def read_md_body(self, md_path: Path) -> str:
        """Reads plain content from markdown, skipping header blocks."""
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Strip auto-summary footer if present
            if "---" in content and "Auto summary" in content:
                content = content.split("---")[0]
            return content.strip()
        except Exception:
            return ""

    def parse_md_article(self, file_path: Path) -> Optional[Article]:
        """Parses a standalone markdown article file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            
            clean_id = self.extract_id_from_path(file_path)
            lines = raw_text.splitlines()
            headline = "Ohne Titel"
            lead = ""
            body_lines = []
            
            is_headline_found = False
            for line in lines:
                stripped = line.strip()
                if not is_headline_found and stripped.startswith("# "):
                    headline = stripped[2:].strip()
                    is_headline_found = True
                elif stripped.startswith("*") and stripped.endswith("*") and not lead:
                    lead = stripped.strip("*").strip()
                elif stripped.startswith("---") and "Auto summary" in raw_text:
                    break
                else:
                    body_lines.append(line)
            
            raw_content = "\n".join(body_lines).strip()
            word_count = len(raw_content.split())
            reading_time = max(30, int(word_count / (220 / 60)))
            
            preprocessing = ArticlePreprocessing(
                main_points=[],
                keywords=[],
                tone=ToneCategory.ANALYTICAL,
                article_length=LengthTier.MEDIUM,
                reading_time=reading_time,
                reading_time_minutes=round(reading_time / 60.0, 1),
                word_count=word_count
            )
            
            return Article(
                id=clean_id,
                source_path=str(file_path),
                headline=headline,
                lead=lead,
                section="Allgemein",
                date=None,
                author=None,
                url=None,
                image_url=None,
                image_caption=None,
                raw_content=raw_content,
                language="de",
                preprocessing=preprocessing
            )
        except Exception as e:
            logger.error(f"Error parsing MD article {file_path}: {e}")
            return None

    def ingest_all(self, force_reload: bool = False) -> Tuple[int, int, List[str]]:
        """
        Scans all input directories and loads articles into memory.
        Returns: (articles_found, articles_indexed, errors)
        """
        if self._articles_cache and not force_reload:
            return len(self._articles_cache), len(self._articles_cache), []
        
        target_dirs = self.get_input_directories()
        articles_indexed = 0
        articles_found = 0
        errors: List[str] = []
        
        # Priority to JSON files, fallback to standalone MD files
        for directory in target_dirs:
            if not directory.exists():
                continue
            
            json_files = list(directory.glob("*.json"))
            articles_found += len(json_files)
            
            for jf in json_files:
                article = self.parse_json_article(jf)
                if article:
                    self._articles_cache[article.id] = article
                    articles_indexed += 1
                else:
                    errors.append(f"Failed to parse {jf.name}")
            
            # Check for any standalone markdown files without a JSON sibling
            md_files = list(directory.glob("*.md"))
            for mf in md_files:
                article_id = self.extract_id_from_path(mf)
                if article_id not in self._articles_cache:
                    articles_found += 1
                    article = self.parse_md_article(mf)
                    if article:
                        self._articles_cache[article.id] = article
                        articles_indexed += 1
        
        logger.info(f"Ingested {articles_indexed} articles across {len(target_dirs)} directories.")
        return articles_found, articles_indexed, errors

    def get_article(self, article_id: str) -> Optional[Article]:
        """Retrieves article by ID."""
        clean_id = article_id.replace(".", "").lower()
        if not clean_id.startswith("ld"):
            clean_id = f"ld{clean_id}"
        
        if clean_id not in self._articles_cache:
            # Try lazy ingestion
            self.ingest_all()
        
        return self._articles_cache.get(clean_id)

    def list_articles(
        self,
        section: Optional[str] = None,
        search_query: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[Article], int]:
        """Lists articles with optional filtering and pagination."""
        if not self._articles_cache:
            self.ingest_all()
        
        articles = list(self._articles_cache.values())
        
        if section:
            section_lower = section.lower()
            articles = [
                a for a in articles 
                if a.section and section_lower in a.section.lower()
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

# Singleton instance
article_ingestion_service = ArticleIngestionService()
