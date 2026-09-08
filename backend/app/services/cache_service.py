import json
import logging
from typing import Any, Dict, List, Optional
from ..config import settings
from ..models.article import FlexReadVariant, ArticlePreprocessing, ReadingMode
from ..models.api import CacheStatsResponse

logger = logging.getLogger(__name__)

class CacheService:
    """
    Ultra-Fast Cache Layer powered by Redis.
    Caches preprocessed article metadata, summaries, and multi-length FlexRead variants
    (60s, bullet_points, inline_simplified, full) to achieve sub-10ms response times.
    Gracefully falls back to an in-memory store if Redis is temporarily offline.
    """
    def __init__(self):
        self.memory_store: Dict[str, str] = {}
        self.hits = 0
        self.misses = 0
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Initializes connection to Redis instance if enabled."""
        if not getattr(settings, "ENABLE_REDIS", False):
            logger.info("Redis is disabled (ENABLE_REDIS=False). Using high-performance in-memory cache layer.")
            self.redis_client = None
            return

        try:
            import redis
            url = settings.get_redis_url()
            client = redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0
            )
            client.ping()
            self.redis_client = client
            logger.info(f"Ultra-Fast Redis cache connected at {url}")
        except Exception as e:
            logger.warning(
                f"Could not connect to Redis at {settings.get_redis_url()} ({e}). "
                "Falling back to high-performance in-memory cache layer."
            )
            self.redis_client = None

    def _make_variant_key(self, article_id: str, mode: str, wpm: int = 220) -> str:
        clean_id = article_id.replace(".", "").lower()
        return f"nzz:flexread:{clean_id}:{mode}:wpm{wpm}"

    def _make_article_meta_key(self, article_id: str) -> str:
        clean_id = article_id.replace(".", "").lower()
        return f"nzz:article:{clean_id}:meta"

    # --------------------------------------------------------------------------
    # FlexRead Multi-Length Variants Caching
    # --------------------------------------------------------------------------

    def get_variant(self, article_id: str, mode: ReadingMode, wpm: int = 220) -> Optional[FlexReadVariant]:
        """Fetches cached reading variant in sub-milliseconds."""
        key = self._make_variant_key(article_id, mode.value, wpm)
        
        # 1. Check Redis
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    self.hits += 1
                    data = json.loads(val)
                    data["cached"] = True
                    return FlexReadVariant(**data)
            except Exception as e:
                logger.warning(f"Redis GET failed for key {key}: {e}")

        # 2. Check In-Memory Fallback
        if key in self.memory_store:
            self.hits += 1
            data = json.loads(self.memory_store[key])
            data["cached"] = True
            return FlexReadVariant(**data)

        self.misses += 1
        return None

    def set_variant(self, article_id: str, mode: ReadingMode, variant: FlexReadVariant, wpm: int = 220):
        """Stores reading variant in Redis cache with configurable TTL."""
        key = self._make_variant_key(article_id, mode.value, wpm)
        data_json = variant.model_dump_json()

        if self.redis_client:
            try:
                self.redis_client.setex(key, settings.CACHE_TTL_SECONDS, data_json)
            except Exception as e:
                logger.warning(f"Redis SET failed for key {key}: {e}")

        # In-memory store
        self.memory_store[key] = data_json

    def warm_article_variants(self, article_id: str, variants_by_mode: Dict[ReadingMode, FlexReadVariant], wpm: int = 220):
        """Pre-populates all reading mode variants for an article into Redis."""
        for mode, variant in variants_by_mode.items():
            self.set_variant(article_id, mode, variant, wpm)
        logger.debug(f"Pre-populated {len(variants_by_mode)} variants in Redis for article {article_id}")

    # --------------------------------------------------------------------------
    # Preprocessed Article Metadata & Summary Caching
    # --------------------------------------------------------------------------

    def cache_preprocessed_article(self, article_dict: Dict[str, Any]):
        """Caches preprocessed article metadata into Redis for instant listing/reading."""
        article_id = article_dict.get("id")
        if not article_id:
            return
        key = self._make_article_meta_key(article_id)
        
        # Only cache fields needed for rapid lookup
        meta_payload = {
            "id": article_id,
            "headline": article_dict.get("headline", ""),
            "lead": article_dict.get("lead", ""),
            "section": article_dict.get("section", ""),
            "date": str(article_dict.get("date", "")),
            "word_count": article_dict.get("word_count", 0),
            "reading_time_seconds": article_dict.get("reading_time_seconds", 0),
            "reading_time_minutes": article_dict.get("reading_time_minutes", 0.0),
            "article_length": article_dict.get("article_length", ""),
            "tone": article_dict.get("tone", ""),
            "keywords": article_dict.get("preprocessing", {}).get("keywords", []) if isinstance(article_dict.get("preprocessing"), dict) else [],
            "main_points": article_dict.get("preprocessing", {}).get("main_points", []) if isinstance(article_dict.get("preprocessing"), dict) else []
        }
        payload_str = json.dumps(meta_payload)

        if self.redis_client:
            try:
                self.redis_client.setex(key, settings.CACHE_TTL_SECONDS, payload_str)
                # Add to section index set
                section = article_dict.get("section", "General")
                self.redis_client.sadd(f"nzz:section:{section.lower()}", article_id)
                self.redis_client.sadd("nzz:articles:all", article_id)
            except Exception as e:
                logger.warning(f"Redis cache_preprocessed_article failed: {e}")

        self.memory_store[key] = payload_str

    def get_cached_preprocessed_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached preprocessed metadata from Redis."""
        key = self._make_article_meta_key(article_id)
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val:
                    self.hits += 1
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Redis GET failed for key {key}: {e}")

        if key in self.memory_store:
            self.hits += 1
            return json.loads(self.memory_store[key])

        self.misses += 1
        return None

    # --------------------------------------------------------------------------
    # Cache Statistics & Health
    # --------------------------------------------------------------------------

    def get_stats(self) -> CacheStatsResponse:
        """Returns statistics on cache performance and entry counts."""
        backend_name = "redis" if self.redis_client else "in-memory-fallback"
        total_entries = len(self.memory_store)
        
        if self.redis_client:
            try:
                redis_keys = self.redis_client.keys("nzz:*")
                total_entries = len(redis_keys)
            except Exception:
                pass

        return CacheStatsResponse(
            backend=backend_name,
            total_entries=total_entries,
            cached_variants=total_entries,
            hits=self.hits,
            misses=self.misses
        )

    def ping(self) -> Dict[str, Any]:
        """Health check for Redis."""
        if self.redis_client:
            try:
                self.redis_client.ping()
                return {"connected": True, "backend": "redis", "url": settings.get_redis_url()}
            except Exception as e:
                return {"connected": False, "backend": "redis", "error": str(e)}
        return {"connected": True, "backend": "in-memory-fallback"}

    def clear(self):
        """Clears all cached variants and keys."""
        self.memory_store.clear()
        self.hits = 0
        self.misses = 0
        if self.redis_client:
            try:
                # Clear all nzz:* keys
                keys = self.redis_client.keys("nzz:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Error clearing Redis: {e}")

cache_service = CacheService()
