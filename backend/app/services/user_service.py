import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import Counter
from ..config import settings
from ..db.mongodb import mongodb_service, MongoDBService
from ..models.user import UserProfile, UserPreferences, ReadingHistoryItem, UserStats
from ..models.article import Article, ReadingMode, ArticleSummary
from ..models.api import CreateUserRequest, UpdatePreferencesRequest, RecommendedArticle
from .cache_service import cache_service, CacheService

logger = logging.getLogger(__name__)

class UserService:
    """
    Manages user profiles, reading preferences, reading history, and adaptive recommendations.
    Uses MongoDB as the primary persistent database and Redis as the ultra-fast cache layer.
    """
    def __init__(
        self,
        db_service: Optional[MongoDBService] = None,
        cache: Optional[CacheService] = None
    ):
        self.db = db_service or mongodb_service
        self.cache = cache or cache_service
        self.users: Dict[str, UserProfile] = {}
        self._seed_default_users()

    def _user_redis_key(self, user_id: str) -> str:
        return f"nzz:user:{user_id}"

    def _seed_default_users(self):
        """Seeds two representative English persona profiles into MongoDB and Redis."""
        try:
            # Persona 1: Busy Commuter (3-minute budget, prefers 60s & bullet points)
            commuter = UserProfile(
                user_id="user_commuter_zurich",
                username="Sophie Commuter",
                email="sophie@example.com",
                preferences=UserPreferences(
                    reading_speed_wpm=240,
                    preferred_mode=ReadingMode.SIXTY_SECONDS,
                    topic_interests=["Business", "Economy", "Technology", "Global Politics"],
                    commute_time_budget_minutes=3
                )
            )
            # Persona 2: In-depth Executive Reader
            executive = UserProfile(
                user_id="user_executive",
                username="Marc Executive",
                email="marc@example.com",
                preferences=UserPreferences(
                    reading_speed_wpm=200,
                    preferred_mode=ReadingMode.BULLET_POINTS,
                    topic_interests=["Business", "Finance", "Opinion", "International"],
                    commute_time_budget_minutes=10
                )
            )
            self.save_user(commuter)
            self.save_user(executive)
        except Exception as e:
            logger.error(f"Error seeding default users: {e}")

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """
        Retrieves user profile:
        1. In-memory hot cache
        2. Ultra-fast Redis cache
        3. MongoDB persistent database
        """
        if user_id in self.users:
            return self.users[user_id]

        # 2. Check Redis cache
        if self.cache.redis_client:
            try:
                cached_json = self.cache.redis_client.get(self._user_redis_key(user_id))
                if cached_json:
                    data = json.loads(cached_json)
                    profile = UserProfile(
                        user_id=data["user_id"],
                        username=data["username"],
                        email=data.get("email"),
                        created_at=datetime.fromisoformat(data["created_at"]),
                        preferences=UserPreferences(**data["preferences"]),
                        reading_history=[ReadingHistoryItem(**item) for item in data.get("reading_history", [])],
                        bookmarked_articles=data.get("bookmarked_articles", [])
                    )
                    self.users[user_id] = profile
                    return profile
            except Exception as e:
                logger.debug(f"Redis get_user error: {e}")

        # 3. Query MongoDB (System of Record)
        try:
            doc = self.db.get_user(user_id)
            if doc:
                profile = UserProfile(
                    user_id=doc["user_id"],
                    username=doc["username"],
                    email=doc.get("email"),
                    created_at=datetime.fromisoformat(doc["created_at"]) if isinstance(doc["created_at"], str) else doc["created_at"],
                    preferences=UserPreferences(**doc["preferences"]),
                    reading_history=[ReadingHistoryItem(**item) for item in doc.get("reading_history", [])],
                    bookmarked_articles=doc.get("bookmarked_articles", [])
                )
                self.users[user_id] = profile
                # Warm Redis cache
                self._cache_user_to_redis(profile)
                return profile
        except Exception as e:
            logger.error(f"MongoDB get_user error for {user_id}: {e}")

        return None

    def _cache_user_to_redis(self, user: UserProfile):
        """Helper to cache user payload in Redis."""
        if self.cache.redis_client:
            try:
                user_payload = {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at.isoformat(),
                    "preferences": user.preferences.model_dump(),
                    "reading_history": [h.model_dump(mode="json") for h in user.reading_history],
                    "bookmarked_articles": user.bookmarked_articles
                }
                self.cache.redis_client.setex(
                    self._user_redis_key(user.user_id),
                    settings.CACHE_TTL_SECONDS,
                    json.dumps(user_payload)
                )
            except Exception as e:
                logger.debug(f"Redis user cache write error: {e}")

    def save_user(self, user: UserProfile):
        """Persists user to MongoDB (primary DB) and updates Redis cache."""
        self.users[user.user_id] = user

        # 1. Persist to MongoDB
        try:
            doc = {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "preferences": user.preferences.model_dump(),
                "reading_history": [h.model_dump(mode="json") for h in user.reading_history],
                "bookmarked_articles": user.bookmarked_articles
            }
            self.db.save_user(doc)
        except Exception as e:
            logger.error(f"Error saving user {user.user_id} to MongoDB: {e}")

        # 2. Update Redis ultra-fast cache
        self._cache_user_to_redis(user)

    def create_user(self, req: CreateUserRequest) -> UserProfile:
        """Creates a new user profile."""
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        prefs = UserPreferences(
            reading_speed_wpm=req.reading_speed_wpm or 220,
            preferred_mode=req.preferred_mode or ReadingMode.SIXTY_SECONDS,
            topic_interests=req.topic_interests or ["Business", "Technology", "Global Politics"],
            commute_time_budget_minutes=req.commute_time_budget_minutes or 5
        )
        profile = UserProfile(
            user_id=user_id,
            username=req.username,
            email=req.email,
            preferences=prefs
        )
        self.save_user(profile)
        logger.info(f"Created user {user_id} ({profile.username}) in MongoDB and Redis")
        return profile

    def update_preferences(self, user_id: str, req: UpdatePreferencesRequest) -> Optional[UserProfile]:
        """Updates user reading preferences."""
        user = self.get_user(user_id)
        if not user:
            return None

        if req.reading_speed_wpm is not None:
            user.preferences.reading_speed_wpm = req.reading_speed_wpm
        if req.preferred_mode is not None:
            user.preferences.preferred_mode = req.preferred_mode
        if req.topic_interests is not None:
            user.preferences.topic_interests = req.topic_interests
        if req.commute_time_budget_minutes is not None:
            user.preferences.commute_time_budget_minutes = req.commute_time_budget_minutes

        self.save_user(user)
        return user

    def record_reading_event(
        self,
        user_id: str,
        article_id: str,
        mode: ReadingMode = ReadingMode.SIXTY_SECONDS,
        headline: str = "",
        time_spent_seconds: int = 60,
        completed: bool = True,
        completion_rate: float = 1.0
    ) -> Optional[UserProfile]:
        """Records a completed or partial reading session."""
        user = self.get_user(user_id)
        if not user:
            return None

        item = ReadingHistoryItem(
            article_id=article_id,
            headline=headline,
            mode_read=mode,
            read_at=datetime.now(timezone.utc),
            time_spent_seconds=time_spent_seconds,
            completion_rate=completion_rate if completed else 0.5
        )
        user.reading_history.append(item)
        self.save_user(user)
        return user

    def record_reading_history(
        self,
        user_id: str,
        article_id: str,
        headline: Optional[str] = None,
        mode_read: ReadingMode = ReadingMode.SIXTY_SECONDS,
        time_spent_seconds: int = 60,
        completion_rate: float = 1.0
    ) -> Optional[UserProfile]:
        """Convenience method to log reading history."""
        return self.record_reading_event(
            user_id=user_id,
            article_id=article_id,
            mode=mode_read,
            headline=headline or "",
            time_spent_seconds=time_spent_seconds,
            completed=(completion_rate >= 0.8),
            completion_rate=completion_rate
        )

    def bookmark_article(self, user_id: str, article_id: str) -> Optional[UserProfile]:
        """Adds article to bookmarks."""
        user = self.get_user(user_id)
        if not user:
            return None
        if article_id not in user.bookmarked_articles:
            user.bookmarked_articles.append(article_id)
            self.save_user(user)
        return user

    def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        """Computes reading statistics and estimated time saved."""
        user = self.get_user(user_id)
        if not user:
            return None

        history = user.reading_history
        total_read = len(history)
        total_time_seconds = sum(h.time_spent_seconds for h in history)
        
        mode_counts = Counter(h.mode_read.value for h in history)

        # Baseline: assume full article takes ~350 seconds
        estimated_time_saved = 0
        for h in history:
            if h.mode_read == ReadingMode.SIXTY_SECONDS:
                estimated_time_saved += max(0, 350 - 60)
            elif h.mode_read == ReadingMode.BULLET_POINTS:
                estimated_time_saved += max(0, 350 - 120)
            elif h.mode_read == ReadingMode.INLINE_SIMPLIFIED:
                estimated_time_saved += max(0, 350 - 180)

        favorite_mode = ReadingMode(mode_counts.most_common(1)[0][0]) if mode_counts else user.preferences.preferred_mode

        return UserStats(
            user_id=user_id,
            articles_read_count=total_read,
            total_reading_time_minutes=round(total_time_seconds / 60.0, 1),
            favorite_mode=favorite_mode,
            top_sections=[],
            time_saved_minutes=round(estimated_time_saved / 60.0, 1),
            mode_breakdown=dict(mode_counts)
        )

    def recommend_mode_for_article(
        self,
        user: UserProfile,
        article: Article,
        override_time_budget_minutes: Optional[int] = None
    ) -> tuple[ReadingMode, float, str]:
        """Recommends reading mode for a specific article given a user's time budget."""
        budget = override_time_budget_minutes or user.preferences.commute_time_budget_minutes
        wpm = user.preferences.reading_speed_wpm
        return self._select_mode_for_window(article, budget, wpm, user.preferences.topic_interests)


    def recommend_articles_for_commute(
        self,
        user_id: str,
        available_articles: List[Article],
        time_budget_minutes: Optional[int] = None,
        limit: int = 5
    ) -> List[RecommendedArticle]:
        """
        Recommends articles and optimal reading modes tailored to user's time window.
        """
        user = self.get_user(user_id)
        wpm = user.preferences.reading_speed_wpm if user else 220
        budget = time_budget_minutes or (user.preferences.commute_time_budget_minutes if user else 5)
        preferred_topics = user.preferences.topic_interests if user else ["Business", "Technology", "Global Politics"]

        recommendations = []
        for article in available_articles:
            rec_mode, est_time_min, reason = self._select_mode_for_window(article, budget, wpm, preferred_topics)
            
            recommendations.append(
                RecommendedArticle(
                    article=article.to_summary(),
                    recommended_mode=rec_mode,
                    estimated_reading_time_minutes=est_time_min,
                    relevance_reason=reason
                )
            )

        recommendations.sort(key=lambda r: (
            0 if any(t.lower() in r.article.section.lower() for t in preferred_topics) else 1,
            abs(r.estimated_reading_time_minutes - budget)
        ))

        return recommendations[:limit]

    def _select_mode_for_window(
        self,
        article: Article,
        budget_minutes: int,
        wpm: int,
        preferred_topics: List[str]
    ) -> tuple[ReadingMode, float, str]:
        """Calculates best reading mode given the commuter's available time budget."""
        full_time_min = article.reading_time_minutes or round(article.word_count / wpm, 1)

        # 1. Extremely short transit budget (<= 2 minutes)
        if budget_minutes <= 2:
            return (
                ReadingMode.SIXTY_SECONDS,
                1.0,
                f"Fits your {budget_minutes}-minute transit window. Distills core developments into 60 seconds."
            )

        # 2. Medium commuter budget (3-5 minutes)
        if budget_minutes <= 5:
            if full_time_min <= budget_minutes:
                return (
                    ReadingMode.FULL,
                    full_time_min,
                    f"Sufficient time ({budget_minutes} min) for the complete original reporting."
                )
            elif full_time_min > 8:
                return (
                    ReadingMode.BULLET_POINTS,
                    2.0,
                    f"Longform piece adapted to structured bullet points for your {budget_minutes}-minute transit window."
                )
            else:
                return (
                    ReadingMode.INLINE_SIMPLIFIED,
                    round(min(3.0, budget_minutes), 1),
                    f"Optimized for your {budget_minutes}-minute transit window with clear explanatory context."
                )

        # 3. Longer reading window (> 5 minutes)
        if full_time_min <= budget_minutes:
            return (
                ReadingMode.FULL,
                full_time_min,
                f"Sufficient time for full in-depth reporting tailored to your {budget_minutes}-minute reading budget."
            )
        else:
            return (
                ReadingMode.INLINE_SIMPLIFIED,
                4.0,
                f"Executive briefing highlighting key economic and strategic drivers for your window."
            )

user_service = UserService()
