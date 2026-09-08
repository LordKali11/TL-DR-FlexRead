from backend.app.models.article import FlexReadVariant, ReadingMode
from backend.app.services.cache_service import CacheService

def test_cache_different_lengths():
    cache = CacheService()
    cache.clear()
    
    article_id = "ld_test_cache_001"
    
    v_60s = FlexReadVariant(
        mode=ReadingMode.SIXTY_SECONDS,
        title="Nvidia: Rekordzahlen im KI-Boom",
        summary="Kurzzusammenfassung in einem Satz.",
        actual_content="- Das Wichtigste in Kürze\n- Der Knackpunkt\n- Was jetzt wichtig ist",
        word_count=85,
        reading_time_seconds=25
    )
    
    v_bullets = FlexReadVariant(
        mode=ReadingMode.BULLET_POINTS,
        title="Fokus: Nvidia Zwischenbericht",
        summary="Zwei Sätze Zusammenfassung der Lage.",
        actual_content="- **Ausgangslage:** Punkt 1\n- **Kontext:** Punkt 2\n- **Ausblick:** Punkt 3",
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

    stats = cache.get_stats()
    assert stats.hits >= 2
    assert stats.misses >= 1
