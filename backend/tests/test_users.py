from backend.app.models.api import CreateUserRequest, UpdatePreferencesRequest
from backend.app.models.article import Article, ArticlePreprocessing, ReadingMode
from backend.app.services.user_service import UserService

def test_user_management_lifecycle():
    user_service = UserService()
    
    # 1. Create user
    req = CreateUserRequest(
        username="Anna Tester",
        email="anna@nzz.ch",
        reading_speed_wpm=250,
        preferred_mode=ReadingMode.SIXTY_SECONDS,
        commute_time_budget_minutes=3
    )
    user = user_service.create_user(req)
    assert user.user_id is not None
    assert user.username == "Anna Tester"
    assert user.preferences.reading_speed_wpm == 250
    
    # 2. Update preferences
    update_req = UpdatePreferencesRequest(
        commute_time_budget_minutes=8,
        preferred_mode=ReadingMode.INLINE_SIMPLIFIED
    )
    updated = user_service.update_preferences(user.user_id, update_req)
    assert updated.preferences.commute_time_budget_minutes == 8
    assert updated.preferences.preferred_mode == ReadingMode.INLINE_SIMPLIFIED
    
    # 3. Log reading history
    user_service.record_reading_history(
        user_id=user.user_id,
        article_id="ld10020939",
        headline="Nvidia Test",
        mode_read=ReadingMode.SIXTY_SECONDS,
        time_spent_seconds=50
    )
    
    # 4. Check stats
    stats = user_service.get_user_stats(user.user_id)
    assert stats.articles_read_count >= 1
    assert stats.total_reading_time_minutes > 0.0

def test_commute_mode_recommendation():
    user_service = UserService()
    user = user_service.get_user("user_commuter_zurich")
    assert user is not None
    
    sample_article = Article(
        id="ld_rec_test",
        source_path="/test",
        headline="Schweizer Konjunkturbericht",
        lead="Lead text",
        section="Wirtschaft",
        raw_content="Wirtschaftstext mit vielen Absätzen..." * 50,
        preprocessing=ArticlePreprocessing(
            word_count=1200,
            reading_time=320,
            main_points=["Punkt 1", "Punkt 2"]
        )
    )
    
    # For a tight 1-minute window -> 60s
    mode_tight, _, _ = user_service.recommend_mode_for_article(user, sample_article, override_time_budget_minutes=1)
    assert mode_tight == ReadingMode.SIXTY_SECONDS
    
    # For an ample 15-minute window -> Full
    mode_ample, _, _ = user_service.recommend_mode_for_article(user, sample_article, override_time_budget_minutes=15)
    assert mode_ample == ReadingMode.FULL
