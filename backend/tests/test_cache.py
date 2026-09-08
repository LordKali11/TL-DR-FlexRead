from backend.app.models.article import FlexReadVariant, ReadingMode
from backend.app.services.cache_service import CacheService

def test_cache_different_lengths_and_preprocessed_metadata():
    cache = CacheService()
    cache.clear()
    
    article_id = "ld_test_cache_001"
    
    v_60s = FlexReadVariant(
        mode=ReadingMode.SIXTY_SECONDS,
        title="Nvidia: Record Performance Amid AI Surge",
        summary="Concise one-sentence executive summary.",
        actual_content="**The Essentials:** Points\n**The Crux:** Conflict\n**What Matters Now:** Outlook",
        word_count=85,
        reading_time_seconds=25
    )
    
    v_bullets = FlexReadVariant(
        mode=ReadingMode.BULLET_POINTS,
        title="Focus: Nvidia Interim Assessment",
        summary="Two-sentence executive overview of market conditions.",
        actual_content="**Core Development:** Point 1\n**Context & Background:** Point 2\n**Outlook:** Point 3",
        word_count=190,
        reading_time_seconds=55
    )
    
    # Save both lengths to cache
    cache.set_variant(article_id, ReadingMode.SIXTY_SECONDS, v_60s)
    cache.set_variant(article_id, ReadingMode.BULLET_POINTS, v_bullets)
    
    # Retrieve 60s
    res_60s = cache.get_variant(article_id, ReadingMode.SIXTY_SECONDS)
    assert res_60s is not None
    assert res_60s.title == v_60s.title
    assert res_60s.mode == ReadingMode.SIXTY_SECONDS
    assert res_60s.cached is True
    
    # Retrieve bullets
    res_bullets = cache.get_variant(article_id, ReadingMode.BULLET_POINTS)
    assert res_bullets is not None
    assert res_bullets.title == v_bullets.title
    assert res_bullets.mode == ReadingMode.BULLET_POINTS
    assert res_bullets.cached is True
    
    # Miss on non-cached mode (inline_simplified)
    res_simplified = cache.get_variant(article_id, ReadingMode.INLINE_SIMPLIFIED)
    assert res_simplified is None

    # Test preprocessed metadata cache
    article_doc = {
        "id": article_id,
        "headline": "Nvidia Leads Global AI Hardware Buildout",
        "section": "Business",
        "word_count": 850,
        "reading_time_seconds": 230,
        "reading_time_minutes": 3.8,
        "preprocessing": {
            "keywords": ["AI", "Semiconductors", "Nvidia"],
            "main_points": ["Revenue doubled", "Hyperscaler demand remains high"]
        }
    }
    cache.cache_preprocessed_article(article_doc)
    cached_meta = cache.get_cached_preprocessed_article(article_id)
    assert cached_meta is not None
    assert cached_meta["headline"] == "Nvidia Leads Global AI Hardware Buildout"
    assert "AI" in cached_meta["keywords"]

    stats = cache.get_stats()
    assert stats.hits >= 3
    assert stats.misses >= 1
