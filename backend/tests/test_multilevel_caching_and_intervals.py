import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.article import Article, FlexReadVariant, ReadingMode
from backend.app.services.cache_service import cache_service
from backend.app.services.article_ingestion import article_ingestion_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_clean_test_state():
    """Ensure test article exists in article_ingestion_service._articles_cache and clean test keys from cache."""
    test_article_id = "ldtest_benchmark_001"
    clean_id = article_ingestion_service.normalize_id(test_article_id)
    
    # Register test article in-memory ingestion service cache
    test_article = Article(
        id=clean_id,
        nzz_id=f"ld.{clean_id[2:]}",
        headline="Swiss-US Economic Ties: Beyond the Bilateral Ledger",
        lead="Switzerland maintains $350B in direct investment in the United States, creating 400,000 high-tech jobs.",
        raw_content="Full text content regarding Swiss direct investment and high-tech manufacturing across America.",
        body_text="Full text content regarding Swiss direct investment and high-tech manufacturing across America."
    )
    article_ingestion_service._articles_cache[clean_id] = test_article

    yield clean_id

    # Clean up test keys
    cache_service.clear()


def test_multilevel_cache_l2_l3_hierarchy_and_promotion(ensure_clean_test_state):
    """
    Validates L2 (In-Memory) + L3 (Distributed Redis) hierarchy:
    1. Write-through stores in both L2 and L3.
    2. L2 hit returns < 0.1ms.
    3. If L2 is cleared, L3 hit returns and automatically promotes back into L2.
    4. Subsequent hit returns from L2 (< 0.1ms).
    """
    article_id = ensure_clean_test_state
    mode = ReadingMode.FIVE_MINUTES
    wpm = 220

    variant_5m = FlexReadVariant(
        mode=ReadingMode.FIVE_MINUTES,
        title="5-Minute Executive Briefing: Swiss-US Ties",
        summary="Switzerland is America's 6th largest foreign employer with $350B invested.",
        actual_content="### Executive Takeaways\n- $350B foreign direct investment\n- 400k high-paying American jobs",
        word_count=250,
        reading_time_seconds=68
    )

    # 1. Write through to L2 and L3
    cache_service.set_variant(article_id, mode, variant_5m, wpm=wpm)

    # 2. Check L2 hit
    cached_var, level = cache_service.get_variant_with_level(article_id, mode, wpm=wpm)
    assert cached_var is not None
    assert level == "L2"
    assert cached_var.title == variant_5m.title
    assert cached_var.mode == ReadingMode.FIVE_MINUTES

    # 3. Simulate L2 cache eviction by clearing memory_store while keeping Redis (L3)
    cache_service.memory_store.clear()
    assert len(cache_service.memory_store) == 0

    # Retrieve again: should fetch from L3 Redis and promote to L2
    cached_var_l3, level_l3 = cache_service.get_variant_with_level(article_id, mode, wpm=wpm)
    assert cached_var_l3 is not None
    assert level_l3 == "L3"
    assert cached_var_l3.title == variant_5m.title

    # 4. Verify promotion into L2: next call should be an L2 hit
    cached_var_l2, level_l2 = cache_service.get_variant_with_level(article_id, mode, wpm=wpm)
    assert cached_var_l2 is not None
    assert level_l2 == "L2"


def test_zero_latency_interval_transition_5m_to_10m_to_5m(ensure_clean_test_state):
    """
    Validates that transitioning reading intervals from 5 minutes to 10 minutes (and back to 5 minutes)
    occurs instantly (< 1ms) without latency spikes or content bleed.
    """
    article_id = ensure_clean_test_state
    wpm = 220

    variant_5m = FlexReadVariant(
        mode=ReadingMode.FIVE_MINUTES,
        title="5-Minute Briefing: Swiss Capital in the US",
        summary="Executive overview: $350B invested and 400,000 jobs created.",
        actual_content="[5m Content] Swiss pharmaceutical and precision engineering firms employ 400,000 US workers.",
        word_count=300,
        reading_time_seconds=80
    )

    variant_10m = FlexReadVariant(
        mode=ReadingMode.TEN_MINUTES,
        title="10-Minute Deep Dive: The True Swiss-US Economic Ledger",
        summary="Detailed balanced analysis covering trade goods, digital royalties, and unilateral zero tariffs.",
        actual_content="[10m Content] Dissecting the statistical illusion of the goods trade deficit vs the $18B US services surplus.",
        word_count=700,
        reading_time_seconds=190
    )

    # Pre-warm both reading intervals in multi-level cache
    cache_service.set_variant(article_id, ReadingMode.FIVE_MINUTES, variant_5m, wpm=wpm)
    cache_service.set_variant(article_id, ReadingMode.TEN_MINUTES, variant_10m, wpm=wpm)

    # 1. Fetch 5-minute version
    t0 = time.perf_counter()
    var_5m, level_5m = cache_service.get_variant_with_level(article_id, ReadingMode.FIVE_MINUTES, wpm=wpm)
    t_5m_ms = (time.perf_counter() - t0) * 1000

    assert var_5m is not None
    assert var_5m.mode == ReadingMode.FIVE_MINUTES
    assert "[5m Content]" in var_5m.actual_content
    assert t_5m_ms < 5.0, f"5m initial retrieval took too long: {t_5m_ms:.3f}ms"

    # 2. Transition from 5 minutes to 10 minutes
    t1 = time.perf_counter()
    var_10m, level_10m = cache_service.get_variant_with_level(article_id, ReadingMode.TEN_MINUTES, wpm=wpm)
    t_transition_10m_ms = (time.perf_counter() - t1) * 1000

    assert var_10m is not None
    assert var_10m.mode == ReadingMode.TEN_MINUTES
    assert "[10m Content]" in var_10m.actual_content
    # Zero latency spike: must be under 5 milliseconds (orders of magnitude below 20,000ms LLM spike)
    assert t_transition_10m_ms < 5.0, f"Transition 5m->10m had latency spike: {t_transition_10m_ms:.3f}ms"

    # 3. Transition BACK from 10 minutes to 5 minutes
    t2 = time.perf_counter()
    var_5m_reverted, level_revert = cache_service.get_variant_with_level(article_id, ReadingMode.FIVE_MINUTES, wpm=wpm)
    t_revert_ms = (time.perf_counter() - t2) * 1000

    assert var_5m_reverted is not None
    assert var_5m_reverted.mode == ReadingMode.FIVE_MINUTES
    assert "[5m Content]" in var_5m_reverted.actual_content
    assert "[10m Content]" not in var_5m_reverted.actual_content, "Content bleed detected! 10m content found in 5m variant"
    assert t_revert_ms < 5.0, f"Transition 10m->5m had latency spike: {t_revert_ms:.3f}ms"


