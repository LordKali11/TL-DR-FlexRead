import json
import logging
import sqlite3
from typing import Any, Dict, Optional, Tuple
from ..config import settings
from ..models.article import FlexReadVariant, ArticlePreprocessing, ReadingMode
from ..models.api import CacheStatsResponse

logger = logging.getLogger(__name__)

class CacheService:
    """
    Multi-tier Cache Service for NZZ FlexRead articles in different lengths.
    Supports in-memory, persistent SQLite, and Redis / Firestore.
    """
    def __init__(self):
        self.cache_type = settings.CACHE_TYPE.lower()
        self.memory_store: Dict[str, str] = {}
        self.hits = 0
        self.misses = 0
        self.redis_client = None
        self._init_backend()

    def _init_backend(self):
        # Redis setup
        if self.cache_type == "redis" or settings.REDIS_URL:
            try:
                import redis
                url = settings.REDIS_URL or "redis://localhost:6379/0"
                self.redis_client = redis.Redis.from_url(url, decode_responses=True)
                self.redis_client.ping()
                logger.info(f"Connected to Redis cache at {url}")
                return
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}. Falling back to SQLite/Memory.")
                self.redis_client = None

        # SQLite persistent cache setup
        self.db_path = settings.DATA_DIR / "article_cache.db"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS article_cache (
                        cache_key TEXT PRIMARY KEY,
                        article_id TEXT,
                        mode TEXT,
                        data JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_article_id ON article_cache(article_id)")
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing SQLite cache: {e}")

    def _make_key(self, article_id: str, mode: str, wpm: int = 220) -> str:
        clean_id = article_id.replace(".", "").lower()
        return f"nzz:flexread:{clean_id}:{mode}:wpm{wpm}"

    def get_variant(self, article_id: str, mode: ReadingMode, wpm: int = 220) -> Optional[FlexReadVariant]:
        """Fetches cached reading variant."""
        key = self._make_key(article_id, mode.value, wpm)
        
        # 1. Try Redis if active
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    self.hits += 1
                    data = json.loads(val)
                    data["cached"] = True
                    return FlexReadVariant(**data)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # 2. Try in-memory
        if key in self.memory_store:
            self.hits += 1
            data = json.loads(self.memory_store[key])
            data["cached"] = True
            return FlexReadVariant(**data)

        # 3. Try SQLite persistent store
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT data FROM article_cache WHERE cache_key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    self.hits += 1
                    data = json.loads(row[0])
                    data["cached"] = True
                    # Populate memory
                    self.memory_store[key] = row[0]
                    return FlexReadVariant(**data)
        except Exception as e:
            logger.debug(f"SQLite cache miss/error: {e}")

        self.misses += 1
        return None

    def set_variant(self, article_id: str, mode: ReadingMode, variant: FlexReadVariant, wpm: int = 220):
        """Stores reading variant in cache."""
        key = self._make_key(article_id, mode.value, wpm)
        clean_id = article_id.replace(".", "").lower()
        data_json = variant.model_dump_json()

        # 1. Redis
        if self.redis_client:
            try:
                self.redis_client.setex(key, settings.CACHE_TTL_SECONDS, data_json)
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")

        # 2. In-memory
        self.memory_store[key] = data_json

        # 3. SQLite persistent store
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO article_cache (cache_key, article_id, mode, data) VALUES (?, ?, ?, ?)",
                    (key, clean_id, mode.value, data_json)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error persisting to SQLite cache: {e}")

    def get_stats(self) -> CacheStatsResponse:
        """Returns statistics on cache performance and entry counts."""
        backend_name = "redis" if self.redis_client else ("sqlite" if hasattr(self, "db_path") else "memory")
        total_entries = len(self.memory_store)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM article_cache")
                sqlite_count = cursor.fetchone()[0]
                total_entries = max(total_entries, sqlite_count)
        except Exception:
            pass

        return CacheStatsResponse(
            backend=backend_name,
            total_entries=total_entries,
            cached_variants=total_entries,
            hits=self.hits,
            misses=self.misses
        )

    def clear(self):
        """Clears all cached variants."""
        self.memory_store.clear()
        self.hits = 0
        self.misses = 0
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception:
                pass
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM article_cache")
                conn.commit()
        except Exception:
            pass

cache_service = CacheService()
