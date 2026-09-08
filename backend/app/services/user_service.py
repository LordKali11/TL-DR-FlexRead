import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import Counter
from ..config import settings
from ..models.user import UserProfile, UserPreferences, ReadingHistoryItem, UserStats
from ..models.article import Article, ReadingMode, ArticleSummary
from ..models.api import CreateUserRequest, UpdatePreferencesRequest, RecommendedArticle

logger = logging.getLogger(__name__)

class UserService:
    """
    Manages user profiles, reading preferences, reading history, and adaptive recommendations.
    Supports commuters and social traffic personalization.
    """
    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.db_path = settings.DATA_DIR / "users.db"
        self._init_db()
        self._seed_default_users()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        email TEXT,
                        created_at TEXT,
                        preferences JSON,
                        reading_history JSON,
                        bookmarked_articles JSON
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing user database: {e}")

    def _seed_default_users(self):
        """Seeds two representative English persona profiles."""
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
            weekend = UserProfile(
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
            self.save_user(weekend)
        except Exception as e:
            logger.error(f"Error seeding default users: {e}")

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Loads user from cache or SQLite database."""
        if user_id in self.users:
            return self.users[user_id]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, username, email, created_at, preferences, reading_history, bookmarked_articles FROM users WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                if row:
                    profile = UserProfile(
                        user_id=row[0],
                        username=row[1],
                        email=row[2],
                        created_at=datetime.fromisoformat(row[3]),
                        preferences=UserPreferences(**json.loads(row[4])),
                        reading_history=[ReadingHistoryItem(**item) for item in json.loads(row[5])],
                        bookmarked_articles=json.loads(row[6])
                    )
                    self.users[user_id] = profile
                    return profile
        except Exception as e:
            logger.error(f"Error reading user {user_id}: {e}")
        return None

    def save_user(self, user: UserProfile):
        """Persists user to SQLite and memory."""
        self.users[user.user_id] = user
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO users (user_id, username, email, created_at, preferences, reading_history, bookmarked_articles)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user.user_id,
                        user.username,
                        user.email,
                        user.created_at.isoformat(),
                        user.preferences.model_dump_json(),
                        json.dumps([h.model_dump(mode="json") for h in user.reading_history]),
                        json.dumps(user.bookmarked_articles)
                    )
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving user {user.user_id}: {e}")

    def create_user(self, req: CreateUserRequest) -> UserProfile:
        """Creates a new user profile."""
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        prefs = UserPreferences(
            reading_speed_wpm=req.reading_speed_wpm or 220,
            preferred_mode=req.preferred_mode or ReadingMode.SIXTY_SECONDS,
            topic_interests=req.topic_interests or ["Wirtschaft", "Schweiz"],
            commute_time_budget_minutes=req.commute_time_budget_minutes or 5
        )
        profile = UserProfile(
            user_id=user_id,
            username=req.username,
            email=req.email,
            preferences=prefs
        )
        self.save_user(profile)
        return profile

    def update_preferences(self, user_id: str, req: UpdatePreferencesRequest) -> Optional[UserProfile]:
        """Updates user preferences."""
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

    def record_reading_history(
        self,
        user_id: str,
        article_id: str,
        headline: str,
        mode_read: ReadingMode,
        time_spent_seconds: int,
        completion_rate: float = 1.0
    ) -> bool:
        """Logs a completed read session."""
        user = self.get_user(user_id)
        if not user:
            return False
        
        item = ReadingHistoryItem(
            article_id=article_id,
            headline=headline,
            mode_read=mode_read,
            time_spent_seconds=time_spent_seconds,
            completion_rate=completion_rate
        )
        user.reading_history.append(item)
        self.save_user(user)
        return True

    def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        """Calculates reading statistics and time saved."""
        user = self.get_user(user_id)
        if not user:
            return None
        
        history = user.reading_history
        articles_read = len(history)
        total_time_seconds = sum(h.time_spent_seconds for h in history)
        
        # Calculate favorite mode
        modes = [h.mode_read for h in history]
        favorite_mode = Counter(modes).most_common(1)[0][0] if modes else user.preferences.preferred_mode
        
        # Time saved metric: comparing reading time of original vs. compressed variant (~65% time saved)
        time_saved_minutes = round((articles_read * 4.5 * 0.65), 1)

        return UserStats(
            user_id=user_id,
            articles_read_count=articles_read,
            total_reading_time_minutes=round(total_time_seconds / 60.0, 1),
            favorite_mode=favorite_mode,
            top_sections=user.preferences.topic_interests,
            time_saved_minutes=time_saved_minutes
        )

    def recommend_mode_for_article(
        self,
        user: UserProfile,
        article: Article,
        override_time_budget_minutes: Optional[int] = None
    ) -> Tuple[ReadingMode, float, str]:
        """
        Determines the optimal reading mode based on:
        - Available time budget (commute window)
        - User reading speed (WPM)
        - Original article length tier
        - Topic interest
        """
        wpm = user.preferences.reading_speed_wpm
        budget_mins = override_time_budget_minutes or user.preferences.commute_time_budget_minutes
        budget_seconds = budget_mins * 60

        word_count = article.preprocessing.word_count if article.preprocessing else len(article.raw_content.split())
        full_read_seconds = int((word_count / wpm) * 60)

        # 1. Very tight budget (< 2 minutes): 60-second essentials
        if budget_seconds <= 120:
            return (
                ReadingMode.SIXTY_SECONDS,
                round(60 / 60, 1),
                f"Fits perfectly into your {budget_mins}-minute transit window."
            )

        # 2. Executive / Business section with medium budget (2 - 5 minutes): Bullet points
        section_lower = (article.section or "").lower()
        if "wirtschaft" in section_lower or "business" in section_lower or "finanzen" in section_lower or "finance" in section_lower:
            if budget_seconds <= 240:
                return (
                    ReadingMode.BULLET_POINTS,
                    round(120 / 60, 1),
                    "Executive briefing highlighting key economic and strategic drivers."
                )

        # 3. Commuter budget (3 - 6 minutes): Inline simplified for smooth reading
        if budget_seconds <= 360 and full_read_seconds > 300:
            return (
                ReadingMode.INLINE_SIMPLIFIED,
                round(180 / 60, 1),
                "Optimized for on-the-go reading: concise paragraphs and clear context."
            )

        # 4. Ample time budget: Full deep dive
        if budget_seconds >= full_read_seconds:
            return (
                ReadingMode.FULL,
                round(full_read_seconds / 60, 1),
                f"Sufficient time ({budget_mins} min) for the complete original reporting."
            )

        # Default to user's preferred mode
        return (
            user.preferences.preferred_mode,
            round(60 / 60, 1),
            "Matched to your personal reading preferences."
        )

user_service = UserService()