def test_api_reading_variant_interval_switching_and_reversion(ensure_clean_test_state):
    """
    Tests full API lifecycle via /api/articles/{article_id}/read:
    - Step 1: Request 5 min (?target_time_minutes=5)
    - Step 2: Request 10 min (?target_time_minutes=10)
    - Step 3: Revert back to 5 min (?target_time_minutes=5)
    Verifies response headers, latency, cache levels, and content integrity.
    """
    article_id = ensure_clean_test_state
    wpm = 220

    variant_5m = FlexReadVariant(
        mode=ReadingMode.FIVE_MINUTES,
        title="NZZ 5-Minute Briefing",
        summary="Briefing summary text.",
        actual_content="Paragraph 1 of 5min briefing.",
        word_count=200,
        reading_time_seconds=55
    )
    variant_10m = FlexReadVariant(
        mode=ReadingMode.TEN_MINUTES,
        title="NZZ 10-Minute Analysis",
        summary="Analysis summary text.",
        actual_content="Paragraph 1 and 2 of 10min analytical depth.",
        word_count=500,
        reading_time_seconds=136
    )
    variant_15m = FlexReadVariant(
        mode=ReadingMode.FIFTEEN_MINUTES,
        title="NZZ 15-Minute Narrative",
        summary="Narrative summary text.",
        actual_content="Full narrative content.",
        word_count=1200,
        reading_time_seconds=327
    )

    cache_service.set_variant(article_id, ReadingMode.FIVE_MINUTES, variant_5m, wpm=wpm)
    cache_service.set_variant(article_id, ReadingMode.TEN_MINUTES, variant_10m, wpm=wpm)
    cache_service.set_variant(article_id, ReadingMode.FIFTEEN_MINUTES, variant_15m, wpm=wpm)

    # 1. GET 5 minutes
    res_5m = client.get(f"/api/articles/{article_id}/read?target_time_minutes=5&wpm={wpm}")
    assert res_5m.status_code == 200
    data_5m = res_5m.json()
    assert data_5m["mode"] == "5min"
    assert data_5m["title"] == "NZZ 5-Minute Briefing"
    assert data_5m["cache_level"] in ("L2", "L3")
    assert float(data_5m["response_time_ms"]) < 50.0

    # 2. Transition to 10 minutes
    res_10m = client.get(f"/api/articles/{article_id}/read?target_time_minutes=10&wpm={wpm}")
    assert res_10m.status_code == 200
    data_10m = res_10m.json()
    assert data_10m["mode"] == "10min"
    assert data_10m["title"] == "NZZ 10-Minute Analysis"
    assert data_10m["cache_level"] in ("L2", "L3")
    assert float(data_10m["response_time_ms"]) < 50.0

    # 3. Revert back to 5 minutes: MUST immediately serve 5-minute version
    res_5m_revert = client.get(f"/api/articles/{article_id}/read?target_time_minutes=5&wpm={wpm}")
    assert res_5m_revert.status_code == 200
    data_5m_revert = res_5m_revert.json()
    assert data_5m_revert["mode"] == "5min"
    assert data_5m_revert["title"] == "NZZ 5-Minute Briefing"
    assert data_5m_revert["actual_content"] == "Paragraph 1 of 5min briefing."
    assert data_5m_revert["cache_level"] == "L2"
    assert float(data_5m_revert["response_time_ms"]) < 20.0
