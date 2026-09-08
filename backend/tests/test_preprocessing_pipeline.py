import pytest
from backend.app.db.mongodb import MongoDBService
from backend.app.services.cache_service import CacheService
from backend.app.services.preprocessor import ArticlePreprocessor
from backend.app.services.preprocessing_service import PreprocessingService
from backend.app.models.article import ReadingMode, ToneCategory, LengthTier

def test_preprocessing_service_ingests_from_mongo_and_populates_redis():
    # Setup isolated test services
    db = MongoDBService(uri="mongodb://localhost:27017", db_name="test_flexread_prep")
    cache = CacheService()
    cache.clear()
    preprocessor = ArticlePreprocessor()
    service = PreprocessingService(db_service=db, preprocessor=preprocessor, cache=cache)

    # 1. Seed raw, unprocessed article into MongoDB
    raw_article_doc = {
        "id": "ld_mongo_test_001",
        "headline": "Swiss National Bank Signals Prudent Monetary Policy Ahead",
        "lead": "Inflation stabilises in Switzerland while major central banks face persistent pressures.",
        "section": "Business",
        "raw_content": """
        The Swiss National Bank (SNB) announced its quarterly policy assessment today. 
        President Martin Schlegel emphasized that price stability remains firmly anchored, 
        with consumer inflation hovering well within the target range of 0 to 2 percent.
        However, the persistent strength of the Swiss franc poses structural challenges for Swiss export manufacturers,
        particularly in machinery, electrical engineering, and precision instruments.
        Consequently, financial markets widely expect the SNB to maintain an accommodative posture 
        to prevent an excessive appreciation of the currency against the euro and US dollar.
        """,
        "date": "2026-08-25T10:00:00Z",
        "preprocessing": None  # Unprocessed!
    }
    db.save_article(raw_article_doc)

    # Verify article is in MongoDB and currently unprocessed
    stored_before = db.get_article("ld_mongo_test_001")
    assert stored_before is not None
    assert stored_before.get("preprocessing") is None

    # 2. Run Pre-processing Service (Ingests from MongoDB -> Calculates -> Updates Mongo -> Populates Redis)
    result = service.process_article_from_mongo("ld_mongo_test_001", wpm=220, warm_variants=True)

    # Assertions on pipeline result
    assert result["article_id"] == "ld_mongo_test_001"
    assert result["word_count"] > 50
    assert result["reading_time_seconds"] > 0
    assert result["redis_cache_populated"] is True
    assert len(result["warmed_modes"]) == 4

    # 3. Verify MongoDB has been updated with pre-processing definitions
    updated_in_mongo = db.get_article("ld_mongo_test_001")
    assert updated_in_mongo is not None
    prep = updated_in_mongo["preprocessing"]
    assert prep is not None
    assert "main_points" in prep and len(prep["main_points"]) >= 1
    assert "keywords" in prep and len(prep["keywords"]) >= 2
    assert "tone" in prep
    assert "article_length" in prep
    assert "reading_time" in prep
    assert "word_count" in prep
    assert updated_in_mongo["word_count"] == result["word_count"]

    # 4. Verify Redis was populated as the ultra-fast cache layer
    # Check preprocessed metadata
    cached_meta = cache.get_cached_preprocessed_article("ld_mongo_test_001")
    assert cached_meta is not None
    assert cached_meta["headline"] == "Swiss National Bank Signals Prudent Monetary Policy Ahead"
    assert cached_meta["word_count"] == result["word_count"]

    # Check that reading modes were pre-populated into Redis
    var_60s = cache.get_variant("ld_mongo_test_001", ReadingMode.SIXTY_SECONDS, wpm=220)
    assert var_60s is not None
    assert var_60s.cached is True
    assert "**The Essentials:**" in var_60s.actual_content
    assert "**The Crux:**" in var_60s.actual_content

    var_bullets = cache.get_variant("ld_mongo_test_001", ReadingMode.BULLET_POINTS, wpm=220)
    assert var_bullets is not None
    assert var_bullets.cached is True

    var_inline = cache.get_variant("ld_mongo_test_001", ReadingMode.INLINE_SIMPLIFIED, wpm=220)
    assert var_inline is not None
    assert var_inline.cached is True

def test_batch_process_unprocessed_from_mongo():
    db = MongoDBService(uri="mongodb://localhost:27017", db_name="test_flexread_batch")
    cache = CacheService()
    service = PreprocessingService(db_service=db, cache=cache)

    # Insert 3 unprocessed articles
    for i in range(1, 4):
        db.save_article({
            "id": f"ld_batch_{i}",
            "headline": f"Global Technology Headline {i}",
            "lead": f"Lead for article {i}",
            "section": "Technology",
            "raw_content": f"Technology and semiconductor market growth continue across European enterprise software sectors in test number {i} with sufficient words for analysis.",
            "preprocessing": None
        })

    # Batch process
    summary = service.process_unprocessed_from_mongo(limit=10, warm_variants=True)
    assert summary["total_unprocessed_found"] >= 3
    assert summary["successfully_processed"] >= 3
    assert "ld_batch_1" in summary["processed_article_ids"]

    # Verify each was updated in Mongo
    for i in range(1, 4):
        art = db.get_article(f"ld_batch_{i}")
        assert art["preprocessing"] is not None
        assert len(art["preprocessing"]["keywords"]) > 0
